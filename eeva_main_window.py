
import threading
import os

# Use default python types instead of QVariant
import sip
sip.setapi('QVariant', 2)

from PyQt4 import QtGui, QtCore
from PyQt4.QtCore import QMetaObject, QObject, QEvent, Qt, Q_ARG
from PyQt4.QtGui import QMainWindow, QColor, QFileDialog
from eeva_designer import Ui_MainWindow
from eeva_glob import DrivingCommand, RobotCommand, Modes, Wave, PidParams
from validate_params import *

class EevaMainWindow(QMainWindow, Ui_MainWindow):
    
    def __init__(self, app, controller, connection_controller):
        
        QMainWindow.__init__(self)

        # Set up the user interface from Designer.
        self.setupUi(self)
        
        self.app = app
        self.controller = controller
        self.connection_controller = connection_controller
        
        # Main Command Buttons
        self.startButton.clicked.connect(self.start_button_clicked)
        self.stopButton.clicked.connect(self.stop_button_clicked)
        self.resetStateButton.clicked.connect(self.reset_state_button_clicked)
        self.collectDataButton.clicked.connect(self.collect_data_button_clicked)
        self.startAndCollectButton.clicked.connect(self.start_and_collect_data_button_clicked)
        self.openOutputDirectoryButton.clicked.connect(self.open_output_directory_clicked)
        self.changeOutputDirectoryButton.clicked.connect(self.change_output_directory_clicked)
        
        # Mode radio buttons
        self.balanceRadioButton.clicked.connect(self.balance_mode_selected)
        self.horizontalRadioButton.clicked.connect(self.horizontal_mode_selected)
        self.followLineRadioButton.clicked.connect(self.line_follow_mode_selected)
        self.experimentRadioButton.clicked.connect(self.experiment_mode_selected)
        self.customRadioButton.clicked.connect(self.custom_mode_selected)
        
        # Experiment selection
        self.experimentComboBox.activated.connect(self.new_experiment_selected)
        
        # Connection
        self.connectButton.clicked.connect(self.connect_button_clicked)
        self.refreshPortsButton.clicked.connect(self.refresh_ports_button_clicked)

        # Data Capture
        self.sampleRateTextEdit.editingFinished.connect(self.sample_rate_changed)
        self.sampleCountTextEdit.editingFinished.connect(self.capture_samples_edited)
        
        # Driving. Install filter to entire app so all key presses get checked.
        self.key_press_filter = DrivingKeyFilter(controller)
        app.installEventFilter(self.key_press_filter)
        self.enableDrivingButton.clicked.connect(self.enabled_driving_button_clicked)
        
        # Controller
        self.controlComboBox.activated.connect(self.controller_changed)
        self.proportionalLineEdit.editingFinished.connect(self.pid_parameters_changed)
        self.integralLineEdit.editingFinished.connect(self.pid_parameters_changed)
        self.derivativeLineEdit.editingFinished.connect(self.pid_parameters_changed)
        self.satLimitLineEdit.editingFinished.connect(self.pid_parameters_changed)
        self.intSatLimitLineEdit.editingFinished.connect(self.pid_parameters_changed)
        
        # Wave settings
        self.sineRadioButton.setChecked(True)
        self.trapezoidRadioButton.clicked.connect(self.trapezoid_wave_selected)
        self.waveMagnitudeLineEdit.editingFinished.connect(self.wave_parameters_changed)
        self.waveOffsetLineEdit.editingFinished.connect(self.wave_parameters_changed)
        self.waveFrequencyLineEdit.editingFinished.connect(self.wave_parameters_changed)
        self.waveDurationLineEdit.editingFinished.connect(self.wave_parameters_changed)
        
        # Manual experiment input
        self.manualCommandLineEdit.editingFinished.connect(self.manual_command_edited)
        self.manualIncrementLineEdit.editingFinished.connect(self.manual_command_increment_edited)
        self.manualCommandDecreaseButton.clicked.connect(self.manual_command_decrease_clicked)
        self.manualCommandIncreaseButton.clicked.connect(self.manual_command_incease_clicked)
        
        # Experiment input type
        self.manualGroupBox.clicked.connect(self.manual_input_clicked)
        self.autoWaveGroupBox.clicked.connect(self.autowave_input_clicked)
        self.manualGroupBox.setChecked(False)

        self.settings = QtCore.QSettings("NER", "EevaUI")
        
    def restore_default_port(self):
        '''Should be called after initializing view.'''
        saved_port = str(self.settings.value("default_port"))
        self.set_port(saved_port)

    def _need_to_switch_thread(self):
        return not isinstance(threading.current_thread(), threading._MainThread)

    def process_events(self):
        self.app.processEvents()
        
    @property
    def saved_base_directory(self):
        base_directory = self.settings.value("base_directory")
        if base_directory is None:
            base_directory = os.path.expanduser('~')
            self.saved_base_directory = base_directory
        return str(base_directory)
        
    @saved_base_directory.setter
    def saved_base_directory(self, new_value):
        self.settings.setValue("base_directory", new_value)
        
    def get_driving_command_states(self):
        return self.key_press_filter.command_state

    def start_button_clicked(self):
        self.controller.send_robot_command(RobotCommand.start)
        
        modifiers = QtGui.QApplication.keyboardModifiers()
        if modifiers == (QtCore.Qt.ControlModifier | QtCore.Qt.ShiftModifier):
            self.controller.send_robot_command(RobotCommand.task_timing)
        
    def stop_button_clicked(self):
        self.controller.send_robot_command(RobotCommand.stop)
        
    def reset_state_button_clicked(self):
        self.controller.send_robot_command(RobotCommand.reset)

    def collect_data_button_clicked(self):
        self.controller.change_capture_status()
        
    def start_and_collect_data_button_clicked(self):
        self.controller.start_data_capture(paused=True)
        self.controller.send_robot_command(RobotCommand.start)

    def sample_rate_changed(self, *args):
        validate_capture_parameters(self.controller, self)
    
    def capture_samples_edited(self, *args):
        validate_capture_parameters(self.controller, self)
        
    def open_output_directory_clicked(self):
        self.controller.open_output_directory()
        
    def change_output_directory_clicked(self):
        
        if self.controller.capturing_data:
            self.display_message("Please finish collecting data first.", 'black')
            return
        
        folder_path = str(QFileDialog.getExistingDirectory(self, "Select Base Directory", directory=self.saved_base_directory))
        if folder_path:
            self.saved_base_directory = folder_path
            popup = QtGui.QMessageBox()
            popup.setText("Base directory changed to\n{}\n\nThis will take effect next time program is started.".format(folder_path))
            popup.setWindowTitle('Directory Changed')
            popup.exec_()
        
    # Robot modes
    def balance_mode_selected(self):
        self.controller.change_robot_mode(Modes.balance)
    def horizontal_mode_selected(self):
        self.controller.change_robot_mode(Modes.horizontal)
    def line_follow_mode_selected(self):
        self.controller.change_robot_mode(Modes.line_follow)
    def experiment_mode_selected(self):
        self.controller.change_robot_mode(Modes.experiment)
    def custom_mode_selected(self):
        self.controller.change_robot_mode(Modes.custom)     
    
    def select_robot_mode(self, mode, submode):
        if mode == Modes.balance:
            self.balanceRadioButton.setChecked(True)
        elif mode == Modes.horizontal:
            self.horizontalRadioButton.setChecked(True)
        elif mode == Modes.line_follow:
            self.followLineRadioButton.setChecked(True)
        elif mode == Modes.experiment:
            self.experimentRadioButton.setChecked(True)
            self.select_experiment_mode(submode)
        elif mode == Modes.custom:
            self.customRadioButton.setChecked(True)
            
        self.set_experiment_list_visibility(mode == Modes.experiment)
        
    def set_experiment_list_visibility(self, make_visible):
        self.experimentComboBox.setEnabled(make_visible)
        
    # Experiment modes
    def set_experiment_list(self, experiment_names):

        self.experimentComboBox.clear()
        self.experimentComboBox.addItems(experiment_names)
        
    def new_experiment_selected(self):
        
        experiment_idx = int(self.experimentComboBox.currentIndex())
        self.controller.change_experiment(experiment_idx)
    
    def select_experiment_mode(self, mode):
        try:
            self.experimentComboBox.setCurrentIndex(mode)
        except:
            pass
    
    def connect_button_clicked(self):
        
        if str(self.connectButton.text()).lower() == 'connect':
            # TODO - would be better to request these from the robot
            self.balanceRadioButton.setChecked(True)
            self.experimentComboBox.setCurrentIndex(0)
            port_name = str(self.portsComboBox.currentText())
            self.connection_controller.connect_to_port(port_name)
        else:
            self.connection_controller.disconnect_from_port()

    def set_start_and_capture_button_text(self, text):

        self.startAndCollectButton.setText(text)

    def set_capture_button_text(self, text):
        
        self.collectDataButton.setText(text)

    def set_start_and_capture_button_enabled(self, state):

        self.startAndCollectButton.setEnabled(state)

    def set_capture_button_enabled(self, state):
        
        self.collectDataButton.setEnabled(state)

    def set_connect_button_text(self, new_text):
        
        self.connectButton.setText(new_text)
        
    def refresh_ports_button_clicked(self):
        
        self.controller.request_new_port_list()
        self.restore_default_port()
        
    def save_default_port(self, port_name):
        '''Save port as default for next time application opens.'''
        self.settings.setValue("default_port", port_name)

    def show_serial_ports(self, port_names):

        self.portsComboBox.clear()
        self.portsComboBox.addItems(port_names)
        
    def set_port(self, port_name):
        
        index = self.portsComboBox.findText(port_name)
        if index >= 0:
            self.portsComboBox.setCurrentIndex(index)
        
    def display_message(self, message, color):

        self.messageCenterTextEdit.setTextColor(QColor(color))
        self.messageCenterTextEdit.append(message)
        
    def clear_all_messages(self):
        self.messageCenterTextEdit.clear()
          
    # PID Parameters
    def set_controller_list(self, controller_names):
        self.controlComboBox.clear()
        self.controlComboBox.addItems(controller_names)

    def pid_parameters_changed(self):
        validate_pid_parameters(self.controller, send=True)
        
    def controller_changed(self):
        self.controller.show_current_pid_params()
    
    def get_pid_parameters(self):
        params = {}
        params['kp'] = self.proportionalLineEdit.text()
        params['ki'] = self.integralLineEdit.text()
        params['kd'] = self.derivativeLineEdit.text()
        params['sat_limit'] = self.satLimitLineEdit.text()
        params['int_sat_limit'] = self.intSatLimitLineEdit.text()
        return params
    
    def get_controller_index(self):
        return int(self.controlComboBox.currentIndex())
        
    def set_pid_parameters(self, params):

        self.proportionalLineEdit.setText('{:.5g}'.format(params.kp))
        self.integralLineEdit.setText('{:.5g}'.format(params.ki))
        self.derivativeLineEdit.setText('{:.5g}'.format(params.kd))
        self.satLimitLineEdit.setText('{:.5g}'.format(params.hilimit))
        self.intSatLimitLineEdit.setText('{:.5g}'.format(params.integral_hilimit))
        
    # Robot Status
    def update_robot_status(self, status):
        
        self.batteryLineEdit.setText('{:.1f}'.format(status["battery"]))
        self.rollLineEdit.setText('{:.1f}'.format(status["roll"]))
        self.pitchLineEdit.setText('{:.1f}'.format(status["pitch"]))
        self.yawLineEdit.setText('{:.1f}'.format(status["yaw"]))
        self.modeLineEdit.setText('{} / {} / {}'.format(status["main_mode"], status["sub_mode"], status["state"]))
        self.rAPLineEdit.setText(str(int(status["right_angular_position"])))
        self.lAPLineEdit.setText(str(int(status["left_angular_position"])))
        self.rAVLineEdit.setText(str(int(status["right_angular_velocity"])))
        self.lAVLineEdit.setText(str(int(status["left_angular_velocity"])))
        self.rLPLineEdit.setText(str(round(status["right_linear_position"], 2)))
        self.lLPLineEdit.setText(str(round(status["left_linear_position"], 2)))
        self.rLVLineEdit.setText(str(round(status["right_linear_velocity"], 1)))
        self.lLVLineEdit.setText(str(round(status["left_linear_velocity"], 1)))
        self.rPWMLineEdit.setText(str(int(status["right_pwm"])))
        self.lPWMLineEdit.setText(str(int(status["left_pwm"])))
        self.rVLineEdit.setText(str(round(status["right_voltage"], 1)))
        self.lVLineEdit.setText(str(round(status["left_voltage"], 1)))

    # Data Capture
    def set_capture_rate(self, new):
        self.sampleRateTextEdit.setText(str(round(new, 3)))
    def set_capture_duration(self, new):
        self.durationLineEdit.setText('{:.5g}'.format(new))
    def set_capture_samples(self, new):
        self.sampleCountTextEdit.setText(str(int(new)))
    def get_capture_rate(self):
        return self.sampleRateTextEdit.text()
    def get_capture_duration(self):
        return self.durationLineEdit.text()
    def get_capture_samples(self):
        return self.sampleCountTextEdit.text()
    
    def get_data_capture_filename(self):
        return str(self.dataFileNameLineEdit.text())

    def set_data_capture_filename(self, fname): 
        self.dataFileNameLineEdit.setText(fname)
    def need_to_generate_filename(self,):
        return bool(self.generateFileNameCheckBox.checkState())
    def set_generate_filename(self, state):
        self.generateFileNameCheckBox.setChecked(state)

    # Connection Status
    def set_num_msgs_sent(self, new):
        self.txPacketsLineEdit.setText(str(new))
    def set_num_msgs_received(self, new):
        self.rxPacketsLineEdit.setText(str(new))
    def set_bps_sent(self, new):
        self.txBPSLineEdit.setText(str(new))
    def set_bps_received(self, new):
        self.rxBPSLineEdit.setText(str(new))
    def set_bad_crc(self, new):
        self.badCRCLineEdit.setText(str(new))
    def set_dropped_msgs(self, new):
        self.droppedLineEdit.setText(str(new))
        
    # Experiment input types
    def autowave_input_clicked(self):
        if self.autoWaveGroupBox.isChecked():
            self.manualGroupBox.setChecked(False)
        else:
            self.manualGroupBox.setChecked(True)
            
    def manual_input_clicked(self):
        if self.manualGroupBox.isChecked():
            self.autoWaveGroupBox.setChecked(False)
        else:
            self.autoWaveGroupBox.setChecked(True)

    # Wave types
    def trapezoid_wave_selected(self):
        self.display_message('TODO - show trapezoid settings dialog', 'black')
    
    def get_selected_wave_type(self):
        if self.sineRadioButton.isChecked():
            return Wave.sine
        if self.squareRadioButton.isChecked():
            return Wave.square
        if self.triangleRadioButton.isChecked():
            return Wave.triangle
        if self.trapezoidRadioButton.isChecked():
            return Wave.trapezoidal
    
    def set_wave_mag(self, new_value):
        self.waveMagnitudeLineEdit.setText(str(new_value))
    def set_wave_offset(self, new_value):
        self.waveOffsetLineEdit.setText(str(new_value))
    def set_wave_freq(self, new_value):
        self.waveFrequencyLineEdit.setText(str(new_value))
    def set_wave_duration(self, new_value):
        self.waveDurationLineEdit.setText(str(new_value))
    def get_wave_mag(self):
        return str(self.waveMagnitudeLineEdit.text())
    def get_wave_offset(self):
        return str(self.waveOffsetLineEdit.text())
    def get_wave_freq(self):
        return str(self.waveFrequencyLineEdit.text())
    def get_wave_duration(self):
        return str(self.waveDurationLineEdit.text())
    def run_wave_continuous(self):
        return bool(self.runWaveContinuousCheckBox.isChecked())
    def run_wave_on_startup(self):
        return bool(self.autoWaveGroupBox.isChecked())
    
    def wave_parameters_changed(self):
        validate_wave_parameters(self)
        
    # Manual experiment input
    def set_manual_command(self, new_value):
        self.manualCommandLineEdit.setText(str(new_value))
    def set_manual_command_increment(self, new_value):
        self.manualIncrementLineEdit.setText(str(new_value))
    def get_manual_command(self):
        return str(self.manualCommandLineEdit.text())
    def get_manual_command_increment(self):
        return str(self.manualIncrementLineEdit.text())
    
    def manual_command_edited(self):
        validate_manual_command_parameters(self)
        self.controller.send_manual_experiment_input()
        
    def manual_command_increment_edited(self):
        validate_manual_command_parameters(self)
        
    def manual_command_decrease_clicked(self):
        increment = float(self.get_manual_command_increment())
        self.controller.change_manual_command(-increment)

    def manual_command_incease_clicked(self):
        increment = float(self.get_manual_command_increment())
        self.controller.change_manual_command(increment)
        
    # Driving
    def enabled_driving_button_clicked(self):
        self.controller.change_driving_mode()
    def update_driving_mode_button(self, text, color):
        self.enableDrivingButton.setText(text)
        self.enableDrivingButton.setStyleSheet("background-color: {}".format(color))

