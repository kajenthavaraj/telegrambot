from elevenlabs import clone, generate, play, set_api_key, stream, Voice, VoiceSettings
import shutil
import subprocess
from typing import Iterator

from queue import Queue
import time
import io
import base64
import pathlib
import base64
import requests
import json
from pydub import AudioSegment
import random
import os



AGENT_ID = "veronica"


# sudo apt update
# sudo apt install ffmpeg


with open("voice_model_map.json", "r") as file:
    voice_model_map = json.load(file)

with open("voice_settings_map.json", "r") as file:
    voice_settings_map = json.load(file)


def get_audio_data(
    text: str, agent_id, chunk_size=3004, model="eleven_multilingual_v2"
):
    text = text.strip(",")
    voice = voice_model_map[agent_id]
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice}/stream"

    # print("similarity " + str(voice_settings_map.get(self.voicestatus.agent_id, {}).get("similarity_boost", 50)))
    # print("stability: " + str(voice_settings_map.get(self.voicestatus.agent_id, {}).get("stability", 50)))
    querystring = {"output_format": "mp3_44100_128"}
    payload = {
        "model_id": model,
        "text": text,
        "voice_settings": {
            "similarity_boost": voice_settings_map.get(agent_id, {}).get(
                "similarity_boost", 0.4
            ),
            "stability": voice_settings_map.get(agent_id, {}).get("stability", 0.7),
        },
    }
    from config import ELEVENLABS_API_KEY
    headers = {
        "xi-api-key": ELEVENLABS_API_KEY,
        "Content-Type": "application/json",
    }

    audio = requests.request(
        "POST", url, json=payload, headers=headers, params=querystring
    )
    # audio = generate(text=text, voice=voice, stream=True, latency=4, stream_chunk_size=chunk_size, model=model, )
    # print(audio.text)

    for chunk in audio.iter_content(chunk_size=chunk_size):
        if chunk:
            # print(len(chunk))
            yield chunk


def get_completed_audio(text, model="eleven_multilingual_v2"):
    gen = get_audio_data(text=text, agent_id=AGENT_ID, chunk_size=3004, model=model)
    complete_audio_bytes = b""
    complete_audio = b""

    for chunk in gen:
        complete_audio_bytes += chunk

    return complete_audio_bytes


def send_voice_note(ai_response: str) -> None:
    # This will send the 'recording audio' action to the chat
    # await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.RECORD_AUDIO)

    # Generate audio from the transcribed text
    audio_bytes = get_completed_audio(ai_response)  # Use your actual agent ID

    # Save the generated audio to a file
    audio_file_path = f"tts_output.mp3"
    with open(audio_file_path, 'wb') as audio_file:
        audio_file.write(audio_bytes)

    # # Send the audio file as a voice note
    # with open(audio_file_path, 'rb') as audio_file:
    #     await update.message.reply_voice(voice=InputFile(audio_file, filename=audio_file_path))

    # Delete the generated audio file after sending it
    # os.remove(audio_file_path)


send_voice_note("Hey there how are you doing today?")