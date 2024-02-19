from typing import Final
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton

from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackContext
import time
import requests
import json
import re
import stripe

from openai import OpenAI

import response_engine
import vectordb

import database
import bubbledb
import loginuser


TOKEN: Final = "6736028246:AAGbbsnfYsBJ1y-Fo0jO4j0c9WBuLxGDFKk"
BOT_USERNAME: Final = "@veronicaavluvaibot"

stripe.api_key = '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'

##### Commands #####
'''
start - starts the bot
help - provides help for Veronica AI
callme - Have Veronica AI call you
'''

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = str(update.message.from_user.id)
    influencer_id = BOT_USERNAME

    # Check if user is subscribed and add them if not
    database.add_user_to_influencer_subscription(influencer_id, user_id)

    user_first_name = update.message.from_user.first_name
    message_text = f'''Hey {user_first_name}, I'm excited to start talking to you. 
    
Please share your phone number to continue. Press the button below.'''
    
    # Custom keyboard to request contact, with an emoji to make the button more noticeable
    keyboard = [[KeyboardButton("📞 Share Phone Number", request_contact=True)]]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    
    await update.message.reply_text(message_text, reply_markup=reply_markup)


async def handle_contact(update: Update, context: CallbackContext) -> None:
    user_id = str(update.message.from_user.id)

    verification_status = database.get_verification_status(BOT_USERNAME, user_id)

    if(verification_status == True):
         await handle_response(update, context)

    phone_number = update.message.contact.phone_number

    # Store the user's phone number in Firestore
    database.store_user_phone_number(BOT_USERNAME, user_id, phone_number)
    
    database.add_chat_to_user_history(BOT_USERNAME, user_id, 'assistant', 'Influencer: ' + "Thank you for sharing your phone number.")

    await update.message.reply_text("Thank you for sharing your phone number.")

    # Send user the verification code

    # Assuming loginuser.generate_random_number() and loginuser.send_verification_code() are defined elsewhere
    verification_code = loginuser.generate_random_number()
    loginuser.send_verification_code(phone_number, verification_code)

    # Store the verification code in the context user data for later verification
    context.user_data['expected_code'] = verification_code

    database.update_verification_status(BOT_USERNAME, user_id, True)
    
    print("Sent verification code: ", verification_code)
    
    # Prompt user for the verification code
    await update.message.reply_text(f'Please enter the verification code sent to {phone_number}')
    
    # await handle_verification_response(update, context)


async def handle_phone_number_via_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = str(update.message.from_user.id)
    text = update.message.text.strip()

    # Custom keyboard to request contact, with an emoji to make the button more noticeable
    keyboard = [[KeyboardButton("📞 Share Phone Number", request_contact=True)]]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)

    retry_message = '''Please try again using the 'Share Phone Number' button below.'''
    
    await update.message.reply_text(retry_message, reply_markup=reply_markup)



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
            await update.message.reply_text("Verification successful!")
            database.update_verification_status(BOT_USERNAME, user_id, "True")
            
            has_phone, phone_number = database.phone_number_status(BOT_USERNAME, user_id)
            
            if(has_phone):
                unique_id = bubbledb.find_user(phone_number)

                if(unique_id != None):
                    database.add_bubble_unique_id(BOT_USERNAME, user_id, unique_id)
                else:
                    # Means the user didn't connect this phone number to their Bubble account
                    pass
                
                await handle_response(update, context)
                return
            else:
                print("ERROR - how the fuck did we get here")

        else:
            # Handle invalid code: ask to try again or enter a different number
            # Prompt the user to share their phone number again
            contact_keyboard = KeyboardButton(text="Share my phone number", request_contact=True)
            custom_keyboard = [[contact_keyboard]]
            reply_markup = ReplyKeyboardMarkup(custom_keyboard, one_time_keyboard=True)

            await update.message.reply_text("Verification failed. Please share your phone number again.", reply_markup=reply_markup)
    
    else:
        print("STATE ERROR - handle_verification_response")
        print("Going into response engine")
        # If there's no expected code in context, it might be an unexpected message or state
        await handle_response(update, context)




async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Hey how can I help you?")


async def callme(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    place_call()
    await update.message.reply_text("Im calling you, check your phone")


async def error(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    print(f"Update {update} caused error {context.error}")


# Maybe have "account info - give status on what's in the account" command that sends all the account info (number of credits, etc.)


def place_call(phone_number, agent_id, prospect_name, prospect_email, user_id, credits_left, credits_per_minute, subscription_id, fan_description):
    url = "https://callfusion-0c6c4ca2c8e6.herokuapp.com/dispatch_demo_call"
    headers = {"Content-Type": "application/json"}
    data = {
        "phone_number": phone_number,
        "agent_id": agent_id,
        "agent_to_use": "emma_live",
        "prospect_details": {
            "name": prospect_name,
            "email": prospect_email,
            "user_id": user_id,
            "credits_left": credits_left,
            "credits_per_minute": credits_per_minute,
            "subscription_id": subscription_id,
            "fan_description": fan_description,
        },
    }

    response = requests.post(url, headers=headers, data=json.dumps(data))
    if response.status_code == 200:
        print(response.json())  # Assuming the successful response is a JSON
        return True
    else:
        print("Error: " + response.text)
        return False


# Example usage
# status = place_call(
#     "<phone_number>", "<agent_id>", "<prospect_name>", "<prospect_email>",
#     "<user_id>", <credits_left>, <credits_per_minute>, "<subscription_id>", "<fan_description>"
# )




################################################################
####################### Chatbot Handler ##########################
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

    for message_reply in reply_array:
        await update.message.reply_text(message_reply)


################################################################
####################### Chatbot Agent ##########################
################################################################


# Main message handler that decides what to do based on the user's context
async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_data = context.user_data
    user_id = str(update.message.from_user.id)
    text = update.message.text
    
    # Check if we are awaiting a verification response
    if (database.get_verification_status(BOT_USERNAME, user_id) == True):
        # Call the verification response handler
        await handle_verification_response(update, context)
    else:
        # Handle other text messages
        await handle_response(update, context)


def main():
    # Get the dispatcher to register handlers
    dp = Application.builder().token(TOKEN).build()

    # on different commands - answer in Telegram
    dp.add_handler(CommandHandler("start", start_command))
    dp.add_handler(MessageHandler(filters.CONTACT, handle_contact))
    dp.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_verification_response))
    
    dp.add_handler(CommandHandler("help", help_command))
    dp.add_handler(CommandHandler("callme", callme))

    # Handle non-command messages
    # This is your main text message handler
    dp.add_handler(MessageHandler(filters.TEXT, message_handler))


    # Errors
    dp.add_error_handler(error)

    # Start the Bot
    print("Polling...")
    dp.run_polling(poll_interval=3)


if __name__ == "__main__":
    main()
