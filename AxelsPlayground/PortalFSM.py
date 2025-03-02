# portal_fsm.py for ESP32-C6 MicroPython
"""
The finite state machine for the portal box service.
Adapted from the original Raspberry Pi implementation to MicroPython for ESP32-C6.
"""
# Standard library
import time
import gc

# Our code - adjust imports based on your file structure
from Database import CardType

# Use simpler time handling for MicroPython
class SimpleDateTime:
    @staticmethod
    def now():
        return time.time()

class SimpleTimeDelta:
    def __init__(self, seconds=0, minutes=0):
        self.seconds = seconds + (minutes * 60)
    
    def total_seconds(self):
        return self.seconds

# Simple replacement for datetime in MicroPython
datetime = SimpleDateTime
timedelta = SimpleTimeDelta

# Global state variables for FSM (this is a critical change for MicroPython)
# These variables will be shared across all state instances
FSM_STATE = {
    "auth_user_id": -1,
    "proxy_id": -1,
    "training_id": -1,
    "user_authority_level": 0,
    "allow_proxy": 0,
    "last_state_name": ""
}

class State(object):
    """The parent state for all FSM states."""

    def __init__(self, portal_box_service, input_data):
        self.service = portal_box_service
        self.timeout_start = datetime.now()
        self.grace_start = datetime.now()
        self.timeout_delta = timedelta(0)
        self.grace_delta = timedelta(seconds=10)
        self.flash_rate = 3
        
        # Initialize allow_proxy from the service if available
        if hasattr(self.service, 'allow_proxy'):
            FSM_STATE["allow_proxy"] = self.service.allow_proxy
            
        self.on_enter(input_data)

    def next_state(self, cls, input_data):
        """Transition to a new state by creating a new instance of the state class"""
        print(f"State transition: {self.__class__.__name__} -> {cls.__name__}")
        print(f"Before transition - auth_user_id: {FSM_STATE['auth_user_id']}, authority: {FSM_STATE['user_authority_level']}")
        
        # Record where we're coming from
        FSM_STATE["last_state_name"] = self.__class__.__name__
        
        # Create a new instance of the target state class
        new_state = cls(self.service, input_data)
        
        # Copy configuration settings to the new state instance
        new_state.timeout_delta = self.timeout_delta
        new_state.grace_delta = self.grace_delta
        new_state.flash_rate = self.flash_rate
        
        # State variables are now global so no need to copy them
        print(f"After transition - auth_user_id: {FSM_STATE['auth_user_id']}, authority: {FSM_STATE['user_authority_level']}")
        return new_state

    def on_enter(self, input_data):
        """
        A default on_enter() method that centers the state name on a 16x2 LCD
        """
        state_name = self.__class__.__name__
        print(f"Entering state {state_name}")
        
        # Determine centering for a 16-character wide LCD
        if len(state_name) > 16:
            # Truncate if too long
            display_name = state_name[:16]
        else:
            # Center the text
            padding = (16 - len(state_name)) // 2
            display_name = " " * padding + state_name
        
        self.service.box.write_to_lcd(display_name)

    def timeout_expired(self):
        """
        Determines whether or not the timeout period has expired
        @return a boolean which is True when the timeout period has expired
        """
        if (
            self.service.timeout_minutes > 0 and  # The timeout period for the equipment type isn't infinite
            (datetime.now() - self.timeout_start) > self.timeout_delta.total_seconds()  # And it has actually timed out
        ):
            print(f"Timeout period expired with time passed = {datetime.now() - self.timeout_start}")
            return True
        else:
            return False

    def grace_expired(self):
        """
        Determines whether or not the grace period has expired
        @return a boolean which is True when the grace period has expired
        """
        if (datetime.now() - self.grace_start) > self.grace_delta.total_seconds():
            print(f"Grace period expired with time passed = {datetime.now() - self.grace_start}")
            return True
        else:
            return False

