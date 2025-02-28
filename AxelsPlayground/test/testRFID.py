#!/usr/bin/env python
# -*- coding: utf8 -*-

import time
from MFRC522 import MFRC522  # Importing the MFRC522 class you provided earlier

# Port configuration for Windows (COM5)
SERIAL_PORT = 'COM8'

# Initialize MFRC522 reader on the specified serial port
reader = MFRC522(dev=SERIAL_PORT)

def main():
    print("MFRC522 RFID Reader Test")
    
    while True:
        # Scan for tags (RFID cards)
        print("Waiting for RFID card...")

        # Request for a card (PICC_REQA) or (PICC_WUPA)
        status, back_bits = reader.MFRC522_Request(reader.PICC_REQA)
        
        if status == reader.MI_OK:
            print("Card detected!")

            # Anti-collision to retrieve the UID
            status, back_data = reader.MFRC522_Anticoll()
            if status == reader.MI_OK:
                print(f"UID detected: {''.join([hex(x) for x in back_data])}")
                
                # Authenticate the card (using key A)
                key = [0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF]  # Default MIFARE key A
                status = reader.MFRC522_Auth(reader.PICC_AUTHENT1A, 8, key, back_data)
                
                if status == reader.MI_OK:
                    print("Authentication successful!")
                    
                    # Read a block of data (example block 8)
                    read_data = reader.MFRC522_Read(8)
                    if read_data:
                        print("Data in block 8:", read_data)
                    
                    # Stop the authentication
                    reader.MFRC522_StopCrypto1()
                else:
                    print("Authentication failed!")
            else:
                print("Anti-collision failed!")
        else:
            print("No card detected.")

        time.sleep(1)  # Delay before next attempt

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Exiting program...")
