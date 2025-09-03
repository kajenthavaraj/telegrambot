from typing import Final
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton

from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import time
import requests
import json

from openai import OpenAI

from config import OPENAI_API_KEY
client = OpenAI(api_key=OPENAI_API_KEY)

import database
import loginuser


from config import TELEGRAM_BOT_TOKENS
TOKEN: Final = TELEGRAM_BOT_TOKENS.get('veronica', "FALLBACK_TOKEN")
BOT_USERNAME: Final = '@influencerai_bot'


from telegram import ReplyKeyboardMarkup, KeyboardButton, Update, ReplyKeyboardRemove
from telegram.ext import Updater, CommandHandler, MessageHandler, filters, CallbackContext

async def start(update: Update, context: CallbackContext) -> None:
    # contact_keyboard = KeyboardButton(text="Share my phone number", request_contact=True)
    # custom_keyboard = [[contact_keyboard]]
    # reply_markup = ReplyKeyboardMarkup(custom_keyboard, one_time_keyboard=True)
    
    await update.message.reply_text('How are you today?')



# Payments function - user enteres any text
async def handle_response(update, context):
    await update.message.reply_text('Payments function')



def main():
    # updater = Updater(TOKEN, use_context=True)
    dp = Application.builder().token(TOKEN).build()

    # dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(filters.TEXT, handle_response))

    dp.run_polling(poll_interval=3)
    # updater.idle()

if __name__ == '__main__':
    main()