class Setup(State):
    """
    The first state, tries to setup everything that needs to be setup and goes
    to shutdown if it can't
    """
    def __call__(self, input_data):
        print("Setup state __call__ method")
        # First time running through setup
        if not hasattr(self, 'setup_completed') or not self.setup_completed:
            print("First time in setup, initializing...")
            self.setup_completed = True
            try:
                self.service.connect_to_database()
                self.service.get_equipment_role()
                
                self.timeout_delta = timedelta(minutes=self.service.timeout_minutes)
                
                # Set grace period (default to 10 seconds if not specified)
                grace_period = 10
                if "user_exp" in self.service.settings and "grace_period" in self.service.settings["user_exp"]:
                    try:
                        grace_period = int(self.service.settings["user_exp"]["grace_period"])
                        print(f"Grace period set to {grace_period} seconds")
                    except ValueError:
                        pass
                
                self.grace_delta = timedelta(seconds=grace_period)
                FSM_STATE["allow_proxy"] = self.service.allow_proxy
                self.flash_rate = 3

                print(f"Setup complete: timeout={self.service.timeout_minutes}m, grace={grace_period}s, allow_proxy={FSM_STATE['allow_proxy']}")
                self.service.box.beep_once('success')
                
                print("Setup complete, transitioning to IdleNoCard...")
                next_state = self.next_state(IdleNoCard, input_data)
                return next_state
            except Exception as e:
                print(f"Setup failed: {e}")
                next_state = self.next_state(Shutdown, input_data)
                self.service.box.beep_once('error')
                return next_state
        return None

    def on_enter(self, input_data):
        super().on_enter(input_data)
        print("Starting setup")
        try:
            try:
                self.service.connect_to_database()
            except Exception as e:
                print(f"Database connection failed: {e}")
                raise e

            try:
                self.service.get_equipment_role()
            except Exception as e:
                print(f"Getting equipment role failed: {e}")
                raise e

            self.timeout_delta = timedelta(minutes=self.service.timeout_minutes)
            
            # Get grace period from settings, with a default of 10 seconds
            grace_period = 10
            if "user_exp" in self.service.settings and "grace_period" in self.service.settings["user_exp"]:
                try:
                    grace_period = int(self.service.settings["user_exp"]["grace_period"])
                    print(f"Grace period set to {grace_period} seconds")
                except ValueError:
                    pass
                    
            self.grace_delta = timedelta(seconds=grace_period)
            
            # Save the allow_proxy setting from the service
            if hasattr(self.service, 'allow_proxy'):
                FSM_STATE["allow_proxy"] = self.service.allow_proxy
                print(f"Using allow_proxy={FSM_STATE['allow_proxy']} from service")
            else:
                print("Warning: service.allow_proxy not found, using default value of 0")
                FSM_STATE["allow_proxy"] = 0
                
            self.flash_rate = 3
            
            # Free up memory after setup is complete
            gc.collect()
            print("Setup completed successfully")
            self.service.box.beep_once('success')
            
        except Exception as e:
            print(f"Unable to complete setup, exception raised: {e}")
            self.service.box.beep_once('error')
            raise e

class Shutdown(State):
    """
    Shuts down the box
    """
    def __call__(self, input_data):
        print("Shutdown state called, powering off equipment")
        self.service.box.set_equipment_power_on(False)
        self.service.shutdown(input_data["card_id"])
        return None

    def on_enter(self, input_data):
        super().on_enter(input_data)
        print("Entering shutdown state")
        self.service.box.set_equipment_power_on(False)
        self.service.shutdown(input_data["card_id"])

class IdleNoCard(State):
    """
    The state that it will spend the most time in, waits for some card input
    """
    def __call__(self, input_data):
        if input_data["card_id"] > 0:
            return self.next_state(IdleUnknownCard, input_data)
        return None

    def on_enter(self, input_data):
        super().on_enter(input_data)
        print("In IDLENOCARD - waiting for card input")

class AccessComplete(State):
    """
    Before returning to the Idle state it logs the machine usage, and turns off
    the power to the machine
    """
    def __call__(self, input_data):
        # The call should immediately transition to IdleNoCard after cleanup
        return self.next_state(IdleNoCard, input_data)

    def on_enter(self, input_data):
        super().on_enter(input_data)
        print("Usage complete, logging usage and turning off machine")
        self.service.db.log_access_completion(FSM_STATE["auth_user_id"], self.service.equipment_id)
        self.service.box.set_equipment_power_on(False)
        
        # Reset all state variables
        FSM_STATE["proxy_id"] = 0
        FSM_STATE["training_id"] = 0
        FSM_STATE["auth_user_id"] = 0
        FSM_STATE["user_authority_level"] = 0

