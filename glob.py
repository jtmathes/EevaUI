
import struct

class GlobID:
    
    DrivingCommand = 3
    StatusData = 5

class Glob(object):
    
    @property
    def id(self):
        return self.__class__.id
        
    @classmethod
    def from_bytes(cls, data_bytes, instance=1):
        obj = cls(instance=instance)
        obj.unpack(data_bytes)
        return obj
    
class DrivingCommand(Glob):
    
    # Unique class ID
    id = GlobID.DrivingCommand
    
    # Struct format for packing/unpacking. Little-endian no padding.
    data_format = '<Iff'
    
    def __init__(self, movement_type=0, speed=0, omega=0, instance=1):
        '''Constructor'''
        self.instance = instance
        self.movement_type = movement_type
        self.speed = speed
        self.omega = omega

    def pack(self):

        return struct.pack(DrivingCommand.data_format, self.movement_type, self.speed, self.omega)
        
    def unpack(self, data_bytes):

        self.movement_type, self.speed, self.omega = struct.unpack(DrivingCommand.data_format, data_bytes)

    
class StatusData(Glob):
    
    # Unique class ID
    id = GlobID.StatusData
    
    # Struct format for packing/unpacking. Little-endian no padding.
    data_format = '<f'
    
    def __init__(self, tilt=0, instance=1):
        '''Constructor'''
        self.instance = instance
        self.tilt = tilt

    def pack(self):
        
        return struct.pack(StatusData.data_format, self.tilt)

    def unpack(self, data_bytes):
        
        self.tilt = struct.unpack(StatusData.data_format, data_bytes)[0]
