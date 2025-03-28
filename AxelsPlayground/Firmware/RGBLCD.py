"""
RGB LCD Serial Control Library for MicroPython
For controlling Matrix Orbital compatible LCD displays with RGB backlight
through TTL serial connection.

Compatible with 16x2 and 20x4 displays with appropriate configuration.
"""
import time
from machine import UART # type: ignore

class RGBLCD:
    """Class for controlling RGB LCD displays via serial connection"""
    
    # Command constants
    CMD_PREFIX = 0xFE
    
    # Display commands
    DISPLAY_ON = 0x42
    DISPLAY_OFF = 0x46
    CLEAR_SCREEN = 0x58
    SET_BRIGHTNESS = 0x99
    SET_CONTRAST = 0x50
    SET_RGB_COLOR = 0xD0
    SET_LCD_SIZE = 0xD1
    
    # Cursor commands
    SET_CURSOR_POS = 0x47
    GO_HOME = 0x48
    CURSOR_BACK = 0x4C
    CURSOR_FORWARD = 0x4D
    UNDERLINE_CURSOR_ON = 0x4A
    UNDERLINE_CURSOR_OFF = 0x4B
    BLOCK_CURSOR_ON = 0x53
    BLOCK_CURSOR_OFF = 0x54
    
    # Scrolling commands
    AUTOSCROLL_ON = 0x51
    AUTOSCROLL_OFF = 0x52
    
    def __init__(self, uart_id=1, tx_pin=5, baud_rate=9600, cols=16, rows=2):
        """
        Initialize the LCD controller
        
        Args:
            uart_id: UART bus ID to use
            tx_pin: TX pin number for serial communication
            rx_pin: RX pin number (can be None if only sending data)
            baud_rate: Serial baud rate (default 9600)
            cols: Number of display columns (default 16)
            rows: Number of display rows (default 2)
        """
        self.cols = cols
        self.rows = rows
        
        # Initialize UART with a larger buffer
        self.uart = UART(uart_id, baud_rate)
        self.uart.init(baud_rate, bits=8, parity=None, stop=1, tx=tx_pin, timeout=50)
        
        # Longer delay to ensure LCD is fully ready
        time.sleep(0.5)
        
        # Initial setup with delays between each command
        self.set_display_size(cols, rows)
        time.sleep(0.1)
        self.clear()
        time.sleep(0.1)
        self.display_on()
        time.sleep(0.1)
        self.cursor_off()
        time.sleep(0.1)
        self.autoscroll_on()
        time.sleep(0.1)
        
        # Set reasonable defaults for contrast and brightness
        self.set_contrast(200)
        time.sleep(0.1)
        self.set_brightness(255)
        time.sleep(0.1)
        self.set_rgb_color(255, 255, 255)  # White backlight by default
        time.sleep(0.1)
    
    def _send_command(self, command, *args):
        """
        Send a command to the LCD
        
        Args:
            command: Command byte
            *args: Any additional bytes needed for the command
        """
        data = bytearray([self.CMD_PREFIX, command])
        for arg in args:
            # Ensure each argument is treated as a byte
            if isinstance(arg, str):
                data.extend(arg.encode())
            else:
                data.append(int(arg) & 0xFF)  # Convert to int and ensure it's a byte
        
        # Write command and flush
        self.uart.write(data)
        
        # Increased delay for command processing - this is critical for reliable operation
        time.sleep(0.05)  # 50ms delay between commands
    
    def display_on(self, timeout_minutes=0):
        """Turn the display on with optional timeout"""
        self._send_command(self.DISPLAY_ON, timeout_minutes)
    
    def display_off(self):
        """Turn the display off"""
        self._send_command(self.DISPLAY_OFF)
    
    def clear(self):
        """Clear the display"""
        self._send_command(self.CLEAR_SCREEN)
    
    def home(self):
        """Move cursor to home position (1,1)"""
        self._send_command(self.GO_HOME)
    
    def set_cursor(self, col, row):
        """
        Set cursor position
        
        Args:
            col: Column (1-based indexing)
            row: Row (1-based indexing)
        """
        # Ensure valid range
        col = max(1, min(self.cols, col))
        row = max(1, min(self.rows, row))
        
        # The command reference shows cursor position is 1-based,
        # but we'll add a debug print to check what's sent
        self._send_command(self.SET_CURSOR_POS, col, row)
        
        # Additional small delay after cursor positioning
        time.sleep(0.02)
    
    def cursor_on(self, block=False):
        """
        Turn on cursor
        
        Args:
            block: If True, use block cursor, otherwise use underline
        """
        if block:
            self._send_command(self.BLOCK_CURSOR_ON)
        else:
            self._send_command(self.UNDERLINE_CURSOR_ON)
    
    def cursor_off(self):
        """Turn off both cursors"""
        self._send_command(self.UNDERLINE_CURSOR_OFF)
        self._send_command(self.BLOCK_CURSOR_OFF)
    
    def autoscroll_on(self):
        """Enable autoscroll mode"""
        self._send_command(self.AUTOSCROLL_ON)
    
    def autoscroll_off(self):
        """Disable autoscroll mode"""
        self._send_command(self.AUTOSCROLL_OFF)
    
    def set_contrast(self, contrast):
        """
        Set display contrast
        
        Args:
            contrast: Contrast value (0-255), typically 180-220 works well
        """
        contrast = max(0, min(255, contrast))
        self._send_command(self.SET_CONTRAST, contrast)
    
    def set_brightness(self, brightness):
        """
        Set backlight brightness
        
        Args:
            brightness: Brightness value (0-255)
        """
        brightness = max(0, min(255, brightness))
        self._send_command(self.SET_BRIGHTNESS, brightness)
    
    def set_rgb_color(self, r, g, b):
        """
        Set RGB backlight color
        
        Args:
            r: Red component (0-255)
            g: Green component (0-255)
            b: Blue component (0-255)
        """
        r = max(0, min(255, r))
        g = max(0, min(255, g))
        b = max(0, min(255, b))
        self._send_command(self.SET_RGB_COLOR, r, g, b)
    
    def set_display_size(self, cols, rows):
        """
        Set the LCD display size
        
        Args:
            cols: Number of columns (typically 16 or 20)
            rows: Number of rows (typically 2 or 4)
        """
        self.cols = cols
        self.rows = rows
        self._send_command(self.SET_LCD_SIZE, cols, rows)
    
    def print(self, text):
        """
        Print text to the display at current cursor position
        
        Args:
            text: Text to display
        """
        self.uart.write(text.encode())
    
    def print_at(self, text, col, row):
        """
        Print text at specified position
        
        Args:
            text: Text to display
            col: Column (1-based indexing)
            row: Row (1-based indexing)
        """
        # Explicitly send cursor position command instead of using self.set_cursor
        self._send_command(self.SET_CURSOR_POS, col, row)
        time.sleep(0.02)  # Small delay to ensure cursor is positioned
        self.print(text)
    
    def create_char(self, slot, bitmap):
        """
        Create a custom character
        
        Args:
            slot: Character slot (0-7)
            bitmap: List of 8 bytes defining the character
        """
        if not 0 <= slot <= 7:
            raise ValueError("Character slot must be between 0 and 7")
        
        if len(bitmap) != 8:
            raise ValueError("Bitmap must contain exactly 8 bytes")
        
        self._send_command(0x4E, slot, *bitmap)