from typing import Final
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup

from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackContext, CallbackQueryHandler
import time
import requests
import json
import re
import asyncio

# import stripe
from openai import OpenAI

import response_engine
import vectordb

import database
import bubbledb
import connectBubble
import loginuser
import paymentstest as payments


TOKEN: Final = "6736028246:AAGbbsnfYsBJ1y-Fo0jO4j0c9WBuLxGDFKk"
BOT_USERNAME: Final = "@veronicaavluvaibot"

AGENT_ID = "veronica_avluv"


# stripe.api_key = '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'

##### Commands - need to add to bot father #####
'''
start - starts the bot
help - provides help for Veronica AI
callme - Have Veronica AI call you
payments - Purchase minutes to use VeronicaAI
'''


# Telegram bot stages stored inside context.user_data['current_stage']
'''
awaiting_email
awaiting_contact
awaiting_verification
response_engine
'''


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = str(update.message.from_user.id)
    influencer_id = BOT_USERNAME

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
        message_text = f'''Hey {user_first_name}, welcome to VeronicaAI 💕!

I was created by Veronica Avluv and trained on everything you can know about her. I'm built to act, talk and sound just like she does.

I can call you, text you, send voice notes, and send pics. 

To get started I need your phone number and email in order to make your account.
☐ Email
☐ Phone number'''
        
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
        message_text = '''Thank you for sharing your email.
☒ Email
☐ Phone number

Now, please share your phone number to continue. Press the button below.'''
        
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
        
        database.add_chat_to_user_history(BOT_USERNAME, user_id, 'assistant', 'Influencer: ' + "Thank you for sharing your phone number.")

        await update.message.reply_text("Thank you for sharing your phone number.")

        # Set stage at awaiting_verification since we're waiting for the verification code
        context.user_data['current_stage'] = "awaiting_verification"


        # Send user the verification code

        # Assuming loginuser.generate_random_number() and loginuser.send_verification_code() are defined elsewhere
        verification_code = loginuser.generate_random_number()
        loginuser.send_verification_code(phone_number, verification_code)

        # Store the verification code in the context user data for later verification
        context.user_data['expected_code'] = verification_code
        
        database.update_verification_status(BOT_USERNAME, user_id, "False")
        
        print("Sent verification code: ", verification_code)

        # Prompt user for the verification code
        await update.message.reply_text(f'Please enter the verification code sent to {phone_number}', reply_markup=ReplyKeyboardRemove())
        
        # await handle_verification_response(update, context)


async def handle_phone_number_via_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = str(update.message.from_user.id)
    text = update.message.text.strip()

    # Custom keyboard to request contact, with an emoji to make the button more noticeable
    keyboard = [[KeyboardButton("📞 Share Phone Number", request_contact=True)]]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)

    retry_message = '''Please try again using the '📞 Share Phone Number' button below.'''
    
    await update.message.reply_text(retry_message, reply_markup=reply_markup)


def get_user_unique_id(update, context):
    if 'user_unique_id' in context.user_data and context.user_data['user_unique_id']:
        return context.user_data['user_unique_id']
    else:
        user_id = str(update.message.from_user.id)

        unique_id = database.get_bubble_unique_id(BOT_USERNAME, user_id)
        
        context.user_data['user_unique_id'] = unique_id



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
            await update.message.reply_text('''Verification successful, you're ready to start using VeronicaAI!

Enter /call_me if you want me to call the phone number you have with your account

Enter /help if you run into any issues''', reply_markup=ReplyKeyboardRemove())

            # Set stage to response engine chatbot since user has entered email and phone number
            context.user_data['current_stage'] = "response_engine"

            database.update_verification_status(BOT_USERNAME, user_id, "True")
            
            has_phone, phone_number = database.phone_number_status(BOT_USERNAME, user_id)
            
            if(has_phone):
                user_unique_id = connectBubble.find_user(phone_number)
                
                # Handle no user being found - must create new user
                if(user_unique_id == False):
                    print("Creating new user in Bubble - user phone number not found")
                    email_status, email = database.user_email_status(BOT_USERNAME, user_id)
                    first_name = update.message.from_user.first_name

                    # Create user in Bubble database
                    user_unique_id = connectBubble.create_user(email, phone_number, first_name)
                    context.user_data['user_unique_id'] = user_unique_id
                    
                    # Add unique id to Bubble
                    database.add_bubble_unique_id(BOT_USERNAME, user_id, user_unique_id)

                    # Create and add subscription
                    database.add_subscription_id(BOT_USERNAME, user_id, user_unique_id)
                else:
                    print("User found ", user_unique_id)
                    context.user_data['user_unique_id'] = user_unique_id
                    
                    # Means user with this number already exists in the database.
                    # Store retrieved user_unique_id in Firebase
                    database.add_bubble_unique_id(BOT_USERNAME, user_id, user_unique_id)
                    
                    # Create and add subscription
                    database.add_subscription_id(BOT_USERNAME, user_id, user_unique_id)                

                
                await update.message.reply_text(f"hey {update.message.from_user.first_name}, it's great to meet you")

                await update.message.reply_text(f"how's your day been so far?")
                database.add_chat_to_user_history(BOT_USERNAME, user_id, 'assistant', 'Influencer: ' + f"hey {update.message.from_user.first_name}, it's great to meet you! how's your day been so far?")

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


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Hey how can I help you?")


