# import network
# import socket
# import time
# import json
# import ubinascii

# # WiFi Configuration
# self.WIFI_SSID = "bucknell_iot"
# self.WIFI_PASSWORD = ""
# self.API_HOST = "ec2-3-14-141-222.us-east-2.compute.amazonaws.com"
# self.API_PATH = "/api/box.php"
# self.API_TOKEN = "290900415d2d7aac80229cdea4f90fbf"

# def connect_wifi():
#     """Connects to WiFi and prints the IP and MAC address."""
#     print("Connecting to WiFi...")
#     wlan = network.WLAN(network.STA_IF)
#     wlan.active(True)

#     if not wlan.isconnected():
#         wlan.connect(self.WIFI_SSID, self.WIFI_PASSWORD)
#         while not wlan.isconnected():
#             time.sleep(1)  # Wait for connection
#             print("Waiting for WiFi connection...")
    
#     print(f"Connected! IP: {wlan.ifconfig()[0]}")
#     # print(wlan.config('mac'))
#     print(f"Device MAC address: {ubinascii.hexlify(wlan.config('mac')).decode()}")
#     return True

# def make_api_request(mode, mac_address):
#     """Makes an HTTP GET request to the API."""
#     try:
#         # Create socket
#         addr_info = socket.getaddrinfo(self.API_HOST, 80)  # Resolve host to IP address
#         addr = addr_info[-1][-1]  # Extract (IP, port)

#         print(f"Connecting to {self.API_HOST} ({addr})...")
#         sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#         print("hi")
#         sock.settimeout(10)
#         sock.connect(addr)  # Connect to API server
#         # Prepare HTTP request
#         url_path = f"{self.API_PATH}?mode={mode}&mac_adr={mac_address}"
#         request = (
#             "GET " + url_path + " HTTP/1.1\r\n"
#             "Host: " + self.API_HOST + "\r\n"
#             "Authorization: Bearer " + self.API_TOKEN + "\r\n"
#             "Connection: close\r\n\r\n"
#         )

#         print(f"Requesting URL: {self.API_HOST}{self.API_PATH}?mode={mode}&mac_adr={mac_address}")
#         sock.sendall(request.encode())  # Send HTTP request
#         print("Request sent successfully")

#         # Receive response
#         response = b""
#         while True:
#             chunk = sock.recv(1024)
#             if not chunk:
#                 break
#             response += chunk
#         print("Response Formatted")

#         # Close socket
#         sock.close()

#         # Convert response to string
#         response_str = response.decode()
#         print("Converted to string")

#         # Split headers and body
#         if "\r\n\r\n" in response_str:
#             headers, body = response_str.split("\r\n\r\n", 1)
#         else:
#             headers, body = response_str, ""

#         print("\nResponse Headers:")
#         print(headers)

#         print("\nResponse Body:")
#         if not body.strip():
#             print("Warning: Empty response body")
#             return None

#         try:
#             json_body = json.loads(body)  # Try parsing as JSON
#             print(json.dumps(json_body))
#         except ValueError as e:
#             print("Error parsing JSON:", e)
#             print("Raw response body:", body)  # Print full response for debugging
#             return None

#     except Exception as e:
#         print(f"API request failed: {e}")
#         return None
    
# def api_get(params=None):
#     """
#     Make a GET request to the API.

#     Args:
#         params (dict): Dictionary of query parameters

#     Returns:
#         dict or None: Parsed JSON response or None if request failed
#     """
#     return _make_api_request("GET", params)

# def api_post(params=None):
#     """
#     Make a POST request to the API.

#     Args:
#         params (dict): Dictionary of query parameters

#     Returns:
#         dict or None: Parsed JSON response or None if request failed
#     """
#     return _make_api_request("POST", params)

# def api_put(params=None):
#     """
#     Make a PUT request to the API.

#     Args:
#         params (dict): Dictionary of query parameters

#     Returns:
#         dict or None: Parsed JSON response or None if request failed
#     """
#     return _make_api_request("PUT", params)

# def main():
#     """Main function to connect to WiFi and test API calls."""
#     if not connect_wifi():
#         return

#     mac_address = ubinascii.hexlify(network.WLAN(network.STA_IF).config('mac')).decode()

#     print("\n1. Testing Get Profile:")
#     make_api_request("get_profile", mac_address)

# if __name__ == "__main__":
#     main()

# import network
# import time

# wlan = network.WLAN(network.STA_IF)
# wlan.active(True)
# wlan.connect("bucknell_iot", "")  # Your network credentials

# # Wait for connection
# timeout = 10
# while timeout > 0:
#     if wlan.isconnected():
#         break
#     timeout -= 1
#     print("Waiting for connection...")
#     time.sleep(1)

# if wlan.isconnected():
#     print("Connected to WiFi")
#     print("IP address:", wlan.ifconfig()[0])
#     # Try a simple DNS lookup
#     import socket
#     try:
#         addr_info = socket.getaddrinfo("ec2-3-14-141-222.us-east-2.compute.amazonaws.com", 80)[-1][-1]
#         print("DNS lookup successful:", addr_info)
#     except Exception as e:
#         print("DNS lookup failed:", e)
# else:
#     print("Failed to connect to WiFi")

import network
import socket
import json
import time

