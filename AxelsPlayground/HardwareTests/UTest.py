import serial
import time

class LCDRGB:
    """
    A library for controlling a 16x2 LCD with RGB backlight via UART.
    Based on the Matrix Orbital command set with Adafruit RGB backlight extensions.
    
    This library provides methods for:
    - Displaying text
    - Setting cursor position
    - Controlling display properties (on/off, cursor, blink)
    - Setting RGB backlight color
    - Creating custom characters
    """
    
    # Command start byte
    CMD_START = 0xFE
    
    # Basic commands
    CMD_DISPLAY_ON = 0x42
    CMD_DISPLAY_OFF = 0x46
    CMD_SET_BRIGHTNESS = 0x99
    CMD_SAVE_BRIGHTNESS = 0x98
    CMD_SET_CONTRAST = 0x50
    CMD_SAVE_CONTRAST = 0x91
    CMD_AUTOSCROLL_ON = 0x51
    CMD_AUTOSCROLL_OFF = 0x52
    CMD_CLEAR = 0x58
    CMD_SPLASH_SCREEN = 0x40
    
    # Cursor commands
    CMD_SET_CURSOR = 0x47
    CMD_HOME = 0x48
    CMD_CURSOR_BACK = 0x4C
    CMD_CURSOR_FORWARD = 0x4D
    CMD_UNDERLINE_ON = 0x4A
    CMD_UNDERLINE_OFF = 0x4B
    CMD_BLOCK_CURSOR_ON = 0x53
    CMD_BLOCK_CURSOR_OFF = 0x54
    
    # Baud rate command
    CMD_SET_BAUD = 0x39
    
    # RGB and Size commands
    CMD_SET_RGB = 0xD0
    CMD_SET_SIZE = 0xD1
    
    # Custom character commands
    CMD_CREATE_CHAR = 0x4E
    CMD_SAVE_CHAR = 0xC1
    CMD_LOAD_CHAR = 0xC0
    
    # GPO Commands
    CMD_GPO_OFF = 0x56
    CMD_GPO_ON = 0x57
    CMD_GPO_START = 0xC3
    
    # Special characters
    NEWLINE = 0x0A  # '\n'
    BACKSPACE = 0x08  # '\b'
    
    # Screen dimensions
    COLS = 16
    ROWS = 2
    
    # Baud rate values
    BAUD_RATES = {
        1200: 0x53,
        2400: 0x29,
        4800: 0xCF,
        9600: 0x67,
        19200: 0x33,
        28800: 0x22,
        38400: 0x19,
        57600: 0x10
    }
    
    def __init__(self, port, baudrate=9600, timeout=1, cols=16, rows=2):
        """
        Initialize the LCD controller.
        
        Args:
            port (str): Serial port (e.g., '/dev/ttyUSB0' or 'COM3')
            baudrate (int): Baud rate for serial communication
            timeout (float): Serial timeout in seconds
            cols (int): Number of columns in the display (default 16)
            rows (int): Number of rows in the display (default 2)
        """
        self.serial = serial.Serial(port, baudrate, timeout=timeout)
        time.sleep(1.0)  # Give plenty of time for serial connection to establish
        
        # Store screen dimensions
        self.COLS = cols
        self.ROWS = rows
        
        # Initialize the display with proper delays between commands
        self.clear()
        time.sleep(0.1)
        self.home()
        time.sleep(0.1)
        self.display_on()
        time.sleep(0.1)
        self.set_rgb(255, 255, 255)  # Set backlight to white
        time.sleep(0.1)
    
    def _send_command(self, command, *params):
        """
        Send a command to the LCD.
        
        Args:
            command (int): Command byte
            *params: Additional parameters for the command
        """
        data = bytearray([self.CMD_START, command])
        if params:
            data.extend(params)
            
        self.serial.write(data)
        time.sleep(0.05)  # Give the display time to process the command
    
    def clear(self):
        """Clear the display."""
        self._send_command(self.CMD_CLEAR)
        time.sleep(0.1)  # This command needs extra time
    
    def home(self):
        """Move cursor to home position (1, 1)."""
        self._send_command(self.CMD_HOME)
        time.sleep(0.05)
    
    def set_cursor(self, col, row):
        """
        Set the cursor position.
        
        Args:
            col (int): Column position (1 to 16/20)
            row (int): Row position (1 to 2/4)
        """
        # Validate position
        if row < 1 or row > self.ROWS or col < 1 or col > self.COLS:
            raise ValueError(f"Position out of bounds. Valid range is 1-{self.COLS} for columns and 1-{self.ROWS} for rows")
        
        self._send_command(self.CMD_SET_CURSOR, col, row)
    
    def cursor_back(self):
        """Move cursor back one position."""
        self._send_command(self.CMD_CURSOR_BACK)
    
    def cursor_forward(self):
        """Move cursor forward one position."""
        self._send_command(self.CMD_CURSOR_FORWARD)
    
    def underline_cursor_on(self):
        """Turn on the underline cursor."""
        self._send_command(self.CMD_UNDERLINE_ON)
    
    def underline_cursor_off(self):
        """Turn off the underline cursor."""
        self._send_command(self.CMD_UNDERLINE_OFF)
    
    def block_cursor_on(self):
        """Turn on the blinking block cursor."""
        self._send_command(self.CMD_BLOCK_CURSOR_ON)
    
    def block_cursor_off(self):
        """Turn off the blinking block cursor."""
        self._send_command(self.CMD_BLOCK_CURSOR_OFF)
    
    def display_on(self, minutes=0):
        """
        Turn the display on.
        
        Args:
            minutes (int): Minutes until auto-off (not supported by all displays)
        """
        self._send_command(self.CMD_DISPLAY_ON, minutes)
    
    def display_off(self):
        """Turn the display off."""
        self._send_command(self.CMD_DISPLAY_OFF)
    
    def autoscroll_on(self):
        """Enable autoscroll mode where text scrolls up when display is full."""
        self._send_command(self.CMD_AUTOSCROLL_ON)
    
    def autoscroll_off(self):
        """Disable autoscroll mode. Text will wrap to top when display is full."""
        self._send_command(self.CMD_AUTOSCROLL_OFF)
    
    def set_brightness(self, brightness):
        """
        Set the display brightness.
        
        Args:
            brightness (int): Brightness level (0-255)
        """
        self._send_command(self.CMD_SET_BRIGHTNESS, brightness)
    
    def save_brightness(self, brightness):
        """
        Set and save the display brightness to EEPROM.
        
        Args:
            brightness (int): Brightness level (0-255)
        """
        self._send_command(self.CMD_SAVE_BRIGHTNESS, brightness)
    
    def set_contrast(self, contrast):
        """
        Set the display contrast.
        
        Args:
            contrast (int): Contrast level (0-255), typically 180-220 works well
        """
        self._send_command(self.CMD_SET_CONTRAST, contrast)
    
    def save_contrast(self, contrast):
        """
        Set and save the display contrast to EEPROM.
        
        Args:
            contrast (int): Contrast level (0-255), typically 180-220 works well
        """
        self._send_command(self.CMD_SAVE_CONTRAST, contrast)
    
    def set_rgb(self, r, g, b):
        """
        Set the RGB backlight color.
        
        Args:
            r (int): Red value (0-255)
            g (int): Green value (0-255)
            b (int): Blue value (0-255)
        """
        self._send_command(self.CMD_SET_RGB, r, g, b)
    
    def set_lcd_size(self, cols, rows):
        """
        Set the LCD dimensions (saved to EEPROM).
        Requires power cycle to take effect.
        
        Args:
            cols (int): Number of columns (typically 16 or 20)
            rows (int): Number of rows (typically 2 or 4)
        """
        self._send_command(self.CMD_SET_SIZE, cols, rows)
        # Update local dimensions
        self.COLS = cols
        self.ROWS = rows
    
    def set_splash_screen(self, text):
        """
        Set custom splash screen text (saved to EEPROM).
        
        Args:
            text (str): Text to display on startup (max 32 chars for 16x2 or 80 chars for 20x4)
        """
        max_chars = self.COLS * self.ROWS
        if len(text) > max_chars:
            text = text[:max_chars]
            
        self._send_command(self.CMD_SPLASH_SCREEN)
        self.serial.write(text.encode('ascii'))
        time.sleep(0.1)
    
    def set_baud_rate(self, baud):
        """
        Set the baud rate for serial communication.
        
        Args:
            baud (int): Baud rate (supported values: 1200, 2400, 4800, 9600, 19200, 28800, 38400, 57600)
        """
        if baud not in self.BAUD_RATES:
            raise ValueError(f"Unsupported baud rate. Supported values are: {list(self.BAUD_RATES.keys())}")
            
        self._send_command(self.CMD_SET_BAUD, self.BAUD_RATES[baud])
        time.sleep(0.1)
    
    def create_custom_char(self, location, charmap):
        """
        Create a custom character.
        
        Args:
            location (int): Character location (0-7)
            charmap (list): List of 8 bytes defining the character bitmap
        """
        if location > 7:
            raise ValueError("Custom character location must be between 0 and 7")
        if len(charmap) != 8:
            raise ValueError("Character map must have exactly 8 bytes")
            
        data = [self.CMD_START, self.CMD_CREATE_CHAR, location]
        data.extend(charmap)
        self.serial.write(bytes(data))
        time.sleep(0.1)
    
    def save_custom_chars(self, bank):
        """
        Save custom characters to EEPROM bank.
        
        Args:
            bank (int): EEPROM bank (0-3)
        """
        if bank < 0 or bank > 3:
            raise ValueError("Bank must be between 0 and 3")
            
        self._send_command(self.CMD_SAVE_CHAR, bank)
    
    def load_custom_chars(self, bank):
        """
        Load custom characters from EEPROM bank.
        
        Args:
            bank (int): EEPROM bank (0-3)
        """
        if bank < 0 or bank > 3:
            raise ValueError("Bank must be between 0 and 3")
            
        self._send_command(self.CMD_LOAD_CHAR, bank)
    
    def gpo_on(self, pin):
        """
        Set a general purpose output pin high.
        
        Args:
            pin (int): Pin number (1-4)
        """
        if pin < 1 or pin > 4:
            raise ValueError("Pin must be between 1 and 4")
            
        self._send_command(self.CMD_GPO_ON, pin)
    
    def gpo_off(self, pin):
        """
        Set a general purpose output pin low.
        
        Args:
            pin (int): Pin number (1-4)
        """
        if pin < 1 or pin > 4:
            raise ValueError("Pin must be between 1 and 4")
            
        self._send_command(self.CMD_GPO_OFF, pin)
    
    def set_gpo_start(self, pin, state):
        """
        Set the initial state of a GPO pin.
        
        Args:
            pin (int): Pin number (1-4)
            state (int): Initial state (0 for off, 1 for on)
        """
        if pin < 1 or pin > 4:
            raise ValueError("Pin must be between 1 and 4")
        if state not in [0, 1]:
            raise ValueError("State must be 0 (off) or 1 (on)")
            
        self._send_command(self.CMD_GPO_START, pin, state)
    
    def write(self, text):
        """
        Write text to the display at the current cursor position.
        
        Args:
            text (str): The text to display
        """
        # Process each character to handle special characters properly
        for char in text:
            if char == '\n':
                # For newline, send the actual newline character
                self.serial.write(bytes([self.NEWLINE]))
            elif char == '\b':
                # For backspace
                self.serial.write(bytes([self.BACKSPACE]))
            else:
                # Regular ASCII character
                self.serial.write(char.encode('ascii'))
                
        time.sleep(0.01)  # Small delay for processing
    
    def print(self, text, col=None, row=None):
        """
        Print text at the specified position.
        If position is not specified, prints at the current cursor position.
        
        Args:
            text (str): Text to display
            col (int, optional): Column position (1 to 16/20)
            row (int, optional): Row position (1 to 2/4)
        """
        if col is not None and row is not None:
            self.set_cursor(col, row)
        self.write(text)
    
    def close(self):
        """Close the serial connection."""
        if self.serial and self.serial.is_open:
            self.serial.close()
    
    def __del__(self):
        """Destructor to ensure serial port is closed."""
        self.close()


