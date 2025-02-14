from flask import Blueprint, request, jsonify
from app.loggers.custom import logger
from app.sql.user_crud import update_user

location_routes = Blueprint("location_routes", __name__)


@location_routes.route("/location", methods=["POST"])
def extract_location_from_lat_long():
    try:
        data = request.get_json()
        phone = data.get("phone")
        formatted_location = data.get("location")
        return update_db_with_location(phone, formatted_location)

    except Exception as e:
        logger.error(f"Error in handling POST request: {str(e)}")
        return jsonify({"output": "Error"}), 500


def update_db_with_location(phone, concatenated_location):
    logger.info(f"Updating {phone} with location: {concatenated_location}")
    update_user(phone=phone, location=concatenated_location)
    return jsonify({"output": "OK"}), 200
