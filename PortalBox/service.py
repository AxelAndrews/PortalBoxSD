import network
import time
import neopixel
from machine import Pin
# import datetime
from portalBoxFSM import State
import os
from Database import Database
import read as CardReader
# relay is 7
# usb is 9
# buzzer 6

class PortalBoxService:
    def __init__(self):
        self.filename="./userData.txt"
        self.debugFile="./debug.txt"
        
        self.wlan = network.WLAN(network.STA_IF)
        self.wlan.active(True)
        self.Database=Database(self.wlan)
        print("1")
        
        self.currUser=[]
        self.userID=""
        led = Pin(8, Pin.OUT)
        self.np=neopixel.NeoPixel(led,1) 
        self.buzzer= Pin(6,Pin.OUT)
        # self.button= Pin(16,Pin.OUT)
        self.powerRelay = Pin(7, Pin.OUT)
        
        # ledDat = Pin(13, Pin.OUT)
        # ledClk = Pin(12, Pin.OUT)
        # self.np=neopixel.NeoPixel(ledDat,1) 
        
        self.state = State.IDLE_NOCARD
        
        self.startUp()
        
    def startUp(self):
        # print("2")
        # while not self.wlan.isconnected():
        #     self.log_to_debug_file("Connecting/Reconnecting to Internet")
        #     self.enterIdleNoCard()
        #     self.connectToWifi()
        # print("3")
        # mac_address = self.Database.get_mac_address()
        # equipment_id = "2"
        # card_id = "1234"

        # print("\n1. Testing Get Profile:")
        # # Example GET request
        # card_details = self.Database.api_get({"mode": "get_card_details", "equipment_id": equipment_id, "card_id": card_id})
        # equipment_profile = self.Database.api_get({"mode": "get_profile", "mac_adr": mac_address})
        # equipment_name = self.Database.api_get({"mode": "get_equipment_name", "mac_adr": mac_address, "equipment_id": equipment_id})

        # # Example POST request
        # if card_details and card_details[0].get("user_auth") == 1 and card_details[0].get("user_active") == 1:
        #     self.Database.api_post({"mode": "log_access_attempt", "equipment_id": equipment_id, "card_id": card_id, "successful": "1"})

        # self.Database.api_post({"mode": "log_access_completion", "equipment_id": equipment_id, "card_id": card_id})
        # reg = self.Database.api_get({"mode": "check_reg", "mac_adr": mac_address})
        # if reg == 1:
        #     print("MAC IS REGISTERED")
        # else:
        #     print("MAC NOT REGISTERED!!!!")
        # reg_fail = self.Database.api_get({"mode": "check_reg", "mac_adr": "000000000000"})
        # if reg_fail == 0:
        #     print("MAC CORRECTLY UNREGISTERED")
        # else:
        #     print("MAC REGISTERED, NOT SUPPOSED TO BE")

        # self.Database.api_get({"mode": "get_user", "card_id": card_id})

        # self.Database.api_post({"mode": "log_shutdown_status", "equipment_id": equipment_id, "card_id": card_id})

        # self.Database.api_post({"mode": "log_started_status", "equipment_id": equipment_id, "card_id": card_id})
        
        while True:
            # Ensure connection to the internet
            while not self.wlan.isconnected():
                self.log_to_debug_file("Connecting/Reconnecting to Internet")
                self.enterIdleNoCard()
                self.connectToWifi()
                
            #Keep looping until it gets a RFID card

            if self.readCardReader()==-1 and self.state != State.IDLE_NOCARD:
                self.powerRelay.off()
                self.enterIdleNoCard()
                
            if self.state == State.IDLE_NOCARD:
                self.userID = self.readCardReader() #Gives up after 1 tries
                if self.verifyUserID(self.userID):
                    self.enterIdleAwaitPin()
                else:
                    self.turnRed()
                    continue
                
            if self.state == State.IDLE_AWAIT_PIN:
                if self.verifyUserPin(self.readKeypad()):
                    self.enterRunningAuthorized()
                    self.powerRelay.on()
                    self.turnGreen()
                else:
                    while not self.buttonPressed():
                        self.buzzer.on()
                        time.sleep(0.5)
                        self.buzzer.off()
                    continue
                    

    def turnGreen(self):
        self.np[0]= (0,30,0)
        self.np.write()

        
    def turnRed(self):
        self.np[0]= (30,0,0)
        self.np.write()

    def enterIdleNoCard(self):
        self.state = State.IDLE_NOCARD
        print(f"State changed to: {self.state}")

    def enterIdleUnauthorized(self):
        self.state = State.IDLE_UNAUTHORIZED
        print(f"State changed to: {self.state}")

    def enterIdleAwaitPin(self):
        self.state = State.IDLE_AWAIT_PIN
        print(f"State changed to: {self.state}")

    def enterRunningAuthorized(self):
        self.state = State.RUNNING_AUTHORIZED
        print(f"State changed to: {self.state}")

    def enterRunningNoCard(self):
        self.state = State.RUNNING_NOCARD
        print(f"State changed to: {self.state}")
        
    def buttonPressed(self):
        return True

    def readKeypad(self):
        '''
        Get data from the RFID Scanner
        '''
        return '0000'
    
    def readCardReader(self):
        '''
        Get data from the RFID Scanner
        '''
        return CardReader.do_read()
        
        
    def verifyUserID(self, userID):
        '''
        Get data from CSV and verify if the given user exists
        '''
        try:
            with open(self.filename, mode='r') as file:
                lines = file.readlines()
                for line in lines[1:]:
                    row = line.strip().split(',')
                    # print(row[1].strip())
                    # print(userID)
                    # print(row[1].strip() == userID)
                    # print("===============")
                    if row[1].strip() == userID:  # Assuming UserID is in the first column
                        self.currUser = row
                        return True
            return False  # Return False if the userID is not found
        finally:
            file.close()
            
    def verifyUserPin(self, pin):
        '''
        Get data from CSV and verify if the given user exists
        '''
        if self.currUser[2].strip()== pin:
            return True
        else:
            return False
        
    def writeUser(self, userID, pin):
        remainingStorage=os.statvfs("/")[0]
        if remainingStorage>0.001:
            with open(self.filename, mode='a', newline='') as file:
                try:
                    writer = csv.writer(file)
                    file.write(f"\n0,{userID},{pin}")
                    print("User added successfully.")
                except Exception as e:
                    print(f"Error: {e}")
        else:
            self.sendDataToSheet('5555555555555555', '5555')
                
    def connectToWifi(self):
        '''
        Connect to WiFi and verify connection
        '''
        SSID='bucknell_iot'
        password=""

        # Scan for local networks
        print("Scanning for networks...")
        networks = self.wlan.scan()
        for network in networks:
            print("Found network:", network)

        # Check if connected
        if not self.wlan.isconnected():
            print('Connecting to network...')
            self.wlan.connect(SSID, password)
            timeout = 10  # Timeout in seconds, should not take more than 10 seconds
            start_time = time.time()  # Start timer

            # Get current timer value and check if it is less than the timeout
            while not self.wlan.isconnected() and (time.time() - start_time) < timeout:
                # Pause between each check
                print("Waiting for connection...")
                time.sleep(1)

            if not self.wlan.isconnected():
                print("Failed to connect within timeout.")
            else:
                print(f"Connected successfully in {time.time() - start_time} seconds")
        else:
            print("Already connected to WiFi.") 
    
    # def connectToWifi(self):
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

    def sendDataToSheet(self):
            # Define the scopes and load credentials from the service account file
            scopes = ["https://www.googleapis.com/auth/spreadsheets"]
            creds = Credentials.from_service_account_file("googleSheets.json", scopes=scopes)
            
            # Authorize the client using the credentials
            client = gspread.authorize(creds)

            # Define the sheet ID and open the spreadsheet
            sheet_id = "1SRf5OOWelnRHOKptlMJtqZEZVGsJi7lgn29zlKJ6IEY"
            workbook = client.open_by_key(sheet_id)

            # Read data from CSV file
            with open(self.filename, mode='r') as file:
                reader = csv.reader(file)
                # Skip the header row if present
                next(reader)
                values = list(reader)  # Convert CSV rows to list of lists

            # Get a list of all worksheets in the workbook
            worksheet_list = map(lambda x: x.title, workbook.worksheets())
            new_worksheet_name = "UserData"

            # Check if the worksheet exists, otherwise, create it
            if new_worksheet_name in worksheet_list:
                print(f"Found existing worksheet: {new_worksheet_name}")
                sheet = workbook.worksheet(new_worksheet_name)
            else:
                print(f"Creating new worksheet: {new_worksheet_name}")
                sheet = workbook.add_worksheet(new_worksheet_name, rows=10, cols=10)

            # Clear the existing content in the sheet
            print("Clearing the sheet...")
            sheet.clear()

            # Update the values in the sheet starting from A1
            print(f"Updating values: {values}")
            sheet.update([["Role", "UserID", "Pin"]] + values)  # Adding header row to the sheet update

            # Optionally, you can add any other operations like adding formulas or formatting
            sheet.format("A1:B1", {"textFormat": {"bold": True}})

            print("Data successfully updated!")
            
    
            
    def readDataFromSheet(self):
        # Define the scopes and load credentials from the service account file
        scopes = ["https://www.googleapis.com/auth/spreadsheets"]
        creds = Credentials.from_service_account_file("googleSheets.json", scopes=scopes)
        
        # Authorize the client using the credentials
        client = gspread.authorize(creds)

        # Define the sheet ID and open the spreadsheet
        sheet_id = "1SRf5OOWelnRHOKptlMJtqZEZVGsJi7lgn29zlKJ6IEY"
        workbook = client.open_by_key(sheet_id)

        # Get the worksheet (assuming the worksheet is named "UserData")
        try:
            sheet = workbook.worksheet("UserData")
        except gspread.exceptions.WorksheetNotFound:
            print("Error: Worksheet 'UserData' not found.")
            return
        
        # Read all values from the sheet (excluding the header)
        values = sheet.get_all_values()

        # Overwrite the CSV file with the data from Google Sheets
        with open(self.filename, mode='w', newline='') as file:
            writer = csv.writer(file)
            # Write the header row
            writer.writerow(values[0])  # Assuming the first row is the header
            # Write the rest of the data
            for row in values[1:]:  # Exclude the header row
                writer.writerow(row)

        print(f"CSV file '{self.filename}' has been overwritten with the latest data from the Google Sheet.")
    
    def log_to_debug_file(self, message):
        """
        A helper function to log messages to 'debug.txt'.
        """
        # Get the current local time as a tuple (year, month, day, hour, minute, second, weekday, yearday)
        current_time = time.localtime()
        
        # Manually format the timestamp as "YYYY-MM-DD HH:MM:SS"
        timestamp = "{:04}-{:02}-{:02} {:02}:{:02}:{:02}".format(
            current_time[0], current_time[1], current_time[2],  # Year, Month, Day
            current_time[3], current_time[4], current_time[5]   # Hour, Minute, Second
        )
        
        with open("debug.txt", "a") as debug_file:
            debug_file.write(f"<{timestamp}> - {message}\n")




