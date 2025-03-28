import machine
import time
import utime
from machine import Pin, UART

# Define the keypad layout
KEYPAD_KEYS = [
    ['1', '2', '3'],
    ['4', '5', '6'],
    ['7', '8', '9'],
    ['*', '0', '#']
]

class RgbLcdDisplay:
    """Class to interface with the 16x2 LCD RGB display via USB-C UART"""
    
    def __init__(self, uart_id=1, baud_rate=9600):
        """Initialize the RGB LCD display using the USB-C UART connection"""
        self.uart = UART(uart_id, baud_rate)
        self.uart.init(baud_rate, bits=8, parity=None, stop=1)
        time.sleep(0.1)  # Wait for UART to initialize
        
    def clear(self):
        """Clear the display"""
        self.uart.write(b'\xFE\x58')  # Command to clear display
        time.sleep(0.1)  # Give display time to process
        
    def home(self):
        """Move cursor to home position"""
        self.uart.write(b'\xFE\x48')
        time.sleep(0.05)
        
    def set_cursor(self, row, col):
        """Position the cursor at specified row and column (0-indexed)"""
        # Calculate cursor position according to Matrix Orbital spec
        # Matrix Orbital uses 1-indexed positions, so we add 1
        col_pos = col + 1
        row_pos = row + 1
        self.uart.write(bytes([0xFE, 0x47, col_pos, row_pos]))
        time.sleep(0.01)
        
    def print(self, text):
        """Print text at the current cursor position"""
        self.uart.write(text.encode())
        time.sleep(0.05)
        
    def write(self, text):
        """Alias for print method"""
        self.print(text)
        
    def set_rgb(self, r, g, b):
        """Set the backlight color using RGB values (0-255)"""
        self.uart.write(b'\xFE\xD0' + bytes([r, g, b]))
        time.sleep(0.05)
        
    def set_color(self, color):
        """Set color using predefined colors"""
        colors = {
            "red": (255, 0, 0),
            "green": (0, 255, 0),
            "blue": (0, 0, 255),
            "yellow": (255, 255, 0),
            "teal": (0, 255, 255),
            "violet": (255, 0, 255),
            "white": (255, 255, 255),
            "off": (0, 0, 0)
        }
        
        if color in colors:
            r, g, b = colors[color]
            self.set_rgb(r, g, b)
    
    def display_on(self, minutes=0):
        """Turn the display on"""
        self.uart.write(bytes([0xFE, 0x42, minutes]))
        time.sleep(0.05)
    
    def display_off(self):
        """Turn the display off"""
        self.uart.write(b'\xFE\x46')
        time.sleep(0.05)
    
    def underline_cursor_on(self):
        """Turn on the underline cursor"""
        self.uart.write(b'\xFE\x4A')
        time.sleep(0.05)
    
    def underline_cursor_off(self):
        """Turn off the underline cursor"""
        self.uart.write(b'\xFE\x4B')
        time.sleep(0.05)
    
    def block_cursor_on(self):
        """Turn on the blinking block cursor"""
        self.uart.write(b'\xFE\x53')
        time.sleep(0.05)
    
    def block_cursor_off(self):
        """Turn off the blinking block cursor"""
        self.uart.write(b'\xFE\x54')
        time.sleep(0.05)
        
    def create_custom_char(self, location, charmap):
        """Create a custom character in CGRAM"""
        if location > 7:
            raise ValueError("Custom character location must be between 0 and 7")
        if len(charmap) != 8:
            raise ValueError("Character map must have exactly 8 bytes")
            
        cmd = bytes([0xFE, 0x4E, location]) + bytes(charmap)
        self.uart.write(cmd)
        time.sleep(0.1)


