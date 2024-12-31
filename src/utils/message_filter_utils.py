"""
Filters a list of message dictionaries, keeping only those with a 'role' of 'user'.
"""
def filter_user_messages(messages):
    return [message for message in messages if message.get('role') == 'user']
    