import random
import string
from twilio.rest import Client
from config import TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN

# General Algo
# 1.) Requests for user's number on Telegram -> ONLY SHARE CONTACT
        # a.) if enters number manually - then prompt them to share contact
# 2.) Search phone number on Bubble
    # a.) If no number found:
            # Send info to make an account
    # b.) If number found:
            # Log user in




# Random letter code generator
def generate_random_code(length=9):
    # Define the characters to choose from, in this case, lowercase letters
    letters = 'abcdefghijklmnopqrstuvwxyz'
    
    # Generate a random 9-letter code as a string
    random_code = ''.join(random.choice(letters) for i in range(length))
    
    return random_code



# Random number generator
def generate_random_number(length=6):
    # Define the characters to choose from, in this case, digits
    digits = '0123456789'
    
    # Generate a random 6-digit number as a string
    random_number = ''.join(random.choice(digits) for i in range(length))
    
    return random_number

# Example usage
# print(generate_random_number())


# Sending SMS to user
def send_verification_code(phone_number:str, code) -> bool:
    # Your Twilio Account SID and Auth Token from environment variables
    client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

    try:
        # Sending an SMS
        message = client.messages.create(
            to=phone_number,
            from_="16473603089",
            body=f"Your InfluencerAI verification code is {code}")

        print(message.sid)

        return True
    
    except:
        # Print out error
        
        print("Error sending SMS")
        return False

# Example Usage
# code = generate_random_number()
# print(code)
send_verification_code("16477667841", str("Wagwan"))






# Once user uses login code. add their telegram user_id to bubble for the AI to know
