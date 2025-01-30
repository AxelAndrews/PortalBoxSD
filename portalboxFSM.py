# MicroPython version of the portal box service FSM

import utime
import logging
import machine

from CardType import CardType

# Minimalistic logging for MicroPython
logging.basicConfig(level=logging.DEBUG)

class State:
    """The parent state for all FSM states."""

    # Shared state variables that keep a little history of the cards
    auth_user_id = -1
    proxy_id = -1
    training_id = -1
    user_authority_level = 0

    def __init__(self, portal_box_service, input_data):
        self.service = portal_box_service
        self.timeout_start = utime.time()
        self.grace_start = utime.time()
        self.timeout_delta = 0
        self.grace_delta = 2  # Grace period in seconds
        self.on_enter(input_data)
        self.flash_rate = 3

    def next_state(self, cls, input_data):
        logging.debug("State transition : {0} -> {1}".format(self.__class__.__name__, cls.__name__))
        self.__class__ = cls
        self.on_enter(input_data)

    def on_enter(self, input_data):
        """
        A default on_enter() method, just logs which state is being entered
        """
        logging.debug("Entering state {}".format(self.__class__.__name__))

    def timeout_expired(self):
        """
        Determines whether or not the timeout period has expired
        @return a boolean which is True when the timeout period has expired
        """
        if self.service.timeout_minutes > 0 and (utime.time() - self.timeout_start) > self.timeout_delta:
            logging.debug("Timeout period expired with time passed = {}".format(utime.time() - self.timeout_start))
            return True
        return False

    def grace_expired(self):
        """
        Determines whether or not the grace period has expired
        @return a boolean which is True when the grace period has expired
        """
        if (utime.time() - self.grace_start) > self.grace_delta:
            logging.debug("Grace period expired with time passed = {}".format(utime.time() - self.grace_start))
            return True
        return False


class Setup(State):
    """Setup the system"""

    def __call__(self, input_data):
        pass

    def on_enter(self, input_data):
        logging.info("Starting setup")
        self.service.box.set_display_color(self.service.settings["display"]["setup_color"])
        try:
            self.service.connect_to_database()
            self.service.box.set_display_color(self.service.settings["display"]["setup_color_db"])
            self.service.connect_to_email()
            self.service.box.set_display_color(self.service.settings["display"]["setup_color_email"])
            self.service.get_equipment_role()
            self.service.record_ip()
            self.service.box.set_display_color(self.service.settings["display"]["setup_color_role"])

            self.timeout_delta = self.service.timeout_minutes * 60
            self.grace_delta = self.service.settings.getint("user_exp", "grace_period")
            self.allow_proxy = self.service.allow_proxy
            self.flash_rate = self.service.settings.getint("display", "flash_rate")
            self.next_state(IdleNoCard, input_data)
            self.service.box.buzz_tone(500, 0.2)
        except Exception as e:
            logging.error("Unable to complete setup exception raised: \n\t{}".format(e))
            self.next_state(Shutdown, input_data)
            raise e


class Shutdown(State):
    """Shuts down the box"""
    def __call__(self, input_data):
        self.service.box.set_equipment_power_on(False)
        self.service.shutdown(input_data["card_id"])


class IdleNoCard(State):
    """Waits for card input"""
    def __call__(self, input_data):
        if input_data["card_id"] > 0:
            self.next_state(IdleUnknownCard, input_data)

    def on_enter(self, input_data):
        self.service.box.sleep_display()


class AccessComplete(State):
    """Logs the usage and shuts off the machine"""
    def __call__(self, input_data):
        pass

    def on_enter(self, input_data):
        logging.info("Usage complete, logging usage and turning off machine")
        self.service.db.log_access_completion(self.auth_user_id, self.service.equipment_id)
        self.service.box.set_equipment_power_on(False)
        self.proxy_id = 0
        self.training_id = 0
        self.auth_user_id = 0
        self.user_authority_level = 0
        self.next_state(IdleNoCard, input_data)


