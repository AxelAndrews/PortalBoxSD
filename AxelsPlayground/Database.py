# Database.py for ESP32-C6 MicroPython
import json
import time
import socket
import gc

# Enum for card types
class CardType:
    INVALID_CARD = -1
    SHUTDOWN_CARD = 1
    PROXY_CARD = 2
    TRAINING_CARD = 3
    USER_CARD = 4

class Database:
    '''
    A high level interface to the backend database using HTTP API
    '''

    def __init__(self, settings):
        '''
        Initialize API connection settings

        @param (dict)settings - a dictionary describing the API connection details
        '''
        # Ensure minimum configuration
        if (not 'website' in settings or 
            not 'api' in settings or 
            not 'bearer_token' in settings):
            raise ValueError("API configuration must include 'website', 'api', and 'bearer_token'")

        # Store connection settings
        self.api_host = settings['website']
        self.api_path = f"/api/{settings['api']}"
        self.api_token = settings['bearer_token']
        print(self.api_token)
        
        # State variables needed for authorization logic
        self.requires_training = True
        self.requires_payment = False

    def _make_api_request(self, method, params=None):
        """
        Makes an HTTP request to the API.

        Args:
            method (str): HTTP method (GET, POST, PUT)
            params (dict): Dictionary of query parameters

        Returns:
            dict, str, or None: Parsed JSON response, text response, or None if request failed
        """
        try:
            # Construct the query string
            query_string = ""
            if params:
                query_parts = []
                for key, value in params.items():
                    query_parts.append(f"{key}={value}")
                query_string = "?" + "&".join(query_parts)

            # Construct the full URL path
            url_path = f"{self.api_path}{query_string}"

            # Create socket
            addr_info = socket.getaddrinfo(self.api_host, 80, 0, socket.SOCK_STREAM)
            addr = addr_info[0][-1]  # Extract (IP, port)
            
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(10)  # 10-second timeout for operations
            print(addr)
            # Try to connect with retries
            max_retries = 3
            for retry in range(max_retries):
                try:
                    sock.connect(addr)
                    print("SOCKET CREATED")
                    break
                except OSError as e:
                    print(f"Connection attempt {retry+1} failed: {e}")
                    if retry < max_retries - 1:
                        print("Retrying in 2 seconds...")
                        time.sleep(2)
                        # Create a new socket for each retry
                        sock.close()
                        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        sock.settimeout(10)
                    else:
                        raise
            # Prepare HTTP request
            request = (
                method + " " + url_path + " HTTP/1.1\r\n"
                "Host: " + self.api_host + "\r\n"
                "Authorization: Bearer " + self.api_token + "\r\n"
                "Content-Type: application/x-www-form-urlencoded\r\n"
                "Connection: close\r\n\r\n"
            )
            print(request)

            print(f"Sending {method} request to: {self.api_host}{url_path}")
            sock.send(request.encode())

            # Receive response
            response = b""
            while True:
                data = sock.recv(1024)
                if not data:
                    break
                response += data

            # Close socket
            sock.close()

            # Convert response to string
            response_str = response.decode()

            # Split headers and body
            if "\r\n\r\n" in response_str:
                headers, body = response_str.split("\r\n\r\n", 1)
            else:
                headers, body = response_str, ""

            # Free memory - important for microcontrollers
            gc.collect()

            # Check if body is empty
            if not body.strip():
                print("Warning: Empty response body")
                return None

            # Check HTTP status code
            status_line = headers.split('\r\n')[0]
            status_code = int(status_line.split(' ')[1]) if len(status_line.split(' ')) > 1 else 0
            
            if status_code >= 400:
                print(f"HTTP Error: {status_code}")
                return None

            # Try to parse as JSON first
            try:
                json_body = json.loads(body)
                return json_body
            except ValueError:
                # If not JSON, check if it's a successful text response
                if "success" in body.lower() or "completed" in body.lower():
                    print("Received success message:", body.strip())
                    return True
                elif body.strip().isdigit():
                    # Handle numeric responses
                    return int(body.strip())
                else:
                    print("Non-JSON response:", body.strip())
                    return body.strip()

        except Exception as e:
            print(f"API request failed: {e}")
            return None

    def is_registered(self, mac_address):
        '''
        Determine if the portal box identified by the MAC address has been
        registered with the database

        @param (string)mac_address - the mac_address of the portal box to
             check registration status of
        '''
        print(f"Checking if portal box with Mac Address {mac_address} is registered")
        params = {
            "mode": "check_reg",
            "mac_adr": mac_address
        }
        
        response = self._make_api_request("GET", params)
        
        if response is None:
            print("API error")
            return -1
        elif isinstance(response, bool):
            return 1 if response else 0
        elif isinstance(response, (int, str)):
            try:
                return int(response)
            except (ValueError, TypeError):
                return -1
        else:
            return -1

    def register(self, mac_address):
        '''
        Register the portal box identified by the MAC address with the database
        as an out of service device
        '''
        params = {
            "mode": "register",
            "mac_adr": mac_address
        }
        
        response = self._make_api_request("PUT", params)
        
        # Handle both JSON and text responses
        if response is None:
            print("API error")
            return False
        elif isinstance(response, bool):
            return response
        else:
            # Any non-None response is considered success
            return True

    def get_equipment_profile(self, mac_address):
        '''
        Discover the equipment profile assigned to the Portal Box in the database

        @return a tuple consisting of: (int)equipment id,
        (int)equipment type id, (str)equipment type, (int)location id,
        (str)location, (int)time limit in minutes, (int) allow proxy
        '''
        print("Querying database for equipment profile")
        profile = (-1, -1, None, -1, None, -1, -1)
        
        params = {
            "mode": "get_profile",
            "mac_adr": mac_address
        }
        
        response = self._make_api_request("GET", params)
        
        if response is None:
            print("API error in get_equipment_profile")
            self.requires_training = True
            self.requires_payment = False
        elif isinstance(response, list) and len(response) > 0:
            try:
                response_details = response[0]
                profile = (
                    int(response_details["id"]),
                    int(response_details["type_id"]),
                    response_details["name"][0],
                    int(response_details["location_id"]),
                    response_details["name"][1],
                    int(response_details["timeout"]),
                    int(response_details["allow_proxy"])
                )
                self.requires_training = int(response_details["requires_training"]) == 1
                self.requires_payment = int(response_details["charge_policy"]) > 0
            except (KeyError, IndexError, TypeError) as e:
                print(f"Error processing profile data: {e}")
                
        return profile

    def log_started_status(self, equipment_id):
        '''
        Logs that this portal box has started up

        @param equipment_id: The ID assigned to the portal box
        '''
        print("Logging with the database that this portalbox has started up")
        
        params = {
            "mode": "log_started_status",
            "equipment_id": equipment_id
        }
        
        response = self._make_api_request("POST", params)
        # Just log the response, we don't need to return anything specific
        if response:
            print("Successfully logged started status")
        else:
            print("Failed to log started status")

    def log_shutdown_status(self, equipment_id, card_id):
        '''
        Logs that this portal box is shutting down

        @param equipment_id: The ID assigned to the portal box
        @param card_id: The ID read from the card presented by the user use
            or a falsy value if shutdown is not related to a card
        '''
        print("Logging with the database that this box has shutdown")
        
        params = {
            "mode": "log_shutdown_status",
            "equipment_id": equipment_id,
            "card_id": card_id
        }
        
        response = self._make_api_request("POST", params)
        
        if response:
            print("Successfully logged shutdown status")
        else:
            print("Failed to log shutdown status")

    def log_access_attempt(self, card_id, equipment_id, successful):
        '''
        Logs start time for user using a resource.

        @param card_id: The ID read from the card presented by the user
        @param equipment_id: The ID assigned to the portal box
        @param successful: If login was successful (user is authorized)
        '''
        print("Logging access attempt with database")
        
        params = {
            "mode": "log_access_attempt",
            "equipment_id": equipment_id,
            "card_id": card_id,
            "successful": int(successful)
        }
        
        response = self._make_api_request("POST", params)
        
        if response:
            print("Successfully logged access attempt")
        else:
            print("Failed to log access attempt")

    def log_access_completion(self, card_id, equipment_id):
        '''
        Logs end time for user using a resource.

        @param card_id: The ID read from the card presented by the user
        @param equipment_id: The ID assigned to the portal box
        '''
        print("Logging access completion with database")
        
        params = {
            "mode": "log_access_completion",
            "equipment_id": equipment_id,
            "card_id": card_id
        }
        
        response = self._make_api_request("POST", params)
        
        if response:
            print("Successfully logged access completion")
        else:
            print("Failed to log access completion")

    def get_card_details(self, card_id, equipment_type_id):
        '''
        This function gets the pertinent details about a card from the database
        
        Returns: {
            "user_is_authorized": true/false //Whether or not the user is authorized for this equipment
            "card_type": CardType //The type of card
            "user_authority_level": int //Returns if the user is a normal user, trainer, or admin
        }
        '''
        print(f"Getting card details for card ID {card_id}")
        
        params = {
            "mode": "get_card_details",
            "card_id": card_id,
            "equipment_id": equipment_type_id
        }
        
        response = self._make_api_request("GET", params)
        
        # Default response if API fails or returns unexpected format
        default_details = {
            "user_is_authorized": False,
            "card_type": CardType.INVALID_CARD,
            "user_authority_level": 0
        }
        
        if response is None:
            print("API error in get_card_details")
            return default_details
        elif not isinstance(response, list) or len(response) == 0:
            print("Invalid response format in get_card_details")
            return default_details
        
        response_details = response[0]
        
        # Handle None values
        user_role = response_details.get("user_role", 0)
        if user_role is None:
            user_role = 0
            
        card_type = response_details.get("card_type", -1)
        if card_type is None:
            card_type = -1
            
        details = {
            "user_is_authorized": self.is_user_authorized_for_equipment_type(response_details),
            "card_type": card_type,
            "user_authority_level": int(user_role)
        }
            
        return details

    def is_user_authorized_for_equipment_type(self, card_details):
        '''
        Check if card holder is authorized for the equipment type
        '''
        is_authorized = False
        
        try:
            # Handle potential None values with defaults
            balance_val = card_details.get("user_balance", 0)
            balance = float(balance_val) if balance_val is not None else 0.0
            
            auth_val = card_details.get("user_auth", 0)
            user_auth = int(auth_val) if auth_val is not None else 0
            
            active_val = card_details.get("user_active")
            user_active = int(active_val) if active_val is not None else 0
            
            if user_active != 1:
                return False
                
            if self.requires_training and self.requires_payment:
                is_authorized = (balance > 0.0 and user_auth == 1)
            elif self.requires_training and not self.requires_payment:
                is_authorized = (user_auth == 1)
            elif not self.requires_training and self.requires_payment:
                is_authorized = (balance > 0.0)
            else:
                is_authorized = True
                
        except (ValueError, TypeError) as e:
            print(f"Error determining authorization: {e}")
            
        return is_authorized

    def get_user(self, card_id):
        '''
        Get details for the user identified by (card) id

        @return, a tuple of name and email
        '''
        user = (None, None)
        
        print(f"Getting user information from card ID: {card_id}")
        
        params = {
            "mode": "get_user",
            "card_id": card_id
        }
        
        response = self._make_api_request("GET", params)
        
        if response is None:
            print("API error in get_user")
        elif isinstance(response, list) and len(response) > 0:
            response_details = response[0]
            user = (
                response_details.get("name", "Unknown User"),
                response_details.get("email", "unknown@example.com")
            )
        elif isinstance(response, str) and response:
            # Try to handle potential string response
            user = (response, "unknown@example.com")
            
        return user

    def get_equipment_name(self, equipment_id):
        '''
        Gets the name of the equipment given the equipment id 

        @return, a string of the name 
        '''
        print("Getting equipment name")
        
        params = {
            "mode": "get_equipment_name",
            "equipment_id": equipment_id
        }
        
        response = self._make_api_request("GET", params)
        
        if response is None:
            print("API error in get_equipment_name")
            return "Unknown"
        elif isinstance(response, list) and len(response) > 0:
            return response[0].get("name", "Unknown")
        elif isinstance(response, str) and response:
            # Handle string response
            return response
        else:
            return "Unknown"

    def record_ip(self, equipment_id, ip):
        '''
        Records the IP address of the equipment
        '''
        print(f"Recording IP address {ip} for equipment {equipment_id}")
        
        params = {
            "mode": "record_ip",
            "equipment_id": equipment_id,
            "ip_address": ip
        }
        
        response = self._make_api_request("POST", params)
        
        # Any non-None response is considered success
        return response is not None
