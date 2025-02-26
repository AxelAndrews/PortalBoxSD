# import mfrc522
# from os import uname
# import board


# def do_read():

# 	if uname()[0] == 'WiPy':
# 		rdr = mfrc522.MFRC522("GP14", "GP16", "GP15", "GP22", "GP17")
# 	elif uname()[0] == 'samd51':
# 		rdr = mfrc522.MFRC522(board.SCK, board.MOSI, board.MISO, board.D5, board.SDA)
# 	else:
# 		raise RuntimeError("Unsupported platform: " + uname()[0])

# 	print("")
# 	print("Place card before reader to read from address 0x08")
# 	print("")

# 	try:
# 		while True:

# 			(stat, tag_type) = rdr.request(rdr.REQIDL)

# 			if stat == rdr.OK:

# 				(stat, raw_uid) = rdr.anticoll()

# 				if stat == rdr.OK:
# 					print("New card detected")
# 					print("  - tag type: 0x%02x" % tag_type)
# 					print("  - uid	 : 0x%02x%02x%02x%02x" % (raw_uid[0], raw_uid[1], raw_uid[2], raw_uid[3]))
# 					print("")

# 					if rdr.select_tag(raw_uid) == rdr.OK:

# 						key = [0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF]

# 						if rdr.auth(rdr.AUTHENT1A, 8, key, raw_uid) == rdr.OK:
# 							print("Address 8 data: %s" % rdr.read(8))
# 							rdr.stop_crypto1()
# 						else:
# 							print("Authentication error")
# 					else:
# 						print("Failed to select tag")

# 	except KeyboardInterrupt:
# 		print("Bye")

import mfrc522
from os import uname
import board
import time 


def do_read():
    start_time = time.time()  # Record the start time
    
    if uname()[0] == 'WiPy':
        rdr = mfrc522.MFRC522("GP14", "GP16", "GP15", "GP22", "GP17")
    elif uname()[0] == 'samd51':
        rdr = mfrc522.MFRC522(board.SCK, board.MOSI, board.MISO, board.D5, board.SDA)
    else:
        raise RuntimeError("Unsupported platform: " + uname()[0])

    print("")
    print("Place card before reader to read from address 0x08")
    print("")

    try:
        while True:
            # Check if 1 seconds have passed
            if time.time() - start_time > 1:
                return True
                break  # Stop the loop after 10 seconds

            (stat, tag_type) = rdr.request(rdr.REQIDL)

            if stat == rdr.OK:
                (stat, raw_uid) = rdr.anticoll()

                if stat == rdr.OK:
                    print("New card detected")
                    print("  - tag type: 0x%02x" % tag_type)
                    print("  - uid     : 0x%02x%02x%02x%02x" % (raw_uid[0], raw_uid[1], raw_uid[2], raw_uid[3]))
                    print("")

                    if rdr.select_tag(raw_uid) == rdr.OK:
                        key = [0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF]

                        if rdr.auth(rdr.AUTHENT1A, 8, key, raw_uid) == rdr.OK:
                            print("Address 8 data: %s" % rdr.read(8))
                            rdr.stop_crypto1()
                        else:
                            print("Authentication error")
                    else:
                        print("Failed to select tag")

    except KeyboardInterrupt:
        print("Bye")
