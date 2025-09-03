from openai import OpenAI
import time
from telegram import Update
import re
import random


from aiogram import Bot, types
from influencer_data import Influencer
import vectordb
from config import OPENAI_API_KEY


client = OpenAI(api_key=OPENAI_API_KEY)

QUESTIONS = [
    "what's your favorite memory from when you were a kid",
    "what a goal you're currently working towards?",
    "so how do you deal with stress",
    "what hobbys do you have?",
    "so what's something you're passionate about",
    "so do you have any fears?",
    "what makes you happy?",
    "so are you into rock and roll?",
    "what's something about you that people might be suprised by?",
    "what's your ideal weekend?",
    "what do you like to do to end the day?",
    "i've had a bit of a long week, what do you do to recharge your batteries when you feel tired?",
    "so do you like working out or doing any sports?",
    "do you know what's been on my mind lately?",
    "do you know what i've really been wanting to do lately?",
    "What have you been up to?",
    "What do you like to do for fun?",
    "What do you like about me?",
    "What are your goals and aspirations?"
]

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


def get_chat_history(chat_history, num, last_or_first="last"):
    if last_or_first == "last":
        # Retrieve the last 2 * num messages from chat_history
        selected_messages = [msg["content"] for msg in chat_history[-2*num:]]
    elif last_or_first == "first":
        # Retrieve the first 2 * num messages from chat_history
        selected_messages = [msg["content"] for msg in chat_history[:2*num]]
    else:
        raise ValueError("last_or_first should be either 'last' or 'first'")

    # Convert the messages list to a single string with line breaks
    return '\n'.join(selected_messages)



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
    reply_array = re.split(r'(?<=[.!?])\s+(?=[A-Za-z])', ai_response)

    new_reply_array = []
    temp = ""

    for i, reply in enumerate(reply_array):

        if i == 0:
            # Store the first sentence temporarily
            temp = reply
        elif i == 1:
            # Combine the first and second sentence and add to new_reply_array
            new_reply_array.append(temp + " " + reply)
        else:
            # Remove period from string
            if("." in reply):
                reply = reply.replace(".", "")
            
            # Add remaining sentences to new_reply_array
            new_reply_array.append(reply)

    # Check if temp has a value and new_reply_array is empty, then add temp to new_reply_array
    if temp and not new_reply_array:
        if("." in temp):
            temp = temp.replace(".", "")
        new_reply_array.append(temp)

    return new_reply_array


def remove_questions(reply_array):
    num_questions = 0

    new_reply_array = []

    for reply in reply_array:
        if("?" in  reply):
            if(num_questions < 1):
                new_reply_array.append(reply)
            
            num_questions+=1
        else:
            new_reply_array.append(reply)

    return new_reply_array


def remove_emojis_except_specific(text: str) -> str:
    # List of emojis to retain
    emojis_to_keep = ['🥰', '😇', '💀', '😉']
    
    # Unicode ranges for emojis, excluding the specific ones to retain
    emoji_pattern = re.compile(
        "(?![" + "".join(re.escape(e) for e in emojis_to_keep) + "])"
        "["
        "\U0001F600-\U0001F64F"  # emoticons
        "\U0001F300-\U0001F5FF"  # symbols & pictographs
        "\U0001F680-\U0001F6FF"  # transport & map symbols
        "\U0001F700-\U0001F77F"  # alchemical symbols
        "\U0001F780-\U0001F7FF"  # Geometric Shapes Extended
        "\U0001F800-\U0001F8FF"  # Supplemental Arrows-C
        "\U0001F900-\U0001F9FF"  # Supplemental Symbols and Pictographs
        "\U0001FA00-\U0001FA6F"  # Chess Symbols
        "\U0001FA70-\U0001FAFF"  # Symbols and Pictographs Extended-A
        "\U00002702-\U000027B0"  # Dingbats
        "\U000024C2-\U0001F251" 
        "]+",
        flags=re.UNICODE,
    )
    return emoji_pattern.sub(r'', text)  # Replace emojis with an empty string

# Example usage
# text_with_emojis = "Hello, this is a test 😊👍💀😉"
# text_without_emojis = remove_emojis_except_specific(text_with_emojis)
# print(text_without_emojis)  # Output should retain 😊, 💀, and 😉 but remove others.



