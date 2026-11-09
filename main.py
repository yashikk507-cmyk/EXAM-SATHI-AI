
import os
import uuid
import time
import hmac
import hashlib
import secrets
import logging

from collections import defaultdict, deque

from dotenv import load_dotenv
from fastapi import (
    FastAPI,
    UploadFile,
    File,
    Form,
    HTTPException,
    Request
)
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from rag_engine import add_pdf_to_database
from ai_engine import generate_answer
from voice_engine import process_voice_question
from tts_engine import generate_speech
from rag_answer import generate_rag_response


# ==========================================
# ENVIRONMENT CONFIGURATION
# ==========================================

load_dotenv()

SESSION_SECRET = os.getenv("EXAMSAATHI_SESSION_SECRET")

if not SESSION_SECRET:
    SESSION_SECRET = secrets.token_hex(32)
    logging.warning(
        "EXAMSAATHI_SESSION_SECRET is not configured. "
        "Sessions will be invalidated when the server restarts."
    )

SESSION_SECRET = SESSION_SECRET.encode("utf-8")

COOKIE_SECURE = (
    os.getenv("COOKIE_SECURE", "false").lower() == "true"
)


# ==========================================
# APPLICATION CONFIGURATION
# ==========================================

MAX_PDF_SIZE = 10 * 1024 * 1024
MAX_AUDIO_SIZE = 10 * 1024 * 1024
MAX_QUESTION_LENGTH = 2000

ALLOWED_LANGUAGES = ["en-IN", "hi-IN"]

UPLOAD_DIR = "uploads"
AUDIO_DIR = "generated_audio"

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(AUDIO_DIR, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

logger = logging.getLogger("ExamSaathi")

app = FastAPI(
    title="ExamSaathi AI",
    version="3.0.1",
    description="Your Personal AI Tutor"
)


# ==========================================
# REQUEST MODELS
# ==========================================

class QuestionRequest(BaseModel):

    question: str = Field(
        min_length=1,
        max_length=MAX_QUESTION_LENGTH
    )

    language_code: str = Field(
        default="en-IN",
        pattern="^(en-IN|hi-IN)$"
    )


class RAGQuestionRequest(BaseModel):

    question: str = Field(
        min_length=1,
        max_length=MAX_QUESTION_LENGTH
    )

    language_code: str = Field(
        default="en-IN",
        pattern="^(en-IN|hi-IN)$"
    )


# ==========================================
# ANONYMOUS SESSION SECURITY
# ==========================================

COOKIE_NAME = "exam_session"
SESSION_MAX_AGE = 7 * 24 * 60 * 60


def sign_session(session_id: str):

    return hmac.new(
        SESSION_SECRET,
        session_id.encode("utf-8"),
        hashlib.sha256
    ).hexdigest()


def get_valid_session(cookie_value):

    if not cookie_value or len(cookie_value) > 512:
        return None

    try:

        session_id, signature = cookie_value.split(".", 1)

        expected_signature = sign_session(session_id)

        if not hmac.compare_digest(
            signature,
            expected_signature
        ):
            return None

        return session_id

    except (ValueError, TypeError):
        return None


@app.middleware("http")
async def anonymous_session_middleware(request: Request, call_next):

    cookie_value = request.cookies.get(COOKIE_NAME)

    session_id = get_valid_session(cookie_value)

    if not session_id:
        session_id = secrets.token_urlsafe(32)

    request.state.session_id = session_id

    response = await call_next(request)

    signature = sign_session(session_id)

    response.set_cookie(
        key=COOKIE_NAME,
        value=f"{session_id}.{signature}",
        max_age=SESSION_MAX_AGE,
        httponly=True,
        secure=COOKIE_SECURE,
        samesite="lax",
        path="/"
    )

    return response


# ==========================================
# SECURITY HEADERS
# ==========================================

def add_security_headers(response):

    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"

    response.headers["Referrer-Policy"] = (
        "strict-origin-when-cross-origin"
    )

    response.headers["Permissions-Policy"] = (
        "camera=(self), microphone=(self), "
        "geolocation=(), payment=()"
    )

    response.headers["Cache-Control"] = "no-store"

    return response


@app.middleware("http")
async def security_headers(request: Request, call_next):

    response = await call_next(request)

    return add_security_headers(response)


# ==========================================
# RATE LIMITING
# ==========================================

RATE_LIMITS = {
    "/ask": (5, 60),
    "/ask-voice": (3, 60),
    "/ask-rag": (10, 60),
    "/upload-pdf": (2, 3600)
}

request_records = defaultdict(deque)


@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):

    path = request.url.path

    if path not in RATE_LIMITS:
        return await call_next(request)

    limit, window = RATE_LIMITS[path]

    client_ip = (
        request.client.host
        if request.client
        else "unknown"
    )

    current_time = time.monotonic()

    records = request_records[client_ip]

    # Remove expired requests
    while records and current_time - records[0][1] >= records[0][2]:
        records.popleft()

    # Count requests for this endpoint
    endpoint_count = sum(
        1
        for endpoint, timestamp, duration in records
        if endpoint == path
        and current_time - timestamp < duration
    )

    if endpoint_count >= limit:

        response = JSONResponse(
            status_code=429,
            content={
                "detail": "Request limit reached. Please try again later."
            }
        )

        return add_security_headers(response)

    records.append((path, current_time, window))

    return await call_next(request)


