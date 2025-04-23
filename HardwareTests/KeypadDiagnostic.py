import machine
import time
import utime
from machine import Pin

# Define all possible pin combinations to test
# We'll modify this during debugging
ROW_PINS = [10, 21, 23, 15]  # GPIO pins for rows
COL_PINS = [22, 11, 19]     # GPIO pins for columns

# Initialize GPIO pins
def setup_pins():
    # Setup row pins as outputs (initially high)
    row_pins = []
    for pin in ROW_PINS:
        try:
            row_pins.append(Pin(pin, Pin.OUT, value=1))
            print(f"Row pin {pin} initialized successfully")
        except Exception as e:
            print(f"Error initializing row pin {pin}: {e}")
    
    # Setup column pins as inputs with pull-down resistors
    col_pins = []
    for pin in COL_PINS:
        try:
            col_pins.append(Pin(pin, Pin.IN, Pin.PULL_DOWN))
            print(f"Column pin {pin} initialized successfully")
        except Exception as e:
            print(f"Error initializing column pin {pin}: {e}")
    
    return row_pins, col_pins

def scan_raw_matrix(row_pins, col_pins):
    """
    Scan the keypad and print the raw row/column values.
    This helps determine the actual mapping of your keypad.
    """
    while True:
        # Scan each row/column combination
        for r, row_pin in enumerate(row_pins):
            # Set the current row low
            row_pin.value(0)
            
            # Check each column
            for c, col_pin in enumerate(col_pins):
                if col_pin.value():
                    # Key press detected
                    print(f"Key press detected at row {r} (pin {ROW_PINS[r]}), column {c} (pin {COL_PINS[c]})")
                    
                    # Wait for key release
                    while col_pin.value():
                        time.sleep_ms(10)
                    
                    print("Key released")
            
            # Set row back high before checking next row
            row_pin.value(1)
        
        # Small delay to prevent CPU from running at 100%
        time.sleep_ms(10)

def detect_keypad_layout():
    """
    A utility to help determine the actual keypad layout.
    This will ask you to press each key in sequence and record the row/column.
    """
    row_pins, col_pins = setup_pins()
    
    print("\n=== KEYPAD LAYOUT DETECTION ===")
    print("We'll detect your keypad's layout.")
    print("Press each key when prompted, from 1 to #.")
    print("This will help create a mapping for your specific keypad.")
    print("Press any key to start...")
    
    # Wait for initial keypress to begin
    wait_for_any_key(row_pins, col_pins)
    time.sleep_ms(500)  # Debounce
    
    # Expected keys in standard order
    expected_keys = [
        '1', '2', '3',
        '4', '5', '6',
        '7', '8', '9',
        '*', '0', '#'
    ]
    
    # Array to hold our detected mapping
    detected_mapping = []
    
    for key in expected_keys:
        print(f"\nPlease press key '{key}' on your keypad...")
        
        # Wait for a key press and record position
        r, c = wait_for_keypress(row_pins, col_pins)
        detected_mapping.append((r, c, key))
        
        print(f"Recorded: Key '{key}' at row {r}, column {c}")
        time.sleep_ms(500)  # Debounce
    
    # Create the KEYPAD_KEYS layout based on detected mapping
    print("\n=== DETECTED KEYPAD LAYOUT ===")
    
    # Initialize a 4x3 empty matrix
    keypad_layout = [[None for _ in range(3)] for _ in range(4)]
    
    # Fill in the detected keys
    for r, c, key in detected_mapping:
        keypad_layout[r][c] = key
    
    # Print the resulting layout
    print("Your KEYPAD_KEYS layout should be:")
    print("KEYPAD_KEYS = [")
    for row in keypad_layout:
        print(f"    {row},")
    print("]")
    
    print("\nAdd this to your code to fix the keypad mapping.")

def wait_for_any_key(row_pins, col_pins):
    """Wait for any key press"""
    while True:
        for r, row_pin in enumerate(row_pins):
            row_pin.value(0)
            for c, col_pin in enumerate(col_pins):
                if col_pin.value():
                    row_pin.value(1)
                    return
            row_pin.value(1)
        time.sleep_ms(10)

def wait_for_keypress(row_pins, col_pins):
    """Wait for a key press and return the row/column"""
    while True:
        for r, row_pin in enumerate(row_pins):
            row_pin.value(0)
            for c, col_pin in enumerate(col_pins):
                if col_pin.value():
                    # Wait for key release
                    while col_pin.value():
                        time.sleep_ms(10)
                    row_pin.value(1)
                    return r, c
            row_pin.value(1)
        time.sleep_ms(10)

def test_pin_continuity():
    """
    Simple test to check if pins are working correctly.
    Sets each row pin low one at a time, which should make
    the corresponding column pin read low if pressed.
    """
    row_pins, col_pins = setup_pins()
    
    print("\n=== PIN CONTINUITY TEST ===")
    print("This test will help verify your wiring.")
    print("For each row pin, press any key in that row when prompted.")
    print("Press any key to begin...")
    
    wait_for_any_key(row_pins, col_pins)
    time.sleep_ms(500)  # Debounce
    
    for r, row_pin in enumerate(row_pins):
        print(f"\nTesting row {r} (pin {ROW_PINS[r]}):")
        print(f"Press any key in row {r}...")
        
        # Start a timeout counter
        start_time = utime.ticks_ms()
        timeout = 10000  # 10 seconds
        
        detected = False
        
        while not detected and utime.ticks_diff(utime.ticks_ms(), start_time) < timeout:
            # Set current row low
            row_pin.value(0)
            
            # Check each column
            for c, col_pin in enumerate(col_pins):
                if col_pin.value():
                    print(f"✓ Connection detected between row {r} (pin {ROW_PINS[r]}) and column {c} (pin {COL_PINS[c]})")
                    detected = True
                    
                    # Wait for key release
                    while col_pin.value():
                        time.sleep_ms(10)
            
            # Set row back high before continuing
            row_pin.value(1)
            time.sleep_ms(10)
        
        if not detected:
            print(f"❌ No connection detected for row {r} (pin {ROW_PINS[r]}). Check wiring!")
    
    print("\nContinuity test complete.")

def main():
    print("=== Keypad Diagnostic Tool ===")
    print("Choose a test to run:")
    print("1. Raw Matrix Scan")
    print("2. Detect Keypad Layout")
    print("3. Test Pin Continuity")
    
    choice = "1"
    
    if choice == "1":
        row_pins, col_pins = setup_pins()
        print("Press keys on your keypad to see raw matrix positions.")
        print("Press Ctrl+C to exit.")
        scan_raw_matrix(row_pins, col_pins)
    elif choice == "2":
        detect_keypad_layout()
    elif choice == "3":
        test_pin_continuity()
    else:
        print("Invalid choice. Exiting.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nDiagnostic tool terminated by user.")
    except Exception as e:
        print(f"Error: {e}")