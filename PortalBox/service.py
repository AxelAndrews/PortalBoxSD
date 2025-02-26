import network #REQUIRES A ESP32 TO BE CONNECTED ELSE AN ERROR WILL OCCUR
import time
import neopixel
from machine import Pin
# import datetime
from portalBoxFSM import State
# import gspread
# from google.oauth2.service_account import Credentials
import os

import read as CardReader

class Database:
    pass

class PortalBoxService:
    def __init__(self):
        self.filename="./userData.txt"
        self.debugFile="./debug.txt"
        self.wlan = network.WLAN(network.STA_IF)
        self.wlan.active(True)
        self.currUser=[]
        self.userID=""

        led = Pin(8, Pin.OUT) # GPIO2 is often connected to the onboard LED
        self.np=neopixel.NeoPixel(led,1) 
        self.state = State.IDLE_NOCARD
        
        self.startUp()
        
    def startUp(self):
        while True:
            # Ensure connection to the internet
            while not self.wlan.isconnected():
                self.log_to_debug_file("Connecting/Reconnecting to Internet")
                self.enterIdleNoCard()
                self.connectToWifi()
                
            #Keep looping until it gets a RFID card

            if self.readCardReader()==-1 and self.state != State.IDLE_NOCARD:
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
                    self.turnGreen()
                else:
                    while not self.buttonPressed():
                        # START BUZZER
                        pass
                    #STOP BUZZER
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
            
    def sendDebugToSheet(self):
        """
        This function reads the 'debug.csv' file and uploads each line to a Google Sheets worksheet, 
        then clears the worksheet after the upload.
        """
        # Define the scopes and load credentials from the service account file
        scopes = ["https://www.googleapis.com/auth/spreadsheets"]
        creds = Credentials.from_service_account_file("googleSheets.json", scopes=scopes)

        # Authorize the client using the credentials
        client = gspread.authorize(creds)

        # Define the sheet ID and open the spreadsheet
        sheet_id = "1SRf5OOWelnRHOKptlMJtqZEZVGsJi7lgn29zlKJ6IEY"
        workbook = client.open_by_key(sheet_id)

        # Read data from CSV file
        with open(self.debugFile, mode='r') as file:
            reader = csv.reader(file)
            values = list(reader)  # Convert CSV rows to list of lists

        # Get a list of all worksheets in the workbook
        worksheet_list = map(lambda x: x.title, workbook.worksheets())
        new_worksheet_name = "debugFile"

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

        # Now, we send each row one by one to the sheet
        print("Sending data to sheet...")
        for row in values:
            # Send each line to the sheet one by one starting from A1
            sheet.append_row(row)

        # Optionally, you can add any other operations like adding formulas or formatting
        print("Data successfully uploaded to the Google Sheet!")

        # After uploading, you can clear the file or reset it if needed
        with open(self.debugFile, 'w') as f:
            f.truncate(0)  # This will clear the contents of the file
            print(f"{self.debugFile} has been cleared.")
            
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



            # # FIGURE OUT HOW WE CAN TRANSITION TO THE RUNNING NO CARD STATE
            # elif self.state==State.RUNNING_AUTHORIZED and self.readCardReader():
            #     self.state = State.RUNNING_NOCARD
            #     continue
            # #Authorized and Looking for a Proxy Card
            # elif self.state == State.RUNNING_NOCARD:
            #     ############
            #     #Start Buzzer
            #     ############
            #     userID = self.readCardReader()
            #     #Check for button press OR a new card is inserted
            #     #THIS DOES NOT WORK ATM, FIGURE OUT HOW TO STOP THE CARD READER
            #     while True:
            #         # If button is pressed then reset to default state and wait for next card
            #         if self.buttonPress():
            #             self.state=State.IDLE_NOCARD
            #             break
            #         # If a new card is inserted, update the self.currUser
            #         else:
            #             userID=self.readCardReader()
            #             # If it is a proxy card, switch to proxy state
            #             if self.currUser[1] != 2:
            #                 self.state==State.RUNNING_PROXY
            #                 break
            #             else:
            #                 break
            #         time.sleep(2)
                    
            # elif self.state == State.RUNNING_TRAINING:
            #     #Don't worry about this for now
            #     pass
                    
            # #Once we get a UserID OR Proxy Card, verify it
            # if self.verifyUserID(userID):
            #     #CardID is in csv
            #     self.enterIdleAuthWaitingPin()
            # else:
            #     self.enterIdleUnauthorized()
            #     time.sleep(2)
            #     self.enterIdleNoCard()
            
            # #Keep looping until it gets a Pin card
            # pin = self.readKeypad()
            # while True:
            #     pin = self.readKeypad()
            #     break
            
            # if self.verifyUserPin(pin):
            #     #Verify Pin and Authorize User
            #     self.enterRunningAuthorized()
            #     #Deliver Power to Machine/Power Relay
            # else:
            #     self.enterIdleUnauthorized()
            #     time.sleep(2)
            #     self.enterIdleNoCard()