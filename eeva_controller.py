import serial
import math
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
        
        # fields for tracking link stats
        self.last_bytes_tx = 0
        self.last_bytes_rx = 0
        
        # list of actively received capture data (cleared after writing to file)
        self.capture_data = []
        
        # What different message sources show as which color.
        self.source_display_colors = {'ui':'black', 'robot':'blue', 'assert':'red'}

    def set_view(self, view):
        
        self.view = view
        
        self.initialize_view(view)
        
        # start link status timer
        self.link_timer_elapsed()
        
    def initialize_view(self, view):
        
        self.request_new_port_list()
        
        self.view.set_capture_rate(DEFAULT_CAPTURE_RATE)
        self.view.set_capture_samples(DEFAULT_NUM_SAMPLES)
        self.validate_capture_parameters()
        
        self.view.restore_saved_settings()
        
    def start_data_capture(self):
        
        rate = float(self.view.get_capture_rate())
        samples = int(self.view.get_capture_samples())
        msg = CaptureCommand(is_start=1, freq=rate, desired_samples=samples)
        self.link.send(msg)
        
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
                
            self.capture_data.append(msg)
            
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
            
            # TODO call stop data capture and write to file
            self.capture_data = []
            
    def request_new_port_list(self):
        
        self.display_message('Refreshing ports')
        
        from serial.tools import list_ports
        port_list = [l[0] for l in list_ports.comports()]
    
        self.view.show_serial_ports(port_list)
    
    def display_message(self, message, source='ui'):

        color = self.source_display_colors.get(source, 'black')

        self.view.display_message(message, color)
        
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
        
        