"""
Topic Generator Service

Generates natural, context-aware conversation starters using GPT-2.
A fixed random seed ensures reproducible outputs for debugging and testing.
"""

import random
from transformers import pipeline

# Fix the random seed for reproducibility
SEED = 42
random.seed(SEED)

# Load the GPT-2 text generation pipeline once at module level
generator = pipeline(
    "text-generation",
    model="gpt2",
    clean_up_tokenization_spaces=False
)


def generate_topics(themes: list, interests: list, max_length: int = 80) -> list:
    """
    Generate conversation starters based on extracted themes and user interests.

    Constructs a structured prompt that guides GPT-2 toward producing
    practical networking conversation openers.

    Args:
        themes: List of extracted event themes.
        interests: List of user interests/background topics.
        max_length: Maximum token length for generated text.

    Returns:
        List of up to 3 cleaned conversation starter strings.
    """
    themes_str = ", ".join(themes)
    interests_str = ", ".join(interests)

    prompt = (
        f"I am attending a networking event about {themes_str}. "
        f"My interests include {interests_str}. "
        f"Here are three conversation starters I could use:\n"
        f"1."
    )

    output = generator(
        prompt,
        max_new_tokens=max_length,
        num_return_sequences=1,
        do_sample=True,
        temperature=0.7,
        top_k=50,
        pad_token_id=50256
    )

    generated_text = output[0]["generated_text"]

    # Split by newlines and extract individual suggestions
    lines = generated_text.split("\n")
    suggestions = []

    for line in lines:
        # Clean bullet markers and leading/trailing whitespace
        cleaned = line.strip()
        for prefix in ["1.", "2.", "3.", "1)", "2)", "3)", "-", "*", "•"]:
            if cleaned.startswith(prefix):
                cleaned = cleaned[len(prefix):].strip()
        if cleaned and len(cleaned) > 10:
            suggestions.append(cleaned)

    # Return up to 3 suggestions
    return suggestions[:3]
