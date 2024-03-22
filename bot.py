from typing import Final
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup, Bot, BotCommand, BotCommandScopeChat

from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackContext, CallbackQueryHandler
import time
import requests
import json
import re
import asyncio

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

# TOKEN: Final = "6736028246:AAGbbsnfYsBJ1y-Fo0jO4j0c9WBuLxGDFKk"
# BOT_USERNAME: Final = "@veronicaavluvaibot"

# AI_NAME = "VeronicaAI"

# AGENT_ID = "veronica_avluv"

bot = Bot(TOKEN)


##### Commands - need to add to bot father #####
'''
callme - Have VeronicaAI call your phone number
deposit - Add credits to your account or subscribe
balance - Display your credits balance
feedback - Provide feedback to improve the bot
help - Display help message
'''

def get_global_commands():
    return[
        # BotCommand("start", "start the bot"),
        BotCommand("callme", f"Have {AI_NAME} call your phone number"),
        BotCommand("deposit", "Add credits to your account or subscribe"),
        BotCommand("balance", "Display your credits balance"),
        BotCommand("feedback", "Provide feedback to improve the bot"),
        # BotCommand("changename", f"Change the name that {AI_NAME} calls you"),
        # BotCommand("changenumber", "Change the phone number for your account"),
        # BotCommand("accountinfo", "Display the information about your account"),

        BotCommand("help", "Display help message")
    ]



# Telegram bot stages stored inside context.user_data['current_stage']
'''
awaiting_email
awaiting_contact
awaiting_verification
pending_intro
response_engine

changenumber
changename
'''


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = str(update.message.from_user.id)
    influencer_id = BOT_USERNAME

    context.user_data['voice_notes_status'] = "enabled"

    start_args = context.args  # context.args contains the parameters passed after /start

    ############### Check if user already exists ###############
    user_exists_status = database.check_user_exists(BOT_USERNAME, user_id)
    if(user_exists_status == True):
        # Call message handler to go the appopriate stage
        await message_handler(update, context)
    else:
        # Check if user is subscribed and add them if not
        database.add_user_to_influencer_subscription(influencer_id, user_id)

        # set stage to awaiting_email
        context.user_data['current_stage'] = "awaiting_email"

        user_first_name = update.message.from_user.first_name
        

        # Send user an intro image
        image_url = "https://static.wixstatic.com/media/e1234e_36641e0f2be447bea722377cd31945d3~mv2.jpg/v1/crop/x_254,y_168,w_972,h_937/fill/w_506,h_488,al_c,q_80,usm_0.66_1.00_0.01,enc_auto/IMG_20231215_134002.jpg"
        await send_image(update, context, image_url)

        message_text = f'''Hey {user_first_name}, welcome to {AI_NAME} 💕!

I was created by Veronica Avluv and trained on everything you can know about her. I'm built to act, talk and sound just like she does.

I can call you, text you, send voice notes, and send pics. I can also get real naughty, especially when you call me ;)

To get started I need your phone number and email in order to make your account.
☐ Email
☐ Phone number

By sharing your email and phone number, you agree to our Terms of Service (https://veronica.tryinfluencerai.com/terms-and-conditions) and have read and acknowledged the Privacy Policy (https://veronica.tryinfluencerai.com/privacy)
'''
        
        # # Custom keyboard to request contact, with an emoji to make the button more noticeable
        # keyboard = [[KeyboardButton("📞 Share Phone Number", request_contact=True)]]
        # reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
        
        # await update.message.reply_text(message_text, reply_markup=reply_markup)

        await update.message.reply_text(message_text)
        await update.message.reply_text("Enter your email below:")


