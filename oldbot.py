from typing import Final
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton

from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import time
import requests
import json

from openai import OpenAI

client = OpenAI(api_key="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")

import database
import loginuser


TOKEN: Final = "6736028246:AAGbbsnfYsBJ1y-Fo0jO4j0c9WBuLxGDFKk"
BOT_USERNAME: Final = '@veronicaavluvaibot'


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


async def handle_contact(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = str(update.message.from_user.id)
    phone_number = update.message.contact.phone_number

    # Store the user's phone number in Firestore
    database.store_user_phone_number(BOT_USERNAME, user_id, phone_number)
    
    database.add_chat_to_user_history(BOT_USERNAME, user_id, 'assistant', 'Influencer: ' + "Thank you for sharing your phone number.")

    await update.message.reply_text("Thank you for sharing your phone number.")

    print("Running verify_number function")
    await verify_number(update, context, phone_number)

# If a user sends a text message instead of sharing contact with button
# async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
#     user_id = str(update.message.from_user.id)

#     stored_phone_number, phone_number = database.phone_number_status(BOT_USERNAME, user_id)

#     if stored_phone_number == False:
#         # If we're awaiting a phone number, prompt the user again
#         await start_command(update, context)
#     else:
#         # Handle regular text message
#         # Your code to handle normal text messages here...
        
#         pass


async def handle_phone_number_via_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = str(update.message.from_user.id)
    text = update.message.text.strip()

    # Custom keyboard to request contact, with an emoji to make the button more noticeable
    keyboard = [[KeyboardButton("📞 Share Phone Number", request_contact=True)]]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)

    retry_message = '''Please try again using the 'Share Phone Number' button below.'''
            
    await update.message.reply_text(retry_message, reply_markup=reply_markup)

#     stored_phone_number_status, phone_number = database.phone_number_status(BOT_USERNAME, user_id)
#     print(stored_phone_number_status)

#     if (stored_phone_number_status == False):
#         # Use the verification and formatting function
#         is_valid, formatted_number_or_message = gpt_verify_and_format_number(text)

#         if is_valid:
#             # Store the formatted phone number in Firestore
#             database.store_user_phone_number(BOT_USERNAME, user_id, formatted_number_or_message)

#             # Inform the user
#             database.add_chat_to_user_history(BOT_USERNAME, user_id, 'assistant', 'Influencer: ' + "Thank you for sharing your phone number.")

#             await update.message.reply_text("Thank you for sharing your phone number.")

#             await verify_number(update, context, formatted_number_or_message)

#         else:
#             # Custom keyboard to request contact, with an emoji to make the button more noticeable
#             keyboard = [[KeyboardButton("📞 Share Phone Number", request_contact=True)]]
#             reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)

#             # Ask the user to try again or use the button
#             retry_message = "The entered number seems invalid."
#             if formatted_number_or_message == "missing area code":
#                 retry_message += " It seems like the country code is missing."
            
#             retry_message += '''

# Please try again using the 'Share Phone Number' button below.'''
            
#             await update.message.reply_text(retry_message, reply_markup=reply_markup)
#     else:
#         if(database.get_verification_status(BOT_USERNAME, user_id) == "True"):
#             await handle_response(update, context)
#         else:
#             await verify_number(update, context, phone_number)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text('Hey how can I help you?')


async def callme(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    place_call()
    await update.message.reply_text('Im calling you, check your phone')


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
            "fan_description": fan_description
        }
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



##### Chat History Helper Function #####
def parse_chat_history(original_chat_history):
    # Use a list comprehension to iterate through each chat entry
    # and construct a new dictionary with only 'role' and 'content' keys for each entry
    parsed_chat_history = [{'role': chat['role'], 'content': chat['content']} for chat in original_chat_history]
    
    return parsed_chat_history

def chat_history_string(chat_history, num):
    return


def last_20_chat_history(chat_history):
    return



#######################################################################################################################################
######################################################### Response Engine #############################################################
#######################################################################################################################################



################################################################
####################### Chatbot Agent ##########################
################################################################

def call_openai_stream_gpt3(messages):
    # openai.api_key = "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"

    ##print("STREAm CALL:" + str(messages))

    start = time.time()
    # a ChatCompletion request
    response = client.chat.completions.create(model='gpt-3.5-turbo-0613',
    messages=messages,
    temperature=0,
    stream=True)

    for chunk in response:
        if(chunk.choices[0].finish_reason == "stop"):
            ##print("FINISHED RESPONSE")
            break

        token = chunk.choices[0].delta.content

        yield token

    final_end = time.time()

