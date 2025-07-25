# portal_fsm.py for ESP32-C6 MicroPython
"""
The finite state machine for the portal box service.
Adapted from the original Raspberry Pi implementation to MicroPython for ESP32-C6.
Updated to work with the enhanced UI/UX using DisplayController.
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
        A default on_enter() method that logs the state name but doesn't update the LCD
        The LCD is managed by the main loop to prevent display flickering
        """
        state_name = self.__class__.__name__
        print(f"Entering state {state_name}")
        
        # Don't update the LCD directly - the main loop will do this
        # This prevents the display from bouncing between states

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
        
        # Update display with setup message if display controller is available
        if hasattr(self.service, 'display'):
            self.service.display.display_message("Setting Up...", "process_color")
        
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
        self.service.box.stop_beeping()
        print("Entering shutdown state")
        
        # Update display with shutdown message if display controller is available
        if hasattr(self.service, 'display'):
            self.service.display.display_message("Shutting Down...", "unauth_color")
            
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
        self.service.box.stop_beeping()
        print("In IDLENOCARD - waiting for card input")
        
        # Show instructional message if display controller is available
        if hasattr(self.service, 'display'):
            self.service.display.display_idle_instructions()


class AccessComplete(State):
    """
    Before returning to the Idle state it logs the machine usage, and turns off
    the power to the machine
    """
    def __call__(self, input_data):
        # Force reset of lastUser to ensure PIN verification
        if hasattr(self.service, 'lastUser'):
            self.service.lastUser = 0
            print("Reset lastUser in AccessComplete to force PIN verification")
            
        # Check if a card is present
        if input_data["card_id"] > 0:
            # IMPORTANT: Clear the input_data's authorization status to force re-verification
            # Create a copy with authorization reset
            new_input = dict(input_data)
            new_input["user_is_authorized"] = False  # Reset authorization
            
            # If card is still present, go to IdleUnknownCard so it will
            # process the card from scratch (including PIN verification)
            print("Card still present after access complete - going to IdleUnknownCard for fresh evaluation")
            return self.next_state(IdleUnknownCard, new_input)
        else:
            # No card present, go to IdleNoCard as usual
            return self.next_state(IdleNoCard, input_data)

    def on_enter(self, input_data):
        super().on_enter(input_data)
        self.service.box.stop_beeping()
        print("Usage complete, logging usage and turning off machine")
        
        # Make sure we reset lastUser immediately on entering AccessComplete
        if hasattr(self.service, 'lastUser'):
            self.service.lastUser = 0
            print("Reset lastUser on AccessComplete entry")
            
        # Log completion and turn off equipment
        self.service.db.log_access_completion(FSM_STATE["auth_user_id"], self.service.equipment_id)
        self.service.box.set_equipment_power_on(False)
        
        # Update display with completion message if display controller is available
        if hasattr(self.service, 'display'):
            self.service.display.display_message("Session Complete", "sleep_color")
        
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
        
        # Show processing message if display controller is available
        if hasattr(self.service, 'display'):
            self.service.display.display_message("Processing Card...", "process_color")

