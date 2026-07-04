"""
Personalized Networking Assistant - FastAPI Application Entry Point

Creates the FastAPI application instance, registers all routers,
and provides a health-check endpoint for monitoring.
"""

from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Load environment variables from .env file (must happen before any other imports)
# Use an absolute path so it works regardless of the current working directory
_env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=_env_path)

from backend.routes.conversation import router as conversation_router

app = FastAPI(
    title="Personalized Networking Assistant",
    description="An AI-powered assistant that generates smart, tailored "
                "conversation starters for professional networking events.",
    version="1.0.0"
)

# CORS middleware — allows the Streamlit frontend to communicate with the backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8501", "http://127.0.0.1:8501"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register the conversation router (hub-and-spoke model)
app.include_router(conversation_router)


@app.get("/", tags=["health"])
def health_check():
    """
    Root health-check endpoint.
    Allows load balancers and monitoring systems to verify the API is running.
    """
    return {"status": "healthy", "service": "Personalized Networking Assistant"}
