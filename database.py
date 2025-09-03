import firebase_admin
from firebase_admin import credentials, firestore
from firebase_admin.firestore import ArrayUnion, SERVER_TIMESTAMP
from datetime import datetime
import pytz
import time


import bubbledb
import connectBubble
# Check if the default Firebase app has already been initialized
if not firebase_admin._apps:
    KEYPATH = 'telegrambot-d6553-firebase-adminsdk-ruf4v-91d571bca9.json'
    cred = credentials.Certificate(KEYPATH)
    firebase_admin.initialize_app(cred)

db = firestore.client()


# Function to  create a new influencer collection
def create_influencer_collection(influencer_id, influencer_name):
    influencer_data = {
        'name': influencer_name,
    }

    
    db.collection('influencers').document(influencer_id).set(influencer_data)
    # print(f"Influencer {influencer_name} with ID {influencer_id} has been added to the database.")

# Example usage
# create_influencer_collection(influencer_id='botid', influencer_name='Influencer')


def check_user_exists(influencer_id, user_id):
    # Create a reference to the influencer's subscription collection and the specific user document
    user_subscription_ref = db.collection('influencers').document(influencer_id).collection('subscriptions').document(user_id)

    # Attempt to get the user document
    user_subscription_doc = user_subscription_ref.get()

    # Check if the document exists
    if user_subscription_doc.exists:
        return True  # The user exists in the database
    else:
        return False  # The user does not exist in the database


# Function to add user to an influencers subscriptions
def add_user_to_influencer_subscription(influencer_id, user_id):
    # Create a reference to the influencer's subscription collection
    subscriptions_ref = db.collection('influencers').document(influencer_id).collection('subscriptions')

    # Check if the user is already subscribed to avoid duplicate entries
    user_subscription = subscriptions_ref.document(user_id).get()
    if user_subscription.exists:
        # print(f"User {user_id} is already subscribed to influencer {influencer_id}.")
        return

    # Add the user to the influencer's subscriptions with initial empty chat history
    subscriptions_ref.document(user_id).set({
        'user_id': user_id,
        'subscribed_on': SERVER_TIMESTAMP,
        'chat_history': []  # Initialize an empty chat history
    })
    # print(f"User {user_id} has been added to the subscriptions of influencer {influencer_id}.")

# Example usage
# add_user_to_influencer_subscription('botid', 'user12345')



# Function to add to chat history
def add_chat_to_user_history(influencer_id, user_id, role, content):
    # Reference to the specific subscription document of the user under the influencer
    user_subscription_ref = db.collection('influencers').document(influencer_id).collection('subscriptions').document(user_id)

    utc_now = datetime.utcnow().replace(tzinfo=pytz.utc)

    # Define the chat entry structure with 'role' and 'content'
    chat_entry = {
        'role': role,  # 'user' or 'agent'
        'content': content,
        'timestamp': utc_now
    }

    # Use the ArrayUnion operation to append the new chat entry to the existing chat history array
    # This ensures that the chat entry is added without needing to read the document first
    user_subscription_ref.update({
        'chat_history': ArrayUnion([chat_entry])
    })
    # print(f"Added chat message to history for {role} in conversation with user {user_id} under influencer {influencer_id}.")

# Example usage
# add_chat_to_user_history('botid', 'user12345', 'user', 'Hello, how are you?')
# add_chat_to_user_history('botid', 'user12345', 'agent', "I'm good, thanks for asking!")



def get_user_chat_history(influencer_id, user_id):
    # Reference to the specific subscription document of the user under the influencer
    user_subscription_ref = db.collection('influencers').document(influencer_id).collection('subscriptions').document(user_id)

    # Attempt to get the subscription document
    user_subscription_doc = user_subscription_ref.get()

    # Check if the document exists
    if user_subscription_doc.exists:
        # Extract the chat history
        chat_history = user_subscription_doc.to_dict().get('chat_history', [])
        # print(f"Chat history for user {user_id} under influencer {influencer_id}:")
        # for chat in chat_history:
        #     print(f"Role: {chat['role']}, Content: {chat['content']}, Timestamp: {chat['timestamp']}")
        return chat_history
    else:
        # print(f"No subscription found for user {user_id} under influencer {influencer_id}.")
        return None

# Example usage
# chat_history = get_user_chat_history('botid', 'user12345')
# if(chat_history == None):
#     print("NO CHAT HISTORY FOR USER")
# else:
#     chat_history_str = '\n'.join(f"{chat['role']}: {chat['content']}" for chat in chat_history)
#     print(chat_history_str)


