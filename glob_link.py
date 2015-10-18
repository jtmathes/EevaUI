import sys
import struct
import serial
import threading
import Queue
import array
from crc import calculate_crc
from serial_extension import SerialConnection

class ParserThread(threading.Thread):

    def __init__(self, connection, new_message_callback):
        
        super(ParserThread, self).__init__()

        self.connection = connection
        self.new_message_callback = new_message_callback
        self.stop_request = threading.Event()

        # Receive fields
        self.parse_state = -1 # Index representing sequential state when parsing incoming bytes. 
        self.num_body_bytes = 0 # How many bytes are going to follow in message.
        self.body_start_index = 0 # Message data index of first body byte.
        self.message_data = bytearray() # Entire message excluding checksum.
        self.data_index = 0 # Index of where to store next received byte in message data array.
        self.expected_crc1 = 0 # lower byte of checksum at end of message
        self.expected_crc2 = 0 # upper byte " "
        self.number_packets_received = 0
        self.number_bytes_received = 0
        self.number_bad_crc_packets = 0
        self.number_dropped_packets = 0
        
        self.reset_parse()
        
    def run(self):
        '''Process bytes put into queue by port connection.'''
        while True:
            try:
                data_buffer = self.connection.read(timeout=0.5)
                self.parse_data(data_buffer)
            except (Queue.Empty, serial.SerialException):
                if self.stop_request.is_set():
                    break # exit thread
                
    def parse_data(self, data):
        
        message_pending = False
        
        self.number_bytes_received += len(data)
        
        for byte in data:
            
            if self.parse_state == -1:
                
                if byte == self.message_start_byte:
                    self.message_data.extend(byte)
                    self.data_index += 1
                    self.advance_parse()
                    
            elif self.parse_state >= 0 or self.parse_state <= 2:
                # Pull out id and both bytes of instance.
                self.message_data.extend(byte)
                self.data_index += 1
                self.advance_parse()
                
            elif self.parse_state == 3:
                
                self.message_data.extend(byte)
                self.data_index += 1
                self.num_body_bytes = byte
                self.body_start_index = self.data_index
                self.advance_parse()
                if self.num_body_bytes == 0:
                    self.advance_parse() # go straight to checksum
                
            elif self.parse_state == 4:
                
                self.message_data.extend(byte)
                self.data_index += 1
                
                if self.data_index - self.body_start_index >= self.num_body_bytes:
                    self.body_end_index = self.data_index
                    self.advance_parse()
                    
            elif self.parse_state == 5:
                
                self.expected_crc1 = byte
                self.advance_parse()
                
            elif self.parse_state == 6:
                
                self.expected_crc2 = byte
                self.advance_part
                
            else:
                
                self.reset_parse() # safety reset
                

            if message_pending:
            
                message_pending = False

                if self.verify_crc():
                
                    self.handle_new_packet()
                
                self.reset_parse()
                
    
    def advance_parse(self):
        self.parse_state += 1
        
    def reset_parse(self):
        self.date_index = 0
        self.body_start_index = 0
        self.parse_state = 0
        self.message_data = bytearray()

    def verify_crc(self):
        
        expected_crc = self.expected_crc1 + (self.expected_crc2 << 8)
        actual_crc = calculate_crc(self.message_data, 0xFFFF)

        # TODO throw exception if they don't match
        
        return expected_crc == actual_crc
    
    def handle_new_message(self):

        self.num_packets_received += 1
        
        id = self.message_data[1]
        instance = struct.unpack('<H', self.message_data[1:2])
        body = self.message_data[self.body_start_index : self.body_end_index]
        
        self.new_message_callback(id, instance, body)

class GlobLink(object):
    
    def __init__(self):
        
        # Port to receive and transmit bytes over.
        self.connection = None
    
        # Special byte that begins each new message.
        self.message_start_byte = 0xFE
        
        self.parser = None
    
        # Transfer fields 
        self.num_bytes_sent = 0
        self.num_packets_sent = 0
        self.transfer_buffer = array.array('c', '\0' * 300)

    def connect(self, port_name, new_message_callback):
        
        if self.connection_open():
            raise IOError('Connection still open.')

        if self.parser:
            # Ask old parser to stop before we create another one for the new connection.
            self.parser.stop_request.set()
            
        self.connection = SerialConnection(port=port_name, timeout=0.2)
        
        connection_thread = threading.Thread(target=self.connection.run)
        connection_thread.setDaemon(True)
        connection_thread.start()
        
        self.parser = ParserThread(self.connection, new_message_callback)
        self.parser.setDaemon(True)
        self.parser.start()
        
    def disconnect(self):
        
        if self.parser:
            self.parser.stop_request.set()
            self.parser = None
        
        if self.connection_open():
            self.connection.close()
            self.connection = None
            return True
        
        return False # connection already closed
    
    def connection_open(self):
        
        return self.connection and self.connection.is_open()
    
    def send(self, glob):
        
        if not self.connection_open():
            return
        
        data_bytes = glob.pack()
        
        header_fmt = '<BBHB'
        header = (self.message_start_byte, glob.id, glob_instance, len(data_bytes))
        header_size = struct.calcsize(header_fmt)
        
        struct.pack_into(self.transfer_buffer, 0, *header)
        
        crc = calculate_crc(transfer_buffer, 0xFFFF)

        struct.pack_into('<H', self.transfer_buffer, header_size + len(data_bytes), crc)

        self.connection.write(self.transfer_buffer, )
        
        self.num_bytes_sent += packet_size
        self.num_packets_sent += 1
