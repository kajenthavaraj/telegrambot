from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove

from aiohttp import web
import database
import asyncio
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
from influencer_data import Influencer, load_influencers

# Telegram bot states
    # awaiting_email
    # awaiting_contact
    # awaiting_verification

    # response_engine


# Tasks
    # Store user_data vars in database
        # Bot states
        # Expected code




# Define global variables

COMMAND_HANDLERS = {
    "/help": None,
    "/feedback": None,
    "/callme": None,
    "/balance": None,
    "/deposit": None,
    "/manage": None,
    "/subscribe": None,
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

        agent_id = request.match_info['slug']
        influencer_obj : Influencer = Influencer._registry[agent_id]
        telegram_bot : Bot = influencer_obj.bot_object
        update = await request.json()

        print("UPDATE: " + str(update))

        if 'message' in update:
            message = types.Message(**update['message'])

            print("MESSAGE: " + str(message))

            user_text = message.text
            print("User said: ", user_text)

            user_id = str(message.from_user.id)

            # Check if user has to login - get current state
            state = database.get_state(influencer_obj.bot_username, user_id)
            print(state)


            if(state != "response_engine" and state != "in_intro_call"):
                login_status = False
            else:
                login_status = True

            if state == "in_intro_call":
                database.update_state(influencer_obj.bot_username, user_id, "response_engine")

            ################## Handling user's message ##################
            
            # Handling if user hasn't logged in
            if(login_status == False):
                # If state doesn't exist then set it to awaiting_email
                if(state == None):
                    # Add user to database, send initial message asking them to send their email, and set state to awaiting_email
                    await initialize_user(message, influencer_obj)
                elif state == "pending_intro":
                    pass
                else:
                    if(user_text != None):
                        text = message.text.strip()
                        print(f"Received text: {text}")  # Print the text of the message
                        if text.startswith('/'):
                            await telegram_bot.send_message(chat_id=message.chat.id, text = "Please complete signing up before using any commands")
                        else:
                            # Use the login function mapping for dispatch
                            login_function = LOGIN_FUNCTIONS.get(state)  # Extract login function and get handler

                            if login_function:
                                await login_function(message, influencer_obj)
                            
                            print("Non message function")
                            # Handle non-command text messages
                    else:
                        # Check if contact exists
                        if(state == "awaiting_contact"):
                            contact = message.contact
                            if(contact != None):
                                await handle_contact_for_login(message, influencer_obj)

            # Handling if user is already signed up
            else:
                if(user_text != None):
                    text = message.text.strip()
                    print(f"Received text: {text}")  # Print the text of the message

                    if text.startswith('/'):
                        print("Is a command")
                        # Use the command mapping for dispatch
                        command_name = text.split()[0]
                        command_handler = COMMAND_HANDLERS.get(command_name)  # Extract command and get handler
                        if command_handler:
                            if(command_name == "/deposit"):
                                print("Called /deposit - passing in bot object")
                                await command_handler(message, influencer_obj)
                            elif(command_name == "/manage"):
                                print("Called /manage - passing in bot object")
                                await command_handler(message, influencer_obj)
                            elif(command_name == "/subscribe"):
                                await command_handler(message, influencer_obj)
                            else:
                                await command_handler(message, influencer_obj)
                        else:
                            # Optionally handle unknown commands
                            await telegram_bot.send_message(chat_id=message.chat.id, text="Sorry, I don't recognize that command.")

                    else:
                        print("Non message function")
                        # Handle non-command text messages
                        await handle_response(message, influencer_obj)
                
                # Handling voice note
                elif message.voice is not None:
                    print("Recieved voice note")
                    await handle_user_voice_note(message, influencer_obj)
        
        # Handling callback queries - when user clicks on buttons
        elif 'callback_query' in update:
            callback_query = types.CallbackQuery(**update['callback_query'])
            print(f"Received callback query data: {callback_query.data}")
            await paymentstest.button(callback_query, influencer_obj)
        
        return web.Response(status=204)
    return web.Response(text='OK', status=200)









########## Telegram bot login functions ##########

async def initialize_user(message: types.Message, influencer_obj : Influencer):

    user_id = str(message.from_user.id)
    bot_username = influencer_obj.bot_username
    bot = influencer_obj.bot_object

    # Check if user is subscribed and add them if not
    database.add_user_to_influencer_subscription(bot_username, user_id)

    # set stage to awaiting_email
    database.update_state(bot_username, user_id, "awaiting_email")

    user_first_name = message.from_user.first_name
    


    
    # await send_image(update, context, image_url)
    if influencer_obj.intro_image_url:
        await bot.send_photo(chat_id=message.chat.id, photo=influencer_obj.intro_image_url)

    message_text = f'''Hey {user_first_name}, welcome to {influencer_obj.ai_name} 💕!

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



async def awaiting_email(message: types.Message, influencer : Influencer):
    user_email = message.text
    user_id = str(message.from_user.id)
    bot_username = influencer.bot_username
    bot = influencer.bot_object


    # Check if user entered a valid email
    if re.match(r"[^@]+@[^@]+\.(?!con$)[^@]+", user_email):
        # Set stage to awaiting_contact
        database.update_state(bot_username, user_id, "awaiting_contact")

        # Store user email in database
        database.store_user_email(bot_username, user_id, user_email)

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
        database.update_state(bot_username, user_id, "awaiting_email")

        # Handle invalid email format
        await bot.send_message(chat_id=message.chat.id, text="""It seems like the email you entered is invalid.
Please enter your email again below:""")


async def verify_number(message: types.Message, phone_number: str, influencer : Influencer) -> None:
    user_id = str(message.from_user.id)

    print("Finding verfication status")
    verification_status = database.get_verification_status(influencer.bot_username, user_id)
    print("verification_status:", verification_status)

    if(verification_status == True):
        return
    
    # Assuming loginuser.generate_random_number() and loginuser.send_verification_code() are defined elsewhere
    verification_code = loginuser.generate_random_number()
    
    loginuser.send_verification_code(phone_number, verification_code)

    database.update_verification_status(influencer.bot_username, user_id, "False")
    database.update_verification_code(influencer.bot_username, user_id, verification_code)

    print("Sent verification code: ", verification_code)

    # Ask user for the verification code
    await influencer.bot_object.send_message(chat_id=message.chat.id, text=f'Also could you please just enter the verification code to {phone_number} for me?', reply_markup=ReplyKeyboardRemove())





# Funciton to handle when user sends contact during login - saves their phone number
async def handle_contact_for_login(message: types.Message, influencer : Influencer):
    contact = message.contact    
    phone_number = contact.phone_number
    user_id = str(message.from_user.id)

    # Save phone number in database
    database.store_user_phone_number(influencer.bot_username, user_id, str(phone_number))
    
    await influencer.bot_object.send_message(chat_id=message.chat.id, text="Thank you for sharing your phone number, can you make sure you're accepting calls from unknown numbers so I can give you a ring?", reply_markup=ReplyKeyboardRemove())
    
    await verify_number(message, phone_number, influencer)

    database.update_state(influencer.bot_username, user_id, "awaiting_verification")




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


async def handle_phone_via_text(message: types.Message, influencer : Influencer):
    phone_number_entered = message.text
    user_id = str(message.from_user.id)

    # Validate phone number by using the verification and formatting function
    is_valid, formatted_number_or_message = gpt_verify_and_format_number(phone_number_entered)

    if is_valid:
        # Store the formatted phone number in Firestore
        database.store_user_phone_number(influencer.bot_username, user_id, formatted_number_or_message)

        # Inform the user
        database.add_chat_to_user_history(influencer.bot_username, user_id, 'assistant', 'Influencer: ' + "Thank you for sharing your phone number.")

        await influencer.bot_object.send_message(chat_id=message.chat.id, text="Thank you for sharing your phone number, can you make sure you're accepting calls from unknown numbers so I can give you a ring?")

        # Update user's state to awaiting_verification
        database.update_state(influencer.bot_username, user_id, "awaiting_verification")

        await verify_number(message, formatted_number_or_message, influencer)

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

        await influencer.bot_object.send_message(chat_id=message.chat.id, text=retry_message, reply_markup=markup)


async def awaiting_verification(message: types.Message, influencer : Influencer):
    user_id = str(message.from_user.id)

    code_entered = message.text
    expected_code =  database.get_verification_code(influencer.bot_username, user_id)


    if(str(code_entered) == str(expected_code)):
        # Go to the response_engine stage - user is fully signed up
        database.update_state(influencer.bot_username, user_id, "pending_intro")
        database.update_verification_status(influencer.bot_username, user_id, "True")

        # Call intro user function to send all the intro and welcome message and initialize user in the Bubble database
        await intro_user(message, influencer)
    
    else:
        # Go back to the awaiting_contact stage to get their phone number again
        database.update_state(influencer.bot_username, user_id, "awaiting_contact") 

        # Custom keyboard to request contact
        markup = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="📞 Share Phone Number", request_contact=True)]
            ],
            resize_keyboard=True
        )

        message_text = "The code you entered was incorrect, please share your phone number again"

        await influencer.bot_object.send_message(chat_id=message.chat.id, text=message_text, reply_markup=markup)



async def intro_user(message: types.Message, influencer : Influencer):
    user_id = str(message.from_user.id)

    # Send user an welcome image
    if influencer.intro_image_url:
        await influencer.bot_object.send_photo(chat_id=message.chat.id, photo=influencer.intro_image_url)

    await influencer.bot_object.send_message(chat_id=message.chat.id, text=f"""You're all set to start using {influencer.ai_name}!

I can send you voice notes, text you picutres, and even be able to call you.

To start a call enter /callme and I'll call the phone number you have with your account. Remember, I can get extra dirty on call ;) (come and find out yourself).

You have 5 free credits. 
To buy more credits or subscribe just enter /deposit

Enter /help if you run into any issues.""")

    has_phone, phone_number = database.phone_number_status(influencer.bot_username, user_id)

    # Initialize user in the database
    user_unique_id = connectBubble.find_user(phone_number)

    email_status, email = database.user_email_status(influencer.bot_username, user_id)

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

    database.add_bubble_unique_id(influencer.bot_username, user_id, user_unique_id)
                
    # Create and add subscription
    subscription_id = database.add_subscription_id(influencer.bot_username, user_id, user_unique_id, influencer.bubble_id)

    await influencer.bot_object.send_message(chat_id=message.chat.id, text=f"hey {message.from_user.first_name}, it's great to meet you")
    await influencer.bot_object.send_message(chat_id=message.chat.id, text=f"I'm going to give you a quick call just to say hi!")
    await influencer.bot_object.send_message(chat_id=message.chat.id, text=f"just make sure that do not disturb is off so my call goes through")

    # Call the user
    dispatch_intro_call(message.from_user.first_name, email, phone_number, influencer.agent_id, subscription_id, user_unique_id)

    asyncio.create_task(change_stage_response_engn(influencer.bot_username, user_id))
    asyncio.create_task(send_first_followup_msg(user_id, influencer))
    

def dispatch_intro_call(name, email, phone_number, agent_id, subscription_id, user_id):
    place_call(agent_id, phone_number, name, email, user_id, 9000, 1, subscription_id, "", is_intro = True)




# Update LOGIN_FUNCTIONS with actual functions
LOGIN_FUNCTIONS["awaiting_email"] = awaiting_email
LOGIN_FUNCTIONS["awaiting_contact"] = handle_phone_via_text
LOGIN_FUNCTIONS["awaiting_verification"] = awaiting_verification








########## Telegram bot commands ##########
async def start_command(message: types.Message, influencer : Influencer):
    return

async def help_command(message: types.Message, influencer : Influencer):
    message_text = f'''If you want me to call you, use /callme
To see your balance use /balance
To buy more credits or subscribe, use /deposit

If you're facing any issues, contact admin@tryinfluencer.ai'''

    await influencer.bot_object.send_message(chat_id=message.chat.id, text=message_text)


async def feedback_command(message: types.Message, influencer : Influencer):
    message_text = f'''Submit any feedback you have for InfluencerAI here:
https://forms.gle/ZvB4vXse3SZKfqHA6

You're feedback helps us improve your experience and add features you want to see.'''
    await influencer.bot_object.send_message(chat_id=message.chat.id, text=message_text)


async def balance_command(message: types.Message, influencer : Influencer):
    user_id = str(message.from_user.id)

    # Get the user's credits info
    unique_id = database.get_bubble_unique_id(influencer.bot_username, user_id)

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
        
    await influencer.bot_object.send_message(chat_id=message.chat.id, text=acountinfo_message, parse_mode='Markdown')


async def callme_command(message: types.Message, influencer: Influencer) -> None:
    user_id = str(message.from_user.id)

    has_phone, phone_number = database.phone_number_status(influencer.bot_username, user_id)

    user_unique_id = database.get_bubble_unique_id(influencer.bot_username, user_id)

    if(has_phone == True):
        user_first_name = message.from_user.first_name
        prospect_email = connectBubble.get_user_email(user_unique_id)
        credits_left = connectBubble.get_minutes_credits(user_unique_id)
        subscription_id = database.get_subscription_id(influencer.bot_username, user_id)
        
        # IMPLEMENT LATER: fan description left blank
        fan_description = ""

        await influencer.bot_object.send_message(chat_id= message.chat.id, text="i'm calling you, check your phone" )
        # await message.reply("i'm calling you, check your phone") 

        place_status = place_call(influencer.agent_id, phone_number, user_first_name, prospect_email, user_unique_id, credits_left, influencer.credits_per_min,
                                  subscription_id, fan_description)
        

        print("place_status: ", place_status)

        if(place_status):
            print("Placed call")
        else:
            # ERROR - add handling later
            database.add_chat_to_user_history(influencer.bot_username, user_id, 'assistant', 'Influencer: ' + "i'm having some trouble calling you right now, can you try again later?")
            await influencer.bot_object.send_message(chat_id= message.chat.id, text="i'm having some trouble calling you right now, can you try again later?")
    else:
        await influencer.bot_object.send_message(chat_id= message.chat.id, text="you need to connect your phone number in order for me to be able to call you")






# Update COMMAND_HANDLERS with actual functions
COMMAND_HANDLERS["/start"] = start_command
COMMAND_HANDLERS["/help"] = help_command
COMMAND_HANDLERS["/feedback"] = feedback_command
COMMAND_HANDLERS["/callme"] = callme_command
COMMAND_HANDLERS["/balance"] = balance_command
COMMAND_HANDLERS["/deposit"] = paymentstest.purchase
COMMAND_HANDLERS["/manage"] = paymentstest.manage_subscription
COMMAND_HANDLERS["/subscribe"] = paymentstest.subscribe








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




async def handle_user_voice_note(message: types.Message, influencer : Influencer) -> None:
    transcription = await voicenoteHandler.transcribe_user_voice_note(message, influencer.bot_object)

    await handle_response(message, transcription, influencer)



async def handle_response(message: types.Message, influencer : Influencer, voicenote_transcription=None) -> None:
    user_id = str(message.from_user.id)    
    
    # Case when user doesn't send voice - take text from Telegram's user data
    if(voicenote_transcription == None):
        text = message.text
    else:
        text = voicenote_transcription
    
    
    # Double check if user has enough credits if voice_notes_status is set to "enabled"
    # if(context.user_data['voice_notes_status'] == "enabled"):
    # Check if user has enough credits
    unique_id = database.get_bubble_unique_id(influencer.bot_username, user_id)

    
    current_minutes_credits = connectBubble.get_minutes_credits(unique_id)
    print("current_minutes_credits: ", current_minutes_credits)
    

    if(current_minutes_credits <= 0):
        # Send message to buy credits
        await influencer.bot_object.send_message(chat_id=message.chat.id, text="You are out of minutes for your account. Purchase more below in order to continue.")
        await paymentstest.purchase(message, influencer)
    else:
        await voicenoteHandler.voice_note_creator(message, text, unique_id, influencer)














async def handle_command(message: types.Message, bot : Bot):
    print("Handling commands")
    # Example: Responding to the /start command
    if message.text == '/start':
        await bot.send_message(chat_id=message.chat.id, text="Welcome to the bot!")
    elif message.text == '/help':
        await bot.send_message(chat_id=message.chat.id, text="How can I assist you?")


async def handle_message(message: types.Message, bot : Bot):
    # Echo the received text message
    await bot.send_message(chat_id=message.chat.id, text=message.text)

async def change_stage_response_engn(agent_username, user_id):
    await asyncio.sleep(15)
    database.update_state(agent_username, user_id, "in_intro_call")

async def send_first_followup_msg(user_id, influencer : Influencer):

    await asyncio.sleep(INTRO_CALL_LENGTH)
    state = database.get_state(influencer.bot_username, user_id)

    if state != "response_engine":
        await influencer.bot_object.send_message(chat_id=user_id, text= "Hey it was great talking to you!", parse_mode='Markdown')
        await influencer.bot_object.send_message(chat_id=user_id, text= "I'm always down to have some fun over chat, but I'd love to call you again if you buy some credits...", parse_mode='Markdown')
        await influencer.bot_object.send_message(chat_id=user_id, text= "Soo what are you up to now?", parse_mode='Markdown')



        database.add_chat_to_user_history(influencer.bot_username, user_id, 'assistant', 'Influencer: ' + "Soo what are you up to now?")

        database.update_state(influencer.bot_username, user_id, "response_engine")

        
    pass





app = web.Application()
app.router.add_post('/webhook/{slug}', webhook_entry)
app.router.add_get('/webhook/{slug}', webhook_entry)  # For simple GET verification

if __name__ == '__main__':
    web.run_app(app, port=5000)


# https://api.telegram.org/bot6736028246:AAGbbsnfYsBJ1y-Fo0jO4j0c9WBuLxGDFKk/setWebhook?url=https://2f3c-2607-fea8-34dd-4f90-35a6-2d3b-2dad-fef2.ngrok-free.app/webhook