import re
user_email = "kajengmai.con"
if (re.match(r"[^@]+@[^@]+\.(?!con$)[^@]+", user_email)):
    print("True")
else:
    print("False")
# def split_messages(ai_response):
#     # Regular expression to match sentences ending with specific punctuation and followed by a space or end of string
#     reply_array = re.split(r'(?<=[.!?])\s+(?=[A-Za-z])', ai_response)

#     new_reply_array = []
#     temp = ""

#     for i, reply in enumerate(reply_array):

#         if i == 0:
#             # Store the first sentence temporarily
#             temp = reply
#         elif i == 1:
#             # Combine the first and second sentence and add to new_reply_array
#             new_reply_array.append(temp + " " + reply)
#         else:
#             # Remove period from string
#             if("." in reply):
#                 reply = reply.replace(".", "")
            
#             # Add remaining sentences to new_reply_array
#             new_reply_array.append(reply)

#     # Check if temp has a value and new_reply_array is empty, then add temp to new_reply_array
#     if temp and not new_reply_array:
#         if("." in temp):
#             temp = temp.replace(".", "")
#         new_reply_array.append(temp)

#     return new_reply_array

# print(split_messages("Wagwan G. What's up with you? Is everything ok?"))