portalInstance = PortalBoxService()

# print("============TESTING FOR API ACCESS============")
# start_time = time.time()
# portalInstance.sendDataToSheet()
# end_time = time.time()
# print(f"Time taken to send data to Google Sheets: {end_time - start_time:.4f} seconds")


# start_time = time.time()
# sheet_data = portalInstance.readDataFromSheet()
# end_time = time.time()
# print(f"Time taken to read data from Google Sheets: {end_time - start_time:.4f} seconds")

# print("============TESTING FOR CARD VERIFICATION============")
# start_time = time.time()
# is_verified = portalInstance.verifyUserID('1111111111111111') & portalInstance.verifyUserPin('1111')
# end_time = time.time()
# print(f"User Verified: {is_verified}")
# print(f"Time taken for first verification: {end_time - start_time:.4f} seconds")

# start_time = time.time()
# is_verified = portalInstance.verifyUserID('3333333333333333') & portalInstance.verifyUserPin('3333')
# end_time = time.time()
# print(f"User Verified: {is_verified}")
# print(f"Time taken for second verification: {end_time - start_time:.4f} seconds")

# start_time = time.time()
# is_verified = portalInstance.verifyUserID('2222222222222222') | portalInstance.verifyUserPin('2222')
# end_time = time.time()
# print(f"User Verified: {is_verified}")
# print(f"Time taken for third verification: {end_time - start_time:.4f} seconds")

# print("============TESTING FOR ADDING USER============")


# is_verified = portalInstance.verifyUserID('4444444444444444')
# print(f"User Verified: {is_verified}")
# print(f"Time taken to verify new user (before adding): {end_time - start_time:.4f} seconds")

# start_time = time.time()
# portalInstance.writeUser('4444444444444444', '4444')
# end_time = time.time()

# is_verified = portalInstance.verifyUserID('4444444444444444')
# print(f"User Verified: {is_verified}")
# print(f"Time taken to verify new user (after adding): {end_time - start_time:.4f} seconds")

# print("============TESTING FOR WIFI CONNECTION============")
# #Need to connect to an ESP32
# portalInstance.connectToWifi() # Previously Tested Successfully