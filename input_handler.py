from machine import Pin, PWM
import utime
import _thread

# TODO: Queue multiple sounds
# TODO: Pre defined sounds / 'sound files'
# TODO: Button combinations? 

# --- BUTTONS ---
buttonL = Pin(2, Pin.IN, Pin.PULL_UP)
buttonM = Pin(3, Pin.IN, Pin.PULL_UP)
buttonR = Pin(4, Pin.IN, Pin.PULL_UP)
ALL_BUTTONS = (
    ("L", buttonL),
    ("M", buttonM),
    ("R", buttonR),
)
_debounce_delay = 10 # ms

# --- AUDIO ---
_buzzer = PWM(Pin(21))
_buzzer.freq(0)
_buzzer.duty_u16(0)

# Shared states
_button_states = {"L": False, "M": False, "R": False}
_button_edges = {"L_down": False, "L_up": False, "M_down": False, "M_up": False, "R_down": False, "R_up": False}
_sound_request = None # for play_sound() and _audio_task()
_active_sound = None
_state_lock = _thread.allocate_lock()

# For debounce
_last_button_values = {k: pin.value() == 0 for k, pin in ALL_BUTTONS}
_last_debounce_times = {k: utime.ticks_ms() for k, pin in ALL_BUTTONS}

def get_buttons():
    with _state_lock:
        return dict(_button_states)

def get_button_events():
    with _state_lock:
        ev = dict(_button_edges)
        for k in _button_edges: _button_edges[k] = False
    return ev

def play_sound(sound):
    global _sound_request
    with _state_lock:
        _sound_request = dict(sound)

def audio_stop():
    _buzzer.duty_u16(0)

def _button_task():
    now = utime.ticks_ms()
    for btn, pin in ALL_BUTTONS:
        current = pin.value() == 0  # Button pressed 
        last = _last_button_values[btn]
        if current != last:
            # (Re)start debounce timer
            _last_debounce_times[btn] = now
            _last_button_values[btn] = current
        elif utime.ticks_diff(now, _last_debounce_times[btn]) > _debounce_delay:
            # Stable state
            with _state_lock:
                old_state = _button_states[btn]
                if current != old_state:
                    if current:
                        _button_edges[f"{btn}_down"] = True
                    else:
                        _button_edges[f"{btn}_up"] = True
                    _button_states[btn] = current

def _audio_task():
    global _sound_request, _active_sound
    # Check for new sound
    with _state_lock:
        requested = _sound_request
        _sound_request = None
    if requested:
        # Start new sound
        _active_sound = dict(requested)
        _active_sound["start_ms"] = utime.ticks_ms()
    # Process active sound
    if _active_sound:
        elapsed = utime.ticks_diff(utime.ticks_ms(), _active_sound["start_ms"])
        if elapsed > _active_sound['length']:
            audio_stop()
            _active_sound = None
        else:
            t = elapsed / _active_sound['length']
            freq = int(_active_sound['freq_start'] +
                       (_active_sound['freq_end'] - _active_sound['freq_start'])*t)
            vol = int(_active_sound['vol_start'] +
                      (_active_sound['vol_end'] - _active_sound['vol_start'])*t)
            if freq < 20: freq = 20
            if vol < 0: vol = 0
            _buzzer.freq(freq)
            _buzzer.duty_u16(vol)

def _handler_thread():
    while True:
        _button_task()
        _audio_task()
        utime.sleep_ms(5)  # fast enough

def start_thread():
    _thread.start_new_thread(_handler_thread, ())