# Function to handle email response
async def handle_email(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_email = update.message.text  # Assuming the next message after start is the email
    user_id = str(update.message.from_user.id)

    # Validate the email format here (basic example)
    if re.match(r"[^@]+@[^@]+\.(?!con$)[^@]+", user_email):
        context.user_data['email'] = user_email  # Store the email in context.user_data for later use
        context.user_data['awaiting_phone_number'] = True  # Indicate that the next step is to collect the phone number

        # Store user email in database
        database.store_user_email(BOT_USERNAME, user_id, user_email)
        
        # After email is received and validated, ask for the phone number
        message_text = '''Thank you for sharing your email honey.
☒ Email
☐ Phone number

Now, could I please get your phone number? Just press the button below for me okay?

By sharing your email and phone number, you agree to our Terms of Service (https://veronica.tryinfluencerai.com/terms-and-conditions) and have read and acknowledged the Privacy Policy (https://veronica.tryinfluencerai.com/privacy)
'''
        
        # # Custom keyboard to request contact
        keyboard = [[KeyboardButton("📞 Share Phone Number", request_contact=True)]]
        reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)

        # Set stage at awaiting_contact since we need the user's contact for the phone number
        context.user_data['current_stage'] = "awaiting_contact"

        await update.message.reply_text(message_text, reply_markup=reply_markup)
    else:
        # Keep the stage at awaiting_email
        context.user_data['current_stage'] = "awaiting_email"
        
        # Handle invalid email format
        await update.message.reply_text("It seems like the email you entered is invalid.")
        await update.message.reply_text("Please enter your email again below:")



async def handle_contact(update: Update, context: CallbackContext) -> None:
    user_id = str(update.message.from_user.id)

    print("Finding verfication status")
    verification_status = database.get_verification_status(BOT_USERNAME, user_id)
    print("verification_status:", verification_status)

    if(verification_status == True):
        return
        #  await handle_response(update, context)
    else:
        phone_number = update.message.contact.phone_number

        # Store the user's phone number in Firestore
        database.store_user_phone_number(BOT_USERNAME, user_id, phone_number)
        
        database.add_chat_to_user_history(BOT_USERNAME, user_id, 'assistant', 'Influencer: ' + "Thank you for sharing your phone number, darling.")

        await update.message.reply_text("Thank you for sharing your phone number, can you make sure you're accepting calls from unknown numbers so I can give you a ring?")

        # Set stage at awaiting_verification since we're waiting for the verification code
        context.user_data['current_stage'] = "awaiting_verification"

        await verify_number(update, context, phone_number)



async def verify_number(update: Update, context: ContextTypes.DEFAULT_TYPE, phone_number: str) -> None:
       
    user_id = str(update.message.from_user.id)

    print("Finding verfication status")
    verification_status = database.get_verification_status(BOT_USERNAME, user_id)
    print("verification_status:", verification_status)

    if(verification_status == True):
        return
    
    # Send user the verification code

    # Assuming loginuser.generate_random_number() and loginuser.send_verification_code() are defined elsewhere
    verification_code = loginuser.generate_random_number()
    loginuser.send_verification_code(phone_number, verification_code)

    # Store the verification code in the context user data for later verification
    context.user_data['expected_code'] = verification_code
    
    database.update_verification_status(BOT_USERNAME, user_id, "False")
    
    print("Sent verification code: ", verification_code)

    # Prompt user for the verification code
    await update.message.reply_text(f'Also could you please just enter the verification code to {phone_number} for me?', reply_markup=ReplyKeyboardRemove())
    
    # await handle_verification_response(update, context)


#### Helper functions ####
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



# Current Issue/Bug to fix
    # Enter number via text (not sharing contact)
    # Enter code
    # Try reentering number via text (not sharing contact)
        # Can only share by contact now


