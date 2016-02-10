import serial
from glob import *
from version import current_gui_version, compatible_versions

from PyQt4.QtCore import QTimer 

# Connection settings
LINK_STATS_TIMER_INTERVAL = 0.25 # seconds

class ConnectionController(object):
    
    def __init__(self, main_controller, link):
        
        self.controller = main_controller
        self.link = link
        
        # fields for tracking link stats
        self.last_bytes_tx = 0
        self.last_bytes_rx = 0
        
        # How many consecutive times we haven't received any bytes in timer callback when connected to robot.
        self.num_times_no_bytes_received = 0
        
        self.link_connected = False
        
    def set_view(self, view):
        self.view = view
        
    def connect_to_port(self, port_name):
        
        self.view.clear_all_messages()
        self.controller.display_message("Connecting...")
        self.view.process_events() # immediately show message in case GUI locks up for a little bit
        try:
            self.link.connect(port_name)
            self.link_connected = True
            self.view.save_default_port(port_name)
            
            # In case we got left in a bad state.
            self.controller.stop_data_capture()
            
            self.controller.request_controller_gains_from_robot()
            
        except serial.SerialException as e:
            self.controller.display_message('Error {}\nTry to connect again.'.format(e))
            self.link.disconnect()
            self.link_connected = False
            
        if self.link_connected:
            self.controller.display_message("Success")
            self.view.set_connect_button_text('Disconnect')
            # make sure flag is reset so GUI verifies firmware version
            self.controller.verified_firmware_version = False
            self.controller.verified_robot_id = False
            
    def disconnect_from_port(self):
        
        self.link.disconnect()
        self.link_connected = False
        self.view.set_connect_button_text('Connect')
        self.controller.display_message('Disconnected')

    def start_link_timer(self):
        self.link_timer_elapsed()

    def link_timer_elapsed(self):

        try:
            bytes_tx = self.link.num_bytes_sent
            bytes_rx = self.link.num_bytes_received

            # Estimate bytes per second.  Assume timer actually elapses close to desired rate.
            bps_tx = max(0, int((bytes_tx - self.last_bytes_tx) / LINK_STATS_TIMER_INTERVAL))
            bps_rx = max(0, int((bytes_rx - self.last_bytes_rx) / LINK_STATS_TIMER_INTERVAL))
            
            self.view.set_num_msgs_sent(self.link.num_messages_sent)
            self.view.set_num_msgs_received(self.link.num_messages_received)
            self.view.set_bps_sent(bps_tx)
            self.view.set_bps_received(bps_rx)
            self.view.set_bad_crc(self.link.num_bad_crc_messages)
            self.view.set_dropped_msgs(self.link.num_dropped_messages)
            
            # Save so can calculate bytes per second next time
            self.last_bytes_tx = bytes_tx
            self.last_bytes_rx = bytes_rx
            
            self.check_for_lost_connection(self.link.num_messages_received, bps_rx)
            
        finally:
            # Constantly reschedule timer to avoid overlapping calls
            QTimer.singleShot(LINK_STATS_TIMER_INTERVAL * 1000, self.link_timer_elapsed)
        
    def check_for_lost_connection(self, num_messages_received, bps_rx):
        
        if self.link.connection_open() and num_messages_received > 0:
            
            if bps_rx == 0:
                self.num_times_no_bytes_received += 1
            else:
                self.num_times_no_bytes_received = 0
                
            no_bytes_received_duration = self.num_times_no_bytes_received * LINK_STATS_TIMER_INTERVAL
            
            if no_bytes_received_duration >= 1.25:
                self.controller.display_message("Eeva not responding...")
                self.disconnect_from_port()
                self.controller.display_message("If robot is still on and was always in range then make sure your operating system isn't using a power-save mode for bluetooth.")
                