# ==========================================
# HELPER FUNCTIONS
# ==========================================

def validate_question(question: str):

    if not question.strip():

        raise HTTPException(
            status_code=400,
            detail="Question cannot be empty."
        )


def cleanup_old_audio():

    current_time = time.time()
    expiry_seconds = 60 * 60

    try:

        for filename in os.listdir(AUDIO_DIR):

            if not filename.endswith(".wav"):
                continue

            file_path = os.path.join(
                AUDIO_DIR,
                filename
            )

            if not os.path.isfile(file_path):
                continue

            if (
                current_time - os.path.getmtime(file_path)
                > expiry_seconds
            ):

                os.remove(file_path)

    except Exception:

        logger.exception("Audio cleanup failed")


# ==========================================
# STATIC FILES
# ==========================================

app.mount(
    "/static",
    StaticFiles(directory="static"),
    name="static"
)


# ==========================================
# HOME PAGE
# ==========================================

@app.get("/")
def home():

    return {
        "message": "ExamSaathi AI is running!",
        "status": "online",
        "version": "3.0.1"
    }


@app.get("/app")
def frontend():

    return FileResponse("static/index.html")


# ==========================================
# NORMAL TEXT QUESTION
# ==========================================

@app.post("/ask")
def ask_question(data: QuestionRequest):

    validate_question(data.question)

    cleanup_old_audio()

    try:

        answer = generate_answer(
            data.question,
            data.language_code
        )

        audio_url = None

        audio_filename = f"{uuid.uuid4().hex}.wav"

        audio_path = os.path.join(
            AUDIO_DIR,
            audio_filename
        )

        try:

            generate_speech(
                answer,
                audio_path,
                data.language_code
            )

            if os.path.isfile(audio_path):
                audio_url = f"/audio/{audio_filename}"

        except Exception:

            logger.exception("TTS generation failed")

            if os.path.exists(audio_path):
                os.remove(audio_path)

        return {
            "question": data.question,
            "answer": answer,
            "audio_url": audio_url,
            "tts_status": "success" if audio_url else "failed"
        }

    except Exception:

        logger.exception("Error in /ask")

        raise HTTPException(
            status_code=500,
            detail="Unable to generate your answer. Please try again."
        )


# ==========================================
# VOICE QUESTION
# ==========================================

