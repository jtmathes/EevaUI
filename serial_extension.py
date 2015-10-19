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

def list_serial_ports():
    '''Return list of available serial port names.'''
    if sys.platform.startswith('win'):
        port_names = ['COM%s' % (i + 1) for i in range(256)]
    elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
        port_names = glob('/dev/tty[A-Za-z]*')
    elif sys.platform.startswith('darwin'):
        port_names = glob('/dev/tty.*')
    else:
        raise EnvironmentError('Unsupported platform')

    available_port_names = []
    for port_name in port_names:
        try:
            s = serial.Serial(port_name)
            s.close()
            available_port_names.append(port_name)
        except (OSError, serial.SerialException):
            pass
    return available_port_names
