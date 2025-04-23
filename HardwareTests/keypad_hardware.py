"""
Script to check the hardware connections of the keypad
Tests for basic connectivity and possible shorts between pins
"""

import time
from machine import Pin, ADC

# Define pin numbers
ROW_PINS = [1, 2, 3, 4]  # GPIO pins for rows
COL_PINS = [5, 6, 7]     # GPIO pins for columns

def init_pins():
    """Initialize all pins as inputs initially"""
    pins = {}
    for pin_num in ROW_PINS + COL_PINS:
        pins[pin_num] = Pin(pin_num, Pin.IN)
    return pins

def check_for_shorts():
    """Check for possible shorts between pins"""
    print("=== Checking for shorts between pins ===")
    pins = init_pins()
    
    # Test each pair of pins
    for i, pin1_num in enumerate(ROW_PINS + COL_PINS):
        for pin2_num in (ROW_PINS + COL_PINS)[i+1:]:
            # Configure first pin as output HIGH
            pin1 = Pin(pin1_num, Pin.OUT)
            pin1.value(1)
            
            # Configure second pin as input with pull-down
            pin2 = Pin(pin2_num, Pin.IN, Pin.PULL_DOWN)
            
            # Check if second pin reads HIGH (potential short)
            time.sleep_ms(10)  # Small delay for stabilization
            if pin2.value() == 1:
                print(f"⚠️ Possible short detected between pins {pin1_num} and {pin2_num}")
            
            # Reset pins to input
            pin1 = Pin(pin1_num, Pin.IN)
            pin2 = Pin(pin2_num, Pin.IN)
    
    print("Short circuit check completed")

def test_pin_state(pin_num):
    """Test the state of a specific pin"""
    # Test as input with pull-up
    pin = Pin(pin_num, Pin.IN, Pin.PULL_UP)
    time.sleep_ms(10)
    pull_up_value = pin.value()
    
    # Test as input with pull-down
    pin = Pin(pin_num, Pin.IN, Pin.PULL_DOWN)
    time.sleep_ms(10)
    pull_down_value = pin.value()
    
    # Reset to input
    pin = Pin(pin_num, Pin.IN)
    
    # Analyze results
    if pull_up_value == 1 and pull_down_value == 0:
        return "Normal"
    elif pull_up_value == 0 and pull_down_value == 0:
        return "Stuck LOW or grounded"
    elif pull_up_value == 1 and pull_down_value == 1:
        return "Stuck HIGH or connected to power"
    else:
        return "Unusual behavior"

def check_individual_pins():
    """Check each pin's state"""
    print("=== Checking individual pins ===")
    
    # Check each row pin
    print("\nRow pins:")
    for pin_num in ROW_PINS:
        state = test_pin_state(pin_num)
        print(f"Pin {pin_num}: {state}")
    
    # Check each column pin
    print("\nColumn pins:")
    for pin_num in COL_PINS:
        state = test_pin_state(pin_num)
        print(f"Pin {pin_num}: {state}")

def check_keypad_connectivity():
    """Test if keypad is connected correctly"""
    print("=== Testing keypad connectivity ===")
    print("Press any key on the keypad...")
    
    # Configure rows as outputs (LOW)
    rows = [Pin(pin, Pin.OUT) for pin in ROW_PINS]
    for row in rows:
        row.value(0)
    
    # Configure columns as inputs with pull-up
    cols = [Pin(pin, Pin.IN, Pin.PULL_UP) for pin in COL_PINS]
    
    # Wait for any key press
    detected = False
    start_time = time.time()
    timeout = 10  # 10 seconds timeout
    
    try:
        while not detected and (time.time() - start_time) < timeout:
            # Check if any column is LOW (key pressed)
            for i, col in enumerate(cols):
                if col.value() == 0:
                    print(f"Key press detected on column {i} (Pin {COL_PINS[i]})")
                    detected = True
            
            time.sleep_ms(100)
        
        if not detected:
            print("No key press detected. Check if keypad is connected properly.")
        
        # Now test rows one by one
        if detected:
            print("\nNow testing each row. Press a key in each row when prompted...")
            
            # Reset rows and columns
            for row in rows:
                row = Pin(row.id(), Pin.IN)
            
            for col in cols:
                col = Pin(col.id(), Pin.IN)
            
            # Test each row
            for i, row_pin in enumerate(ROW_PINS):
                row = Pin(row_pin, Pin.OUT)
                row.value(1)  # Set HIGH
                
                # Configure columns as inputs with pull-down
                cols = [Pin(pin, Pin.IN, Pin.PULL_DOWN) for pin in COL_PINS]
                
                print(f"\nPress any key in row {i}...")
                
                # Wait for key press
                row_detected = False
                start_time = time.time()
                
                while not row_detected and (time.time() - start_time) < timeout:
                    for j, col in enumerate(cols):
                        if col.value() == 1:
                            print(f"Key press detected at Row {i}, Column {j}")
                            row_detected = True
                    
                    time.sleep_ms(100)
                
                if not row_detected:
                    print(f"⚠️ No key press detected in row {i}. Check wiring for pin {row_pin}")
                
                # Reset row
                row.value(0)
                row = Pin(row_pin, Pin.IN)
    
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
    finally:
        # Reset all pins
        for pin_num in ROW_PINS + COL_PINS:
            Pin(pin_num, Pin.IN)

def main():
    """Run hardware checks"""
    print("=== Keypad Hardware Check Tool ===")
    print("This tool will check your keypad hardware connections")
    print()
    
    try:
        check_individual_pins()
        print()
        
        check_for_shorts()
        print()
        
        check_keypad_connectivity()
        print()
        
        print("Hardware check completed.")
        print("If you're still having issues, try using keypad_advanced_debug.py")
    
    except Exception as e:
        print(f"Error during hardware check: {e}")

if __name__ == "__main__":
    main()