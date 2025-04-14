# DisplayController.py - Enhanced UI handling for PortalBox
import time

class DisplayController:
    """
    Manages enhanced LCD and LED display features for the PortalBox
    Coordinates messaging, colors, and visual feedback
    """
    def __init__(self, portal_box):
        """
        Initialize with reference to the PortalBox hardware abstraction
        
        Args:
            portal_box: Reference to PortalBox instance
        """
        self.box = portal_box
        self.last_message = ""
        self.last_color = ""
        self.grace_start_time = 0
        self.grace_total_time = 0
        self.progress_chars = ['-', '=', '=', '#']
        self.animation_frame = 0
        self.animation_last_update = 0
        
        # Color shortcuts
        self.colors = {
            "red": (0, 0, 255),
            "green": (255, 0, 0),
            "blue": (0, 255, 0),
            "yellow": (255, 255, 0),
            "magenta": (255, 0, 255),
            "cyan": (0, 255, 255),
            "white": (255, 255, 255),
            "orange": (255, 165, 0),
            "purple": (128, 0, 128)
        }
    
    def set_color(self, color_name):
        """
        Sets both LCD and DotStar LEDs to the same color
        
        Args:
            color_name: String name of color from self.colors
        """
        try:
            if color_name == self.last_color:
                return
                
            self.last_color = color_name
            self.box.setScreenColor(color_name)
            
            # Use existing dotstar if available
            if hasattr(self.box, 'dotstar'):
                color = self.colors.get(color_name.lower(), (0, 0, 255))# Default to blue
                if color_name.lower()=="blue":
                    self.box.dotstar.rainbow_cycle(1000)
                else:
                    self.box.dotstar.fill(color)
                self.box.dotstar.show()
        except Exception as e:
            print(f"Color setting error: {e}")
    
    def display_message(self, message, color=None):
        """
        Display a message on the LCD with optional color change
        
        Args:
            message: Text to display (will be centered if shorter than display)
            color: Optional color to set
        """
        try:
            if message == self.last_message and color == self.last_color:
                return
                
            self.last_message = message
            
            # Truncate if too long or center if shorter than display
            if len(message) > 16:
                display_text = message[:16]
            else:
                padding = (16 - len(message)) // 2
                display_text = " " * padding + message + " " * padding
                # If odd length, add one more space at the end
                if len(display_text) < 16:
                    display_text += " "
            
            self.box.lcd_print(display_text)
            
            if color:
                self.set_color(color)
        except Exception as e:
            print(f"Display message error: {e}")
    
    def display_two_line_message(self, line1, line2, color=None):
        """
        Display a two-line message on the LCD
        
        Args:
            line1: First line text
            line2: Second line text
            color: Optional color to set
        """
        try:
            composite_message = f"{line1}\n{line2}"
            if composite_message == self.last_message and color == self.last_color:
                return
                
            self.last_message = composite_message
            
            # Truncate lines to fit display
            if len(line1) > 16:
                line1 = line1[:16]
            if len(line2) > 16:
                line2 = line2[:16]
            
            # Clear and print each line directly
            self.box.lcd.clear()
            time.sleep(0.01)  # Short delay to allow clear to complete
            
            # Print first line
            self.box.lcd.set_cursor(1, 1)
            time.sleep(0.01)  # Short delay to ensure cursor position
            self.box.lcd.print(line1)
            time.sleep(0.01)  # Short delay between lines
            
            # Print second line
            self.box.lcd.set_cursor(1, 2)
            time.sleep(0.01)  # Short delay to ensure cursor position
            self.box.lcd.print(line2)
            
            if color:
                self.set_color(color)
        except Exception as e:
            print(f"Two-line display error: {e}")
    
    def display_welcome(self, user_id):
        """
        Display welcome message for authorized user
        
        Args:
            user_id: User ID to get name for
        """
        try:
            # Get user details from the database
            user_info = self.box.service.db.get_user(user_id)
            if user_info and user_info[0]:
                name = user_info[0].split(" ")[0]  # Get just the first name
                self.display_two_line_message("Welcome " + name, "Machine On", "green")
            else:
                self.display_two_line_message("Welcome", "Machine On", "green")
        except Exception as e:
            print(f"Error getting user: {e}")
            self.display_two_line_message("Welcome", "Machine On", "green")
    
    def start_grace_timer(self, total_seconds):
        """
        Start tracking grace period for progress display
        
        Args:
            total_seconds: Total grace period in seconds
        """
        try:
            self.grace_start_time = time.time()
            self.grace_total_time = total_seconds
        except Exception as e:
            print(f"Grace timer error: {e}")
    
    def update_grace_display(self):
        """
        Update the LCD with grace period countdown progress bar
        Returns remaining seconds
        """
        try:
            if self.grace_total_time <= 0:
                return 0
            
            elapsed = time.time() - self.grace_start_time
            remaining = max(0, self.grace_total_time - elapsed)
            
            # Create a simpler progress indicator
            progress_percent = (self.grace_total_time - remaining) / self.grace_total_time
            filled_chars = int(10 * progress_percent)
            progress_bar = "[" + "#" * filled_chars + "-" * (10 - filled_chars) + "]"
            
            # Format as "Insert Card" on first line, progress bar and timer on second
            time_str = f"{int(remaining)}s"
            self.display_two_line_message("Insert Card", progress_bar + " " + time_str, "yellow")
            
            return remaining
        except Exception as e:
            print(f"Grace display update error: {e}")
            return 0
    
    def display_idle_instructions(self):
        """Display instructions in idle mode"""
        try:
            self.display_two_line_message("Welcome!", "Scan Card to Use", "blue")
        except Exception as e:
            print(f"Idle instructions error: {e}")
    
    def display_card_id(self, card_id):
        """Display card ID information"""
        try:
            id_str = str(card_id) if card_id > 0 else "No Card"
            self.display_two_line_message("Card ID:", id_str, "cyan")
        except Exception as e:
            print(f"Card ID display error: {e}")
    
    def display_unauthorized(self):
        """Display unauthorized message"""
        try:
            self.display_two_line_message("Unauthorized", "Access Denied", "red")
        except Exception as e:
            print(f"Unauthorized display error: {e}")
    
    def animate_scanning(self, inputText):
        """
        Show a scanning animation while in card reading mode
        Should be called regularly from main loop
        """
        try:
            current_time = time.ticks_ms()
            
            # Update animation every 250ms
            if time.ticks_diff(current_time, self.animation_last_update) >= 250:
                self.animation_frame = (self.animation_frame + 1) % 4
                
                # Create animation string with dots
                dots = "." * self.animation_frame
                scan_text = f"Scanning{dots}"
                
                # Display the animation
                self.display_two_line_message(inputText, scan_text, "cyan")
                
                self.animation_last_update = current_time
        except Exception as e:
            print(f"Animation error: {e}")