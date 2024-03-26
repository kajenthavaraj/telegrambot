# from typing import Final
# from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, LabeledPrice, InlineKeyboardButton, InlineKeyboardMarkup
# from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, Updater, CallbackContext, CallbackQueryHandler
# from telegram.ext import PreCheckoutQueryHandler


from aiogram import Bot, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


from bubbledb import update_database
import asyncio
import time
import requests
import json
import stripe
from database import get_bubble_unique_id
from connectBubble import get_user_subscription, check_user_subscription, update_subscription, check_user_subscription_more_detail
import connectBubble
from datetime import datetime 
from influencer_data import Influencer
import openai

# stripe.api_key = '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'
stripe.api_key = 'sk_test_51IsqDJBo1ZNr3GjAvWVMXtJUnocMO3LsOBaZKJIwtKcAd6regW0OrOgLGrjldgvMmS3K6PW3q4rkTDIbWb3VCUm00072rgmWbe'

# bot = Bot(token=TOKEN)


# async def start(update: Update, context: ContextTypes) -> None:
#     # Extract the start parameter if present
#     start_args = context.args  # context.args contains the parameters passed after /start
    
#     if start_args:
#         start_param = start_args[0]
#         if start_param == 'payment_successful':
#             response_message = 'Thank you for completing the payment!'
#         elif start_param == 'payment_canceled':
#             response_message = 'Payment was canceled.'
#         else:
#             response_message = 'Welcome! How can I assist you today?'
#     else:
#         response_message = 'Welcome! How can I assist you today?'

#     await update.message.reply_text(response_message)


# async def handle_response(update: Update, context: ContextTypes) -> None:
#     # Extract the text from the user's message
#     user_message = update.message.text

#     # Here, you would typically generate a response. For simplicity, let's echo the message.
#     # In a real scenario, you might want to generate a response based on some logic or external API calls.
#     response_message = f"You said: {user_message}"

#     # Send the response back to the user
#     await update.message.reply_text(response_message)


# async def purchase(update: Update, context: ContextTypes) -> None:
#     keyboard = [
#         [InlineKeyboardButton("5 minutes ($5)", callback_data='5')],
#         [InlineKeyboardButton("10 minutes ($10)", callback_data='10')],
#         [InlineKeyboardButton("20 minutes ($20)", callback_data='20')],
#         [InlineKeyboardButton("50 minutes ($50)", callback_data='50')],
#     ]
#     reply_markup = InlineKeyboardMarkup(keyboard)
#     await update.message.reply_text('Please choose the duration you’d like to purchase:', reply_markup=reply_markup)



async def purchase(message: types.Message, influencer : Influencer) -> None:
    user_id = str(message.from_user.id)

    # Define the buttons
    buttons = [
        types.InlineKeyboardButton(text="5 minutes ($5)", callback_data='5'),
        types.InlineKeyboardButton(text="10 minutes ($10)", callback_data='10'),
        types.InlineKeyboardButton(text="20 minutes ($20)", callback_data='20'),
        types.InlineKeyboardButton(text="50 minutes ($50)", callback_data='50'),
    ]

    bubble_unique_id = get_bubble_unique_id(influencer.bot_username, user_id)
    # The function now returns a boolean indicating active status and the subscription status
    has_active_subscription, subscription_status = check_user_subscription(bubble_unique_id, influencer.bubble_id) 
    print(f"Active subscription status: {has_active_subscription}, Status: {subscription_status}")

    if not has_active_subscription and subscription_status == None:
        buttons.append(types.InlineKeyboardButton(text="Subscribe - 50 minutes/month ($24.99)", callback_data='btn_from_deposit'),)

    # Organize buttons into a keyboard layout
    keyboard_layout = [[btn] for btn in buttons]

    # Create InlineKeyboardMarkup with the specified layout
    reply_markup = types.InlineKeyboardMarkup(inline_keyboard=keyboard_layout)

    # Send the message with the inline keyboard
    await influencer.bot_object.send_message(chat_id=message.chat.id, text='Please choose the duration you’d like to purchase:', reply_markup=reply_markup)



