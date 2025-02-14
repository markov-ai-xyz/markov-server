from flask import request, jsonify
from functools import wraps
from app.sql.api_key_crud import create_api_key, validate_api_key


def generate_api_key(user_id):
    api_key = create_api_key(user_id)
    if api_key:
        return jsonify({"api_key": api_key}), 201
    return jsonify({"error": "Failed to create API key"}), 500


def require_api_key(view_function):
    @wraps(view_function)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        if not api_key:
            return jsonify({"error": "API key is missing"}), 401

        if validate_api_key(api_key):
            return view_function(*args, **kwargs)

        return jsonify({"error": "Invalid API key"}), 401

    return decorated_function


if __name__ == '__main__':
    generated_api_key = generate_api_key("some_cool_user")
    print(f"Generated API-Key: {generated_api_key}")