async def callme(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = str(update.message.from_user.id)

    has_phone, phone_number = database.phone_number_status(BOT_USERNAME, user_id)
    user_first_name = update.message.from_user.first_name

    user_unique_id = database.get_bubble_unique_id(BOT_USERNAME, user_id)

    if(has_phone == True):
        place_call(phone_number, user_first_name, )
        await update.message.reply_text("i'm calling you, check your phone")
    else:
        await update.message.reply_text("you need to connect your phone number in order for me to be able to call you")


async def error(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    print(f"Update {update} caused error {context.error}")


# Maybe have "account info - give status on what's in the account" command that sends all the account info (number of credits, etc.)


def place_call(phone_number, prospect_name, prospect_email, unique_id, credits_left, credits_per_minute, subscription_id, fan_description):
    url = "https://callfusion-0c6c4ca2c8e6.herokuapp.com/dispatch_demo_call"
    headers = {"Content-Type": "application/json"}
    data = {
        "phone_number": phone_number,
        "agent_id": AGENT_ID,
        "agent_to_use": "emma_live",
        "prospect_details": {
            "name": prospect_name,
            "email": prospect_email,
            "user_id": unique_id,
            "credits_left": credits_left,
            "credits_per_minute": credits_per_minute,
            "subscription_id": subscription_id,
            "fan_description": fan_description
        },
    }

    response = requests.post(url, headers=headers, data=json.dumps(data))
    if response.status_code == 200:
        print(response.json())  # Assuming the successful response is a JSON
        return True
    else:
        print("Error: ", response.text)
        return False


# Example usage
# status = place_call(
#     "<phone_number>", "<agent_id>", "<prospect_name>", "<prospect_email>",
#     "<user_id>", <credits_left>, <credits_per_minute>, "<subscription_id>", "<fan_description>"
# )




################################################################
####################### Chatbot Handler ########################
################################################################

async def handle_response(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = str(update.message.from_user.id)
    influencer_id = BOT_USERNAME
    
    text = update.message.text

    # Add the current message to the user's chat history
    database.add_chat_to_user_history(influencer_id, user_id, "user", "Fan: " + text)

    # Retrieve the updated chat history
    chat_history = database.get_user_chat_history(influencer_id, user_id)

    # Format the chat history for display
    parsed_chat_history = response_engine.parse_chat_history(chat_history)

    # Generate a response based on the user's message history (modify this function as needed)
    ai_response = response_engine.create_response(parsed_chat_history, text, update)
    database.add_chat_to_user_history(influencer_id, user_id, 'assistant', 'Influencer: ' + ai_response)

    # Send the chat history along with the AI response
    # chat_history_str = '\n'.join(f"{chat['content']}" for chat in chat_history)
    # print(f"Current Chat History: \n {chat_history_str}")

    reply_array = response_engine.split_messages(ai_response)
    reply_array = response_engine.remove_questions(reply_array)

    for message_reply in reply_array:
        print("message_reply: ", message_reply)
        await update.message.reply_text(message_reply)
        # asyncio.sleep(1)


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
        else:
            print("Going into response engine - no stage identified")
            user_data["current_stage"] = "response_engine"
            await handle_response(update, context)


def main():
    # Get the dispatcher to register handlers
    dp = Application.builder().token(TOKEN).build()

    # on different commands - answer in Telegram
    dp.add_handler(CommandHandler("start", start_command))
    
    # dp.add_handler(MessageHandler(filters.TEXT, handle_email))
    dp.add_handler(MessageHandler(filters.CONTACT, handle_contact))

    # Handle non-command messages
    # This is your main text message handler
    dp.add_handler(MessageHandler(filters.TEXT, message_handler))

    # dp.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_verification_response))
    
    dp.add_handler(CommandHandler("help", help_command))
    dp.add_handler(CommandHandler("callme", callme))
    dp.add_handler(CommandHandler("payments", payments.purchase))
    dp.add_handler(CallbackQueryHandler(payments.button))


    # Errors
    dp.add_error_handler(error)

    # Start the Bot
    print("Polling...")
    dp.run_polling(poll_interval=3)


if __name__ == "__main__":
    main()