# async def subscribe(update: Update, context: ContextTypes) -> None:
#     influencer_id = BOT_USERNAME 
#     influencer_UID = INFLUENCER_UID
#     user_id = str(update.effective_user.id)


#     bubble_unique_id = get_bubble_unique_id(influencer_id, user_id)
#     print("The bubble ID is: ", bubble_unique_id)

#     if not bubble_unique_id:
#             print("Bubble unique ID not found")
#             await update.message.reply_text("Error retrieving your subscription information. Please try again.")


#     # The function now returns a boolean indicating active status and the subscription status
#     has_active_subscription, subscription_status = check_user_subscription(bubble_unique_id, influencer_UID) 
#     print(f"Active subscription status: {has_active_subscription}, Status: {subscription_status}")

#     if has_active_subscription and subscription_status == "complete":
#         print("User already has an active subscription.")
#         message = "You already have an active subscription."
#         await update.message.reply_text(message)
#     else:
#         keyboard = [
#             [InlineKeyboardButton("Monthly - $24.99", callback_data='subscribe_monthly')],
#             [InlineKeyboardButton("Yearly - $249", callback_data='subscribe_yearly')]
#         ]
#         reply_markup = InlineKeyboardMarkup(keyboard)
#         await update.message.reply_text('Choose your subscription plan:', reply_markup=reply_markup)


async def send_subscription_message(chat_id, bot: Bot):
    buttons = [
                types.InlineKeyboardButton(text="Monthly - $24.99", callback_data='subscribe_monthly'),
                types.InlineKeyboardButton(text="Yearly - $249", callback_data='subscribe_yearly'),
    ]
    
    # Organize buttons into a keyboard layout
    keyboard_layout = [[btn] for btn in buttons]

    # Create InlineKeyboardMarkup with the specified layout
    reply_markup = types.InlineKeyboardMarkup(inline_keyboard=keyboard_layout)
    
    subscription_message = '''*What You Get:*
    • Daily pictures
    • 50 free minutes/month

Choose your subscription plan:'''

    await bot.send_message(chat_id=chat_id, text=subscription_message, reply_markup=reply_markup, parse_mode='Markdown')




async def subscribe(message: types.Message, influencer : Influencer) -> None:
    influencer_id = influencer.bot_username
    influencer_UID = influencer.bubble_id
    user_id = str(message.from_user.id)

    bubble_unique_id = get_bubble_unique_id(influencer_id, user_id)
    print("The bubble ID is: ", bubble_unique_id)

    if not bubble_unique_id:
        print("Bubble unique ID not found")
        await influencer.bot_object.send_message(chat_id=message.chat.id, text="Error retrieving your subscription information. Please try again.")

    
    # The function now returns a boolean indicating active status and the subscription status
    has_active_subscription, subscription_status = check_user_subscription(bubble_unique_id, influencer_UID) 
    print(f"Active subscription status: {has_active_subscription}, Status: {subscription_status}")

    if has_active_subscription and subscription_status == "complete":
        print("User already has an active subscription.")
        message_text = "You already have an active subscription."
        await influencer.bot_object.send_message(chat_id=message.chat.id, text=message_text)

    else:
        await send_subscription_message(message.chat.id, influencer.bot_object)



# async def manage_subscription(update: Update, context: CallbackContext) -> None:
#     query = update.callback_query
#     influencer_id = BOT_USERNAME 
#     influencer_UID = INFLUENCER_UID
#     user_id = str(update.effective_user.id)


#     bubble_unique_id = get_bubble_unique_id(influencer_id, user_id)
#     print("The bubble ID is: ", bubble_unique_id)

#     if not bubble_unique_id:
#             print("Bubble unique ID not found")
#             await update.message.reply_text("Error retrieving your subscription information. Please try again.")
    
#     # The function now returns a boolean indicating active status and the subscription status
#     has_active_subscription, subscription_status = check_user_subscription(bubble_unique_id, influencer_UID) 
#     print(f"Active subscription status: {has_active_subscription}, Status: {subscription_status}")

