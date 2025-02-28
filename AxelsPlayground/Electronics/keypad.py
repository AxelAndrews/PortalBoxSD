import time
import machine
from machine import Pin

# Keypad configuration for a 3x4 matrix
cols = [Pin(x, Pin.IN, Pin.PULL_UP) for x in (21, 20, 19, 18)]  # MicroPython pin numbers
rows = [Pin(x, Pin.OUT) for x in (17, 15, 23, 22)]

# Define the key map (rows x columns)
keys = ((1, 2, 3, 'A'), (4, 5, 6, 'B'), (7, 8, 9, 'C'), ('*', 0, '#', 'D'))

class Keypad:
    """
    A class to represent the 3x4 matrix keypad and handle key scanning.
    """

    def __init__(self):
        # Initialize the rows and columns of the keypad
        self.cols = [Pin(x, Pin.IN, Pin.PULL_UP) for x in (21, 20, 19, 18)]
        self.rows = [Pin(x, Pin.OUT) for x in (17, 15, 23, 22)]
        self.keys = ((1, 2, 3, 'A'), (4, 5, 6, 'B'), (7, 8, 9, 'C'), ('*', 0, '#', 'D'))

    def scan_keypad(self):
        """
        Scans the keypad for any pressed keys and returns the value of the key(s).
        """
        pressed_keys = []
        
        for row_num, row in enumerate(self.rows):
            row.value(0)
            for col_num, col in enumerate(self.cols):
                if col.value() == 0:  # If the column is low, it means the key is pressed
                    key = self.keys[row_num][col_num]  # Get the key from the map
                    pressed_keys.append(key)
                    print(f"Key pressed: {key}")  # Print the key pressed for feedback
            row.value(1)

        return pressed_keys

    def get_pressed_key(self):
        """
        Returns the first pressed key if any, otherwise None.
        """
        pressed_keys = self.scan_keypad()
        if pressed_keys:
            return pressed_keys[0]  # Return the first pressed key
        return None  # No key pressed

    