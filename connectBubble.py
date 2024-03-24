import re
import requests
import bubbledb
import phonenumbers
import loginuser
import json

def extract_country_code_and_number(phone_number):
    print("extract_country_code_and_number ", phone_number)
    try:
        # Parse the phone number without specifying a default region
        parsed_number = phonenumbers.parse(phone_number, None)
        
        # Extract the country code from the parsed phone number
        country_code = str(parsed_number.country_code)
        
        # Extract the national number part of the phone number
        national_number = str(parsed_number.national_number)
        
        # Return the country code and the national number as a list
        return [country_code, national_number]
    except phonenumbers.NumberParseException as e:
        print(f"Error parsing phone number: {e}")
        return None

# Example Usage:
# phone_number = "+14167009468"
# print(extract_country_code_and_number(phone_number))


def extract_country_code_from_text(text):
    match = re.search(r"\+(\d+)", text)

    if match:
        area_code = match.group(1)
        return area_code
    else:
        return None

# Example Usage:
# text = "🇬🇧 United Kingdom +44"
# extract_area_code(text)


# Filters through Bubble database and finds the user with the phone number
# Returns unique_id of use
def find_user(phone_number_to_find):

    print("phone_number_to_find inputted into find_user ", phone_number_to_find)

    if(phone_number_to_find == None):
        return False

    # Parse phone number entered
    if("+" in phone_number_to_find):
        country_code, phone_number = extract_country_code_and_number(str(phone_number_to_find))
    else:
        country_code, phone_number = extract_country_code_and_number("+" + str(phone_number_to_find))

    response = bubbledb.get_data_list("User", ["phone_number"], [phone_number], ["equals"])
    
    if(response == 404):
        print("404 Error when trying to find user")
        return False

    if(len(response['results']) == 0):
        return False

    if(len(response['results']) == 1):
        first_user = response['results'][0]

        # Check if area codes match
        bubble_area_code = first_user.get('area_code', '')
        parsed_bubble_area_code = extract_country_code_from_text(bubble_area_code)
        
        # Return found user with the correct area code
        if(parsed_bubble_area_code == country_code):
            first_user = response['results'][0]
            user_unique_id = first_user.get('_id', '')

            return user_unique_id
        else:
            return False # need to create a new user

    # Handle case where there's multiple numbers - loop through them and get the first one where they share the same area code
    else:
        print("Multiple users with the phone number has been found")
        user_list = response['results']

        for user in user_list:
            # Get the area code stored in bubble
            bubble_area_code = user.get('area_code', '')
            parsed_bubble_area_code = extract_country_code_from_text(bubble_area_code)
            
            # Return found user with the correct area code
            if(parsed_bubble_area_code == country_code):
                user = response['results'][0]
                user_unique_id = user.get('_id', '')
                return user_unique_id
            else:
                return False


# uid = find_user("16477667841")
# print(uid)


def get_user_email(unique_id):
    data_type = "User"  # Assuming the data type for users is "User"
    
    jsondata = bubbledb.get_data(unique_id, data_type)
    print(jsondata)

    if jsondata != 404:
        try:
            # Navigate through the nested dictionaries to get the email
            email = jsondata['authentication']['email']['email']
            return email
        except KeyError as e:
            print(f"Key error: {e} - Check the JSON structure.")
            return False
    else:
        return 404



# Creating user
    
def create_user(email, unparsed_phone_number, first_name):
    
    # Parse phone number entered
    if("+" in unparsed_phone_number):
        area_code, phone_number = extract_country_code_and_number(str(unparsed_phone_number))
    else:
        area_code, phone_number = extract_country_code_and_number("+" + str(unparsed_phone_number))

    area_code = "+" + str(area_code)
    
    # Create random password for user
    password = loginuser.generate_random_code(8)

    user_data = {
        "email": email,
        "first_name": first_name,
        "area_code": area_code,
        "phone_number": str(phone_number),
        "credits": 10,  # Initialize minutes credits with 10
        "chat_credits": 15, # Initialize chat credits with 15
        "is_influencer": "no",
        "telegram_phone_number": str(unparsed_phone_number),
        "password_field": password,
        "password": password
    }
    
    result = bubbledb.add_entry("user", user_data)
    print("Creating User - result: ", result)

    return result