#     if has_active_subscription:
#         keyboard = [
#             [InlineKeyboardButton("Cancel Subscription", callback_data='cancel_subscription')],
#             [InlineKeyboardButton("Check Balance and Subscription ", callback_data='check_account')]
#         ]
#         reply_markup = InlineKeyboardMarkup(keyboard)
#         await update.message.reply_text('Manage your subscription:', reply_markup=reply_markup)
#     else:
#         await update.message.reply_text("You currently do not have an active subscription. Please use /subscribe to subscribe.")


async def manage_subscription(message: types.Message, influencer : Influencer) -> None:
    influencer_id = influencer.bot_username
    influencer_UID = influencer.bubble_id
    user_id = str(message.from_user.id)

    bubble_unique_id = get_bubble_unique_id(influencer_id, user_id)
    print("The bubble ID is: ", bubble_unique_id)

    if not bubble_unique_id:
            print("Bubble unique ID not found")
            await influencer.bot_object.send_message(chat_id=message.chat.id, text="Error retrieving your subscription information. Please try again.")
    
    # The function now returns a boolean indicating active status and the subscription status
    has_active_subscription, subscription_status = check_user_subscription(bubble_unique_id, influencer_UID) 
    print(f"Active subscription status: {has_active_subscription}, Status: {subscription_status}")

    # if has_active_subscription:
    if True:
        buttons = [
            types.InlineKeyboardButton(text="Cancel Subscription", callback_data='cancel_subscription'),
            types.InlineKeyboardButton(text="Check Balance and Subscription", callback_data='check_account'),
        ]

        # Organize buttons into a keyboard layout
        keyboard_layout = [[btn] for btn in buttons]

        # Create InlineKeyboardMarkup with the specified layout
        reply_markup = types.InlineKeyboardMarkup(inline_keyboard=keyboard_layout)
        
         # Send the message with the inline keyboard
        await influencer.bot_object.send_message(chat_id=message.chat.id, text='Manage your subscription:', reply_markup=reply_markup)

    else:
        await influencer.bot_object.send_message(chat_id=message.chat.id, text="""You currently do not have an active subscription.
Please use /subscribe to subscribe.""")




# async def handle_subscription_cancellation(message: types.Message) -> None:
#     query = update.callback_query
#     # Prepare the confirmation message with InlineKeyboardMarkup
#     keyboard = [
#         [InlineKeyboardButton("Yes, cancel my subscription", callback_data='confirm_cancel_subscription')],
#         [InlineKeyboardButton("No, keep my subscription", callback_data='keep_subscription')]
#     ]
#     reply_markup = InlineKeyboardMarkup(keyboard)
#     await query.edit_message_text("Are you sure you want to cancel your subscription?", reply_markup=reply_markup)
    

async def handle_subscription_cancellation(callback_query: types.CallbackQuery, bot: Bot):
    buttons = [
        types.InlineKeyboardButton(text="Yes, cancel my subscription", callback_data='confirm_cancel_subscription'),
        types.InlineKeyboardButton(text="No, keep my subscription", callback_data='keep_subscription'),
    ]

    # Organize buttons into a keyboard layout
    keyboard_layout = [[btn] for btn in buttons]

    # Create InlineKeyboardMarkup with the specified layout
    reply_markup = types.InlineKeyboardMarkup(inline_keyboard=keyboard_layout)
    # await callback_query.message.edit_text("Are you sure you want to cancel your subscription?", reply_markup=reply_markup)
    await bot.send_message(chat_id=callback_query.message.chat.id, text="Are you sure you want to cancel your subscription?", reply_markup=reply_markup)






# async def confirm_subscription_cancellation(update: Update, context: CallbackContext) -> None:
#     query = update.callback_query
#     user_id = str(update.effective_user.id)
#     influencer_id = BOT_USERNAME
#     influencer_UID = INFLUENCER_UID

#     bubble_unique_id = get_bubble_unique_id(influencer_id, user_id)

#     print("going to try and get user subscription now")
#     # Using the get_user_subscription function to directly retrieve the Stripe subscription ID
#     stripe_subscription_id = get_user_subscription(bubble_unique_id, influencer_UID)
#     print("stripe subscriptin id after the function is called: ", stripe_subscription_id)