class RunningUnknownCard(State):
    """
    A Card has been read from the no card grace period
    """
    def __call__(self, input_data):
        print(f"RunningUnknownCard __call__ with input: card_id={input_data['card_id']}, type={input_data['card_type']}")
        print(f"user_is_authorized: {input_data['user_is_authorized']}")
        
        # Debug information for understanding the training mode conditions
        print(f"Training mode check: Card type is USER_CARD? {input_data['card_type'] == CardType.USER_CARD}")
        print(f"Training mode check: Authority level >= 3? {FSM_STATE['user_authority_level'] >= 3}")
        print(f"Training mode check: Not from proxy (proxy_id <= 0)? {FSM_STATE['proxy_id'] <= 0}")
        print(f"Training mode check: Not from training or same card? {FSM_STATE['training_id'] <= 0 or FSM_STATE['training_id'] == input_data['card_id']}")
        print(f"Training mode check: Not authorized? {not input_data['user_is_authorized']}")
        
        # Coming from RunningNoCard (during grace period)
        coming_from_no_card = FSM_STATE["last_state_name"] == "RunningNoCard"
        print(f"Coming from RunningNoCard? {coming_from_no_card}")
        
        # FIXED LOGIC: Only these specific cases should exit the grace period
        
        # Case 1: If it's the same user as before then just go back to auth user
        if input_data["card_id"] == FSM_STATE["auth_user_id"]:
            print("Same authorized user card detected - returning to RunningAuthUser")
            return self.next_state(RunningAuthUser, input_data)
        
        # Case 2: Check for training mode conditions - admin followed by unauthorized user
        if (
            input_data["card_type"] == CardType.USER_CARD and
            coming_from_no_card and 
            FSM_STATE["user_authority_level"] >= 3 and  # Original user was admin/trainer
            FSM_STATE["proxy_id"] <= 0 and  # Not coming from proxy mode
            (FSM_STATE["training_id"] <= 0 or FSM_STATE["training_id"] == input_data["card_id"]) and  # Not already in training mode
            not input_data["user_is_authorized"]  # Current card is not authorized
        ):
            print("All training mode criteria met! Entering RunningTrainingCard")
            return self.next_state(RunningTrainingCard, input_data)
        
        # Case 3: Proxy card during grace period and machine allows proxy cards
        if (
            input_data["card_type"] == CardType.PROXY_CARD and
            FSM_STATE["training_id"] <= 0 and
            coming_from_no_card and
            FSM_STATE["allow_proxy"] == 1  # Machine allows proxy cards
        ):
            print(f"Allowing proxy card since allow_proxy={FSM_STATE['allow_proxy']}")
            return self.next_state(RunningProxyCard, input_data)
        
        # For all other cases, go back to RunningNoCard to continue the grace period
        print("Card detected but doesn't meet criteria to exit grace period - continuing grace period")
        return self.next_state(RunningNoCard, input_data)

    def on_enter(self, input_data):
        super().on_enter(input_data)
        print("Card detected during grace period")
        
        # Show processing message if display controller is available
        if hasattr(self.service, 'display'):
            self.service.display.display_message("Processing Card...", "process_color")

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
        self.service.box.stop_beeping()
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
            
            # Show welcome message if display controller is available
            if hasattr(self.service, 'display'):
                self.service.display.display_welcome(input_data["card_id"])

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
        
        # Show unauthorized message if display controller is available
        if hasattr(self.service, 'display'):
            self.service.display.display_unauthorized()

