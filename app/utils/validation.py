from datetime import datetime, timedelta
from flask import request, jsonify
from functools import wraps
from jwt import decode, encode, ExpiredSignatureError, InvalidTokenError


def extract_user_as_api_key(token, secret_key):
    try:
        decoded = decode(token, secret_key, algorithms=["HS256"])
        return decoded.get("user")
    except (ExpiredSignatureError, InvalidTokenError):
        return False


def extract_token(header_value):
    if header_value and header_value.startswith("Bearer "):
        return header_value.split("Bearer ")[1]
    return None


def validate_token(secret_key):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            token = extract_token(request.headers.get("Authorization"))
            api_key = extract_user_as_api_key(token, secret_key)
            if api_key:
                request.api_key = api_key
                return f(*args, **kwargs)
            return jsonify({"error": "Unauthorized"}), 401

        return decorated_function

    return decorator


def create_token(user, secret_key, expiration_minutes=30):
    return encode(
        {
            "user": user,
            "exp": datetime.utcnow() + timedelta(minutes=expiration_minutes),
        },
        secret_key,
        algorithm="HS256",
    )


if __name__ == "__main__":
    dev_user = "dev_user"
    dev_secret_key = "markov_decision_process"
    dev_token = create_token(dev_user, dev_secret_key)
    print(f"Generated token: {dev_token}")