# result = create_user("joemamabad@gmail.com", "16477667841", "JoeMama")
# print(result)


# Creating subscription
def add_subscription(user_uid, telegram_user_id, influencer_uid):

    # Create subscription
    
    data = {
        "credits_used": 0,
        "influencer": influencer_uid,
        "minutes_spent": 0,
        "telegram_user_id": telegram_user_id,
        "user": user_uid
    }
    
    sub_id = bubbledb.add_entry("subscription", data)
    print("subscription_id: ", sub_id)
    

    if(sub_id != 400 or sub_id != 401):
        # Append subscription to user
        response = bubbledb.add_to_database_list(user_uid, "user", "subscriptions", [sub_id])
        print(response)
        if(response == 400 or response == 401):
            return False
    else:
        return False

    # Return the subscription_id
    return sub_id


# ADD CODE HERE FOR APPENDING SUBSCRIPTION
def update_subscription(user_uid, telegram_user_id, influencer_uid, subscription_ID, subscription_plan, status, last_billing_date, next_billing_date, amount_paid):
    print("Attempting to update subscription entry in Bubble...")

    # Attempt to find the existing subscription for the specific influencer
    existing_sub_id = bubbledb.get_subscription_id(user_uid, influencer_uid)

    if existing_sub_id:
        print(f"Existing subscription found: {existing_sub_id}. Updating with new data...")

        # Prepare the new data for the subscription
        updated_data = {
            "subscription_stripe_id": subscription_ID,
            "subscription_plan": subscription_plan,
            "status": status,
            "last_billing_date": last_billing_date,
            "next_billing_date": next_billing_date,
        }

        # Update each field in the subscription
        response = True
        for field, value in updated_data.items():
            update_response = bubbledb.update_database(existing_sub_id, "Subscription", field, value)
            
            if update_response != 204:
                response = False
                print(f"Failed to update {field} in Bubble.")
                break  # Stop updating if any field update fails

        if not response:
            print("Failed to update subscription in Bubble.")
            return False
        
    # Prepare the data for new subscription history entry
    subscription_history_data = {
        "influencer": influencer_uid,
        "last_billing_date": last_billing_date,
        "next_billing_date": next_billing_date,
        "purchase_amount": amount_paid,  
        "status": status,
        "subscription_plan": subscription_plan,
        "subscription_stripe_id": subscription_ID,
        "telegram_user_id": telegram_user_id,
        "user": user_uid,
    }

    # Create new subscription history entry
    new_history_id = bubbledb.add_entry("purchase_subscription", subscription_history_data)
    if new_history_id == -1:
        print("Failed to create a new subscription history entry.")
        return False

    # Append the new subscription history ID to the user's subscription_history field
    append_response = bubbledb.add_to_database_list(user_uid, "User", "subscription_history", [new_history_id])
    if append_response == 204:
        print("Subscription history updated successfully.")
        return True
    else:
        print("Failed to update subscription history.")
        return False
    


def check_user_subscription(bubble_unique_id, influencer_uid):
    # Assuming 'bubbledb.get_data' is a method to fetch data based on unique ID and data type.
    user_data_type = "User"
    subscription_data_type = "Subscription"

    # Fetch user data from Bubble database
    user_data = bubbledb.get_data(bubble_unique_id, user_data_type)
    print("The user data gotten is: ", user_data)

    # Check if user data was successfully fetched
    if user_data == 404 or not user_data:
        print("User not found or error fetching user data.")
        return False, None

    # Access the 'Subscriptions' field which is expected to contain a list of subscription IDs
    subscriptions = user_data.get('subscriptions', [])
    print("User subscriptions:", subscriptions)

    if not subscriptions:
        print("User does not have any subscriptions.")
        return False, None

    # Iterate through each subscription ID to fetch subscription details
    for subscription_id in subscriptions:
        # Fetching detailed data for each subscription from Bubble database
        sub_data = bubbledb.get_data(subscription_id, subscription_data_type)

        # Continue if specific subscription data not found or error occurred
        if sub_data == 404 or not sub_data:
            print(f"Subscription data not found for ID: {subscription_id}")
            continue

        # Check if the subscription's 'influencer' field matches the given influencer UID
        if sub_data.get('influencer') == influencer_uid:
            subscription_status = sub_data.get('status')
            if subscription_status == "complete":
                print("User has an active subscription with the influencer.")
                return True, subscription_status  # User is subscribed to the influencer and it's active
            else:
                return False, subscription_status

    # If no matching subscription is found
    print("User does not have an active subscription with the influencer.")
    return False, None


