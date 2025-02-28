import time
import machine 
from machine import Pin
import array

# Keypad configuration for a 3x4 matrix
cols = [Pin(x, Pin.IN, Pin.PULL_UP) for x in (21, 20, 19, 18)]  # MicroPython pin numbers
rows = [Pin(x, Pin.OUT) for x in (17, 15, 23, 22)]

# Define the key map (rows x columns)
keys = ((1, 2, 3, 'A'), (4, 5, 6, 'B'), (7, 8, 9, 'C'), ('*', 0, '#', 'D'))

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

while True:
    pressed_keys = scan_keypad()
    if pressed_keys:
        print("Pressed:", pressed_keys)
    time.sleep(0.1)     

#Keypad hold 100 Hrz 
# Use interrupts, cannot allocate mem, use an array and modify it.
# When you do python assignments, it like to allocate new varaibles. You only want to make modifications
# Handle Debouncing We can use an RC circuit. 

# from machine import Pin, SoftI2C
# from machine_i2c_lcd import I2cLcd
# from time import sleep

# # Define the LCD I2C address and dimensions
# I2C_ADDR = 0x27
# I2C_NUM_ROWS = 2
# I2C_NUM_COLS = 16

# # Initialize I2C and LCD objects
# i2c = SoftI2C(sda=Pin(20), scl=Pin(21), freq=400000)

# # for ESP8266, uncomment the following line
# # i2c = SoftI2C(sda=Pin(21), scl=Pin(20), freq=400000)

# lcd = I2cLcd(i2c, I2C_ADDR, I2C_NUM_ROWS, I2C_NUM_COLS)

# lcd.putstr("It's working :)")
# sleep(4)

# try:
#     while True:
#         # Clear the LCD
#         lcd.clear()
#         # Display two different messages on different lines
#         # By default, it will start at (0,0) if the display is empty
#         lcd.putstr("Hello World!")
#         sleep(2)
#         lcd.clear()
#         # Starting at the second line (0, 1)
#         lcd.move_to(0, 1)
#         lcd.putstr("Hello World!")
#         sleep(2)

# except KeyboardInterrupt:
#     # Turn off the display
#     print("Keyboard interrupt")
#     lcd.backlight_off()
#     lcd.display_off()

# from machine import Pin, SoftI2C
# from lib_lcd1602_2004_with_i2c import LCD
# scl_pin = 21 # write your own pin number
# sda_pin = 20 # write your own pin number
# lcd = LCD(SoftI2C(scl=Pin(scl_pin), sda=Pin(sda_pin), freq=100000))
# lcd.puts("Hello, World!")