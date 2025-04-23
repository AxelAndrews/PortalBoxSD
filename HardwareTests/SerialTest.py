import serial
import time

# Adjust the port and baud rate to match your setup
PORT = '/dev/tty.usbmodem1101'  # Change this to your port
BAUD_RATE = 9600

def main():
    try:
        # Open serial connection
        ser = serial.Serial(PORT, BAUD_RATE, timeout=1)
        print(f"Connected to {PORT}")
        time.sleep(1)  # Give the display time to initialize
        
        # First, set white backlight (this command works)
        ser.write(b'\xFE\xD0\xFF\xFF\xFF')
        time.sleep(0.5)
        
        # Clear the display by filling with spaces and using backspace to reset position
        # Send spaces to fill entire display (assuming 16x2 display = 32 characters)
        print("Clearing display with spaces...")
        ser.write(b' ' * 32)
        time.sleep(0.5)
        
        # Use backspace to get back to beginning
        print("Moving cursor to beginning...")
        ser.write(b'\x08' * 32)  # More than enough backspaces to ensure we're at the start
        time.sleep(0.5)
        
        # Write a test message at what should now be the beginning
        print("Writing test message...")
        ser.write(b"Hello World")
        time.sleep(3)
        
        # Try to use newline to get to second line
        print("Testing newline...")
        ser.write(b'\n')
        time.sleep(0.5)
        
        # Write to what should be the second line
        ser.write(b"Line Two")
        time.sleep(3)
        
        # Close the connection
        ser.close()
        print("Test complete")
        
    except serial.SerialException as e:
        print(f"Error: {e}")
        print(f"Make sure the display is connected and the port ({PORT}) is correct.")

if __name__ == "__main__":
    main()