from dotenv import load_dotenv
from flask import Blueprint, request, jsonify
from app.exporters.pinecone_db import PineconeLoader
from app.aws.s3 import download_large_file_from_s3, get_s3_client
from app.utils.api_keys import require_api_key
from urllib.parse import urlparse
import os

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")

transformation_routes = Blueprint("transformation_routes", __name__)

s3_client = get_s3_client()
pinecone_loader = PineconeLoader(
    pinecone_api_key=PINECONE_API_KEY,
    index_name="markov",
    openai_api_key=OPENAI_API_KEY
)


@transformation_routes.route("/embeddings", methods=["POST"])
@require_api_key
def generate_embeddings():
    try:
        payload = request.get_json()
        if not payload:
            return jsonify({"error": "Invalid request payload"}), 400

        input_message = payload.get("input")
        if not input_message:
            return jsonify({"error": "Input message is required"}), 400

        pinecone_loader.process_text(input_message)
        return jsonify({"message": "Success"}), 200
    except Exception as e:
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500


@transformation_routes.route("/ref-embeddings", methods=["POST"])
@require_api_key
def generate_ref_embeddings():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400

        markov_s3_key = data.get("markov_s3_key")
        if not markov_s3_key:
            return jsonify({"error": "All parameters weren't supplied"}), 400

        parsed_url = urlparse(markov_s3_key)
        file_name = parsed_url.path.lstrip("/")
        file_path = download_large_file_from_s3(markov_s3_key, file_name)
        pinecone_loader.process_file(file_path)
        return jsonify({"message": "Success"}), 200

    except Exception as e:
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500


@transformation_routes.route("/query-embeddings", methods=["POST"])
@require_api_key
def query_embeddings():
    try:
        payload = request.get_json()
        if not payload:
            return jsonify({"error": "Invalid request payload"}), 400

        query = payload.get("query")
        top_k = payload.get("top_k")
        if not query:
            return jsonify({"error": "Query is required"}), 400

        query_results = pinecone_loader.search(query, top_k)
        results = {
            "matches": [
                {
                    "id": match.id,
                    "score": match.score,
                    "metadata": match.metadata,
                    "values": match.values,
                }
                for match in query_results.matches
            ],
            "namespace": query_results.namespace,
        }
        return jsonify(results), 200

    except Exception as e:
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500



