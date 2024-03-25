from typing import Final

# from telegram.ext import Application, MessageHandler, filters, ContextTypes
# from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup, InputFile, Bot
# from telegram.constants import ChatAction

from aiogram import Bot, types
from aiogram.types import InputFile
from aiogram.methods.send_voice import SendVoice

import requests
import asyncio
import json
import time
import os
from pydub import AudioSegment
import subprocess

from openai import OpenAI

import response_engine
import database
import elevenlabsTTS
import connectBubble
from influencer_data import Influencer

async def download_file(url: str, path: str):
    response = requests.get(url)
    with open(path, 'wb') as f:
        f.write(response.content)


def transcribe_audio_file(audio_file_path):
    client = OpenAI(api_key="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")

    with open(audio_file_path, "rb") as audio_file:
        transcript = client.audio.transcriptions.create(model="whisper-1", file=audio_file)

        print("transcript")
        print(transcript)

        # Assuming 'transcript' object has a 'text' attribute or similar to access the transcription
        extracted_text = transcript.text  # Modify this line according to how you can access the text in the 'transcript' object

    return extracted_text


# async def send_voice_note(message: types.Message):
#     result = await bot.send_voice(
#         chat_id=message.chat.id,
#         voice="PATH_TO_YOUR_VOICE_FILE_OR_FILE_ID",
#         caption="Your optional caption here",
#         parse_mode="Markdown",
#     )
#     print(result)


# Get the length of an audio file in minutes
def get_audio_duration(audio_file_path):
    # Load the audio file
    audio = AudioSegment.from_file(audio_file_path)
    
    # Calculate the duration in minutes
    duration_seconds = len(audio) / 1000  # pydub calculates in millisec
    duration_minutes = duration_seconds / 60
    
    return duration_minutes



async def send_voice_note(message: types.Message, ai_response: str, unique_id : str, influencer : Influencer) -> None:
    # This will send the 'recording audio' action to the chat
    chat_id = message.chat.id
    action_url = f"https://api.telegram.org/bot{influencer.telegram_token}/sendChatAction"
    action_data = {
        'chat_id': chat_id,
        'action': 'record_voice'
    }
    response = requests.post(action_url, data=action_data)



    # Generate audio from the transcribed text
    audio_bytes = elevenlabsTTS.get_completed_audio(ai_response, influencer)

    # Save the generated audio to a file
    audio_file_path = f"tts_output_{message.message_id}.mp3"
    with open(audio_file_path, 'wb') as audio_file:
        audio_file.write(audio_bytes)

    # voice = InputFile(audio_file_path)
    url = f"https://api.telegram.org/bot{influencer.telegram_token}/sendVoice"

    # Open the audio file in binary mode
    with open(audio_file_path, 'rb') as audio:
        files = {'voice': audio}
        data = {'chat_id': message.chat.id}
        # Make the request
        response = requests.post(url, files=files, data=data)

    # Check response
    print(response.text)

    ##### Remove credits from user ####
    # Find how long audio file it
    duration_minutes = get_audio_duration(audio_file_path)
    print("duration_minutes: ", duration_minutes)
    
    # Check if type of duration_minutes is valid, and then remove the credits from the user
    if (isinstance(duration_minutes, float) or isinstance(duration_minutes, int)):
        connectBubble.deduct_minutes_credits(unique_id, -duration_minutes)

    # Delete the generated audio file after sending it
    os.remove(audio_file_path)




async def transcribe_user_voice_note(message: types.Message, bot : Bot) -> str:
    user_id = str(message.from_user.id)
    
    voice_note = message.voice
    file = await bot.get_file(voice_note.file_id)
    file_path = f"voice_note_{message.message_id}.ogg"  # Telegram voice notes are in .ogg format
    
    # Download the voice note file
    await bot.download_file(file.file_path, file_path)

    # Transcribe the voice note using Whisper API
    transcription = transcribe_audio_file(file_path)

    # Delete the file after transcription
    os.remove(file_path)

    return transcription


async def voice_note_creator(message: types.Message, text:str, unique_id : str, influencer : Influencer) -> None:
    user_id = str(message.from_user.id)



    # Add the current message to the user's chat history
    database.add_chat_to_user_history(influencer.bot_username, user_id, "user", "Fan: " + text)

    # Retrieve the updated chat history
    chat_history = database.get_user_chat_history(influencer.bot_username, user_id)
    # Format the chat history for display
    parsed_chat_history = response_engine.parse_chat_history(chat_history)


    # Generate response using Response Engine
    ai_response = response_engine.voicenotes_create_response(parsed_chat_history, text, message, influencer)
    print("ai_response: ", ai_response)

    ## Add the AI response to user's chat history
    database.add_chat_to_user_history(influencer.bot_username, user_id, "agent", "Girlfriend: " + ai_response)

    await send_voice_note(message, ai_response, unique_id, influencer)



# def main():
#     application = Application.builder().token(TOKEN).build() 
#     application.add_handler(MessageHandler(filters.VOICE, voice_note_creator))

#     print("Polling...")
#     application.run_polling()

# if __name__ == "__main__":
#     main()
