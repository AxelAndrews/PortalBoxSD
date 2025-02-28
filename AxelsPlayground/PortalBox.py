# PortalBox.py for MicroPython on ESP32
# Hardware abstraction layer for managing peripherals

from machine import Pin, PWM, SPI, SoftSPI, I2C
# In the imports section, add:
from Button import KeypadButton
import time
import gc
from LCD_lib import I2cLcd

# Import local modules
from AbstractController import BLACK
from BuzzerController import BuzzerController

# For ESP32 RFID implementation
from MFRC522 import MFRC522

# Pin definitions for ESP32
INTERLOCK_PIN = 9       # GPIO16
#BUTTON_LED_PIN = 17      # GPIO17
BUZZER_PIN = 6          # GPIO18
BUTTON_PIN = 20          # GPIO19
RELAY_PIN = 7           # GPIO21
#RFID_RST_PIN = 22        # GPIO22
NEOPIXEL_PIN = 13
ROW_PIN = 17  # Row 1 pin
COL_PIN = 16  # Column 1 pin

# The MCP23008 has a jumper selectable address: 0x20 - 0x27
LCD_I2C_ADDR = 0x20
BUS = 0
LCD_SDA = Pin(18, Pin.PULL_UP)
LCD_SCL = Pin(19, Pin.PULL_UP)

# RFID SPI pins
sda = Pin(3, Pin.OUT)
sck = Pin(2, Pin.OUT)
mosi = Pin(11, Pin.OUT)
miso = Pin(10, Pin.OUT)
spi = SoftSPI(baudrate=100000, polarity=0, phase=0, sck=sck, mosi=mosi, miso=miso)


# Default color - black (off)
BLACK = "00 00 00"
RED = "FF 00 00"
YELLOW = "FF FF 00"

