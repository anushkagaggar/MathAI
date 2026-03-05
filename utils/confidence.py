import os
import re
import math
from dotenv import load_dotenv

load_dotenv()


def estimate_ocr_confidence(extracted_text: str) -> float:
    """
    Heuristic confidence scorer for OCR output from Groq Vision.
    Returns float 0.0-1.0.
    """
    if not extracted_text or len(extracted_text.strip()) == 0:
        return 0.0

    text = extracted_text.strip()

    if len(text) < 10:
        return 0.2

    total_chars = len(text)
    valid_pattern = re.compile(r"[a-zA-Z0-9\s\+\-\*\/\^\=\(\)\[\]\{\}\.\,\!\?\:\;\'\`\<\>\|\\\_\%\&]")
    valid_count = len(valid_pattern.findall(text))
    invalid_ratio = 1 - (valid_count / total_chars)

    if invalid_ratio > 0.35:
        return max(0.1, 0.5 - invalid_ratio)

    junk_pattern = re.compile(r"([^a-zA-Z0-9\s])\1{3,}")
    if junk_pattern.search(text):
        return 0.3

    alphanum_count = len(re.findall(r"[a-zA-Z0-9]", text))
    if total_chars > 0 and (alphanum_count / total_chars) < 0.25:
        return 0.35

    base_score = 1.0 - (invalid_ratio * 1.5)
    return round(min(1.0, max(0.5, base_score)), 3)


def estimate_asr_confidence(transcript: str, avg_logprob: float = None) -> float:
    """
    Heuristic confidence scorer for ASR output from Groq Whisper.
    Uses avg_logprob if available (from verbose_json response).
    Returns float 0.0-1.0.
    """
    if not transcript or len(transcript.strip()) == 0:
        return 0.0

    text = transcript.strip()

    if avg_logprob is not None:
        if avg_logprob >= -0.3:
            return 0.95
        elif avg_logprob >= -0.6:
            return 0.85
        elif avg_logprob >= -1.0:
            return 0.70
        elif avg_logprob >= -1.5:
            return 0.50
        else:
            return max(0.1, 0.4 + avg_logprob * 0.1)

    placeholder_tokens = ["[blank_audio]", "[inaudible]", "[noise]", "[music]", "[silence]"]
    if any(token in text.lower() for token in placeholder_tokens):
        return 0.1

    if len(text) < 5:
        return 0.2

    words = text.lower().split()
    if len(words) > 3:
        unique_ratio = len(set(words)) / len(words)
        if unique_ratio < 0.4:
            return 0.3

    math_keywords = [
        "solve", "find", "calculate", "derivative", "integral", "limit",
        "probability", "matrix", "equation", "function", "value", "root",
        "square", "cube", "power", "sum", "product", "factor", "simplify",
        "differentiate", "integrate", "prove", "evaluate", "maximize", "minimize"
    ]
    has_math = any(kw in text.lower() for kw in math_keywords)
    word_count = len(words)

    if word_count >= 3 and has_math:
        return 0.85
    elif word_count >= 3 and not has_math:
        return 0.65
    else:
        return 0.50


def is_below_threshold(score: float, threshold_env_key: str) -> bool:
    """
    Returns True if score is below the threshold defined in .env.
    """
    try:
        threshold = float(os.getenv(threshold_env_key, "0.75"))
    except ValueError:
        threshold = 0.75
    return score < threshold