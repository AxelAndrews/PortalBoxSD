"""
DotStar LED library for ESP32-C6 in MicroPython
Controls DotStar LEDs (APA102/SK9822) via SPI interface

Based on the PortalBox implementation but optimized for MicroPython on ESP32
"""
import time
import math
from machine import SPI, Pin, SoftSPI

# Color constants
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
WHITE = (255, 255, 255)
YELLOW = (255, 255, 0)
CYAN = (0, 255, 255)
MAGENTA = (255, 0, 255)
ORANGE = (255, 165, 0)
PURPLE = (128, 0, 128)

class DotStar:
    """
    Class to control DotStar LED strips/arrays via SPI
    
    The DotStar protocol requires:
    - Start frame: 4 bytes of 0x00
    - LED frames: 4 bytes per LED (0xE0 + brightness, blue, green, red)
    - End frame: 4 bytes of 0xFF (or (n/2) / 16 bytes of 0x00 for SK9822)
    """
    
    def __init__(self, spi_bus=1, data_pin=13, clock_pin=12, num_leds=15, brightness=16):
        """
        Initialize the DotStar controller
        
        Args:
            spi_bus: SPI bus number (1 or 2)
            data_pin: GPIO pin for SPI MOSI (data)
            clock_pin: GPIO pin for SPI SCK (clock)
            num_leds: Number of LEDs in the strip
            brightness: Default brightness level (0-31)
        """
        self.num_leds = num_leds
        self.brightness = brightness
        self.leds = [(0, 0, 0)] * num_leds  # Initialize all LEDs as off
        
        print("Starting.........")
        # Configure SPI bus
        self.spi = SPI(spi_bus, 
                    baudrate=1000000,  # 1 MHz
                    polarity=0, 
                    phase=0,
                    sck=Pin(clock_pin),
                    mosi=Pin(data_pin),
                    miso=Pin(4))  # No MISO needed for DotStar
        
        
        print("Made SPI Bus for Dotstars")
        
        # Initialize state variables for animations
        self.is_pulsing = False
        self.pulse_color = BLACK
        self.pulse_rising = False
        self.pulse_brightness = brightness
        self.pulse_min_brightness = 1
        self.pulse_max_brightness = 31
        self.pulse_step = 2
        
        self.is_blinking = False
        self.blink_color = BLACK
        self.blink_duration = 0
        self.blink_count = 0
        self.blink_last_toggle = 0
        self.blink_state = False
        
        self.is_wiping = False
        self.wipe_color = BLACK
        self.wipe_position = 0
        self.wipe_last_update = 0
        self.wipe_duration = 0
        
        # Clear the LEDs on startup
        self.fill(BLACK)
        self.show()
    
    def _write_bytes(self, data):
        """Write bytes to the SPI bus"""
        self.spi.write(bytearray(data))
    
    def show(self):
        """Update the LED strip with current colors"""
        # Start frame - 4 bytes of 0
        self._write_bytes([0x00, 0x00, 0x00, 0x00])
        
        # LED frames - 4 bytes per LED
        for r, g, b in self.leds:
            # Format: [0xE0 + brightness, blue, green, red]
            self._write_bytes([0xE0 | self.brightness, b, g, r])
            
        # End frame - SK9822 compatible
        # For SK9822, need at least (num_leds / 16) + 1 bytes of 0x00
        end_frame_length = (self.num_leds // 16) + 1
        self._write_bytes([0x00] * end_frame_length)
    
    def fill(self, color):
        """Fill the entire strip with a single color"""
        self.leds = [color] * self.num_leds
    
    def set_pixel(self, index, color):
        """Set a specific pixel to a color"""
        if 0 <= index < self.num_leds:
            self.leds[index] = color
    
    def set_brightness(self, brightness):
        """Set the global brightness level (0-31)"""
        if 0 <= brightness <= 31:
            self.brightness = brightness
    
    def color_wipe(self, color, duration_ms=1000):
        """
        Start a color wipe animation
        
        Args:
            color: RGB tuple (r, g, b)
            duration_ms: Total duration of the wipe in milliseconds
        """
        self.is_pulsing = False
        self.is_blinking = False
        self.is_wiping = True
        self.wipe_color = color
        self.wipe_position = 0
        self.wipe_duration = duration_ms
        self.wipe_last_update = time.ticks_ms()
        
        # Calculate time per LED
        self.wipe_step_ms = duration_ms // self.num_leds
        if self.wipe_step_ms < 10:
            self.wipe_step_ms = 10  # Minimum 10ms per LED for smooth animation
        
        # Set the first LED
        self.set_pixel(0, color)
        self.show()
    
    def blink(self, color, duration_ms=1000, count=5):
        """
        Start a blinking animation
        
        Args:
            color: RGB tuple (r, g, b)
            duration_ms: Total duration of all blinks in milliseconds
            count: Number of blinks (on-off cycles)
        """
        self.is_pulsing = False
        self.is_wiping = False
        self.is_blinking = True
        self.blink_color = color
        self.blink_count = count * 2  # Each count is one on-off cycle (2 states)
        self.blink_duration = duration_ms
        
        # Calculate time per blink state
        self.blink_step_ms = duration_ms // (count * 2)
        if self.blink_step_ms < 50:
            self.blink_step_ms = 50  # Minimum 50ms per state for visible blinking
        
        self.blink_state = True
        self.blink_last_toggle = time.ticks_ms()
        
        # Set initial state (on)
        self.fill(color)
        self.show()
    
    def pulse(self, color):
        """
        Start a pulsing animation (fading in and out)
        
        Args:
            color: RGB tuple (r, g, b)
        """
        self.is_blinking = False
        self.is_wiping = False
        self.is_pulsing = True
        self.pulse_color = color
        self.pulse_rising = False  # Start by decreasing brightness
        self.pulse_brightness = self.brightness
        
        # Set the color
        self.fill(color)
        self.show()
    
    def update_animations(self):
        """Update any running animations - call this in your main loop"""
        current_time = time.ticks_ms()
        
        if self.is_wiping:
            # Check if it's time to update the wipe
            if time.ticks_diff(current_time, self.wipe_last_update) >= self.wipe_step_ms:
                self.wipe_position += 1
                
                if self.wipe_position < self.num_leds:
                    self.set_pixel(self.wipe_position, self.wipe_color)
                    self.show()
                    self.wipe_last_update = current_time
                else:
                    self.is_wiping = False
        
        if self.is_blinking:
            # Check if it's time to toggle the blink state
            if time.ticks_diff(current_time, self.blink_last_toggle) >= self.blink_step_ms:
                self.blink_count -= 1
                self.blink_state = not self.blink_state
                
                if self.blink_count > 0:
                    if self.blink_state:
                        self.fill(self.blink_color)
                    else:
                        self.fill(BLACK)
                    self.show()
                    self.blink_last_toggle = current_time
                else:
                    self.is_blinking = False
                    self.fill(BLACK)
                    self.show()
        
        if self.is_pulsing:
            # Update pulse every 50ms
            if time.ticks_diff(current_time, getattr(self, 'pulse_last_update', 0)) >= 50:
                if self.pulse_rising:
                    self.pulse_brightness += self.pulse_step
                    if self.pulse_brightness >= self.pulse_max_brightness:
                        self.pulse_brightness = self.pulse_max_brightness
                        self.pulse_rising = False
                else:
                    self.pulse_brightness -= self.pulse_step
                    if self.pulse_brightness <= self.pulse_min_brightness:
                        self.pulse_brightness = self.pulse_min_brightness
                        self.pulse_rising = True
                
                self.brightness = self.pulse_brightness
                self.show()
                self.pulse_last_update = current_time
    
    def rainbow_cycle(self, duration_ms=1000):
        """
        Display a cycling rainbow pattern
        
        Args:
            duration_ms: Duration of one full cycle in milliseconds
        """
        self.is_pulsing = False
        self.is_blinking = False
        self.is_wiping = False
        
        step_time = duration_ms // 256
        
        for j in range(256):
            for i in range(self.num_leds):
                # Calculate color based on position and cycle
                pos = (i * 256 // self.num_leds + j) % 256
                self.set_pixel(i, self._wheel(pos))
            self.show()
            time.sleep_ms(step_time)
    
    def _wheel(self, pos):
        """
        Color wheel helper for rainbow effects
        
        Args:
            pos: Position on wheel (0-255)
        
        Returns:
            RGB tuple
        """
        # Convert wheel position to RGB color
        if pos < 85:
            return (255 - pos * 3, pos * 3, 0)
        elif pos < 170:
            pos -= 85
            return (0, 255 - pos * 3, pos * 3)
        else:
            pos -= 170
            return (pos * 3, 0, 255 - pos * 3)
    
    def stop_animations(self):
        """Stop all animations"""
        self.is_pulsing = False
        self.is_blinking = False
        self.is_wiping = False

    def cleanup(self):
        """Turn off all LEDs and release resources"""
        self.fill(BLACK)
        self.show()
        # No need to explicitly close SPI in MicroPython