@app.post("/ask-voice")
async def ask_voice(
    request: Request,
    audio: UploadFile = File(...),
    language_code: str = Form("en-IN")
):

    if language_code not in ALLOWED_LANGUAGES:

        raise HTTPException(
            status_code=400,
            detail="Unsupported response language."
        )

    if (
        not audio.filename
        or not audio.filename.lower().endswith(".wav")
    ):

        raise HTTPException(
            status_code=400,
            detail="Please upload a WAV audio file."
        )

    cleanup_old_audio()

    file_name = f"{uuid.uuid4().hex}.wav"

    audio_path = os.path.join(
        UPLOAD_DIR,
        file_name
    )

    total_size = 0

    try:

        with open(audio_path, "wb") as output_file:

            while True:

                chunk = await audio.read(1024 * 1024)

                if not chunk:
                    break

                total_size += len(chunk)

                if total_size > MAX_AUDIO_SIZE:

                    raise HTTPException(
                        status_code=413,
                        detail="Audio size cannot exceed 10 MB."
                    )

                output_file.write(chunk)

        if total_size == 0:

            raise HTTPException(
                status_code=400,
                detail="Empty audio file."
            )

        with open(audio_path, "rb") as audio_file:
            header = audio_file.read(12)

        if (
            len(header) < 12
            or header[:4] != b"RIFF"
            or header[8:12] != b"WAVE"
        ):

            raise HTTPException(
                status_code=400,
                detail="Invalid WAV audio file."
            )

        question, answer, generated_audio_path = (
            process_voice_question(
                audio_path,
                language_code
            )
        )

        audio_url = None

        if (
            generated_audio_path
            and os.path.isfile(generated_audio_path)
        ):

            audio_filename = os.path.basename(
                generated_audio_path
            )

            audio_url = f"/audio/{audio_filename}"

        return {
            "question": question,
            "answer": answer,
            "audio_url": audio_url,
            "tts_status": "success" if audio_url else "failed"
        }

    except HTTPException:
        raise

    except Exception:

        logger.exception("Error in /ask-voice")

        raise HTTPException(
            status_code=500,
            detail="Voice processing failed. Please try again."
        )

    finally:

        if os.path.exists(audio_path):
            os.remove(audio_path)

        await audio.close()


# ==========================================
# INDIVIDUAL AUDIO RESPONSE
# ==========================================

@app.get("/audio/{filename}")
def get_audio(filename: str):

    if (
        not filename.endswith(".wav")
        or os.path.basename(filename) != filename
    ):

        raise HTTPException(
            status_code=400,
            detail="Invalid audio filename."
        )

    audio_path = os.path.join(
        AUDIO_DIR,
        filename
    )

    if not os.path.isfile(audio_path):

        raise HTTPException(
            status_code=404,
            detail="Audio not found."
        )

    return FileResponse(
        audio_path,
        media_type="audio/wav",
        filename="answer.wav"
    )


# ==========================================
# PDF UPLOAD
# ==========================================

@app.post("/upload-pdf")
async def upload_pdf(
    request: Request,
    upload: UploadFile = File(...)
):

    if (
        not upload.filename
        or not upload.filename.lower().endswith(".pdf")
    ):

        raise HTTPException(
            status_code=400,
            detail="Only PDF files are allowed."
        )

    file_name = f"{uuid.uuid4().hex}.pdf"

    pdf_path = os.path.join(
        UPLOAD_DIR,
        file_name
    )

    total_size = 0

    try:

        with open(pdf_path, "wb") as output_file:

            while True:

                chunk = await upload.read(1024 * 1024)

                if not chunk:
                    break

                total_size += len(chunk)

                if total_size > MAX_PDF_SIZE:

                    raise HTTPException(
                        status_code=413,
                        detail="PDF size cannot exceed 10 MB."
                    )

                if total_size == len(chunk):

                    if not chunk.startswith(b"%PDF-"):

                        raise HTTPException(
                            status_code=400,
                            detail="Invalid PDF file."
                        )

                output_file.write(chunk)

        if total_size == 0:

            raise HTTPException(
                status_code=400,
                detail="Empty PDF file."
            )

        total_chunks = add_pdf_to_database(
            pdf_path,
            session_id=request.state.session_id
        )

        return {
            "message": "PDF uploaded and processed successfully!",
            "chunks_added": total_chunks
        }

    except HTTPException:
        raise

    except Exception:

        logger.exception("PDF processing failed")

        raise HTTPException(
            status_code=500,
            detail="PDF processing failed. Please try again."
        )

    finally:

        if os.path.exists(pdf_path):
            os.remove(pdf_path)

        await upload.close()


# ==========================================
# RAG QUESTION ANSWERING
# ==========================================

@app.post("/ask-rag")
def ask_rag(
    data: RAGQuestionRequest,
    request: Request
):

    validate_question(data.question)

    try:

        result = generate_rag_response(
            data.question,
            session_id=request.state.session_id,
            output_language=data.language_code
        )

        return {
            "question": data.question,
            "answer": result["answer"],
            "sources": result["sources"],
            "mode": "RAG"
        }

    except Exception:

        logger.exception("Error in /ask-rag")

        raise HTTPException(
            status_code=500,
            detail="Unable to process your study notes question."
        )
