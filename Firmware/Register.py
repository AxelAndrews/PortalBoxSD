# register.py for MicroPython
# Registers the device with the database if not already registered

# Import required libraries
import json
import network # type: ignore
import sys

# Import our local modules
from Database import Database

# Define config file path
CONFIG_FILE_PATH = "config.json"

def get_mac_address():
    """Get the MAC address of the ESP32 as a hex string without colons"""
    sta_if = network.WLAN(network.STA_IF)
    mac = sta_if.config('mac')
    return ''.join('{:02x}'.format(b) for b in mac)

def main():
    # Load configuration
    try:
        # Try to load from custom path if provided
        config_path = CONFIG_FILE_PATH
        if len(sys.argv) > 1:
            config_path = sys.argv[1]
            
        # Load config file
        with open(config_path, 'r') as f:
            settings = json.load(f)
        
        print(f"Loaded configuration from {config_path}")
    except Exception as e:
        print(f"Error loading configuration: {e}")
        sys.exit(1)
    
    # Get MAC address
    try:
        mac_address = get_mac_address()
        print(f"Device MAC address: {mac_address}")
    except Exception as e:
        print(f"Error getting MAC address: {e}")
        sys.exit(1)
    
    # Connect to database
    try:
        db = Database(settings['db'])
        print("Connected to database")
    except Exception as e:
        print(f"Error connecting to database: {e}")
        sys.exit(1)
    
    # Check if registered and register if not
    try:
        is_registered = db.is_registered(mac_address)
        print(f"Registration status: {'Registered' if is_registered else 'Not registered'}")
        
        if not is_registered:
            print("Registering device...")
            result = db.register(mac_address)
            if result:
                print("Device successfully registered")
            else:
                print("Registration failed")
    except Exception as e:
        print(f"Error during registration check/process: {e}")
        sys.exit(1)
    
    print("Registration process complete")

# Run the program
if __name__ == "__main__":
    main()