from aiogram import Bot, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove

from aiohttp import web
import database

import re
import os
import time
import json
import requests

import response_engine
import vectordb

import database
import bubbledb
import connectBubble
import loginuser
import paymentstest
import voicenoteHandler
import imagesdb
import math


from CONSTANTS import *

# Telegram bot states
    # awaiting_email
    # awaiting_contact
    # awaiting_verification

    # response_engine


# Tasks
    # Store user_data vars in database
        # Bot states
        # Expected code



bot = Bot(token=TOKEN)


# Define global variables

COMMAND_HANDLERS = {
    "/help": None,
    "/feedback": None,
    "/callme": None,
    "/balance": None,
    "/deposit": None,
}


LOGIN_FUNCTIONS = {
    "awaiting_email": None,
    "awaiting_contact": None,
    "awaiting_verification": None,
}




# Default assuming user has logged in
login_status = True



# @functions_framework.http
async def webhook_entry(request):
    print("Request received")
    if request.method == "POST":
        update = await request.json()

        if 'message' in update:
            message = types.Message(**update['message'])

            user_text = message.text
            print("User said: ", user_text)

            user_id = str(message.from_user.id)

            # Check if user has to login - get current state
            state = database.get_state(BOT_USERNAME, user_id)
            print(state)
                        
            if(state != "response_engine"):
                login_status = False
            else:
                login_status = True

            ################## Handling user's message ##################
            
            # Handling if user hasn't logged in
            if(login_status == False):
                # If state doesn't exist then set it to awaiting_email
                if(state == None):
                    # Add user to database, send initial message asking them to send their email, and set state to awaiting_email
                    await initialize_user(message)
                else:
                    if(user_text != None):
                        text = message.text.strip()
                        print(f"Received text: {text}")  # Print the text of the message
                        if text.startswith('/'):
                            await bot.send_message(chat_id=message.chat.id, text = "Please complete signing up before using any commands")
                        else:
                            # Use the login function mapping for dispatch
                            login_function = LOGIN_FUNCTIONS.get(state)  # Extract login function and get handler

                            if login_function:
                                await login_function(message)
                            
                            print("Non message function")
                            # Handle non-command text messages
                    else:
                        # Check if contact exists
                        if(state == "awaiting_contact"):
                            contact = message.contact
                            if(contact != None):
                                await handle_contact_for_login(message)

            # Handling if user is already signed up
            else:
                if(user_text != None):
                    text = message.text.strip()
                    print(f"Received text: {text}")  # Print the text of the message

                    if text.startswith('/'):
                        print("Is a command")
                        # Use the command mapping for dispatch
                        command_handler = COMMAND_HANDLERS.get(text.split()[0])  # Extract command and get handler
                        if command_handler:
                            await command_handler(message)
                        else:
                            # Optionally handle unknown commands
                            await bot.send_message(chat_id=message.chat.id, text="Sorry, I don't recognize that command.")

                    else:
                        print("Non message function")
                        # Handle non-command text messages
                        await handle_response(message)
                
                # Handling voice note
                elif message.voice is not None:
                    print("Recieved voice note")
                    await handle_user_voice_note(message)
        
        return web.Response(status=204)
    return web.Response(text='OK', status=200)









########## Telegram bot login functions ##########

async def initialize_user(message: types.Message):

    user_id = str(message.from_user.id)

    # Check if user is subscribed and add them if not
    database.add_user_to_influencer_subscription(BOT_USERNAME, user_id)

    # set stage to awaiting_email
    database.update_state(BOT_USERNAME, user_id, "awaiting_email")

    user_first_name = message.from_user.first_name
    

    # Send user an intro image
    image_url = "https://static.wixstatic.com/media/e1234e_36641e0f2be447bea722377cd31945d3~mv2.jpg/v1/crop/x_254,y_168,w_972,h_937/fill/w_506,h_488,al_c,q_80,usm_0.66_1.00_0.01,enc_auto/IMG_20231215_134002.jpg"
   
    # await send_image(update, context, image_url)
    await bot.send_photo(chat_id=message.chat.id, photo=image_url)

    message_text = f'''Hey {user_first_name}, welcome to {AI_NAME} 💕!

I was created by Veronica Avluv and trained on everything you can know about her. I'm built to act, talk and sound just like she does.

I can call you, text you, send voice notes, and send pics. I can also get real naughty, especially when you call me ;)

To get started I need your phone number and email in order to make your account.
☐ Email
☐ Phone number

By sharing your email and phone number, you agree to our Terms of Service (https://veronica.tryinfluencerai.com/terms-and-conditions) and have read and acknowledged the Privacy Policy (https://veronica.tryinfluencerai.com/privacy)
'''
    print("Sending message to user")
    await bot.send_message(chat_id=message.chat.id, text=message_text)
    await bot.send_message(chat_id=message.chat.id, text="Enter your email below:")