class Database:
    def __init__(self,connection):
        self.wlan=connection
        self.WIFI_SSID = "bucknell_iot"
        self.WIFI_PASSWORD = ""
        self.API_HOST = "ec2-3-14-141-222.us-east-2.compute.amazonaws.com"
        self.API_PATH = "/api/box.php"
        self.API_TOKEN = "290900415d2d7aac80229cdea4f90fbf"
    # WiFi Configuration

    # def connect_wifi():
    #     """Connects to WiFi and prints the IP and MAC address."""
    #     print("Connecting to WiFi...")
    #     wlan = network.WLAN(network.STA_IF)
    #     wlan.active(True)
    
    #     try:
    #         wlan.connect(self.WIFI_SSID, self.WIFI_self.WIFI_PASSWORD)
        
    #         # Wait for connection with timeout
    #         max_wait = 10
    #         while max_wait > 0:
    #             if wlan.isconnected():
    #                 break
    #             max_wait -= 1
    #             print("Waiting for connection...")
    #             time.sleep(1)
            
    #         if wlan.isconnected():
    #             print(f"Connected! IP: {wlan.ifconfig()[0]}")
    #             mac_bytes = wlan.config('mac')
    #             mac_hex = ''.join(['{:02x}'.format(b) for b in mac_bytes])
    #             print(f"Device MAC address: {mac_hex}")
    #             return True
    #         else:
    #             print("Could not connect to WiFi")
    #             return False
    #     except Exception as e:
    #         print(f"WiFi connection failed: {e}")
    #         return False

    def api_get(self, params=None):
        """
        Make a GET request to the API.

        Args:
            params (dict): Dictionary of query parameters

        Returns:
            dict or None: Parsed JSON response or None if request failed
        """
        return _make_api_request("GET", params)

    def api_post(self, params=None):
        """
        Make a POST request to the API.

        Args:
            params (dict): Dictionary of query parameters

        Returns:
            dict or None: Parsed JSON response or None if request failed
        """
        return _make_api_request("POST", params)

    def api_put(params=None):
        """
        Make a PUT request to the API.

        Args:
            params (dict): Dictionary of query parameters

        Returns:
            dict or None: Parsed JSON response or None if request failed
        """
        return _make_api_request("PUT", params)

    def _make_api_request(self, method, params=None):
        """
        Makes an HTTP request to the API.

        Args:
            method (str): HTTP method (GET, POST, PUT)
            params (dict): Dictionary of query parameters

        Returns:
            dict or None: Parsed JSON response or None if request failed
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
            url_path = f"{self.API_PATH}{query_string}"

            # Create socket
            addr_info = socket.getaddrinfo(self.API_HOST, 80, 0, socket.SOCK_STREAM)
            addr = addr_info[0][-1]  # Extract (IP, port)
        
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(10)  # 10-second timeout

            print(f"Connecting to {self.API_HOST} ({addr})...")
            sock.connect(addr)  # Connect to API server

            # Prepare HTTP request - using string concatenation instead of f-strings
            request = (
                method + " " + url_path + " HTTP/1.1\r\n"
                "Host: " + self.API_HOST + "\r\n"
                "Authorization: Bearer " + self.API_TOKEN + "\r\n"
                "Content-Type: application/x-www-form-urlencoded\r\n"
                "Connection: close\r\n\r\n"
            )

            print(f"Sending {method} request to: {self.API_HOST}{url_path}")
            sock.send(request.encode())
            print("Request sent successfully")

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

            print("\nResponse Headers:")
            print(headers)

            print("\nResponse Body:")
            if not body.strip():
                print("Warning: Empty response body")
                return None

            try:
                json_body = json.loads(body)  # Try parsing as JSON
                print(json.dumps(json_body))
                return json_body
            except ValueError as e:
                print("Error parsing JSON:", e)
                print("Raw response body:", body)
                return None

        except Exception as e:
            print(f"API request failed: {e}")
            return None

    def get_mac_address(self,wlan):
        """Returns the MAC address as a hex string."""
        wlan = network.WLAN(network.STA_IF)
        mac_bytes = wlan.config('mac')
        return ''.join(['{:02x}'.format(b) for b in mac_bytes])

    # def main():
    #     """Main function to connect to WiFi and test API calls."""
    #     if not connect_wifi():
    #         return

        # mac_address = get_mac_address()
        # equipment_id = "2"
        # card_id = "1234"

        # print("\n1. Testing Get Profile:")
        # # Example GET request
        # card_details = api_get({"mode": "get_card_details", "equipment_id": equipment_id, "card_id": card_id})
        # equipment_profile = api_get({"mode": "get_profile", "mac_adr": mac_address})
        # equipment_name = api_get({"mode": "get_equipment_name", "mac_adr": mac_address, "equipment_id": equipment_id})

        # # Example POST request
        # if card_details and card_details[0].get("user_auth") == 1 and card_details[0].get("user_active") == 1:
        #     api_post({"mode": "log_access_attempt", "equipment_id": equipment_id, "card_id": card_id, "successful": "1"})

        # api_post({"mode": "log_access_completion", "equipment_id": equipment_id, "card_id": card_id})
        # reg = api_get({"mode": "check_reg", "mac_adr": mac_address})
        # if reg == 1:
        #     print("MAC IS REGISTERED")
        # else:
        #     print("MAC NOT REGISTERED!!!!")
        # reg_fail = api_get({"mode": "check_reg", "mac_adr": "000000000000"})
        # if reg_fail == 0:
        #     print("MAC CORRECTLY UNREGISTERED")
        # else:
        #     print("MAC REGISTERED, NOT SUPPOSED TO BE")

        # api_get({"mode": "get_user", "card_id": card_id})

        # api_post({"mode": "log_shutdown_status", "equipment_id": equipment_id, "card_id": card_id})

        # api_post({"mode": "log_started_status", "equipment_id": equipment_id, "card_id": card_id})

    # if __name__ == "__main__":
    #     main()