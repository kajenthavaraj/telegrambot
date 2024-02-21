from typing import Final
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, LabeledPrice, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, Updater, CallbackContext, CallbackQueryHandler
from telegram.ext import PreCheckoutQueryHandler
import asyncio
import time
import requests
import json
import stripe 

import openai

openai.api_key = "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"
# stripe.api_key = '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'
stripe.api_key = 'sk_test_51IsqDJBo1ZNr3GjAvWVMXtJUnocMO3LsOBaZKJIwtKcAd6regW0OrOgLGrjldgvMmS3K6PW3q4rkTDIbWb3VCUm00072rgmWbe'

TOKEN: Final = "6736028246:AAGbbsnfYsBJ1y-Fo0jO4j0c9WBuLxGDFKk"
BOTUSERNAME: Final = '@veronicaavluvaibot'

'''
start - starts the bot
help - provides help for Veronica AI
callme - Have Veronica AI call you
purchase - purchase credits 
'''

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Extract the start parameter if present
    start_args = context.args  # context.args contains the parameters passed after /start
    
    if start_args:
        start_param = start_args[0]
        if start_param == 'payment_successful':
            response_message = 'Thank you for completing the payment!'
        elif start_param == 'payment_canceled':
            response_message = 'Payment was canceled.'
        else:
            response_message = 'Welcome! How can I assist you today?'
    else:
        response_message = 'Welcome! How can I assist you today?'

    await update.message.reply_text(response_message)


async def handle_response(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Extract the text from the user's message
    user_message = update.message.text

    # Here, you would typically generate a response. For simplicity, let's echo the message.
    # In a real scenario, you might want to generate a response based on some logic or external API calls.
    response_message = f"You said: {user_message}"

    # Send the response back to the user
    await update.message.reply_text(response_message)


async def purchase(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [
        [InlineKeyboardButton("5 minutes ($5)", callback_data='5')],
        [InlineKeyboardButton("10 minutes ($10)", callback_data='10')],
        [InlineKeyboardButton("20 minutes ($20)", callback_data='20')],
        [InlineKeyboardButton("50 minutes ($50)", callback_data='50')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('Please choose the duration you’d like to purchase:', reply_markup=reply_markup)


async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    # Extract the selected duration and calculate the price
    duration_minutes = int(query.data)  # This is based on the callback_data set in the InlineKeyboardButton
    amount = duration_minutes * 100  # Stripe expects amounts in cents

    user_id = str(update.effective_user.id)
    print(user_id)

    # Create a Stripe Checkout Session with deep link redirection
    checkout_session = stripe.checkout.Session.create(
        payment_method_types=['card'],
        line_items=[{
            'price_data': {
                'currency': 'usd',
                'product_data': {
                    'name': f'{duration_minutes} minutes credits for Veronica AI',
                },
                'unit_amount': amount,
            },
            'quantity': 1,
        }],
        metadata={'telegram_user_id': user_id}, # pass in metadata
        mode='payment',
        success_url='https://t.me/veronicaavluvaibot?start=payment_successful',
        cancel_url='https://t.me/veronicaavluvaibot?start=payment_canceled',
    )

    # Prepare the inline keyboard with the payment URL
    keyboard = [[InlineKeyboardButton("Complete Payment", url=checkout_session.url)]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    payment_text = '''Please complete your payment:

(all payments are securely processed by Stripe)'''

    # Use context.bot.send_message to send a new message to the chat
    await context.bot.send_message(chat_id=query.message.chat_id, text=payment_text, reply_markup=reply_markup)


def main():
    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_response))

    application.add_handler(CommandHandler("purchase", purchase))
    application.add_handler(CallbackQueryHandler(button))

    print("Bot is polling...")
    application.run_polling()


if __name__ == '__main__':
    main()