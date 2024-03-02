import response_engine




def start_up_flow():
    flow_prompt = '''
    
Try to guide the conversation using the following script below. Still keep the conversation casual and respond to the user conversationally.
1. guess what i've been thinking about today?
2. it involves us, a quiet room, and very little clothing.
3. maybe i can show you better than i can tell you ## SEND IMAGE ##

'''

    return flow_prompt