class IdleUnknownCard(State):
    """
    A card input has been read, the next state is determined by the card type
    """
    def __call__(self, input_data):
        print(f"IdleUnknownCard __call__ with input: card_id={input_data['card_id']}, type={input_data['card_type']}")
        print(f"user_is_authorized: {input_data['user_is_authorized']}")
        
        if input_data["card_type"] == CardType.SHUTDOWN_CARD:
            print(f"Inserted a shutdown card, shutting the box down")
            return self.next_state(Shutdown, input_data)
        
        # Check if the user is authorized, regardless of card type
        elif input_data["user_is_authorized"]:
            # If it's a user card, go to normal running state
            if input_data["card_type"] == CardType.USER_CARD:
                print(f"Authorized user card, transitioning to RunningAuthUser")
                return self.next_state(RunningAuthUser, input_data)
            # If it's a training card and authorized, handle it properly
            elif input_data["card_type"] == CardType.TRAINING_CARD:
                print(f"Authorized training card, transitioning to RunningAuthUser")
                return self.next_state(RunningAuthUser, input_data)
            # If it's a proxy card and authorized, handle it properly
            elif input_data["card_type"] == CardType.PROXY_CARD:
                print(f"Authorized proxy card, transitioning to RunningProxyCard")
                return self.next_state(RunningProxyCard, input_data)
            else:
                print(f"Authorized card of unknown type: {input_data['card_type']}")
                return self.next_state(RunningAuthUser, input_data)
        
        else:
            print(f"Unauthorized card with id {input_data['card_id']}, type: {input_data['card_type']}")
            return self.next_state(IdleUnauthCard, input_data)

    def on_enter(self, input_data):
        super().on_enter(input_data)
        print(f"Entering IdleUnknownCard state. Card ID: {input_data['card_id']}, Card Type: {input_data['card_type']}")

class RunningUnknownCard(State):
    """
    A Card has been read from the no card grace period
    """
    def __call__(self, input_data):
        print(f"Is USER? {input_data['card_type'] == CardType.USER_CARD}")
        print(f"User authority level: {FSM_STATE['user_authority_level']}")
        print(f"Proxy Id: {FSM_STATE['proxy_id']}")
        print(f"Allow proxy: {FSM_STATE['allow_proxy']}")
        print(f"Previous state: {FSM_STATE['last_state_name']}")
        print(f"Auth user ID: {FSM_STATE['auth_user_id']}")
        
        # Debug logging to help diagnose training mode issues
        print(f"Training mode check: Card type is USER_CARD? {input_data['card_type'] == CardType.USER_CARD}")
        print(f"Training mode check: Authority level >= 3? {FSM_STATE['user_authority_level'] >= 3}")
        print(f"Training mode check: Not from proxy (proxy_id <= 0)? {FSM_STATE['proxy_id'] <= 0}")
        print(f"Training mode check: Not from training or same card? {FSM_STATE['training_id'] <= 0 or FSM_STATE['training_id'] == input_data['card_id']}")
        print(f"Training mode check: Not authorized? {not input_data['user_is_authorized']}")
        
        # Coming from RunningNoCard (during grace period)
        coming_from_no_card = FSM_STATE["last_state_name"] == "RunningNoCard"
        
        # Proxy card during grace period
        if (
            input_data["card_type"] == CardType.PROXY_CARD and
            FSM_STATE["training_id"] <= 0 and
            coming_from_no_card
        ):
            # If the machine allows proxy cards then go into proxy mode
            if FSM_STATE["allow_proxy"] == 1:
                print(f"Allowing proxy card since allow_proxy={FSM_STATE['allow_proxy']}")
                return self.next_state(RunningProxyCard, input_data)
            # Otherwise go into a grace period 
            else:
                print(f"Not allowing proxy card since allow_proxy={FSM_STATE['allow_proxy']}")
                return self.next_state(RunningUnauthCard, input_data)

        # If it's the same user as before then just go back to auth user
        elif input_data["card_id"] == FSM_STATE["auth_user_id"]:
            return self.next_state(RunningAuthUser, input_data)

        # Check for training mode conditions
        # 1. Card is a USER_CARD
        # 2. Coming from RunningNoCard (during grace period)
        # 3. Original user had authority level >= 3
        # 4. Not coming from proxy mode
        # 5. Either not from training mode OR this is the same trainee
        # 6. Current card is not authorized
        if (
            input_data["card_type"] == CardType.USER_CARD and
            coming_from_no_card and 
            FSM_STATE["user_authority_level"] >= 3 and
            FSM_STATE["proxy_id"] <= 0 and
            (FSM_STATE["training_id"] <= 0 or FSM_STATE["training_id"] == input_data["card_id"]) and
            not input_data["user_is_authorized"]
        ):
            print("All training mode criteria met! Entering RunningTrainingCard")
            return self.next_state(RunningTrainingCard, input_data)
        
        # Any other card during grace period, stay in grace period
        elif coming_from_no_card:
            print("Unknown card during grace period, staying in RunningNoCard")
            return self.next_state(RunningNoCard, input_data)

        # Check if time expired
        elif self.grace_expired():
            print("Exiting Grace period because the grace period expired")
            return self.next_state(AccessComplete, input_data)
            
        # Check if button pressed
        elif input_data["button_pressed"]:
            print("Exiting Grace period because button was pressed")
            return self.next_state(AccessComplete, input_data)
            
        return None

    def on_enter(self, input_data):
        super().on_enter(input_data)
        print("Card detected during grace period")

