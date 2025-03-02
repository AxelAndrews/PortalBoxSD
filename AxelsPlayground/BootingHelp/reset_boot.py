# Run in REPL
# Remove the dev_mode file

# To use this script, run it in the REPL
# Access REPL by rebooting with RST button, type mpremote, then CTRL+C during bootup to enter REPL
# Copy and paste script, then press Enter
# CTRL+X to exit REPL, box now has default boot.py and can be accessed with mpremote
import os
try:
 os.remove('dev_mode')
 print("dev_mode file removed")
except:
 print("No dev_mode file found or error removing it")

# Overwrite boot.py with minimal content
with open('boot.py', 'w') as f:
 f.write('# This file is executed on every boot (including wake-boot from deepsleep)\n# import esp\n# esp.osdebug(None)\n')

print("boot.py has been reset to default")

# Verify the file exists with proper content
with open('boot.py', 'r') as f:
 print(f.read())