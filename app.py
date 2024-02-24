from flask import Flask, request, abort
import stripe
import requests
from typing import Final
from connectBubble import update_minutes_credits, add_subscription, check_user_subscriptions
from database import get_bubble_unique_id
import CONSTANTS
import logging
from datetime import datetime


# Flask app setup
app = Flask(__name__)

# Stripe setup
stripe.api_key = "sk_test_51IsqDJBo1ZNr3GjAvWVMXtJUnocMO3LsOBaZKJIwtKcAd6regW0OrOgLGrjldgvMmS3K6PW3q4rkTDIbWb3VCUm00072rgmWbe"  

# endpoint_secret = 'whsec_TRS246LG1aQG1tsWzW2D0hYLFZYqWwja'  # this is the live version

endpoint_secret = 'whsec_xtHqX4aEuAlh8kYH8Wcp90sQeENaUS52' # this is the test version


# Telegram setup
BOT_TOKEN = "6736028246:AAGbbsnfYsBJ1y-Fo0jO4j0c9WBuLxGDFKk"  

# Bubble setup
BUBBLE_API_URL = "https://app.tryinfluencerai.com/api/1.1/obj/"  
BUBBLE_API_TOKEN = "7bfc4e7b2cfbd0475b1ec923a0ea4c99"  

@app.route('/webhook', methods=['POST'])
def stripe_webhook():
    payload = request.get_data(as_text=True)  
    sig_header = request.headers.get('Stripe-Signature')


    try:
        event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
    except ValueError as e:
        print(f"ValueError: {e}")
        abort(400)
    except stripe.error.SignatureVerificationError as e:
        print(f"SignatureVerificationError: {e}")
        abort(400)

    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        
        metadata = session.get('metadata', {})
        telegram_user_id = metadata.get('telegram_user_id')
        influencer_id = CONSTANTS.BOT_USERNAME 
        bubble_unique_id = get_bubble_unique_id(influencer_id, telegram_user_id)
        #bubble_unique_id = '1705089991492x506710590267403400'

        if not bubble_unique_id:
            print("Bubble unique ID not found in the first if statement")
            # Handle error, maybe send a message back to user
            return '', 200

        if session.get('subscription'):
            print("Subscription started")
            subscription = event['data']['object']
            metadata = subscription.get('metadata', {})
            telegram_user_id = metadata.get('telegram_user_id')

            influencer_id = CONSTANTS.BOT_USERNAME 
            bubble_unique_id = get_bubble_unique_id(influencer_id, telegram_user_id)

            print("The telegram ID is: ", telegram_user_id)

            if not bubble_unique_id:
                print("Bubble unique ID not found after calling the handle function.")
                # Handle error, maybe send a message back to user
                return '', 200
                    
            stripe_subscription_id = subscription.get('id')
            subscription_plan = subscription.get('items').get('data')[0].get('plan').get('nickname')  # Adjust based on actual Stripe response structure
            status = subscription.get('status')
            current_period_start = subscription.get('current_period_start')
            current_period_end = subscription.get('current_period_end')
                    
            # Convert timestamps to readable dates
            last_billing_date = datetime.utcfromtimestamp(current_period_start).strftime('%Y-%m-%d')
            next_billing_date = datetime.utcfromtimestamp(current_period_end).strftime('%Y-%m-%d')

            # Check if a subscription already exists for the user
            existing_subscriptions = check_user_subscriptions(bubble_unique_id)  # You'll need to implement this function
            if existing_subscriptions and any(sub['status'] in ['active', 'trialing'] for sub in existing_subscriptions):
                print("User already has an active subscription.")
                message = "You already have an active subscription."
            else:
                # Add the new subscription to Bubble
                success = add_subscription(
                    bubble_unique_id, telegram_user_id, influencer_id, stripe_subscription_id,
                    subscription_plan, status, last_billing_date, next_billing_date
                )

                if success:
                    print(f"Subscription {stripe_subscription_id} added successfully")
                    message = f"Your subscription has been activated! Next billing date: {next_billing_date}."
                else:
                    print("Failed to add subscription")
                    message = "Failed to add subscription. Please contact support."

                send_telegram_message(telegram_user_id, message)
        else:
            if telegram_user_id and bubble_unique_id:
                credits_purchased = calculate_credits(session)
                amount_paid = format(session.get('amount_total') / 100, '.2f')
                currency = session.get('currency').upper()

                # Now you can update the credits in Bubble using this unique ID
                update_minutes_credits(bubble_unique_id, credits_purchased)

                message = f"Thank you for your purchase! You have successfully bought {credits_purchased} credits for {amount_paid} {currency}."

                send_telegram_message(telegram_user_id, message)
            else:
                logging.warning("Missing metadata or Bubble unique ID")
                if telegram_user_id:
                    send_telegram_message(telegram_user_id, "Something went wrong. Please contact support at admin@tryinfluencerai.com")
                else:
                    logging.error("Telegram user ID not found in session metadata.")

    # Handle successful invoice payment (renewal)
    elif event['type'] == 'invoice.payment_succeeded':
        invoice = event['data']['object']
        metadata = invoice.get('metadata', {})
        telegram_user_id = metadata.get('telegram_user_id')
        
        # Fetch next billing date from invoice
        next_billing_timestamp = invoice.get('next_payment_attempt')
        next_billing_date = datetime.utcfromtimestamp(next_billing_timestamp).strftime('%Y-%m-%d') if next_billing_timestamp else "N/A"

        message = f"Thank you for your continued subscription. Next billing date: {next_billing_date}."
        send_telegram_message(telegram_user_id, message)
    
    return '', 200
    

def send_telegram_message(telegram_user_id, message):
    send_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": telegram_user_id,
        "text": message
    }
    response = requests.post(send_url, json=payload)
    if response.status_code == 200:
        print("Message sent successfully")
    else:
        print(f"Failed to send message: {response.text}")


def calculate_credits(session):
    amount_paid = session.get('amount_total') / 100
    credits = amount_paid / 1.20
    return round(credits, 2)


if __name__ == '__main__':
    app.run(debug=True)

