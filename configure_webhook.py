from influencer_data import Influencer
import requests

# Put your NGROK url here, will replace with heroku url later
DOMAIN = "https://szfrq9g2-8080.use.devtunnels.ms"
SET_WEBHOOK_URL_TEMPLATE = "https://api.telegram.org/bot{token}/setWebhook?url={domain}/webhook/{influencer_id}"



for agent_id, influencer in Influencer._registry.items():
    set_webhook_url = SET_WEBHOOK_URL_TEMPLATE.format(token = influencer.telegram_token, domain = DOMAIN, influencer_id = agent_id)
    response = requests.post(set_webhook_url)
    print(response)