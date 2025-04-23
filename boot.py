# boot.py - Minimalist boot script for ESP32-C6-DevKit
import time
import sys
import gc
from machine import Pin, reset

# Check for development mode flag file
def in_dev_mode():
    try:
        with open('dev_mode', 'r') as f:
            return f.read().strip() == '1'
    except:
        return False

# Check for registration flag file
def should_register():
    try:
        with open('register', 'r') as f:
            return f.read().strip() == '1'
    except:
        return False

# Main boot sequence
print("ESP32-C6-DevKit booting...")

# Check boot mode
if in_dev_mode():
    print("Development mode detected. REPL available.")
    print("- To enable normal mode: remove 'dev_mode' file")
    print("- To register device: create 'register' file")
    sys.exit()

# Check if we should run registration instead of Service
if should_register():
    print("Registration mode detected. Running Register.py...")
    try:
        import Register
        Register.main()
        # Remove register flag after registration
        try:
            import os
            os.remove('register')
            print("Register flag removed. Rebooting to normal mode...")
            time.sleep(1)
            reset()  # Reboot after registration
        except:
            print("Failed to remove register flag. Please remove manually.")
    except Exception as e:
        print(f"Registration error: {e}")
        sys.print_exception(e)
    sys.exit()

# Normal boot - Service with brief interrupt window
print("Starting Service in 3 seconds... (Ctrl+C to interrupt)")
for i in range(3, 0, -1):
    print(i)
    time.sleep(1)

# Clean up memory before launching
gc.collect()

# Import and start Service
try:
    import Service
    print("Starting Service...")
    Service.main()
except KeyboardInterrupt:
    print("Boot interrupted - REPL available")
except Exception as e:
    print(f"Error running Service: {e}")
    sys.print_exception(e)