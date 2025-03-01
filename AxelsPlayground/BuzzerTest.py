from BuzzerController import BuzzerController
import time
import sys

def main():
    print("Buzzer Controller Test Script")
    
    # Initialize buzzer controller
    try:
        buzzer = BuzzerController()
        print("Buzzer Controller initialized successfully")
    except Exception as e:
        print(f"Failed to initialize Buzzer Controller: {e}")
        sys.exit(1)
    
    # Test 1: Simple tone
    print("\nTest 1: Single Tone")
    buzzer.buzz_tone(800, 1.0)  # 800 Hz for 1 second
    
    # Main loop to handle updates
    start_time = time.ticks_ms()
    while time.ticks_diff(time.ticks_ms(), start_time) < 1500:
        buzzer.update()
        time.sleep_ms(100)
    
    # Test 2: Beeping
    print("\nTest 2: Beeping")
    buzzer.beep(500, duration=2.0, beeps=5)  # 500 Hz, 2 seconds, 5 beeps
    
    # Main loop to handle updates
    start_time = time.ticks_ms()
    while time.ticks_diff(time.ticks_ms(), start_time) < 3000:
        buzzer.update()
        time.sleep_ms(100)
    
    # Test 3: Song playback (create a simple song file first)
    print("\nTest 3: Song Playback")
    try:
        # Create a simple song file
        with open('test_song.txt', 'w') as f:
            # Format: Note,Duration (in 4th octave)
            f.write("C4,0.5\n")
            f.write("D4,0.5\n")
            f.write("E4,0.5\n")
            f.write("F4,0.5\n")
        
        # Play the song
        buzzer.play_song('test_song.txt')
        
        # Main loop to handle updates
        start_time = time.ticks_ms()
        while time.ticks_diff(time.ticks_ms(), start_time) < 3000:
            buzzer.update()
            time.sleep_ms(100)
    
    except Exception as e:
        print(f"Error during song playback: {e}")
    
    # Final shutdown
    print("\nShutting down Buzzer Controller")
    buzzer.shutdown_buzzer()
    print("Test complete!")

# Run the test
if __name__ == '__main__':
    main()