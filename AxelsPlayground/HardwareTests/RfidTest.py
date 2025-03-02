from MFRC522 import MFRC522

# Code derived from https://github.com/Tasm-Devil/micropython-mfrc522-esp32/tree/master

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