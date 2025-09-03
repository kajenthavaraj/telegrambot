
from openai import OpenAI
from config import OPENAI_API_KEY

client = OpenAI(api_key=OPENAI_API_KEY)
import time


def call_openai_stream_gpt4_turbo(messages):
    # OpenAI API key now loaded from environment variables

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



#### Helper functions ####
def verify_and_format_number(phone_number:str) -> [bool, str]:
    phone_verify_prompt = '''You're job is to verify and format if a phone number is correct.
A phone number should follow the conventional code such where it's the country code followed by the area code and rest of the number.
For example this is an example of a correct number: 16477667841
And this is an example of a wrong number: 164776678

If number is valid but is in the wrong format, reformat it and return it back. If a number is not valid, then return back INVALID. Do not include "OUTPUT" in your actual message.
These are some examples:
Input:16477667
Output: INVALID

Input: 6477667841
Output: MISSING COUNTRY CODE

Input:1416-933-221
Output: 16477667841'''

    phone_input_prompt = f'''Phone number: {phone_number}
OUTPUT: '''

    messages = [{"role" : "system", "content" : phone_verify_prompt}]
    messages.append({"role": "user", "content": phone_input_prompt})

    ai_response = ""    
    for res in call_openai_stream_gpt4_turbo(messages):
        ai_response += res
    
    print(ai_response)

    if("invalid" in ai_response.lower()):
        return False, None
    elif("missing" in ai_response.lower()):
        return False, "missing area code"
    else:
        return True, ai_response



status, reformatted_number = verify_and_format_number("+1 647-766-7841")
if(status):
    print(reformatted_number)
else:
    print("Invalid")