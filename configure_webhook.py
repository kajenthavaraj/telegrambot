from influencer_data import Influencer
import requests

# Put your NGROK url here, will replace with heroku url later
DOMAIN = "https://4ff9-138-51-65-10.ngrok-free.app"
SET_WEBHOOK_URL_TEMPLATE = "https://api.telegram.org/bot{token}/setWebhook?url={domain}/webhook/{influencer_id}"



for agent_id, influencer in Influencer._registry.items():
    set_webhook_url = SET_WEBHOOK_URL_TEMPLATE.format(token = influencer.telegram_token, domain = DOMAIN, influencer_id = agent_id)
    response = requests.post(set_webhook_url)
    print(response)