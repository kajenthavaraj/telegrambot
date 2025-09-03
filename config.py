"""
Configuration module to load environment variables
"""
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# API Keys and Secrets
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
ELEVENLABS_API_KEY = os.getenv('ELEVENLABS_API_KEY')

# Telegram Bot Tokens
TELEGRAM_BOT_TOKENS = {
    'veronica_avluv': os.getenv('TELEGRAM_BOT_TOKEN_VERONICA'),
    'jasmine_larsen': os.getenv('TELEGRAM_BOT_TOKEN_JASMINE'),
    'ani_blackfox': os.getenv('TELEGRAM_BOT_TOKEN_ANI')
}

# Bubble IDs
BUBBLE_IDS = {
    'veronica_avluv': os.getenv('BUBBLE_ID_VERONICA'),
    'jasmine_larsen': os.getenv('BUBBLE_ID_JASMINE'),
    'ani_blackfox': os.getenv('BUBBLE_ID_ANI')
}

# Voice IDs
VOICE_IDS = {
    'veronica_avluv': os.getenv('VOICE_ID_VERONICA'),
    'jasmine_larsen': os.getenv('VOICE_ID_JASMINE'),
    'ani_blackfox': os.getenv('VOICE_ID_ANI')
}

def validate_config():
    """Validate that all required environment variables are set"""
    required_vars = [
        'OPENAI_API_KEY',
        'TWILIO_ACCOUNT_SID', 
        'TWILIO_AUTH_TOKEN',
        'ELEVENLABS_API_KEY',
        'TELEGRAM_BOT_TOKEN_VERONICA',
        'TELEGRAM_BOT_TOKEN_JASMINE',
        'TELEGRAM_BOT_TOKEN_ANI'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
    
    return True