def improve_ai_response(ai_response, chat_history, texting_performance_str):
    main_prompt = f'''you are a girlfriend that is texting her boyfriend. your job is to improve the text message you're about to send.

edit the response you get to make sure it follows the following rules:
- reformat the response so that there's only 2 sentences in there
- there is no more than 1 emoji in your response. Do NOT add one in if there isn't one already
- given you're chat history make sure you don't sound repetitive
- have a max of 3 punctuation points in your response, remove them if there's too many
- make sure your response is short
- convert the response into lowercase
- remove any mentions of "Take Care"
- make the response flirty and get the Fan to open up
- end the response with an open-ended question to get the user talking


Avoid asking mundane questions/statements like these:
[ X "Just know that I'm here for you whenever you need me." , X "Anything else on your mind?", X "is there anything else you'd like to talk about?"]


Instead try to ask deeper questions about what the user is currently talking about, but if here are some general questions if the conversation seems to be coming to an end:
{random.sample(QUESTIONS, 3)}

This is an example of a good response: {texting_performance_str}

Here are a few example of how you should respond to the input:
Response: Oh, Travis Scott! He's got some catchy tunes. What's your favorite song of his? 🎶😊
Girlfriend: oh i love travis scott! what's your favorite song?

Response: Of course, honey. Let's take our time and enjoy getting to know each other. 😊💕
Girlfriend: of course, honey. let's take our time and enjoy getting to know each other.

Response: Oh, my day has been quite eventful, babe. I've been busy filming some new content for my channel. But now that i'm talking to you, it's definitely the highlight of my day. What about you, sweetheart. How was your day? 😊
Girlfriend: oh, my day has been quite eventful, babe, i've been busy filming some new content for my channel. but now that i'm talking to you, it's definitely the highlight of my day. what about you, sweetheart, how was your day? 😊

fr
Make sure to only return back the "Girlfriend:" respond and nothing else. You don't need to include "Girlfriend: " in your response'''

    chat_input_prompt = f'''Response: {ai_response}
Girlfriend: {chat_history}'''
    
    messages = [{"role" : "system", "content" : main_prompt}]
    
    # Get reduced chat history and write it into the messages array
    append_messages_chat_history(messages, chat_history, 300)
    
    messages.append({"role": "user", "content": chat_input_prompt})

    improved_response = ""
    for res in call_openai_stream_gpt3(messages):
        improved_response += res

    if("Influencer:" in improved_response):
        print(" 'Influencer:' key word found in response, removing it")
        improved_response = improved_response.replace("Influencer:", "")

    if("Girlfriend:" in improved_response):
        print(" 'Girlfriend:' key word found in response, removing it")
        improved_response = improved_response.replace("Girlfriend:", "")

    if("girlfriend:" in improved_response):
        print(" 'girlfriend:' key word found in response, removing it")
        improved_response = improved_response.replace("girlfriend:", "")

    if("Response:" in improved_response):
        # The AI's response is likely incorrect so return False and use original response
        return False

    return improved_response


################################################################
################## End of Helper Functions #####################
################################################################






########################################################################
################## Chatbot Response Creation Function ##################
########################################################################


def start_up_flow():
    flow_prompt = '''
    
Try to guide the conversation using the following script below. Still keep the conversation casual and respond to the user conversationally.
1. guess what i've been thinking about today?
2. it involves us, a quiet room, and very little clothing.
3. maybe i can show you better than i can tell you ## SEND IMAGE ##'''

    return flow_prompt


def chatbot_create_response(chat_history: dict, text: str, update: Update) -> str:

    user_first_name = update.message.from_user.first_name

    # Load Influencer's Knowledge base
    knowledge_kb = vectordb.load_knowledge_base("veronica_kb")

    # Load Texting Performance Base
    texing_performance_db = vectordb.load_knowledge_base("texting_performance")


    last_2_chats = get_chat_history(chat_history, 2, "last")

    texting_perf_string = vectordb.retrieve_info(texing_performance_db, last_2_chats, 2)
    knowledge_kb_string = vectordb.retrieve_info(knowledge_kb, last_2_chats, 1)

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


<Info on Veronica>
{knowledge_kb_string}
</Info on Veronica>


<example responses>
{texting_perf_string}
</example responses>

