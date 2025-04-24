from machine import Pin
import time
import neopixel
led_power = Pin(21, Pin.OUT)
led_power.on() # GPIO2 is often connected to the onboard LED
led = Pin(8, Pin.OUT)
np=neopixel.NeoPixel(led,1) 
# Run this to test the connection with the ESP32-C6 using the command below:
# mpremote run test.py

# Run this to copy the file locally onto the ESP32 more information is found in the Firmware/Software tutorial
# mpremote fs cp testKeypad.py :main.py


#The below code will turn the **Neopixel** on and flash RBG continuously on the ESP32-C6
while True:
     np[0]= (30,0,0)
     np.write()
     time.sleep(0.5) # Wait for 0.5 seconds
     np[0]= (0,0,0)
     np.write()
     time.sleep(0.5)
     np[0]= (0,30,0)
     np.write()
     time.sleep(0.5)
     np[0]= (0,0,0)
     np.write()
     time.sleep(0.5)
     np[0]= (0,0,30)
     np.write()
     time.sleep(0.5)
     np[0]= (0,0,0)
     np.write()
     time.sleep(0.5)