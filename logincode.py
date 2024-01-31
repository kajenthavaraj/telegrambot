import random
import string



# Random code generator
def generate_random_code(length=10):
    # Define the characters to choose from, in this case, lowercase letters
    letters = string.ascii_lowercase
    
    # Generate a random 10-letter code
    random_code = ''.join(random.choice(letters) for i in range(length))
    
    return random_code

print(generate_random_code())




# Loop to update code for each user on Bubble every 3 minutes









# Once user uses login code. add their telegram user_id to bubble for the AI to know
