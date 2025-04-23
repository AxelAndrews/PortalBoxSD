"""
Test program for the DotStar LED library on ESP32-C6
"""
import time
from DotstarController import DotStar, RED, GREEN, BLUE, YELLOW, CYAN, PURPLE, WHITE, ORANGE

def main():
    print("Initializing DotStar LED strip...")
    
    # Initialize the DotStar controller
    # Using GPIO 13 for data and GPIO 12 for clock as specified
    strip = DotStar(spi_bus=1, data_pin=13, clock_pin=12, num_leds=15, brightness=16)
    
    try:
        # Test 1: Basic colors
        print("Testing basic colors...")
        colors = [RED, GREEN, BLUE, YELLOW, CYAN, PURPLE, WHITE, ORANGE]
        for color in colors:
            strip.fill(color)
            strip.show()
            time.sleep(0.5)
        
        # Test 2: Color wipe animation
        print("Testing color wipe animation...")
        strip.color_wipe(RED, 1000)  # Red wipe over 1 second
        # Wait for the animation to complete
        while strip.is_wiping:
            strip.update_animations()
            time.sleep_ms(10)
        
        time.sleep(0.5)  # Pause between animations
        
        # Test 3: Blinking animation
        print("Testing blinking animation...")
        strip.blink(BLUE, 2000, 5)  # Blink blue 5 times over 2 seconds
        # Wait for the animation to complete
        while strip.is_blinking:
            strip.update_animations()
            time.sleep_ms(10)
        
        time.sleep(0.5)  # Pause between animations
        
        # Test 4: Pulse animation
        print("Testing pulse animation...")
        strip.pulse(GREEN)  # Pulse green
        # Run the pulse animation for 5 seconds
        start_time = time.ticks_ms()
        while time.ticks_diff(time.ticks_ms(), start_time) < 5000:
            strip.update_animations()
            time.sleep_ms(10)
        
        # Stop the pulsing animation
        strip.stop_animations()
        
        # Test 5: Individual pixel control
        print("Testing individual pixel control...")
        strip.fill((0, 0, 0))  # Clear all LEDs
        strip.show()
        time.sleep(0.5)
        
        # Light up each LED in sequence
        for i in range(strip.num_leds):
            strip.set_pixel(i, RED)
            strip.show()
            time.sleep(0.1)
        
        time.sleep(0.5)  # Pause between animations
        
        # Test 6: Rainbow cycle
        print("Testing rainbow cycle animation...")
        for _ in range(2):  # Do 2 cycles
            strip.rainbow_cycle(1000)  # One rainbow cycle over 1 second
        
        # Final test: Brightness control
        print("Testing brightness control...")
        strip.fill(WHITE)
        
        # Fade from low to high brightness
        for brightness in range(1, 32):
            strip.set_brightness(brightness)
            strip.show()
            time.sleep(0.05)
        
        # Fade from high to low brightness
        for brightness in range(31, 0, -1):
            strip.set_brightness(brightness)
            strip.show()
            time.sleep(0.05)
        
        print("Test complete!")
        
    finally:
        # Ensure LEDs are turned off when done
        print("Cleaning up...")
        strip.cleanup()

if __name__ == "__main__":
    main()