def store_user_phone_number(influencer_id, user_id, phone_number):
    subscriptions_ref = db.collection('influencers').document(influencer_id).collection('subscriptions').document(user_id)
    
    # Update the document with the user's phone number, creating the document if it does not exist
    subscriptions_ref.set({'phone_number': phone_number}, merge=True)
    # print(f"Stored phone number {phone_number} for user {user_id} under influencer {influencer_id}.")

def set_user_intro_status(influencer_id, user_id, status):
    subscription_ref = db.collection('influencers').document(influencer_id).collection('subscriptions').document(user_id)
    subscription_ref.update({"intro_status" : status})

def get_user_intro_status(influencer_id, user_id):
    subscription_ref = db.collection('influencers').document(influencer_id).collection('subscriptions').document(user_id)
    doc = subscription_ref.get()
    return doc.to_dict().get("intro_status")


# Example usage
# store_user_phone_number('botid', 'user12345', '6477667841')



def phone_number_status(influencer_id, user_id):

    # Reference to the user's subscription document
    user_subscription_ref = db.collection('influencers').document(influencer_id).collection('subscriptions').document(user_id)
    
    # Attempt to get the document
    user_subscription_doc = user_subscription_ref.get()
    
    # Check if the document exists and if the phone_number field is filled
    if user_subscription_doc.exists:
        user_data = user_subscription_doc.to_dict()
        if 'phone_number' in user_data and user_data['phone_number']:
            return True, user_data['phone_number']  # Phone number exists and is not empty
        else:
            return False, None  # Phone number field does not exist or is empty
    else:
        return False, None  # Document does not exist

# Example usage:
# has_phone, phone_number = phone_number_status('botid', 'user12345')
# if has_phone:
#     print(f"User's phone number is {phone_number}.")
# else:
#     print("User's phone number is not available.")
    




def update_verification_code(influencer_id, user_id, code):
    # Reference to the specific subscription document of the user under the influencer
    user_subscription_ref = db.collection('influencers').document(influencer_id).collection('subscriptions').document(user_id)
    
    # Update the document with the new verification code
    user_subscription_ref.set({'verification_code': code}, merge=True)
    # The merge=True option ensures that only the 'verification_code' field is modified, leaving other fields untouched


def get_verification_code(influencer_id, user_id):
    # Reference to the specific subscription document of the user under the influencer
    user_subscription_ref = db.collection('influencers').document(influencer_id).collection('subscriptions').document(user_id)

    # Attempt to fetch the subscription document
    user_subscription_doc = user_subscription_ref.get()

    # Check if the document exists
    if user_subscription_doc.exists:
        user_data = user_subscription_doc.to_dict()
        # Check if the 'verification_code' field is present in the document
        if 'verification_code' in user_data:
            return user_data['verification_code']  # Return the verification code
        else:
            return None  # 'verification_code' field is not present
    else:
        return None  # Document does not exist



def update_verification_status(influencer_id, user_id, status):
    # Reference to the user's subscription document
    user_subscription_ref = db.collection('influencers').document(influencer_id).collection('subscriptions').document(user_id)
    
    # Update the document with the verification status
    user_subscription_ref.update({
        'number_verified': status
    })
    # print(f"Updated verification status to {status} for user {user_id} under influencer {influencer_id}.")

# Example usage:
# update_verification_status('botid', 'user12345', "True")


def get_verification_status(influencer_id, user_id):
    # Reference to the user's subscription document
    user_subscription_ref = db.collection('influencers').document(influencer_id).collection('subscriptions').document(user_id)
    
    # Get the current document
    doc = user_subscription_ref.get()
    if doc.exists:
        # Retrieve the verification status, default to False if not set
        verification_status = doc.to_dict().get('number_verified', False)

        if(verification_status == "True"):
            return True
        else:
            return False

    else:
        print(f"Document for user {user_id} under influencer {influencer_id} does not exist.")
        return False  # Document does not exist, hence verification status is False
    


# Example usage:
# status = get_verification_status('botid', 'user12345')
# print(status)





## Storing user's states
    # awaiting_email
    # awaiting_contact
    # awaiting_code
    # awaiting_verification
    
    # response_engine

def update_state(influencer_id, user_id, state):
    # Reference to the specific subscription document of the user under the influencer
    user_subscription_ref = db.collection('influencers').document(influencer_id).collection('subscriptions').document(user_id)
    
    # Update the document with the new state
    user_subscription_ref.set({'state': state}, merge=True)


