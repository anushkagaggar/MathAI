import os
import base64
from io import BytesIO
from groq import Groq
from PIL import Image
from dotenv import load_dotenv

from utils.confidence import estimate_ocr_confidence, is_below_threshold
from utils.formatting import normalize_math_text, clean_whitespace
from utils.logger import get_logger

load_dotenv()

logger = get_logger(__name__)
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# The ONLY supported Groq vision model as of 2026
# Override via .env: GROQ_VISION_MODEL=meta-llama/llama-4-scout-17b-16e-instruct
VISION_MODEL = os.getenv("GROQ_VISION_MODEL", "meta-llama/llama-4-scout-17b-16e-instruct")
MAX_IMAGE_WIDTH = 1024

logger.info("image_processor ready — vision model: %s", VISION_MODEL)


def _load_and_encode_image(image_path: str) -> str:
    """
    Loads image with Pillow, converts to RGB JPEG, resizes if too wide,
    returns base64-encoded string.
    """
    with Image.open(image_path) as img:
        # Convert RGBA/P/palette modes to RGB for JPEG compatibility
        if img.mode != "RGB":
            img = img.convert("RGB")

        # Resize if too wide (Groq vision handles smaller images better)
        width, height = img.size
        if width > MAX_IMAGE_WIDTH:
            ratio = MAX_IMAGE_WIDTH / width
            new_size = (MAX_IMAGE_WIDTH, int(height * ratio))
            img = img.resize(new_size, Image.LANCZOS)

        buffer = BytesIO()
        img.save(buffer, format="JPEG", quality=90)
        buffer.seek(0)
        b64 = base64.b64encode(buffer.read()).decode("utf-8")

    return b64


def process_image(image_path: str) -> dict:
    """
    Sends image to Groq Vision (Llama 4 Scout), extracts math text,
    scores confidence.

    Returns dict with keys:
        extracted_text, confidence, input_type, needs_hitl, hitl_reason
    """
    if not os.path.exists(image_path):
        logger.error("Image file not found: %s", image_path)
        return {
            "extracted_text": "",
            "confidence": 0.0,
            "input_type": "image",
            "needs_hitl": True,
            "hitl_reason": f"Image file not found: {image_path}"
        }

    try:
        b64_image = _load_and_encode_image(image_path)
        logger.debug("Image encoded — %d chars of base64", len(b64_image))
    except Exception as e:
        logger.error("Failed to load/encode image: %s", e)
        return {
            "extracted_text": "",
            "confidence": 0.0,
            "input_type": "image",
            "needs_hitl": True,
            "hitl_reason": f"Failed to load image: {str(e)}"
        }

    extraction_prompt = (
        "You are a math OCR system. Extract ALL mathematical text from this image exactly as written. "
        "Preserve all symbols, equations, variables, numbers, and operators. "
        "If there are multiple problems, extract all of them. "
        "Return ONLY the extracted math problem text — no explanations, no commentary, nothing else."
    )

    # NOTE: per Groq docs, text block goes BEFORE image_url in content array
    try:
        logger.info("Calling Groq Vision — model: %s", VISION_MODEL)
        response = client.chat.completions.create(
            model=VISION_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": extraction_prompt
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{b64_image}"
                            }
                        }
                    ]
                }
            ],
            max_tokens=1024
        )
        extracted_raw = response.choices[0].message.content or ""
        logger.info("Vision API returned %d chars", len(extracted_raw))

    except Exception as e:
        logger.error("Groq Vision API error: %s", e)
        return {
            "extracted_text": "",
            "confidence": 0.0,
            "input_type": "image",
            "needs_hitl": True,
            "hitl_reason": f"Groq Vision API error: {str(e)}"
        }

    # Normalize
    extracted_text = normalize_math_text(extracted_raw)
    extracted_text = clean_whitespace(extracted_text)
    logger.info("Extracted text: %r", extracted_text[:120])

    # Confidence scoring
    confidence = estimate_ocr_confidence(extracted_text)
    needs_hitl = is_below_threshold(confidence, "OCR_CONFIDENCE_THRESHOLD")
    logger.info("OCR confidence: %.2f — needs_hitl: %s", confidence, needs_hitl)

    hitl_reason = ""
    if needs_hitl:
        hitl_reason = (
            f"OCR confidence is low ({confidence:.0%}). "
            "Please review and correct the extracted text before solving."
        )

    return {
        "extracted_text": extracted_text,
        "confidence": confidence,
        "input_type": "image",
        "needs_hitl": needs_hitl,
        "hitl_reason": hitl_reason
    }