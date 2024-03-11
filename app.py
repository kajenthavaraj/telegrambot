from flask import Flask, request, abort
import stripe
import requests
from typing import Final
from connectBubble import update_minutes_credits, update_subscription, check_user_subscription
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
        influencer_UID = CONSTANTS.INFLUENCER_UID 
        bubble_unique_id = get_bubble_unique_id(influencer_id, telegram_user_id)
        print("the influencer id is: ", influencer_id)
        print ("the bubble unique id is: ", bubble_unique_id, "the telegram user id is: ", telegram_user_id)
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
            subscription_id = session.get('subscription')

            print("The telegram ID is: ", telegram_user_id)
                    
            stripe_subscription_id = session.get('subscription') 

            amount_paid = format(session.get('amount_total') / 100, '.2f')
            
            print("The amount paid is: ", amount_paid)

            if amount_paid == '24.99':
                subscription_plan = 'Monthly'
            elif amount_paid == '249.00':
                subscription_plan = 'Yearly'
            else:
                subscription_plan = 'Unknown Plan'

            status = subscription.get('status')


            if subscription_id:
                print("Fetching subscription details for:", subscription_id)
                subscription = stripe.Subscription.retrieve(subscription_id)

                current_period_start = subscription['current_period_start']
                current_period_end = subscription['current_period_end']
                print(f"Current Period Start (UNIX): {current_period_start}, Current Period End (UNIX): {current_period_end}")


                # Check if current_period_start and current_period_end are not None before converting
                if current_period_start is not None and current_period_end is not None:
                    last_billing_date = datetime.utcfromtimestamp(current_period_start).strftime('%Y-%m-%d')
                    next_billing_date = datetime.utcfromtimestamp(current_period_end).strftime('%Y-%m-%d')
                    print(f"Last billing: {last_billing_date}, Next billing: {next_billing_date}")

                else:   
                    current_date = datetime.utcnow().strftime('%Y-%m-%d')
                    last_billing_date = current_date
                    next_billing_date = current_date

                
            # Check if a subscription already exists for the user
            has_active_subscription, subscription_status = check_user_subscription(bubble_unique_id, influencer_UID)

            if has_active_subscription and subscription_status == "complete":
                print("User already has an active subscription.")
                message = "You already have an active subscription."

            elif has_active_subscription and subscription_status != "complete":
                print("User has a subscription that is not active.")
                # Here you could prompt the user to reactivate their subscription or handle accordingly.
                message = "Your subscription is currently not active. Would you like to reactivate it?"

            else:
                # Add the new subscription to Bubble
                print("Influencer: ", influencer_UID, " bubble unique id: ", bubble_unique_id)
                success = update_subscription(
                    bubble_unique_id, telegram_user_id, influencer_UID, stripe_subscription_id,
                    subscription_plan, status, last_billing_date, next_billing_date, amount_paid
                )

                # ADD SOME CODE HERE FOR APPENDING THE PAYMENT DETAILS

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

                charge_id = session.get('id')  # Assuming the charge ID is stored in the session object
                print("The charge id is: ", charge_id)
                influencer_attribution = influencer_UID
                paid_status = "Paid" 

                # Now you can update the credits in Bubble using this unique ID
                success = update_minutes_credits(bubble_unique_id, credits_purchased, amount_paid, charge_id, influencer_attribution, paid_status)

                if success:
                    message = f"Thank you for your purchase! You have successfully bought {credits_purchased} credits for {amount_paid} {currency}."
                else:
                    message = "There was an issue processing your purchase. Please contact support."
                
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

