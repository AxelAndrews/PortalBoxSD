# service.py - MicroPython version with enhanced UI

# from the standard library
import time
import network # type: ignore
import gc
import json

# our code
import PortalFSM as fsm
from PortalBox import PortalBox
from Database import Database
from Database import CardType as CardType
from DisplayController import DisplayController
import Keypad

# Definitions aka constants
DEFAULT_CONFIG_FILE_PATH = "config.json"

# Common input data structure shared across states
input_data = {
    "card_id": 0,
    "user_is_authorized": False,
    "card_type": "none",
    "user_authority_level": 0,
    "button_pressed": False,
}

class PortalBoxApplication():
    """
    wrap code as a class to allow for clean sharing of objects
    between states
    """

    def __init__(self, settings):
        """
        Setup the bare minimum, deferring as much as possible to the run method
        """
        self.equipment_id = -1
        self.settings = settings
        self.running = False
        self.card_id = 0
        self.current_state_name = "Initializing"  # Track current state name
        self.last_displayed_state = ""  # Keep track of what's on the LCD
        self.lastUser=""
        
        # Set WiFi credentials from config if available
        self.WIFI_SSID = "bucknell_iot"
        self.WIFI_PASSWORD = ""
        
        if "wifi" in settings:
            if "ssid" in settings["wifi"]:
                self.WIFI_SSID = settings["wifi"]["ssid"]
            if "password" in settings["wifi"]:
                self.WIFI_PASSWORD = settings["wifi"]["password"]
                
        print(f"Using WiFi SSID: {self.WIFI_SSID}")
        
        # Initialize the box hardware
        print("Initializing PortalBox hardware...")
        self.box = PortalBox(settings)
        
        # Store reference to service in box for user lookups
        self.box.set_service(self)
        
        # Create the display controller
        self.display = DisplayController(self.box)
        
        # Special mode flag for RFID card reading
        self.in_card_reader_mode = False
        self.in_certification_mode= False
        
        # Connect to WiFi
        self.connect_wifi()
        
    def connect_wifi(self):
        """Connects to WiFi and prints the IP and MAC address."""
        print("Connecting to WiFi...")
        self.display.display_two_line_message("Connecting to", "WiFi...", "process_color")
        
        wlan = network.WLAN(network.STA_IF)
        wlan.active(True)
    
        try:
            wlan.connect(self.WIFI_SSID, self.WIFI_PASSWORD)
        
            # Wait for connection with timeout
            max_wait = 10
            while max_wait > 0:
                if wlan.isconnected():
                    break
                max_wait -= 1
                print("Waiting for connection...")
                time.sleep(1)
            
            if wlan.isconnected():
                ip_address = wlan.ifconfig()[0]
                print(f"Connected! IP: {ip_address}")
                self.display.display_two_line_message("WiFi Connected", f"IP: {ip_address}", "auth_color")
                time.sleep(1)
                
                mac_bytes = wlan.config('mac')
                mac_hex = ''.join(['{:02x}'.format(b) for b in mac_bytes])
                print(f"Device MAC address: {mac_hex}")
                return True
            else:
                print("Could not connect to WiFi")
                self.display.display_two_line_message("WiFi Failed!", "Check Settings", "unauth_color")
                time.sleep(1)
                return False
        except Exception as e:
            print(f"WiFi connection failed: {e}")
            self.display.display_two_line_message("WiFi Error!", f"{e}", "unauth_color")
            time.sleep(1)
            return False

    def connect_to_database(self):
        '''
        Connects to the database
        '''
        # connect to backend database
        print("Attempting to connect to database")
        self.display.display_message("Connecting to DB", "process_color")

        try:
            self.db = Database(self.settings["db"])
            self.display.display_message("DB Connected!", "auth_color")
            time.sleep(0.5)
        except Exception as e:
            print(f"Unable to connect to database exception raised: {e}")
            self.display.display_message("DB Failed!", "unauth_color")
            time.sleep(1)
            raise e

        print("Successfully connected to database")

    def getmac(self):
        """Get the MAC address as a string without colons"""
        sta_if = network.WLAN(network.STA_IF)
        mac = sta_if.config('mac')
        return ''.join(['%02x' % b for b in mac])

    def record_ip(self):
        """
        This gets the IP address for the box and then records it in the database
        """
        sta_if = network.WLAN(network.STA_IF)
        ip_address = sta_if.ifconfig()[0]
        self.db.record_ip(self.equipment_id, ip_address)

    def get_equipment_role(self):
        """
        Gets the equipments role from the database with the given mac address
        """
        # Determine what we are
        profile = (-1,)
        self.display.display_message("Getting Role...", "process_color")
        
        while profile[0] < 0:
            try:
                # Step 1 Figure out our identity
                print("Attempting to get mac address")
                mac_address = self.getmac()
                print(f"Successfully got mac address: {mac_address}")

                profile = self.db.get_equipment_profile(mac_address)
            except Exception as e:
                print(f"Error: {e}")
                print("Didn't get profile, trying again in 5 seconds")
                self.display.display_two_line_message("Role Failed!", "Retrying...", "unauth_color")
                time.sleep(5)

        # only run if we have role, which we might not if we were asked to
        # shutdown before we discovered a role
        if profile[0] < 0:
            self.display.display_message("No Role Found!", "unauth_color")
            time.sleep(1)
            raise RuntimeError("Cannot start, no role has been assigned")
        else:
            self.equipment_id = profile[0]
            self.equipment_type_id = profile[1]
            self.equipment_type = profile[2]
            self.location = profile[4]
            self.timeout_minutes = profile[5]
            self.allow_proxy = profile[6]
        
        print(f"Discovered identity. Type: {self.equipment_type}({self.equipment_type_id}) Timeout: {self.timeout_minutes} m Allows Proxy: {self.allow_proxy}")
        if self.timeout_minutes==0:
            self.display.display_two_line_message(f"{self.equipment_type}", 
                                                f"Timeout: {self.timeout_minutes}m", "admin_mode")
        else:
            self.display.display_two_line_message(f"No", 
                                                f"Timeout", "admin_mode")
        time.sleep(1)
        
        # Log that we're started
        self.db.log_started_status(self.equipment_id)
        
        self.display.display_message("Ready!", "auth_color")
        time.sleep(0.5)

    def get_inputs(self, old_input_data):
        """
        Gets new inputs for the FSM and returns the dictionary
        With improved card detection during grace period
        """
        print("Getting inputs for FSM")
        
        # Track state transitions for PIN verification
        # This helps us know when we need to force PIN verification
        if not hasattr(self, 'previous_state'):
            self.previous_state = None
        
        # Record the previous state for tracking transitions
        self.previous_state = self.current_state_name
        
        # Reset lastUser if we've transitioned to or from AccessComplete
        # This ensures PIN verification happens after a session ends
        if self.current_state_name == "AccessComplete" or self.previous_state == "AccessComplete":
            self.lastUser = 0
            print("Reset lastUser due to AccessComplete state transition")
        
        # Rest of the method remains unchanged...
        
        # Check for entering card reader mode specifically from IdleNoCard state
        if (self.current_state_name == "IdleNoCard" and 
            "*" in Keypad.scan_keypad() and 
            not self.in_card_reader_mode):
            
            print("*** Entering card reader mode ***")
            # Enter card reader mode
            self.in_card_reader_mode = True
            self.in_certification_mode= False
            self.display.display_two_line_message("Admin Card","Required", "admin_mode")
            self.box.beep_once('success')
            
            # Create a copy and reset button pressed to avoid side effects
            new_input_data = dict(old_input_data)
            new_input_data["button_pressed"] = False
            return new_input_data
        
        elif (self.current_state_name == "IdleNoCard" and 
            "#" in Keypad.scan_keypad() and 
            not self.in_certification_mode):
            
            print("*** Entering certification mode ***")
            # Enter certification mode
            self.in_card_reader_mode = False
            self.in_certification_mode = True
            self.cert_mode_state = 'init'  # Initialize state machine
            self.display.display_two_line_message("Admin Mode", "Starting...", "admin_mode")
            self.box.beep_once('success')
            
            # Create a copy and reset button pressed to avoid side effects
            new_input_data = dict(old_input_data)
            new_input_data["button_pressed"] = False
            return new_input_data
                
        if self.in_certification_mode:
            # Run card reader mode, exit if it returns False
            still_in_mode = self.handle_certification_mode()
            if not still_in_mode:
                self.in_certification_mode= False
                # Update display after exiting card Certification mode
                self.update_display_for_state(self.current_state_name)
                time.sleep(1)
                new_input_data = dict(old_input_data)
                return new_input_data
                
            # Create a copy and reset button pressed to avoid side effects
            new_input_data = dict(old_input_data)
            new_input_data["button_pressed"] = False
            return new_input_data
        
        # Normal input handling
        # Check for a card and get its ID
        card_id = self.box.read_RFID_card()
        print("Tried to read card")
        print(card_id)
        
        # Convert hex string to int if card was read
        card_id = int(card_id, 16) if card_id != -1 else -1
        
        # Check if this is a card removal event (old card present, new card not present)
        card_removal = (old_input_data["card_id"] > 0 and card_id <= 0)
        
        # FIXED: Removed the special case for RunningNoCard that was blocking new cards
        # This was preventing training mode from being entered properly
        
        # If a card was just removed and we're not in RunningNoCard state,
        # display a card removal message before continuing
        if card_removal and self.current_state_name not in ["IdleNoCard", "RunningNoCard"]:
            print("Card removal detected")
            self.display.display_message("Card Removed", "process_color")
            time.sleep(0.5)  # Short delay to show the message
        
        # If a card is present, and old_input_data showed either no card present, or a different card present
        if(card_id > 0 and card_id != old_input_data["card_id"]):
            print(f"Card with ID: {card_id} read, Getting info from DB")
            
            # Briefly show card ID but don't overwrite state display
            temp_lcd = f"Card: {card_id}"
            print(temp_lcd)
            # Don't update the LCD here to avoid interfering with state display
            
            while True:
                try:
                    details = self.db.get_card_details(card_id, self.equipment_type_id)
                    break
                except Exception as e:
                    print(f"Exception: {e}\n trying again")
                    # Only temporarily show error messages, then restore state
                    prev_display = self.last_displayed_state
                    self.display.display_message("DB Error", "unauth_color")
                    time.sleep(1)
                    self.display.display_message("Retrying...", "process_color")
                    time.sleep(1)
                    if prev_display:
                        self.display.display_message(prev_display)
                    
            new_input_data = {
                "card_id": card_id,
                "user_is_authorized": details["user_is_authorized"],              
                "card_type": details["card_type"],
                "user_authority_level": details["user_authority_level"],
                "button_pressed": self.box.has_button_been_pressed()[0],
                "pin": details['pin'],
                "card_removal": card_removal
            }
            
            # Only verify PIN if not in grace period to avoid interfering with training mode
            if self.current_state_name!="RunningNoCard":
                new_input_data["user_is_authorized"]=self.verifyPin(new_input_data["user_is_authorized"],new_input_data["pin"])
                self.lastUser=new_input_data["card_id"]
            
            # Handle card reader mode if active
            if self.in_card_reader_mode and new_input_data["user_is_authorized"]:
                # Run card reader mode, exit if it returns False
                self.in_card_reader_mode=self.handle_card_reader_mode(old_input_data['card_id'])
                new_input_data = dict(old_input_data)
                new_input_data["button_pressed"] = False
                return new_input_data
            else:
                self.in_card_reader_mode=False
                return new_input_data
                    
            # Log the card reading with the card type and ID
            print(f"Card of type: {new_input_data['card_type']} with ID: {new_input_data['card_id']} was read")
            
            # Create card type debug info for log but don't show on LCD
            card_type_str = "Unknown"
            if new_input_data['card_type'] == CardType.USER_CARD:
                card_type_str = "User"
            elif new_input_data['card_type'] == CardType.PROXY_CARD:
                card_type_str = "Proxy"
            elif new_input_data['card_type'] == CardType.TRAINING_CARD:
                card_type_str = "Training"
            elif new_input_data['card_type'] == CardType.SHUTDOWN_CARD:
                card_type_str = "Shutdown"
            print(f"Card type: {card_type_str}")

        # If no card is present, just update the button
        elif(card_id <= 0):
            new_input_data = {
                "card_id": -1,
                "user_is_authorized": False,
                "card_type": CardType.INVALID_CARD,
                "user_authority_level": 0,
                "button_pressed": self.box.has_button_been_pressed()[0],
                "pin": -1,
                "card_removal": card_removal
            }
        # Else just use the old data and update the button
        # i.e., if there is a card, but it's the same as before
        else:
            new_input_data = dict(old_input_data)  # Create a copy of the dictionary
            new_input_data["button_pressed"] = self.box.has_button_been_pressed()[0]
            new_input_data["card_removal"] = card_removal

        print(f"New input data: {new_input_data}")
        return new_input_data

    
    def get_inputs_padless(self, old_input_data):
        """
        Gets new inputs for the FSM and returns the dictionary

        @returns a dictionary of the form
                "card_id": (int)The card ID which was read,
                "user_is_authorized": (boolean) Whether or not the user is authorized,
                    for the current machine
                "card_type": (CardType enum) the type of card,
                "user_authority_level": (int) The authority of the user, 1 for normal user, 2 for trainer, 3 for admin
                "button_pressed": (boolean) whether or not the button has been
                    pressed since the last time it was checked
        """
        print("Getting inputs for FSM")
        
        # Normal input handling
        # Check for a card and get its ID
        card_id = self.box.read_RFID_card()
        print("Tried to read card")
        print(card_id)
        
        # Convert hex string to int if card was read
        card_id = int(card_id, 16) if card_id != -1 else -1
        
        # If a card is present, and old_input_data showed either no card present, or a different card present
        if(card_id > 0 and card_id != old_input_data["card_id"] and self.lastUser!=old_input_data["card_id"]):
            print(f"Card with ID: {card_id} read, Getting info from DB")
            
            # Briefly show card ID but don't overwrite state display
            temp_lcd = f"Card: {card_id}"
            print(temp_lcd)
            # Don't update the LCD here to avoid interfering with state display
            
            while True:
                try:
                    details = self.db.get_card_details(card_id, self.equipment_type_id)
                    break
                except Exception as e:
                    print(f"Exception: {e}\n trying again")
                    # Only temporarily show error messages, then restore state
                    prev_display = self.last_displayed_state
                    self.display.display_message("DB Error", "unauth_color")
                    time.sleep(1)
                    self.display.display_message("Retrying...", "process_color")
                    time.sleep(1)
                    if prev_display:
                        self.display.display_message(prev_display)
                    
            new_input_data = {
                "card_id": card_id,
                "user_is_authorized": details["user_is_authorized"],              
                "card_type": details["card_type"],
                "user_authority_level": details["user_authority_level"],
                "button_pressed": self.box.has_button_been_pressed(),
                "pin": details['pin']
            }
                    
            # Log the card reading with the card type and ID
            print(f"Card of type: {new_input_data['card_type']} with ID: {new_input_data['card_id']} was read")
            
            # Create card type debug info for log but don't show on LCD
            card_type_str = "Unknown"
            if new_input_data['card_type'] == CardType.USER_CARD:
                card_type_str = "User"
            elif new_input_data['card_type'] == CardType.PROXY_CARD:
                card_type_str = "Proxy"
            elif new_input_data['card_type'] == CardType.TRAINING_CARD:
                card_type_str = "Training"
            elif new_input_data['card_type'] == CardType.SHUTDOWN_CARD:
                card_type_str = "Shutdown"
            print(f"Card type: {card_type_str}")

        # If no card is present, just update the button
        elif(card_id <= 0):
            new_input_data = {
                "card_id": -1,
                "user_is_authorized": False,
                "card_type": CardType.INVALID_CARD,
                "user_authority_level": 0,
                "button_pressed": self.box.has_button_been_pressed(),
                "pin": -1
            }
        # Else just use the old data and update the button
        # i.e., if there is a card, but it's the same as before
        else:
            new_input_data = dict(old_input_data)  # Create a copy of the dictionary
            new_input_data["button_pressed"] = self.box.has_button_been_pressed()

        print(f"New input data: {new_input_data}")
        return new_input_data
    
    def loopRainbowCycle(self):
        """
        Displays a rainbow cycle on the LCD until a card is detected
        Fixed to handle type conversions properly
        """
        try:
            # Initial card read
            curr_card = self.box.read_RFID_card()
            
            # Loop until a card is detected
            while curr_card == -1:  # No card detected
                self.display.set_color("sleep_color")
                # Get new card state
                curr_card = self.box.read_RFID_card()
                time.sleep(0.1)  # Small delay to avoid excessive CPU usage
                
            # When card is detected, convert to int if it's a hex string
            if curr_card != -1:
                try:
                    # Only try to convert if it's a string (hex ID)
                    if isinstance(curr_card, str):
                        return int(curr_card, 16)
                    return curr_card
                except (ValueError, TypeError) as e:
                    print(f"Error converting card ID: {e}")
                    return -1
            
            return -1
        except Exception as e:
            print(f"Error in loopRainbowCycle: {e}")
            return -1
            
    def verifyPin(self, isAuthorized, userPin):
        """
        Verify user's PIN for authorized access
        
        Args:
            isAuthorized: Whether the user is initially authorized
            userPin: The PIN associated with the user
            
        Returns:
            bool: True if PIN is verified, False otherwise
        """
        # Important: If we're coming from AccessComplete, always require PIN verification
        # This prevents security issues when grace period expires
        force_verify = self.current_state_name in ["AccessComplete", "IdleUnknownCard"]
        
        # CRITICAL: If we're coming from AccessComplete or IdleUnknownCard, always verify PIN
        # regardless of isAuthorized status (force verification)
        if force_verify or isAuthorized == True:
            # Show clear message when forced verification is happening
            if force_verify:
                print("FORCED PIN VERIFICATION due to state:", self.current_state_name)
                
            # Ensure userPin is converted to string for comparison
            if userPin is None or userPin == -1:
                print("No PIN available for this user, denying access")
                self.display.display_two_line_message("Invalid PIN", "Access Denied", "unauth_color")
                time.sleep(1.5)
                return False
                    
            # Convert userPin to string if it's an integer
            userPin = str(userPin) if isinstance(userPin, int) else userPin
            
            attempts = 3  # Start with 3 attempts
            self.display.display_two_line_message("Please Enter Pin", "Attempts:" + str(attempts), "sleep_color")
            
            while attempts > 0:  # Run while attempts are greater than 0
                currPin = ""
                while len(currPin) < 4:  # Ensure the PIN is 4 digits long
                    # Check for card removal during PIN entry
                    card_id = self.box.read_RFID_card()
                    if card_id == -1:  # Card was removed
                        print("Card removed during PIN verification")
                        self.display.display_message("Card Removed", "unauth_color")
                        time.sleep(1)
                        return False
                    
                    # Convert card_id from hex string to integer if it's valid
                    try:
                        card_id = int(card_id, 16) if card_id != -1 else -1
                    except (ValueError, TypeError):
                        # Handle case where card_id is already an integer or invalid
                        if not isinstance(card_id, int):
                            card_id = -1
                    
                    # Check if card is still present
                    if card_id == -1:
                        print("Card removed during PIN verification")
                        self.display.display_message("Card Removed", "unauth_color")
                        time.sleep(1)
                        return False
                    
                    # Get the pressed button
                    button_pressed = self.box.has_button_been_pressed()[1]
                    
                    # Check if a button was pressed and it contains a digit
                    if button_pressed and len(button_pressed) > 0:
                        # Ensure we have a valid integer in the button_pressed list
                        try:
                            if isinstance(button_pressed[0], int):
                                digit = str(button_pressed[0])  # Convert the number to a string
                                print(digit)
                                currPin += digit  # Append the digit to the PIN
                                
                                # Display PIN with masking
                                pinStar = "*" * len(currPin)  # Shows masked PIN
                                
                                self.display.display_two_line_message(
                                    "Pin:" + pinStar, 
                                    "Attempts:" + str(attempts), 
                                    "sleep_color"
                                )
                        except (IndexError, TypeError) as e:
                            print(f"Button press error: {e}")
                    
                    time.sleep(0.1)  # Small delay to avoid excessive CPU usage
                
                # Check if the entered PIN matches the user's PIN
                print(f"Comparing PINs: entered={currPin}, user={userPin}")
                if currPin == userPin:
                    print("PIN verified successfully")
                    self.display.display_message("PIN Correct", "auth_color")
                    time.sleep(0.5)
                    return True
                elif len(currPin) == 4 and attempts > 1:
                    self.display.display_message("Incorrect Pin", "unauth_color")
                    time.sleep(0.5)
                    self.display.display_two_line_message("Pin:", "Attempts:" + str(attempts-1), "sleep_color")
                
                # Decrement attempts after a failed attempt
                attempts -= 1
                
                if attempts == 0:
                    self.display.display_message("Incorrect Pin", "unauth_color")
                    time.sleep(1)
                    self.display.display_message("Please Retry!", "unauth_color")
                    return False
        
        # If we get here, the user is not authorized or something went wrong
        return False
                
    def handle_card_reader_mode(self, old_input):
        """
        Handles the card reader mode, showing card IDs when cards are detected
        Fixed to properly handle type conversions and avoid crashes
        """
        try:
            time.sleep(1)
            old_card_id = old_input
            
            while True:
                # Check for exit command (* key)
                if "*" in Keypad.scan_keypad() and not self.box.has_button_been_pressed()[0]:
                    print("Exiting card reader mode")
                    self.display.display_two_line_message("Exiting", "Card Reader Mode", "sleep_color")
                    time.sleep(1)
                    self.cert_mode_state = 'init'  # Reset state for next time
                    self.display.display_two_line_message("Welcome!", "Scan Card to Use", "sleep_color")
                    
                    # Don't call loopRainbowCycle on exit to avoid potential crashes
                    # Just return False to exit the mode
                    return False
                
                # Read card
                card_id = self.box.read_RFID_card()
                
                # Handle animation and display
                if card_id == -1 and old_card_id == -1:
                    # No card detected, show animation
                    self.display.animate_scanning("Card ID Reader")
                elif card_id == old_card_id:
                    # Same card still present, no update needed
                    pass
                else:
                    # New card detected, display ID
                    try:
                        # Only convert to int if card_id is a string (hex ID)
                        if card_id != -1 and isinstance(card_id, str):
                            decimal_val = int(card_id, 16)
                            self.display.display_two_line_message("Card ID:", f"{decimal_val}", "admin_mode")
                    except (ValueError, TypeError) as e:
                        print(f"Error converting card ID: {e}")
                        # Show error but continue
                        self.display.display_two_line_message("Card Error", "Try Again", "unauth_color")
                        time.sleep(1)
                
                # Update old card ID for next iteration
                old_card_id = card_id
                
                # Small delay to avoid excessive CPU usage
                time.sleep(0.1)
        
        except Exception as e:
            print(f"Error in card reader mode: {e}")
            self.display.display_two_line_message("Error", "Exiting Mode", "unauth_color")
            time.sleep(1)
            return False
            
        # Should never reach here due to while True loop, but added for completeness
        return True
    
    def handle_certification_mode(self):
        """
        Admin mode for granting machine access authorization to new users
        This mode requires an admin/trainer card followed by the user card to be authorized
        Returns True if still in this mode, False if exiting
        """
        try:
            time.sleep(1)
            # Step 1: Initial state - waiting for admin card
            if not hasattr(self, 'cert_mode_state') or self.cert_mode_state == 'init':
                self.cert_mode_state = 'waiting_admin'
                self.admin_card_id = None
                self.user_card_id = None
                self.display.display_two_line_message("Admin Mode", "Scan Admin Card", "admin_mode")
            
            # Check for exit button press (# key)
            if "#" in Keypad.scan_keypad():
                print("Exiting admin certification mode")
                self.display.display_two_line_message("Exiting", "Admin Mode", "sleep_color")
                time.sleep(1)
                self.cert_mode_state = 'init'  # Reset state for next time
                self.display.display_two_line_message("Welcome!", "Scan Card to Use", "sleep_color")
                self.loopRainbowCycle()
                return False
            
            # Step 2: Waiting for admin card
            if self.cert_mode_state == 'waiting_admin':
                # Show scanning animation
                self.display.animate_scanning("Scan Admin Card")
                
                # Try reading a card
                card_id = self.box.read_RFID_card()
                
                # If card read successful
                if card_id != -1:
                    try:
                        decimal_id = int(card_id, 16)
                        
                        # Verify this is an admin/trainer card
                        details = self.db.get_card_details(decimal_id, self.equipment_type_id)
                        details["user_is_authorized"]=self.verifyPin(details["user_is_authorized"],details["pin"])
                        
                        if details["user_authority_level"] >= 3 and details["user_is_authorized"]:  # Admin or trainer level
                            # Admin card accepted
                            self.admin_card_id = decimal_id
                            self.cert_mode_state = 'waiting_user'
                            self.display.display_two_line_message("Admin Verified", "Remove Card", "auth_color")
                            self.box.beep_once('success')
                            time.sleep(1)
                            
                            # Wait for admin to remove card
                            self.display.display_two_line_message("Admin Mode", "Remove Card", "process_color")
                            
                            # Wait for card removal
                            waiting_removal = True
                            start_time = time.time()
                            while waiting_removal and (time.time() - start_time < 10):  # 10 second timeout
                                if self.box.read_RFID_card() == -1:  # No card detected
                                    waiting_removal = False
                                time.sleep(0.2)
                            
                            self.display.display_two_line_message("Admin Mode", "Scan User Card", "process_color")
                        else:
                            # Not an admin card
                            self.display.display_two_line_message("Not Admin Card", "Need Admin Card", "unauth_color")
                            self.box.beep_once('error')
                            time.sleep(1)
                            self.display.display_two_line_message("Admin Mode", "Scan Admin Card", "admin_mode")
                    except Exception as e:
                        print(f"Error processing admin card: {e}")
                        self.display.display_two_line_message("Card Error", "Try Again", "unauth_color")
                        self.box.beep_once('error')
                        time.sleep(1)
            
            # Step 3: Waiting for user card
            elif self.cert_mode_state == 'waiting_user':
                # Show scanning animation
                self.display.animate_scanning("Scan User Card")
                
                # Try reading a card
                card_id = self.box.read_RFID_card()
                
                # If card read successful
                if card_id != -1:
                    try:
                        decimal_id = int(card_id, 16)
                        
                        # Verify this is a user card and not already authorized
                        details = self.db.get_card_details(decimal_id, self.equipment_type_id)
                        
                        if details["card_type"] == CardType.USER_CARD:
                            if details["user_is_authorized"]:
                                # Already authorized
                                self.display.display_two_line_message("Already Auth", "No Change Needed", "process_color")
                                self.box.beep_once('warning')
                                time.sleep(1)
                                self.cert_mode_state = 'init'
                                # self.display.display_two_line_message("Welcome!", "Scan Card to Use", "sleep_color")
                                self.display.display_message("Press # to Exit", "process_color")
                                while "#" not in Keypad.scan_keypad():
                                    time.sleep(0.5)
                                print("Exiting admin certification mode")
                                self.display.display_two_line_message("Exiting", "Admin Mode", "sleep_color")
                                time.sleep(1)
                                self.display.display_two_line_message("Welcome!", "Scan Card to Use", "sleep_color")
                                self.cert_mode_state = 'init'  # Reset state for next time
                                self.loopRainbowCycle()
                                return False
                            else:
                                # User needs authorization - proceed to update
                                self.user_card_id = decimal_id
                                self.cert_mode_state = 'updating'
                                self.display.display_two_line_message("User Card OK", "Authorizing...", "sleep_color")
                        else:
                            # Not a user card
                            self.display.display_two_line_message("Not User Card", "Need User Card", "unauth_color")
                            self.box.beep_once('error')
                            time.sleep(1)
                            self.display.display_two_line_message("Admin Mode", "Scan User Card", "process_color")
                    except Exception as e:
                        print(f"Error processing user card: {e}")
                        self.display.display_two_line_message("Card Error", "Try Again", "unauth_color")
                        self.box.beep_once('error')
                        time.sleep(1)
            
            # Step 4: Updating authorization
            elif self.cert_mode_state == 'updating':
                try:
                    # Make API call to update user authorization
                    success = self.update_user_authorization(self.user_card_id)
                    
                    if success:
                        self.display.display_two_line_message("Authorization", "Successful!", "auth_color")
                        self.box.beep_once('success')
                        time.sleep(1.5)
                        self.display.display_message("Press # to Exit", "process_color")
                        while "#" not in Keypad.scan_keypad():
                            time.sleep(0.5)
                        print("Exiting admin certification mode")
                        self.display.display_two_line_message("Exiting", "Admin Mode", "sleep_color")
                        time.sleep(1)
                        self.display.display_two_line_message("Welcome!", "Scan Card to Use", "sleep_color")
                        self.cert_mode_state = 'init'
                    else:
                        self.display.display_two_line_message("Auth Failed", "DB Error", "unauth_color")
                        self.box.beep_once('error')
                    
                    time.sleep(2)
                    self.cert_mode_state = 'init'  # Reset for next time
                    return False
                except Exception as e:
                    print(f"Error updating authorization: {e}")
                    self.display.display_two_line_message("Update Error", "Try Again Later", "unauth_color")
                    self.box.beep_once('error')
                    time.sleep(2)
                    self.cert_mode_state = 'init'  # Reset for next time
                    return False
            
            # Continue in certification mode
            return True
        except Exception as e:
            print(f"Error in certification mode: {e}")
            # Exit certification mode on error
            return False
        
    def update_user_authorization(self, user_card_id):
        """
        Updates a user's authorization for the current equipment type
        
        Args:
            user_card_id: The card ID of the user to authorize
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            print(f"Updating authorization for user card {user_card_id} on equipment type {self.equipment_type_id}")
            
            # First, get the user ID associated with this card
            user_info = self.db.get_user(user_card_id)
            if not user_info or len(user_info) < 2 or not user_info[0]:
                print("Failed to retrieve user info from card")
                return False
                
            # Get user ID from card if possible
            user_id = None
            try:
                # Fetch user details from the card - this is implementation-dependent
                # This might require an additional API call to get the user ID
                # For now, we'll simulate this by getting the user's info from the card
                
                # Try to get existing authorizations
                current_details = self.db.get_card_details(user_card_id, self.equipment_type_id)
                
                # We need to add our current equipment type to the user's authorizations
                # Make API call to update authorizations using our Database class method
                response = self.db.add_user_authorization(user_card_id, self.equipment_type_id)
                
                # Check for success
                if response is True or (isinstance(response, str) and "success" in response.lower()):
                    print(f"Successfully authorized user for equipment type {self.equipment_type_id}")
                    return True
                else:
                    print(f"Authorization failed with response: {response}")
                    return False
                    
            except Exception as e:
                print(f"Error updating authorization: {e}")
                return False
                
            return False
        except Exception as e:
            print(f"Exception in update_user_authorization: {e}")
            return False

    def update_display_for_state(self, state_name, card_id=-1):
        """Update the display based on current state and context"""
        # if state_name == self.last_displayed_state and (not self.in_card_reader_mode or not self.in_certification_mode):
        if state_name == self.last_displayed_state and (not self.in_card_reader_mode):

            # Don't update if it's already displaying this state
            return
            
        self.last_displayed_state = state_name
        print(f"Updating display for state: {state_name}")
        
        if state_name == "IdleNoCard":
            self.display.display_idle_instructions()
            
        elif state_name == "RunningAuthUser":
            # Display personalized welcome if possible
            if card_id > 0:
                self.display.display_welcome(card_id)
            else:
                self.display.display_two_line_message("Authorized", "Machine On", "auth_color")
                
        elif state_name == "RunningTrainingCard":
            self.display.display_two_line_message("Training Mode", "Machine On", self.settings["display"]["training_color"])
            
        elif state_name == "RunningProxyCard":
            self.display.display_two_line_message("Proxy Access", "Machine On", "proxy_color")
            
        elif state_name == "IdleUnauthCard":
            self.display.display_unauthorized()
            
        elif state_name == "RunningNoCard":
            # Start grace timer if not already started
            if not hasattr(self, 'grace_timer_started') or not self.grace_timer_started:
                self.display.start_grace_timer(self.settings["user_exp"]["grace_period"])
                self.grace_timer_started = True
            
        elif state_name == "Setup":
            self.display.display_message("Setting Up...", "process_color")
            
        elif state_name == "Shutdown":
            self.display.display_message("Shutting Down...", "unauth_color")
            
        # Other states use default display from their on_enter methods
        else:
            # Center the state name on the display
            if len(state_name) > 16:
                # Truncate if too long
                display_name = state_name[:16]
            else:
                # Center the text
                padding = (16 - len(state_name)) // 2
                display_name = " " * padding + state_name
                
            # self.display.display_message(display_name)

    def update_grace_display_if_needed(self):
        """Update grace period countdown if in RunningNoCard state"""
        if self.current_state_name == "RunningNoCard" and hasattr(self, 'grace_timer_started') and self.grace_timer_started:
            remaining = self.display.update_grace_display()
            if remaining <= 0:
                # Grace period ended, reset flag
                self.grace_timer_started = False
                return True  # Indicate grace period has ended
        return False  # Grace period still running or not in grace period

    def get_user_auths(self, card_id):
        '''
        Determines whether or not the user is authorized for the equipment type
        @return a boolean of whether or not the user is authorized for the equipment
        '''
        return self.db.is_user_authorized_for_equipment_type(card_id, self.equipment_type_id)

    def shutdown(self, card_id=1):
        '''
        Stops the program
        '''
        print("Service Exiting")
        self.display.display_message("Shutting down...", "unauth_color")
        self.box.cleanup()

        if self.equipment_id:
            print("Logging exit-while-running to DB")
            self.db.log_shutdown_status(self.equipment_id, card_id)
        self.running = False


# Load configuration
def load_config(config_file_path=DEFAULT_CONFIG_FILE_PATH):
    """
    Loads configuration from JSON file with fallback defaults
    """
    print(f"Loading configuration from {config_file_path}")
    
    # Default configuration
    default_config = {
    "db": {
            "user": "admin",
            "password": "PORTALBOX",
            "host": "portalboxdb.cbwumiue49n9.us-east-2.rds.amazonaws.com",
            "database": "portalboxdb",
            "website": "makerportal-steam.com",
            "api": "box.php",
            "bearer_token": "290900415d2d7aac80229cdea4f90fbf"
        },
        "display": {
            "setup_color":         [255, 255, 255],   
            "setup_color_db":      [255, 255, 0],    
            "setup_color_email":   [255, 0, 255],     
            "setup_color_role":    [0, 255, 255],     
            "auth_color":          [255, 0, 0],       
            "proxy_color":         [32, 0, 223],      
            "training_color":      [0, 128, 128],     
            "sleep_color":         [0, 255, 0],       
            "unauth_color":        [0, 0, 255],
            "admin_mode":          [153, 255, 204],
            "no_card_grace_color": [255, 0, 255],     
            "grace_timeout_color": [32, 0, 223],      
            "timeout_color":       [0, 0, 255],       
            "unauth_card_grace_color": [128, 0, 255],
            "flash_rate": 3,
            "led_type": "DOTSTAR"
        },
        "user_exp": {
            "grace_period": 10
        },
        "wifi": {
            "ssid": "bucknell_iot",
            "password": ""
        },
        "pins": {
            "INTERLOCK_PIN": 9,
            "BUZZER_PIN": 6,
            "RELAY_PIN": 7,
            "DOTSTAR_DATA": 13,
            "DOTSTAR_CLOCK": 12,
            "LCD_TX": 5,
            "RFID_SDA": 3,
            "RFID_SCK": 2,
            "RFID_MOSI": 11,
            "RFID_MISO": 10,
            "SINGLE_BUTTON": 4,
            "KEYPAD_1": 15,
            "KEYPAD_2": 23,
            "KEYPAD_3": 22,
            "KEYPAD_4": 21,
            "KEYPAD_5": 20,
            "KEYPAD_6": 19,
            "KEYPAD_7": 18
        }
        ,
        "toggles": {
            "enable_buzzer": False,
            "buzzer_pwm": False,
            "enable_keypad": True,
            "enable_LCDScreen": True
        }
  }
    
    # Try to load from file
    try:
        with open(config_file_path, 'r') as f:
            file_config = json.load(f)
            print("Successfully loaded config from file")
            
            # Merge the loaded config with defaults
            # This ensures all required keys exist even if not in the file
            merged_config = default_config.copy()
            
            # Update top-level sections 
            for section in file_config:
                if section in merged_config:
                    # If section exists in defaults, update values
                    if isinstance(merged_config[section], dict) and isinstance(file_config[section], dict):
                        merged_config[section].update(file_config[section])
                    else:
                        # Direct replacement for non-dict sections
                        merged_config[section] = file_config[section]
                else:
                    # Add new sections
                    merged_config[section] = file_config[section]
            
            return merged_config
            
    except Exception as e:
        print(f"Error loading config file {config_file_path}: {e}")
        print("Using default configuration")
        return default_config


# Main entry point
def main():
    # Load configuration
    settings = load_config()
    
    # Print config summary
    print("\n--- Configuration Summary ---")
    if "toggles" in settings and "enable_buzzer" in settings["toggles"]:
        print(f"Buzzer enabled: {settings['toggles']['enable_buzzer']}")
    if "user_exp" in settings and "grace_period" in settings["user_exp"]:
        print(f"Grace period: {settings['user_exp']['grace_period']}s")
    if "pins" in settings:
        print(f"Custom pin configuration: {len(settings['pins'])} pins defined")
    print("---------------------------\n")

    # Create Portal Box Service
    print("Creating PortalBoxApplication")
    service = PortalBoxApplication(settings)

    # Create finite state machine
    print("Creating FSM initial state")
    fsm_state = fsm.Setup(service, input_data)
    last_state_class = fsm_state.__class__
    
    # Run service
    print("Running the FSM")
    service.running = True
    
    try:
        while service.running:
            print("\n---- New loop iteration ----")
            current_state_name = fsm_state.__class__.__name__
            print(f"CURRENT FSM STATE: {current_state_name}")
            service.current_state_name = current_state_name
            
            # Update display for current state if changed
            if fsm_state.__class__ != last_state_class:
                service.update_display_for_state(current_state_name, input_data["card_id"])
                last_state_class = fsm_state.__class__
            
            # Update grace period display if needed
            service.update_grace_display_if_needed()
            
            # Get inputs
            if settings["toggles"]["enable_keypad"]==True:
                input_data_new = service.get_inputs(input_data)
            else:
                input_data_new = service.get_inputs_padless(input_data)
            print(f"Input data: {input_data_new}")
            
            # Handle card removal - if card was just removed, don't show additional messages
            # Jump directly to the appropriate state based on the current state
            card_removed = input_data_new.get("card_removal", False)
            if card_removed and current_state_name not in ["IdleNoCard", "RunningNoCard", "Shutdown"]:
                print("Card removal detected - transitioning to appropriate state")
                
                # If card was removed while machine was running, go to RunningNoCard (grace period)
                if current_state_name in ["RunningAuthUser", "RunningProxyCard", "RunningTrainingCard"]:
                    print("Card removed while machine was running - entering grace period")
                    # Create a new RunningNoCard state
                    fsm_state = fsm.RunningNoCard(service, input_data_new)
                    service.grace_timer_started = True
                    service.update_display_for_state("RunningNoCard", -1)
                    last_state_class = fsm_state.__class__
                else:
                    # For other states, go to IdleNoCard
                    print("Card removed - returning to idle state")
                    fsm_state = fsm.IdleNoCard(service, input_data_new)
                    service.update_display_for_state("IdleNoCard", -1)
                    last_state_class = fsm_state.__class__
                
                # Update input data dictionary
                for key in input_data:
                    if key in input_data_new:
                        input_data[key] = input_data_new[key]
                
                service.box.update()
                # Skip the rest of the loop to avoid processing the FSM with the removed card
                continue
            
            # Update input data dictionary
            for key in input_data:
                if key in input_data_new:
                    input_data[key] = input_data_new[key]
            
            # Skip state machine processing if in card reader mode
            if service.in_card_reader_mode:
                service.box.update()
                time.sleep(0.1)
                continue

            # ADD THIS CODE HERE: Check if grace period has ended naturally
            # Update grace period display and check if it has ended
            if service.current_state_name == "RunningNoCard":
                grace_ended = service.update_grace_display_if_needed()
                if grace_ended:
                    # Grace period ended naturally, transition to AccessComplete
                    print("Grace period ended via display timer")
                    fsm_state = fsm.AccessComplete(service, input_data)
                    service.update_display_for_state(fsm_state.__class__.__name__, input_data["card_id"])
                    last_state_class = fsm_state.__class__
                    service.box.update()
                    continue
            
            # Call the state handler which might return a new state
            print(f"Calling FSM state: {fsm_state.__class__.__name__}")
            new_state = fsm_state(input_data)
            
            # Check if we need to transition state
            if new_state:
                # Special case: prevent bouncing between RunningNoCard and RunningUnknownCard 
                # for unauthorized cards during grace period
                skip_transition = False
                if (new_state.__class__.__name__ == "RunningNoCard" and 
                    fsm_state.__class__.__name__ == "RunningUnknownCard" and
                    fsm.FSM_STATE["last_state_name"] == "RunningNoCard"):
                    # We're trying to go back to RunningNoCard from RunningUnknownCard
                    # But we were in RunningNoCard before - this is a bounce situation
                    # Don't transition, stay in RunningUnknownCard
                    if not input_data["user_is_authorized"] and input_data["card_type"] == CardType.USER_CARD:
                        print(f"Preventing state bounce - staying in {fsm_state.__class__.__name__}")
                        skip_transition = True
                
                # IMPORTANT: Force lastUser reset when transitioning to/from AccessComplete
                # This ensures PIN verification after grace period expiration
                if (new_state.__class__.__name__ == "AccessComplete" or 
                    fsm_state.__class__.__name__ == "AccessComplete"):
                    service.lastUser = 0
                    input_data["user_is_authorized"] = False  # Force re-verification
                    print("Reset lastUser and auth status due to AccessComplete transition")
                
                if not skip_transition:
                    print(f"State transition occurred")
                    fsm_state = new_state
                    # Reset grace timer flag on state transition
                    service.grace_timer_started = False
                    # Update display with new state
                    service.update_display_for_state(fsm_state.__class__.__name__, input_data["card_id"])
                    last_state_class = fsm_state.__class__
            
            print(f"After FSM call, state is: {fsm_state.__class__.__name__}")
            
            service.box.update()
            # Memory management and brief pause
            gc.collect()
            time.sleep(0.1)
            # If the FSM is in the Shutdown state, then stop running the while loop
            if fsm_state.__class__.__name__ == "Shutdown":
                break
                
    except KeyboardInterrupt:
        print("Keyboard interrupt detected")
    except Exception as e:
        print(f"Error in main loop: {e}")
        import sys
        sys.print_exception(e)
    finally:
        print("FSM ends")
        # Cleanup
        service.box.cleanup()
        print("Service shutdown complete")


if __name__ == "__main__":
    main()