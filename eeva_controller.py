import serial
import math
from serial_extension import list_serial_ports
from glob import *

from PyQt4.QtCore import QTimer 

class EevaController:

    def __init__(self, link):
        
        self.link = link
        self.view = None
        
        # fields for tracking link stats
        self.last_bytes_tx = 0
        self.last_bytes_rx = 0

    def set_view(self, view):
        
        self.view = view
        
        self.request_new_port_list()
        
        # start link status timer
        self.link_timer_elapsed()
        
    def link_timer_elapsed(self):
        
        timer_period = 1 # seconds
        try:

            bytes_tx = self.link.num_messages_sent
            bytes_rx = self.link.num_messages_received

            # Estimate bytes per second.  Assume timer actually elapses close to desired rate.
            bps_tx = max(0, int((bytes_tx - self.last_bytes_tx) / timer_period))
            bps_rx = max(0, int((bytes_rx - self.last_bytes_rx) / timer_period))
            
            self.view.set_num_msgs_sent(bytes_tx)
            self.view.set_num_msgs_received(bytes_rx)
            self.view.set_bps_sent(bps_tx)
            self.view.set_bps_received(bps_rx)
            self.view.set_bad_crc(self.link.num_bad_crc_messages)
            self.view.set_dropped_msgs(self.link.num_dropped_messages)
            
            # Save so can calculate bytes per second next time
            self.last_bytes_tx = bytes_tx
            self.last_bytes_rx = bytes_rx
            
            test_glob = DrivingCommand(movement_type=0)
            self.link.send(test_glob)
        
        finally:
            # Constantly reschedule timer to avoid overlapping calls
            QTimer.singleShot(timer_period * 1000, self.link_timer_elapsed)
        
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
    
    def new_message_callback(self, id, instance, body):
        
        if id == GlobID.StatusData:
            msg = StatusData.from_bytes(body)
            self.view.set_pitch_angle(math.degrees(msg.tilt))
            
    def request_new_port_list(self):
        
        self.display_message('Refreshing ports')
        
        from serial.tools import list_ports
        port_list = [l[0] for l in list_ports.comports()]
    
        self.view.show_serial_ports(port_list)
    
    def display_message(self, message, source='ui'):

        color = 'black'

        self.view.display_message(message, color)
        