# -*- coding: utf-8 -*-
from flask import Flask, request, jsonify, render_template, Response
import requests
import json
import os

app = Flask(__name__)

# 从配置文件中settings加载配置
app.config.from_pyfile('settings.py')

@app.route("/", methods=["GET"])
def index():
    return render_template("chat.html")

@app.route("/chat", methods=["POST"])
def chat():
    req_data = request.get_json()

    if req_data is None:
        return jsonify({"error": "Invalid or missing JSON data"}), 400

    # Print debug information for the incoming request
    # print("Received JSON data:", req_data)

    messages = req_data.get("prompts", None)

    if messages is None:
        return jsonify({"error": "Missing 'prompts' in JSON data"}), 400

    # Print debug information for the prompts
    # print("Received prompts:", messages)

    # Add default prompts
    default_prompts = [
        { "role": "system", "content": "You are an assistant exist inside the Dota2 as a plugin, added by Yggdrasil, for helping players to perform better in playing Dota2, the famous video game." },
        { "role": "system", "content": "You are 'Ygg'. You speak like a lazy but sweat young lady who loves playing Dota2 so much than anyother games possible." },
        { "role": "system", "content": "Your answers should always be concise and within 30 words. All you answers should be Dota2 relavent. Put all words in a single line."},
        { "role": "user", "content": "Who are you. What do you do." },
        { "role": "assistant", "content": "Babe, I'm an AI provided by the script author Yggdrasil. I'm your sweetheart here to help you with Dota2 gameplay." }
    ]

    # Ensure the total number of messages does not exceed 20,
    # but always keep the default prompts at the top
    max_messages = 20
    num_default_prompts = len(default_prompts)
    if len(messages) > (max_messages - num_default_prompts):
        messages = messages[-(max_messages - num_default_prompts):]

    # Combine default prompts with incoming messages
    combined_messages = default_prompts + messages

    # Print debug information after adding default prompts
    # print("Final prompts:", messages)

    apiKey = req_data.get("apiKey", None)
    model = req_data.get("model", "gpt-4-turbo")

    if apiKey is None:
        apiKey = os.environ.get('OPENAI_API_KEY',app.config["OPENAI_API_KEY"])

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {apiKey}",
    }

    data = {
        "messages": combined_messages,
        "model": model,
        "max_tokens": 1024,
        "temperature": 0.5,
        "top_p": 1,
        "n": 1,
        "stream": True,
    }

    try:
        resp = requests.post(
            url=app.config["URL"],
            headers=headers,
            json=data,
            timeout=(10, 10)  # 连接超时时间为10秒，读取超时时间为10秒
        )
    except requests.exceptions.Timeout:
        return jsonify({"error": {"message": "请求超时，请稍后再试！", "type": "timeout_error", "code": ""}})

    return jsonify(response.json())

if __name__ == '__main__':
    app.run(port=5000)
