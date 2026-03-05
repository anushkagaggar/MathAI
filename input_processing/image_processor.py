import os
import base64
from io import BytesIO
from groq import Groq
from PIL import Image
from dotenv import load_dotenv

from utils.confidence import estimate_ocr_confidence, is_below_threshold
from utils.formatting import normalize_math_text, clean_whitespace

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

VISION_MODEL = os.getenv("GROQ_VISION_MODEL", "llava-v1.5-7b-4096-preview")
MAX_IMAGE_WIDTH = 1024


def _load_and_encode_image(image_path: str) -> str:
    """
    Loads image with Pillow, converts to RGB JPEG, resizes if needed,
    returns base64-encoded string.
    """
    with Image.open(image_path) as img:
        # Convert RGBA/P/etc to RGB for JPEG compatibility
        if img.mode not in ("RGB",):
            img = img.convert("RGB")

        # Resize if too wide
        width, height = img.size
        if width > MAX_IMAGE_WIDTH:
            ratio = MAX_IMAGE_WIDTH / width
            new_size = (MAX_IMAGE_WIDTH, int(height * ratio))
            img = img.resize(new_size, Image.LANCZOS)

        # Encode to JPEG bytes in memory
        buffer = BytesIO()
        img.save(buffer, format="JPEG", quality=90)
        buffer.seek(0)
        b64 = base64.b64encode(buffer.read()).decode("utf-8")

    return b64


def process_image(image_path: str) -> dict:
    """
    Accepts an image file path, sends to Groq Vision (LLaVA),
    extracts math text, scores confidence.

    Returns:
        dict with keys: text, confidence, input_type, needs_hitl, hitl_reason
    """
    if not os.path.exists(image_path):
        return {
            "text": "",
            "confidence": 0.0,
            "input_type": "image",
            "needs_hitl": True,
            "hitl_reason": f"Image file not found: {image_path}"
        }

    try:
        b64_image = _load_and_encode_image(image_path)
    except Exception as e:
        return {
            "text": "",
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

    try:
        response = client.chat.completions.create(
            model=VISION_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{b64_image}"
                            }
                        },
                        {
                            "type": "text",
                            "text": extraction_prompt
                        }
                    ]
                }
            ],
            max_tokens=1024
        )
        extracted_raw = response.choices[0].message.content or ""
    except Exception as e:
        return {
            "text": "",
            "confidence": 0.0,
            "input_type": "image",
            "needs_hitl": True,
            "hitl_reason": f"Groq Vision API error: {str(e)}"
        }

    # Normalize and clean
    extracted_text = normalize_math_text(extracted_raw)
    extracted_text = clean_whitespace(extracted_text)

    # Score confidence
    confidence = estimate_ocr_confidence(extracted_text)
    needs_hitl = is_below_threshold(confidence, "OCR_CONFIDENCE_THRESHOLD")

    hitl_reason = ""
    if needs_hitl:
        hitl_reason = (
            f"OCR confidence is low ({confidence:.0%}). "
            "Please review and correct the extracted text before solving."
        )

    return {
        "text": extracted_text,
        "confidence": confidence,
        "input_type": "image",
        "needs_hitl": needs_hitl,
        "hitl_reason": hitl_reason
    }