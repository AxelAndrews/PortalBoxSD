# service.py - MicroPython version

# from the standard library
import sys
import time
import network # type: ignore
import gc
from machine import Pin # type: ignore

# our code
import PortalFSM as fsm
# import PortalBox
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
        self.box = PortalBox(settings)
        self.settings = settings
        self.running = False
        self.card_id = 0
        self.WIFI_SSID="bucknell_iot"
        self.WIFI_PASSWORD=""
        self.connect_wifi()
        
    def connect_wifi(self):
        """Connects to WiFi and prints the IP and MAC address."""
        print("Connecting to WiFi...")
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
                print(f"Connected! IP: {wlan.ifconfig()[0]}")
                mac_bytes = wlan.config('mac')
                mac_hex = ''.join(['{:02x}'.format(b) for b in mac_bytes])
                print(f"Device MAC address: {mac_hex}")
                return True
            else:
                print("Could not connect to WiFi")
                return False
        except Exception as e:
            print(f"WiFi connection failed: {e}")
            return False

    def connect_to_database(self):
        '''
        Connects to the database
        '''
        # connect to backend database
        print("Attempting to connect to database")

        try:
            self.db = Database(self.settings["db"])
        except Exception as e:
            print(f"Unable to connect to database exception raised: {e}")
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
                time.sleep(5)

        # only run if we have role, which we might not if we were asked to
        # shutdown before we discovered a role
        if profile[0] < 0:
            raise RuntimeError("Cannot start, no role has been assigned")
        else:
            self.equipment_id = profile[0]
            self.equipment_type_id = profile[1]
            self.equipment_type = profile[2]
            self.location = profile[4]
            self.timeout_minutes = profile[5]
            self.allow_proxy = profile[6]
        
        print(f"Discovered identity. Type: {self.equipment_type}({self.equipment_type_id}) Timeout: {self.timeout_minutes} m Allows Proxy: {self.allow_proxy}")
        self.db.log_started_status(self.equipment_id)

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
        # Check for a card and get its ID
        card_id = self.box.read_RFID_card()

        # If a card is present, and old_input_data showed either no card present, or a different card present
        if(card_id > 0 and card_id != old_input_data["card_id"]):
            print(f"Card with ID: {card_id} read, Getting info from DB")
            while True:
                try:
                    details = self.db.get_card_details(card_id, self.equipment_type_id)
                    break
                except Exception as e:
                    print(f"Exception: {e}\n trying again")
                    time.sleep(1)
                    
            new_input_data = {
                "card_id": card_id,
                "user_is_authorized": details["user_is_authorized"],              
                "card_type": details["card_type"],
                "user_authority_level": details["user_authority_level"],
                "button_pressed": self.box.has_button_been_pressed()
            }

            # Log the card reading with the card type and ID
            print(f"Card of type: {new_input_data['card_type']} with ID: {new_input_data['card_id']} was read")

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

        return new_input_data

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
        self.box.cleanup()

        if self.equipment_id:
            print("Logging exit-while-running to DB")
            self.db.log_shutdown_status(self.equipment_id, card_id)
        self.running = False


# Load configuration
def load_config(config_file_path=DEFAULT_CONFIG_FILE_PATH):
    import json
    
    try:
        with open(config_file_path, 'r') as f:
            settings = json.load(f)
        return settings
    except:
        print(f"Error loading config file: {config_file_path}")
        return None


# Main entry point
def main():
    # Load configuration
    settings = load_config()
    if not settings:
        print("Failed to load configuration. Exiting.")
        sys.exit(1)

    # Create Portal Box Service
    print("Creating PortalBoxApplication")
    service = PortalBoxApplication(settings)

    # Create finite state machine
    fsm_instance = fsm.Setup(service, input_data)

    # Run service
    print("Running the FSM")
    service.running = True
    try:
        while service.running:
            input_data_new = service.get_inputs(input_data)
            # Update the global input_data
            for key in input_data:
                input_data[key] = input_data_new[key]
            
            fsm_instance(input_data)
            
            # Free memory to avoid potential memory issues
            gc.collect()
            
            # Brief sleep to prevent CPU hogging
            time.sleep(0.01)
            
            # If the FSM is in the Shutdown state, then stop running the while loop
            if fsm_instance.__class__.__name__ == "Shutdown":
                break
    except KeyboardInterrupt:
        print("Keyboard interrupt detected")
    except Exception as e:
        print(f"Error in main loop: {e}")
    finally:
        print("FSM ends")
        # Cleanup
        service.box.cleanup()
        print("Service shutdown complete")


if __name__ == "__main__":
    main()