async def handle_phone_number_via_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = str(update.message.from_user.id)
    user_data = context.user_data
    text = update.message.text.strip()

    # Custom keyboard to request contact, with an emoji to make the button more noticeable
    keyboard = [[KeyboardButton("📞 Share Phone Number", request_contact=True)]]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)

    retry_message = '''Please try again using the '📞 Share Phone Number' button below.'''
    
    await update.message.reply_text(retry_message, reply_markup=reply_markup)

    stored_phone_number_status, phone_number = database.phone_number_status(BOT_USERNAME, user_id)
    print(stored_phone_number_status)
    
    if (stored_phone_number_status == False):
        # Use the verification and formatting function
        is_valid, formatted_number_or_message = gpt_verify_and_format_number(text)

        if is_valid:
            # Store the formatted phone number in Firestore
            database.store_user_phone_number(BOT_USERNAME, user_id, formatted_number_or_message)

            # Inform the user
            database.add_chat_to_user_history(BOT_USERNAME, user_id, 'assistant', 'Influencer: ' + "Thank you for sharing your phone number.")

            await update.message.reply_text("Thank you for sharing your phone number, can you make sure you're accepting calls from unknown numbers so I can give you a ring?")

            user_data["current_stage"] == "awaiting_verification"
            await verify_number(update, context, formatted_number_or_message)

        else:
            # Custom keyboard to request contact, with an emoji to make the button more noticeable
            keyboard = [[KeyboardButton("📞 Share Phone Number", request_contact=True)]]
            reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)

            # Ask the user to try again or use the button
            retry_message = "The entered number seems invalid."
            if formatted_number_or_message == "missing area code":
                retry_message += " It seems like the country code is missing."
            
            retry_message += '''

Please try again using the '📞 Share Phone Number' button below.'''
            
            await update.message.reply_text(retry_message, reply_markup=reply_markup)
    else:
        if(database.get_verification_status(BOT_USERNAME, user_id) == "True"):
            await handle_response(update, context)
        else:
            user_data["current_stage"] == "awaiting_contact"

            keyboard = [[KeyboardButton("📞 Share Phone Number", request_contact=True)]]
            reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)

            retry_message = '''Please share your number again using the '📞 Share Phone Number' button below.'''
            
            await update.message.reply_text(retry_message, reply_markup=reply_markup)

            # user_data["current_stage"] == "awaiting_verification"
            # await verify_number(update, context, phone_number)



def get_user_unique_id(update, context):
    if 'user_unique_id' in context.user_data and context.user_data['user_unique_id']:
        return context.user_data['user_unique_id']
    else:
        user_id = str(update.message.from_user.id)

        unique_id = database.get_bubble_unique_id(BOT_USERNAME, user_id)
        
        context.user_data['user_unique_id'] = unique_id
        return unique_id


