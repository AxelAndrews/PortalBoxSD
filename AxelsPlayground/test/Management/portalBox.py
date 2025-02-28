import os
import time
import uthread
from machine import Pin
from time import sleep
from .display.AbstractController import BLACK
from .BuzzerController import BuzzerController
import logging

# Constants defining how peripherals are connected
GPIO_INTERLOCK_PIN = 11
GPIO_BUTTON_LED_PIN = 31
GPIO_BUZZER_PIN = 33
GPIO_BUTTON_PIN = 35
GPIO_SOLID_STATE_RELAY_PIN = 37
GPIO_RFID_NRST_PIN = 13
GPIO_RESET_BTN_PIN = 3

# Constants (MicroPython does not support the standard RPi constants)
BLACK = "00 00 00"

# # Utility functions
# def get_revision():
#     try:
#         with open("/proc/cpuinfo", "r") as file:
#             for line in file:
#                 if "Revision" in line:
#                     return line.split(":")[1].strip()
#     except:
#         return -1

# class PortalBox:
#     '''
#     Wrapper to manage peripherals
#     '''
#     # def __init__(self, settings):
#     def __init__(self):
#         self.is_pi_zero_w = "9000c1" == get_revision()

#         # Set up GPIO pins
#         self.interlock_pin = Pin(GPIO_INTERLOCK_PIN, Pin.OUT)
#         self.ssr_pin = Pin(GPIO_SOLID_STATE_RELAY_PIN, Pin.OUT)

#         # Set up buzzer controller
#         self.buzzer_controller = BuzzerController(GPIO_BUZZER_PIN, settings)

#         # Set up button LED (LED on for REV 3.x boards)
#         self.button_led_pin = Pin(GPIO_BUTTON_LED_PIN, Pin.OUT)
#         self.button_led_pin.value(1)  # Turn on LED

#         # Reset the RFID card
#         self.rfid_rst_pin = Pin(GPIO_RFID_NRST_PIN, Pin.OUT)
#         self.rfid_rst_pin.value(0)

#         # Setup the button
#         self.button_pin = Pin(GPIO_BUTTON_PIN, Pin.IN, Pin.PULL_DOWN)
        
#         # Set up display controller
#         self.led_type = settings["display"]["led_type"]
#         self.display_controller = None

#         # Initialize buzzer settings
#         self.buzzer_enabled = settings.get("display", {}).get("buzzer_enabled", True)

#         # Create RFID reader (Adapt this part as necessary for MicroPython)
#         self.RFIDReader = None  # You'll need to adapt your RFID code for MicroPython

#         # State initialization
#         self.sleepMode = False

#     def set_equipment_power_on(self, state):
#         '''
#         Turn on/off power to the attached equipment by switching on/off relay
#         and interlock.
#         '''
#         if state:
#             os.system("echo True > /tmp/running")
#         else:
#             os.system("echo False > /tmp/running")

#         self.ssr_pin.value(state)
#         self.interlock_pin.value(state)

#     def get_button_state(self):
#         '''
#         Determine the current button state
#         '''
#         return self.button_pin.value() == 1

#     def has_button_been_pressed(self):
#         '''
#         Check if the button has been pressed since the last call
#         '''
#         return self.button_pin.value() == 1

#     def read_RFID_card(self):
#         '''
#         Read an RFID card
#         '''
#         return 123456
    
#     def read_Pin(self):
#         '''
#         Read an Pin from the keypad
#         '''
#         return 1234

#     def set_display_color(self, color=BLACK):
#         '''
#         Set the entire display strip to the specified color.
#         '''
#         if self.display_controller:
#             self.display_controller.set_display_color(bytes.fromhex(color))
#         else:
#             logging.info("Display controller not initialized.")

#     def start_beeping(self, freq, duration=2.0, beeps=10):
#         '''
#         Start beeping for the duration with the given number of beeps
#         '''
#         if self.buzzer_enabled:
#             self.buzzer_controller.beep(freq, duration, beeps)

#     def stop_buzzer(self):
#         '''
#         Stops buzzer activity.
#         '''
#         self.buzzer_controller.stop()

#     def cleanup(self):
#         '''
#         Clean up resources.
#         '''
#         logging.info("Cleaning up resources.")
#         self.buzzer_controller.shutdown_buzzer()
#         self.set_display_color("00 00 00")  # Turn off display
#         self.interlock_pin.value(0)
#         self.ssr_pin.value(0)
#         os.system("echo False > /tmp/running")