
from glob import PidParams

# Data capture parameters
DEFAULT_NUM_SAMPLES = 300
MIN_NUM_SAMPLES = 1
MAX_NUM_SAMPLES = 2000
FASTEST_CAPTURE_RATE = 5000.0 # Hz
DEFAULT_CAPTURE_RATE = FASTEST_CAPTURE_RATE / 50 # Hz

# Wave parameters
DEFAULT_WAVE_MAGNITUDE = 1
DEFAULT_WAVE_OFFSET = 0
DEFAULT_WAVE_FREQ = 1
DEFAULT_WAVE_DURATION = 5

# Manual command parameters
DEFAULT_MANUAL_COMMAND = 0
DEFAULT_MANUAL_INCREMENT = 1

def limit(val, min_val, max_val):
    
    val_type = type(val)
    if val > max_val:
        return val_type(max_val)
    if val < min_val:
        return val_type(min_val)
    return val

def try_parse(value, cast_type, default_value):
    
    try:
        value = cast_type(value)
    except ValueError:
        value = cast_type(default_value)
    return value

def validate_capture_parameters(view):
    
    rate = try_parse(view.get_capture_rate(), float, DEFAULT_CAPTURE_RATE)
    rate = limit(rate, 0.001, FASTEST_CAPTURE_RATE)
    samples = try_parse(view.get_capture_samples(), int, DEFAULT_NUM_SAMPLES)
    samples = limit(samples, MIN_NUM_SAMPLES, MAX_NUM_SAMPLES)

    # Account for the fact the MCU can only capture at certain rates.  
    scale = int(FASTEST_CAPTURE_RATE / rate)
    rate = FASTEST_CAPTURE_RATE / scale

    duration = samples / rate

    view.set_capture_rate(rate)
    view.set_capture_samples(samples)
    view.set_capture_duration(duration)
    
    return duration

def validate_wave_parameters(view):
    
    mag = try_parse(view.get_wave_mag(), float, DEFAULT_WAVE_MAGNITUDE)
    mag = limit(mag, 0, 1e10)
    offset = try_parse(view.get_wave_offset(), float, DEFAULT_WAVE_OFFSET)
    offset = limit(offset, -1e10, 1e10)
    freq = try_parse(view.get_wave_freq(), float, DEFAULT_WAVE_FREQ)
    freq = limit(freq, 0.00001, 1e10)
    duration = try_parse(view.get_wave_duration(), float, DEFAULT_WAVE_DURATION)
    duration = limit(duration, 0, 1e10)

    view.set_wave_mag(mag)
    view.set_wave_offset(offset)
    view.set_wave_freq(freq)
    view.set_wave_duration(duration)
    
def validate_pid_parameters(controller, send=False):
    
    view = controller.view
    
    view_params = view.get_pid_parameters()
    params = PidParams()
    params.kp = try_parse(view_params['kp'], float, 0)
    params.ki = try_parse(view_params['ki'], float, 0)
    params.kd = try_parse(view_params['kd'], float, 0)
    params.hilimit = try_parse(view_params['sat_limit'], float, 0)
    params.lolimit = -params.hilimit
    params.integral_hilimit = try_parse(view_params['int_sat_limit'], float, 0)
    params.integral_lolimit = -params.integral_hilimit

    view.set_pid_parameters(params)
    
    pid_idx = view.get_controller_index()
    params.instance = pid_idx + 1;
    
    if send:
        # Save before sending so we don't need to request new value.
        controller.pid_params[pid_idx] = params
        controller.link.send(params)
    
def validate_manual_command_parameters(view):
    
    command = try_parse(view.get_manual_command(), float, DEFAULT_MANUAL_COMMAND)
    command = limit(command, -1e10, 1e10)
    increment = try_parse(view.get_manual_command_increment(), float, DEFAULT_MANUAL_INCREMENT)
    increment = limit(increment, -1e10, 1e10)

    view.set_manual_command(command)
    view.set_manual_command_increment(increment)