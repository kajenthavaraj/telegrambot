from typing import Final
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, LabeledPrice, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, Updater, CallbackContext, CallbackQueryHandler
from telegram.ext import PreCheckoutQueryHandler
from bubbledb import update_database
import asyncio
import time
import requests
import json
import stripe 
import CONSTANTS
from database import get_bubble_unique_id
from connectBubble import get_user_subscription, check_user_subscription, update_subscription


import openai

# stripe.api_key = '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'
stripe.api_key = 'sk_test_51IsqDJBo1ZNr3GjAvWVMXtJUnocMO3LsOBaZKJIwtKcAd6regW0OrOgLGrjldgvMmS3K6PW3q4rkTDIbWb3VCUm00072rgmWbe'

TOKEN: Final = "6736028246:AAGbbsnfYsBJ1y-Fo0jO4j0c9WBuLxGDFKk"
BOTUSERNAME: Final = '@veronicaavluvaibot'



async def start(update: Update, context: ContextTypes) -> None:
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


async def handle_response(update: Update, context: ContextTypes) -> None:
    # Extract the text from the user's message
    user_message = update.message.text

    # Here, you would typically generate a response. For simplicity, let's echo the message.
    # In a real scenario, you might want to generate a response based on some logic or external API calls.
    response_message = f"You said: {user_message}"

    # Send the response back to the user
    await update.message.reply_text(response_message)


