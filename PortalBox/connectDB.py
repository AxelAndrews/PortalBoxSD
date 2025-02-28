import network
import socket
import urequests

wifi = network.WLAN(network.STA_IF)
wifi.active(True)
wifi.connect('bucknell_iot', '')  # Replace with your Wi-Fi credentials

# Wait for connection
while not wifi.isconnected():
    pass

print('Wi-Fi connected, IP address:', wifi.ifconfig()[0])

# Test DNS resolution (e.g., ping Google DNS)
try:
    socket.getaddrinfo('ec2-3-14-141-222.us-east-2.compute.amazonaws.com', 80)
    print("DNS resolved correctly")
except OSError as e:
    print("DNS resolution failed", e)


# Once connected and DNS is resolved, send the HTTP request
url = "http://ec2-3-14-141-222.us-east-2.compute.amazonaws.com/mode"

try:
    response = urequests.get(url)
    
    if response.status_code == 200:
        data = response.json()
        print("Mode:", data['mode'])
    else:
        print("Error:", response.text)
except Exception as e:
    print("Failed to make HTTP request:", e)
