from flask import Flask, request, abort
import stripe
import requests
from typing import Final
from connectBubble import update_minutes_credits, update_chat_credits
from database import get_bubble_unique_id
import CONSTANTS

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
        
        # Assume you have telegram_user_id and influencer_id in metadata
        metadata = session.get('metadata', {})
        telegram_user_id = metadata.get('telegram_user_id')
        influencer_id = CONSTANTS.BOT_USERNAME # Example; adjust as needed

        if telegram_user_id:
            credits_purchased = calculate_credits(session)

            message = f"Thank you for your purchase! You have successfully bought {credits_purchased} credits"
            send_telegram_message(telegram_user_id, message)
        else:
            print("Telegram user ID not found in session metadata.")
        
        print(f"Attempting to retrieve Bubble unique ID for Telegram user ID: {telegram_user_id} and Influencer ID: {influencer_id}")
        bubble_unique_id = get_bubble_unique_id(influencer_id, telegram_user_id)
    
        #bubble_unique_id = '1705089991492x506710590267403400'
        
        if bubble_unique_id:
            credits_purchased = calculate_credits(session)

            # Now you can update the credits in Bubble using this unique ID
            update_minutes_credits(bubble_unique_id, credits_purchased)
            # Send confirmation message to Telegram
            send_telegram_message(telegram_user_id, "Your purchase was successful!")
        else:
            # Handle case where the unique Bubble ID couldn't be retrieved
            print("Failed to retrieve Bubble unique ID")

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


def update_credits_in_bubble(user_id, credits):
    url = f"{BUBBLE_API_URL}/{user_id}"  # URL to the specific user object in Bubble
    headers = {
        "Authorization": f"Bearer {BUBBLE_API_TOKEN}",
        "Content-Type": "application/json"
    }
    data = {"credits": credits}  # Assuming 'credits' is the field to update
    response = requests.patch(url, json=data, headers=headers)
    return response.status_code == 200


def calculate_credits(session):
    amount_paid = session.get('amount_total') / 100
    credits = amount_paid / 1.20
    return round(credits, 2)


if __name__ == '__main__':
    app.run(debug=True)

