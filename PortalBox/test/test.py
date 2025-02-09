from machine import Pin
import time
import neopixel
led = Pin(8, Pin.OUT) # GPIO2 is often connected to the onboard LED
np=neopixel.NeoPixel(led,1) 
# mpremote run test.py
# mpremote fs cp testKeypad.py :main.py
# ASYNC IO
while True:
     # print("hi")
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