async def awaiting_email(message: types.Message):
    user_email = message.text
    user_id = str(message.from_user.id)


    # Check if user entered a valid email
    if re.match(r"[^@]+@[^@]+\.(?!con$)[^@]+", user_email):
        # Set stage to awaiting_contact
        database.update_state(BOT_USERNAME, user_id, "awaiting_contact")

        # Store user email in database
        database.store_user_email(BOT_USERNAME, user_id, user_email)

        # After email is received and validated, ask for the phone number
        message_text = '''Thank you for sharing your email honey.
☒ Email
☐ Phone number

Now, could I please get your phone number? Just press the button below for me okay?

By sharing your email and phone number, you agree to our Terms of Service (https://veronica.tryinfluencerai.com/terms-and-conditions) and have read and acknowledged the Privacy Policy (https://veronica.tryinfluencerai.com/privacy)
'''

        # Custom keyboard to request contact
        markup = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="📞 Share Phone Number", request_contact=True)]
            ],
            resize_keyboard=True
        )

        await bot.send_message(chat_id=message.chat.id, text=message_text)
        await bot.send_message(chat_id=message.chat.id, text="Please share your phone number.", reply_markup=markup)


    # If user didn't enter a valid email - ask them to re-enter it
    else:
        # Set stage to awaiting_contact
        database.update_state(BOT_USERNAME, user_id, "awaiting_email")

        # Handle invalid email format
        await bot.send_message(chat_id=message.chat.id, text="It seems like the email you entered is invalid.")
        await bot.send_message(chat_id=message.chat.id, text="Please enter your email again below:")



async def verify_number(message: types.Message, phone_number: str) -> None:
    user_id = str(message.from_user.id)

    print("Finding verfication status")
    verification_status = database.get_verification_status(BOT_USERNAME, user_id)
    print("verification_status:", verification_status)

    if(verification_status == True):
        return

    # Assuming loginuser.generate_random_number() and loginuser.send_verification_code() are defined elsewhere
    verification_code = loginuser.generate_random_number()
    
    loginuser.send_verification_code(phone_number, verification_code)

    database.update_verification_status(BOT_USERNAME, user_id, "False")
    database.update_verification_code(BOT_USERNAME, user_id, verification_code)

    print("Sent verification code: ", verification_code)

    # Ask user for the verification code
    await bot.send_message(chat_id=message.chat.id, text=f'Also could you please just enter the verification code to {phone_number} for me?', reply_markup=ReplyKeyboardRemove())





# Funciton to handle when user sends contact during login - saves their phone number
async def handle_contact_for_login(message: types.Message):
    contact = message.contact    
    phone_number = contact.phone_number
    user_id = str(message.from_user.id)

    # Save phone number in database
    database.store_user_phone_number(BOT_USERNAME, user_id, str(phone_number))
    
    await bot.send_message(chat_id=message.chat.id, text="Thank you for sharing your phone number, can you make sure you're accepting calls from unknown numbers so I can give you a ring?", reply_markup=ReplyKeyboardRemove())
    
    await verify_number(message, phone_number)

    database.update_state(BOT_USERNAME, user_id, "awaiting_verification")




