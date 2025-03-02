# BuzzerController.py for MicroPython on ESP32
# Controls the buzzer peripheral

from machine import Pin, PWM # type: ignore
import time

class BuzzerController:
    """
    BuzzerController for managing buzzer sounds on the ESP32
    """
    def __init__(self, pin=6, settings=None, enabled=True):
        """
        Initialize the buzzer controller
        
        :param pin: GPIO pin number for the buzzer
        :param settings: Configuration settings
        :param enabled: Whether the buzzer is enabled
        """
        self.enabled = enabled
        print(f"Initializing buzzer on pin {pin}, enabled: {enabled}")
        
        if settings and "display" in settings:
            # Override enabled status from settings if present
            if "enable_buzzer" in settings["display"]:
                # Check if the value is a string or boolean
                if isinstance(settings["display"]["enable_buzzer"], bool):
                    self.enabled = settings["display"]["enable_buzzer"]
                else:
                    self.enabled = not (str(settings["display"]["enable_buzzer"]).lower() in ("no", "false", "0"))
                print(f"Buzzer enabled from settings: {self.enabled}")
                
            # Check if PWM is enabled for the buzzer
            self.pwm_enabled = True
            if "buzzer_pwm" in settings["display"]:
                # Check if the value is a string or boolean
                if isinstance(settings["display"]["buzzer_pwm"], bool):
                    self.pwm_enabled = settings["display"]["buzzer_pwm"]
                else:
                    self.pwm_enabled = not (str(settings["display"]["buzzer_pwm"]).lower() in ("no", "false", "0"))
        else:
            self.pwm_enabled = True
        
        # Initialize the buzzer pin
        self.buzzer_pin = pin
        self.pin = Pin(self.buzzer_pin, Pin.OUT)
        
        # Initialize PWM if enabled
        if self.pwm_enabled:
            try:
                self.buzzer_pwm = PWM(self.pin)
                self.buzzer_pwm.freq(1000)  # Default frequency
                self.buzzer_pwm.duty(0)     # Start with 0% duty cycle (off)
                print("Buzzer PWM initialized")
            except Exception as e:
                print(f"PWM initialization failed: {e}")
                self.pwm_enabled = False
                
        # Track current state
        self.current_beep = None
        self.beep_start_time = 0
        self.beep_duration = 0
        self.beep_count = 0
        self.beep_interval = 0
        self.last_toggle_time = 0
        self.beep_state = False  # False = off, True = on
        
    def update(self):
        """
        Updates the beeper state, should be called in the main loop
        """
        if not self.enabled or self.current_beep is None:
            return
            
        current_time = time.ticks_ms()
        
        # Check if the entire beep sequence is done
        if time.ticks_diff(current_time, self.beep_start_time) >= self.beep_duration:
            self.stop_buzzer()
            self.current_beep = None
            return
            
        # Check if we need to toggle the beep state
        if time.ticks_diff(current_time, self.last_toggle_time) >= self.beep_interval:
            self.last_toggle_time = current_time
            
            if self.beep_state:
                # Turn off
                self.stop_buzzer()
                self.beep_state = False
            else:
                # Turn on
                self.start_buzzer(self.current_beep)
                self.beep_state = True
    
    def buzz_tone(self, freq=1000, length=0.2):
        """
        Play a single tone
        
        :param freq: Frequency in Hz
        :param length: Duration in seconds
        """
        if not self.enabled:
            return
            
        self.start_buzzer(freq)
        time.sleep(length)
        self.stop_buzzer()
    
    def beep(self, freq=1000, duration=2.0, beeps=10):
        """
        Start a beeping pattern
        
        :param freq: Frequency in Hz
        :param duration: Total duration in seconds
        :param beeps: Number of beeps
        """
        if not self.enabled:
            return
            
        self.current_beep = freq
        self.beep_start_time = time.ticks_ms()
        self.beep_duration = int(duration * 1000)  # Convert to ms
        self.beep_count = beeps
        
        # Calculate interval between toggles (half cycle)
        self.beep_interval = int(self.beep_duration / (2 * beeps))
        self.last_toggle_time = self.beep_start_time
        self.beep_state = True
        
        # Start the first beep
        self.start_buzzer(freq)
    
    def stop(self, stop_beeping=True):
        """
        Stop the buzzer
        
        :param stop_beeping: Whether to stop an ongoing beep pattern
        """
        if stop_beeping:
            self.current_beep = None
            
        self.stop_buzzer()
    
    def play_song(self, file_name):
        """
        Play a song from a file (not implemented in this version)
        
        :param file_name: File containing notes and durations
        """
        print(f"Song playback not implemented: {file_name}")
    
    def start_buzzer(self, freq=1000):
        """
        Start the buzzer at the specified frequency
        
        :param freq: Frequency in Hz
        """
        if not self.enabled:
            return
            
        if self.pwm_enabled:
            try:
                self.buzzer_pwm.freq(int(freq))
                self.buzzer_pwm.duty(512)  # 50% duty cycle
            except Exception as e:
                print(f"PWM error: {e}")
                self.pin.on()  # Fallback to digital output
        else:
            self.pin.on()
    
    def stop_buzzer(self):
        """
        Stop the buzzer
        """
        if self.pwm_enabled:
            try:
                self.buzzer_pwm.duty(0)  # 0% duty cycle (off)
            except Exception as e:
                print(f"PWM error: {e}")
                self.pin.off()  # Fallback to digital output
        else:
            self.pin.off()
    
    def shutdown_buzzer(self):
        """
        Clean up resources
        """
        self.stop_buzzer()
        if self.pwm_enabled:
            try:
                self.buzzer_pwm.deinit()
            except:
                pass