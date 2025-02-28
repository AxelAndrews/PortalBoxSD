import time
from machine import Pin, SoftSPI # type: ignore
# from lib.rfid.mfrc522 import MFRC522
from MFRC522 import MFRC522

# Code derived from https://github.com/Tasm-Devil/micropython-mfrc522-esp32/tree/master

import neopixel # type: ignore

led = Pin(8, Pin.OUT) # GPIO2 is often connected to the onboard LED
np=neopixel.NeoPixel(led,1) 

# sck = Pin(18, Pin.OUT)
# mosi = Pin(23, Pin.OUT)
# miso = Pin(19, Pin.OUT)
# spi = SoftSPI(baudrate=100000, polarity=0, phase=0, sck=sck, mosi=mosi, miso=miso)

# sda = Pin(5, Pin.OUT)
# sda = Pin(3, Pin.OUT)
# sck = Pin(2, Pin.OUT)
# mosi = Pin(11, Pin.OUT)
# miso = Pin(10, Pin.OUT)
# spi = SoftSPI(baudrate=100000, polarity=0, phase=0, sck=sck, mosi=mosi, miso=miso)

def do_read():
    try:
        maxAttempts=0
        while maxAttempts != 1:
            # print(maxAttempts)
            rdr = MFRC522(spi, sda)
            uid = ""
            (stat, tag_type) = rdr.request(rdr.REQIDL)
            if stat == rdr.OK:
                (stat, raw_uid) = rdr.anticoll()
                if stat == rdr.OK:
                    uid = ("0x%02x%02x%02x%02x" % (raw_uid[0], raw_uid[1], raw_uid[2], raw_uid[3]))
                    return uid
            maxAttempts+=1
        return -1
    except KeyboardInterrupt:
        print("Bye")
print(do_read())