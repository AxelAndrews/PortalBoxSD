# TestLCDKeypad.py - Simple test program for LCD and Keypad
import time
import json
from machine import Pin

# Import necessary modules
from Keypad import scan_keypad
from RGBLCD import RGBLCD

# Load configuration for pins
def load_config(config_file_path="config.json"):
    try:
        with open(config_file_path, 'r') as f:
            config = json.load(f)
            print("Loaded configuration")
            return config
    except Exception as e:
        print(f"Error loading config: {e}")
        return {
            "pins": {
                "LCD_TX": 5
            }
        }

def main():
    print("Starting LCD and Keypad test")
    
    # Load configuration
    config = load_config()
    
    # Initialize LCD
    print("Initializing LCD...")
    lcd_tx_pin = config["pins"].get("LCD_TX", 5)
    lcd = RGBLCD(uart_id=1, tx_pin=lcd_tx_pin, baud_rate=9600, cols=16, rows=2)
    
    # Basic LCD test
    print("Testing LCD...")
    lcd.display_on()
    lcd.set_rgb_color(255, 255, 255)  # White
    
    # Clear and print a welcome message
    lcd.clear()
    time.sleep(0.05)
    lcd.home()
    time.sleep(0.05)
    lcd.print("LCD Test")
    time.sleep(0.05)
    
    # Test second line
    lcd.set_cursor(1, 2)  # Column 1, Row 2
    time.sleep(0.05)
    lcd.print("Press keys...")
    
    # Main loop for keypad test
    print("Testing keypad...")
    try:
        while True:
            # Scan keypad
            keys = scan_keypad()
            
            # If any keys pressed, display them
            if keys:
                # Clear second line
                lcd.set_cursor(1, 2)
                time.sleep(0.02)
                lcd.print("Key: " + " ".join(str(k) for k in keys) + "      ")
                
                # Change color based on key
                if '*' in keys:
                    lcd.set_rgb_color(255, 0, 0)  # Red
                elif '#' in keys:
                    lcd.set_rgb_color(0, 255, 0)  # Green
                elif '0' in keys:
                    lcd.set_rgb_color(0, 0, 255)  # Blue
                elif '1' in keys:
                    lcd.set_rgb_color(255, 255, 0)  # Yellow
                    
                print("Keys pressed:", keys)
                time.sleep(0.3)  # Debounce delay
            
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("Test ended")
    finally:
        # Clear display
        lcd.clear()
        lcd.set_rgb_color(0, 0, 0)  # Off
        lcd.print("Test complete")

if __name__ == "__main__":
    main()