#     if stripe_subscription_id:
#         try:
#             # Cancel the subscription with Stripe
#             stripe.Subscription.delete(stripe_subscription_id)
#             # Assuming update_subscription can also update the status to 'cancelled'
#             successful_update = update_subscription(user_uid=bubble_unique_id, telegram_user_id=user_id, influencer_uid=influencer_UID, subscription_ID=stripe_subscription_id, subscription_plan=None, status="cancelled", last_billing_date=None, next_billing_date=None, amount_paid=None)
#             if successful_update:
#                 await query.edit_message_text("Your subscription has been successfully cancelled.")
#             else:
#                 raise Exception("Failed to update Bubble database.")
#         except Exception as e:
#             print(f"Error cancelling subscription with Stripe: {e}")
#             await query.edit_message_text("Failed to cancel the subscription. Please contact support.")
#     else:
#         await query.edit_message_text("You do not have an active subscription to cancel.")


async def confirm_subscription_cancellation(callback_query: types.CallbackQuery, influencer : Influencer):
    # query = update.callback_query

    user_id = str(callback_query.from_user.id)
    influencer_id = influencer.bot_username
    influencer_UID = influencer.bubble_id

    bubble_unique_id = get_bubble_unique_id(influencer_id, user_id)

    print("going to try and get user subscription now")
    # Using the get_user_subscription function to directly retrieve the Stripe subscription ID
    stripe_subscription_id = get_user_subscription(bubble_unique_id, influencer_UID)
    print("stripe subscriptin id after the function is called: ", stripe_subscription_id)

    if stripe_subscription_id:
        try:
            # Cancel the subscription with Stripe
            stripe.Subscription.delete(stripe_subscription_id)
            
            # Update the subscription status in your database
            successful_update = update_subscription(user_uid=bubble_unique_id, telegram_user_id=user_id, influencer_uid=influencer_UID, subscription_ID=stripe_subscription_id, subscription_plan=None, status="cancelled", last_billing_date=None, next_billing_date=None, amount_paid=None)
            if successful_update:
                # await callback_query.message.edit_text("Your subscription has been successfully cancelled.")
                await influencer.bot_object.send_message(chat_id=callback_query.message.chat.id, text="Your subscription has been successfully cancelled.")
            else:
                raise Exception("Failed to update Bubble database.")
        except Exception as e:
            print(f"Error cancelling subscription with Stripe: {e}")
            # await callback_query.message.edit_text("Failed to cancel the subscription. Please contact support.")
            await influencer.bot_object.send_message(chat_id=callback_query.message.chat.id, text="Failed to cancel the subscription. Please contact support.")
    else:
        # await callback_query.message.edit_text("You do not have an active subscription to cancel.")
        await influencer.bot_object.send_message(chat_id=callback_query.message.chat.id, text="You do not have an active subscription to cancel.")






# async def balance_command(update: Update, context: ContextTypes) -> None:
#     query = update.callback_query
#     user_id = str(update.effective_user.id)
#     influencer_id = BOT_USERNAME
#     influencer_UID = INFLUENCER_UID

#     bubble_unique_id = get_bubble_unique_id(influencer_id, user_id)

#     # Assuming get_minutes_credits returns the number of credits the user has
#     num_credits = connectBubble.get_minutes_credits(bubble_unique_id)
#     num_credits = str(round(num_credits, 2))

#     has_active_subscription, subscription_status, next_billing_date = check_user_subscription_more_detail(bubble_unique_id, influencer_UID)

#     # Prepare message content based on subscription status and credits
#     if has_active_subscription:
#         next_billing_date = datetime.strptime(next_billing_date, "%Y-%m-%dT%H:%M:%S.%fZ")
#         formatted_next_billing_date = next_billing_date.strftime("%Y-%m-%d")
#         subscription_message = f"You have an active subscription. Your next billing date is on {formatted_next_billing_date}."
#     else:
#         subscription_message = "You do not have an active subscription."

