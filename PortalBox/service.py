# import network #REQUIRES A ESP32 TO BE CONNECTED ELSE AN ERROR WILL OCCUR
import time
import datetime
import csv
from portalboxFSM import State
import gspread
from google.oauth2.service_account import Credentials

class Database:
    pass

class PortalBoxService:
    def __init__(self):
        self.filename="./userData.csv"
        self.state = State.IDLE_NOCARD
        # self.startUp()
        # self.timeStart = datetime.now()
        # self.graceStart = datetime.now()
        # self.timeDelta = timedelta(0)
        # self.graceDelta = timedelta(seconds = 2)
        
    def startUp(self):
        while True:
            # First thing that Happens is that it checks to see if it is connected to the internet
            while ~self.isConnectedToWifi():
                print("Connecting/Reconnecting to Internet")
                self.enterIdleNoCard()
                self.connectToWifi()
                
            if self.verifyUserID(self.readCardReader()):
                self.enterIdleAuthWaitingPin()
            elif ~self.verifyUserID(self.readCardReader()):
                self.enterIdleUnauthorized()
                #Send data back somehow
                self.enterIdleNoCard()
                continue
            
            if self.verifyUserPin(self.readKeypad()):
                self.enterRunningAuthorized()
                #DELIVER POWER TO MACHINE
                #KEEP CHECKING THAT CARD IS THERE
                while self.verifyUserPin(self.readKeypad()):
                    pass
                
            time.sleep(2)
                
            
            
    def enterIdleNoCard(self):
        self.state = State.IDLE_NOCARD
        print(f"State changed to: {self.state}")

    def enterIdleUnauthorized(self):
        self.state = State.IDLE_UNAUTHORIZED
        print(f"State changed to: {self.state}")

    def enterIdleAuthWaitingPin(self):
        self.state = State.IDLE_AUTH_WAITINGPIN
        print(f"State changed to: {self.state}")

    def enterRunningAuthorized(self):
        self.state = State.RUNNING_AUTHORIZED
        print(f"State changed to: {self.state}")

    def enterRunningNoCard(self):
        self.state = State.RUNNING_NOCARD
        print(f"State changed to: {self.state}")

    def enterRunningProxy(self):
        self.state = State.RUNNING_PROXY
        print(f"State changed to: {self.state}")

    def enterRunningTraining(self):
        self.state = State.RUNNING_TRAINING
        print(f"State changed to: {self.state}")

    def readKeypad(self):
        '''
        Get data from the RFID Scanner
        '''
        return ['1111','2222', '3333']
    
    def readCardReader(self):
        '''
        Get data from the RFID Scanner
        '''
        #Simulates 3 different RFID tags with pins
        return ['1111111111111111',
                '2222222222222222',
                '3333333333333333']
        
        
    def verifyUserID(self, userID):
        '''
        Get data from CSV and verify if the given user exists
        '''
        file = open(self.filename, mode='r')
        try:
            reader = csv.reader(file)
            next(reader)
            for row in reader:
                if row[1] == userID:
                    return True
            return False
        finally:
            file.close()
            
    def verifyUserPin(self, pin):
        '''
        Get data from CSV and verify if the given user exists
        '''
        file = open(self.filename, mode='r')
        try:
            reader = csv.reader(file)
            next(reader)
            for row in reader:
                if row[2] == pin:
                    return True
            return False
        finally:
            file.close()
        
    def writeUser(self, userID, pin):
        with open(self.filename, mode='a', newline='') as file:
            try:
                writer = csv.writer(file)
                file.write(f"\n0,{userID},{pin}")
                print("User added successfully.")
            except Exception as e:
                print(f"Error: {e}")
                
    def connectToWifi(self):
        '''
        Connect to WiFi and verify connection
        '''
        SSID='bucknell_iot'
        password=""
        wlan = network.WLAN(network.STA_IF)
        wlan.active(True)

        # Scan for local networks
        print("Scanning for networks...")
        networks = wlan.scan()
        for network in networks:
            print("Found network:", network)

        # Check if connected
        if not wlan.isconnected():
            print('Connecting to network...')
            wlan.connect(SSID, password)
            timeout = 10  # Timeout in seconds, should not take more than 10 seconds
            start_time = time.time()  # Start timer

            # Get current timer value and check if it is less than the timeout
            while not wlan.isconnected() and (time.time() - start_time) < timeout:
                # Pause between each check
                print("Waiting for connection...")
                time.sleep(1)

            if not wlan.isconnected():
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



portalInstance = PortalBoxService()

start_time = time.time()
portalInstance.sendDataToSheet()
end_time = time.time()
print(f"Time taken to send data to Google Sheets: {end_time - start_time:.4f} seconds")


start_time = time.time()
sheet_data = portalInstance.readDataFromSheet()
end_time = time.time()
print(f"Time taken to read data from Google Sheets: {end_time - start_time:.4f} seconds")

print("============TESTING FOR CARD VERIFICATION============")
start_time = time.time()
is_verified = portalInstance.verifyUserID('1111111111111111') & portalInstance.verifyUserPin('1111')
end_time = time.time()
print(f"User Verified: {is_verified}")
print(f"Time taken for first verification: {end_time - start_time:.4f} seconds")

start_time = time.time()
is_verified = portalInstance.verifyUserID('3333333333333333') & portalInstance.verifyUserPin('3333')
end_time = time.time()
print(f"User Verified: {is_verified}")
print(f"Time taken for second verification: {end_time - start_time:.4f} seconds")

start_time = time.time()
is_verified = portalInstance.verifyUserID('2222222222222222') | portalInstance.verifyUserPin('2222')
end_time = time.time()
print(f"User Verified: {is_verified}")
print(f"Time taken for third verification: {end_time - start_time:.4f} seconds")

print("============TESTING FOR ADDING USER============")


is_verified = portalInstance.verifyUserID('4444444444444444')
print(f"User Verified: {is_verified}")
print(f"Time taken to verify new user (before adding): {end_time - start_time:.4f} seconds")

start_time = time.time()
portalInstance.writeUser('4444444444444444', '4444')
end_time = time.time()

is_verified = portalInstance.verifyUserID('4444444444444444')
print(f"User Verified: {is_verified}")
print(f"Time taken to verify new user (after adding): {end_time - start_time:.4f} seconds")

print("============TESTING FOR WIFI CONNECTION============")
Need to connect to an ESP32
portalInstance.connectToWifi() # Previously Tested Successfully