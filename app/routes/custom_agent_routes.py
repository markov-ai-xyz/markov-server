from app.clients.credentials import EREKRUT_API_KEY
from dotenv import load_dotenv
from flask import Blueprint, request, jsonify
from app.utils.validation import validate_token
from app.messages.mappings import map_chat_history_to_langchain
from app.server.setup import create_sql_engine, create_rag_only_agent
from app.models.erekrut_model import structured_parser
import traceback
import assemblyai as aai
import os
from threading import Thread
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from app.sql.user_crud import update_user

load_dotenv()
ASSEMBLY_AI_API_KEY = os.getenv("ASSEMBLY_AI_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

aai.settings.api_key = ASSEMBLY_AI_API_KEY
transcriber = aai.Transcriber()
custom_agent_routes = Blueprint("custom_agent_routes", __name__)
create_sql_engine()
erekrut_agent = create_rag_only_agent(
    "erekrut",
    "erekrut_retriever",
    "Search for jobs, but no more than 3! You must use this tool when finding job titles. If you find related titles, share them with the user verbatim and ask for his years of experience and email address in order to confirm his registration. Reiterate the exact jobs you found for his tenure once he provides his years of experience and email, and confirm his registration.",
    "anant-chandra/recruiter",
)


@custom_agent_routes.route("/erekrut-agent-audio", methods=["POST"])
@validate_token("markov_decision_process")
def erekrut_agent_audio_route():
    try:
        if "audio" not in request.files:
            return jsonify({"error": "No audio file provided"}), 400

        audio_file = request.files["audio"]

        file_path = f"temp_{audio_file.filename}"
        audio_file.save(file_path)

        transcript = transcriber.transcribe(file_path)

        if transcript.status == aai.TranscriptStatus.error:
            return jsonify({"error": str(transcript.error)}), 500

        audio_text = transcript.text

        return jsonify({"output": audio_text}), 200

    except Exception as e:
        print("Error processing audio:", str(e))
        return jsonify({"error": "An error occurred while processing the audio"}), 500


@custom_agent_routes.route("/erekrut-agent", methods=["POST"])
@validate_token("markov_decision_process")
def erekrut_agent_route():
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

        client_phone_number = payload.get("phone_number")
        if not client_phone_number:
            return jsonify({"error": "Phone number is required"}), 400

        # Being appended in @validate_token
        api_key = request.api_key
        if not api_key:
            return jsonify({"error": "Could not identify client"}), 400

        if api_key != EREKRUT_API_KEY:
            return jsonify({"error": "Client not allowed"}), 400

        langchain_chat_history = map_chat_history_to_langchain(client_chat_history)
        input_data = {"input": input_message, "chat_history": langchain_chat_history}

        agent_response = erekrut_agent.invoke(input_data)
        output_message = agent_response["output"]

        thread = Thread(
            target=process_output_message,
            args=(input_message, output_message, client_phone_number),
        )
        thread.start()

        return jsonify({"output": output_message}), 200

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


def process_output_message(input_message, output_message, client_phone_number):
    try:
        user_input = f"{input_message}. {output_message}"
        model = ChatOpenAI(
            api_key=OPENAI_API_KEY,
            model="gpt-3.5-turbo",
            temperature=0,
        )
        format_instructions = structured_parser.get_format_instructions()

        prompt_template = PromptTemplate(
            template="Map the user input to the format instructions if possible. Don't make any assumptions or try mapping values if they don't exist; let the key map to an empty string or empty list in the JSON, depending on the type. You should be 100% confident about the mapping."
            "\n{user_input}\n\nThe output should be a JSON object formatted according to these keys, where missing values are represented as empty strings or empty lists as appropriate:\n{format_instructions}",
            input_variables=["user_input"],
            partial_variables={"format_instructions": format_instructions},
        )

        chain = prompt_template | model | structured_parser
        structured_response = chain.invoke({"user_input": user_input})
        print(structured_response)

        years_of_experience = structured_response.get("years_of_experience")
        job_designations = structured_response.get("job_designations")
        email = structured_response.get("email")

        update_user(
            client_phone_number,
            None,
            None,
            email,
            job_designations,
            years_of_experience,
        )

    except Exception as e:
        traceback.print_exc()