#     credits_message = f"Your available credits: {num_credits}" if num_credits is not None else "Error retrieving credits information."

#     # Send message to user
#     message_content = f"{subscription_message}\n{credits_message}"
#     await query.edit_message_text(message_content)



async def balance_command(callback_query: types.CallbackQuery, influencer : Influencer):
    user_id = str(callback_query.from_user.id)
    influencer_id = influencer.bot_username
    influencer_UID = influencer.bubble_id

    bubble_unique_id = get_bubble_unique_id(influencer_id, user_id)

    # Assuming connectBubble.get_minutes_credits returns the number of credits the user has
    num_credits = connectBubble.get_minutes_credits(bubble_unique_id)
    num_credits = str(round(num_credits, 2)) if num_credits is not None else "Error retrieving credits information."

    has_active_subscription, subscription_status, next_billing_date = check_user_subscription_more_detail(bubble_unique_id, influencer_UID)

    # Prepare message content based on subscription status and credits
    if has_active_subscription and next_billing_date:
        next_billing_date = datetime.strptime(next_billing_date, "%Y-%m-%dT%H:%M:%S.%fZ")
        formatted_next_billing_date = next_billing_date.strftime("%Y-%m-%d")
        subscription_message = f"You have an active subscription. Your next billing date is on {formatted_next_billing_date}."
    else:
        subscription_message = "You do not have an active subscription."

    credits_message = f"Your available credits: {num_credits}."

    # Send message to user
    message_content = f"{subscription_message}\n{credits_message}"
    # await callback_query.message.edit_text(message_content)
    await influencer.bot_object.send_message(chat_id=callback_query.message.chat.id, text=message_content)




# async def button(update: Update, context: ContextTypes) -> None:
#     query = update.callback_query
#     await query.answer()
#     user_id = str(update.effective_user.id)

#     if query.data.startswith('subscribe'):
#         # Subscription handling logic
#         if query.data == 'subscribe_monthly':
#             price_id = 'price_1OnAcnBo1ZNr3GjAKryjcBaa'  
#         elif query.data == 'subscribe_yearly':
#             price_id = 'price_1OnAe8Bo1ZNr3GjAvMXybMlU' 

#         # Create a Stripe Checkout Session for subscription
#         checkout_session = stripe.checkout.Session.create(
#             payment_method_types=['card'],
#             line_items=[{
#                 'price': price_id,
#                 'quantity': 1,
#             }],
#             mode='subscription',
#             success_url='https://t.me/veronicaavluvaibot?start=subscription_successful',
#             cancel_url='https://t.me/veronicaavluvaibot?start=subscription_canceled',
#             # success_url='https://t.me/veronicaavluvaibot?start=subscription_successful',
#             # cancel_url='https://t.me/veronicaavluvaibot?start=subscription_canceled',
#             metadata={'telegram_user_id': user_id},  # Pass in metadata to identify the user
#         )

#         keyboard = [[InlineKeyboardButton("Complete Subscription", url=checkout_session.url)]]
#         reply_markup = InlineKeyboardMarkup(keyboard)
#         await context.bot.send_message(chat_id=query.message.chat_id, text="Please complete your subscription:", reply_markup=reply_markup)

#     elif query.data == 'cancel_subscription':
#         await handle_subscription_cancellation(update, context)
    
#     elif query.data == 'confirm_cancel_subscription':
#         await confirm_subscription_cancellation(update, context)

#     elif query.data == 'keep_subscription':
#         await query.edit_message_text("Your subscription remains active. Thank you for staying with us.")

#     elif query.data == 'check_account':
#         await balance_command(update, context)
    
#     else:
#         # One-off payment handling logic
#         duration_minutes = int(query.data)  # This is based on the callback_data set in the InlineKeyboardButton
#         amount = duration_minutes * 100  # Stripe expects amounts in cents

