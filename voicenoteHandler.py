from typing import Final

from telegram.ext import Application, MessageHandler, filters, ContextTypes
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
from telegram.constants import ChatAction

import requests
import asyncio
import json
import time
import os

from openai import OpenAI

import voicenote_response_engine as vn_response_engine
import database
import elevenlabsTTS

import CONSTANTS


TOKEN: Final = "6736028246:AAGbbsnfYsBJ1y-Fo0jO4j0c9WBuLxGDFKk"
BOT_USERNAME: Final = "@veronicaavluvaibot"

async def download_file(url: str, path: str):
    response = requests.get(url)
    with open(path, 'wb') as f:
        f.write(response.content)


def transcribe_audio(audio_file_path):
    client = OpenAI(api_key="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")

    with open(audio_file_path, "rb") as audio_file:
        transcript = client.audio.transcriptions.create(model="whisper-1", file=audio_file)

        print("transcript")
        print(transcript)

        # Assuming 'transcript' object has a 'text' attribute or similar to access the transcription
        extracted_text = transcript.text  # Modify this line according to how you can access the text in the 'transcript' object

    return extracted_text



async def send_voice_note(update: Update, context: ContextTypes.DEFAULT_TYPE, ai_response: str) -> None:
    # This will send the 'recording audio' action to the chat
    # await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.RECORD_AUDIO)

    # Generate audio from the transcribed text
    audio_bytes = elevenlabsTTS.get_completed_audio(ai_response, CONSTANTS.AGENT_ID)  # Use your actual agent ID

    # Save the generated audio to a file
    audio_file_path = f"tts_output_{update.message.message_id}.mp3"
    with open(audio_file_path, 'wb') as audio_file:
        audio_file.write(audio_bytes)

    # Send the audio file as a voice note
    with open(audio_file_path, 'rb') as audio_file:
        await update.message.reply_voice(voice=InputFile(audio_file, filename=audio_file_path))

    # Delete the generated audio file after sending it
    os.remove(audio_file_path)



async def voice_note_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = str(update.message.from_user.id)
    
    voice_note = update.message.voice
    file = await context.bot.get_file(voice_note.file_id)
    file_path = f"voice_note_{update.message.message_id}.ogg"  # Telegram voice notes are in .ogg format
    
    # Download the voice note file
    await download_file(file.file_path, file_path)

    # Transcribe the voice note using Whisper API
    transcription = transcribe_audio(file_path)

    # Delete the file after transcription
    os.remove(file_path)

    
    ######### Send the voice note #########
    # will need to add logic for whether to send a text message or not

    # Add the current message to the user's chat history
    database.add_chat_to_user_history(BOT_USERNAME, user_id, "user", "Fan: " + transcription)

    # Retrieve the updated chat history
    chat_history = database.get_user_chat_history(BOT_USERNAME, user_id)
    # Format the chat history for display
    parsed_chat_history = vn_response_engine.parse_chat_history(chat_history)


    # Generate response using Response Engine
    ai_response = vn_response_engine.create_response(parsed_chat_history, transcription, update)
    # print("ai_response: ", ai_response)


    await send_voice_note(update, context, ai_response)



def main():
    application = Application.builder().token(TOKEN).build() 
    application.add_handler(MessageHandler(filters.VOICE, voice_note_handler))

    print("Polling...")
    application.run_polling()

if __name__ == "__main__":
    main()