class RunningAuthUser(State):
    """
    An authorized user has put their card in, the machine will function
    """
    def __call__(self, input_data):
        if input_data["card_id"] <= 0:
            return self.next_state(RunningNoCard, input_data)

        if self.timeout_expired():
            return self.next_state(RunningTimeout, input_data)
            
        return None

    def on_enter(self, input_data):
        super().on_enter(input_data)
        print("Authorized card in box, turning machine on and logging access")
        self.timeout_start = datetime.now()
        FSM_STATE["proxy_id"] = 0
        FSM_STATE["training_id"] = 0
        self.service.box.set_equipment_power_on(True)
        self.service.box.beep_once('success')

        # If the card is new, not coming from a timeout, then log as a new session
        if FSM_STATE["auth_user_id"] != input_data["card_id"]:
            self.service.db.log_access_attempt(input_data["card_id"], self.service.equipment_id, True)
            # Save the user's authority level for future state transitions
            FSM_STATE["auth_user_id"] = input_data["card_id"]
            FSM_STATE["user_authority_level"] = input_data["user_authority_level"]
            print(f"Set user authority level to {FSM_STATE['user_authority_level']} from input data")

class IdleUnauthCard(State):
    """
    An unauthorized card has been put into the machine, turn off machine
    """
    def __call__(self, input_data):
        if input_data["card_id"] <= 0:
            return self.next_state(IdleNoCard, input_data)
        return None

    def on_enter(self, input_data):
        super().on_enter(input_data)
        print("Unauthorized card detected, turning off equipment")
        self.service.box.beep_once('error')
        self.service.box.set_equipment_power_on(False)
        self.service.db.log_access_attempt(input_data["card_id"], self.service.equipment_id, False)

class RunningNoCard(State):
    """
    An authorized card has been removed, waits for a new card until the grace
    period expires, or a button is pressed
    """
    def __call__(self, input_data):
        # Card detected
        if input_data["card_id"] > 0 and input_data["card_type"] != CardType.INVALID_CARD:
            # Make sure the state knows where the authority level is coming from
            print(f"Card detected in grace period, authority level: {FSM_STATE['user_authority_level']}")
            return self.next_state(RunningUnknownCard, input_data)

        if self.grace_expired():
            print("Exiting Grace period because the grace period expired")
            return self.next_state(AccessComplete, input_data)
                
        if input_data["button_pressed"]:
            print("Exiting Grace period because button was pressed")
            return self.next_state(AccessComplete, input_data)
            
        return None

    def on_enter(self, input_data):
        super().on_enter(input_data)
        print(f"Grace period started - card removed. Auth user: {FSM_STATE['auth_user_id']}, Authority: {FSM_STATE['user_authority_level']}")
        self.grace_start = datetime.now()
        self.service.box.start_beeping()

