
from PyQt4 import QtGui
from PyQt4.QtGui import QMainWindow
from eeva_designer import Ui_MainWindow

class EevaMainWindow(QMainWindow, Ui_MainWindow):
    
    def __init__(self, controller):
        
        QMainWindow.__init__(self)

        # Set up the user interface from Designer.
        self.setupUi(self)
        
        self.controller = controller
        
        self.connectButton.clicked.connect(self.connect_button_clicked)
        
        self.refreshPortsButton.clicked.connect(self.refresh_ports_button_clicked)

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
        
    def display_message(self, message, color):
        
        self.messageCenterTextEdit.append(message)
