
import os
import uuid
import requests
from dotenv import load_dotenv

from ai_engine import generate_answer
from tts_engine import generate_speech

load_dotenv()

API_KEY = os.getenv("GNANI_API_KEY_ID")

AUDIO_DIR = "generated_audio"
os.makedirs(AUDIO_DIR, exist_ok=True)


def process_voice_question(audio_path, output_language="en-IN"):

    if not API_KEY:
        raise RuntimeError("Gnani API key is missing from .env")

    print("Detecting spoken language...")

    url = "https://api.vachana.ai/stt/v3"

    headers = {
        "X-API-Key-ID": API_KEY
    }

    with open(audio_path, "rb") as audio:

        response = requests.post(
            url,
            headers=headers,
            files={
                "audio_file": (
                    os.path.basename(audio_path),
                    audio,
                    "audio/wav"
                )
            },
            data={
                "language_code": "indic-auto",
                "model": "prisma-v3.0",
                "format": "codemix"
            },
            timeout=60
        )

    response.raise_for_status()

    result = response.json()

    if not result.get("success"):
        raise RuntimeError("Prisma transcription failed.")

    question = result["transcript"]

    detected_language = result.get(
        "detected_language_code", "unknown"
    )

    print("Detected language:", detected_language)
    print("You asked:", question)

    print("ExamSaathi is thinking...")

    answer = generate_answer(question, output_language)

    print("ExamSaathi:", answer)

    audio_filename = f"{uuid.uuid4().hex}.wav"
    audio_path_output = os.path.join(AUDIO_DIR, audio_filename)

    audio_url = None

    try:
        generate_speech(
            answer,
            audio_path_output,
            output_language
        )

        if os.path.exists(audio_path_output):
            audio_url = audio_path_output
            print("TTS generated successfully.")

    except Exception as e:
        print("TTS failed, but the text answer is available:", e)

    return question, answer, audio_url
