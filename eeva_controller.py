import serial
from serial_extension import list_serial_ports

class EevaController:

    def __init__(self, link):
        
        self.link = link

    def set_view(self, view):
        
        self.view = view
        
        self.request_new_port_list()
        
    def connect_to_port(self, port_name):
        
        try:
            self.link.connect(port_name, self.new_message_callback)
            self.link_connected = True
        except serial.SerialException as e:
            self.display_message('Failed to open {}.\n{}'.format(port_name, e))
            self.link.disconnect()
            self.link_connected = False
            
        if self.link_connected:
            
            self.display_message('Opened port {}'.format(port_name))
            
            self.view.set_connect_button_text('Disconnect')
            
            # TODO save port name for next time form is opened
    
    def disconnect_from_port(self):
        
        self.link.disconnect()
        self.link_connected = False
        self.view.set_connect_button_text('Connect')
        self.display_message('Port closed')
    
    def new_message_callback(self):
        
        pass
    
    def request_new_port_list(self):
        
        self.display_message('Refreshing ports')
    
        self.view.show_serial_ports(list_serial_ports())
    
    def display_message(self, message, source='ui'):

        color = 'black'

        self.view.display_message(message, color)
        