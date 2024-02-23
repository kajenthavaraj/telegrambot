import re
import requests



def extract_area_code(text):
    match = re.search(r"\+(\d+)", text)

    if match:
        area_code = match.group(1)
        return area_code
    else:
        return None

# Example Usage:
# text = "🇬🇧 United Kingdom +44"
# extract_area_code(text)


import requests

def find_user(find_phone_number):
    api_key = '7bfc4e7b2cfbd0475b1ec923a0ea4c99'
    data_type = 'user'  # Assuming 'User' is the data type for users in your Bubble app

    # Construct the URL for fetching all users. Adjust if your API supports query parameters for filtering.
    bubble_url = f"https://app.tryinfluencerai.com/api/1.1/obj/{data_type}"
    headers = {"Authorization": f"Bearer {api_key}"}

    response = requests.get(bubble_url, headers=headers)

    if response.status_code == 200:
        users = response.json()['response']['results']

        for user in users:
            area_code = extract_area_code(user.get('previous_area_code', ''))
            user_phone_number = user.get('phone_number', '')

            if(str(area_code) + str(user_phone_number) == find_phone_number):
                print(f"User found! - {user['first_name']}")
                return user.get('_id', '')  # Returns the user object. Adjust if you need a specific field.

        print("User not found.")
        return None
    else:
        print(f"Error: {response.status_code} - {response.text}")
        return None

# # Example Usage:
# print(find_user("16477667841"))


# def get_user_data(user_unique_id):
#     api_key = '7bfc4e7b2cfbd0475b1ec923a0ea4c99'
#     data_type = 'user'

#     # Construct the URL for fetching a user by ID.
#     bubble_url = f"https://app.tryinfluencerai.com/api/1.1/obj/{data_type}/{user_unique_id}"
#     headers = {"Authorization": f"Bearer {api_key}"}

#     response = requests.get(bubble_url, headers=headers)

#     if response.status_code == 200:
#         user = response.json()['response']  # Adjust based on the actual JSON structure returned by your API

#         # Assuming you want to print or return some basic information about the user
#         print(f"User found! - {user['first_name']} {user['last_name']}")
#         return user  # Returns the complete user object. Adjust if you need specific fields.

#     else:
#         print(f"Error: {response.status_code} - {response.text}")
#         return None