<Example Questions>
Try to ask deeper questions about what the user is currently talking about, but if here are some general questions if the conversation seems to be coming to an end:
{random.sample(QUESTIONS, 4)}
<Example Questions>


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
- Never change what is is inside ##  ##
- Whatever is inside ## is an action. For example ## SEND IMAGE ## is to send an image to the fan
- Do not say "Hey" or "Hi" ANYWHERE in your response
- Be flirty in your response and get the Fan to open up
- End the response with an open-ended question to get the user talking'''


    chat_input_prompt = '''Try to respond to the user in lowercase letters unless you are excited. And do not repeat what you previously said. Keep your response under 20 words.
Influencer: '''
    
    start_up_prompt = start_up_flow()
    chat_input_prompt = start_up_prompt + chat_input_prompt

    messages = [{"role" : "system", "content" : main_prompt}]
    

    # Get reduced chat history and write it into the messages array
    append_messages_chat_history(messages, chat_history, 300)
    
    messages.append({"role": "user", "content": chat_input_prompt})

    ai_response = ""
    for res in call_openai_stream_gpt3(messages):
        ai_response += res

    # Redo response generation if it contains "fan" - due to hallucination
    if("fan:" in ai_response.lower()):
        ai_response = ""
        for res in call_openai_stream_gpt3(messages):
            ai_response += res

        # Check 1 more time (just in case)
        if("fan:" in ai_response.lower()):
            ai_response = ""
            for res in call_openai_stream_gpt3(messages):
                ai_response += res

    
    if("Influencer:" in ai_response):
        print(" 'Influencer:' key word found in response, removing it")
        ai_response = ai_response.replace("Influencer: ", "")
    

    ## Improve the AI response using another chain of GPT-3 editing
    improved_response = improve_ai_response(ai_response, chat_history, texting_perf_string)
    

    print()
    print()
    print("ai_response: ", ai_response)
    print("improved_response: ", improved_response) 
    print()
    print()


    return remove_emojis_except_specific(improved_response.lower())

#############################################################################################################
############################# End of Chatbot Response Creation Function #####################################
#############################################################################################################






###################################################################################
###################### Voicenotes Response Creation Function ######################
###################################################################################
def voicenotes_create_response(chat_history: dict, user_transcription: str, message: types.Message, influencer : Influencer) -> str:


    main_prompt : str = influencer.main_prompt
    chat_input_prompt : str = influencer.chat_input_prompt
    user_first_name = message.from_user.first_name
    
    user_transcription = str(user_transcription)

    # Load Influencer's Knowledge base
    text_kb = vectordb.load_knowledge_base(vectordb.KB_PATH_TEMPLATE.format(agent_id = influencer.agent_id) + "/text")
    
    qa_kb = vectordb.load_knowledge_base(vectordb.KB_PATH_TEMPLATE.format(agent_id  = influencer.agent_id) + "/qa")

    

    last_2_chats = get_chat_history(chat_history, 2, "last")
    example_questions = random.sample(QUESTIONS, 4)

    text_kb_string = ""
    qa_string = ""

    if qa_kb:
        qa_string = vectordb.retrieve_info(qa_kb, last_2_chats, 2)
        print("qa found: " + str(qa_string))
    if text_kb:
        text_kb_string = vectordb.retrieve_info(text_kb, last_2_chats, 1)
        print("textkb found "  + str(text_kb_string))
    

    main_prompt = main_prompt.format(user_first_name= user_first_name, text_kb_string = text_kb_string, qa_string = qa_string, example_questions = example_questions)
    chat_input_prompt = chat_input_prompt.format(user_transcription=user_transcription)
    
    messages = [{"role" : "system", "content" : main_prompt}]
    
    # print(main_prompt)
    # Get reduced chat history and write it into the messages array
    # append_messages_chat_history(messages, chat_history, 300)
    
    
    messages.append({"role": "user", "content": chat_input_prompt})

    ai_response = ""
    for res in call_openai_stream_gpt3(messages):
        ai_response += res

    # Redo response generation if it contains "fan" - due to hallucination
    if("fan:" in ai_response.lower()):
        ai_response = ""
        for res in call_openai_stream_gpt3(messages):
            ai_response += res

    
    if("Influencer:" in ai_response):
        print(" 'Influencer:' key word found in response, removing it")
        ai_response = ai_response.replace("Influencer: ", "")
    

    ai_response = remove_emojis_except_specific(ai_response)
    print("ai_response: ", ai_response)

    return ai_response

#############################################################################################################
########################### End of Voicenotes Response Creation Function ####################################
#############################################################################################################

