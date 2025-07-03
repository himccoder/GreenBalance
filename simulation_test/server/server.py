from flask import Flask, jsonify
import os

app = Flask(__name__)

msg = os.environ.get('RESPONSE_TEXT', "hello from server") # "hello from server" is default message
id = os.environ.get('SERVER_ID', "0")

@app.route("/")
def send_response():
    # return msg, 200
    json = {
        "response": msg,
        "id": id
    }
    return jsonify(json), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000)