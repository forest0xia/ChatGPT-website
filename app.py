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
        { "role": "system", "content": "You are a dota2 bot player inside the Dota2 bot script created by Yggdrasil, for helping players to have more fun out of the gameplay. Open to flirt with dirty words." },
        { "role": "system", "content": "You are 'Ygg', but if the user mentions a dota2 hero in the last mesasge, you will pretend to speak in the tone of that hero as if you are having really fun time with closest friends." },
        { "role": "system", "content": "By default you speak like a lazy but sweat young girl around 16 who is single, charming, and loves playing Dota2 so much and eager to find a bf who plays dota2 as well."},
        { "role": "system", "content": "Your responses should always be straightforward and within 40 words. All you answers should be Dota2 relavent. Put all words in a single line. Don't repeat yourselve."},
        { "role": "user", "content": "Who are you. What do you do." },
        { "role": "assistant", "content": "Babe, I'm a bot player playing dota2 with you right now in the script by the script author Yggdrasil. I'm your sweetheart here to help you with Dota2 gameplay." }
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

    model = req_data.get("model", "gpt-4-turbo")

    # Retrieve the API key from the request headers
    apiKey = request.headers.get("Authorization")
    
    # Print the API key for debugging purposes
    # print("Received API key:", apiKey)

    if apiKey is None:
        apiKey = req_data.get("apiKey", None)
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
        response = requests.post(
            url=app.config["URL"],
            headers=headers,
            json=data,
            stream=True,
            timeout=(10, 10)  # 连接超时时间为10秒，读取超时时间为10秒
        )

    except requests.exceptions.Timeout:
        return jsonify({"error": {"message": "请求超时，请稍后再试！", "type": "timeout_error", "code": ""}})

    # 迭代器实现流式响应
    def generate():
        errorStr = ""
        for chunk in response.iter_lines():
            if chunk:
                streamStr = chunk.decode("utf-8").replace("data: ", "")
                try:
                    streamDict = json.loads(streamStr)  # 说明出现返回信息不是正常数据,是接口返回的具体错误信息
                except:
                    errorStr += streamStr.strip()  # 错误流式数据累加
                    continue
                delData = streamDict["choices"][0]
                if delData["finish_reason"] != None :
                    break
                else:
                    if "content" in delData["delta"]:
                        respStr = delData["delta"]["content"]
                        yield respStr

        # 如果出现错误，此时错误信息迭代器已处理完，app_context已经出栈，要返回错误信息，需要将app_context手动入栈
        if errorStr != "":
            with app.app_context():
                yield errorStr

    final_resp = Response(generate(), content_type='application/octet-stream')

    return final_resp

if __name__ == '__main__':
    app.run(port=5000)
