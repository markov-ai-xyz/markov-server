import assemblyai as aai
import os
from dotenv import load_dotenv
from typing import Any, Dict

load_dotenv()

ASSEMBLY_AI_API_KEY = os.getenv("ASSEMBLY_AI_API_KEY")
aai.settings.api_key = ASSEMBLY_AI_API_KEY
transcriber = aai.Transcriber()


def parse(file_path: str, kwargs: Dict[str, Any]) -> Dict[str, Any]:
    transcript = transcriber.transcribe(file_path)

    if transcript.status == aai.TranscriptStatus.error:
        raise ValueError(f"Transcription failed: {transcript.error}")
    else:
        return {"utterances": transcript.utterances, "transcript": transcript.text}
