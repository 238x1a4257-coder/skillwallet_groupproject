"""
History Logger Service

Provides persistent storage for conversation sessions using a JSON file.
Uses an append-to-JSON-list pattern with read-modify-write for data integrity.
"""

import json
from datetime import datetime, timezone
from pathlib import Path

# Define the data directory path
DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
HISTORY_FILE = DATA_DIR / "conversation_history.json"


def _ensure_data_dir():
    """Ensure the data directory exists."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def log_conversation(data: dict) -> None:
    """
    Log a conversation session to the history file.

    Adds an ISO-formatted timestamp and appends the entry to the JSON history list.

    Args:
        data: Dictionary containing description, interests, themes, and suggestions.
    """
    _ensure_data_dir()

    # Add timestamp
    data["timestamp"] = datetime.now(timezone.utc).isoformat()

    # Read existing history or initialize empty list
    if HISTORY_FILE.exists():
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            history = json.load(f)
    else:
        history = []

    # Append and write back
    history.append(data)

    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2)


def load_history() -> list:
    """
    Load the full conversation history from the JSON file.

    Returns:
        List of conversation history entries, or an empty list if no history exists.
    """
    _ensure_data_dir()

    if HISTORY_FILE.exists():
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)

    return []