#### Helper function to vaidate phone number format ####
def gpt_verify_and_format_number(phone_number:str): # -> List[bool, str]:
    phone_verify_prompt = '''Your job is to verify and format if a phone number is correct.
A phone number should follow the conventional code such where it's the country code followed by the area code and rest of the number.
For example this is an example of a correct number: +16477667841
And this is an example of a wrong number: 164776678

If number is valid but is in the wrong format, reformat it and return it back. If a number is not valid, then return back INVALID. Do not include "OUTPUT" in your actual message.
These are some examples:
Input:16477667
Output: INVALID

Input: 6477667841
Output: MISSING COUNTRY CODE

Input:+1-416-933-2213
Output: +14169332213'''

    phone_input_prompt = f'''Phone number: {phone_number}
OUTPUT: '''

    messages = [{"role" : "system", "content" : phone_verify_prompt}]
    messages.append({"role": "user", "content": phone_input_prompt})

    ai_response = ""    
    for res in response_engine.call_openai_stream_gpt4_turbo(messages):
        ai_response += res
    
    print(ai_response)

    if("invalid" in ai_response.lower()):
        return False, None
    elif("missing" in ai_response.lower()):
        return False, "missing area code"
    else:
        return True, ai_response


async def handle_phone_via_text(message: types.Message):
    phone_number_entered = message.text
    user_id = str(message.from_user.id)

    # Validate phone number by using the verification and formatting function
    is_valid, formatted_number_or_message = gpt_verify_and_format_number(phone_number_entered)

    if is_valid:
        # Store the formatted phone number in Firestore
        database.store_user_phone_number(BOT_USERNAME, user_id, formatted_number_or_message)

        # Inform the user
        database.add_chat_to_user_history(BOT_USERNAME, user_id, 'assistant', 'Influencer: ' + "Thank you for sharing your phone number.")

        await bot.send_message(chat_id=message.chat.id, text="Thank you for sharing your phone number, can you make sure you're accepting calls from unknown numbers so I can give you a ring?")

        # Update user's state to awaiting_verification
        database.update_state(BOT_USERNAME, user_id, "awaiting_verification")

        await verify_number(message, formatted_number_or_message)

    else:
        # Custom keyboard to request contact
        markup = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="📞 Share Phone Number", request_contact=True)]
            ],
            resize_keyboard=True
        )

        # Ask the user to try again or use the button
        retry_message = "The entered number seems invalid."
        if formatted_number_or_message == "missing area code":
            retry_message += " It seems like the country code is missing."
        
        retry_message += '''

Please try again using the '📞 Share Phone Number' button below.'''

        await bot.send_message(chat_id=message.chat.id, text=retry_message, reply_markup=markup)


async def awaiting_verification(message: types.Message):
    user_id = str(message.from_user.id)

    code_entered = message.text
    expected_code =  database.get_verification_code(BOT_USERNAME, user_id)


    if(str(code_entered) == str(expected_code)):
        # Go to the response_engine stage - user is fully signed up
        database.update_state(BOT_USERNAME, user_id, "response_engine")
        database.update_verification_status(BOT_USERNAME, user_id, "True")

        # Call intro user function to send all the intro and welcome message and initialize user in the Bubble database
        await intro_user(message)
    
    else:
        # Go back to the awaiting_contact stage to get their phone number again
        database.update_state(BOT_USERNAME, user_id, "awaiting_contact") 

        # Custom keyboard to request contact
        markup = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="📞 Share Phone Number", request_contact=True)]
            ],
            resize_keyboard=True
        )

        message_text = "The code you entered was incorrect, please share your phone number again"

        await bot.send_message(chat_id=message.chat.id, text=message_text, reply_markup=markup)



