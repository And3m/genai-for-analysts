"""
Input and output guardrails: topic classification, PII detection/redaction, output validation.
"""

import re
import os
import anthropic
from dotenv import load_dotenv

load_dotenv()

# --- Topic restriction ---
ALLOWED_TOPICS = ["leave policy", "HR policy", "company policy", "employment", "benefits", "payroll", "compliance", "onboarding", "offboarding"]
TOPIC_SYSTEM_PROMPT = (
    "You are a topic classifier. Determine if the user's message is related to HR policies, "
    "company policies, employment, benefits, payroll, or compliance matters. "
    "Reply with only 'ON_TOPIC' or 'OFF_TOPIC'."
)


def is_on_topic(user_message: str) -> bool:
    """Use a fast LLM call to classify whether the message is on-topic."""
    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=10,
        system=TOPIC_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_message}],
    )
    verdict = response.content[0].text.strip().upper()
    return "ON_TOPIC" in verdict


# --- PII Detection and Redaction ---
PII_PATTERNS = {
    "EMAIL": r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}",
    "PHONE_AU": r"\b(?:\+61|0)[2-9]\d{8}\b",
    "PHONE_INTL": r"\b\+?[1-9]\d{6,14}\b",
    "SSN_US": r"\b\d{3}-\d{2}-\d{4}\b",
    "CREDIT_CARD": r"\b(?:\d{4}[- ]?){3}\d{4}\b",
}


def detect_and_redact_pii(text: str) -> tuple[str, list[str]]:
    """
    Replace PII patterns with [REDACTED_TYPE] placeholders.
    Returns (redacted_text, list_of_detected_pii_types).
    """
    detected_types = []
    redacted = text
    for pii_type, pattern in PII_PATTERNS.items():
        matches = re.findall(pattern, redacted)
        if matches:
            detected_types.append(pii_type)
            redacted = re.sub(pattern, f"[REDACTED_{pii_type}]", redacted)
    return redacted, detected_types


# --- Output validation ---
MAX_RESPONSE_CHARS = 3000
BLOCKED_PHRASES = [
    "I cannot assist with",  # overly restrictive refusals for on-topic content
]


def validate_output(response_text: str) -> tuple[bool, str]:
    """
    Validate the LLM response.
    Returns (is_valid, reason).
    """
    if len(response_text) > MAX_RESPONSE_CHARS:
        truncated = response_text[:MAX_RESPONSE_CHARS] + "\n\n[Response truncated for length]"
        return True, truncated

    if not response_text.strip():
        return False, "Empty response from model."

    return True, response_text
