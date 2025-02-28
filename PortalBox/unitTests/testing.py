
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