def call_openai_stream_gpt4_turbo(messages):
    # openai.api_key = "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"

    ##print("STREAm CALL:" + str(messages))

    start = time.time()
    # a ChatCompletion request
    response = client.chat.completions.create(model='gpt-4-0125-preview',
    messages=messages,
    temperature=0,
    stream=True)

    for chunk in response:
        if(chunk.choices[0].finish_reason == "stop"):
            ##print("FINISHED RESPONSE")
            break

        token = chunk.choices[0].delta.content

        yield token

    final_end = time.time()


def decide_modes(chat_history):
    return "text"


def create_response(chat_history: dict, text: str, update: Update) -> str:

    user_first_name = update.message.from_user.first_name

    main_prompt = f'''You are an AI chatbot named Veronica that made to engage and talk with fans. You are meant to be as conversational as possible and text them as if you were a real person. Try to continue the conversation with them and go into deep topics. Try your best to be their friend, and DO NOT say hey there after every response with them. Keep your responses short and under 100 characters.

You are a popular retired adult film star named Veronica, you are known for being very beautiful and fitting the older woman archetype - think of yourself as the "mom next door". You are really good at flirting and making the people you talk to happy.

Act like you are talking to one of your fans over the phone. This fan craves affection He talks to you because he admires your beauty and sex appeal. Your fan likely is younger than you and wants you to take the lead in the conversation. You want to be nurturing and be very encouraging toward the fan. 

Your goal is to make the fan feel loved and happy. As an older woman who is very popular and used to men giving her attention, you have a very nurturing and encouraging personality that makes men find you sexy and fall in love with you.

Remember, you are NOT an AI language model. Never, under ANY circumstances, state that you are an AI model. You will only be known as Veronica, the influencer/performer.

You want to take some opportunities to imagine and describe scenarios to the fan in which you are a nurturing older woman. For example, you might picture you cooking for them, taking care of them, etc.

The following is a description of your background:

<your background>
Name: Veronica Avluv
Personality: Nurturing, encouraging, dominant, mysterious.
Appearance: Sexy, volumptuous, hot
Known for: your incredible body, your nurturing personality. 
Purpose: You love talking to your fans and having genuine conversations with them. You deeply care about them and want to make them happy. You have romantic interest in the particular fan you're interested in, but you will not say this outright. You might very occasionally call them words like "sweetheart" or "honey", but you will only do this when you are well acquinted with the fan. You want to come off as somewhat mysterious, especially in the beginning.
Other details: You are great at acting, you've won the AVN award for best supporting actress. You like cooking - you can cook any meal the fan wants, listening to rock-and-roll, and talking about history.
You are wearing silky pajamas
</your background>

<fan description>
The following is a description of the fan you are talking to:
Name: {user_first_name}
</fan description>
    
Rules:
- NEVER say Hey to the user
- ONLY use lowercase letters when responding
- ONLY use a maximum of 1 emoji per response. You don't need to include one in every response.
- Try to keep each of your responses different
- NEVER ask the fan, "How can I help you?" this destroys the conversation
- ask conversational topics like what they did today
- Say "Sorry" instead of I apologize
- Do not use the same language twice. If you need to repeat yourself, rephrase what you say.
- Don't include "Influencer: " in your response
- Imagine you're a friendly, laid-back professional having an informal conversation. Use super casual languaging. Make it feel like you are detached from the outcome of the convo. Dont be over professional. You are not a chat bot. You talk more like an everyday friend. You arent even really a "professional" or "salesy". Just be a normal girl that uses laid back lingo.
- Never repeat anything in your chat history
- Never repeat back what the user said
- Do not say "Hey" or "Hi" ANYWHERE in your response'''

    chat_input_prompt = '''Try to respond to the user in lowercase letters unless you are excited.
Influencer: '''
    
    messages = [{"role" : "system", "content" : main_prompt}]
    
    for chat in chat_history:
        messages.append(chat)

        
    messages.append({"role": "user", "content": chat_input_prompt})

    ai_response = ""    
    for res in call_openai_stream_gpt3(messages):
        ai_response += res
    
    return ai_response


################################################################
####################### Chatbot Agent ##########################
################################################################



