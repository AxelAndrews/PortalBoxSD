import neopixel
import board
import time

class NeoPixelController:
    def __init__(self, pin=13, numPixels=15, brightness=0.2, setting=None):
        """Initializes the NeoPixel controller.
        
        Args:
            pin (int): The GPIO pin where NeoPixels are connected.
            numPixels (int): The number of NeoPixel LEDs.
            brightness (float): The brightness of the LEDs (between 0.0 and 1.0).
        """
        self.pin = pin
        self.numPixels = numPixels
        self.brightness = brightness
        
        # Set up the NeoPixel strip
        self.strip = neopixel.NeoPixel(
            getattr(board, pin),
            self.numPixels,
            brightness=self.brightness,
            auto_write=False,
            pixel_order=neopixel.RGB
        )
    
    def set_color(self, color):
        """Sets all NeoPixels to a single color.
        
        Args:
            color (tuple): The RGB color to set (e.g., (255, 0, 0) for red).
        """
        for i in range(self.numPixels):
            self.strip[i] = color
        self.strip.show()
