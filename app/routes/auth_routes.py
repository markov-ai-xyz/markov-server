from flask import Blueprint, request, jsonify
from app.clients.credentials import WHITELISTED_API_KEYS
from app.sql.auth_crud import create_auth, update_auth, validate_auth
from app.utils.api_keys import generate_api_key
from app.utils.validation import create_token, validate_token

auth_routes = Blueprint("auth_routes", __name__)


@auth_routes.route("/validate-api-key", methods=["POST"])
def validate_api_key():
    api_key = request.headers.get("X-API-KEY")

    if api_key in WHITELISTED_API_KEYS:
        token = create_token(api_key, "markov_decision_process")
        return jsonify({"token": token}), 200
    return jsonify({"message": "Invalid API key"}), 401


@auth_routes.route("/validate-login", methods=["POST"])
@validate_token("markov_decision_process")
def validate_login():
    return jsonify({"message": "Token is valid"}), 200


@auth_routes.route("/generate-api-key", methods=["POST"])
def generate_api_key_for_user_id():
    user_id = request.json.get('user_id')
    if not user_id:
        return jsonify({"error": "User ID is required"}), 400
    return generate_api_key(user_id)


@auth_routes.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    if validate_auth(username, password):
        token = create_token("Admin", "markov_decision_process")
        return jsonify({"token": token}), 200
    return jsonify({"message": "Invalid credentials"}), 401


@auth_routes.route("/sign-up", methods=["POST"])
def sign_up():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    create_auth(username, password)
    token = create_token("Admin", "markov_decision_process")
    return jsonify({"token": token}), 200


@auth_routes.route("/update-password", methods=["POST"])
def update_password():
    data = request.get_json()
    username = data.get("username")
    old_password = data.get("old_password")
    new_password = data.get("new_password")

    if not validate_auth(username, old_password):
        return jsonify({"message": "Invalid credentials"}), 401
    else:
        update_auth(username, new_password)
        token = create_token("Admin", "markov_decision_process")
        return jsonify({"token": token}), 200


# TODO: Add logic for building customer SSO tokens; don't return Admin