class MatrixKeypad:
    """Class to interface with a matrix keypad."""
    
    def __init__(self, row_pins, col_pins, keys=KEYPAD_KEYS):
        """
        Initialize the keypad.
        
        Args:
            row_pins (list): List of GPIO pin numbers for rows
            col_pins (list): List of GPIO pin numbers for columns
            keys (list): 2D list mapping keypad layout
        """
        self.rows = len(row_pins)
        self.cols = len(col_pins)
        self.keys = keys
        
        # Setup row pins as outputs (initially high)
        self.row_pins = []
        for pin in row_pins:
            self.row_pins.append(Pin(pin, Pin.OUT, value=1))
            
        # Setup column pins as inputs with pull-down resistors
        self.col_pins = []
        for pin in col_pins:
            self.col_pins.append(Pin(pin, Pin.IN, Pin.PULL_DOWN))
        
        # Variables for debouncing
        self.last_key_press = None
        self.last_press_time = 0
        self.debounce_time = 200  # ms
    
    def scan(self):
        """
        Scan the keypad and return the pressed key, or None if no key is pressed.
        Includes debouncing to avoid multiple detections of the same press.
        """
        # Check if enough time has passed since the last press
        if (utime.ticks_ms() - self.last_press_time) < self.debounce_time:
            return None
        
        # Scan the keypad
        for r, row_pin in enumerate(self.row_pins):
            # Set the current row low
            row_pin.value(0)
            
            # Check each column
            for c, col_pin in enumerate(self.col_pins):
                if col_pin.value():
                    # Key press detected
                    key = self.keys[r][c]
                    
                    # Set row back high
                    row_pin.value(1)
                    
                    # If same key is pressed again quickly, ignore it (debounce)
                    if key == self.last_key_press and (utime.ticks_ms() - self.last_press_time) < 500:
                        return None
                    
                    # Update last key press info
                    self.last_key_press = key
                    self.last_press_time = utime.ticks_ms()
                    
                    return key
            
            # Set row back high before checking next row
            row_pin.value(1)
        
        # No key was pressed
        return None
    
    def wait_for_key(self):
        """Wait for a key press and return the key."""
        key = None
        while key is None:
            key = self.scan()
            time.sleep_ms(10)
        return key


def main():
    """Main application to interface keypad with LCD."""
    print("Starting keypad-LCD interface...")
    
    # Define pins for the keypad
    # Modify these according to your actual connections
    ROW_PINS = [1, 2, 3, 4]  # Connected to rows of keypad
    COL_PINS = [5, 6, 7]     # Connected to columns of keypad
    
    try:
        # Initialize the LCD using USB-C UART
        print("Initializing LCD...")
        lcd = RgbLcdDisplay(uart_id=1)  # UART1 for USB-C port
        
        # Initialize the keypad
        print("Initializing keypad...")
        keypad = MatrixKeypad(ROW_PINS, COL_PINS)
        
        # Display welcome message
        lcd.clear()
        lcd.set_cursor(0, 0)  # First row (0-indexed)
        lcd.print("Keypad Test")
        lcd.set_cursor(1, 0)  # Second row (0-indexed)
        lcd.print("Press any key")
        lcd.set_rgb(0, 128, 255)  # Light blue backlight
        
        # For tracking cursor position (0-indexed)
        cursor_col = 0
        cursor_row = 0
        max_col = 15  # 16 columns (0-15) on a 16x2 display
        
        # Clear after a short delay
        time.sleep_ms(2000)
        lcd.clear()
        
        # Enable cursor
        lcd.underline_cursor_on()
        lcd.set_cursor(cursor_row, cursor_col)
        
        print("Ready for keypad input...")
        
        while True:
            key = keypad.scan()
            
            if key:
                print(f"Key pressed: {key}")
                
                # Handle special keys
                if key == '*':
                    # Backspace functionality
                    if cursor_col > 0:
                        cursor_col -= 1
                        lcd.set_cursor(cursor_row, cursor_col)
                        lcd.write(' ')  # Erase character
                        lcd.set_cursor(cursor_row, cursor_col)
                    elif cursor_row == 1 and cursor_col == 0:
                        # Move to end of first row
                        cursor_row = 0
                        cursor_col = max_col
                        lcd.set_cursor(cursor_row, cursor_col)
                
                elif key == '#':
                    # Enter/newline functionality
                    if cursor_row == 0:
                        cursor_row = 1
                        cursor_col = 0
                        lcd.set_cursor(cursor_row, cursor_col)
                    else:
                        # Clear and start over if already on second row
                        lcd.clear()
                        cursor_row = 0
                        cursor_col = 0
                        lcd.set_cursor(cursor_row, cursor_col)
                
                else:
                    # Display the key
                    lcd.write(key)
                    
                    # Update cursor position
                    cursor_col += 1
                    
                    # Handle wrapping
                    if cursor_col > max_col:
                        if cursor_row == 0:
                            cursor_row = 1
                            cursor_col = 0
                        else:
                            # Scroll up
                            lcd.clear()
                            lcd.set_cursor(0, 0)
                            # You could save the second row and move it to first row here
                            # For simplicity, we just clear and continue on first row
                            cursor_row = 0
                            cursor_col = 0
                    
                    # Position cursor
                    lcd.set_cursor(cursor_row, cursor_col)
                
                # Add a small delay after processing a key
                time.sleep_ms(100)
            
            # Prevent CPU from running at 100%
            time.sleep_ms(10)
                
    except KeyboardInterrupt:
        print("Program terminated by user")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        try:
            # Clean up
            lcd.clear()
            lcd.set_cursor(0, 0)
            lcd.print("Goodbye!")
            time.sleep_ms(1000)
            lcd.display_off()
            print("Program ended")
        except:
            pass


if __name__ == "__main__":
    main()