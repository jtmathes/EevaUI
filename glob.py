
import struct

class GlobID:
    
    AssertMessage = 0
    DebugMessage = 1
    CaptureData = 2
    DrivingCommand = 3
    CaptureCommand = 4
    StatusData = 5
    Modes = 14
    RobotCommand = 16

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
    
    forward = 0
    reverse = 1
    turn_right = 2
    turn_left = 3
    stop = 4
    
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
    
class StatusData(Glob):
    
    # Unique class ID
    id = GlobID.StatusData
    
    # Struct format for packing/unpacking. Little-endian no padding.
    data_format = '<f'
    
    def __init__(self, tilt=0, instance=1):
        '''Constructor'''
        self.instance = instance
        self.tilt = tilt

    def unpack(self, data_bytes):
        
        self.tilt = struct.unpack(StatusData.data_format, data_bytes)[0]
        
        
class CaptureCommand(Glob):
    
    # Unique class ID
    id = GlobID.CaptureCommand
    
    # Struct format for packing/unpacking. Little-endian no padding.
    data_format = '<BBHII'
    
    def __init__(self, is_start=0, freq=1, desired_samples=1, total_samples=1, instance=1):
        '''Constructor'''
        self.instance = instance
        self.is_start = is_start
        self.pad0 = 0
        self.freq = freq
        self.desired_samples = desired_samples
        self.total_samples = total_samples

    def pack(self):
        
        return struct.pack(CaptureCommand.data_format, self.is_start, self.pad0, self.freq,
                            self.desired_samples, self.total_samples)

    def unpack(self, data_bytes):
        
        values = struct.unpack(CaptureCommand.data_format, data_bytes)
        self.is_start = values[0]
        self.pad0 = values[1]
        self.freq = values[2]
        self.desired_samples = values[3]
        self.total_samples = values[4]
        
class CaptureData(Glob):
    
    # Unique class ID
    id = GlobID.CaptureData
    
    # Struct format for packing/unpacking. Little-endian no padding.
    data_format = '<' + ('f'*9)
    
    def __init__(self, instance=1):
        '''Constructor'''
        self.instance = instance

    def unpack(self, data_bytes):
        
        self.values = struct.unpack(CaptureData.data_format, data_bytes)
        self.time = self.values[0]
        self.data = self.values[1:]
        
    def as_tuple(self):
        return self.values
        
class AssertMessage(Glob):
    
    # Unique class ID
    id = GlobID.AssertMessage
    
    # Struct format for packing/unpacking. Little-endian no padding.
    data_format = '<I200s'
    
    def __init__(self, instance=1):
        '''Constructor'''
        self.instance = instance

    def unpack(self, data_bytes):
        
        self.action, self.message = struct.unpack(AssertMessage.data_format, data_bytes)

class DebugMessage(Glob):
    
    # Unique class ID
    id = GlobID.DebugMessage
    
    # Struct format for packing/unpacking. Little-endian no padding.
    data_format = '<200s'
    
    def __init__(self, instance=1):
        '''Constructor'''
        self.instance = instance

    def unpack(self, data_bytes):
        
        self.message = struct.unpack(DebugMessage.data_format, data_bytes)[0]

class Modes(Glob):
    
    # Unique class ID
    id = GlobID.Modes
    
    # Main mode IDs
    balance = 0
    horizontal = 1
    line_follow = 2
    experiment = 3
    
    # Operating State IDs
    stopped = 0
    initialing = 1
    normal = 2
    
    # Experiment sub IDs
    experiment1 = 0
    
    # Struct format for packing/unpacking. Little-endian no padding.
    data_format = '<BBB'
    
    def __init__(self, main_mode=balance, sub_mode=0, state=normal, instance=1):
        '''Constructor'''
        self.instance = instance
        self.main_mode = main_mode
        self.sub_mode = sub_mode
        self.state = state
        
    def pack(self):

        return struct.pack(Modes.data_format, self.main_mode, self.sub_mode, self.state)

class RobotCommand(Glob):
    
    # Unique class ID
    id = GlobID.RobotCommand
    
    start = 0
    stop = 1
    reset = 2
    
    # Struct format for packing/unpacking. Little-endian no padding.
    data_format = '<B'
    
    def __init__(self, command=stop, instance=1):
        '''Constructor'''
        self.instance = instance
        self.command = command
        
    def pack(self):

        return struct.pack(RobotCommand.data_format, self.command)
    
