
from src.config.bot_commands import CHAT_COMMANDS

"""
Filters a list of message dictionaries, keeping only those with a 'role' of 'user'.
"""
def filter_user_messages(messages):
    return [message for message in messages if message.get('role') == 'user']
    
def verify_is_chat_command(input_str):
    # Check if it starts with ! or -
    if input_str.startswith('!') or input_str.startswith('-'):
        return True
    
    # Otherwise, check if it starts with any of the known commands
    for cmd in CHAT_COMMANDS:
        if input_str.startswith(cmd):
            return True
    
    return False