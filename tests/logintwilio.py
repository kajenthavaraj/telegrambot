# from twilio.rest import Client

# def send_verification_code(phone_number: str) -> bool:
#     # Your Twilio Account SID and Auth Token
#     account_sid = 'AC457220702163236cebf7cc88bbe12298'
#     auth_token = 'cfc1b41040343f5cc76ce88190093706'
#     client = Client(account_sid, auth_token)

#     # Your Verify Service SID
#     verify_service_sid = 'VA0e796368adda7eec951ba7debeac64df'

#     try:
#         # Sending a verification code using the Verify service
#         verification = client.verify.services(verify_service_sid) \
#             .verifications \
#             .create(to=phone_number, channel='sms')

#         print(verification.sid)

#         return True

#     except Exception as e:
#         print(f"An error occurred: {e}")
#         return False

# # Example usage
# # send_verification_code("+16477667841")


# def check_verification_code(phone_number: str, code: str) -> bool:
#     account_sid = 'AC457220702163236cebf7cc88bbe12298'
#     auth_token = 'cfc1b41040343f5cc76ce88190093706'
#     client = Client(account_sid, auth_token)

#     verify_service_sid = 'VA0e796368adda7eec951ba7debeac64df'

#     try:
#         verification_check = client.verify.services(verify_service_sid) \
#             .verification_checks \
#             .create(to=phone_number, code=code)

#         if verification_check.status == "approved":
#             print("Verification successful.")
#             return True
#         else:
#             print("Verification failed.")
#             return False

#     except Exception as e:
#         print(f"An error occurred: {e}")
#         return False

# # Example usage
# check_verification_code("+16477667841", "618199")