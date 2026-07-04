"""
Pydantic data models for the Personalized Networking Assistant.

These models define the data contracts between the frontend and backend,
providing automatic type validation, serialization, and API documentation.
"""

from pydantic import BaseModel, Field
from typing import List, Optional


class EventRequest(BaseModel):
    """Request model for event theme extraction."""
    description: str = Field(..., description="Event description text")
    candidate_labels: Optional[List[str]] = Field(
        None,
        description="Optional list of candidate theme labels for classification"
    )


class EventResponse(BaseModel):
    """Response model for event theme extraction."""
    themes: List[str] = Field(..., description="Top extracted themes from the event")


class ConversationRequest(BaseModel):
    """Request model for full conversation generation pipeline."""
    description: str = Field(..., description="Event description text")
    interests: List[str] = Field(..., description="User's interests and background topics")


class ConversationResponse(BaseModel):
    """Response model for full conversation generation pipeline."""
    themes: List[str] = Field(..., description="Extracted event themes")
    suggestions: List[str] = Field(..., description="Generated conversation starters")


class FactCheckRequest(BaseModel):
    """Request model for fact-checking via Wikipedia."""
    query: str = Field(..., description="Search query for fact verification")


class FactCheckResponse(BaseModel):
    """Response model for fact-checking results."""
    summary: str = Field(..., description="Wikipedia summary of the queried topic")


class FeedbackRequest(BaseModel):
    """Request model for logging user feedback on suggestions."""
    suggestion: str = Field(..., description="The conversation suggestion that was rated")
    action: str = Field(..., description="User action: 'like' or 'dislike'")


class FeedbackResponse(BaseModel):
    """Response model for feedback logging acknowledgment."""
    message: str = Field(..., description="Status message confirming feedback was logged")


class HistoryEntry(BaseModel):
    """Data model for a single conversation history entry."""
    description: str
    interests: List[str]
    themes: List[str]
    suggestions: List[str]
    timestamp: str


class FeedbackEntry(BaseModel):
    """Data model for a single feedback history entry."""
    suggestion: str
    action: str
    timestamp: str


# ---------------------------------------------------------------------------
# Gemini-powered models
# ---------------------------------------------------------------------------


class GeminiSuggestionsRequest(BaseModel):
    """Request model for Gemini-powered smart conversation starters."""
    description: str = Field(..., description="Event description text")
    interests: List[str] = Field(..., description="User's interests and background topics")
    temperature: Optional[float] = Field(
        0.8,
        description="Creativity temperature (0.0 - 1.0)",
        ge=0.0,
        le=1.0,
    )


class GeminiSuggestionsResponse(BaseModel):
    """Response model for Gemini-powered smart conversation starters."""
    suggestions: List[str] = Field(..., description="Generated conversation starters")


class GeminiNetworkingTipsRequest(BaseModel):
    """Request model for Gemini-powered networking tips."""
    description: str = Field(..., description="Event description text")
    interests: List[str] = Field(..., description="User's interests and background topics")


class GeminiNetworkingTipsResponse(BaseModel):
    """Response model for Gemini-powered networking tips."""
    tips: List[str] = Field(..., description="Personalized networking tips")


class GeminiStatusResponse(BaseModel):
    """Response model for Gemini API health status."""
    configured: bool = Field(..., description="Whether the Gemini API is configured")
    message: str = Field(..., description="Status description")