async def purchase(update: Update, context: ContextTypes) -> None:
    keyboard = [
        [InlineKeyboardButton("5 minutes ($5)", callback_data='5')],
        [InlineKeyboardButton("10 minutes ($10)", callback_data='10')],
        [InlineKeyboardButton("20 minutes ($20)", callback_data='20')],
        [InlineKeyboardButton("50 minutes ($50)", callback_data='50')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('Please choose the duration you’d like to purchase:', reply_markup=reply_markup)

async def subscribe(update: Update, context: ContextTypes) -> None:
    influencer_id = CONSTANTS.BOT_USERNAME 
    influencer_UID = CONSTANTS.INFLUENCER_UID
    user_id = str(update.effective_user.id)


    bubble_unique_id = get_bubble_unique_id(influencer_id, user_id)
    print("The bubble ID is: ", bubble_unique_id)

    if not bubble_unique_id:
            print("Bubble unique ID not found")
            await update.message.reply_text("Error retrieving your subscription information. Please try again.")


    # The function now returns a boolean indicating active status and the subscription status
    has_active_subscription, subscription_status = check_user_subscription(bubble_unique_id, influencer_UID) 
    print(f"Active subscription status: {has_active_subscription}, Status: {subscription_status}")

    if has_active_subscription and subscription_status == "complete":
        print("User already has an active subscription.")
        message = "You already have an active subscription."
        await update.message.reply_text(message)
    else:
        keyboard = [
            [InlineKeyboardButton("Monthly - $24.99", callback_data='subscribe_monthly')],
            [InlineKeyboardButton("Yearly - $249", callback_data='subscribe_yearly')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text('Choose your subscription plan:', reply_markup=reply_markup)

async def manage_subscription(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    influencer_id = CONSTANTS.BOT_USERNAME 
    influencer_UID = CONSTANTS.INFLUENCER_UID
    user_id = str(update.effective_user.id)


    bubble_unique_id = get_bubble_unique_id(influencer_id, user_id)
    print("The bubble ID is: ", bubble_unique_id)

    if not bubble_unique_id:
            print("Bubble unique ID not found")
            await update.message.reply_text("Error retrieving your subscription information. Please try again.")
    
    # The function now returns a boolean indicating active status and the subscription status
    has_active_subscription, subscription_status = check_user_subscription(bubble_unique_id, influencer_UID) 
    print(f"Active subscription status: {has_active_subscription}, Status: {subscription_status}")

    if has_active_subscription:
        keyboard = [
            [InlineKeyboardButton("Cancel Subscription", callback_data='cancel_subscription')],
            [InlineKeyboardButton("Check Credits and Subscription", callback_data='check_credits')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text('Manage your subscription:', reply_markup=reply_markup)
    else:
        await update.message.reply_text("You currently do not have an active subscription. Please use /subscribe to subscribe.")

async def handle_subscription_cancellation(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    user_id = str(update.effective_user.id)
    influencer_id = CONSTANTS.BOT_USERNAME
    influencer_UID = CONSTANTS.INFLUENCER_UID

    bubble_unique_id = get_bubble_unique_id(influencer_id, user_id)

    # Using the get_user_subscription function to directly retrieve the Stripe subscription ID
    stripe_subscription_id = get_user_subscription(bubble_unique_id)

    if stripe_subscription_id:
        try:
            # Cancel the subscription with Stripe
            stripe.Subscription.delete(stripe_subscription_id)
            # Assuming update_subscription can also update the status to 'cancelled'
            successful_update = update_subscription(user_uid=bubble_unique_id, telegram_user_id=user_id, influencer_uid=influencer_UID, subscription_ID=stripe_subscription_id, subscription_plan=None, status="cancelled", last_billing_date=None, next_billing_date=None)
            if successful_update:
                await query.edit_message_text("Your subscription has been successfully cancelled.")
            else:
                raise Exception("Failed to update Bubble database.")
        except Exception as e:
            print(f"Error cancelling subscription with Stripe: {e}")
            await query.edit_message_text("Failed to cancel the subscription. Please contact support.")
    else:
        await query.edit_message_text("You do not have an active subscription to cancel.")




async def button(update: Update, context: ContextTypes) -> None:
    query = update.callback_query
    await query.answer()
    user_id = str(update.effective_user.id)

    
    if query.data.startswith('subscribe') or query.data in ['cancel_subscription']:
        # Subscription handling logic
        if query.data == 'subscribe_monthly':
            price_id = 'price_1OnAcnBo1ZNr3GjAKryjcBaa'  # Replace with your Stripe price ID
        elif query.data == 'subscribe_yearly':
            price_id = 'price_1OnAe8Bo1ZNr3GjAvMXybMlU'  # Replace with your Stripe price ID

        elif query.data == 'cancel_subscription':
            # Call your function to handle subscription cancellation
            await handle_subscription_cancellation(update, context)
            return
        

        # Create a Stripe Checkout Session for subscription
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price': price_id,
                'quantity': 1,
            }],
            mode='subscription',
            success_url='https://t.me/veronicaavluvaibot?start=subscription_successful',
            cancel_url='https://t.me/veronicaavluvaibot?start=subscription_canceled',
            metadata={'telegram_user_id': user_id},  # Pass in metadata to identify the user
        )

        keyboard = [[InlineKeyboardButton("Complete Subscription", url=checkout_session.url)]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await context.bot.send_message(chat_id=query.message.chat_id, text="Please complete your subscription:", reply_markup=reply_markup)
    else:
        # One-off payment handling logic
        duration_minutes = int(query.data)  # This is based on the callback_data set in the InlineKeyboardButton
        amount = duration_minutes * 100  # Stripe expects amounts in cents

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
            metadata={'telegram_user_id': user_id},
            mode='payment',
            success_url='https://t.me/veronicaavluvaibot?start=payment_successful',
            cancel_url='https://t.me/veronicaavluvaibot?start=payment_canceled',
        )
        payment_text = '''Please complete your payment:

(all payments are securely processed by Stripe)'''

        keyboard = [[InlineKeyboardButton("Complete Payment", url=checkout_session.url)]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await context.bot.send_message(chat_id=query.message.chat_id, text = payment_text, reply_markup=reply_markup)



def main():
    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_response))

    application.add_handler(CommandHandler("payments", purchase))
    application.add_handler(CommandHandler("subscribe", subscribe))
    application.add_handler(CommandHandler("manage", manage_subscription))


    application.add_handler(CallbackQueryHandler(button))

    print("Bot is polling...")
    application.run_polling()


if __name__ == '__main__':
    main()