def check_user_subscription_more_detail(bubble_unique_id, influencer_uid):
    # Assuming 'bubbledb.get_data' is a method to fetch data based on unique ID and data type.
    user_data_type = "User"
    subscription_data_type = "Subscription"

    # Fetch user data from Bubble database
    user_data = bubbledb.get_data(bubble_unique_id, user_data_type)
    print("The user data gotten is: ", user_data)

    # Check if user data was successfully fetched
    if user_data == 404 or not user_data:
        print("User not found or error fetching user data.")
        return False, None, None  # Also return None for next_billing_date when user data is not found

    # Access the 'Subscriptions' field which is expected to contain a list of subscription IDs
    subscriptions = user_data.get('subscriptions', [])
    print("User subscriptions:", subscriptions)

    if not subscriptions:
        print("User does not have any subscriptions.")
        return False, None, None  # Also return None for next_billing_date when there are no subscriptions

    # Iterate through each subscription ID to fetch subscription details
    for subscription_id in subscriptions:
        # Fetching detailed data for each subscription from Bubble database
        sub_data = bubbledb.get_data(subscription_id, subscription_data_type)

        # Continue if specific subscription data not found or error occurred
        if sub_data == 404 or not sub_data:
            print(f"Subscription data not found for ID: {subscription_id}")
            continue

        # Check if the subscription's 'influencer' field matches the given influencer UID
        if sub_data.get('influencer') == influencer_uid:
            subscription_status = sub_data.get('status')
            # Fetch the next billing date from the subscription data
            next_billing_date = sub_data.get('next_billing_date', 'N/A')
            if subscription_status == "complete":
                print("User has an active subscription with the influencer.")
                # Return the next billing date along with the subscription status
                return True, subscription_status, next_billing_date
            else:
                # Return the next billing date even if the subscription is not "complete"
                return False, subscription_status, next_billing_date

    # If no matching subscription is found
    print("User does not have an active subscription with the influencer.")
    return False, None, None  # Also return None for next_billing_date when no matching subscription is found





def get_user_subscription(bubble_unique_id, influencer_uid):
    print("The get_user_subscription function is being called")
    user_data_type = "User"
    
    # Fetch the user data
    user_data = bubbledb.get_data(bubble_unique_id, user_data_type)

    if user_data == 404:
        print("User not found or error fetching user data.")
        return None

    # Access the 'subscriptions' list from the user data
    subscription_ids = user_data.get('subscriptions', [])

    if not subscription_ids:
        print("User does not have any subscriptions.")
        return None

    # Iterate through each subscription ID to fetch subscription details
    for subscription_id in subscription_ids:
        subscription_data = bubbledb.get_data(subscription_id, "Subscription")

        if subscription_data == 404:
            print(f"Subscription data not found for ID: {subscription_id}")
            continue
        
        # Check if the subscription's 'influencer' field matches the given influencer UID
        if subscription_data.get('influencer') == influencer_uid:
            # Retrieve the Stripe subscription ID from the subscription data
            stripe_subscription_id = subscription_data.get('subscription_stripe_id', None)
            print(f"Stripe subscription ID: {stripe_subscription_id}")
            
            if not stripe_subscription_id:
                print("Stripe subscription ID not found in the subscription data.")
                continue  # Continue searching in case of multiple subscriptions
                
            return stripe_subscription_id

    print("No matching subscription found for the influencer.")
    return None





