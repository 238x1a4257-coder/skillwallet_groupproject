"""
Conversation Router

Defines the API endpoints that wire together the service modules.
This routing layer acts as the integration point between the HTTP interface
and the business logic layers.
"""

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from backend.models import (
    EventRequest,
    EventResponse,
    ConversationRequest,
    ConversationResponse,
    FactCheckRequest,
    FactCheckResponse,
    FeedbackRequest,
    FeedbackResponse,
    HistoryEntry,
    FeedbackEntry,
    GeminiSuggestionsRequest,
    GeminiSuggestionsResponse,
    GeminiNetworkingTipsRequest,
    GeminiNetworkingTipsResponse,
    GeminiStatusResponse,
)
from backend.services.event_analyzer import extract_event_themes
from backend.services.topic_generator import generate_topics
from backend.services.fact_checker import fact_check
from backend.services.history_logger import log_conversation, load_history
from backend.services.feedback_logger import log_feedback, load_feedback
from backend.services.gemini_service import generate_smart_suggestions, generate_networking_tips
from typing import List
import os

router = APIRouter(prefix="/api", tags=["conversation"])


@router.post(
    "/analyze-event",
    response_model=EventResponse,
    summary="Extract themes from an event description",
    description="Uses DistilBERT zero-shot classification to identify "
                "the top themes from an event description."
)
def analyze_event(request: EventRequest):
    """
    Standalone endpoint for theme extraction.
    Useful for debugging or building custom integrations.
    """
    themes = extract_event_themes(
        description=request.description,
        candidate_labels=request.candidate_labels
    )
    return EventResponse(themes=themes)


@router.post(
    "/generate-conversation",
    response_model=ConversationResponse,
    summary="Generate personalized conversation starters",
    description="Orchestrates the full pipeline: theme extraction, conversation "
                "generation, and automatic history logging."
)
def generate_conversation(request: ConversationRequest):
    """
    Primary application endpoint that orchestrates the full pipeline:
    1. Extracts themes from the event description
    2. Generates conversation starters using themes + user interests
    3. Automatically logs the interaction to history
    4. Returns both themes and suggestions in a single response
    """
    # Step 1: Extract themes
    themes = extract_event_themes(description=request.description)

    # Step 2: Generate conversation starters
    suggestions = generate_topics(
        themes=themes,
        interests=request.interests
    )

    # Step 3: Automatically log to history (side-effect)
    log_conversation({
        "description": request.description,
        "interests": request.interests,
        "themes": themes,
        "suggestions": suggestions
    })

    # Step 4: Return structured response
    return ConversationResponse(themes=themes, suggestions=suggestions)


@router.post(
    "/fact-check",
    response_model=FactCheckResponse,
    summary="Quick fact verification via Wikipedia",
    description="Queries the Wikipedia REST API to return a summarized "
                "reference for a given topic."
)
def fact_check_endpoint(request: FactCheckRequest):
    """
    Wraps the Wikipedia fact-checking service in a type-safe API contract.
    """
    summary = fact_check(query=request.query)
    return FactCheckResponse(summary=summary)


@router.post(
    "/feedback",
    response_model=FeedbackResponse,
    summary="Log user feedback on a suggestion",
    description="Records a like or dislike action on a specific conversation suggestion."
)
def submit_feedback(request: FeedbackRequest):
    """
    Captures explicit user feedback on conversation suggestions.
    This data forms the foundation for future recommendation improvements.
    """
    if request.action not in ("like", "dislike"):
        return FeedbackResponse(
            message="Invalid action. Please use 'like' or 'dislike'."
        )

    log_feedback(suggestion=request.suggestion, action=request.action)

    return FeedbackResponse(
        message=f"Feedback '{request.action}' recorded successfully."
    )


@router.get(
    "/history",
    response_model=List[HistoryEntry],
    summary="Load conversation history",
    description="Returns the full conversation history from persistent storage."
)
def get_history():
    """Load and return the full conversation history."""
    return load_history()


@router.get(
    "/feedback-history",
    response_model=List[FeedbackEntry],
    summary="Load feedback history",
    description="Returns the full feedback history from persistent storage."
)
def get_feedback_history():
    """Load and return the full feedback history."""
    return load_feedback()


# ---------------------------------------------------------------------------
# Gemini-powered endpoints
# ---------------------------------------------------------------------------


@router.get(
    "/gemini/status",
    response_model=GeminiStatusResponse,
    summary="Check Gemini API configuration status",
    description="Returns whether the Gemini API key is configured in the environment."
)
def gemini_status():
    """Check whether the Gemini API key is available."""
    configured = bool(os.environ.get("GEMINI_API_KEY"))
    if configured:
        return GeminiStatusResponse(
            configured=True,
            message="Gemini API is configured and ready."
        )
    return GeminiStatusResponse(
        configured=False,
        message="GEMINI_API_KEY not found. Set it in your .env file or environment variables."
    )


@router.post(
    "/gemini/smart-suggestions",
    response_model=GeminiSuggestionsResponse,
    summary="Generate smart conversation starters with Gemini",
    description="Uses Google Gemini to generate high-quality, context-aware "
                "conversation starters based on event description and user interests."
)
def gemini_smart_suggestions(request: GeminiSuggestionsRequest):
    """
    Generate smarter conversation starters using Google Gemini,
    offering more nuanced and creative suggestions than the GPT-2 baseline.
    """
    try:
        suggestions = generate_smart_suggestions(
            description=request.description,
            interests=request.interests,
            temperature=request.temperature or 0.8,
        )
        return GeminiSuggestionsResponse(suggestions=suggestions)
    except RuntimeError as exc:
        return JSONResponse(
            status_code=400,
            content={"detail": str(exc)}
        )


@router.post(
    "/gemini/networking-tips",
    response_model=GeminiNetworkingTipsResponse,
    summary="Get personalized networking tips from Gemini",
    description="Provides actionable networking advice tailored to the event "
                "and the user's interests."
)
def gemini_networking_tips(request: GeminiNetworkingTipsRequest):
    """
    Generate personalized networking strategy tips using Gemini.
    """
    try:
        tips = generate_networking_tips(
            description=request.description,
            interests=request.interests,
        )
        return GeminiNetworkingTipsResponse(tips=tips)
    except RuntimeError as exc:
        return JSONResponse(
            status_code=400,
            content={"detail": str(exc)}
        )
