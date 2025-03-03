# PortalBox.py for MicroPython on ESP32
# Hardware abstraction layer for managing peripherals

from machine import Pin, SoftSPI, I2C # type: ignore
import time

# Import local modules
from Button import KeypadButton
from LCD import I2cLcd
from BuzzerController import BuzzerController
from MFRC522 import MFRC522

# Default pin definitions for ESP32 (will be overridden by config.json if present)
DEFAULT_PIN_CONFIG = {
    "INTERLOCK_PIN": 9,
    "BUZZER_PIN": 6,
    "BUTTON_PIN": 20,
    "RELAY_PIN": 7,
    "NEOPIXEL_PIN": 13,
    "ROW_PIN": 17,
    "COL_PIN": 16,
    "LCD_I2C_ADDR": 0x20,
    "LCD_BUS": 0,
    "LCD_SDA": 18,
    "LCD_SCL": 19,
    "RFID_SDA": 3,
    "RFID_SCK": 2,
    "RFID_MOSI": 11,
    "RFID_MISO": 10
}

# Default colors
BLACK = "00 00 00"
RED = "FF 00 00"
YELLOW = "FF FF 00"

class PortalBox:
    '''
    Wrapper to manage peripherals on ESP32
    '''
    def __init__(self, settings):
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
        self.keypad_button = KeypadButton(self.config["ROW_PIN"], self.config["COL_PIN"])

        # Set up I2C for LCD
        self.i2c = I2C(
            self.config["LCD_BUS"], 
            sda=Pin(self.config["LCD_SDA"], Pin.PULL_UP), 
            scl=Pin(self.config["LCD_SCL"], Pin.PULL_UP), 
            freq=400000
        )
        self.lcd = I2cLcd(self.i2c, self.config["LCD_I2C_ADDR"], 2, 16)
        ###############################################################
        ##### THIS IS CURRENTLY HARD CODED
        # self.lcd.backlight_off()
        
        self.backlight=Pin(21,Pin.OUT)
        self.Blue=Pin(23,Pin.OUT)
        self.Green=Pin(15,Pin.OUT)
        self.Red=Pin(22,Pin.OUT)
        self.backlight.on()
        self.Red.on()
        self.Blue.on()
        self.Green.on()
        ###############################################################
        print("LCD initialized")
        
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
            self.write_to_lcd("Portal Box")
            time.sleep(0.5)
            self.write_to_lcd("Initialized")
            print("LCD test successful")
        except Exception as e:
            print(f"LCD test failed: {e}")

    def update(self):
        """
        Update method to be called in main loop
        Ensures buzzer effects are processed
        """
        self.buzzer.update()

    def write_to_lcd(self, message):
        '''
        Write a message to the LCD display
        @param message - string to display
        '''
        try:
            self.lcd.clear()
            self.lcd.putstr(message)
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
        Determine the current button state
        Returns True if the "1" key on the keypad is pressed
        '''
        return self.keypad_button.is_pressed()
    
    def has_button_been_pressed(self):
        '''
        Check if the "1" key on the keypad has been pressed since the last call
        Implements simple debouncing and edge detection
        '''
        return self.keypad_button.was_pressed()
    
    def read_RFID_card(self):
        '''
        @return a positive integer representing the uid from the card on a successful read, -1 otherwise
        '''
        print("READING RFID CARD")
        try:
            maxAttempts = 0
            while maxAttempts != 1:
                # print(maxAttempts)
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
        
        # Clear the LCD display
        try:
            self.lcd.clear()
            self.lcd.putstr("Shutting down...")
        except:
            pass
            
        print("Buzzer, display, and GPIO should be turned off")
        
    def turn_LCD_Blue(self):
        # self.lcd.backlight_off()
        self.Red.on()
        self.Blue.off()
        self.Green.on()
        
    def turn_LCD_Red(self):
        # self.lcd.backlight_off()
        self.Blue.on()
        self.Green.on()
        self.Red.off()
        
    def turn_LCD_Green(self):
        # self.lcd.backlight_off()
        self.Red.on()
        self.Blue.on()
        self.Green.off()
    