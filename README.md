# Telegram Bot - Environment Setup

This project uses environment variables to manage API keys and sensitive configuration data securely.

## Setup Instructions

1. **Copy the environment template:**
   ```bash
   cp .env.example .env
   ```

2. **Fill in your actual API keys and tokens in the `.env` file:**
   
   ### Required API Keys:
   - **OpenAI API Key**: Get from https://platform.openai.com/api-keys
   - **Twilio Credentials**: Get from https://console.twilio.com/
   - **ElevenLabs API Key**: Get from https://elevenlabs.io/
   - **Telegram Bot Tokens**: Create bots via @BotFather on Telegram
   - **Stripe API Keys**: Get from https://dashboard.stripe.com/apikeys
   - **Stripe Webhook Secrets**: Get from https://dashboard.stripe.com/webhooks
   - **Bubble API Token**: Get from your Bubble.io app settings
   
   ### Configuration Values:
   - **Bubble IDs**: Internal system identifiers
   - **Voice IDs**: ElevenLabs voice model identifiers

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application:**
   ```bash
   python main.py
   ```

## Security Notes

- **Never commit the `.env` file** to version control
- The `.env` file is already added to `.gitignore`
- Use `.env.example` as a template for required variables
- Keep your API keys secure and rotate them regularly

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `OPENAI_API_KEY` | OpenAI API key for AI responses | Yes |
| `TWILIO_ACCOUNT_SID` | Twilio account SID for SMS | Yes |
| `TWILIO_AUTH_TOKEN` | Twilio auth token for SMS | Yes |
| `ELEVENLABS_API_KEY` | ElevenLabs API key for voice synthesis | Yes |
| `TELEGRAM_BOT_TOKEN_VERONICA` | Telegram bot token for Veronica | Yes |
| `TELEGRAM_BOT_TOKEN_JASMINE` | Telegram bot token for Jasmine | Yes |
| `TELEGRAM_BOT_TOKEN_ANI` | Telegram bot token for Ani | Yes |
| `BUBBLE_ID_VERONICA` | Bubble database ID for Veronica | Yes |
| `BUBBLE_ID_JASMINE` | Bubble database ID for Jasmine | Yes |
| `BUBBLE_ID_ANI` | Bubble database ID for Ani | Yes |
| `VOICE_ID_VERONICA` | ElevenLabs voice ID for Veronica | Yes |
| `VOICE_ID_JASMINE` | ElevenLabs voice ID for Jasmine | Yes |
| `VOICE_ID_ANI` | ElevenLabs voice ID for Ani | Yes |
| `STRIPE_SECRET_KEY_LIVE` | Stripe live secret key | No* |
| `STRIPE_SECRET_KEY_TEST` | Stripe test secret key | Yes |
| `STRIPE_WEBHOOK_SECRET_LIVE` | Stripe live webhook endpoint secret | No* |
| `STRIPE_WEBHOOK_SECRET_TEST` | Stripe test webhook endpoint secret | Yes |
| `STRIPE_ENV` | Stripe environment ('test' or 'live') | No |
| `BUBBLE_API_TOKEN` | Bubble.io API token for database access | Yes |

*Required only if using live Stripe environment

## Configuration Validation

The application automatically validates that all required environment variables are set on startup. If any are missing, it will display an error message listing the missing variables.

## Migration from Hardcoded Values

This project has been updated to use environment variables instead of hardcoded API keys for security. The following files were updated:

- `config.py` - Central configuration management
- `loginuser.py` - Twilio credentials
- `voicenoteHandler.py` - OpenAI API key
- `elevenlabsTTS.py` - ElevenLabs API key
- `response_engine.py` - OpenAI API key
- `vectordb.py` - OpenAI API key
- `influencer_data.py` - Telegram tokens and IDs
- `main.py` - Configuration validation
- `paymentstest.py` - Stripe API key
- `app.py` - Stripe API key, webhook secrets, and Bubble API token
- `tests/testbot.py` - Stripe API key and Telegram bot token
- `requirements.txt` - Added python-dotenv dependency
