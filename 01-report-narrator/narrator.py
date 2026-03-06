"""
Core LLM narration logic using Anthropic Claude.
"""

import os
from pathlib import Path
from typing import Generator

import anthropic
from jinja2 import Environment, FileSystemLoader
from dotenv import load_dotenv

load_dotenv(override=True)

PROMPT_DIR = Path(__file__).parent / "prompts"
jinja_env = Environment(loader=FileSystemLoader(str(PROMPT_DIR)))

TONE_INSTRUCTIONS = {
    "Executive summary": "Write a concise, high-level executive summary. Use confident, direct language. Focus on key takeaways only.",
    "Detailed analyst": "Write a thorough analyst commentary. Include trend analysis, comparisons, and nuanced observations.",
    "Casual update": "Write a friendly, conversational update suitable for a team Slack message or informal email.",
}

_SYSTEM_PROMPT = (
    "You are a senior business analyst who writes clear, insightful data narratives. "
    "{tone_instruction} "
    "Never use bullet points — write in flowing prose paragraphs. "
    "Lead with the most important insight, not with a description of the dataset."
)


def _build_messages(stats: dict, tone: str, max_words: int) -> tuple[str, list[dict]]:
    load_dotenv(override=True)  # re-read .env so key changes take effect without restart
    tone_instruction = TONE_INSTRUCTIONS.get(tone, TONE_INSTRUCTIONS["Executive summary"])
    system = _SYSTEM_PROMPT.format(tone_instruction=tone_instruction)
    template = jinja_env.get_template("narrative_prompt.j2")
    user_prompt = template.render(stats=stats, tone=tone, max_words=max_words)
    return system, [{"role": "user", "content": user_prompt}]


def generate_narrative(stats: dict, tone: str = "Executive summary", max_words: int = 300) -> str:
    """Return the full narrative as a string (non-streaming)."""
    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    system, messages = _build_messages(stats, tone, max_words)
    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        system=system,
        messages=messages,
    )
    return message.content[0].text


def generate_narrative_stream(
    stats: dict, tone: str = "Executive summary", max_words: int = 300
) -> Generator[str, None, None]:
    """
    Stream the narrative token-by-token.
    Pass directly to st.write_stream() for real-time display in Streamlit.
    """
    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    system, messages = _build_messages(stats, tone, max_words)
    with client.messages.stream(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        system=system,
        messages=messages,
    ) as stream:
        for text in stream.text_stream:
            yield text
