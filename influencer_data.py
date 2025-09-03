from dataclasses import dataclass, field
from typing import ClassVar
from bubbledb import get_data_field
import json
from aiogram import Bot
from config import TELEGRAM_BOT_TOKENS, BUBBLE_IDS, VOICE_IDS


MAIN_PROMPT_PATH = "./influencer_files/{agent_id}/main_prompt.txt"
CHAT_INPUT_PROMPT_PATH = "./influencer_files/{agent_id}/chat_input_prompt.txt"



@dataclass
class Influencer:
    agent_id : str
    ai_name : str
    bot_username : str
    real_name : str
    voice_id : str
    voice_settings : dict
    telegram_token : str
    bubble_id : str
    credits_per_min : float
    intro_image_url : str
    bot_object : Bot
    knowledge_bases : list
    main_prompt : str = ""
    chat_input_prompt : str = ""


    _registry : ClassVar[dict] = {}


    def __post_init__(self):
        Influencer._registry[self.agent_id] = self

    def load_prompt(self):
    
        with open(MAIN_PROMPT_PATH.format(agent_id = self.agent_id)) as main_prompt_file:
            self.main_prompt = main_prompt_file.read()
        with open(CHAT_INPUT_PROMPT_PATH.format(agent_id = self.agent_id)) as chat_input_prompt_file:
            self.chat_input_prompt = chat_input_prompt_file.read()

    @classmethod
    def load_prompts(cls):
        for influencer in Influencer._registry.values():
            try:
                influencer.load_prompt()
            except:
                print("prompt not found for " + str(influencer.agent_id))

    @classmethod
    def load_voices_data(cls, voice_model_map, voice_settings_map):
        for influencer in Influencer._registry.values():
            influencer.voice_id = voice_model_map[influencer.agent_id]
            influencer.voice_settings = voice_settings_map.get(influencer.agent_id, {})

def load_influencers():
    with open("./influencer_data.json", "r") as influencer_data_json:
        influencer_data_map  : dict= json.load(influencer_data_json)
    
    for agent_id, data in influencer_data_map.items():
        try:
            # Get values from environment variables or fallback to JSON data
            token = TELEGRAM_BOT_TOKENS.get(agent_id, data.get("token"))
            bubble_id = BUBBLE_IDS.get(agent_id, data.get("bubble_id"))
            voice_id = VOICE_IDS.get(agent_id, data.get("voice_id"))
            
            Influencer(agent_id, 
                       data["ai_name"], 
                       data["bot_username"], 
                       data["real_name"], 
                       voice_id, 
                       data.get("voice_settings", {}), 
                       token,
                       bubble_id, 
                       float(get_data_field(bubble_id, "Influencer", "cost_per_min")),
                       data.get("image_url", ""),
                       Bot(token=token),
                       data.get("knowledge_bases", [])
                       )
        except:
            print("ERROR")

load_influencers()
Influencer.load_prompts()