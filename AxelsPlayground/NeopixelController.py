import neopixel
import board
import time

class NeoPixelController:
    def __init__(self, pin, num_pixels, brightness=0.2):
        """Initializes the NeoPixel controller.
        
        Args:
            pin (int): The GPIO pin where NeoPixels are connected.
            num_pixels (int): The number of NeoPixel LEDs.
            brightness (float): The brightness of the LEDs (between 0.0 and 1.0).
        """
        self.pin = pin
        self.num_pixels = num_pixels
        self.brightness = brightness
        
        # Set up the NeoPixel strip
        self.strip = neopixel.NeoPixel(
            getattr(board, pin),
            self.num_pixels,
            brightness=self.brightness,
            auto_write=False,
            pixel_order=neopixel.GRB
        )
    
    def set_color(self, color):
        """Sets all NeoPixels to a single color.
        
        Args:
            color (tuple): The RGB color to set (e.g., (255, 0, 0) for red).
        """
        for i in range(self.num_pixels):
            self.strip[i] = color
        self.strip.show()