async def intro_user(message: types.Message):
    user_id = str(message.from_user.id)

    # Send user an welcome image
    image_url = "https://static.wixstatic.com/media/e1234e_36641e0f2be447bea722377cd31945d3~mv2.jpg/v1/crop/x_254,y_168,w_972,h_937/fill/w_506,h_488,al_c,q_80,usm_0.66_1.00_0.01,enc_auto/IMG_20231215_134002.jpg"

    await bot.send_photo(chat_id=message.chat.id, photo=image_url)

    await bot.send_message(chat_id=message.chat.id, text=f"""You're all set to start using {AI_NAME}!

I can send you voice notes, text you picutres, and even be able to call you.

To start a call enter /callme and I'll call the phone number you have with your account. Remember, I can get extra dirty on call ;) (come and find out yourself).

You have 5 free credits. 
To buy more credits or subscribe just enter /deposit

Enter /help if you run into any issues.""")

    has_phone, phone_number = database.phone_number_status(BOT_USERNAME, user_id)

    # Initialize user in the database
    user_unique_id = connectBubble.find_user(phone_number)

    email_status, email = database.user_email_status(BOT_USERNAME, user_id)

    if(has_phone == False or email_status == False):
        print("HOW THE FUCK DID WE GET HERE")
        print("USER DOESN'T HAVE AN EMAIL OR PHONE NUMBER STORED")
        print("Possible issue with Firebase storing")
        return

    # Handle no user being found - must create new user
    if(user_unique_id == False):
        print("Creating new user in Bubble - user phone number not found")
        
        first_name = message.from_user.first_name

        # Create user in Bubble database
        user_unique_id = connectBubble.create_user(email, phone_number, first_name)
    else:
        print("User found ", user_unique_id)

    database.add_bubble_unique_id(BOT_USERNAME, user_id, user_unique_id)
                
    # Create and add subscription
    subscription_id = database.add_subscription_id(BOT_USERNAME, user_id, user_unique_id)

    await bot.send_message(chat_id=message.chat.id, text=f"hey {message.from_user.first_name}, it's great to meet you")
    await bot.send_message(chat_id=message.chat.id, text=f"I'm going to give you a quick call just to say hi!")
    await bot.send_message(chat_id=message.chat.id, text=f"just make sure that do not disturb is off so my call goes through")

    # Call the user
    dispatch_intro_call(message.from_user.first_name, email, phone_number, AGENT_ID, subscription_id, user_unique_id)



def dispatch_intro_call(name, email, phone_number, agent_id, subscription_id, user_id):
    place_call(agent_id, phone_number, name, email, user_id, 9000, 1, subscription_id, "", is_intro = True)




# Update LOGIN_FUNCTIONS with actual functions
LOGIN_FUNCTIONS["awaiting_email"] = awaiting_email
LOGIN_FUNCTIONS["awaiting_contact"] = handle_phone_via_text
LOGIN_FUNCTIONS["awaiting_verification"] = awaiting_verification








########## Telegram bot commands ##########
async def start_command(message: types.Message):
    return

async def help_command(message: types.Message):
    message_text = f'''If you want me to call you, use /callme
To see your balance use /balance
To buy more credits or subscribe, use /deposit

If you're facing any issues, contact admin@tryinfluencer.ai'''

    await bot.send_message(chat_id=message.chat.id, text=message_text)


async def feedback_command(message: types.Message):
    message_text = f'''Submit any feedback you have for InfluencerAI here:
https://forms.gle/ZvB4vXse3SZKfqHA6

You're feedback helps us improve your experience and add features you want to see.'''
    await bot.send_message(chat_id=message.chat.id, text=message_text)


async def balance_command(message: types.Message):
    user_id = str(message.from_user.id)

    # Get the user's credits info
    unique_id = database.get_bubble_unique_id(BOT_USERNAME, user_id)

    # Double check that user actually exists
    if(unique_id == False or unique_id == 'False'):
        print("Unique ID is False - doesn't exist")
        print("User should not get here - fix the bug")
        acountinfo_message = f'''You don't have a phone number connected to your account yet. Please finsh signing up in order to access your account info.'''
    else:
        num_credits = connectBubble.get_minutes_credits(unique_id)
        num_credits = str(round(num_credits, 2))
        acountinfo_message = f'''You have *{num_credits} InfluencerAI credits* available

To add credits to your account or subscribe, use /deposit'''
        
    await bot.send_message(chat_id=message.chat.id, text=acountinfo_message, parse_mode='Markdown')


async def callme_command(message: types.Message) -> None:
    user_id = str(message.from_user.id)

    has_phone, phone_number = database.phone_number_status(BOT_USERNAME, user_id)

    user_unique_id = database.get_bubble_unique_id(BOT_USERNAME, user_id)

    if(has_phone == True):
        user_first_name = message.from_user.first_name
        prospect_email = connectBubble.get_user_email(user_unique_id)
        credits_left = connectBubble.get_minutes_credits(user_unique_id)
        subscription_id = database.get_subscription_id(BOT_USERNAME, user_id)
        
        # IMPLEMENT LATER: fan description left blank
        fan_description = ""

        await message.reply("i'm calling you, check your phone") 

        place_status = place_call(AGENT_ID, phone_number, user_first_name, prospect_email, user_unique_id, credits_left, CREDITS_PER_MINUTE,
                                  subscription_id, fan_description)
        

        print("place_status: ", place_status)

        if(place_status):
            print("Placed call")
        else:
            # ERROR - add handling later
            database.add_chat_to_user_history(BOT_USERNAME, user_id, 'assistant', 'Influencer: ' + "i'm having some trouble calling you right now, can you try again later?")
            await message.reply("i'm having some trouble calling you right now, can you try again later?")
    else:
        await message.reply("you need to connect your phone number in order for me to be able to call you")






