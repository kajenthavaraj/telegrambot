from typing import Final
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

import database



TOKEN: Final = "6736028246:AAGbbsnfYsBJ1y-Fo0jO4j0c9WBuLxGDFKk"
BOT_USERNAME: Final = '@veronicaavluvaibot'

chat_history = {}


##### Commands #####
'''
start - starts the bot
help - provides help for Veronica AI
callme - Have Veronica AI call you
'''

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text('Wagwan G')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text('Hey how can I help you?')


async def callme(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    execute_call()
    await update.message.reply_text('Im calling you, check your phone')


async def error(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    print(f"Update {update} caused error {context.error}")



# Maybe have "account info - give status on what's in the account" command that sends all the account info (number of credits, etc.)



def execute_call() -> bool:
    # EXECTUTE API CALL
    return True




##### Chat History Helper Function #####
def parse_chat_history(original_chat_history):
    # Use a list comprehension to iterate through each chat entry
    # and construct a new dictionary with only 'role' and 'content' keys for each entry
    parsed_chat_history = [{'role': chat['role'], 'content': chat['content']} for chat in original_chat_history]
    
    return parsed_chat_history


def last_20_chat_history(chat_history):
    return



#######################################################################################################################################
######################################################### Response Engine #############################################################
#######################################################################################################################################

def create_response(chat_history: dict, text: str) -> str:
    prompt = '''
'''

    return "What's up G"


async def handle_response(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = str(update.message.from_user.id)
    text = update.message.text

    influencer_id = BOT_USERNAME
    
    # Check if user is subscribed and add them if not
    database.add_user_to_influencer_subscription(influencer_id, user_id)

    # Add the current message to the user's chat history
    database.add_chat_to_user_history(influencer_id, user_id, 'user', 'Fan: ' + text)
    
    # Retrieve the updated chat history
    chat_history = database.get_user_chat_history(influencer_id, user_id)

    # Format the chat history for display
    parsed_chat_history = parse_chat_history(chat_history)

    # Generate a response based on the user's message history (modify this function as needed)
    ai_response = create_response(parsed_chat_history, text)
    database.add_chat_to_user_history(influencer_id, user_id, 'assistant', 'Influencer: ' + ai_response)

    # Send the chat history along with the AI response
    chat_history_str = '\n'.join(f"{chat['content']}" for chat in chat_history)
    print(f"Current Chat History: \n {chat_history_str}")
    
    await update.message.reply_text(ai_response)


#######################################################################################################################################
###################################################### End of Response Engine #########################################################
#######################################################################################################################################


def main():

    # Get the dispatcher to register handlers
    dp = Application.builder().token(TOKEN).build()

    # on different commands - answer in Telegram
    dp.add_handler(CommandHandler("start", start_command))
    dp.add_handler(CommandHandler("help", help_command))
    dp.add_handler(CommandHandler("callme", callme))

    # Handle non-command messages
    dp.add_handler(MessageHandler(filters.TEXT, handle_response))


    # Errors
    dp.add_error_handler(error)

    # Start the Bot
    print("Polling...")
    dp.run_polling(poll_interval=3)


if __name__ == '__main__':
    main()