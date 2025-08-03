
from flask import request, jsonify, current_app
from src.config.bot_commands import CHAT_COMMANDS
from src.config.settings import MIN_USER_CHAT_LENGTH_FOR_LLM

"""
Filters a list of message dictionaries, keeping only those with a 'role' of 'user'.
"""
def filter_user_messages(messages):
    return [message for message in messages if message.get('role') == 'user']
    
def should_skip_llm_chat(input_str):
    if len(input_str) < MIN_USER_CHAT_LENGTH_FOR_LLM:
        current_app.logger.warning(f"Message too short: {input_str}. Should skip processing.")
        return True
    # Check if it starts with ! or -
    if input_str.startswith('!') or input_str.startswith('-'):
        current_app.logger.warning(f"Message starts with command char: {input_str}. Should skip processing.")
        return True
    
    # Otherwise, check if it starts with any of the known commands
    for cmd in CHAT_COMMANDS:
        if input_str.startswith(cmd):
            current_app.logger.warning(f"Message starts with chat command: {input_str}. Should skip processing.")
            return True
        if 'pos' in input_str and len(input_str) < 7:
            current_app.logger.warning(f"Message contains chat command: {input_str}. Should skip processing.")
            return True
    
    return False
