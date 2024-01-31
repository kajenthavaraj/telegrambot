
from openai import OpenAI

client = OpenAI(api_key="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")
import time
import boto3
import json
import random
import re


api_key = "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"



urls = ['https://www.linkedin.com/in/raecountingsolutions/']

AWS_ACCESS_KEY_ID = 'AKIAU6WY5LPTAERRPHUX'
AWS_SECRET_ACCESS_KEY = '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'
REGION_NAME = 'us-east-1'

def get_claude_stream(prompt, message_history = [], model = "v2"):

    start = time.time()

    message_str : str = "\n\nHuman: " + prompt

    for message in message_history:

        if message["role"] == "user":
            message_str += "\n\nHuman: " + message["content"]
        else:
            message_str += "\n\nAssistant: " + message["content"]

    message_str += "\n\nAssistant: "

    print(message_str)


    print("FORMAT: " + str(time.time() - start))

    boto3.setup_default_session(aws_access_key_id=AWS_ACCESS_KEY_ID,
                                aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
                                region_name=REGION_NAME)

    bedrock = boto3.client(service_name='bedrock-runtime')

    body = json.dumps({
        "prompt": message_str,
        "max_tokens_to_sample": 2000,
        "temperature": 0,
        "top_p": 0.9,
    })

    if model == "v2":
        modelId = 'anthropic.claude-v2'
    else:
        modelId = 'anthropic.claude-instant-v1'
    accept = 'application/json'
    contentType = 'application/json'

    # stream the response to client
    response = bedrock.invoke_model_with_response_stream(body=body, modelId=modelId, accept=accept, contentType=contentType)


    event_stream = response.body

    print("response finished: " + str(time.time() - start))

    return event_stream

def get_openai_stream(model, prompt, message_history = []):

    print("start")
    if model == "gpt-3.5-turbo" or model == "gpt-4-1106-preview":
        messages : list = message_history
        

        if len(message_history) > 15:
            messages = messages[-14:]

        messages.insert(0, {"role" : "system", "content" : prompt})


        
        response = client.chat.completions.create(stream = True, model=model, messages=messages)
    else:
        response = client.completions.create(stream = True, model=model, prompt=prompt)
    
    print("respinsegen")
    return response




