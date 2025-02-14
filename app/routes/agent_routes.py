from app.clients.credentials import CLIENT_CREDENTIALS
from flask import Blueprint, request, jsonify
from app.utils.validation import validate_token
from app.messages.mappings import map_chat_history_to_langchain
from app.server.setup import create_agent_executor

agent_routes = Blueprint("agent_routes", __name__)
api_key_to_agent = {}

for key, value in CLIENT_CREDENTIALS.items():
    agent_executor = create_agent_executor(
        value["COLLECTION_NAME"],
        value["RETRIEVER_TOOL_NAME"],
        value["PROMPT"],
        value["HUB"],
    )
    api_key_to_agent[key] = agent_executor


def get_agent_executor(api_key):
    if api_key in api_key_to_agent:
        return api_key_to_agent[api_key]
    else:
        raise KeyError(f"Agent executor not found for API key: {api_key}")


@agent_routes.route("/agent", methods=["POST"])
@validate_token("markov_decision_process")
def agent_route():
    try:
        payload = request.get_json()
        if not payload:
            return jsonify({"error": "Invalid request payload"}), 400

        input_message = payload.get("input")
        if not input_message:
            return jsonify({"error": "Input message is required"}), 400

        client_chat_history = payload.get("chat_history")
        if not client_chat_history:
            return jsonify({"error": "Chat history is required"}), 400

        # Being appended in @validate_token
        api_key = request.api_key
        if not api_key:
            return jsonify({"error": "Could not identify client"}), 400

        if api_key not in CLIENT_CREDENTIALS:
            return jsonify({"error": "Client not allowed"}), 400

        langchain_chat_history = map_chat_history_to_langchain(client_chat_history)
        input_data = {"input": input_message, "chat_history": langchain_chat_history}

        client_agent_executor = get_agent_executor(api_key)
        response = client_agent_executor.invoke(input_data)

        output = response["output"]
        return jsonify({"output": output}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