# Example usage
if __name__ == "__main__":
    # Example: Connect to LCD on a specific port
    # lcd = LCDRGB('/dev/ttyUSB0')  # Linux
    # lcd = LCDRGB('COM3')          # Windows
    # lcd = LCDRGB('/dev/tty.usbserial-XXXXXX')  # macOS USB-to-Serial adapters
    # lcd = LCDRGB('/dev/tty.usbmodemXXXXXX')    # macOS direct USB devices
    
    # For demonstration purposes only
    import sys
    import glob
    
    # Auto-detect available serial ports on macOS
    def list_serial_ports():
        if sys.platform.startswith('darwin'):  # macOS
            ports = glob.glob('/dev/tty.*')
            usb_ports = [p for p in ports if 'usb' in p.lower()]
            return usb_ports
        elif sys.platform.startswith('linux'):
            return glob.glob('/dev/ttyUSB*') + glob.glob('/dev/ttyACM*')
        elif sys.platform.startswith('win'):
            # Windows needs pyserial installed for this
            try:
                from serial.tools import list_ports
                return [port.device for port in list_ports.comports()]
            except ImportError:
                return ['COM1', 'COM2', 'COM3', 'COM4', 'COM5']
        return []
    
    if len(sys.argv) < 2:
        ports = list_serial_ports()
        if ports:
            print("Available serial ports:")
            for i, port in enumerate(ports):
                print(f"{i+1}: {port}")
            print("\nUsage: python lcd_rgb.py <port>")
            print("Example: python lcd_rgb.py /dev/tty.usbserial-XXXXX")
        else:
            print("No serial ports detected.")
            print("Usage: python lcd_rgb.py <port>")
        sys.exit(1)
    
    port = sys.argv[1]
    
    try:
        # Initialize LCD
        lcd = LCDRGB(port)
        
        # Make sure the display is clear first
        lcd.clear()
        time.sleep(0.2)  # Add extra delay after clearing
        
        # Display a greeting with proper positioning
        lcd.set_cursor(1, 1)  # First row, first column (1-indexed)
        lcd.write("LCD Test")
        
        lcd.set_cursor(1, 2)  # Second row, first column (1-indexed)
        lcd.write("RGB Backlight")
        
        # Cycle through some colors
        colors = [
            (255, 0, 0),    # Red
            (0, 255, 0),    # Green
            (0, 0, 255),    # Blue
            (255, 255, 0),  # Yellow
            (0, 255, 255),  # Cyan
            (255, 0, 255),  # Magenta
            (255, 255, 255) # White
        ]
        
        for r, g, b in colors:
            lcd.set_rgb(r, g, b)
            time.sleep(1)
        
        # Turn off the display when done
        lcd.display_off()
        lcd.close()
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)