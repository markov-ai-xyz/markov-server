import os
import requests
import threading
import uuid
from flask import Blueprint, request, jsonify
from app.aws.s3 import download_large_file_from_s3, get_s3_client
from app.enums.status import Status
from app.processors.upload import (
    process_audio,
    process_pdf,
    process_image,
)
from app.parsers.audio import parse as parse_audio
from app.parsers.document import parse_pdf
from app.parsers.image import parse as parse_image
from app.parsers.video import parse as parse_video
from app.utils.api_keys import require_api_key
from urllib.parse import urlparse
from botocore.exceptions import ClientError, NoCredentialsError

ingestion_routes = Blueprint("ingestion_routes", __name__)

FILE_TYPE_TO_PARSER_MAP = {
    ".jpeg": parse_image,
    ".jpg": parse_image,
    ".m4a": parse_audio,
    ".mp3": parse_audio,
    ".mp4": parse_video,
    ".pdf": parse_pdf,
    ".png": parse_image,
    ".wav": parse_audio,
}

FILE_TYPE_TO_PROCESSOR_MAP = {
    ".jpeg": process_image,
    ".jpg": process_image,
    ".m4a": process_audio,
    ".mp3": process_audio,
    ".pdf": process_pdf,
    ".png": process_image,
    ".wav": process_audio,
}

# TODO: Migrate to CockroachDB
WHITELISTED_API_KEYS = ["dev_user"]
# TODO: Migrate to Redis
task_status = {}
s3_client = get_s3_client()


@ingestion_routes.route("/local-upload", methods=["POST"])
@require_api_key
def local_upload():
    try:
        if "file" not in request.files:
            return jsonify({"message": "No file uploaded"}), 400

        file = request.files["file"]
        if not file or file.filename == "":
            return jsonify({"message": "No file selected"}), 400

        s3_client.upload_fileobj(file, "file-destination", file.filename)
        return jsonify(
            {"message": "File uploaded successfully"}
        ), 200

    except Exception as e:
        return jsonify({"message": f"S3 upload failed: {str(e)}"}), 500


@ingestion_routes.route("/stream", methods=["POST"])
@require_api_key
def stream_artifact():
    try:
        data = request.json
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400

        pre_signed_url = data.get("pre_signed_url")
        parsed_url = urlparse(pre_signed_url)
        source_key = parsed_url.path.lstrip("/")
        print(f"Transferring: {source_key}")

        response = requests.get(pre_signed_url, stream=True)
        response.raise_for_status()

        s3_client.upload_fileobj(response.raw, "file-destination", source_key)
        return (
            jsonify(
                {"message": f"File {source_key} has been transferred successfully"}
            ),
            200,
        )

    except NoCredentialsError:
        return jsonify({"error": "Destination credentials not available"}), 400
    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        error_message = e.response["Error"]["Message"]
        return jsonify({"error": f"AWS Error: {error_code} - {error_message}"}), 401
    except requests.RequestException as e:
        return jsonify({"error": f"Error accessing pre-signed URL: {str(e)}"}), 401
    except Exception as e:
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500


@ingestion_routes.route("/stream-async", methods=["POST"])
@require_api_key
def stream_artifact_async():
    try:
        data = request.json
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400

        pre_signed_url = data.get("pre_signed_url")
        parsed_url = urlparse(pre_signed_url)
        source_key = parsed_url.path.lstrip("/")
        task_id = str(uuid.uuid4())

        threading.Thread(
            target=transfer_file, args=(task_id, pre_signed_url, source_key)
        ).start()
        return jsonify({"task_id": task_id, "message": "File transfer started"}), 200

    except Exception as e:
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500


def transfer_file(task_id, pre_signed_url, source_key):
    task_status[task_id] = {"status": Status.IN_PROGRESS, "message": "Transfer started"}
    try:
        response = requests.get(pre_signed_url, stream=True)
        response.raise_for_status()

        s3_client.upload_fileobj(response.raw, "file-destination", source_key)
        task_status[task_id] = {
            "status": Status.DONE,
            "message": f"File {source_key} has been transferred successfully",
        }

    except Exception as e:
        task_status[task_id] = {
            "status": Status.ABANDONED,
            "message": f"An error occurred: {str(e)}",
        }


@ingestion_routes.route("/status/<task_id>", methods=["GET"])
@require_api_key
def check_status(task_id):
    status_info = task_status.get(
        task_id, {"status": Status.ABANDONED, "message": "Task not found"}
    )
    return jsonify(
        {
            "status": status_info["status"].name,
            "status_code": status_info["status"].value,
            "message": status_info["message"],
        }
    )


@ingestion_routes.route("/parse", methods=["POST"])
@require_api_key
def parse_link():
    try:
        data = request.json
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400

        kwargs = data.get("kwargs")
        markov_s3_key = data.get("markov_s3_key")
        if not kwargs or not markov_s3_key:
            return jsonify({"error": "All parameters weren't supplied"}), 400

        parsed_url = urlparse(markov_s3_key)
        file_name = parsed_url.path.lstrip("/")
        file_path = download_large_file_from_s3(markov_s3_key, file_name)
        file_extension = os.path.splitext(file_path)[1]

        if file_extension in FILE_TYPE_TO_PARSER_MAP:
            response = FILE_TYPE_TO_PARSER_MAP[file_extension](file_path, kwargs)
            return jsonify(response), 200
        return jsonify({"error": f"{file_extension} isn't supported"}), 400

    except Exception as e:
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500


@ingestion_routes.route("/process", methods=["POST"])
@require_api_key
def process_link():
    try:
        data = request.json
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400

        kwargs = data.get("kwargs")
        markov_s3_key = data.get("markov_s3_key")
        if not kwargs or not markov_s3_key:
            return jsonify({"error": "All parameters weren't supplied"}), 400

        parsed_url = urlparse(markov_s3_key)
        file_name = parsed_url.path.lstrip("/")
        file_path = download_large_file_from_s3(markov_s3_key, file_name)
        file_extension = os.path.splitext(file_path)[1]

        if file_extension in FILE_TYPE_TO_PROCESSOR_MAP:
            response = FILE_TYPE_TO_PROCESSOR_MAP[file_extension](file_path, kwargs)
            # TODO: Unify format and jsonify
            return response, 200
        return jsonify({"error": f"{file_extension} isn't supported"}), 400

    except Exception as e:
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500
