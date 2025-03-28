# KeypadButton.py - Handles matrix keypad "1" button for PortalBox ESP32
from machine import Pin
import time

class KeypadButton:
    """Handles keypad button "1" input with debouncing and edge detection"""
    
    def __init__(self, row_pin, col_pin):
        """
        Initialize matrix keypad "1" button monitoring
        
        Args:
            row_pin: GPIO pin number for row 1
            col_pin: GPIO pin number for column 1
        """
        # Configure GPIO pins
        self.row = Pin(row_pin, Pin.OUT, value=0)  # Row pin as output, initially LOW
        self.col = Pin(col_pin, Pin.IN, Pin.PULL_DOWN)  # Column pin as input with pull-down
        
        self.last_state = False
        self.last_check = time.ticks_ms()
        self.debounce_ms = 50  # Debounce time in milliseconds
    
    def is_pressed(self):
        """
        Check if the "1" key is currently pressed
        
        Returns:
            True if "1" key is pressed, False otherwise
        """
        # Set row high to check button
        self.row.value(1)
        time.sleep(0.001)  # Short delay for electrical stability
        
        # Read column value (HIGH if button is pressed)
        pressed = bool(self.col.value())
        
        # Return row to low state
        self.row.value(0)
        
        return pressed
    
    def was_pressed(self):
        """
        Check if "1" key has been pressed since the last call
        Implements debouncing and rising edge detection
        
        Returns:
            True if "1" key was pressed, False otherwise
        """
        current_state = self.is_pressed()
        current_time = time.ticks_ms()
        
        # Only check if enough time has passed (debounce)
        if time.ticks_diff(current_time, self.last_check) > self.debounce_ms:
            # Detect rising edge (button press)
            if current_state and not self.last_state:
                self.last_state = current_state
                self.last_check = current_time
                return True
            
            # Update state for next check
            self.last_state = current_state
            self.last_check = current_time
        
        return False