class PortalBox:
    '''
    Wrapper to manage peripherals on ESP32
    '''
    def __init__(self, settings):
        # Set up GPIO pins
        print("Setting up RFID PINS")
        self.interlock_pin = Pin(INTERLOCK_PIN, Pin.OUT)
        self.relay_pin = Pin(RELAY_PIN, Pin.OUT)
        self.keypad_button = KeypadButton(ROW_PIN, COL_PIN)

        # Set up I2C for LCD
        self.i2c = I2C(BUS, sda=LCD_SDA, scl=LCD_SCL, freq = 400000)
        self.lcd = I2cLcd(self.i2c, LCD_I2C_ADDR, 2, 16)
        print("LCD initialized")

        
        # Button press tracking
        # self.button_last_state = False
        # self.button_last_check = time.ticks_ms()
        
        # Setup the buzzer controller
        # self.buzzer_controller = BuzzerController(BUZZER_PIN, settings)
        
        # Turn on button LED
        # self.button_led_pin.on()
        
        # Reset the RFID card
        # self.rfid_rst_pin.off()
        
        # Power off equipment
        self.set_equipment_power_on(False)
        
        # Set up display
        # self.led_type = settings["display"]["led_type"]
        # if self.led_type == "DOTSTARS":
        #     print("Creating DotStar display controller")
        #     from .display.DotstarController import DotstarController
        #     self.display_controller = DotstarController()
        # elif self.led_type == "NEOPIXELS":
        #     print("Creating Neopixel display controller")
        #     from .display.NeopixelController import NeopixelController
        #     self.display_controller = NeopixelController()
        # else:
        #     print("No display driver!")
        #     self.display_controller = None
        
        # Get buzzer settings
        # self.buzzer_enabled = True
        # if "buzzer_enabled" in settings["display"]:
        #     if settings["display"]["buzzer_enabled"].lower() in ("no", "false", "0"):
        #         self.buzzer_enabled = False
        
        # Init RFID
        # self.rfid_rst_pin.on()  # Deassert reset
        time.sleep(0.1)
        
        # Create RFID reader
        print("Creating RFID reader")
        spi = SPI(1, baudrate=2500000, polarity=0, phase=0, sck=sck, mosi=mosi, miso=miso)
        self.RFIDReader = MFRC522(spi=spi, cs=sda)
        
        # Setup state
        self.sleepMode = False
        self.outlist = [0] * 64  # RFID register tracking
        self.flash_signal = False
        self.flash_task = None

    def write_to_lcd(self, message):
        '''
        Write a message to the LCD display
        @param message - string to display
        '''
        self.lcd.clear()
        self.lcd.putstr(message)
        
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
    
    # In the get_button_state method:
    def get_button_state(self):
        '''
        Determine the current button state
        Returns True if the "1" key on the keypad is pressed
        '''
        return self.keypad_button.is_pressed()
    
    # In the has_button_been_pressed method:
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
            maxAttempts=0
            while maxAttempts != 1:
                # print(maxAttempts)
                rdr = MFRC522(spi, sda)
                uid = ""
                (stat, tag_type) = rdr.request(rdr.REQIDL)
                if stat == rdr.OK:
                    (stat, raw_uid) = rdr.anticoll()
                    if stat == rdr.OK:
                        uid = ("0x%02x%02x%02x%02x" % (raw_uid[0], raw_uid[1], raw_uid[2], raw_uid[3]))
                        return uid
                maxAttempts+=1
            return -1
        except KeyboardInterrupt:
            print("Bye")
            return -1
    
    # def wake_display(self):
    #     if self.display_controller:
    #         self.display_controller.wake_display()
    #     else:
    #         print("PortalBox wake_display failed")
    
    # def sleep_display(self):
    #     '''
    #     Sets LED display to indicate the box is in a low power mode
    #     '''
    #     self.stop_flashing()
    #     if self.display_controller:
    #         self.display_controller.sleep_display()
    #     else:
    #         print("PortalBox sleep_display failed")
    
    # def set_display_color(self, color=BLACK, stop_flashing=True):
    #     '''
    #     Set the entire strip to specified color
    #     @param color - hex string with color to set ("RR GG BB"). Defaults to LEDs off
    #     '''
    #     self.wake_display()
    #     if stop_flashing:
    #         self.stop_flashing()
        
    #     if self.display_controller:
    #         # Convert hex string to bytes
    #         if isinstance(color, str):
    #             color = bytes.fromhex(color)
    #         self.display_controller.set_display_color(color)
    #     else:
    #         print("PortalBox set_display_color failed")
    
    # def set_display_color_wipe(self, color=BLACK, duration=1000):
    #     '''
    #     Set the entire strip to specified color using a "wipe" effect
    #     @param color - color to set. Defaults to LEDs off
    #     @param duration - milliseconds for the effect
    #     '''
    #     self.wake_display()
    #     if self.display_controller:
    #         # Convert hex string to bytes if needed
    #         if isinstance(color, str):
    #             color = bytes.fromhex(color)
    #         self.display_controller.set_display_color_wipe(color, duration)
    #     else:
    #         print("PortalBox color_wipe failed")
    
    # def flash_display(self, color, duration=2000, flashes=10, end_color=BLACK):
    #     """
    #     Flash color across all display pixels multiple times
    #     @param color - color to flash
    #     @param duration - milliseconds for entire effect
    #     @param flashes - number of flashes during duration
    #     @param end_color - color to end with
    #     """
    #     self.wake_display()
        
        # if self.display_controller:
        #     # Create and start flash task
        #     self.stop_flashing()  # Stop any existing flash
            
        #     if self.led_type == "NEOPIXELS":
        #         # Start flash manually in a loop
        #         self.flash_signal = True
        #         self._flash_thread(color, duration, flashes, end_color)
        #     elif self.led_type == "DOTSTARS":
        #         # Use controller's flash method
        #         if isinstance(color, str):
        #             color = bytes.fromhex(color)
        #         self.display_controller.flash_display(color, duration, flashes)
        # else:
        #     print("PortalBox flash_display failed")
    
    # def _flash_thread(self, color, duration, flashes, end_color):
    #     """
    #     Perform the flashing effect (called directly, no threading in MicroPython)
    #     """
    #     start_time = time.ticks_ms()
    #     interval = duration / flashes
        
    #     if isinstance(color, str):
    #         color = bytes.fromhex(color)
    #     if isinstance(end_color, str):
    #         end_color = bytes.fromhex(end_color)
        
    #     while self.flash_signal and time.ticks_diff(time.ticks_ms(), start_time) < duration:
    #         # Toggle between colors
    #         self.set_display_color(color, False)
    #         time.sleep(interval/2000)  # Half interval with first color
            
    #         if not self.flash_signal:
    #             break
                
    #         self.set_display_color(end_color, False)
    #         time.sleep(interval/2000)  # Half interval with second color
            
    #         # Allow other tasks to run
    #         gc.collect()
    
    # def stop_flashing(self):
    #     """
    #     Stops the flashing effect
    #     """
    #     self.flash_signal = False
    
    # def buzz_tone(self, freq, length=0.2, stop_song=False, stop_beeping=False):
    #     """
    #     Plays the specified tone on the buzzer for the specified length
    #     """
    #     if self.buzzer_enabled:
    #         self.buzzer_controller.buzz_tone(freq, length, stop_song, stop_beeping)
    
    # def start_beeping(self, freq, duration=2.0, beeps=10):
    #     """
    #     Starts beeping for the duration with the given number of beeps
    #     """
    #     if self.buzzer_enabled:
    #         self.buzzer_controller.beep(freq, duration, beeps)
    
    # def stop_buzzer(self, stop_singing=False, stop_buzzing=False, stop_beeping=False):
    #     """
    #     Stops the specified effect(s) on the buzzer
    #     """
    #     self.buzzer_controller.stop(stop_singing, stop_buzzing, stop_beeping)
    
    # def beep_once(self):
    #     """
    #     Beeps the buzzer once for a default freq and length
    #     """
    #     self.buzz_tone(800, 0.1)
    
    def cleanup(self):
        """
        Clean up resources before shutting down
        """
        print("PortalBox.cleanup() starts")
        # self.buzzer_controller.shutdown_buzzer()
        # self.set_display_color(BLACK, False)
        
        # Turn off all pins
        self.relay_pin.off()
        self.interlock_pin.off()
        #self.button_led_pin.off()
        
        print("Buzzer, display, and GPIO should be turned off")