class DrivingKeyFilter(QObject):
    
    def __init__(self, controller):
        QObject.__init__(self)
        self.controller = controller
        self.command_state = {}
        for movement_type in DrivingCommand.possible_movements:
            self.command_state[movement_type] = False

    def eventFilter(self, obj, event):
        
        if self.controller.driving_mode_enabled:
            
            if (event.type() == QEvent.KeyPress):
                    
                cmd = self.convert_key_to_driving_command(event.key())
                if cmd is not None:
                    if not event.isAutoRepeat():
                        self.command_state[cmd] = True
                    return True # don't pass on key press

            elif (event.type() == QEvent.KeyRelease):
                    
                cmd = self.convert_key_to_driving_command(event.key())
                if cmd is not None:
                    if not event.isAutoRepeat():
                        self.command_state[cmd] = False
                    return True # don't pass on key release 
                    
        return False  # event wasn't handled      
    
    def convert_key_to_driving_command(self, key):
        
        if key == Qt.Key_Up:
            return DrivingCommand.forward
        elif key == Qt.Key_Right:
            return DrivingCommand.turn_right
        elif key == Qt.Key_Left:
            return DrivingCommand.turn_left
        elif key == Qt.Key_Down:
            return DrivingCommand.reverse
        elif key == Qt.Key_Space:
            return DrivingCommand.stop
        
        return None 
