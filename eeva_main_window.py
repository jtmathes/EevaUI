
import threading

# Use default python types instead of QVariant
import sip
sip.setapi('QVariant', 2)

from PyQt4 import QtGui, QtCore
from PyQt4.QtCore import QMetaObject, QObject, QEvent, Qt, Q_ARG
from PyQt4.QtGui import QMainWindow, QColor
from eeva_designer import Ui_MainWindow
from glob import DrivingCommand

class EevaMainWindow(QMainWindow, Ui_MainWindow):
    
    def __init__(self, app, controller):
        
        QMainWindow.__init__(self)

        # Set up the user interface from Designer.
        self.setupUi(self)
        
        self.controller = controller
        
        # Main Command Buttons
        self.collectDataButton.clicked.connect(self.collect_data_button_clicked)
        
        # Connection
        self.connectButton.clicked.connect(self.connect_button_clicked)
        self.refreshPortsButton.clicked.connect(self.refresh_ports_button_clicked)

        # Data Capture
        self.sampleRateTextEdit.editingFinished.connect(self.sample_rate_changed)
        self.sampleCountTextEdit.editingFinished.connect(self.capture_samples_edited)
        
        # Driving. Install filter to entire app so all keypresses get checked.
        self.key_press_filter = DrivingKeyFilter(controller)
        app.installEventFilter(self.key_press_filter)
        self.enableDrivingButton.clicked.connect(self.enabled_driving_button_clicked)

        self.settings = QtCore.QSettings("NER", "EevaUI")
        
    def restore_saved_settings(self):
        '''Should be called after initializing view.'''
        saved_port = str(self.settings.value("default_port"))
        print saved_port
        self.set_port(saved_port)

    def _need_to_switch_thread(self):
        return not isinstance(threading.current_thread(), threading._MainThread)

    def collect_data_button_clicked(self):
        self.controller.start_data_capture()

    def sample_rate_changed(self, *args):
        self.controller.validate_capture_parameters()
    
    def capture_samples_edited(self, *args):
        self.controller.validate_capture_parameters()

    def connect_button_clicked(self):
        
        if str(self.connectButton.text()).lower() == 'connect':
            port_name = str(self.portsComboBox.currentText())
            self.controller.connect_to_port(port_name)
        else:
            self.controller.disconnect_from_port()
           
    def set_connect_button_text(self, new_text):
        
        self.connectButton.setText(new_text)
        
    def refresh_ports_button_clicked(self):
        
        self.controller.request_new_port_list()
        
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
        
    @QtCore.pyqtSlot(str, str)
    def display_message(self, message, color):
        if self._need_to_switch_thread():
            QMetaObject.invokeMethod(self, 'display_message', Qt.QueuedConnection, Q_ARG(str, message), Q_ARG(str, color))
            return
        self.messageCenterTextEdit.setTextColor(QColor(color))
        self.messageCenterTextEdit.append(message)

    # Robot Status
    def set_pitch_angle(self, new):
        self.pitchLineEdit.setText('{:.1f}'.format(new))

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

    def eventFilter(self, obj, event):
        
        if (event.type() == QEvent.KeyPress) and (self.controller.driving_mode_enabled):

            cmd = self.convert_key_to_driving_command(event.key())
            
            if cmd is not None:
                self.controller.handle_driving_command(cmd)
                return True # don't pass on key press

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