# Functions for getting user's first name
def get_user_first_name(unique_id):
    data_type = "User" 

    # Use the get_data function to fetch the user data by unique_id
    user_data = bubbledb.get_data(unique_id, data_type)

    if user_data != 404:
        first_name = user_data.get('first_name', 'First name not found')
        return first_name
    else:
        print("Failed to retrieve user data.")
        return None

# print(get_user_first_name("1708499428569x406893957846703700"))


def update_user_first_name(unique_id, new_first_name):
    data_type = "User"  
    field_name = "first_name" 

    # Prepare the data for updating the user's first name
    data = {field_name: new_first_name}

    # Use the update_data_fields function to update the user's first name
    response = bubbledb.update_data_fields(unique_id, data_type, data)

    if response == 204:
        print("User's first name updated successfully.")
    else:
        print(f"Failed to update user's first name. Response: {response}")

# update_user_first_name("1708499428569x406893957846703700", "Joemama")





################################################################
###################### Credits Functions #######################
################################################################

def get_minutes_credits(unique_id):
    data_type = "User"
    
    # Use the get_data function to fetch the user data by unique_id
    user_data = bubbledb.get_data(unique_id, data_type)

    if user_data != 404:
        minutes_credits = user_data.get('credits', 'credits not found')
        return minutes_credits
    else:
        print("Failed to retrieve user data.")
        return None

def get_chat_credits(unique_id):
    data_type = "User"
    
    # Use the get_data function to fetch the user data by unique_id
    user_data = bubbledb.get_data(unique_id, data_type)

    if user_data != 404:
        chat_credits = user_data.get('chat_credits', 'chat_credits not found')
        return chat_credits
    else:
        print("Failed to retrieve user data.")
        return None



def update_minutes_credits(unique_id, num_minutes, amount_paid, charge_id, influencer_attribution, paid_status):
    data_type = "User"  
    field_name = "credits"

    # First, update the user's credits
    current_credits = get_minutes_credits(unique_id)
    data_for_credits_update = {field_name: current_credits + num_minutes}
    response_credits_update = bubbledb.update_data_fields(unique_id, data_type, data_for_credits_update)

    if response_credits_update != 204:
        print("Failed to update user's minutes credits.")
        return False

    # Append purchase history
    purchase_history_data = {
        "amount": amount_paid,
        "charge_id": charge_id,
        "influencer_attribution": influencer_attribution,
        "minutes": num_minutes,
        "paid_status": paid_status,
        "user": unique_id  
    }

    new_purchase_history_id = bubbledb.add_entry("purchase_usage", purchase_history_data)

    if new_purchase_history_id == -1:
        print("Failed to create a new purchase history entry.")
        return False

    # Finally, append the new purchase history ID to the user's purchase_history field
    append_response = bubbledb.add_to_database_list(unique_id, data_type, "purchase_history", [new_purchase_history_id])

    if append_response == 204:
        print("Purchase history updated successfully.")
        return True
    else:
        print("Failed to update purchase history.")
        return False




def deduct_minutes_credits(unique_id, num_credits):
    data_type = "User"  
    field_name = "credits"

    current_credits = get_minutes_credits(unique_id)

    # Prepare the data for updating the user's first name
    data = {field_name: current_credits + num_credits}

    # Use the update_data_fields function to update the user's first name
    response = bubbledb.update_data_fields(unique_id, data_type, data)

    if response == 204:
        print("User's credits updated successfully.")
    else:
        print(f"Failed to update user's credits. Response: {response}")





def update_chat_credits(unique_id, num_credits):
    data_type = "User"  
    field_name = "chat_credits"

    current_credits = get_chat_credits(unique_id)

    # Prepare the data for updating the user's first name
    data = {field_name: current_credits + num_credits}

    # Use the update_data_fields function to update the user's first name
    response = bubbledb.update_data_fields(unique_id, data_type, data)

    if response == 204:
        print("User's chat credits updated successfully.")
    else:
        print(f"Failed to update user's chat credits. Response: {response}")


# Inside of Firebase store the following
    # User's unique_id
    # subscription_id