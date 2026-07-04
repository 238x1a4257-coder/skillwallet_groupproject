"""
Event Analyzer Service

Uses DistilBERT zero-shot classification to extract themes from event descriptions.
The pipeline is loaded once at module import time to avoid repeated model loading
on every request, ensuring fast inference for real-time responses.
"""

from transformers import pipeline

# Default candidate labels for zero-shot classification
DEFAULT_LABELS = [
    "artificial intelligence",
    "machine learning",
    "healthcare",
    "blockchain",
    "education",
    "sustainability",
    "climate change",
    "urban planning",
    "finance",
    "cybersecurity",
    "robotics",
    "data science",
]

# Load the zero-shot classification pipeline once at module level
classifier = pipeline(
    "zero-shot-classification",
    model="distilbert-base-uncased-finetuned-sst-2-english"
)


def extract_event_themes(
    description: str,
    candidate_labels: list = None,
    top_k: int = 3
) -> list:
    """
    Extract the top themes from an event description using zero-shot classification.

    Args:
        description: The event description text to analyze.
        candidate_labels: Optional list of candidate labels. Defaults to professional themes.
        top_k: Number of top themes to return.

    Returns:
        List of top-k theme strings ranked by classification confidence.
    """
    if candidate_labels is None:
        candidate_labels = DEFAULT_LABELS

    result = classifier(
        description,
        candidate_labels=candidate_labels,
        multi_label=False
    )

    # Return the top-k labels sorted by highest score
    top_themes = result["labels"][:top_k]
    return top_themes
