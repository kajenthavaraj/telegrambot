import elevenlabsTTS
import CONSTANTS


ai_response = "My day is going great now that I'm talking to you. How about you, how's your day?"

audio_bytes = elevenlabsTTS.get_completed_audio(ai_response, CONSTANTS.AGENT_ID)

audio_file_path = f"tts_output.mp3"
with open(audio_file_path, 'wb') as audio_file:
    audio_file.write(audio_bytes)