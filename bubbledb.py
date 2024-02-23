import requests
import json
# Returns Json File of Data for the Data Entry with the Uniuqe ID
api_key = "7bfc4e7b2cfbd0475b1ec923a0ea4c99"

INFLUENCER_ID_TO_BUBBLE_ID = {

    "veronica_avluv" : "1703701959468x374948791862866400"

}

DATA_URL = "https://app.tryinfluencerai.com/api/1.1/obj/"



def get_data(unique_id, data_type):
    # api_key "cb49dfd6e576e3153fcf8d3b211698b0"

    bubble_url = f"{DATA_URL}{data_type}/{unique_id}"
    headers = {"Authorization": f"Bearer {api_key}"}

    response = requests.get(bubble_url, headers=headers)

    if response.status_code == 200:
        data = response.json()
        print("Data retrieved successfully!")
        return data["response"]
    else:
        print(f"Error: {response.status_code} - {response.text}")
        return 404
    
def get_data_list(data_type, keys, values, constraint_types, cursor = None, limit=None):

    # api_key "cb49dfd6e576e3153fcf8d3b211698b0"

    url = f"{DATA_URL}{data_type}"
    if keys != None:
        constraints = '['

        for i, key in enumerate(keys):
            constraints = constraints + f'{{"key" : "{key}", "constraint_type" : "{constraint_types[i]}","value" : "{values[i]}"}},'
        
        constraints = constraints[:-1]
        
        constraints = constraints + ']'


        url = url + "?constraints=" + constraints
    if keys != None and cursor != None:
        url = url + "&"
    if cursor != None:
        url = url + f'cursor={cursor}'
    if (keys != None or cursor != None) and limit != None:
        url = url + "&"
    if limit != None:
        url = url + f'limit={limit}'


    headers = {"Authorization": f"Bearer {api_key}"}

    response = requests.get(url, headers=headers,)

    if response.status_code == 200:
        # print(response.json())
        dataset = response.json()['response']
        return dataset
    else:
        # print(response.json())
        return 404
    
# Returns a data field from data base
def get_data_field(unique_id, data_type, field_name):

    jsondata = get_data(unique_id, data_type)

    if jsondata != 404:
        print("JSON DATA")
        print(jsondata)
        try:
            lead_list = jsondata[field_name]
        except:
            lead_list = []
        return lead_list
    else:
        return "fail 404 error"

# Updates the database with a new value
def update_database(unique_id, data_type, field_name, new_value, **kwargs):
    # api_key 'cb49dfd6e576e3153fcf8d3b211698b0'


    bubble_url = f"{DATA_URL}{data_type}/{unique_id}"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    
    data = {field_name: new_value}
    
    response = requests.patch(bubble_url, json=data, headers=headers)

    if response.status_code == int(204):
        return 204
    else:
        return -1

def bulk_create_data(data_type, data):
    # print(data)
    # api_key 'cb49dfd6e576e3153fcf8d3b211698b0'
    bubble_url = f"{DATA_URL}{data_type}/bulk"

    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "text/plain"}

    data_to_send = ""

    for dict in data:
        data_to_send = data_to_send + json.dumps(dict) + "\n"
    response = requests.post(bubble_url, headers=headers, data=data_to_send)

    result = []

    for item in response.iter_lines():
        result.append(json.loads(item))
    if response.status_code == int(200):
        return result
    else:
        # print(response)
        raise Exception

def update_data_fields(unique_id, data_type, data):
    # api_key 'cb49dfd6e576e3153fcf8d3b211698b0'


    bubble_url = f"{DATA_URL}{data_type}/{unique_id}"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}


    response = requests.patch(bubble_url, json=data, headers=headers)

    if response.status_code == int(204):
        return 204
    else:
        # print(response)
        # print(response.content)
        return response

# Adds a new entry to database

def add_entry(data_type, data):
    # api_key 'cb49dfd6e576e3153fcf8d3b211698b0'

    bubble_url = f"{DATA_URL}{data_type}"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    response = requests.post(bubble_url, json=data, headers=headers)

    if response.status_code == 201:

        response_data = response.json()

        unique_id = response_data['id']
        return unique_id

    else:
        print(response)
        return -1
    


# if __name__ == "__main__":
#     response = get_data_list("User", ["phone_number"], ["6477667841"], ["equals"])

#     if response != 404 and 'results' in response and len(response['results']) > 0:
#         users = response['results']

#         # Access the first user object (assuming you want the first one)
#         first_user = users[0]
#         print(first_user)
#         print()
#         print(first_user.get('_id', ''))




# # Creating user test
    
# new_user_data = {
#     "first_name": "33ssd",
#     "email": "ksss@example.com",
#     # "password": "securepassword"  # Be mindful of security and privacy concerns when handling passwords
#     # Add any other fields you have for your User data type
# }

# result = add_entry("User", new_user_data)
# print(result)






def add_to_database_list(unique_id, data_type, field_name, new_values):
    """
    Updates a list field in the database by adding new values after retrieving the current list.
    :param unique_id: The unique identifier for the data entry to update.
    :param data_type: The type of data (e.g., User, Subscription).
    :param field_name: The name of the list field to update.
    :param new_values: A list of new values to add to the list field.
    :return: HTTP status code indicating the result of the operation.
    """
    # Step 1: Perform a GET request to fetch the current list
    get_url = f"{DATA_URL}{data_type}/{unique_id}"
    headers = {"Authorization": f"Bearer {api_key}"}
    get_response = requests.get(get_url, headers=headers)

    if get_response.status_code != 200:
        print(f"Error fetching data: {get_response.status_code} - {get_response.text}")
        return get_response.status_code

    # Extract the current list from the response
    current_list = get_response.json().get('response', {}).get(field_name, [])
    
    # Step 2: Append the new values to the current list
    updated_list = current_list + new_values  # This combines the old and new values

    # Step 3: Perform a PATCH request to update the list with the new complete list
    update_url = f"{DATA_URL}{data_type}/{unique_id}"
    update_headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    update_data = {field_name: updated_list}
    update_response = requests.patch(update_url, json=update_data, headers=update_headers)

    if update_response.status_code == 204:
        print("List updated successfully!")
        return 204  # Success, no content to return
    else:
        print(f"Error updating list: {update_response.status_code} - {update_response.text}")
        return update_response.status_code
