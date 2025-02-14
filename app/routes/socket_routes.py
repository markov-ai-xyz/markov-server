from app.utils.wa_requests import dispatch_wa_auth_template
from app.state.connections import ws_connections
from app.loggers.custom import logger
from app.sql.user_crud import read_user
import threading
import json
import time


def send_response(ws, status, message):
    response = {"status": status, "message": message}
    ws.send(json.dumps(response))


def init_socket_routes(sock):
    @sock.route("/authenticate")
    def authenticate(ws):
        try:
            phone_number = ws.receive()
            logger.info(f"Received message: {phone_number}")

            if not phone_number:
                send_response(ws, "Error", "Invalid phone number")
                logger.info("Received invalid phone number")
                return

            user = read_user(phone_number)
            if user:
                name = user.name
                send_response(
                    ws,
                    "Error",
                    f"{name} is already registered with number {phone_number}",
                )
                return

            if phone_number in ws_connections:
                ws_connections.pop(phone_number)
                logger.info(
                    f"Deleted existing WebSocket connection for phone number {phone_number}"
                )

            ws_connections[phone_number] = ws
            logger.info(
                f"Stored new WebSocket connection for phone number {phone_number}"
            )

            thread = threading.Thread(
                target=dispatch_wa_auth_template, args=(str(phone_number),)
            )
            thread.start()
            send_response(ws, "OK", "Please acknowledge the WhatsApp message")
            logger.info("Verifying...")
            time.sleep(30)

            # Remove connection if user hasn't confirmed
            if phone_number in ws_connections:
                ws_connections.pop(phone_number)
                send_response(
                    ws,
                    "Error",
                    "No acknowledgment; please retype your number for authentication when you're ready",
                )
                ws.close()

        except Exception as e:
            logger.error("An error occurred during authentication", exc_info=True)
            send_response(ws, "Error", "An internal error occurred")
