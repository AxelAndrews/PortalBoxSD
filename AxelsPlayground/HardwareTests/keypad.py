"""
MicroPython library for 3x4 matrix keypad on ESP32-C6 DevKit
Row pins: 1, 2, 3, 4
Column pins: 5, 6, 7
Key layout:
    [[1, 2, 3],
     [4, 5, 6],
     [7, 8, 9],
     [*, 0, #]]
"""

from machine import Pin
import time

class KeyPad:
    def __init__(self, row_pins, col_pins):
        """
        Initialize the keypad with row and column pins.
        
        Args:
            row_pins (list): List of GPIO pin numbers for rows
            col_pins (list): List of GPIO pin numbers for columns
        """
        # Reset all pins first to ensure clean state
        for pin in row_pins + col_pins:
            p = Pin(pin, Pin.IN)
            
        # Then set up pins with correct configuration
        self.row_pins = [Pin(pin, Pin.OUT) for pin in row_pins]
        self.col_pins = [Pin(pin, Pin.IN, Pin.PULL_DOWN) for pin in col_pins]
        
        # Keypad layout - corrected based on observed outputs
        self.keys = [
            ['4', '5', '6'],  # Row 0 correctly produces 4,5,6
            ['1', '2', '3'],  # Row 1 correctly produces 1,2,3
            ['7', '8', '9'],  # Row 2 should be 7,8,9
            ['*', '0', '#']   # Row 3 should be *,0,#
        ]
        
        # Initialize all rows as HIGH
        for row in self.row_pins:
            row.value(1)
    
    def scan(self):
        """
        Scan the keypad once and return the pressed key if any.
        
        Returns:
            str or None: The pressed key or None if no key is pressed
        """
        for i, row in enumerate(self.row_pins):
            # Set all rows to HIGH first
            for r in self.row_pins:
                r.value(1)
                
            # Then set the current row to LOW
            row.value(0)
            
            # Small delay for stabilization
            time.sleep_ms(20)  # Increased delay for better stability
            
            # Check each column
            for j, col in enumerate(self.col_pins):
                if col.value() == 1:
                    # Key is pressed, set row back to HIGH and return key
                    row.value(1)
                    return self.keys[i][j]
            
            # Set the row back to HIGH
            row.value(1)
        
        # No key is pressed
        return None
    
    def read_key(self, blocking=True, debounce_time=50):
        """
        Read a key press with debounce.
        
        Args:
            blocking (bool): If True, wait until a key is pressed
            debounce_time (int): Debounce time in milliseconds
            
        Returns:
            str or None: The pressed key or None if no key is pressed and non-blocking
        """
        key = None
        
        while key is None:
            key = self.scan()
            
            if key is not None:
                # Wait for debounce
                time.sleep_ms(debounce_time)
                
                # Check if key is still pressed
                if key == self.scan():
                    # Wait until key is released
                    while self.scan() is not None:
                        time.sleep_ms(10)
                    
                    return key
                
                key = None
            
            # If non-blocking and no key pressed, return None
            if not blocking:
                return None
    
    def read_keys_sequence(self, max_length=4, timeout=5000):
        """
        Read a sequence of keys.
        
        Args:
            max_length (int): Maximum number of keys to read
            timeout (int): Timeout in milliseconds between key presses
            
        Returns:
            list: List of pressed keys
        """
        sequence = []
        last_press_time = time.ticks_ms()
        
        while len(sequence) < max_length:
            key = self.read_key(blocking=False)
            
            if key is not None:
                sequence.append(key)
                print(f"Key pressed: {key}")
                last_press_time = time.ticks_ms()
            
            # Check for timeout
            if time.ticks_diff(time.ticks_ms(), last_press_time) > timeout and len(sequence) > 0:
                break
                
            time.sleep_ms(10)
        
        return sequence