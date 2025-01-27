import network
import time

SSID='bucknell_iot'
password=""

# Initialize the WLAN interface
wlan = network.WLAN(network.STA_IF)
wlan.active(True)

# Scan for local networks
print("Scanning for networks...")
networks = wlan.scan()
for network in networks:
    print("Found network:", network)

# Check if connected
if not wlan.isconnected():
    print('Connecting to network...')
    wlan.connect(SSID, password)
    timeout = 10  # Timeout in seconds SHOULD NOT TAKE MORE THAN 10 SECONDS
    start_time = time.time() # Start timer
    # Get curr timer val and check if it is less than the timeout
    
    while not wlan.isconnected() and (time.time() - start_time) < timeout:
        # Pause between each check
        print("Waiting for connection...")
        time.sleep(1)
    
    if not wlan.isconnected():
        print("Failed to connect within timeout.")
    else:
        print(f"Connected successfully in {time.time() - start_time} seconds")

