"""
Document extraction using Claude Vision API.
Handles image files (PNG, JPG) and single-page PDFs (converted to image).
"""

import os
import base64
import json
import logging
from pathlib import Path

import anthropic
from dotenv import load_dotenv
from pydantic import ValidationError

from models import Invoice

load_dotenv()
logger = logging.getLogger(__name__)

SUPPORTED_IMAGE_TYPES = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".gif": "image/gif", ".webp": "image/webp"}

EXTRACTION_PROMPT = """
Extract all invoice information from this document image and return it as valid JSON matching this schema:

{
  "vendor_name": "string (required)",
  "invoice_number": "string or null",
  "invoice_date": "YYYY-MM-DD string or null",
  "due_date": "YYYY-MM-DD string or null",
  "line_items": [
    {"description": "string", "quantity": number_or_null, "unit_price": number_or_null, "amount": number}
  ],
  "subtotal": number_or_null,
  "tax": number_or_null,
  "total": number (required, must be > 0),
  "currency": "3-letter currency code",
  "notes": "string or null"
}

Rules:
- Return ONLY the JSON object, no markdown, no explanation
- All monetary values must be numbers (floats), not strings
- If a field is not present in the document, use null
- Dates must be in YYYY-MM-DD format when possible
"""


def encode_image(image_path: str) -> tuple[str, str]:
    """Return (base64_data, media_type) for an image file."""
    suffix = Path(image_path).suffix.lower()
    media_type = SUPPORTED_IMAGE_TYPES.get(suffix, "image/jpeg")
    with open(image_path, "rb") as f:
        data = base64.standard_b64encode(f.read()).decode("utf-8")
    return data, media_type


def pdf_to_image(pdf_path: str, output_path: str = "/tmp/invoice_page.png") -> str:
    """Convert first page of a PDF to a PNG image."""
    try:
        import fitz  # PyMuPDF
        doc = fitz.open(pdf_path)
        page = doc[0]
        pix = page.get_pixmap(dpi=150)
        pix.save(output_path)
        return output_path
    except ImportError:
        raise ImportError("PyMuPDF not installed. Run: pip install pymupdf")


def extract_invoice(file_path: str) -> tuple[Invoice | None, str | None, dict]:
    """
    Extract invoice data from an image or PDF file.

    Returns: (invoice_or_None, error_message_or_None, raw_llm_response_dict)
    """
    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    suffix = Path(file_path).suffix.lower()

    if suffix == ".pdf":
        image_path = pdf_to_image(file_path)
    elif suffix in SUPPORTED_IMAGE_TYPES:
        image_path = file_path
    else:
        return None, f"Unsupported file type: {suffix}", {}

    image_data, media_type = encode_image(image_path)

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2048,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {"type": "base64", "media_type": media_type, "data": image_data},
                    },
                    {"type": "text", "text": EXTRACTION_PROMPT},
                ],
            }
        ],
    )

    raw_text = response.content[0].text.strip()
    logger.debug("Raw LLM response: %s", raw_text[:500])

    # Clean markdown code blocks if present
    if raw_text.startswith("```"):
        raw_text = raw_text.split("```")[1]
        if raw_text.startswith("json"):
            raw_text = raw_text[4:]

    try:
        data = json.loads(raw_text)
        invoice = Invoice(**data)
        return invoice, None, data
    except json.JSONDecodeError as e:
        return None, f"JSON parse error: {e}", {"raw": raw_text}
    except ValidationError as e:
        return None, f"Validation error: {e}", data
