from flask import Flask, request, abort
import stripe
import requests
from typing import Final
# from database import update_chat_credits


# Flask app setup
app = Flask(__name__)

# Stripe setup
stripe.api_key = "sk_test_51IsqDJBo1ZNr3GjAvWVMXtJUnocMO3LsOBaZKJIwtKcAd6regW0OrOgLGrjldgvMmS3K6PW3q4rkTDIbWb3VCUm00072rgmWbe"  

# endpoint_secret = 'whsec_TRS246LG1aQG1tsWzW2D0hYLFZYqWwja'  # this is the live version

endpoint_secret = 'whsec_xtHqX4aEuAlh8kYH8Wcp90sQeENaUS52' # this is the test version


# Telegram setup
BOT_TOKEN = "6736028246:AAGbbsnfYsBJ1y-Fo0jO4j0c9WBuLxGDFKk"  
BOT_USERNAME: Final = "@veronicaavluvaibot"

# Bubble setup
BUBBLE_API_URL = "https://app.tryinfluencerai.com/api/1.1/obj/"  
BUBBLE_API_TOKEN = "7bfc4e7b2cfbd0475b1ec923a0ea4c99"  

@app.route('/webhook', methods=['POST'])
def stripe_webhook():
    payload = request.get_data(as_text=True)  
    sig_header = request.headers.get('Stripe-Signature')
    print(f"Received Stripe-Signature: {sig_header}")


    try:
        event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
    except ValueError as e:
        print(f"ValueError: {e}")
        abort(400)
    except stripe.error.SignatureVerificationError as e:
        print(f"SignatureVerificationError: {e}")
        abort(400)

    # Handle successful checkout session completion
    # if event['type'] == 'checkout.session.completed':
    #     session = event['data']['object']
        
    #     telegram_user_id = session.get('metadata', {}).get('telegram_user_id')
    #     # Assume influencer_id is also part of the metadata or determine how to set it
    #     influencer_id = 'veronicaavluvaibot'
    #     credits_purchased = calculate_credits(session)
        
    #     # Update credits in Firebase
    #     update_chat_credits(influencer_id, telegram_user_id, credits_purchased)
        
    #     # Optionally, update credits in Bubble and notify the user via Telegram
    #     # if update_credits_in_bubble(bubble_user_id, credits_purchased):
    #     send_telegram_message(telegram_user_id, 'Thank you for your purchase! Your credits have been updated.')

    print(f"Processed event id={event['id']} type={event['type']}")
    return '', 200


def send_telegram_message(telegram_user_id, message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": telegram_user_id,
        "text": message
    }
    requests.post(url, json=payload)


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
    # Placeholder function to calculate credits based on session details
    # Customize this based on your own logic
    return 5  # Example static return, replace with your logic


if __name__ == '__main__':
    app.run(debug=True)

