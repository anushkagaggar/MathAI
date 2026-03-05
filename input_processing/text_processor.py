from utils.formatting import normalize_math_text, clean_whitespace


def process_text(raw_text: str) -> dict:
    """
    Handles typed text input.
    Cleans and normalizes, then passes through.

    Returns:
        dict with keys: text, confidence, input_type, needs_hitl
    """
    if not raw_text or not raw_text.strip():
        return {
            "text": "",
            "confidence": 0.0,
            "input_type": "text",
            "needs_hitl": True,
            "hitl_reason": "Empty input received."
        }

    cleaned = normalize_math_text(raw_text)
    cleaned = clean_whitespace(cleaned)

    return {
        "text": cleaned,
        "confidence": 1.0,        # Typed input is always fully confident
        "input_type": "text",
        "needs_hitl": False,
        "hitl_reason": ""
    }