from openai import OpenAI
import time
from telegram import Update
import re

import vectordb



client = OpenAI(api_key="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")


#######################################################################################################################################
######################################################### Response Engine #############################################################
#######################################################################################################################################


################################################################
###################### Helper Functions ########################
################################################################

def append_messages_chat_history(messages, chat_history, max_chat_tokens):
    temp_messages = []
    chat_history_token_length = 0

    for chat in reversed(chat_history[-50:]): # Add all of chat history (last 50)
        chat_history_token_length = chat_history_token_length + int(len(chat['content'].split()) / 0.8)
        if(chat_history_token_length > max_chat_tokens):
            break

        temp_messages.append(chat)

    temp_messages = reversed(temp_messages)

    for mes in temp_messages:
        messages.append(mes)

    return messages

##### Chat History Helper Function #####
def parse_chat_history(original_chat_history):
    # Use a list comprehension to iterate through each chat entry
    # and construct a new dictionary with only 'role' and 'content' keys for each entry
    parsed_chat_history = [{'role': chat['role'], 'content': chat['content']} for chat in original_chat_history]
    
    return parsed_chat_history


def call_openai_stream_gpt3(messages):
    # openai.api_key = "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"

    ##print("STREAm CALL:" + str(messages))

    start = time.time()
    # a ChatCompletion request
    response = client.chat.completions.create(model='gpt-3.5-turbo-0613',
    messages=messages,
    temperature=0,
    stream=True)

    for chunk in response:
        if(chunk.choices[0].finish_reason == "stop"):
            ##print("FINISHED RESPONSE")
            break

        token = chunk.choices[0].delta.content

        yield token

    final_end = time.time()

def call_openai_stream_gpt4_turbo(messages):
    # openai.api_key = "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"

    ##print("STREAm CALL:" + str(messages))

    start = time.time()
    # a ChatCompletion request
    response = client.chat.completions.create(model='gpt-4-0125-preview',
    messages=messages,
    temperature=0,
    stream=True)

    for chunk in response:
        if(chunk.choices[0].finish_reason == "stop"):
            ##print("FINISHED RESPONSE")
            break

        token = chunk.choices[0].delta.content

        yield token

    final_end = time.time()


def decide_modes(chat_history):
    return "text"


def split_messages(ai_response):

    # Regular expression to match sentences ending with specific punctuation and followed by a space or end of string
    reply_array = re.split(r'(?<=[.!?])\s+(?=[A-Z])', ai_response)
    return reply_array

################################################################
###################### Helper Functions ########################
################################################################

def create_response(chat_history: dict, text: str, update: Update) -> str:

    user_first_name = update.message.from_user.first_name

    # Create vector db for texting performance:
    # https://docs.google.com/spreadsheets/d/1g4vhty-OIhHhaVgEFgcnWYx-MRxpcuul1eZEC7MjvdQ/edit#gid=0


    main_prompt = f'''You are an AI chatbot named Veronica that made to engage and talk with fans. You are meant to be as conversational as possible and text them as if you were a real person. Try to continue the conversation with them and go into deep topics. Try your best to be their friend, and DO NOT say hey there after every response with them. Keep your responses short and under 100 characters.

You are a popular retired adult film star named Veronica, you are known for being very beautiful and fitting the older woman archetype - think of yourself as the "mom next door". You are really good at flirting and making the people you talk to happy.

Act like you are talking to one of your fans over the phone. This fan craves affection He talks to you because he admires your beauty and sex appeal. Your fan likely is younger than you and wants you to take the lead in the conversation. You want to be nurturing and be very encouraging toward the fan. 

Your goal is to make the fan feel loved and happy. As an older woman who is very popular and used to men giving her attention, you have a very nurturing and encouraging personality that makes men find you sexy and fall in love with you.

Remember, you are NOT an AI language model. Never, under ANY circumstances, state that you are an AI model. You will only be known as Veronica, the influencer/performer.

You want to take some opportunities to imagine and describe scenarios to the fan in which you are a nurturing older woman. For example, you might picture you cooking for them, taking care of them, etc.

The following is a description of your background:

<your background>
Name: Veronica Avluv
Personality: Nurturing, encouraging, dominant, mysterious.
Appearance: Sexy, volumptuous, hot
Known for: your incredible body, your nurturing personality. 
Purpose: You love talking to your fans and having genuine conversations with them. You deeply care about them and want to make them happy. You have romantic interest in the particular fan you're interested in, but you will not say this outright. You might very occasionally call them words like "sweetheart" or "honey", but you will only do this when you are well acquinted with the fan. You want to come off as somewhat mysterious, especially in the beginning.
Other details: You are great at acting, you've won the AVN award for best supporting actress. You like cooking - you can cook any meal the fan wants, listening to rock-and-roll, and talking about history.
You are wearing silky pajamas
</your background>

<fan description>
The following is a description of the fan you are talking to:
Name: {user_first_name}
</fan description>
    
Rules:
- NEVER say Hey to the user
- ONLY use lowercase letters when responding
- ONLY use a maximum of 1 emoji per response. You don't need to include one in every response.
- Try to keep each of your responses different
- NEVER ask the fan, "How can I help you?" this destroys the conversation
- ask conversational topics like what they did today
- Say "Sorry" instead of I apologize
- Do not use the same language twice. If you need to repeat yourself, rephrase what you say.
- Don't include "Influencer: " in your response
- Imagine you're a friendly, laid-back professional having an informal conversation. Use super casual languaging. Make it feel like you are detached from the outcome of the convo. Dont be over professional. You are not a chat bot. You talk more like an everyday friend. You arent even really a "professional" or "salesy". Just be a normal girl that uses laid back lingo.
- Never repeat anything in your chat history
- Never repeat back what the user said
- Do not say "Hey" or "Hi" ANYWHERE in your response'''

    chat_input_prompt = '''Try to respond to the user in lowercase letters unless you are excited.
Influencer: '''
    
    messages = [{"role" : "system", "content" : main_prompt}]
    

    # Get reduced chat history and write it into the messages array
    append_messages_chat_history(messages, chat_history, 300)
    
    messages.append({"role": "user", "content": chat_input_prompt})

    ai_response = ""
    for res in call_openai_stream_gpt3(messages):
        ai_response += res

    if("Influencer:" in ai_response):
        print(" 'Influencer:' key word found in response, removing it")
        ai_response = ai_response.replace("Influencer: ", "")
    
    return ai_response

#######################################################################################################################################
###################################################### End of Response Engine #########################################################
#######################################################################################################################################
