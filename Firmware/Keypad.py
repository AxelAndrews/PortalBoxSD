import time
import machine 
from machine import Pin
import array

# Keypad configuration for a 3x4 matrix
cols = [Pin(x, Pin.IN, Pin.PULL_UP) for x in (22, 15, 20)]  # MicroPython pin numbers
rows = [Pin(x, Pin.OUT) for x in (23, 18, 19, 21)]

# Define the key map (rows x columns)
keys = ((1, 2, 3), (4, 5, 6), (7, 8, 9), ('*', 0, '#'))

# Function to scan the keypad
def scan_keypad():
    # Create an empty array to store pressed keys
    pressed_keys = []
    
    for row_num, row in enumerate(rows):
        row.value(0)  # Drive the row low (active)
        for col_num, col in enumerate(cols):
            if col.value() == 0:  # If the column is low, it means the key is pressed
                pressed_keys.append(keys[row_num][col_num])
        row.value(1)  # Drive the row high (inactive)

    return pressed_keys

# while True:
#     pressed_keys = scan_keypad()
#     if pressed_keys:
#         print("Pressed:", pressed_keys)
#     time.sleep(0.1)     