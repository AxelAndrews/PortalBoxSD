"""
Test script for the 3x4 matrix keypad on ESP32-C6 DevKit
This script tests different modes of reading from the keypad
"""

import time
from keypad import KeyPad

# Define pin numbers
ROW_PINS = [13, 21, 20, 18]  # GPIO pins for rows
COL_PINS = [22, 12, 19]     # GPIO pins for columns

def test_single_key_press():
    """Test single key press detection"""
    print("=== Testing Single Key Press ===")
    print("Press any key on the keypad...")
    
    keypad = KeyPad(ROW_PINS, COL_PINS)
    
    for _ in range(5):  # Test 5 key presses
        key = keypad.read_key()
        print(f"Detected key: {key}")
        time.sleep(0.5)
    
    print("Single key press test completed")
    print()

def test_continuous_scanning():
    """Test continuous scanning for 10 seconds"""
    print("=== Testing Continuous Scanning ===")
    print("Press keys continuously for 10 seconds...")
    
    keypad = KeyPad(ROW_PINS, COL_PINS)
    end_time = time.time() + 10  # Run for 10 seconds
    
    last_key = None
    
    while time.time() < end_time:
        key = keypad.scan()
        
        # Only print when key state changes
        if key != last_key:
            if key:
                print(f"Key pressed: {key}")
            last_key = key
        
        time.sleep(0.1)
    
    print("Continuous scanning test completed")
    print()

def test_key_sequence():
    """Test reading a sequence of keys"""
    print("=== Testing Key Sequence ===")
    print("Enter a sequence of up to 4 keys (5 second timeout between keys)...")
    
    keypad = KeyPad(ROW_PINS, COL_PINS)
    sequence = keypad.read_keys_sequence(max_length=4, timeout=5000)
    
    print(f"Sequence entered: {''.join(sequence)}")
    print("Key sequence test completed")
    print()

def test_pin_verification():
    """Test PIN verification functionality"""
    print("=== Testing PIN Verification ===")
    print("Enter the PIN: 4152")
    
    keypad = KeyPad(ROW_PINS, COL_PINS)
    correct_pin = "4152"
    
    sequence = keypad.read_keys_sequence(max_length=4, timeout=5000)
    entered_pin = ''.join(sequence)
    
    if entered_pin == correct_pin:
        print("PIN correct!")
    else:
        print(f"PIN incorrect! You entered: {entered_pin}")
    
    print("PIN verification test completed")
    print()

def main():
    """Run all tests"""
    print("Starting keypad tests...")
    print("Make sure the keypad is properly connected to the ESP32-C6 DevKit")
    print("Row pins:", ROW_PINS)
    print("Column pins:", COL_PINS)
    print()
    
    try:
        # Run all tests
        test_single_key_press()
        test_continuous_scanning()
        test_key_sequence()
        test_pin_verification()
        
        print("All tests completed!")
        
    except KeyboardInterrupt:
        print("\nTests interrupted by user")
    except Exception as e:
        print(f"\nError occurred: {e}")

if __name__ == "__main__":
    main()