#         checkout_session = stripe.checkout.Session.create(
#             payment_method_types=['card'],
#             line_items=[{
#                 'price_data': {
#                     'currency': 'usd',
#                     'product_data': {
#                         'name': f'{duration_minutes} minutes credits for Veronica AI',
#                     },
#                     'unit_amount': amount,
#                 },
#                 'quantity': 1,
#             }],
#             metadata={'telegram_user_id': user_id},
#             mode='payment',
#             success_url='https://t.me/veronicaavluvaibot?start=payment_successful',
#             cancel_url='https://t.me/veronicaavluvaibot?start=payment_canceled',
#         )
#         payment_text = '''Please complete your payment:

# (all payments are securely processed by Stripe)'''

#         keyboard = [[InlineKeyboardButton("Complete Payment", url=checkout_session.url)]]
#         reply_markup = InlineKeyboardMarkup(keyboard)
#         await context.bot.send_message(chat_id=query.message.chat_id, text = payment_text, reply_markup=reply_markup)




async def button(callback_query: types.CallbackQuery, influencer : Influencer):
    print("Button called")
    # await callback_query.answer() ###MAYBE comment back in
    user_id = str(callback_query.from_user.id)
    bot_username_short = influencer.bot_username[1:]
    
    if callback_query.data.startswith('subscribe'):
        # Subscription handling logic
        if callback_query.data == 'subscribe_monthly':
            price_id = 'price_1OnAcnBo1ZNr3GjAKryjcBaa'
        elif callback_query.data == 'subscribe_yearly':
            price_id = 'price_1OnAe8Bo1ZNr3GjAvMXybMlU'

        # Create a Stripe Checkout Session for subscription
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price': price_id,
                'quantity': 1,
            }],
            mode='subscription',
            success_url=f'https://t.me/{bot_username_short}?start=subscription_successful',
            cancel_url=f'https://t.me/{bot_username_short}?start=subscription_canceled',
            metadata={'telegram_user_id': user_id},
        )

        payment_text = "Complete Subscription"
        payment_button = types.InlineKeyboardButton(text="Complete Payment", url=checkout_session.url)
        keyboard = types.InlineKeyboardMarkup(inline_keyboard=[[payment_button]])
        await influencer.bot_object.send_message(chat_id=callback_query.message.chat.id, text=payment_text, reply_markup=keyboard)



    elif callback_query.data == 'btn_from_deposit':
        await send_subscription_message(callback_query.message.chat.id, influencer.bot_object)

    elif callback_query.data == 'cancel_subscription':
        await handle_subscription_cancellation(callback_query, influencer.bot_object)

    elif callback_query.data == 'confirm_cancel_subscription':
        await confirm_subscription_cancellation(callback_query, influencer)

    elif callback_query.data == 'keep_subscription':
        # await callback_query.message.edit_text("Your subscription remains active. Thank you for staying with us.")
        await influencer.bot_object.send_message(chat_id=callback_query.message.chat.id, text="Your subscription remains active. Thank you for staying with us.")

    elif callback_query.data == 'check_account':
        await balance_command(callback_query, influencer)

    else:
        # One-off payment handling logic
        duration_minutes = int(callback_query.data)  # Based on the callback_data set in the InlineKeyboardButton
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
            success_url=f'https://t.me/{bot_username_short}?start=payment_successful',
            cancel_url=f'https://t.me/{bot_username_short}?start=payment_canceled',
        )

        payment_text = "Please complete your payment:\n\n(all payments are securely processed by Stripe)"
        payment_button = types.InlineKeyboardButton(text="Complete Payment", url=checkout_session.url)
        keyboard = types.InlineKeyboardMarkup(inline_keyboard=[[payment_button]])

        
        print("checkout_session.url")
        print(checkout_session.url)
        await influencer.bot_object.send_message(chat_id=callback_query.message.chat.id, text=payment_text, reply_markup=keyboard)




# def main():
#     application = Application.builder().token(TOKEN).build()

#     application.add_handler(CommandHandler("start", start))
#     application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_response))

#     application.add_handler(CommandHandler("payments", purchase))
#     application.add_handler(CommandHandler("subscribe", subscribe))
#     application.add_handler(CommandHandler("manage", manage_subscription))


#     application.add_handler(CallbackQueryHandler(button))

#     print("Bot is polling...")
#     application.run_polling()


# if __name__ == '__main__':
#     main()