import machine
import time
from pcf8574 import PCF8574

# I2C initialization with SCL on Pin 7 and SDA on Pin 6
i2c = machine.SoftI2C(scl=machine.Pin(7), sda=machine.Pin(6), freq=10000)

# I2C Address of PCF8574 GPIO Expander
I2C_ADDR = 0x34

# Initialize PCF8574
pcf = PCF8574(i2c, I2C_ADDR)

# Keypad layout: 4x4 matrix
keypad_keys = [
    ['1', '2', '3', 'A'],
    ['4', '5', '6', 'B'],
    ['7', '8', '9', 'C'],
    ['*', '0', '#', 'D']
]

# Pin mappings for rows (0 to 3) and columns (4 to 7) on the PCF8574
rows = [pcf.pin(0), pcf.pin(1), pcf.pin(2), pcf.pin(3)]  # PCF8574 pins for rows
cols = [pcf.pin(4), pcf.pin(5), pcf.pin(6), pcf.pin(7)]  # PCF8574 pins for columns

# Function to set all columns high (inactive)
def set_cols_high():
    for col in cols:
        col.on()

# Function to scan the keypad and detect pressed keys
def scan_keypad():
    # Iterate through each row
    for row_index, row in enumerate(rows):
        row.off()  # Set the current row to LOW
        time.sleep(0.01)  # Wait for the signal to stabilize

        # Check each column
        for col_index, col in enumerate(cols):
            if not col.value():  # If the column is LOW, the key is pressed
                key = keypad_keys[row_index][col_index]
                print(f"Key pressed: {key}")
                return key  # Return the key that was pressed

        row.on()  # Set the current row back to HIGH

    set_cols_high()  # Set all columns back to high (inactive)
    return None  # No key is pressed

# Main function to run the keypad scanner
def main():
    while True:
        key = scan_keypad()
        if key:
            print(f"Detected key: {key}")
        time.sleep(0.1)

# Run the main function
main()
