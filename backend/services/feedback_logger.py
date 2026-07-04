"""
Feedback Logger Service

Captures explicit user feedback (like/dislike) on individual conversation suggestions.
This data forms the foundation for future recommendation improvements.
"""

import json
from datetime import datetime, timezone
from pathlib import Path

# Define the data directory path
DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
FEEDBACK_FILE = DATA_DIR / "feedback_history.json"


def _ensure_data_dir():
    """Ensure the data directory exists."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def log_feedback(suggestion: str, action: str) -> None:
    """
    Log user feedback for a conversation suggestion.

    Args:
        suggestion: The conversation suggestion text that was rated.
        action: The user's action — 'like' or 'dislike'.
    """
    _ensure_data_dir()

    entry = {
        "suggestion": suggestion,
        "action": action,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

    # Read existing feedback or initialize empty list
    if FEEDBACK_FILE.exists():
        with open(FEEDBACK_FILE, "r", encoding="utf-8") as f:
            feedback = json.load(f)
    else:
        feedback = []

    # Append and write back
    feedback.append(entry)

    with open(FEEDBACK_FILE, "w", encoding="utf-8") as f:
        json.dump(feedback, f, indent=2)


def load_feedback() -> list:
    """
    Load the full feedback history from the JSON file.

    Returns:
        List of feedback entries, or an empty list if no feedback exists.
    """
    _ensure_data_dir()

    if FEEDBACK_FILE.exists():
        with open(FEEDBACK_FILE, "r", encoding="utf-8") as f:
            return json.load(f)

    return []
