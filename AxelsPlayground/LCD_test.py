"""Implements a HD44780 character LCD connected via MCP23008 on I2C.
   This code was based on pyb_i2c_adafruit_lcd.py at https://github.com/dhylands/python_lcd/blob/master/lcd/pyb_i2c_adafruit_lcd_test.py"""

from machine import I2C, Pin
import utime
from LCD_lib import I2cLcd

# The MCP23008 has a jumper selectable address: 0x20 - 0x27
LCD_I2C_ADDR = 0x20
BUS = 0
LCD_SDA = Pin(18, Pin.PULL_UP)
LCD_SCL = Pin(19, Pin.PULL_UP)

def test_main():
    """Test function for verifying basic functionality."""
    print("Running test_main")
    i2c = I2C(BUS, sda=LCD_SDA, scl=LCD_SCL, freq = 400000)
    lcd = I2cLcd(i2c, DEFAULT_I2C_ADDR, 2, 16)
    lcd.putstr("It Works!\nSecond Line")
    utime.sleep_ms(3000)
    lcd.clear()
    count = 0
    while True:
        lcd.move_to(0, 0)
        lcd.putstr("%7d" % (utime.ticks_ms() // 1000))
        utime.sleep_ms(1000)
        count += 1
        if count % 10 == 3:
            print("Turning backlight off")
            lcd.backlight_off()
        if count % 10 == 4:
            print("Turning backlight on")
            lcd.backlight_on()
        if count % 10 == 5:
            print("Turning display off")
            lcd.display_off()
        if count % 10 == 6:
            print("Turning display on")
            lcd.display_on()
        if count % 10 == 7:
            print("Turning display & backlight off")
            lcd.backlight_off()
            lcd.display_off()
        if count % 10 == 8:
            print("Turning display & backlight on")
            lcd.backlight_on()
            lcd.display_on()

#if __name__ == "__main__":
test_main()