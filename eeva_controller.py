import os
import sys
import time
import csv
import datetime
import numbers
from eeva_glob import *
from eeva_io import *
from validate_params import *
from version import *

from PyQt4.QtCore import QTimer 

DRIVING_TIMER_INTERVAL = 0.2 # seconds

class EevaController:

    def __init__(self, link):
        
        self.link = link
        self.view = None
        
        # Hookup to our slot so can run new message callback from main thread.
        self.link.new_message.connect(self.new_message_callback)
        
        self.driving_mode_enabled = False
        
        # List of actively received capture data (cleared after writing to file)
        self.capture_data = []
        
        # List of messages that store information about robot task timing.
        self.task_timing_results = []
        
        self.capturing_data = False
        
        # Last main mode sent to the robot. 
        self.last_main_mode = Modes.balance
        self.last_sub_mode = 0
        
        # List of PID parameters for controllers.
        self.pid_params = [PidParams()] * PidParams.num_controllers
        
        # Set to true once robot's firmware version has been checked for compatibility issues with GUI.
        # Should be reset after each connection to the robot.
        self.verified_firmware_version = False
        
        # Set to true once robot ID has been checked. Should be reset after each connection to robot.
        self.verified_robot_id = False
        
        # Last time the user changed the mode from the GUI.
        self.last_mode_change_time = 0
        
        # What different message sources show as which color.
        self.source_display_colors = {'ui':'black', 'robot':'blue', 'assert':'red'}

    def set_view(self, view):
        
        self.view = view
        
        self.initialize_view(view)
        
    def initialize_view(self, view):
        
        self.display_message('GUI version: {}'.format(current_gui_version))
        
        # Create timestamped directory for current run.
        self.output_directory = os.path.join(view.saved_base_directory, 'eeva_output')
        self.session_directory = os.path.join(self.output_directory, time.strftime("output_%Y-%m-%d_%H-%M-%S/"))
        if not os.path.exists(self.session_directory):
            os.makedirs(self.session_directory)
        
        self.request_new_port_list()
        
        self.view.select_robot_mode(Modes.balance, 0)
        
        self.view.set_data_capture_filename('data')
        self.view.set_generate_filename(False)
        self.view.set_capture_rate(DEFAULT_CAPTURE_RATE)
        self.view.set_capture_samples(DEFAULT_NUM_SAMPLES)
        validate_capture_parameters(None, view)
        
        validate_wave_parameters(view)
        validate_manual_command_parameters(view)
        validate_pid_parameters(self, send=False)
        
        self.view.set_experiment_list([experiment[1] for experiment in Modes.experiments])
        self.view.set_experiment_list_visibility(False)
        
        self.view.set_controller_list([controller[1] for controller in PidParams.controllers])
        
        self.view.restore_default_port()
        
        self.driving_timer_elapsed()
        
    def driving_timer_elapsed(self):
        '''Send driving commands based on which keys are currently pressed down.'''
        try:
            if self.driving_mode_enabled:
                
                states = self.view.get_driving_command_states()
                
                # Set the correct bits based on what driving keys are being pressed.
                movement_commands = 0x00000000
                for movement_type in DrivingCommand.possible_movements:
                    movement_commands |= (movement_type if states[movement_type] else 0)

                msg = DrivingCommand(movement_commands = movement_commands)
                self.link.send(msg)
            
        finally:
            # Constantly reschedule timer to avoid overlapping calls
            QTimer.singleShot(DRIVING_TIMER_INTERVAL * 1000, self.driving_timer_elapsed)
        
    def verify_firmware_version(self, firmware_version):

        self.display_message("Eeva version: {}".format(firmware_version))
        
        compatible_firmware_versions = compatible_versions.get(current_gui_version, [])
        
        if firmware_version not in compatible_firmware_versions:
            self.display_message("Warning: Eeva version {} not compatible with GUI version {}.".format(firmware_version, current_gui_version))
            self.display_message("List of compatible Eeva versions is:")
            self.display_message(str(compatible_firmware_versions))
            compatible_gui_versions = list_compatible_gui_versions(firmware_version)
            if len(compatible_gui_versions) > 0:
                self.display_message("List of GUI versions that are compatible with Eeva version is:")
                self.display_message(str(compatible_gui_versions))
            else:
                self.display_message("Eeva version is newer than GUI.  Please upgrade to newest version of GUI.")
        
        self.verified_firmware_version = True
        
    def verify_robot_id(self, robot_id):

        self.display_message("ID: {}".format(robot_id))
        
        try:
            id_filepath = os.path.join(self.output_directory, 'eeva_ids.csv')
            with open(id_filepath, 'ab+') as id_file:
                csv_reader = csv.reader(id_file, delimiter=",")
                stored_ids = [row[0].strip() for row in csv_reader]
                if robot_id not in stored_ids:
                    csv_writer = csv.writer(id_file)
                    now = datetime.datetime.now()
                    csv_writer.writerow([robot_id, now.strftime("%Y-%m-%d %H:%M:%S")])
        except:
            self.display_message("Error when storing ID.")
        
        self.verified_robot_id = True
        
        # Now that robot ID is verified request recent messages, this makes output consistent.
        self.request_recent_text_messages_from_robot()
        
    def verify_robot_mode(self, msg):

        # Don't sync to robot mode if we've tried to change mode recently or it will
        # switch back and forth really fast.
        if self.time_since_last_mode_change() > 1:
            self.view.select_robot_mode(msg['main_mode'], msg['sub_mode'])
            self.last_main_mode = msg['main_mode']
            self.last_sub_mode = msg['sub_mode']
        
    def time_since_last_mode_change(self):
        
        return time.time() - self.last_mode_change_time
        
    def send_robot_command(self, cmd_type):
        
        # Send experiment input in case we're in experiment mode.
        if cmd_type == RobotCommand.start:
            if self.view.run_wave_on_startup():
                self.send_wave()
            else:
                self.send_manual_experiment_input()
        
        cmd = RobotCommand(command = cmd_type)
        self.link.send(cmd)
        
    def change_robot_mode(self, mode):
        
        cmd = Modes(main_mode = mode, sub_mode=self.last_sub_mode)
        self.link.send(cmd)
        self.last_main_mode = mode
        
        self.view.set_experiment_list_visibility(mode == Modes.experiment)
        
        self.last_mode_change_time = time.time()
        
    def change_experiment(self, experiment_number):
        
        experiment_id = Modes.experiments[experiment_number][0]
        
        cmd = Modes(main_mode=self.last_main_mode, sub_mode = experiment_id)
        self.link.send(cmd)
        self.last_sub_mode = experiment_id
        
        self.last_mode_change_time = time.time()
        
    def send_wave(self):
        
        wave_type = self.view.get_selected_wave_type()
        mag = float(self.view.get_wave_mag())
        offset = float(self.view.get_wave_offset())
        freq = float(self.view.get_wave_freq())
        duration = float(self.view.get_wave_duration())
        run_continuous = bool(self.view.run_wave_continuous())
        
        wave = Wave(wave_type=wave_type, mag=mag, offset=offset, freq=freq, 
                    duration=duration, run_continuous=run_continuous, wave_time=0)
        
        self.link.send(wave)
        
    def change_capture_status(self):
        
        if self.capturing_data:
            self.stop_data_capture()
        else: 
            self.start_data_capture()
        
    def start_data_capture(self, paused=False):
        
        if self.capturing_data:
            self.display_message("Need to finish collecting data first.")
        
        self.capture_data = []
        
        rate = float(self.view.get_capture_rate())
        samples = int(self.view.get_capture_samples())
        msg = CaptureCommand(is_start=1, paused=paused, freq=rate, desired_samples=samples)
        self.link.send(msg)
        
        self.capturing_data = True
        self.view.set_capture_button_text("Stop Collecting")
        
    def stop_data_capture(self):
        
        stop_msg = CaptureCommand(is_start = 0)
        self.link.send(stop_msg)
        
        self.capturing_data = False
        self.view.set_capture_button_text("Collect Data")
        
    def change_manual_command(self, amount):
        
        command = float(self.view.get_manual_command())
        
        self.view.set_manual_command(command + amount)
        
        self.send_manual_experiment_input() 
        
    def send_manual_experiment_input(self):
        
        command = float(self.view.get_manual_command())
        
        msg = Wave(wave_type=Wave.constant, offset=command, run_continuous=True)
        
        self.link.send(msg)
    
    def new_message_callback(self, id, instance, body):
        
        if id == GlobID.AssertMessage:
            msg = AssertMessage.from_bytes(body)
            if msg.valid:
                self.display_message(msg.message, 'assert')
                if msg.action == AssertMessage.stop_action:
                    self.display_message('Critical error, cannot continue to run.', 'assert')
                if msg.action == AssertMessage.restart_action:
                    self.display_message('Robot will restart...', 'assert')
        
        elif id == GlobID.DebugMessage:
            msg = DebugMessage.from_bytes(body)
            if msg.valid:
                self.display_message(msg.message, 'robot')
        
        elif id == GlobID.StatusData:
            msg = StatusData.from_bytes(body)
            self.view.update_robot_status(msg.data)
            
            if not self.verified_firmware_version:
                self.verify_firmware_version(msg.data['firmware_version'])
                
            if not self.verified_robot_id:
                self.verify_robot_id(msg.data['robot_id'])
                
            self.verify_robot_mode(msg.data)
            
        elif id == GlobID.CaptureData:
            
            msg = CaptureData.from_bytes(body)
            
            if len(self.capture_data) == 0:
                self.display_message('Receiving data...')
                
            self.capture_data.append(msg.as_tuple())
            
        elif id == GlobID.CaptureCommand:
            msg = CaptureCommand.from_bytes(body)
            expected_samples = msg.total_samples
            
            if len(self.capture_data) == 0 and expected_samples == 0:
                # This message was returned to validate capture parameters, not to send back data.
                # TODO this is kind of hacky
                self.view.set_capture_rate(msg.freq)
                self.view.set_capture_samples(msg.desired_samples)
                self.view.set_capture_duration(float(msg.desired_samples) / msg.freq)
                return
            elif len(self.capture_data) == 0:
                self.display_message("Expecting {} samples but didn't receive any.".format(expected_samples))
                return # nothing left to do since no data
            elif len(self.capture_data) == expected_samples:
                self.display_message("Received all {} samples.".format(expected_samples))
            elif len(self.capture_data) < expected_samples:
                self.display_message("Only received {} of {} samples.".format(len(self.capture_data), expected_samples))
            else: # Received more data than expected.
                self.display_message("Received too many samples ({}). Only expecting {}.".format(len(self.capture_data), expected_samples))

            self.write_data_to_file()
            
            self.stop_data_capture()
            
            self.capture_data = []
            
        elif id == GlobID.PidParams:
            
            controller_id = instance - 1
            
            if instance > len(self.pid_params):
                self.display_message("Received params for unknown controller with ID {}".format(controller_id))
                return
            
            msg = PidParams.from_bytes(body, instance)

            self.pid_params[controller_id] = msg
            
            # Update view for whichever controller is showing.
            self.show_current_pid_params()
            
            # If all parameters were being sent back make sure they all got here.
            if instance == PidParams.num_controllers:
                for k, pid_params in enumerate(self.pid_params):
                    if not pid_params.received:
                        #self.display_message("Failed to receive parameters for {}".format(PidParams.controllers[k]))
                        #self.display_message("Requesting PID parameters again.")
                        self.request_controller_gains_from_robot()
                        break
                    
        elif id == GlobID.TaskTimingResult:
            
            msg = TaskTimingResult.from_bytes(body, instance)

            if msg.task_name[:4].lower() == "done":
                self.write_task_timing_results_to_file()
                self.task_timing_results = []
            else:
                self.task_timing_results.append(msg)

        else:
            self.display_message("Received unhandled glob with ID {}".format(id))
            
    def show_current_pid_params(self):
        
        pid_idx = self.view.get_controller_index()
        
        try:
            params = self.pid_params[pid_idx]
        except IndexError:
            params = PidParams()
            
        self.view.set_pid_parameters(params)
    
    def request_controller_gains_from_robot(self):
        
        # Request all instances of PID parameters.
        self.link.send(Request(PidParams.id, instance=0))
        
    def request_recent_text_messages_from_robot(self):
        
        self.link.send(Request(DebugMessage.id, instance=0))
        self.link.send(Request(AssertMessage.id, instance=0))
    
    def display_message(self, message, source='ui'):

        color = self.source_display_colors.get(source, 'black')

        self.view.display_message(message, color)
        
    def change_driving_mode(self):
        
        if not self.driving_mode_enabled:
            self.view.update_driving_mode_button("Driving Enabled", "lightgreen")
        else: # driving mode disabled
            self.view.update_driving_mode_button("Driving Disabled", "pink")
        
        # Toggle driving mode
        self.driving_mode_enabled = not self.driving_mode_enabled
        
    def write_data_to_file(self):
        
        if len(self.capture_data) == 0:
            return
        
        filename = self.view.get_data_capture_filename()
        
        need_to_generate_fname = self.view.need_to_generate_filename()
        
        if not need_to_generate_fname and not filename:
            
            self.display_message("Generating file name since none was provided")
            self.view.set_generate_filename(True)
            need_to_generate_fname = True
            
        if need_to_generate_fname:
    
            filename = "data_" + time.strftime("%Y-%m-%d-%H-%M-%S")
            
        filename = make_filename_unique(self.session_directory, filename)
            
        # update text box so user can see actually used name
        self.view.set_data_capture_filename(filename)
            
        csv_filename = filename + ".csv"
        csv_filepath = os.path.join(self.session_directory, csv_filename)

        matlab_filename = filename + ".m"
        matlab_filepath = os.path.join(self.session_directory, matlab_filename)

        column_names = ('time', 'd1', 'd2', 'd3', 'd4', 'd5', 'd6', 'd7', 'd8')
        
        try:
            write_to_csv(csv_filepath, column_names, self.capture_data)
            self.display_message('Created {}'.format(csv_filename))
            write_to_matlab_script_file(matlab_filepath, column_names, self.capture_data)
            self.display_message('Created {}'.format(matlab_filename))
        except IOError:
            self.display_message('IO Error. Filename {} is most likely invalid.'.format(csv_filename))
            
    def write_task_timing_results_to_file(self):
        
        if len(self.task_timing_results) == 0:
            return
            
        filename = make_filename_unique(self.session_directory, "task_timing")
        filepath = os.path.join(self.session_directory, filename + ".csv")
        
        column_names = ('Task', 'Duration', 'Counts', 'Skip', 'Delay Max', 'Delay Min', 'Delay Avg', 'Run Max',
                         'Run Min', 'Run Avg', 'Intv. Max', 'Intv. Min', 'Intv. Avg', 'Total (s)', '%')
        
        try:
            with open(filepath, 'wb') as outfile:
                writer = csv.writer(outfile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
                writer.writerow(column_names)
                for r in self.task_timing_results:
                    
                    total_run_time = r.run_usec_avg * r.execute_counts / 1e6 # seconds
                    percentage_run_time = total_run_time * 100 / r.recording_duration
                    
                    result_list = [r.task_name, r.recording_duration, r.execute_counts, r.times_skipped, 
                                   r.delay_usec_max, r.delay_usec_min, r.delay_usec_avg,
                                   r.run_usec_max, r.run_usec_min, r.run_usec_avg,
                                   r.interval_usec_max, r.interval_usec_min, r.interval_usec_avg,
                                   total_run_time, percentage_run_time]
                    for i, val in enumerate(result_list):
                        if isinstance(val, numbers.Real):
                            result_list[i] = round(val, 1)
                    writer.writerow(result_list) 
            self.display_message('Created {}'.format(filepath))
        except IOError:
            self.display_message('IO Error. Filename {} is most likely invalid.'.format(filename))

    def open_output_directory(self):
        
        if self.capturing_data:
            self.display_message("Please finish collecting data first.")
            return
        
        open_output_directory_in_viewer(self.session_directory, self)
        
    def request_new_port_list(self):
        
        self.display_message('Refreshing ports')
        
        from serial.tools import list_ports
        port_list = [l[0] for l in list_ports.comports()]
    
        self.view.show_serial_ports(port_list)
        
