import wifi
import socketpool
import json

# WiFi Configuration
WIFI_SSID = "KINETIC_4acab1"
WIFI_PASSWORD = "FFTbw6kQTJ"
API_HOST = "ec2-3-14-141-222.us-east-2.compute.amazonaws.com"
API_PATH = "/api/box.php"
API_TOKEN = "290900415d2d7aac80229cdea4f90fbf"

# def connect_wifi():
#     """Connects to WiFi and prints the IP and MAC address."""
#     print("Connecting to WiFi...")
#     try:
#         wifi.radio.connect(WIFI_SSID, WIFI_PASSWORD)
#         print(f"Connected! IP: {wifi.radio.ipv4_address}")
#         print(f"Device MAC address: {wifi.radio.mac_address.hex()}")
#         return True
#     except Exception as e:
#         print(f"WiFi connection failed: {e}")
#         return False
import network

def connect_wifi():
    """Connects to WiFi and prints the IP and MAC address."""
    print("Connecting to WiFi...")
    try:
        wlan = network.WLAN(network.STA_IF)
        wlan.active(True)
        wlan.connect(WIFI_SSID, WIFI_PASSWORD)
        while not wlan.isconnected():
            pass
        print(f"Connected! IP: {wlan.ifconfig()[0]}")
        print(f"Device MAC address: {wlan.config('mac')}")
        return True
    except Exception as e:
        print(f"WiFi connection failed: {e}")
        return False

def api_get(params=None):
    """
    Make a GET request to the API.

    Args:
        params (dict): Dictionary of query parameters

    Returns:
        dict or None: Parsed JSON response or None if request failed
    """
    return _make_api_request("GET", params)

def api_post(params=None):
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

def _make_api_request(method, params=None):
    """
    Makes an HTTP request to the API.

    Args:
        method (str): HTTP method (GET, POST, PUT)
        params (dict): Dictionary of query parameters

    Returns:
        dict or None: Parsed JSON response or None if request failed
    """
    try:
        # Create socket pool
        pool = socketpool.SocketPool(wifi.radio)

        # Construct the query string
        query_string = ""
        if params:
            query_parts = []
            for key, value in params.items():
                query_parts.append(f"{key}={value}")
            query_string = "?" + "&".join(query_parts)

        # Construct the full URL path
        url_path = f"{API_PATH}{query_string}"

        # Create socket
        sock = pool.socket(pool.AF_INET, pool.SOCK_STREAM)
        sock.settimeout(10)  # 10-second timeout

        # Resolve host to IP address
        addr_info = pool.getaddrinfo(host=API_HOST, port=80)
        addr = addr_info[0][4]  # Extract (IP, port)

        print(f"Connecting to {API_HOST} ({addr})...")
        sock.connect(addr)  # Connect to API server

        # Prepare HTTP request - using string concatenation instead of f-strings
        request = (
            method + " " + url_path + " HTTP/1.1\r\n"
            "Host: " + API_HOST + "\r\n"
            "Authorization: Bearer " + API_TOKEN + "\r\n"
            "Content-Type: application/x-www-form-urlencoded\r\n"
            "Connection: close\r\n\r\n"
        )

        print(f"Sending {method} request to: {API_HOST}{url_path}")
        sock.sendall(request.encode())
        print("Request sent successfully")

        # Receive response
        response = b""
        buffer = bytearray(1024)
        while True:
            bytes_received = sock.recv_into(buffer)
            if bytes_received == 0:
                break
            response += buffer[:bytes_received]

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

def main():
    """Main function to connect to WiFi and test API calls."""
    if not connect_wifi():
        return

    mac_address = wifi.radio.mac_address.hex()
    equipment_id = "2"
    card_id = "1234"

    print("\n1. Testing Get Profile:")
    # Example GET request
    card_details = api_get({"mode": "get_card_details", "equipment_id": equipment_id, "card_id": card_id})
    equipment_profile = api_get({"mode": "get_profile", "mac_adr": mac_address})
    equipment_name = api_get({"mode": "get_equipment_name", "mac_adr": mac_address, "equipment_id": equipment_id})

    # Example POST request
    if (card_details[0]["user_auth"] == 1) & (card_details[0]["user_active"] == 1):
        api_post({"mode": "log_access_attempt", "equipment_id": equipment_id, "card_id": card_id, "successful": "1"})

    api_post({"mode": "log_access_completion", "equipment_id": equipment_id, "card_id": card_id})
    reg = api_get({"mode": "check_reg", "mac_adr": mac_address})
    if reg == 1:
        print("MAC IS REGISTERED")
    else:
        print("MAC NOT REGISTERED!!!!")
    reg_fail = api_get({"mode": "check_reg", "mac_adr": "000000000000"})
    if reg_fail == 0:
        print("MAC CORRECTLY UNREGISTERED")
    else:
        print("MAC REGISTERED, NOT SUPPOSED TO BE")


    api_get({"mode": "get_user", "card_id": card_id})

    api_post({"mode": "log_shutdown_status", "equipment_id": equipment_id, "card_id": card_id})

    api_post({"mode": "log_started_status", "equipment_id": equipment_id, "card_id": card_id})

if __name__ == "__main__":
    main()
