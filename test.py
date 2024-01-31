from openai import OpenAI

client = OpenAI(api_key="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",
api_key="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")
import time

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

def create_response(chat_history: dict, text: str) -> str:

    main_prompt = '''You are an AI chatbot named Veronica that made to engage and talk with fans. You are meant to be as conversational as possible and text them as if you were a real person.
Try to continue the conversation with them and go into deep topics.'''


    
    messages = [{"role" : "system", "content" : main_prompt}]
    
    for chat in chat_history:
        messages.append(chat)

    ai_response = ""    
    for res in call_openai_stream_gpt3(messages):
        ai_response += res
    
    return ai_response


