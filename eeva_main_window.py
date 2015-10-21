
import threading

from PyQt4 import QtGui, QtCore
from PyQt4.QtCore import QMetaObject, Qt, Q_ARG
from PyQt4.QtGui import QMainWindow, QColor
from eeva_designer import Ui_MainWindow

class EevaMainWindow(QMainWindow, Ui_MainWindow):
    
    def __init__(self, controller):
        
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

    def show_serial_ports(self, port_names):
        
        self.portsComboBox.clear()
        self.portsComboBox.addItems(port_names)
        
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

