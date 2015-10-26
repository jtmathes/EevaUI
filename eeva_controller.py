import serial
import math
import csv
import os
import sys
import time
import subprocess
from serial_extension import list_serial_ports
from glob import *

from PyQt4.QtCore import QTimer 

DEFAULT_NUM_SAMPLES = 300
MIN_NUM_SAMPLES = 1
MAX_NUM_SAMPLES = 2000
FASTEST_CAPTURE_RATE = 10000.0 # Hz
DEFAULT_CAPTURE_RATE = FASTEST_CAPTURE_RATE / 100 # Hz
LINK_STATS_TIMER_INTERVAL = 1 # seconds

class EevaController:

    def __init__(self, link):
        
        self.link = link
        self.view = None
        
        self.driving_mode_enabled = False
        
        # Use home directory for root output directory. This is platform independent and works well with an installed package.
        home_directory = os.path.expanduser('~')
        
        # Create timestamped directory for current run.
        self.session_directory = os.path.join(home_directory, 'eeva-output/', time.strftime("output-%Y-%m-%d-%H-%M-%S/"))
        if not os.path.exists(self.session_directory):
            os.makedirs(self.session_directory)
        
        # fields for tracking link stats
        self.last_bytes_tx = 0
        self.last_bytes_rx = 0
        
        # list of actively received capture data (cleared after writing to file)
        self.capture_data = []
        
        self.capturing_data = False
        
        # What different message sources show as which color.
        self.source_display_colors = {'ui':'black', 'robot':'blue', 'assert':'red'}

    def set_view(self, view):
        
        self.view = view
        
        self.initialize_view(view)
        
        # start link status timer
        self.link_timer_elapsed()
        
    def initialize_view(self, view):
        
        self.request_new_port_list()
        
        self.view.select_balance_mode()
        
        self.view.set_data_capture_filename('data')
        self.view.set_generate_filename(False)
        self.view.set_capture_rate(DEFAULT_CAPTURE_RATE)
        self.view.set_capture_samples(DEFAULT_NUM_SAMPLES)
        self.validate_capture_parameters()
        
        self.view.restore_saved_settings()
        
    def send_robot_command(self, cmd_type):
        
        cmd = RobotCommand(command = cmd_type)
        self.link.send(cmd)
        
    def change_robot_mode(self, mode):
        
        print mode
        cmd = Modes(main_mode = mode)
        self.link.send(cmd)
        
    def change_capture_status(self):
        
        if self.capturing_data:
            self.stop_data_capture()
        else: 
            self.start_data_capture()
        
    def start_data_capture(self):
        
        if self.capturing_data:
            self.display_message("Need to finish collecting data first.")
        
        self.capture_data = []
        
        rate = float(self.view.get_capture_rate())
        samples = int(self.view.get_capture_samples())
        msg = CaptureCommand(is_start=1, freq=rate, desired_samples=samples)
        self.link.send(msg)
        
        self.capturing_data = True
        self.view.set_capture_button_text("Stop Collecting")
        
    def stop_data_capture(self):
        
        stop_msg = CaptureCommand(is_start = 0)
        self.link.send(stop_msg)
        
        self.capturing_data = False
        self.view.set_capture_button_text("Collect Data")
        
    def validate_capture_parameters(self):
        
        rate = self.try_parse(self.view.get_capture_rate(), float, DEFAULT_CAPTURE_RATE)
        rate = self.limit(rate, 0.001, FASTEST_CAPTURE_RATE)
        samples = self.try_parse(self.view.get_capture_samples(), int, DEFAULT_NUM_SAMPLES)
        samples = self.limit(samples, MIN_NUM_SAMPLES, MAX_NUM_SAMPLES)

        # Account for the fact the MCU can only capture at certain rates.  
        scale = int(FASTEST_CAPTURE_RATE / rate)
        rate = FASTEST_CAPTURE_RATE / scale

        duration = samples / rate

        self.view.set_capture_rate(rate)
        self.view.set_capture_samples(samples)
        self.view.set_capture_duration(duration)
        
        return duration
        
    def link_timer_elapsed(self):

        try:
            bytes_tx = self.link.num_messages_sent
            bytes_rx = self.link.num_messages_received

            # Estimate bytes per second.  Assume timer actually elapses close to desired rate.
            bps_tx = max(0, int((bytes_tx - self.last_bytes_tx) / LINK_STATS_TIMER_INTERVAL))
            bps_rx = max(0, int((bytes_rx - self.last_bytes_rx) / LINK_STATS_TIMER_INTERVAL))
            
            self.view.set_num_msgs_sent(bytes_tx)
            self.view.set_num_msgs_received(bytes_rx)
            self.view.set_bps_sent(bps_tx)
            self.view.set_bps_received(bps_rx)
            self.view.set_bad_crc(self.link.num_bad_crc_messages)
            self.view.set_dropped_msgs(self.link.num_dropped_messages)
            
            # Save so can calculate bytes per second next time
            self.last_bytes_tx = bytes_tx
            self.last_bytes_rx = bytes_rx

        finally:
            # Constantly reschedule timer to avoid overlapping calls
            QTimer.singleShot(LINK_STATS_TIMER_INTERVAL * 1000, self.link_timer_elapsed)
        
    def connect_to_port(self, port_name):
        
        try:
            self.link.connect(port_name, self.new_message_callback)
            self.link_connected = True
            self.view.save_default_port(port_name)
            
            # In case we got left in a bad state.
            self.stop_data_capture()
            
        except serial.SerialException as e:
            self.display_message('Failed to open {}.\n{}'.format(port_name, e))
            self.link.disconnect()
            self.link_connected = False
            
        if self.link_connected:
            
            self.display_message('Opened port {}'.format(port_name))
            
            self.view.set_connect_button_text('Disconnect')
            
    def disconnect_from_port(self):
        
        self.link.disconnect()
        self.link_connected = False
        self.view.set_connect_button_text('Connect')
        self.display_message('Port closed')
    
    def new_message_callback(self, id, instance, body):
        
        if id == GlobID.AssertMessage:
            msg = AssertMessage.from_bytes(body)
            self.display_message(msg.message, 'assert')
        
        elif id == GlobID.DebugMessage:
            msg = DebugMessage.from_bytes(body)
            self.display_message(msg.message, 'robot')
        
        elif id == GlobID.StatusData:
            msg = StatusData.from_bytes(body)
            self.view.set_pitch_angle(math.degrees(msg.tilt))
            
        elif id == GlobID.CaptureData:
            
            msg = CaptureData.from_bytes(body)
            
            if len(self.capture_data) == 0:
                self.display_message('Receiving data...')
                
            self.capture_data.append(msg.as_tuple())
            
        elif id == GlobID.CaptureCommand:
            msg = CaptureCommand.from_bytes(body)
            expected_samples = msg.total_samples
            
            if len(self.capture_data) == 0 and expected_samples == 0:
                self.display_message("No data was recorded by robot.")
                return # nothing left to do since no data
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
            
    def request_new_port_list(self):
        
        self.display_message('Refreshing ports')
        
        from serial.tools import list_ports
        port_list = [l[0] for l in list_ports.comports()]
    
        self.view.show_serial_ports(port_list)
    
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
        
    def handle_driving_command(self, cmd):
        
        if not self.driving_mode_enabled:
            return False # didn't handle key

        msg = DrivingCommand(movement_type = cmd)
        self.link.send(msg)
        
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
            
        filename = self.make_filename_unique(self.session_directory, filename)
            
        # update text box so user can see actually used name
        self.view.set_data_capture_filename(filename)
            
        csv_filename = filename + ".csv"
        csv_filepath = os.path.join(self.session_directory, csv_filename)
        #csv_filepath = self.make_filepath_unique(csv_filepath)
        
        column_names = ('time', 'd1', 'd2', 'd3', 'd4', 'd5', 'd6', 'd7', 'd8')
        
        try:
            self.write_to_csv(csv_filepath, column_names, self.capture_data)
            self.display_message('Created file {}'.format(csv_filename))
        except IOError:
            self.display_message('IO Error. Filename {} is most likely invalid.'.format(csv_filename))
        
    def write_to_csv(self, filepath, column_names, data):
        
        with open(filepath, 'wb') as outfile:
            writer = csv.writer(outfile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            writer.writerow(column_names)
            writer.writerows(data) 

    def open_output_directory(self):
        
        if sys.platform=='win32':
            os.startfile(self.session_directory)
        elif sys.platform=='darwin':
            subprocess.Popen(['open', self.session_directory])
        else:
            try:
                subprocess.Popen(['xdg-open', self.session_directory])
            except OSError:
                self.display_message("OS not supported.")

    def limit(self, val, min_val, max_val):
        
        val_type = type(val)
        if val > max_val:
            return val_type(max_val)
        if val < min_val:
            return val_type(min_val)
        return val
    
    def try_parse(self, value, cast_type, default_value):
        
        try:
            value = cast_type(value)
        except ValueError:
            value = default_value
        return value
    
    def make_filepath_unique(self, path):
        
        _, fname = os.path.split(path)
        just_fname, ext = os.path.splitext(fname)[1]
        
        i = 1 # number to append_to file name
        while os.path.exists(path):

            new_fname = '{}_{}{}'.format(just_fname, i, ext)
            path = os.path.join(dir, new_fname)
            i += 1
            
        return path

    def make_filename_unique(self, directory, fname_no_ext):
        
        original_fname = fname_no_ext
        dir_contents = os.listdir(directory)
        dir_fnames = [os.path.splitext(c)[0] for c in dir_contents]
        
        while fname_no_ext in dir_fnames:
            
            try:
                v = fname_no_ext.split('_')
                i = int(v[-1])
                i += 1
                fname_no_ext = '_'.join(v[:-1] + [str(i)])
            except ValueError:
                fname_no_ext = '{}_{}'.format(original_fname, 1)

        return fname_no_ext

        