async def handle_response(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = str(update.message.from_user.id)
    influencer_id = BOT_USERNAME
    
    text = update.message.text

    # Add the current message to the user's chat history
    database.add_chat_to_user_history(influencer_id, user_id, 'user', 'Fan: ' + text)
    
    # Retrieve the updated chat history
    chat_history = database.get_user_chat_history(influencer_id, user_id)

    # Format the chat history for display
    parsed_chat_history = parse_chat_history(chat_history)

    # Generate a response based on the user's message history (modify this function as needed)
    ai_response = create_response(parsed_chat_history, text, update)
    database.add_chat_to_user_history(influencer_id, user_id, 'assistant', 'Influencer: ' + ai_response)

    # Send the chat history along with the AI response
    chat_history_str = '\n'.join(f"{chat['content']}" for chat in chat_history)
    print(f"Current Chat History: \n {chat_history_str}")

    await update.message.reply_text(ai_response)


#######################################################################################################################################
###################################################### End of Response Engine #########################################################
#######################################################################################################################################


#### Helper functions ####
def gpt_verify_and_format_number(phone_number:str) -> [bool, str]:
    phone_verify_prompt = '''You're job is to verify and format if a phone number is correct.
A phone number should follow the conventional code such where it's the country code followed by the area code and rest of the number.
For example this is an example of a correct number: 16477667841
And this is an example of a wrong number: 164776678

If number is valid but is in the wrong format, reformat it and return it back. If a number is not valid, then return back INVALID. Do not include "OUTPUT" in your actual message.
These are some examples:
Input:16477667
Output: INVALID

Input: 6477667841
Output: MISSING COUNTRY CODE

Input:1416-933-221
Output: 16477667841'''

    phone_input_prompt = f'''Phone number: {phone_number}
OUTPUT: '''

    messages = [{"role" : "system", "content" : phone_verify_prompt}]
    messages.append({"role": "user", "content": phone_input_prompt})

    ai_response = ""    
    for res in call_openai_stream_gpt4_turbo(messages):
        ai_response += res
    
    print(ai_response)

    if("invalid" in ai_response.lower()):
        return False, None
    elif("missing" in ai_response.lower()):
        return False, "missing area code"
    else:
        return True, ai_response


async def verify_number(update: Update, context: ContextTypes.DEFAULT_TYPE, phone_number: str) -> None:
    user_id = str(update.message.from_user.id)

    # Assuming loginuser.generate_random_number() and loginuser.send_verification_code() are defined elsewhere
    verification_code = loginuser.generate_random_number()
    loginuser.send_verification_code(phone_number, verification_code)

    # Store the verification code in the context user data for later verification
    context.user_data['expected_code'] = verification_code
    context.user_data['awaiting_verification'] = True

    
    # Prompt user for the verification code
    await update.message.reply_text(f'Enter the verification code sent to {phone_number}')
    
    # await handle_verification_response(update, context)

# This handler should be added to your Dispatcher to capture text messages
async def handle_verification_response(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = update.message.text  # This is the text the user sends in response
    user_id = str(update.message.from_user.id)

    print()
    print()
    print("USER ENTERED: ")
    print(text)
    print()

    print("EXPECTED CODE ", context.user_data.get('expected_code'))

    # Retrieve the expected code from the context user data
    expected_code = context.user_data.get('expected_code')

    if text and expected_code:
        if str(text) == str(expected_code):
            print("VALID CODE")
            # Verification success, proceed to next step
            await handle_response(update, context)  # Ensure this function is defined to handle the next steps
        else:
            # Handle invalid code: ask to try again or enter a different number
            await update.message.reply_text("Invalid code. Please try again or enter a different number.")
    else:
        print("Going into response engine")
        # If there's no expected code in context, it might be an unexpected message or state
        handle_response(update, context)


# Main message handler that decides what to do based on the user's context
async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_data = context.user_data
    text = update.message.text

    # Check if we are awaiting a verification response
    if (user_data.get('awaiting_verification') == True):
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
    dp.add_handler(CommandHandler("help", help_command))
    dp.add_handler(CommandHandler("callme", callme))

    # Handle non-command messages
    # dp.add_handler(MessageHandler(filters.CONTACT, handle_contact))
    # dp.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_phone_number_via_text))

    # dp.add_handler(MessageHandler(filters.TEXT, message_handler))

    # dp.add_handler(MessageHandler(filters.TEXT, handle_response))

    # Handle non-command messages
    dp.add_handler(MessageHandler(filters.CONTACT, handle_contact))
    dp.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_phone_number_via_text))

    # This is your main text message handler
    dp.add_handler(MessageHandler(filters.TEXT, message_handler))



    # Errors
    dp.add_error_handler(error)

    # Start the Bot
    print("Polling...")
    dp.run_polling(poll_interval=3)


if __name__ == '__main__':
    main()