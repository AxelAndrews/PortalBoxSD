# service.py - MicroPython version

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

# Definitions aka constants
DEFAULT_CONFIG_FILE_PATH = "config.json"

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
        
        # Connect to WiFi
        self.connect_wifi()
        
    def connect_wifi(self):
        """Connects to WiFi and prints the IP and MAC address."""
        print("Connecting to WiFi...")
        self.box.write_to_lcd("Connecting to")
        self.box.write_to_lcd("WiFi...")
        
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
                self.box.write_to_lcd(f"IP: {ip_address}")
                time.sleep(1)
                
                mac_bytes = wlan.config('mac')
                mac_hex = ''.join(['{:02x}'.format(b) for b in mac_bytes])
                print(f"Device MAC address: {mac_hex}")
                return True
            else:
                print("Could not connect to WiFi")
                self.box.write_to_lcd("WiFi Failed!")
                time.sleep(1)
                return False
        except Exception as e:
            print(f"WiFi connection failed: {e}")
            self.box.write_to_lcd("WiFi Error!")
            time.sleep(1)
            return False

    def connect_to_database(self):
        '''
        Connects to the database
        '''
        # connect to backend database
        print("Attempting to connect to database")
        self.box.write_to_lcd("Connecting to DB")

        try:
            self.db = Database(self.settings["db"])
            self.box.write_to_lcd("DB Connected!")
            time.sleep(0.5)
        except Exception as e:
            print(f"Unable to connect to database exception raised: {e}")
            self.box.write_to_lcd("DB Failed!")
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
        self.box.write_to_lcd("Getting Role...")
        
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
                self.box.write_to_lcd("Role Failed!")
                time.sleep(1)
                self.box.write_to_lcd("Retrying...")
                time.sleep(4)

        # only run if we have role, which we might not if we were asked to
        # shutdown before we discovered a role
        if profile[0] < 0:
            self.box.write_to_lcd("No Role Found!")
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
        self.box.write_to_lcd(f"{self.equipment_type}")
        time.sleep(0.5)
        self.box.write_to_lcd(f"Timeout: {self.timeout_minutes}m")
        time.sleep(0.5)
        
        # Log that we're started
        self.db.log_started_status(self.equipment_id)
        
        self.box.write_to_lcd("Ready!")
        time.sleep(0.5)

    def get_inputs(self, old_input_data):
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
        # Check for a card and get its ID
        card_id = self.box.read_RFID_card()
        print("Tried to read card")
        print(card_id)
        
        # Convert hex string to int if card was read
        card_id = int(card_id, 16) if card_id != -1 else -1
        
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
                    self.box.write_to_lcd("DB Error")
                    time.sleep(1)
                    self.box.write_to_lcd("Retrying...")
                    time.sleep(1)
                    if prev_display:
                        self.box.write_to_lcd(prev_display)
                    
            new_input_data = {
                "card_id": card_id,
                "user_is_authorized": details["user_is_authorized"],              
                "card_type": details["card_type"],
                "user_authority_level": details["user_authority_level"],
                "button_pressed": self.box.has_button_been_pressed()
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
                
            auth_str = "Auth" if new_input_data['user_is_authorized'] else "Unauth"
            
            # Print to console but don't update LCD - this was the issue!
            print(f"Card info: {card_type_str}-{auth_str}")

        # If no card is present, just update the button
        elif(card_id <= 0):
            new_input_data = {
                "card_id": -1,
                "user_is_authorized": False,
                "card_type": CardType.INVALID_CARD,
                "user_authority_level": 0,
                "button_pressed": self.box.has_button_been_pressed()
            }
        # Else just use the old data and update the button
        # i.e., if there is a card, but it's the same as before
        else:
            new_input_data = dict(old_input_data)  # Create a copy of the dictionary
            new_input_data["button_pressed"] = self.box.has_button_been_pressed()

        print(f"New input data: {new_input_data}")
        return new_input_data

    def update_display(self, state_name):
        """Update the LCD display with a centered state name"""
        if state_name == self.last_displayed_state:
            # Don't update if it's already displaying this state
            return
            
        # Center the state name on the display
        if len(state_name) > 16:
            # Truncate if too long
            display_name = state_name[:16]
        else:
            # Center the text
            padding = (16 - len(state_name)) // 2
            display_name = " " * padding + state_name
            
        self.box.write_to_lcd(display_name)
        self.last_displayed_state = display_name
        print(f"LCD updated to: '{display_name}'")

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
        self.box.write_to_lcd("Shutting down...")
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
            "website": "ec2-3-14-141-222.us-east-2.compute.amazonaws.com",
            "api": "box.php",
            "bearer_token": "290900415d2d7aac80229cdea4f90fbf"
        },
        "display": {
            "setup_color": "FF FF FF",
            "setup_color_db": "00 FF FF",
            "setup_color_email": "FF FF 00",
            "setup_color_role": "FF 00 FF",
            "auth_color": "00 FF 00",
            "proxy_color": "DF 20 00",
            "training_color": "80 00 80",
            "sleep_color": "00 00 FF",
            "unauth_color": "FF 00 00",
            "no_card_grace_color": "FF FF 00",
            "grace_timeout_color": "DF 20 00",
            "timeout_color": "FF 00 00",
            "unauth_card_grace_color": "FF 80 00",
            "flash_rate": 3,
            "enable_buzzer": True,
            "buzzer_pwm": True,
            "led_type": "NEOPIXEL"
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
            "BUTTON_PIN": 20,
            "RELAY_PIN": 7,
            "NEOPIXEL_PIN": 13,
            "ROW_PIN": 17,
            "COL_PIN": 16,
            "LCD_I2C_ADDR": "0x20",  # Hexadecimal values should be strings in the JSON
            "LCD_BUS": 0,
            "LCD_SDA": 18,
            "LCD_SCL": 19,
            "RFID_SDA": 3,
            "RFID_SCK": 2,
            "RFID_MOSI": 11,
            "RFID_MISO": 10
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
    if "display" in settings and "enable_buzzer" in settings["display"]:
        print(f"Buzzer enabled: {settings['display']['enable_buzzer']}")
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
            
            # Only update LCD if state class has changed
            if fsm_state.__class__ != last_state_class:
                service.update_display(current_state_name)
                last_state_class = fsm_state.__class__
            
            # Get inputs
            input_data_new = service.get_inputs(input_data)
            print(f"Input data: {input_data_new}")
            
            # Update input data dictionary
            for key in input_data:
                input_data[key] = input_data_new[key]
            
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
                
                if not skip_transition:
                    print(f"State transition occurred")
                    fsm_state = new_state
                    # Update display with new state
                    service.update_display(fsm_state.__class__.__name__)
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