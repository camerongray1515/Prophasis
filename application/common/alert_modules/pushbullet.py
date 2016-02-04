import requests
import json
from alerting import AlertExecutionError

module_name = "Pushbullet"

config = {
    "Access Token(s)": "",
    "Message Title": "Prophasis Alert!"
}

def handle_alert(message):
    for token in config["Access Token(s)"].split(","):
        _send_push(token.strip(), message)

def _send_push(token, message):
    url = "https://api.pushbullet.com/v2/pushes"
    data = {"body": message, "title": config["Message Title"], "type": "note"}
    headers = {
        "Content-Type": "application/json",
        "Access-Token": token
    }

    r = requests.post(url, data=json.dumps(data), headers=headers).json()
    if "error" in r:
        raise AlertExecutionError(r["error"]["message"])
