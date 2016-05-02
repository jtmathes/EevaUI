
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
    RobotCommand = 15
    Wave = 17
    PidParams = 18
    Request = 19
    TaskTimingResult = 20

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
    
    forward = 1
    reverse = 2
    turn_right = 4
    turn_left = 8
    stop = 16
    
    possible_movements = [forward, reverse, turn_left, turn_right, stop]
    
    # Struct format for packing/unpacking. Little-endian no padding.
    data_format = '<Iff'
    
    def __init__(self, movement_commands=0, linear_velocity=0, angular_velocity=0, instance=1):
        '''Constructor'''
        self.instance = instance
        self.movement_commands = movement_commands
        self.linear_velocity = linear_velocity
        self.angular_velocity = angular_velocity

    def pack(self):

        return struct.pack(DrivingCommand.data_format, self.movement_commands, self.linear_velocity, self.angular_velocity)
    
class StatusData(Glob):
    
    # Unique class ID
    id = GlobID.StatusData
    
    # Struct format for packing/unpacking. Little-endian no padding.
    data_format = '<' + ('f' * 4) + ('B' * 4) + ('f' * 10) + 'i' + ('B' * 12)
    
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
        self.data["left_angular_velocity"] = math.degrees(values[14]) * 60.0 / 360.0  # rad/s to RPM
        self.data["right_angular_velocity"] = math.degrees(values[15]) * 60.0 / 360.0  # rad/s to RPM
        self.data["left_pwm"] = values[16] * 100  # to percentage
        self.data["right_pwm"] = values[17] * 100  # to percentage
        self.data["left_voltage"] = self.data["battery"] * self.data["left_pwm"] / 100.0
        self.data["right_voltage"] = self.data["battery"] * self.data["right_pwm"] / 100.0
        self.data["firmware_version"] = values[18]
        robot_id_bytes = values[19:31]
        self.data["robot_id"] = ''.join('{:02X}'.format(b) for b in robot_id_bytes)
            
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
    data_format = '<' + ('f' * 9)
    
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
    
    continue_action = 0
    restart_action = 1
    stop_action = 2
    
    # Struct format for packing/unpacking. Little-endian no padding.
    data_format = '<I200sI'
    
    def __init__(self, instance=1):
        '''Constructor'''
        self.instance = instance

    def unpack(self, data_bytes):
        
        self.action, self.message, valid = struct.unpack(AssertMessage.data_format, data_bytes)
        self.valid = bool(valid)

class DebugMessage(Glob):
    
    # Unique class ID
    id = GlobID.DebugMessage
    
    # Struct format for packing/unpacking. Little-endian no padding.
    data_format = '<200sI'
    
    def __init__(self, instance=1):
        '''Constructor'''
        self.instance = instance

    def unpack(self, data_bytes):
        
        self.message, valid = struct.unpack(DebugMessage.data_format, data_bytes)
        self.valid = bool(valid)

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
    experiments = [(0, "None"),
                   (1, "Wheel Linear Speed"),
                   (2, "Wheel Angular Position"),
                   (3, "Motor Voltage")]
    
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
    task_timing = 3
    
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
        # self.pad = [0, 0]
        self.mag = kargs.get('mag', 0)
        self.freq = kargs.get('freq', 1)
        self.duration = kargs.get('duration', 1)
        self.offset = kargs.get('offset', 0)
        self.time = kargs.get('wave_time', 0)
        self.total_time = 0
        self.run_continuous = kargs.get('run_continuous', False)
        # self.pad2 = [0, 0, 0]
        
        # Trapezoid parameters
        self.vmax = kargs.get('vmax', 0)
        self.amax = kargs.get('amax', 0)
        self.dx = kargs.get('dx', 0)
        self.ts_and_cs = [0] * 12  # calculated on robot
        
    def pack(self):

        return struct.pack(Wave.data_format, self.type, self.state, 0, 0, self.value, self.mag, self.freq, self.duration,
                           self.offset, self.time, self.total_time, self.run_continuous, 0, 0, 0, self.vmax, self.amax, self.dx, *self.ts_and_cs)

class PidParams(Glob):
    
    # Unique class ID
    id = GlobID.PidParams
    
    # Controller IDs. Text labels so can show on form.
    controllers = [(0, "Left Wheel Speed (m/s)"),
                   (1, "Right Wheel Speed (m/s)"),
                   (2, "Yaw (radians)"),
                   (3, "Balance Tilt (radians)"),
                   (4, "Balance Position (meters)"),
                   (5, "Line Following (meters)"),
                   (6, "Left Wheel Position (deg)"),
                   (7, "Right Wheel Position (deg)")]
    
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
        
        # Not part of actual glob.  Used so GUI can keep track which ones have been received.
        self.received = False

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
        
        # Mark that glob is now valid.
        self.received = True
        
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

class TaskTimingResult(Glob):
    
    # Unique class ID
    id = GlobID.TaskTimingResult
    
    # Struct format for packing/unpacking. Little-endian no padding.
    data_format = '<32sIfII' + (9 * 'I')
    
    def __init__(self, instance=1):
        '''Constructor'''
        self.instance = instance

    def unpack(self, data_bytes):
        
        values = struct.unpack(TaskTimingResult.data_format, data_bytes)
        
        self.task_name = values[0]
        
        self.timer_frequency = values[1]
        
        ticks2usec = 1.0e6 / self.timer_frequency
        
        self.recording_duration = values[2]
        self.execute_counts = values[3] 
        self.times_skipped = values[4]

        self.delay_usec_max = values[5] * ticks2usec
        self.delay_usec_min = values[6] * ticks2usec
        self.delay_usec_avg = values[7] * ticks2usec
        
        self.run_usec_max = values[8] * ticks2usec
        self.run_usec_min = values[9] * ticks2usec
        self.run_usec_avg = values[10] * ticks2usec
        
        self.interval_usec_max = values[11] * ticks2usec
        self.interval_usec_min = values[12] * ticks2usec
        self.interval_usec_avg = values[13] * ticks2usec
