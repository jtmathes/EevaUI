import sys
import glob
import serial
from Queue import Queue
from threading import Event

class SerialConnection(serial.Serial):

    def __init__(self, *args, **kargs):

        super(SerialConnection, self).__init__(*args, **kargs)

        self.receive_queue = Queue()
        self.close_request = Event()

    def read(self, timeout=0):
        
        return self.receive_queue.get(block=True, timeout=timeout)

    def write(self, data):

        serial.Serial.write(self, data)
        
    def close(self):

        self.close_request.set()

    def is_open(self):
        
        return serial.Serial.isOpen(self) and not self.close_request.is_set()
    
    def run(self):
        
        self.timeout = 0.5

        while True:
        
            new_data = bytearray(serial.Serial.read(self))
            
            if new_data and len(new_data) > 0:
                self.receive_queue.put(new_data)
            
            if self.close_request.is_set():
                break
            
        serial.Serial.close(self)
