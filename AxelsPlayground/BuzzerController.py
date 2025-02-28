"""
BuzzerController.py for MicroPython - ESP32 version
Based on original Raspberry Pi implementation
"""
import time
from machine import Pin, PWM # type: ignore

# Default values
DEFAULT_TONE = 800.0
DEFAULT_DUTY = 512  # PWM range in ESP32 is 0-1023
GPIO_BUZZER_PIN = 18  # Change to your ESP32 pin

# Time interval for checking buzzer state
LOOP_MS = 100

# Musical notes frequencies
NOTES_4TH_OCTAVE = {
    "C":  261.63,
    "Db": 277.18,
    "D":  293.66,
    "Eb": 311.13,
    "E":  329.63,
    "F":  349.23,
    "Gb": 369.99,
    "G":  392,
    "Ab": 415.3,
    "A":  440,
    "Bb": 466.16,
    "B":  493.88
}

class BuzzerController:
    """
    Buzzer controller for ESP32 using MicroPython
    """
    def __init__(self, buzzer_pin=GPIO_BUZZER_PIN, settings={}):
        """
        Initialize the buzzer controller
        """
        self.buzzer_pin = buzzer_pin
        
        # Check if PWM is enabled in settings
        pwm_enabled = True
        if settings and "display" in settings and "buzzer_pwm" in settings["display"]:
            if settings["display"]["buzzer_pwm"].lower() in ("no", "false", "0"):
                pwm_enabled = False
        
        # Initialize the buzzer state
        self.pwm_buzzer = pwm_enabled
        self.buzzer = None
        self.buzzer_pin_obj = Pin(self.buzzer_pin, Pin.OUT)
        
        # Initialize the buzzer effects state
        self.is_singing = False
        self.song_list = []
        
        self.is_buzzing = False
        self.buzz_info = {
            "freq": -1,
            "loops_remaining": 0,
            "start_time": 0
        }
        
        self.is_beeping = False
        self.beep_info = {
            "freq": -1,
            "duration_ms": 0,
            "wait_ms": 0,
            "effect_time": 0,
            "start_time": 0
        }
        
        # State variables
        self.state = False  # Is buzzer currently on?
        self.last_update = time.ticks_ms()
        
        # Start task for handling buzzer effects
        self._setup_buzzer_effect_handler()
    
    def _setup_buzzer_effect_handler(self):
        """
        Setup a timer or task to periodically check buzzer state
        In MicroPython we can't use multiprocessing, so we'll call update
        from main loop instead
        """
        pass  # This will be called from main loop
    
    def update(self):
        """
        Update buzzer state - call this periodically from main loop
        """
        now = time.ticks_ms()
        elapsed = time.ticks_diff(now, self.last_update)
        
        if elapsed >= LOOP_MS:
            self.last_update = now
            self._update_buzzer_state()
    
    def _update_buzzer_state(self):
        """
        Update the buzzer state based on current effects
        """
        # Handle song playback
        if self.is_singing and self.song_list:
            freq, length = self.song_list[0]
            
            # Turn off buzzer if freq <= 0 and it's currently on
            if freq <= 0 and self.state:
                self.stop_buzzer()
            # Turn on buzzer if freq > 0 and it's currently off
            elif freq > 0 and not self.state:
                self.start_buzzer(freq)
            
            # Decrease note duration
            self.song_list[0][1] -= 1
            
            # Remove note if duration is complete
            if self.song_list[0][1] <= 0:
                self.song_list.pop(0)
                
            # End singing if no more notes
            if not self.song_list:
                self.stop_buzzer()
                self.is_singing = False
        
        # Handle beeping effect
        elif self.is_beeping:
            now = time.ticks_ms()
            elapsed = time.ticks_diff(now, self.beep_info["start_time"])
            
            if elapsed < self.beep_info["duration_ms"]:
                # Calculate which phase we're in (on or off)
                phase = (elapsed // self.beep_info["wait_ms"]) % 2
                
                # Even phase = on, Odd phase = off
                if phase == 0 and not self.state:
                    self.start_buzzer(self.beep_info["freq"])
                elif phase == 1 and self.state:
                    self.stop_buzzer()
            else:
                # Beeping complete
                self.stop_buzzer()
                self.is_beeping = False
        
        # Handle single buzz
        elif self.is_buzzing:
            now = time.ticks_ms()
            elapsed = time.ticks_diff(now, self.buzz_info["start_time"])
            duration = self.buzz_info["loops_remaining"] * LOOP_MS / 1000
            
            if elapsed < duration * 1000:
                if not self.state:
                    self.start_buzzer(self.buzz_info["freq"])
            else:
                self.stop_buzzer()
                self.is_buzzing = False
        
        # If no effect is active, ensure buzzer is off
        elif not (self.is_buzzing or self.is_beeping or self.is_singing):
            if self.state:
                self.stop_buzzer()
    
    def play_song(self, file_name, sn_len=0.1, spacing=0.05):
        """
        Play a song from a file
        """
        self.stop(True, True, True)
        self.is_singing = True
        self.song_list = self._create_song_list(file_name, sn_len, spacing)
    
    def _create_song_list(self, file_name, sn_len=0.1, spacing=0.05):
        """
        Parse a song file into a list of [frequency, duration] pairs
        """
        try:
            song_list = []
            loop_spacing = int((spacing * 1000) // LOOP_MS)
            if loop_spacing < 1:
                loop_spacing = 1
                
            with open(file_name, "r") as song_file:
                for line in song_file:
                    try:
                        split_line = line.strip().split(",")
                        if len(split_line) != 2:
                            continue
                            
                        note_oct = split_line[0]
                        
                        # Determine if note is flat
                        if len(note_oct) > 1 and note_oct[1] == "b":
                            note = note_oct[0:2]
                            octave = int(note_oct[2])
                        else:
                            note = note_oct[0]
                            octave = int(note_oct[1])
                            
                        # Calculate frequency relative to 4th octave
                        freq = NOTES_4TH_OCTAVE[note] * (2**(octave-4))
                        
                        # Calculate note length
                        length = float(split_line[1]) * sn_len
                        
                        # Convert to loop iterations
                        loop_length = int((length * 1000) // LOOP_MS)
                        if loop_length < 1:
                            loop_length = 1
                        
                        # Add note and spacing to song list
                        song_list.append([freq, loop_length])
                        song_list.append([-1, loop_spacing])  # Silence between notes
                    except (ValueError, IndexError, KeyError) as e:
                        print(f"Error parsing note: {line.strip()} - {e}")
                        continue
                        
            return song_list
            
        except Exception as e:
            print(f"Error loading song file: {e}")
            return []
    
    def buzz_tone(self, freq, length=0.2, stop_song=False, stop_beeping=False):
        """
        Play a single tone for specified length
        """
        if stop_song:
            self.is_singing = False
        
        if stop_beeping:
            self.is_beeping = False
        
        self.is_buzzing = True
        self.buzz_info = {
            "freq": float(freq),
            "loops_remaining": int((float(length) * 1000) // LOOP_MS),
            "start_time": time.ticks_ms()
        }
    
    def beep(self, freq, duration=2.0, beeps=10):
        """
        Beep at a specific frequency for a given duration with specified number of beeps
        """
        self.is_singing = False
        self.is_buzzing = False
        self.is_beeping = True
        
        duration_ms = int(duration * 1000)
        wait_ms = duration_ms // (2 * beeps)
        wait_ms = int((wait_ms + (LOOP_MS // 2)) // LOOP_MS * LOOP_MS)
        
        if wait_ms < LOOP_MS:
            wait_ms = LOOP_MS
        
        total_duration = wait_ms * 2 * beeps
        
        self.beep_info = {
            "freq": float(freq),
            "duration_ms": total_duration,
            "wait_ms": wait_ms,
            "effect_time": 0,
            "start_time": time.ticks_ms()
        }
    
    def stop(self, stop_singing=False, stop_buzzing=False, stop_beeping=False):
        """
        Stop specified buzzer effects
        """
        if stop_singing:
            self.is_singing = False
        
        if stop_buzzing:
            self.is_buzzing = False
        
        if stop_beeping:
            self.is_beeping = False
        
        if not (self.is_singing or self.is_buzzing or self.is_beeping):
            self.stop_buzzer()
    
    def start_buzzer(self, freq=DEFAULT_TONE, duty=DEFAULT_DUTY):
        """
        Start the buzzer at specified frequency and duty cycle
        """
        if not self.state:
            self.state = True
            
            if self.pwm_buzzer:
                # Clean up any existing PWM
                if self.buzzer:
                    self.buzzer.deinit()
                
                # Initialize new PWM instance with current frequency
                self.buzzer = PWM(self.buzzer_pin_obj, freq=int(freq), duty=duty)
            else:
                self.buzzer_pin_obj.on()
    
    def stop_buzzer(self):
        """
        Stop the buzzer
        """
        if self.state:
            self.state = False
            
            if self.pwm_buzzer and self.buzzer:
                self.buzzer.deinit()
                self.buzzer = None
            else:
                self.buzzer_pin_obj.off()
    
    def shutdown_buzzer(self):
        """
        Completely shut down buzzer controller
        """
        self.stop(True, True, True)
        self.stop_buzzer()
        
        # Clean up resources
        if self.buzzer:
            self.buzzer.deinit()
            self.buzzer = None