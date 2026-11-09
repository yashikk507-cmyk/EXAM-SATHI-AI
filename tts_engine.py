
import os
import re
import time
import wave
import logging
from io import BytesIO

from dotenv import load_dotenv
from gnani.tts import GnaniTTSClient, AudioConfig

load_dotenv()

logger = logging.getLogger(__name__)

API_KEY = os.getenv("GNANI_API_KEY_ID")

if not API_KEY:
    raise ValueError("GNANI_API_KEY_ID is missing from your .env file")

client = GnaniTTSClient(api_key=API_KEY)

MAX_CHUNK_SIZE = 1200
MAX_ATTEMPTS = 3


def split_text(text, max_chars=MAX_CHUNK_SIZE):
    """Split long text into smaller sentence-aware chunks."""

    if not text or not text.strip():
        raise ValueError("TTS text cannot be empty")

    text = text.strip()
    sentences = re.split(r"(?<=[.!?])\s+|\n+", text)

    chunks = []
    current = ""

    for sentence in sentences:
        sentence = sentence.strip()

        if not sentence:
            continue

        while len(sentence) > max_chars:
            if current:
                chunks.append(current)
                current = ""

            split_at = sentence.rfind(" ", 0, max_chars)

            if split_at <= 0:
                split_at = max_chars

            chunks.append(sentence[:split_at].strip())
            sentence = sentence[split_at:].strip()

        candidate = f"{current} {sentence}".strip() if current else sentence

        if len(candidate) <= max_chars:
            current = candidate
        else:
            if current:
                chunks.append(current)
            current = sentence

    if current:
        chunks.append(current)

    return chunks


def synthesize_chunk(text, language_code):
    """Generate one audio chunk with retry support."""

    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            logger.info(
                "TTS attempt %s/%s | characters=%s",
                attempt,
                MAX_ATTEMPTS,
                len(text)
            )

            audio = client.synthesize(
                text,
                voice="Nalini",
                model="timbre-v2.5",
                language=language_code,
                speed=1.0,
                audio_config=AudioConfig(
                    container="wav",
                    sample_rate=48000
                )
            )

            if not isinstance(audio, bytes) or len(audio) < 44:
                raise RuntimeError("Invalid or empty audio response")

            with wave.open(BytesIO(audio), "rb") as wav:
                if wav.getcomptype() != "NONE":
                    raise RuntimeError("Unsupported WAV compression")

                audio_frames = wav.readframes(wav.getnframes())
                audio_params = wav.getparams()

            return audio_frames, audio_params

        except Exception as error:
            status_code = getattr(error, "status_code", None)

            logger.exception("TTS attempt %s failed", attempt)

            if status_code not in {500, 502, 503, 504}:
                raise RuntimeError(f"TTS error: {error}") from error

            if attempt == MAX_ATTEMPTS:
                raise RuntimeError(
                    f"TTS failed after {MAX_ATTEMPTS} attempts: {error}"
                ) from error

            time.sleep(attempt)


def combine_audio_chunks(audio_chunks, output_file):
    """Combine compatible WAV audio chunks into one WAV file."""

    if not audio_chunks:
        raise RuntimeError("No audio chunks were generated")

    reference_params = audio_chunks[0][1]
    all_frames = []

    for frames, params in audio_chunks:
        if (
            params.nchannels != reference_params.nchannels
            or params.sampwidth != reference_params.sampwidth
            or params.framerate != reference_params.framerate
            or params.comptype != reference_params.comptype
        ):
            raise RuntimeError("Incompatible WAV audio formats")

        all_frames.append(frames)

    output_dir = os.path.dirname(os.path.abspath(output_file))
    os.makedirs(output_dir, exist_ok=True)

    temp_file = output_file + ".tmp"

    try:
        with wave.open(temp_file, "wb") as output:
            output.setnchannels(reference_params.nchannels)
            output.setsampwidth(reference_params.sampwidth)
            output.setframerate(reference_params.framerate)
            output.setcomptype(
                reference_params.comptype,
                reference_params.compname
            )
            output.writeframes(b"".join(all_frames))

        os.replace(temp_file, output_file)

    finally:
        if os.path.exists(temp_file):
            os.remove(temp_file)

    logger.info("Complete audio saved: %s", output_file)


def generate_speech(
    text,
    output_file="answer.wav",
    language_code="en-IN"
):
    """Generate complete speech, splitting long answers automatically."""

    chunks = split_text(text)

    logger.info(
        "Starting TTS | characters=%s | chunks=%s | language=%s",
        len(text),
        len(chunks),
        language_code
    )

    audio_chunks = []

    for index, chunk in enumerate(chunks, start=1):
        logger.info("Generating chunk %s/%s", index, len(chunks))

        audio_frames, audio_params = synthesize_chunk(
            chunk,
            language_code
        )

        audio_chunks.append((audio_frames, audio_params))

    combine_audio_chunks(audio_chunks, output_file)

    return output_file