# Update COMMAND_HANDLERS with actual functions
COMMAND_HANDLERS["/start"] = start_command
COMMAND_HANDLERS["/help"] = help_command
COMMAND_HANDLERS["/feedback"] = feedback_command
COMMAND_HANDLERS["/callme"] = callme_command
COMMAND_HANDLERS["/balance"] = balance_command
COMMAND_HANDLERS["/deposit"] = paymentstest.purchase








def place_call(agent_id, phone_number, prospect_name, prospect_email, unique_id, credits_left, credits_per_minute, subscription_id, fan_description, **kwargs):
    url = "https://callfusion-0c6c4ca2c8e6.herokuapp.com/dispatch_demo_call"
    headers = {"Content-Type": "application/json"}

    prospect_details = {
            "name": prospect_name,
            "email": prospect_email,
            "user_id": unique_id,
            "credits_left": credits_left,
            "credits_per_minute": credits_per_minute,
            "subscription_id": subscription_id,
            "fan_description": fan_description
        }
    prospect_details.update(kwargs)
    data = {
        "phone_number": phone_number,
        "agent_id": agent_id,
        "agent_to_use": "emma_live",
        "prospect_details": prospect_details,
    }

    response = requests.post(url, headers=headers, data=json.dumps(data))
    if response.status_code == 200:
        # print(response.json())  # Assuming the successful response is a JSON
        return True
    else:
        # print("Error: ", response.text)
        return False




async def handle_user_voice_note(message: types.Message) -> None:
    transcription = await voicenoteHandler.transcribe_user_voice_note(message)

    await handle_response(message, transcription)



async def handle_response(message: types.Message, voicenote_transcription=None) -> None:
    user_id = str(message.from_user.id)    
    
    # Case when user doesn't send voice - take text from Telegram's user data
    if(voicenote_transcription == None):
        text = message.text
    else:
        text = voicenote_transcription
    
    
    # Double check if user has enough credits if voice_notes_status is set to "enabled"
    # if(context.user_data['voice_notes_status'] == "enabled"):
    # Check if user has enough credits
    unique_id = database.get_bubble_unique_id(BOT_USERNAME, user_id)

    
    current_minutes_credits = connectBubble.get_minutes_credits(unique_id)
    print("current_minutes_credits: ", current_minutes_credits)
    

    if(current_minutes_credits <= 0):
        # Send message to buy credits
        await bot.send_message(chat_id=message.chat.id, text="You are out of minutes for your account. Purchase more below in order to continue.")
        await paymentstest.purchase(message)
        
    else:
        await voicenoteHandler.voice_note_creator(message, text, unique_id)














async def handle_command(message: types.Message):
    print("Handling commands")
    # Example: Responding to the /start command
    if message.text == '/start':
        await bot.send_message(chat_id=message.chat.id, text="Welcome to the bot!")
    elif message.text == '/help':
        await bot.send_message(chat_id=message.chat.id, text="How can I assist you?")


async def handle_message(message: types.Message):
    # Echo the received text message
    await bot.send_message(chat_id=message.chat.id, text=message.text)







app = web.Application()
app.router.add_post('/webhook', webhook_entry)
app.router.add_get('/webhook', webhook_entry)  # For simple GET verification

if __name__ == '__main__':
    web.run_app(app, port=8080)


# https://api.telegram.org/bot6736028246:AAGbbsnfYsBJ1y-Fo0jO4j0c9WBuLxGDFKk/setWebhook?url=https://f2a5-2607-fea8-34dd-4f90-d3a-4bf1-b225-d1e2.ngrok-free.app/webhook