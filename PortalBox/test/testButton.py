import machine 
from machine import Pin
import time
import neopixel

led = Pin(8, Pin.OUT) # GPIO2 is often connected to the onboard LED
np=neopixel.NeoPixel(led,1) # mpremote run test.py
button_pin = machine.Pin(1, machine.Pin.IN, machine.Pin.PULL_UP)

while True:
    # print("hi")
    button_state = button_pin.value()

    if button_state == 0: 
        print("Button pressed!")
        time.sleep(0.1)
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
    else: 
        print("Button released!")