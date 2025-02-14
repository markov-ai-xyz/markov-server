import requests
import json
import os
from app.loggers.custom import logger
from dotenv import load_dotenv

load_dotenv()

META_AUTH_TOKEN = os.getenv("META_AUTH_TOKEN")
META_GRAPH_UUID = os.getenv("META_GRAPH_UUID")
AUTH_TOKEN = f"Bearer {META_AUTH_TOKEN}"
URL = f"https://graph.facebook.com/v19.0/{META_GRAPH_UUID}/messages"
HEADERS = {"Authorization": AUTH_TOKEN, "Content-Type": "application/json"}


def dispatch_wa_auth_template(wa_number):

    payload = {
        "messaging_product": "whatsapp",
        "to": wa_number,
        "type": "template",
        "template": {"name": "markov_auth", "language": {"code": "en"}},
    }

    response = requests.post(URL, headers=HEADERS, data=json.dumps(payload))
    logger.info(f"{response.status_code}: {response.text}")


def dispatch_wa_message(wa_number, message):
    payload = {
        "messaging_product": "whatsapp",
        "to": wa_number,
        "text": {"body": message},
    }

    response = requests.post(URL, headers=HEADERS, data=json.dumps(payload))
    logger.info(f"{response.status_code}: {response.text}")


def dispatch_location_request(wa_number, message):
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "type": "interactive",
        "to": wa_number,
        "interactive": {
            "type": "location_request_message",
            "body": {"text": message},
            "action": {"name": "send_location"},
        },
    }

    response = requests.post(URL, headers=HEADERS, data=json.dumps(payload))
    logger.info(f"{response.status_code}: {response.text}")
