import firebase_admin
from firebase_admin import credentials, firestore
from firebase_admin.firestore import ArrayUnion, SERVER_TIMESTAMP
from datetime import datetime
import pytz


def init_database():
    # Check if the default Firebase app has already been initialized
    if not firebase_admin._apps:
        KEYPATH = 'telegrambot-d6553-firebase-adminsdk-ruf4v-91d571bca9.json'
        cred = credentials.Certificate(KEYPATH)
        firebase_admin.initialize_app(cred)
    
    db = firestore.client()
    return db


# Function to  create a new influencer collection
def create_influencer_collection(influencer_id, influencer_name):
    influencer_data = {
        'name': influencer_name,
    }

    db = init_database()
    
    db.collection('influencers').document(influencer_id).set(influencer_data)
    print(f"Influencer {influencer_name} with ID {influencer_id} has been added to the database.")

# Example usage
# create_influencer_collection(influencer_id='veronicaavluvaibot', influencer_name='Veronica Avluv')


# Function to add user to an influencers subscriptions
def add_user_to_influencer_subscription(influencer_id, user_id):
    db = init_database()
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
    print(f"User {user_id} has been added to the subscriptions of influencer {influencer_id}.")

# Example usage
# add_user_to_influencer_subscription('veronicaavluvaibot', 'user12345')



# Function to add to chat history
def add_chat_to_user_history(influencer_id, user_id, role, content):
    db = init_database()
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
# add_chat_to_user_history('veronicaavluvaibot', 'user12345', 'user', 'Hello, how are you?')
# add_chat_to_user_history('veronicaavluvaibot', 'user12345', 'agent', "I'm good, thanks for asking!")




def get_user_chat_history(influencer_id, user_id):
    db = init_database()
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
        print(f"No subscription found for user {user_id} under influencer {influencer_id}.")
        return None

# Example usage
# chat_history = get_user_chat_history('veronicaavluvaibot', 'user12345')
# if(chat_history == None):
#     print("NO CHAT HISTORY FOR USER")
# else:
#     chat_history_str = '\n'.join(f"{chat['role']}: {chat['content']}" for chat in chat_history)
#     print(chat_history_str)