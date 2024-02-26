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
from connectBubble import get_user_subscription, check_user_subscription


import openai

# stripe.api_key = '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'
stripe.api_key = 'sk_test_51IsqDJBo1ZNr3GjAvWVMXtJUnocMO3LsOBaZKJIwtKcAd6regW0OrOgLGrjldgvMmS3K6PW3q4rkTDIbWb3VCUm00072rgmWbe'

TOKEN: Final = "6736028246:AAGbbsnfYsBJ1y-Fo0jO4j0c9WBuLxGDFKk"
BOTUSERNAME: Final = '@veronicaavluvaibot'



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

async def subscribe(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    influencer_id = CONSTANTS.BOT_USERNAME 
    user_id = str(update.effective_user.id)


    bubble_unique_id = get_bubble_unique_id(influencer_id, user_id)
    print("The bubble ID is: ", bubble_unique_id)

    if not bubble_unique_id:
            print("Bubble unique ID not found")


    existing_subscriptions = check_user_subscription(bubble_unique_id, influencer_id) 
    print (existing_subscriptions)

    if existing_subscriptions:
        print("User already has an active subscription.")
        message = "You already have an active subscription."
        return await update.message.reply_text(message)

    else:
        keyboard = [
            [InlineKeyboardButton("Monthly - $24.99", callback_data='subscribe_monthly')],
            [InlineKeyboardButton("Yearly - $249", callback_data='subscribe_yearly')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text('Choose your subscription plan:', reply_markup=reply_markup)

async def manage_subscription(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = str(update.effective_user.id)
    influencer_id = CONSTANTS.BOT_USERNAME
    bubble_unique_id = get_bubble_unique_id(influencer_id, user_id)

    if not bubble_unique_id:
        await update.message.reply_text("Error retrieving your subscription information. Please try again.")
        return

    existing_subscription = check_user_subscription(bubble_unique_id, influencer_id)
    
    if existing_subscription:
        # User has an active subscription
        keyboard = [
            [InlineKeyboardButton("Cancel Subscription", callback_data='cancel_subscription')],
            [InlineKeyboardButton("Upgrade Subscription", callback_data='upgrade_subscription')],
            [InlineKeyboardButton("Downgrade Subscription", callback_data='downgrade_subscription')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text('Manage your subscription:', reply_markup=reply_markup)
    else:
        # User does not have an active subscription
        await update.message.reply_text("You currently do not have an active subscription. Please use /subscribe to subscribe.")

async def handle_subscription_cancellation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = str(query.from_user.id)
    print(f"Handling subscription cancellation for user ID: {user_id}")

    bubble_unique_id = get_bubble_unique_id(CONSTANTS.BOT_USERNAME, user_id)
    print(f"Bubble unique ID retrieved: {bubble_unique_id}")

    # Retrieve the subscription ID, which is also the Stripe subscription ID
    subscription_id = get_user_subscription(bubble_unique_id)
    print(f"Subscription ID (also Stripe ID): {subscription_id}")

    if not subscription_id:
        print("No active subscription found.")
        await query.edit_message_text("You do not have an active subscription to cancel.")
        return

    # Cancel the subscription with Stripe
    if cancel_stripe_subscription(subscription_id):
        print("Stripe subscription cancelled successfully.")
        # If successful, update the status in Bubble
        if update_database(bubble_unique_id, "User", "subscription_telegram", None) == 204:
            await query.edit_message_text("Your subscription has been successfully cancelled.")
        else:
            await query.edit_message_text("Failed to update subscription status in our system. Please contact support.")
    else:
        print("Failed to cancel the subscription with Stripe.")
        await query.edit_message_text("Failed to cancel the subscription with Stripe. Please contact support.")


def cancel_stripe_subscription(subscription_id):
    try:
        stripe.Subscription.delete(subscription_id)
        return True
    except Exception as e:
        print(f"Error canceling subscription with Stripe: {e}")
        return False

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    user_id = str(update.effective_user.id)

    
    if query.data.startswith('subscribe') or query.data in ['cancel_subscription', 'upgrade_subscription', 'downgrade_subscription']:
        # Subscription handling logic
        if query.data == 'subscribe_monthly':
            price_id = 'price_1OnAcnBo1ZNr3GjAKryjcBaa'  # Replace with your Stripe price ID
        elif query.data == 'subscribe_yearly':
            price_id = 'price_1OnAe8Bo1ZNr3GjAvMXybMlU'  # Replace with your Stripe price ID

        elif query.data == 'cancel_subscription':
            # Call your function to handle subscription cancellation
            await handle_subscription_cancellation(update, context)
            return
        elif query.data == 'upgrade_subscription':
            # Handle subscription upgrade
            # You'll need to implement this part
            return
        elif query.data == 'downgrade_subscription':
            # Handle subscription downgrade
            # You'll need to implement this part
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