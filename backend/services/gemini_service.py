"""
Gemini Service

Provides AI-powered features using Google's Gemini API:
  - Smart conversation starters with deeper context awareness than GPT-2
  - Personalized networking tips and icebreakers

Requires the GEMINI_API_KEY environment variable to be set.
"""

import os
import logging
from typing import Optional

from google import genai

logger = logging.getLogger(__name__)

# Module-level client; will be None if no API key is configured
_client: Optional[genai.Client] = None
_MODEL = "gemini-2.0-flash"


def _get_client() -> genai.Client:
    """Return the singleton Gemini client, raising if no API key is set."""
    global _client
    if _client is None:
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError(
                "GEMINI_API_KEY environment variable is not set. "
                "Please set it in a .env file or your environment."
            )
        _client = genai.Client(api_key=api_key)
    return _client


def _safe_generate(client, model: str, contents: str, config: dict) -> str | None:
    """
    Safely call the Gemini API with proper error handling.

    Returns:
        The response text on success, or None on failure.
    """
    try:
        response = client.models.generate_content(
            model=model,
            contents=contents,
            config=config,
        )
        return response.text
    except Exception as e:
        error_str = str(e)
        if "401" in error_str or "UNAUTHENTICATED" in error_str:
            logger.error(
                "Gemini API authentication failed. The API key in .env is invalid "
                "or not authorized for the Gemini API. Get a valid key at "
                "https://aistudio.google.com/apikey"
            )
            raise RuntimeError(
                "Gemini API authentication failed. Your API key is invalid. "
                "Please get a valid Gemini API key from "
                "https://aistudio.google.com/apikey — it should start with 'AIzaSy'."
            ) from e
        logger.error(f"Gemini API error: {error_str}")
        raise RuntimeError(f"Gemini API error: {error_str}") from e


def generate_smart_suggestions(
    description: str,
    interests: list[str],
    temperature: float = 0.8,
) -> list[str]:
    """
    Generate high-quality, context-aware conversation starters using Gemini.

    Unlike the simpler GPT-2 approach, this uses Gemini's advanced language
    understanding to produce more nuanced, creative, and relevant suggestions.

    Args:
        description: The event description text.
        interests: List of the user's interests/background topics.
        temperature: Creativity temperature (0.0 - 1.0). Default 0.8.

    Returns:
        List of up to 3 polished conversation starter strings.
    """
    client = _get_client()

    interests_str = ", ".join(interests)

    prompt = (
        f"You are an expert networking coach attending an event described as:\n"
        f'"{description}"\n\n'
        f"The attendee's interests include: {interests_str}.\n\n"
        f"Generate exactly 3 thoughtful, natural conversation starters that:\n"
        f"- Connect the event's themes with the attendee's interests\n"
        f"- Sound genuine and human, not robotic\n"
        f"- Could be used in real conversation at a professional networking event\n"
        f"- Are each 1-2 sentences long\n\n"
        f"Return ONLY the 3 conversation starters, one per line, without numbering or bullet points."
    )

    response_text = _safe_generate(
        client,
        model=_MODEL,
        contents=prompt,
        config={
            "temperature": temperature,
            "max_output_tokens": 300,
        },
    )

    if not response_text:
        return ["I couldn't generate suggestions right now. Please try again."]

    # Parse the response: split by newlines, filter empty lines, clean up
    lines = [
        line.strip().lstrip("0123456789.)-*•").strip()
        for line in response_text.strip().split("\n")
        if line.strip()
    ]

    # Return up to 3 non-empty suggestions
    suggestions = [line for line in lines if len(line) > 10][:3]
    return suggestions if suggestions else [response_text.strip()[:200]]


def generate_networking_tips(
    description: str,
    interests: list[str],
) -> list[str]:
    """
    Generate personalized networking strategy tips using Gemini.

    Provides actionable advice on how to approach conversations, what to ask,
    and how to follow up — tailored to the specific event and user interests.

    Args:
        description: The event description text.
        interests: List of the user's interests/background topics.

    Returns:
        List of up to 4 networking tip strings.
    """
    client = _get_client()

    interests_str = ", ".join(interests)

    prompt = (
        f"Given a professional networking event described as:\n"
        f'"{description}"\n\n'
        f"A participant with interests in {interests_str} is attending.\n\n"
        f"Provide exactly 4 concise, actionable networking tips:\n"
        f"- Tip 1: What key question to ask other attendees\n"
        f"- Tip 2: How to connect the event's themes to their interests in conversation\n"
        f"- Tip 3: A good follow-up angle after meeting someone\n"
        f"- Tip 4: What to mention when introducing themselves\n\n"
        f"Keep each tip to 1-2 sentences. Return one tip per line, without numbering."
    )

    response_text = _safe_generate(
        client,
        model=_MODEL,
        contents=prompt,
        config={
            "temperature": 0.7,
            "max_output_tokens": 400,
        },
    )

    if not response_text:
        return ["Networking tips are not available right now. Please try again."]

    lines = [
        line.strip().lstrip("0123456789.)-*•").strip()
        for line in response_text.strip().split("\n")
        if line.strip()
    ]

    tips = [line for line in lines if len(line) > 10][:4]
    return tips if tips else [response_text.strip()[:300]]
