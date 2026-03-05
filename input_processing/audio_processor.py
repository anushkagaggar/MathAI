import os
import math
from groq import Groq
from dotenv import load_dotenv

from utils.confidence import estimate_asr_confidence, is_below_threshold
from utils.formatting import normalize_math_text, clean_whitespace

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

WHISPER_MODEL = os.getenv("GROQ_WHISPER_MODEL", "whisper-large-v3")

# Formats natively supported by Groq Whisper
SUPPORTED_FORMATS = {".mp3", ".mp4", ".mpeg", ".mpga", ".m4a", ".wav", ".webm", ".ogg", ".flac"}

MIMETYPE_MAP = {
    ".mp3": "audio/mpeg",
    ".mp4": "audio/mp4",
    ".mpeg": "audio/mpeg",
    ".mpga": "audio/mpeg",
    ".m4a": "audio/mp4",
    ".wav": "audio/wav",
    ".webm": "audio/webm",
    ".ogg": "audio/ogg",
    ".flac": "audio/flac",
}


def _convert_to_wav(audio_path: str) -> str:
    """
    Uses pydub to convert unsupported audio format to .wav.
    Returns path to the converted file in temp/.
    """
    from pydub import AudioSegment
    import tempfile

    audio = AudioSegment.from_file(audio_path)
    temp_dir = os.path.join(os.path.dirname(os.path.dirname(audio_path)), "temp")
    os.makedirs(temp_dir, exist_ok=True)
    base_name = os.path.splitext(os.path.basename(audio_path))[0]
    wav_path = os.path.join(temp_dir, f"{base_name}_converted.wav")
    audio.export(wav_path, format="wav")
    return wav_path


def _extract_avg_logprob(response) -> float | None:
    """
    Extracts average log probability from Whisper verbose_json response.
    Returns None if not available.
    """
    try:
        segments = response.segments
        if segments and len(segments) > 0:
            logprobs = [seg.avg_logprob for seg in segments if hasattr(seg, "avg_logprob")]
            if logprobs:
                return sum(logprobs) / len(logprobs)
    except Exception:
        pass
    return None


def process_audio(audio_path: str) -> dict:
    """
    Accepts an audio file path, sends to Groq Whisper,
    returns transcript with confidence score.

    Returns:
        dict with keys: text, confidence, input_type, needs_hitl, hitl_reason
    """
    if not os.path.exists(audio_path):
        return {
            "text": "",
            "confidence": 0.0,
            "input_type": "audio",
            "needs_hitl": True,
            "hitl_reason": f"Audio file not found: {audio_path}"
        }

    ext = os.path.splitext(audio_path)[1].lower()
    converted_path = None

    # Convert unsupported formats
    if ext not in SUPPORTED_FORMATS:
        try:
            audio_path = _convert_to_wav(audio_path)
            converted_path = audio_path
            ext = ".wav"
        except Exception as e:
            return {
                "text": "",
                "confidence": 0.0,
                "input_type": "audio",
                "needs_hitl": True,
                "hitl_reason": f"Audio format conversion failed: {str(e)}"
            }

    mimetype = MIMETYPE_MAP.get(ext, "audio/wav")

    try:
        with open(audio_path, "rb") as audio_file:
            response = client.audio.transcriptions.create(
                model=WHISPER_MODEL,
                file=(os.path.basename(audio_path), audio_file, mimetype),
                language="en",
                response_format="verbose_json"
            )

        transcript_raw = response.text or ""
        avg_logprob = _extract_avg_logprob(response)

    except Exception as e:
        # Cleanup temp file if created
        if converted_path and os.path.exists(converted_path):
            os.remove(converted_path)
        return {
            "text": "",
            "confidence": 0.0,
            "input_type": "audio",
            "needs_hitl": True,
            "hitl_reason": f"Groq Whisper API error: {str(e)}"
        }

    # Cleanup temp converted file
    if converted_path and os.path.exists(converted_path):
        os.remove(converted_path)

    # Normalize math phrases from spoken form
    transcript = normalize_math_text(transcript_raw)
    transcript = clean_whitespace(transcript)

    # Score confidence
    confidence = estimate_asr_confidence(transcript, avg_logprob=avg_logprob)
    needs_hitl = is_below_threshold(confidence, "ASR_CONFIDENCE_THRESHOLD")

    hitl_reason = ""
    if needs_hitl:
        hitl_reason = (
            f"Transcription confidence is low ({confidence:.0%}). "
            "Please review and correct the transcript before solving."
        )

    return {
        "text": transcript,
        "confidence": confidence,
        "input_type": "audio",
        "needs_hitl": needs_hitl,
        "hitl_reason": hitl_reason,
        "raw_transcript": transcript_raw  # keep original for HITL display
    }