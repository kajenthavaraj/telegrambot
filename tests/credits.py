################################################################
###################### Credits Functions #######################
################################################################

# def initialize_credits(influencer_id, user_id):
#     db = init_database()
#     # Reference to the specific subscription document of the user under the influencer
#     user_subscription_ref = db.collection('influencers').document(influencer_id).collection('subscriptions').document(user_id)
    
#     # Get the current local time
#     current_time = time.localtime()

#     # Format the time to extract just the date, month, and year
#     current_date = time.strftime("%d-%m-%Y", current_time)

#     # Update the document with the new bubble_user_unique_id field
#     user_subscription_ref.update({
#         'minutes_credits': 5,
#         'chat_credits': 30,
#         'last_chat_base_refill': current_date,
#     })
#     print(f"Initialized credits under for {user_id} under {influencer_id}")


# # Example usage:
# # initialize_credits('influencerai_bot', 'user12345')


def get_minutes_credits(influencer_id, user_id):
    db = init_database()
    # Reference to the specific subscription document of the user under the influencer
    user_subscription_ref = db.collection('influencers').document(influencer_id).collection('subscriptions').document(user_id)

    # Attempt to fetch the subscription document
    user_subscription_doc = user_subscription_ref.get()

    # Check if the document exists and contains the 'minutes_credits' field
    if user_subscription_doc.exists:
        user_data = user_subscription_doc.to_dict()
        if 'minutes_credits' in user_data:
            return user_data['minutes_credits']
        else:
            initialize_credits(influencer_id, user_id)
            return False  # 'minutes_credits' field is not present
    else:
        return False  # Document does not exist


def get_chat_credits(influencer_id, user_id):
    db = init_database()
    # Reference to the specific subscription document of the user under the influencer
    user_subscription_ref = db.collection('influencers').document(influencer_id).collection('subscriptions').document(user_id)

    # Attempt to fetch the subscription document
    user_subscription_doc = user_subscription_ref.get()

    # Check if the document exists and contains the 'chat_credits' field
    if user_subscription_doc.exists:
        user_data = user_subscription_doc.to_dict()
        if 'chat_credits' in user_data:
            return user_data['chat_credits']
        else:
            initialize_credits(influencer_id, user_id)
            return False  # 'chat_credits' field is not present
    else:
        return False  # Document does not exist


def update_minutes_credits(influencer_id, user_id, num_minutes):
    db = init_database()
    # Reference to the specific subscription document of the user under the influencer
    user_subscription_ref = db.collection('influencers').document(influencer_id).collection('subscriptions').document(user_id)

    # Fetch the current minutes credits, if any
    current_credits = get_minutes_credits(influencer_id, user_id)
    if current_credits is False:
        # Initialize credits if they don't exist
        current_credits = 0

    # Update the 'minutes_credits' field with the new value
    new_credits = current_credits + num_minutes
    user_subscription_ref.update({'minutes_credits': new_credits})


def update_chat_credits(influencer_id, user_id, num_credits):
    db = init_database()
    # Reference to the specific subscription document of the user under the influencer
    user_subscription_ref = db.collection('influencers').document(influencer_id).collection('subscriptions').document(user_id)

    # Fetch the current chat credits, if any
    current_credits = get_chat_credits(influencer_id, user_id)
    if current_credits is False:
        # Initialize credits if they don't exist
        current_credits = 0

    # Update the 'chat_credits' field with the new value
    new_credits = current_credits + num_credits
    user_subscription_ref.update({'chat_credits': new_credits})