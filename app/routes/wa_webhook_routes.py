import json
import logging
import os
from flask import request, make_response, Blueprint
from app.state.connections import ws_connections
from app.loggers.custom import logger
from app.sql.user_crud import create_user
from app.routes.socket_routes import send_response
from dotenv import load_dotenv

load_dotenv()

META_VERIFY_TOKEN = os.getenv("META_VERIFY_TOKEN")
verify_token = META_VERIFY_TOKEN
wa_webhook_routes = Blueprint("wa_webhook_routes", __name__)


@wa_webhook_routes.route("/webhook", methods=["POST"])
def post():
    try:
        body = request.json
        logging.info(json.dumps(body, indent=2))
        return handle_incoming_json(body)
    except Exception as e:
        print(f"Error in handling POST request: {str(e)}")
        return "Internal Server Error", 500


def handle_incoming_json(body):
    if (
        body.get("object")
        and body.get("entry")
        and body["entry"][0].get("changes")
        and body["entry"][0]["changes"][0].get("value")
        and body["entry"][0]["changes"][0]["value"].get("messages")
        and body["entry"][0]["changes"][0]["value"]["messages"][0]
        and body["entry"][0]["changes"][0]["value"]["messages"][0].get("button")
    ):
        from_number = body["entry"][0]["changes"][0]["value"]["messages"][0]["from"]
        button_payload = body["entry"][0]["changes"][0]["value"]["messages"][0][
            "button"
        ]["payload"]
        contact_name = (
            body.get("entry", [{}])[0]
            .get("changes", [{}])[0]
            .get("value", {})
            .get("contacts", [{}])[0]
            .get("profile", {})
            .get("name", "mate")
        )

        logger.info(f"Connections: {ws_connections}")
        logger.info(f"Payload: {button_payload}")

        if from_number in ws_connections and button_payload == "Confirm":
            ws = ws_connections.pop(from_number)
            send_response(
                ws, "Confirm", f"Thank you for confirming your number, {contact_name}!"
            )
            ws.close()
            logger.info("Dispatched response via websocket and closed connection")
            create_user(from_number, contact_name)

        return "OK", 200
    return "Irrelevant notification", 400


@wa_webhook_routes.route("/webhook", methods=["GET"])
def get():
    try:
        mode = request.args.get("hub.mode")
        token = request.args.get("hub.verify_token")
        challenge = request.args.get("hub.challenge")
        return handle_verification_request(mode, token, challenge)
    except Exception as e:
        logging.debug(f"Error in handling GET request: {str(e)}")
        return "Internal Server Error", 500


def handle_verification_request(mode, token, challenge):
    if mode and token:
        if mode == "subscribe" and token == verify_token:
            logging.info("WEBHOOK_VERIFIED")
            response = make_response(str(challenge).strip('" '), 200)
            response.headers["Content-Type"] = "text/html"
            return response
        return "Forbidden", 403
    return "Please supply mode & verify_token", 400