class IdleUnknownCard(State):
    """Card input is read and action is determined by card type"""
    def __call__(self, input_data):
        pass

    def on_enter(self, input_data):
        if input_data["card_type"] == CardType.SHUTDOWN_CARD:
            logging.info("Inserted a shutdown card, shutting the box down")
            self.next_state(Shutdown, input_data)
        elif input_data["user_is_authorized"] and input_data["card_type"] == CardType.USER_CARD:
            logging.info("Inserted card with id {}, is authorized".format(input_data["card_id"]))
            self.next_state(RunningAuthUser, input_data)
        else:
            logging.info("Inserted card with id {}, is not authorized".format(input_data["card_id"]))
            self.next_state(IdleUnauthCard, input_data)


class RunningAuthUser(State):
    """Authorized user has put their card in"""
    def __call__(self, input_data):
        if input_data["card_id"] <= 0:
            self.next_state(RunningNoCard, input_data)
        if self.timeout_expired():
            self.next_state(RunningTimeout, input_data)

    def on_enter(self, input_data):
        logging.info("Authorized card in box, turning machine on")
        self.timeout_start = utime.time()
        self.proxy_id = 0
        self.training_id = 0
        self.service.box.set_equipment_power_on(True)
        self.service.box.set_display_color(self.service.settings["display"]["auth_color"])
        self.service.box.beep_once()
        if self.auth_user_id != input_data["card_id"]:
            self.service.db.log_access_attempt(input_data["card_id"], self.service.equipment_id, True)

        self.auth_user_id = input_data["card_id"]
        self.user_authority_level = input_data["user_authority_level"]


class IdleUnauthCard(State):
    """Unauthorized card has been put into the machine"""
    def __call__(self, input_data):
        if input_data["card_id"] <= 0:
            self.next_state(IdleNoCard, input_data)

    def on_enter(self, input_data):
        self.service.box.beep_once()
        self.service.box.set_equipment_power_on(False)
        self.service.box.set_display_color(self.service.settings["display"]["unauth_color"])
        self.service.db.log_access_attempt(input_data["card_id"], self.service.equipment_id, False)


class RunningNoCard(State):
    """An authorized card has been removed"""
    def __call__(self, input_data):
        if input_data["card_id"] > 0:
            self.next_state(RunningUnknownCard, input_data)

        if self.grace_expired():
            logging.debug("Exiting Grace period because the grace period expired")
            self.next_state(AccessComplete, input_data)

        if input_data["button_pressed"]:
            logging.debug("Exiting Grace period because button was pressed")
            self.next_state(AccessComplete, input_data)

    def on_enter(self, input_data):
        logging.info("Grace period started")
        self.grace_start = utime.time()
        self.service.box.flash_display(
            self.service.settings["display"]["no_card_grace_color"],
            self.grace_delta * 1000,
            int(self.grace_delta * self.flash_rate)
        )


class RunningTimeout(State):
    """The machine has timed out"""
    def __call__(self, input_data):
        if input_data["button_pressed"]:
            self.next_state(RunningUnknownCard, input_data)
        if input_data["card_id"] <= 0:
            self.next_state(AccessComplete, input_data)

        if self.grace_expired():
            self.next_state(IdleAuthCard, input_data)

    def on_enter(self, input_data):
        logging.info("Machine timeout, grace period started")
        self.grace_start = utime.time()
        self.service.box.flash_display(
            self.service.settings["display"]["grace_timeout_color"],
            self.grace_delta * 1000,
            int(self.grace_delta * self.flash_rate)
        )


class IdleAuthCard(State):
    """Timeout grace period expired"""
    def __call__(self, input_data):
        if input_data["card_id"] <= 0:
            self.next_state(IdleNoCard, input_data)

    def on_enter(self, input_data):
        self.service.box.set_equipment_power_on(False)
        self.service.db.log_access_completion(self.auth_user_id, self.service.equipment_id)
        self.service.box.set_display_color(self.service.settings["display"]["timeout_color"])
        self.proxy_id = 0
        self.training_id = 0
        self.auth_user_id = 0
        self.user_authority_level = 0

