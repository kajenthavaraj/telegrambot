# from twilio.rest import Client

# def send_verification_code(phone_number: str) -> bool:
#     # Twilio credentials loaded from environment variables
#     from config import TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN
#     client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

#     # Your Verify Service SID
#     verify_service_sid = 'YOUR_VERIFY_SERVICE_SID'

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
#     # Twilio credentials loaded from environment variables
#     from config import TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN
#     client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

#     verify_service_sid = 'YOUR_VERIFY_SERVICE_SID'

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