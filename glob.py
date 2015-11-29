
import struct
import math

class GlobID:
    
    AssertMessage = 0
    DebugMessage = 1
    CaptureData = 2
    DrivingCommand = 3
    CaptureCommand = 4
    StatusData = 5
    Modes = 14
    RobotCommand = 16
    Wave = 19
    PidParams = 20
    Request = 21

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
    data_format = '<' + ('f' * 4) + ('B' * 4) + ('f' * 14)
    
    def __init__(self, instance=1):
        '''Constructor'''
        self.instance = instance
        self.data = {}

    def unpack(self, data_bytes):
        
        values = struct.unpack(StatusData.data_format, data_bytes)
        self.data["battery"] = values[0]
        self.data["roll"] = math.degrees(values[1])
        self.data["pitch"] = math.degrees(values[2])
        self.data["yaw"] = math.degrees(values[3])
        self.data["main_mode"] = values[4]
        self.data["sub_mode"] = values[5]
        self.data["state"] = values[6]
        self.data["pad0"] = values[7]
        self.data["left_linear_position"] = values[8]
        self.data["right_linear_position"] = values[9]
        self.data["left_angular_position"] = math.degrees(values[10])
        self.data["right_angular_position"] = math.degrees(values[11])
        self.data["left_linear_velocity"] = values[12]
        self.data["right_linear_velocity"] = values[13]
        self.data["left_angular_velocity"] = math.degrees(values[14]) * 60.0 / 360.0 # rad/s to RPM
        self.data["right_angular_velocity"] = math.degrees(values[15]) * 60.0 / 360.0 # rad/s to RPM
        self.data["left_current"] = values[16]
        self.data["right_current"] = values[17]
        self.data["left_pwm"] = values[18] * 100 # to percentage
        self.data["right_pwm"] = values[19] * 100 # to percentage
        self.data["left_torque"] = values[20] * 1000 # to mNm
        self.data["right_torque"] = values[21] * 1000 # to mNm
        self.data["left_voltage"] = self.data["battery"] * self.data["left_pwm"] / 100.0
        self.data["right_voltage"] = self.data["battery"] * self.data["right_pwm"] / 100.0
        self.data["left_power"] = abs(self.data["left_voltage"] * self.data["left_current"])
        self.data["right_power"] = abs(self.data["right_voltage"] * self.data["right_current"])
            
class CaptureCommand(Glob):
    
    # Unique class ID
    id = GlobID.CaptureCommand
    
    # Struct format for packing/unpacking. Little-endian no padding.
    data_format = '<BBHII'
    
    def __init__(self, is_start=0, paused=0, freq=1, desired_samples=1, total_samples=1, instance=1):
        '''Constructor'''
        self.instance = instance
        self.is_start = is_start
        self.paused = paused
        self.freq = freq
        self.desired_samples = desired_samples
        self.total_samples = total_samples

    def pack(self):
        
        return struct.pack(CaptureCommand.data_format, self.is_start, self.paused, self.freq,
                            self.desired_samples, self.total_samples)

    def unpack(self, data_bytes):
        
        values = struct.unpack(CaptureCommand.data_format, data_bytes)
        self.is_start = values[0]
        self.paused = values[1]
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
    custom = 4
    
    # Operating State IDs
    stopped = 0
    initialing = 1
    normal = 2
    
    # Experiment sub IDs. Text labels so can show on form.
    experiments = {0 : "None",
                   1 : "Motor Speed Control",
                   2 : "Some Other Experiment"}
    
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
    
class Wave(Glob):
    
    # Unique class ID
    id = GlobID.Wave
    
    # wave types
    sine = 0
    square = 1
    triangle = 2
    trapezoidal = 3
    constant = 4
    
    # wave states
    stopped = 0
    ready_to_start = 1
    starting_up = 2
    started = 3
    
    # Struct format for packing/unpacking. Little-endian no padding.
    data_format = '<BBBBfffffffBBBB' + (15 * 'f')
    
    def __init__(self, **kargs):
        '''Constructor'''
        self.instance = kargs.get('instance', 1)
        
        self.type = kargs.get('wave_type', Wave.sine)
        self.state = kargs.get('state', Wave.stopped)
        self.value = kargs.get('wave_value', 0)
        #self.pad = [0, 0]
        self.mag = kargs.get('mag', 0)
        self.freq = kargs.get('freq', 1)
        self.duration = kargs.get('duration', 1)
        self.offset = kargs.get('offset', 0)
        self.time = kargs.get('wave_time', 0)
        self.total_time = 0
        self.run_continuous = kargs.get('run_continuous', False)
        #self.pad2 = [0, 0, 0]
        
        # Trapezoid parameters
        self.vmax = kargs.get('vmax', 0)
        self.amax = kargs.get('amax', 0)
        self.dx = kargs.get('dx', 0)
        self.ts_and_cs = [0] * 12 # calculated on robot
        
    def pack(self):

        return struct.pack(Wave.data_format, self.type, self.state, 0, 0, self.value, self.mag, self.freq, self.duration,
                           self.offset, self.time, self.total_time, self.run_continuous, 0, 0, 0, self.vmax, self.amax, self.dx, *self.ts_and_cs)

class PidParams(Glob):
    
    # Unique class ID
    id = GlobID.PidParams
    
    # Controller IDs. Text labels so can show on form.
    controllers = {0 : "Left Wheel Speed",
                   1 : "Right Wheel Speed",
                   2 : "Yaw",
                   3 : "Left Motor Current",
                   4 : "Right Motor Current",
                   5 : "Balance Tilt",
                   6 : "Balance Position"}
    
    num_controllers = len(controllers)
    
    # Struct format for packing/unpacking. Little-endian no padding.
    data_format = '<' + ('f' * 7)
    
    def __init__(self, **kargs):
        '''Constructor'''
        self.instance = kargs.get('instance', 1)
        
        self.kp = kargs.get('kp', 0)
        self.ki = kargs.get('ki', 0)
        self.kd = kargs.get('kd', 0)
        self.integral_lolimit = -kargs.get('int_sat_limit', 0)
        self.integral_hilimit = kargs.get('int_sat_limit', 0)
        self.lolimit = -kargs.get('sat_limit', 0)
        self.hilimit = kargs.get('sat_limit', 0)

    def pack(self):
        
        return struct.pack(PidParams.data_format, self.kp, self.ki, self.kd, 
                           self.integral_lolimit, self.integral_hilimit,
                           self.lolimit, self.hilimit)

    def unpack(self, data_bytes):
        
        values = struct.unpack(PidParams.data_format, data_bytes)
        self.kp = values[0]
        self.ki = values[1]
        self.kd = values[2]
        self.integral_lolimit = values[3]
        self.integral_hilimit = values[4]
        self.lolimit = values[5]
        self.hilimit = values[6]
        
class Request(Glob):
    
    # Special ID for requesting globs
    id = GlobID.Request

    # Struct format for packing/unpacking. Little-endian no padding.
    data_format = '<B'
    
    def __init__(self, requested_id, instance=1):
        '''Constructor'''
        self.instance = instance
        self.requested_id = requested_id

    def pack(self):

        return struct.pack(Request.data_format, self.requested_id)
