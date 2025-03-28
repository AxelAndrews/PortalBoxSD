import time
from machine import UART

class RgbLcdDisplay:
    def __init__(self, tx_pin=5, uart_id=1, baud_rate=9600, cols=16, rows=2):
        """Initialize the RGB LCD display using UART with TX pin connection"""
        self.uart = UART(uart_id, baud_rate)
        self.uart.init(tx=tx_pin)  # Only TX needed
        self.cols = cols
        self.rows = rows
        time.sleep(0.1)  # Wait for UART to initialize
        
    def clear(self):
        """Clear the display"""
        self.uart.write(b'\xFE\x58')  # Command to clear display
        time.sleep(0.1)  # Give display time to process
        
    def set_cursor(self, row, col):
        """Position the cursor at specified row and column"""
        if row == 0:
            position = col
        else:
            position = 0x40 + col  # For 16x2 LCD, second row starts at 0x40
            
        self.uart.write(b'\xFE\x47' + bytes([position]))
        time.sleep(0.01)
        
    def print(self, text):
        """Print text at the current cursor position"""
        self.uart.write(text.encode())
        time.sleep(0.1)
        
    def set_rgb(self, r, g, b):
        """Set the backlight color using RGB values (0-255)"""
        self.uart.write(b'\xFE\xD0' + bytes([r, g, b]))
        time.sleep(0.1)
        
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

# Test program
def test_lcd():
    # Initialize the display - using USB UART
    # For ESP32-C6-DevKit, typically UART0 is used for USB-C connection
    lcd = RgbLcdDisplay(uart_id=1, tx_pin=5)
    
    # Test clearing the display
    lcd.clear()
    
    # Test different colors
    colors = ["red", "green", "blue", "yellow", "teal", "violet", "white"]
    
    for color in colors:
        lcd.clear()
        lcd.set_color(color)
        lcd.set_cursor(0, 0)
        lcd.print(f"Color: {color}")
        lcd.set_cursor(1, 0)
        lcd.print("ESP32-C6 Test")
        time.sleep(2)
    
    # Test message printing
    lcd.clear()
    lcd.set_color("white")
    lcd.set_cursor(0, 0)
    lcd.print("Test complete!")
    lcd.set_cursor(1, 0)
    lcd.print("MicroPython :)")
    
if __name__ == "__main__":
    test_lcd()