class RunningNoCard(State):
    """
    An authorized card has been removed, waits for a new card until the grace
    period expires, or a button is pressed
    """
    
    def __call__(self, input_data):
        # Most critical fix: ALWAYS check grace period expiration first
        if self.grace_expired():
            print("Exiting Grace period because the grace period expired")
            return self.next_state(AccessComplete, input_data)
                
        if input_data["button_pressed"]:
            print("Exiting Grace period because button was pressed")
            return self.next_state(AccessComplete, input_data)
        
        # Card detected - only handle specific cases that should exit grace period
        if input_data["card_id"] > 0 and input_data["card_type"] != CardType.INVALID_CARD:
            # Case 1: Same user reinserted card
            if input_data["card_id"] == FSM_STATE["auth_user_id"]:
                print("Same authorized user card detected - returning to RunningAuthUser")
                return self.next_state(RunningAuthUser, input_data)
            
            # Case 2: Training mode conditions - admin followed by unauthorized user
            if (input_data["card_type"] == CardType.USER_CARD and 
                FSM_STATE["user_authority_level"] >= 3 and  # Original user was admin/trainer
                FSM_STATE["proxy_id"] <= 0 and  # Not coming from proxy mode
                (FSM_STATE["training_id"] <= 0 or FSM_STATE["training_id"] == input_data["card_id"]) and
                not input_data["user_is_authorized"]):  # Current card is not authorized
                print("All training mode criteria met! Entering RunningTrainingCard")
                return self.next_state(RunningTrainingCard, input_data)
            
            # Case 3: Proxy card when machine allows proxy
            if (input_data["card_type"] == CardType.PROXY_CARD and
                FSM_STATE["training_id"] <= 0 and
                FSM_STATE["allow_proxy"] == 1):  # Machine allows proxy cards
                print(f"Allowing proxy card since allow_proxy={FSM_STATE['allow_proxy']}")
                return self.next_state(RunningProxyCard, input_data)
            
            # For all other cases, display a message briefly but STAY in RunningNoCard
            # This prevents state bouncing while ensuring the grace timer continues
            print("Card detected but doesn't meet criteria - continuing grace period")
            # Update the display but don't change state - limit how often we show the message
            if hasattr(self.service, 'display') and not hasattr(self, 'last_message_time'):
                self.service.display.display_two_line_message(
                    "Card Not Accepted", 
                    "Grace Continuing", 
                    "unauth_color"
                )
                self.last_message_time = datetime.now()
                time.sleep(1)  # Show message briefly
                # Return to grace period display
                # Calculate remaining time properly
                elapsed = datetime.now() - self.grace_start
                remaining = max(0, self.grace_delta.total_seconds() - elapsed)
                self.service.display.start_grace_timer(remaining)
            elif hasattr(self, 'last_message_time') and (datetime.now() - self.last_message_time) > 5:
                # Only show the message again after 5 seconds
                self.service.display.display_two_line_message(
                    "Card Not Accepted", 
                    "Grace Continuing", 
                    "unauth_color"
                )
                self.last_message_time = datetime.now()
                time.sleep(1)  # Show message briefly
                # Return to grace period display
                elapsed = datetime.now() - self.grace_start
                remaining = max(0, self.grace_delta.total_seconds() - elapsed)
                self.service.display.start_grace_timer(remaining)
            
        return None

    def on_enter(self, input_data):
        super().on_enter(input_data)
        print(f"Grace period started - card removed. Auth user: {FSM_STATE['auth_user_id']}, Authority: {FSM_STATE['user_authority_level']}")
        self.grace_start = datetime.now()
        # Reset any message tracking
        if hasattr(self, 'last_message_time'):
            delattr(self, 'last_message_time')
        
        # Start grace timer on display controller if available
        if hasattr(self.service, 'display'):
            self.service.display.start_grace_timer(self.grace_delta.total_seconds())
            self.service.display.display_two_line_message("Grace Period", "Insert Card", "process_color")
        
        self.service.box.start_beeping(
            freq=500,
            duration=self.grace_delta.total_seconds(),
            beeps=self.flash_rate,
        )


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
        
        # Show unauthorized message if display controller is available
        if hasattr(self.service, 'display'):
            self.service.display.display_two_line_message("Unauthorized Card", "Insert Auth Card", "unauth_color")
            
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
        
        # Show timeout message if display controller is available
        if hasattr(self.service, 'display'):
            self.service.display.display_two_line_message("Time Expired!", "Remove Card", "orange")
            
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
        self.service.box.stop_beeping()
        print("Timeout grace period expired with card still in machine")
        self.service.box.set_equipment_power_on(False)
        self.service.db.log_access_completion(FSM_STATE["auth_user_id"], self.service.equipment_id)
        
        # Show timeout message if display controller is available
        if hasattr(self.service, 'display'):
            self.service.display.display_two_line_message("Session Ended", "Remove Card", "orange")
        
        # In the future, email notifications would go here
        # self.service.send_user_email(input_data["card_id"])
            
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
        self.service.box.stop_beeping()
        print("Running in proxy mode")
        self.timeout_start = datetime.now()
        FSM_STATE["training_id"] = 0
        
        # If the same proxy card is being reinserted then don't log it
        if FSM_STATE["proxy_id"] != input_data["card_id"]:
            self.service.db.log_access_attempt(input_data["card_id"], self.service.equipment_id, True)
            
        FSM_STATE["proxy_id"] = input_data["card_id"]
        self.service.box.set_equipment_power_on(True)
        self.service.box.beep_once('success')
        
        # Show proxy mode message if display controller is available
        if hasattr(self.service, 'display'):
            self.service.display.display_two_line_message("Proxy Access", "Machine On", "proxy_color")

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
        self.service.box.stop_beeping()
        print("Running in training mode")
        self.timeout_start = datetime.now()
        FSM_STATE["proxy_id"] = 0
        
        # If the training card is new and not just reinserted after a grace period
        if FSM_STATE["training_id"] != input_data["card_id"]:
            self.service.db.log_access_attempt(input_data["card_id"], self.service.equipment_id, True)
            
        FSM_STATE["training_id"] = input_data["card_id"]
        
        self.service.box.set_equipment_power_on(True)
        self.service.box.beep_once('success')
        
        # Show training mode message if display controller is available
        if hasattr(self.service, 'display'):
            self.service.display.display_two_line_message("Training Mode", "Machine On", "training_color")