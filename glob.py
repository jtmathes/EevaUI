
import struct

class GlobID:
    
    StatusData = 5

class InvalidGlobFormat(Exception):
    
    def __init__(self, *args, **kargs):
        Exception.__init__(args, kargs)
        self.id = kargs.get('id', -1)

class Glob(object):
    
    @property
    def id(self):
        return self.__class__.id
        
    @classmethod
    def from_bytes(cls, data_bytes):
        obj = cls()
        obj.unpack(data_bytes)
        return obj
    
class StatusData(Glob):
    
    # Unique class ID
    id = GlobID.StatusData
    
    # Struct format for packing/unpacking. Little-endian no padding.
    data_format = '<ff'
    
    def __init__(self, time=0, tilt=0, instance=1):
        '''Constructor'''
        self.instance = instance
        self.time = time
        self.tilt = tilt

    def pack(self):
        
        try:
            data_bytes = struct.pack(StatusData.data_format, self.time, self.tilt)
        except struct.error:
            raise InvalidGlobFormat(id = StatusData.id)
        
        return data_bytes
        
    def unpack(self, data_bytes):

        self.time, self.tilt = struct.unpack('<10sHHb', data_bytes)
        
        try:
            self.time, self.tilt = struct.unpack(StatusData.data_format)
        except struct.error:
            raise InvalidGlobFormat(id = StatusData.id)