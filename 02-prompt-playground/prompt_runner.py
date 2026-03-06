"""
Runs each prompting technique against the Anthropic Claude API.
"""

import os
import anthropic
from dotenv import load_dotenv

load_dotenv()

TECHNIQUES = ["Zero-shot", "Few-shot", "Chain-of-Thought", "Role Prompting"]


def _get_client() -> anthropic.Anthropic:
    return anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))


def run_technique(technique: str, task: dict, user_input: str) -> tuple[str, dict]:
    """
    Run a prompting technique and return (output_text, token_counts).
    """
    client = _get_client()
    system, user = build_prompt(technique, task, user_input)

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=512,
        system=system,
        messages=[{"role": "user", "content": user}],
    )

    tokens = {
        "input": response.usage.input_tokens,
        "output": response.usage.output_tokens,
    }
    return response.content[0].text, tokens


def build_prompt(technique: str, task: dict, user_input: str) -> tuple[str, str]:
    """Return (system_prompt, user_prompt) for the given technique."""
    base_instruction = task["instruction"]
    examples = task.get("examples", [])

    if technique == "Zero-shot":
        system = "You are a helpful business assistant."
        user = f"{base_instruction}\n\nInput:\n{user_input}"

    elif technique == "Few-shot":
        example_block = "\n\n".join(
            f"Input: {ex['input']}\nOutput: {ex['output']}" for ex in examples
        )
        system = "You are a helpful business assistant. Follow the pattern shown in the examples."
        user = f"{base_instruction}\n\nExamples:\n{example_block}\n\nNow process this:\nInput: {user_input}\nOutput:"

    elif technique == "Chain-of-Thought":
        system = "You are a helpful business assistant. Think step by step before giving your final answer."
        user = (
            f"{base_instruction}\n\n"
            f"Input:\n{user_input}\n\n"
            "First, reason through this step by step. Then provide your final answer on a new line starting with 'Answer:'"
        )

    elif technique == "Role Prompting":
        role = task.get("role", "a senior business analyst with 10 years of experience")
        system = f"You are {role}. Apply your domain expertise to produce precise, professional outputs."
        user = f"{base_instruction}\n\nInput:\n{user_input}"

    else:
        raise ValueError(f"Unknown technique: {technique}")

    return system, user
