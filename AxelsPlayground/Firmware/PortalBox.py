# PortalBox.py for MicroPython on ESP32
# Hardware abstraction layer for managing peripherals

from machine import Pin, SoftSPI, I2C # type: ignore
import time

# Import local modules
from Keypad import scan_keypad  # Use existing Keypad module
from RGBLCD import RGBLCD
from BuzzerController import BuzzerController
from MFRC522 import MFRC522
from DotstarController import DotStar

# Default pin definitions for ESP32 (will be overridden by config.json if present)
DEFAULT_PIN_CONFIG = {
    "INTERLOCK_PIN": 9,
    "BUZZER_PIN": 6,
    "RELAY_PIN": 7,
    "DOTSTAR_DATA": 13,
    "DOTSTAR_CLOCK": 12,
    "LCD_TX": 5,
    "RFID_SDA": 3,
    "RFID_SCK": 2,
    "RFID_MOSI": 11,
    "RFID_MISO": 10,
}

# Define colors
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
MAGENTA = (255, 0, 255)
CYAN = (0, 255, 255)
WHITE = (255, 255, 255)

class PortalBox:
    '''
    Wrapper to manage peripherals on ESP32
    '''
    def __init__(self, settings):
        # Store service reference for later user info lookup
        self.service = None
        
        # Load pin configuration from settings if available
        self.config = DEFAULT_PIN_CONFIG.copy()
        
        # Override defaults with settings from config.json if available
        if 'pins' in settings:
            for key, value in settings['pins'].items():
                if key in self.config:
                    # Handle special case for hexadecimal values given as strings
                    if isinstance(value, str) and value.startswith("0x"):
                        try:
                            self.config[key] = int(value, 16)
                            print(f"Pin config override (hex): {key} = {value} → {self.config[key]}")
                        except ValueError:
                            print(f"Error parsing hex value: {value} for {key}")
                    else:
                        self.config[key] = value
                        print(f"Pin config override: {key} = {value}")
        
        print("Initializing hardware with configuration:")
        for key, value in self.config.items():
            print(f"  {key}: {value}")
            
        # Get buzzer settings
        self.buzzer_enabled = True
        if "display" in settings and "enable_buzzer" in settings["display"]:
            if str(settings["display"]["enable_buzzer"]).lower() in ("no", "false", "0"):
                self.buzzer_enabled = False
                print("Buzzer disabled in config")
            else:
                print("Buzzer enabled in config")
        
        # Set up GPIO pins
        print("Setting up pins")
        self.interlock_pin = Pin(self.config["INTERLOCK_PIN"], Pin.OUT)
        self.relay_pin = Pin(self.config["RELAY_PIN"], Pin.OUT)
        
        # Variables for keypad state tracking
        self.last_key_state = False
        self.last_keypad_check = time.ticks_ms()
        self.last_keys_pressed = []

        # Initialize the LCD with conservative timing
        self.lcd = RGBLCD(uart_id=1, tx_pin=5, baud_rate=9600, cols=16, rows=2)
        self.lcd.display_on()
        self.setScreenColor("white")
        print("LCD initialized")
        
        # # Initialize DotStar LEDs
        # self.dotstar = DotStar(
        #     spi_bus=1,
        #     data_pin=self.config["DOTSTAR_DATA"],
        #     clock_pin=self.config["DOTSTAR_CLOCK"],
        #     num_leds=15,
        #     brightness=16
        # )
        print("DotStar LEDs initialized")
        
        # Initialize buzzer with optional settings
        self.buzzer = BuzzerController(
            pin=self.config["BUZZER_PIN"], 
            settings=settings,
            enabled=self.buzzer_enabled
        )
        
        # Predefined buzzer patterns
        self.BEEP_PATTERNS = {
            'success': {'freq': 1000, 'duration': 0.2},
            'error':   {'freq': 500, 'duration': 0.5},
            'warning': {'freq': 750, 'duration': 0.3},
            'alert':   {'freq': 900, 'duration': 0.4}
        }
        print("Buzzer controller initialized, enabled:", self.buzzer_enabled)
        
        # Power off equipment
        self.set_equipment_power_on(False)
        
        # Initialize RFID
        print("Creating RFID reader")
        sda = Pin(self.config["RFID_SDA"], Pin.OUT)
        sck = Pin(self.config["RFID_SCK"], Pin.OUT)
        mosi = Pin(self.config["RFID_MOSI"], Pin.OUT)
        miso = Pin(self.config["RFID_MISO"], Pin.OUT)
        spi = SoftSPI(baudrate=100000, polarity=0, phase=0, sck=sck, mosi=mosi, miso=miso)
        self.RFIDReader = MFRC522(spi=spi, cs=sda)
        
        # Setup state
        self.sleepMode = False
        self.outlist = [0] * 64  # RFID register tracking
        self.flash_signal = False
        self.flash_task = None
        
        # Check if LCD is actually connected
        try:
            self.lcd_print("Portal Box")
            time.sleep(0.5)
            self.lcd_print("Initialized")
            print("LCD test successful")
        except Exception as e:
            print(f"LCD test failed: {e}")

    def set_service(self, service):
        """Store reference to the service for database access"""
        self.service = service

    def update(self):
        """
        Update method to be called in main loop
        Ensures buzzer effects are processed
        """
        self.buzzer.update()
        
        # # If DotStar animations are active, update them
        # if self.dotstar:
        #     self.dotstar.update_animations()

    def lcd_print(self, message):
        '''
        Write a message to the LCD display
        @param message - string to display
        '''
        try:
            # Split message into lines if it contains newlines
            lines = message.split('\n')
            
            # Clear the display
            self.lcd.clear()
            time.sleep(0.02)  # Short delay after clear
            
            # Print first line
            self.lcd.home()
            time.sleep(0.02)  # Short delay after home
            
            if len(lines) > 0:
                self.lcd.print(lines[0])
                time.sleep(0.02)  # Short delay after print
            
            # If there's a second line, position cursor and print it
            if len(lines) > 1:
                self.lcd.set_cursor(1, 2)  # Column 1, Row 2 (second line)
                time.sleep(0.02)  # Short delay after cursor positioning
                self.lcd.print(lines[1])
        except Exception as e:
            print(f"LCD write error: {e}")
        
    def set_equipment_power_on(self, state):
        '''
        Turn on/off power to the attached equipment by switching the relay and interlock
        @param (boolean) state - True to turn on power to equipment, False to turn off
        '''
        if state:
            print("Turning on equipment power and interlock")
            # Set relay and interlock pins
            self.relay_pin.on()
            self.interlock_pin.on()
        else:
            print("Turning off equipment power and interlock")
            # Reset relay and interlock pins
            self.relay_pin.off()
            self.interlock_pin.off()
    
    def get_button_state(self):
        '''
        Determine if "*" key is currently pressed
        Returns True if "*" key on the keypad is pressed
        '''
        try:
            keys_pressed = scan_keypad()
            return '*' in keys_pressed
        except Exception as e:
            print(f"Keypad scan error: {e}")
            return False
    
    def has_button_been_pressed(self):
        '''
        Check if the "*" key on the keypad has been pressed since the last call
        Implements simple debouncing and edge detection for * key
        '''
        try:
            current_time = time.ticks_ms()
            keys_pressed=""
            # Only check if enough time has passed (debounce)
            if time.ticks_diff(current_time, self.last_keypad_check) > 25:  # 25ms debounce
                # time.sleep(0.00001)
                keys_pressed = scan_keypad()
                
                # Check for "*" key press
                star_pressed_now = '*' in keys_pressed or "#" in keys_pressed
                star_pressed_before = '*' in self.last_keys_pressed or "#" in self.last_keys_pressed
                
                # Store current state for next check
                self.last_keys_pressed = keys_pressed
                self.last_keypad_check = current_time
                
                # Detect rising edge (button press)
                if star_pressed_now and not star_pressed_before:
                    print("* or # key pressed")
                    return [True, keys_pressed]
                        
            return [False, keys_pressed]
        except Exception as e:
            print(f"Button press check error: {e}")
            return [False,""]
    
    def read_RFID_card(self):
        '''
        @return a positive integer representing the uid from the card on a successful read, -1 otherwise
        '''
        print("READING RFID CARD")
        try:
            maxAttempts = 0
            while maxAttempts != 1:
                rdr = MFRC522(spi=self.RFIDReader.spi, cs=self.RFIDReader.cs)
                uid = ""
                (stat, tag_type) = rdr.request(rdr.REQIDL)
                if stat == rdr.OK:
                    (stat, raw_uid) = rdr.anticoll()
                    if stat == rdr.OK:
                        uid = ("0x%02x%02x%02x%02x" % (raw_uid[0], raw_uid[1], raw_uid[2], raw_uid[3]))
                        return uid
                maxAttempts += 1
            return -1
        except KeyboardInterrupt:
            print("Bye")
            return -1
        except Exception as e:
            print(f"RFID read error: {e}")
            return -1
    
    def beep_once(self, pattern='success'):
        """
        Trigger a single beep with a predefined or custom pattern
        
        :param pattern: Either a predefined pattern name or a dict with 'freq' and 'duration'
        """
        if not self.buzzer_enabled:
            print("Beep skipped - buzzer disabled")
            return
            
        if isinstance(pattern, str):
            # Use predefined pattern
            beep_config = self.BEEP_PATTERNS.get(pattern, self.BEEP_PATTERNS['success'])
        else:
            # Use custom pattern
            beep_config = pattern
        
        self.buzzer.buzz_tone(
            freq=beep_config.get('freq', 1000),
            length=beep_config.get('duration', 0.2)
        )
    
    def start_beeping(self, freq=500, duration=2.0, beeps=10):
        """
        Start a repeated beeping pattern
        
        :param freq: Frequency of beeps
        :param duration: Total duration of beeping
        :param beeps: Number of beeps
        """
        if not self.buzzer_enabled:
            print("Beeping skipped - buzzer disabled")
            return
            
        self.buzzer.beep(freq, duration, beeps)
    
    def stop_beeping(self):
        """
        Stop any ongoing beeping
        """
        self.buzzer.stop(stop_beeping=True)
    
    def play_alert_song(self, song_file='alert.txt'):
        """
        Play a predefined alert song
        
        :param song_file: Path to the song file
        """
        if not self.buzzer_enabled:
            print("Song skipped - buzzer disabled")
            return
            
        self.buzzer.play_song(song_file)
    
    def cleanup(self):
        """
        Clean up resources before shutting down
        """
        print("PortalBox.cleanup() starts")
        self.buzzer.shutdown_buzzer()
        
        # Turn off all pins
        self.relay_pin.off()
        self.interlock_pin.off()
        
        # # Turn off DotStar LEDs
        # if self.dotstar:
        #     self.dotstar.cleanup()
        
        # Clear the LCD display
        try:
            self.lcd.clear()
            self.lcd.home()
            self.lcd.print("Shutting down...")
        except:
            pass
            
        print("Buzzer, display, and GPIO should be turned off")
    
    def setScreenColor(self, color):
        """Set the LCD backlight color"""
        if color=="red":
            self.lcd.set_rgb_color(RED[0], RED[1], RED[2])
        elif color=="blue":
            self.lcd.set_rgb_color(BLUE[0], BLUE[1], BLUE[2])
        elif color=="green":
            self.lcd.set_rgb_color(GREEN[0], GREEN[1], GREEN[2])
        elif color=="magenta":
            self.lcd.set_rgb_color(MAGENTA[0], MAGENTA[1], MAGENTA[2])
        elif color=="yellow":
            self.lcd.set_rgb_color(YELLOW[0], YELLOW[1], YELLOW[2])
        elif color=="white":
            self.lcd.set_rgb_color(WHITE[0], WHITE[1], WHITE[2])
        elif color=="cyan":
            self.lcd.set_rgb_color(CYAN[0], CYAN[1], CYAN[2])