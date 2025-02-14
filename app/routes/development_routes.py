from flask import Blueprint, jsonify

development_routes = Blueprint("development_routes", __name__)


@development_routes.route("/dev", methods=["POST"])
def dev():
    try:
        return jsonify({}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