async def handle_verification_response(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    print("handle_verification_response invoked")
    user_id = str(update.message.from_user.id)
    
    verification_status = database.get_verification_status(BOT_USERNAME, user_id)
    print(verification_status)
    if(verification_status == True):
         await handle_response(update, context)
         return
    
    text = update.message.text  # This should be the verification code the user recieved

    print()
    print()
    print("USER ENTERED: ")
    print(text)
    print()

    # Retrieve the expected code from the context user data
    expected_code = context.user_data.get('expected_code')

    print("EXPECTED CODE ", expected_code)

    if text and expected_code:
        if str(text) == str(expected_code):
            await update.message.reply_text('''Verification successful''', reply_markup=ReplyKeyboardRemove())

            # Set stage to response engine chatbot since user has entered email and phone number
            context.user_data['current_stage'] = "pending_intro"

            # Send user an welcome image
            image_url = "https://static.wixstatic.com/media/e1234e_36641e0f2be447bea722377cd31945d3~mv2.jpg/v1/crop/x_254,y_168,w_972,h_937/fill/w_506,h_488,al_c,q_80,usm_0.66_1.00_0.01,enc_auto/IMG_20231215_134002.jpg"
            await send_image(update, context, image_url)

            await update.message.reply_text(f"""You're all set to start using {AI_NAME}!

I can send you voice notes, text you picutres, and even be able to call you.

To start a call enter /callme and I'll call the phone number you have with your account. Remember, I can get extra dirty on call ;) (come and find out yourself).

You have 5 free credits. 
To buy more credits or subscribe just enter /deposit

Enter /help if you run into any issues.""")

            database.update_verification_status(BOT_USERNAME, user_id, "True")
            
            has_phone, phone_number = database.phone_number_status(BOT_USERNAME, user_id)
            
            if(has_phone):
                print("phone_number: ", phone_number)
                user_unique_id = connectBubble.find_user(phone_number)
                email_status, email = database.user_email_status(BOT_USERNAME, user_id)
                # Handle no user being found - must create new user
                if(user_unique_id == False):
                    print("Creating new user in Bubble - user phone number not found")
                    
                    first_name = update.message.from_user.first_name

                    # Create user in Bubble database
                    user_unique_id = connectBubble.create_user(email, phone_number, first_name)
                else:
                    print("User found ", user_unique_id)
                context.user_data['user_unique_id'] = user_unique_id
                
                # Means user with this number already exists in the database.
                # Store retrieved user_unique_id in Firebase
                database.add_bubble_unique_id(BOT_USERNAME, user_id, user_unique_id)
                
                # Create and add subscription
                subscription_id = database.add_subscription_id(BOT_USERNAME, user_id, user_unique_id)                

                await update.message.reply_text(f"hey {update.message.from_user.first_name}, it's great to meet you")
                await update.message.reply_text(f"I'm going to give you a quick call just to say hi!")
                await update.message.reply_text(f"just make sure that do not disturb is off so my call goes through")
                
                database.add_chat_to_user_history(BOT_USERNAME, user_id, 'assistant', 'Influencer: ' + f"hey {update.message.from_user.first_name}, it's great to meet you! how's your day been so far?")
                context.user_data["intro_status"] = "pending"
                dispatch_intro_call(update.message.from_user.first_name, email, phone_number, AGENT_ID, subscription_id, user_unique_id)
                asyncio.create_task(change_stage_response_engn(context))
                asyncio.create_task(send_first_followup_msg(context, BOT_USERNAME, user_id))
                
                # await handle_response(update, context)
                return
            else:
                print("ERROR - how the fuck did we get here. user got here without having a phone number in db.")

        else:
            # Handle invalid code: ask to try again or enter a different number
            # Prompt the user to share their phone number again
            contact_keyboard = KeyboardButton(text="📞 Share Phone Number", request_contact=True)
            custom_keyboard = [[contact_keyboard]]
            reply_markup = ReplyKeyboardMarkup(custom_keyboard, one_time_keyboard=True)
            
            context.user_data['awaiting_phone_number'] = True

            # Set stage at awaiting_contact since we need to go back to the getting the user's contact stage
            context.user_data['current_stage'] = "awaiting_contact"

            await update.message.reply_text("Verification failed. Please share your phone number again.", reply_markup=reply_markup)
    
    else:
        print("STATE ERROR - handle_verification_response")
        # print("Going into response engine")
        # # If there's no expected code in context, it might be an unexpected message or state
        context.user_data['current_stage'] = "response_engine"
        await handle_response(update, context)


# Commands

async def balance_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = str(update.message.from_user.id)

    # Get the user's credits info
    unique_id = get_user_unique_id(update, context)
    print(unique_id)
    num_credits = connectBubble.get_minutes_credits(unique_id)
    num_credits = str(round(num_credits, 2))
    

    # Get user's phone number
    status, phone_number = database.phone_number_status(BOT_USERNAME, user_id)

    if(context.user_data is None or ('current_stage' not in context.user_data)):
        pass
        print("ERROR: RUN CHECK CURRENT STAGE FUNCTION")

        if(unique_id != False or unique_id != 'False'):
            acountinfo_message = f'''You have *{num_credits} InfluencerAI credits* available

To add credits to your account or subscribe, use /deposit'''
    elif(context.user_data['current_stage'] != 'response_engine' and status == False):
        acountinfo_message = f'''You don't have a phone number connected to your account yet. Please finsh signing up in order to access your account info.'''
    else:
        acountinfo_message = f'''You have *{num_credits} InfluencerAI credits* available

To add credits to your account or subscribe, use /deposit'''

    await context.bot.send_message(chat_id=user_id, text=acountinfo_message, parse_mode='Markdown')



# async def accountinfo_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
#     user_id = str(update.message.from_user.id)
#     unique_id = get_user_unique_id(update, context)

#     first_name = connectBubble.get_user_first_name(unique_id)

#     # Get user's email info
#     email = connectBubble.get_user_email(unique_id)

#     # Get user's phone number
#     status, phone_number = database.phone_number_status(BOT_USERNAME, user_id)

#     if(status == False):
#         acountinfo_message = f'''You don't have a phone number connected to your account yet. Please finsh signing up in order to see your account info.'''
#     else:
#         acountinfo_message = f'''First Name: {first_name}
# Email: {email}
# Phone Number: {phone_number}

# To change your account's email, use /changenumber
# To change your account's first name, use /changename'''

#     await context.bot.send_message(chat_id=user_id, text=acountinfo_message, parse_mode='Markdown')

async def change_stage_response_engn(context: ContextTypes.DEFAULT_TYPE):
    await asyncio.sleep(15)
    context.user_data["current_stage"] = "response_engine"


async def send_first_followup_msg( context: ContextTypes.DEFAULT_TYPE, influencer_id, user_id):

    await asyncio.sleep(INTRO_CALL_LENGTH)
    intro_status = context.user_data.get("intro_status", "")
    print("INTRO STATUS")
    print(intro_status)
    if intro_status == "pending":
        await context.bot.send_message(chat_id=user_id, text= "Hey it was great talking to you!", parse_mode='Markdown')
        await context.bot.send_message(chat_id=user_id, text= "I'm always down to have some fun over chat, but I'd love to call you again if you buy some credits...", parse_mode='Markdown')
        await context.bot.send_message(chat_id=user_id, text= "Soo what are you up to now?", parse_mode='Markdown')



        database.add_chat_to_user_history(BOT_USERNAME, user_id, 'assistant', 'Influencer: ' + "Soo what are you up to now?")

        
    pass

async def feedback_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(f'''Submit any feedback you have for InfluencerAI here:
https://forms.gle/ZvB4vXse3SZKfqHA6

You're feedback helps us improve your experience and add features you want to see.''')


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
#     await update.message.reply_text(f'''You can edit any of your account info using the follwowing commands:
# Change the name that {AI_NAME} calls you -  /changename
# Change your account's phone number -  /changephone
                                    
# If you're facing any other issues, contact admin@tryinfluencer.ai''')
    
    await update.message.reply_text(f'''If you want me to call you, use /callme
To see your balance use /balance
To buy more credits or subscribe, use /deposit

If you're facing any issues, contact admin@tryinfluencer.ai''')



# async def update_voice_notes_commands(user_id, voice_notes_status):
#     global_commands = get_global_commands()
#     if voice_notes_status == 'enabled':
#         scoped_commands = [BotCommand("disable_voicenotes", "Disable voice notes")] + global_commands
#     else:
#         scoped_commands = [BotCommand("enable_voicenotes", "Enable voice notes")] + global_commands

#     scope = BotCommandScopeChat(chat_id=user_id)
#     await bot.setMyCommands(commands=scoped_commands, scope=scope)


# async def enable_voice_notes_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
#     user_id = str(update.message.from_user.id)

#     context.user_data['voice_notes_status'] = "enabled"
#     await update_voice_notes_commands(user_id, 'enabled')
#     await update.message.reply_text("Voice notes enabled")


# async def disable_voice_notes_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
#     user_id = str(update.message.from_user.id)

#     context.user_data['voice_notes_status'] = "disabled"
#     await update_voice_notes_commands(user_id, 'disabled')
#     await update.message.reply_text("Voice notes disabled")


async def callme_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = str(update.message.from_user.id)

    has_phone, phone_number = database.phone_number_status(BOT_USERNAME, user_id)

    user_unique_id = get_user_unique_id(update, context)

    if(has_phone == True):
        user_first_name = update.message.from_user.first_name
        prospect_email = connectBubble.get_user_email(user_unique_id)
        credits_left = connectBubble.get_minutes_credits(user_unique_id)
        subscription_id = database.get_subscription_id(BOT_USERNAME, user_id)
        
        # IMPLEMENT LATER: fan description left blank
        fan_description = ""

        await update.message.reply_text("i'm calling you, check your phone") 

        place_status = place_call(AGENT_ID, phone_number, user_first_name, prospect_email, user_unique_id, credits_left, CREDITS_PER_MINUTE,
                                  subscription_id, fan_description)

        print("place_status: ", place_status)

        if(place_status):
            print("Placed call")
        else:
            # ERROR - add handling later
            database.add_chat_to_user_history(BOT_USERNAME, user_id, 'assistant', 'Influencer: ' + "i'm having some trouble calling you right now, can you try again later?")
            await update.message.reply_text("i'm having some trouble calling you right now, can you try again later?")
    else:
        await update.message.reply_text("you need to connect your phone number in order for me to be able to call you")


async def error(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    print(f"Update {update} caused error {context.error}")



async def send_image(update: Update, context: ContextTypes.DEFAULT_TYPE, image_url) -> None:
    chat_id = update.message.chat_id  # Get the chat ID to know where to send the image
    
    # Sending an image by a URL
    await context.bot.send_photo(chat_id=chat_id, photo=image_url)

    # If you have a local image file you want to send, you can use file open
    # with open('path/to/your/image.jpg', 'rb') as file:
    #     await context.bot.send_photo(chat_id=chat_id, photo=file)


async def send_daily_image(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:    
    today_date = time.time()
    
    # Sending an image by a URL
    image_url = imagesdb.get_image(today_date)
    send_image(update, context, image_url)

    # If you have a local image file you want to send, you can use file open
    # with open('path/to/your/image.jpg', 'rb') as file:
    #     await context.bot.send_photo(chat_id=chat_id, photo=file)


def changenumber(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return

async def changenumber_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    pass


def changename(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return

async def changename_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    pass


# Maybe have "account info - give status on what's in the account" command that sends all the account info (number of credits, etc.)


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


# Example usage
# status = place_call(
#     "<phone_number>", "<agent_id>", "<prospect_name>", "<prospect_email>",
#     "<user_id>", <credits_left>, <credits_per_minute>, "<subscription_id>", "<fan_description>"
# )




################################################################
####################### Chatbot Handler ########################
################################################################

async def handle_user_voice_note(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    transcription = await voicenoteHandler.transcribe_user_voice_note(update, context)

    await handle_response(update, context, transcription)


async def handle_response(update: Update, context: ContextTypes.DEFAULT_TYPE, voicenote_transcription=None) -> None:
    user_id = str(update.message.from_user.id)
    influencer_id = BOT_USERNAME
    context.user_data["intro_status"] = "completed"
    
    
    # Case when user doesn't send voice - take text from Telegram's user data
    if(voicenote_transcription == None):
        text = update.message.text
    else:
        text = voicenote_transcription


    # Initialize stage as enabled if voice_notes_status is not inside user data
    if('voice_notes_status' not in context.user_data):
        context.user_data['voice_notes_status'] = "enabled"

    
    # Double check if user has enough credits if voice_notes_status is set to "enabled"
    # if(context.user_data['voice_notes_status'] == "enabled"):
    # Check if user has enough credits
    unique_id = get_user_unique_id(update, context)#database.get_bubble_unique_id(BOT_USERNAME, user_id)

    current_minutes_credits = connectBubble.get_minutes_credits(unique_id)
    print("current_minutes_credits: ", current_minutes_credits)

    if(current_minutes_credits <= 0):
        # Send message to buy credits
        await update.message.reply_text('''You are out of minutes for your account. Purchase more below in order to continue.''')
        await paymentstest.purchase(update, context)
    else:
        await voicenoteHandler.voice_note_creator(update, context, text)

    
    # context.user_data['voice_notes_status'] = "disabled"


    
    # # Check whether to use voice notes or chatbot
    # if(context.user_data['voice_notes_status'] == "disabled"):

    #     # Add the current message to the user's chat history
    #     database.add_chat_to_user_history(influencer_id, user_id, "user", "Fan: " + text)

    #     # Retrieve the updated chat history
    #     chat_history = database.get_user_chat_history(influencer_id, user_id)

    #     # Format the chat history for display
    #     parsed_chat_history = response_engine.parse_chat_history(chat_history)

    #     # Generate a response based on the user's message history (modify this function as needed)
    #     ai_response = response_engine.chatbot_create_response(parsed_chat_history, text, update)
    #     database.add_chat_to_user_history(influencer_id, user_id, 'assistant', 'Influencer: ' + ai_response)
        
    #     # Send the chat history along with the AI response
    #     # chat_history_str = '\n'.join(f"{chat['content']}" for chat in chat_history)
    #     # print(f"Current Chat History: \n {chat_history_str}")

    #     reply_array = response_engine.split_messages(ai_response)
    #     reply_array = response_engine.remove_questions(reply_array)

    #     for message_reply in reply_array:
    #         print("message_reply: ", message_reply)
    #         await update.message.reply_text(message_reply)
    #         # asyncio.sleep(1)
        
    # else:
    #     # Call voice notes handler
    #     await voicenoteHandler.voice_note_creator(update, context, text)



'''
awaiting_email
awaiting_contact
awaiting_verification
response_engine
'''



# Main message handler that decides what to do based on the user's context
async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    print("Called message handler")
    user_data = context.user_data
    user_id = str(update.message.from_user.id)
    text = update.message.text
    
    
    # Check if user_data exists - if false it's likely due to the code being refreshed
    if(user_data is None or ('current_stage' not in context.user_data)):
        print("No user data")

        verification_status = database.get_verification_status(BOT_USERNAME, user_id)
        

        ########### Define current stage ###########
        
        if(verification_status == True):
            # Go into chatbot response engine if phone number is already verified
            print("Going into response engine - number is verified")
            context.user_data['current_stage'] = "response_engine"
            await handle_response(update, context)
        else:
            phone_status, phone_number = database.phone_number_status(BOT_USERNAME, user_id)

            # If number has been stored but then we need to verify it since verification_stauts is False
            if(phone_status == True):
                user_data["current_stage"] = "awaiting_verification"
                await handle_verification_response(update, context)
            else:
                user_email_status, user_email = database.user_email_status(BOT_USERNAME, user_id)
                
                if(user_email_status == False):
                    user_data["current_stage"] = "awaiting_email"
                    await handle_email(update, context)
                else:
                    user_data["current_stage"] = "awaiting_contact"
                    if(update.message.contact == None):
                        await handle_phone_number_via_text(update, context)
                    
                    # This will probably not run since message_handler only runs for text based inputs (not contact shares)
                    else:
                        # Since handle_contact is already set up to handle phone number sharing,
                        # we directly call handle_contact when a phone number is expected.
                        # This requires the next message to be a contact share, not a text.
                        await handle_contact(update, context)

    # If user data exists
    else:
        print("Current Stage: ", user_data["current_stage"])

        if(user_data["current_stage"] == "awaiting_email"):
            await handle_email(update, context)
        elif(user_data["current_stage"] == "awaiting_contact"):
            if(update.message.contact == None):
                await handle_phone_number_via_text(update, context)
            else:
                # Since handle_contact is already set up to handle phone number sharing,
                # we directly call handle_contact when a phone number is expected.
                # This requires the next message to be a contact share, not a text.
                await handle_contact(update, context)
        elif(user_data["current_stage"] == "awaiting_verification"):
            await handle_verification_response(update, context)
        
        elif(user_data["current_stage"] == "changenumber"):
            # Call change number function
            pass
        elif(user_data["current_stage"] == "changename"):
            # Call change number function
            pass
        elif(user_data["current_stage"] == "pending_intro"):
            pass
        else:
            print("Going into response engine - no stage identified")

            user_data["current_stage"] = "response_engine"
            await handle_response(update, context)

def dispatch_intro_call(name, email, phone_number, agent_id, subscription_id, user_id):
    place_call(agent_id, phone_number, name, email, user_id, 9000, 1, subscription_id, "", is_intro = True)




def main():
    # Get the dispatcher to register handlers
    dp = Application.builder().token(TOKEN).build()

    # on different commands - answer in Telegram
    dp.add_handler(CommandHandler("start", start_command))
    
    # dp.add_handler(MessageHandler(filters.TEXT, handle_email))
    dp.add_handler(MessageHandler(filters.CONTACT, handle_contact))
        
    dp.add_handler(MessageHandler(filters.VOICE, handle_user_voice_note))

    dp.add_handler(CommandHandler("help", help_command))
    dp.add_handler(CommandHandler("help", feedback_command))
    dp.add_handler(CommandHandler("callme", callme_command))
    dp.add_handler(CommandHandler("balance", balance_command))

    # dp.add_handler(CommandHandler("accountinfo", accountinfo_command))
    # dp.add_handler(CommandHandler("changenumber", changenumber_command))
    # dp.add_handler(CommandHandler("changename", changename_command))

    # dp.add_handler(CommandHandler("disable_voicenotes", disable_voice_notes_command))
    # dp.add_handler(CommandHandler("enable_voicenotes", enable_voice_notes_command))
    
    dp.add_handler(CommandHandler("deposit", paymentstest.purchase))
    dp.add_handler(CallbackQueryHandler(paymentstest.button))

    # Handle non-command messages
    # This is your main text message handler
    dp.add_handler(MessageHandler(filters.TEXT, message_handler))

    # Errors
    dp.add_error_handler(error)

    # Start the Bot
    print("Polling...")
    dp.run_polling(poll_interval=3)


# dispatch_intro_call("Michael", "michaell.liao44452@gmail.com", "+16475148397", "veronica_avluv", "1705360220475x278663031583932400", "1705027196160x594032453186675500")

if __name__ == "__main__":
    main()