def get_state(influencer_id, user_id):
    # Reference to the specific subscription document of the user under the influencer
    user_subscription_ref = db.collection('influencers').document(influencer_id).collection('subscriptions').document(user_id)

    # Attempt to fetch the subscription document
    user_subscription_doc = user_subscription_ref.get()

    # Check if the document exists
    if user_subscription_doc.exists:
        user_data = user_subscription_doc.to_dict()
        # Check if the 'state' field is present in the document
        if 'state' in user_data:
            return user_data['state']  # Return the user's state
        else:
            return None  # 'state' field is not present
    else:
        return None  # Document does not exist





def add_bubble_unique_id(influencer_id, user_id, unique_id):
        # Reference to the specific subscription document of the user under the influencer
    user_subscription_ref = db.collection('influencers').document(influencer_id).collection('subscriptions').document(user_id)
    
    # Update the document with the new bubble_user_unique_id field
    user_subscription_ref.update({
        'bubble_user_unique_id': unique_id
    })
    # print(f"Added bubble_user_unique_id: {unique_id} for user {user_id} under influencer {influencer_id}.")


# Example usage:
# add_bubble_unique_id('botid', 'user12345', "aksjdfkasdkjskafjksdf")


def get_bubble_unique_id(influencer_id, user_id):
    # Reference to the specific subscription document of the user under the influencer
    user_subscription_ref = db.collection('influencers').document(influencer_id).collection('subscriptions').document(user_id)

    # Attempt to fetch the subscription document
    user_subscription_doc = user_subscription_ref.get()
    
    # Check if the document exists and contains the 'bubble_user_unique_id' field
    if user_subscription_doc.exists:
        user_data = user_subscription_doc.to_dict()
        if 'bubble_user_unique_id' in user_data:
            print("bubble_user_unique_id: ", user_data['bubble_user_unique_id'])
            return user_data['bubble_user_unique_id']  # Return the unique ID
        else:
            return False  # 'bubble_user_unique_id' field is not present
    else:
        return False  # Document does not exist

# # Example usage:
# unique_id = get_bubble_unique_id('botid', 'user12345')
# print(unique_id if unique_id else "No unique ID found for user.")




def add_subscription_id(influencer_id, user_id, bubble_user_uid, influencer_bubble_id):
    # Create subscription_id
    subscription_id = connectBubble.add_subscription(bubble_user_uid, user_id, influencer_bubble_id)

    # Add to Firebase
    # Reference to the specific subscription document of the user under the influencer
    user_subscription_ref = db.collection('influencers').document(influencer_id).collection('subscriptions').document(user_id)
    
    # Update the document with the new subscription_id field
    user_subscription_ref.update({
        'subscription_id': subscription_id
    })

    return subscription_id
    # print(f"Added subscription_id: {subscription_id} for user {user_id} under influencer {influencer_id}.")



def get_subscription_id(influencer_id, user_id):
    # Reference to the specific subscription document of the user under the influencer
    user_subscription_ref = db.collection('influencers').document(influencer_id).collection('subscriptions').document(user_id)

    # Attempt to fetch the subscription document
    user_subscription_doc = user_subscription_ref.get()

    # Check if the document exists and contains the 'subscription_id' field
    if user_subscription_doc.exists:
        user_data = user_subscription_doc.to_dict()
        if 'subscription_id' in user_data:
            return user_data['subscription_id']  # Return the subscription ID
        else:
            return False  # 'subscription_id' field is not present
    else:
        return False  # Document does not exist







def store_user_email(influencer_id, user_id, email):
    # Reference to the specific subscription document of the user under the influencer
    user_subscription_ref = db.collection('influencers').document(influencer_id).collection('subscriptions').document(user_id)

    # Update the document with the new bubble_user_unique_id field
    user_subscription_ref.update({
        'user_email': email,
    })
    # print(f"Stored email under for {user_id} under {influencer_id}")


# Example usage:
# store_user_email('botid', 'user12345', 'kajen@gmail.com')

def user_email_status(influencer_id, user_id):
    
    # Reference to the user's subscription document
    user_subscription_ref = db.collection('influencers').document(influencer_id).collection('subscriptions').document(user_id)
    
    # Attempt to get the document
    user_subscription_doc = user_subscription_ref.get()
    
    # Check if the document exists and if the user_email field is filled
    if user_subscription_doc.exists:
        user_data = user_subscription_doc.to_dict()
        if 'user_email' in user_data and user_data['user_email']:
            return True, user_data['user_email']  # Email exists and is not empty
        else:
            return False, None  # Email field does not exist or is empty
    else:
        return False, None  # Document does not exist

# Example usage:
# user_email_status('botid', 'user12345')