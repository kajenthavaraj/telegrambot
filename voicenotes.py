from elevenlabs import clone, generate, play, set_api_key, stream, Voice, VoiceSettings
import shutil
import subprocess
from typing import Iterator
from pydub import AudioSegment

from queue import Queue
import time
import io
import numpy as np
import audioop
import base64
import pathlib
import base64
import requests
import json

with open("voice_model_map.json", "r") as file:
    voice_model_map = json.load(file)

with open("voice_settings_map.json", "r") as file:
    voice_settings_map = json.load(file)

def get_audio_data(self, text : str, agent_id, chunk_size = 3004, model = "eleven_multilingual_v2"):
    
    text = text.strip(",")

    voice = voice_model_map[agent_id]

    
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice}/stream"

    # print("similarity " + str(voice_settings_map.get(self.voicestatus.agent_id, {}).get("similarity_boost", 50)))
    # print("stability: " + str(voice_settings_map.get(self.voicestatus.agent_id, {}).get("stability", 50)))
    querystring = {"output_format":"mp3_44100_128"}
    payload = {
        "model_id": model,
        "text": text,
        "voice_settings": {
            "similarity_boost": voice_settings_map.get(agent_id, {}).get("similarity_boost", 0.4),
            "stability": voice_settings_map.get(agent_id, {}).get("stability",0.7),
        }
    }
    headers = {
        "xi-api-key": "827435e41a0abb6bdad7ea666024dd86",
        "Content-Type": "application/json"
    }

    audio = requests.request("POST", url, json=payload, headers=headers, params=querystring)
    # audio = generate(text=text, voice=voice, stream=True, latency=4, stream_chunk_size=chunk_size, model=model, )
    # print(audio.text)

    for chunk in audio.iter_content(chunk_size=chunk_size):
        if chunk:
            # print(len(chunk))
            yield chunk

def get_completed_audio(self, text, model="eleven_multilingual_v2"):
    gen = get_audio_data(text, model=model)
    complete_audio_bytes = b""
    complete_audio = b""

    for chunk in gen:
        complete_audio_bytes += chunk

        
    return complete_audio_bytes