class RunningUnauthCard(State):
    """
    A card type which isn't allowed on this machine has been read while the machine is running, 
    gives the user time to put back their authorized card
    """
    def __call__(self, input_data):
        # Card detected and its the same card that was using the machine before the unauth card was inserted 
        if (
            input_data["card_id"] > 0 and
            input_data["card_id"] == FSM_STATE["auth_user_id"]
        ):
            return self.next_state(RunningUnknownCard, input_data)

        if self.grace_expired():
            print("Exiting Running Unauthorized Card because the grace period expired")
            return self.next_state(AccessComplete, input_data)
                
        if input_data["button_pressed"]:
            print("Exiting Running Unauthorized Card because button was pressed")
            return self.next_state(AccessComplete, input_data)
            
        return None

    def on_enter(self, input_data):
        super().on_enter(input_data)
        print("Unauthorized Card grace period started")
        print(f"Card type was {input_data['card_type']}")
        self.grace_start = datetime.now()
        self.service.box.start_beeping()

class RunningTimeout(State):
    """
    The machine has timed out, has a grace period before going to the next state
    """
    def __call__(self, input_data):
        # If the button has been pressed, then re-read the card
        if input_data["button_pressed"]:
            return self.next_state(RunningUnknownCard, input_data)
            
        # If the card is removed then finish the access attempt
        if input_data["card_id"] <= 0:
            return self.next_state(AccessComplete, input_data)

        if self.grace_expired():
            return self.next_state(IdleAuthCard, input_data)
            
        return None

    def on_enter(self, input_data):
        super().on_enter(input_data)
        print("Machine timeout, grace period started")
        self.grace_start = datetime.now()
        self.service.box.start_beeping()

class IdleAuthCard(State):
    """
    The timeout grace period is expired and the user is sent an email that
    their card is still in the machine, waits until the card is removed
    """
    def __call__(self, input_data):
        if input_data["card_id"] <= 0:
            return self.next_state(IdleNoCard, input_data)
        return None

    def on_enter(self, input_data):
        super().on_enter(input_data)
        print("Timeout grace period expired with card still in machine")
        self.service.box.set_equipment_power_on(False)
        self.service.db.log_access_completion(FSM_STATE["auth_user_id"], self.service.equipment_id)
        
        # # If its a proxy card 
        # if FSM_STATE["proxy_id"] > 0:
        #     self.service.send_user_email_proxy(FSM_STATE["auth_user_id"])
        # elif FSM_STATE["training_id"] > 0:
        #     self.service.send_user_email_training(FSM_STATE["auth_user_id"], FSM_STATE["training_id"])
        # else:
        #     self.service.send_user_email(input_data["card_id"])
            
        FSM_STATE["proxy_id"] = 0
        FSM_STATE["training_id"] = 0
        FSM_STATE["auth_user_id"] = 0
        FSM_STATE["user_authority_level"] = 0

class RunningProxyCard(State):
    """
    Runs the machine in the proxy mode
    """
    def __call__(self, input_data):
        if input_data["card_id"] <= 0:
            return self.next_state(RunningNoCard, input_data)
            
        if self.timeout_expired():
            return self.next_state(RunningTimeout, input_data)
            
        return None

    def on_enter(self, input_data):
        super().on_enter(input_data)
        print("Running in proxy mode")
        self.timeout_start = datetime.now()
        FSM_STATE["training_id"] = 0
        
        # If the same proxy card is being reinserted then don't log it
        if FSM_STATE["proxy_id"] != input_data["card_id"]:
            self.service.db.log_access_attempt(input_data["card_id"], self.service.equipment_id, True)
            
        FSM_STATE["proxy_id"] = input_data["card_id"]
        self.service.box.set_equipment_power_on(True)
        self.service.box.beep_once('success')

class RunningTrainingCard(State):
    """
    Runs the machine in the training mode
    """
    def __call__(self, input_data):
        if input_data["card_id"] <= 0:
            return self.next_state(RunningNoCard, input_data)
            
        if self.timeout_expired():
            return self.next_state(RunningTimeout, input_data)
            
        return None

    def on_enter(self, input_data):
        super().on_enter(input_data)
        print("Running in training mode")
        self.timeout_start = datetime.now()
        FSM_STATE["proxy_id"] = 0
        
        # If the training card is new and not just reinserted after a grace period
        if FSM_STATE["training_id"] != input_data["card_id"]:
            self.service.db.log_access_attempt(input_data["card_id"], self.service.equipment_id, True)
            
        FSM_STATE["training_id"] = input_data["card_id"]
        
        self.service.box.set_equipment_power_on(True)
        self.service.box.beep_once('success')