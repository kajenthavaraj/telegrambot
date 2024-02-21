from flask import Flask, request, abort
import stripe
import database
from typing import Final


BOT_USERNAME: Final = "@veronicaavluvaibot"

app = Flask(__name__)

@app.route('/webhook', methods=['POST'])
def stripe_webhook():
    payload = request.data
    sig_header = request.headers.get('Stripe-Signature')
    endpoint_secret = 'your_endpoint_secret'  # Replace with your actual endpoint secret

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
    except ValueError:
        # Invalid payload
        abort(400)
    except stripe.error.SignatureVerificationError:
        # Invalid signature
        abort(400)

    # Handle the event
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        telegram_user_id = session.get('metadata', {}).get('telegram_user_id')
        if telegram_user_id:
            # Now, use the telegram_user_id to send a message via your bot
            send_telegram_message(telegram_user_id, 'Thank you for completing the payment!')

    return '', 200

def send_telegram_message(telegram_user_id, message):
    # Implement function to send message via Telegram bot
    pass

if __name__ == '__main__':
    app.run(debug=True)





# # Code to update user credits
# database.update_minutes_credits(BOT_USERNAME, user_id, num_credits) #minutes credits

# database.update_chat_credits(BOT_USERNAME, user_id, num_credits) #chat credits