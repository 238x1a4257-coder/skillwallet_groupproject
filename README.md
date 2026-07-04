# 🤝 Personalized Networking Assistant

An AI-powered assistant that generates smart, tailored conversation starters for professional networking events. Enter an event description and your interests, and the system extracts relevant themes using **DistilBERT**, generates conversation starters using **GPT-2**, and optionally enhances results with **Google Gemini** for more creative and nuanced suggestions.

---

## Table of Contents

- [Architecture Overview](#architecture-overview)
- [Project Structure](#project-structure)
- [The AI Pipeline (Workflow)](#the-ai-pipeline-workflow)
  - [1. Theme Extraction (DistilBERT)](#1-theme-extraction-distilbert)
  - [2. Conversation Generation (GPT-2)](#2-conversation-generation-gpt-2)
  - [3. Fact Checking (Wikipedia)](#3-fact-checking-wikipedia)
  - [4. Gemini-Powered Features (Optional)](#4-gemini-powered-features-optional)
- [API Endpoints](#api-endpoints)
- [Prerequisites](#prerequisites)
- [Setup & Installation](#setup--installation)
- [Running the Application](#running-the-application)
- [Usage Guide](#usage-guide)
- [Data Persistence](#data-persistence)
- [Troubleshooting](#troubleshooting)
- [Tech Stack](#tech-stack)

---

## Architecture Overview

The application uses a **client-server architecture** with two main processes:

```
┌─────────────────────┐     HTTP      ┌──────────────────────────────┐
│   Streamlit UI      │◄────────────►│       FastAPI Backend         │
│   (frontend/app.py) │   (REST API)  │       (backend/)             │
│                     │               │                              │
│  - Input forms      │               │  ┌──────────────────────┐   │
│  - Result cards     │               │  │  Event Analyzer      │   │
│  - Feedback buttons │               │  │  (DistilBERT)         │   │
│  - History view     │               │  ├──────────────────────┤   │
│  - Gemini features  │               │  │  Topic Generator     │   │
└─────────────────────┘               │  │  (GPT-2)             │   │
                                       │  ├──────────────────────┤   │
                                       │  │  Fact Checker        │   │
Port: 8501                              │  │  (Wikipedia API)     │   │
                                       │  ├──────────────────────┤   │
                                       │  │  Gemini Service      │   │
                                       │  │  (Google Gemini API) │   │
                                       │  ├──────────────────────┤   │
                                       │  │  History Logger      │──│──► data/conversation_history.json
                                       │  ├──────────────────────┤   │
                                       │  │  Feedback Logger     │──│──► data/feedback_history.json
                                       │  └──────────────────────┘   │
                                       │                              │
                                       └──────────────────────────────┘
                                                  Port: 8000
```

**Key design principles:**

- **Hub-and-spoke routing**: A single `conversation` router dispatches requests to isolated service modules.
- **Lazy-loaded AI models**: DistilBERT and GPT-2 pipelines are loaded once at module import time and reused across requests.
- **Singleton Gemini client**: The `google-genai` client is initialized once and cached for the lifetime of the server process.
- **JSON persistence**: Conversation history and user feedback are stored in human-readable JSON files under `data/`.
- **Frontend-backend separation**: The Streamlit frontend communicates with the FastAPI backend exclusively via REST API calls, allowing each service to be developed and scaled independently.

---

## Project Structure

```
personalized-networking-assistant/
│
├── backend/                          # FastAPI backend (Python)
│   ├── main.py                       # App entry point — creates FastAPI instance, registers routers
│   ├── models.py                     # Pydantic data models for all request/response contracts
│   ├── __init__.py
│   ├── routes/
│   │   ├── __init__.py
│   │   └── conversation.py           # All API endpoints wired to service modules
│   └── services/
│       ├── __init__.py
│       ├── event_analyzer.py         # DistilBERT zero-shot classification
│       ├── topic_generator.py        # GPT-2 text generation
│       ├── fact_checker.py           # Wikipedia REST API queries
│       ├── gemini_service.py         # Google Gemini API (smart suggestions + networking tips)
│       ├── history_logger.py         # Read/write conversation history to JSON
│       └── feedback_logger.py        # Read/write user feedback to JSON
│
├── frontend/
│   └── app.py                        # Streamlit UI — all pages, forms, and styling
│
├── data/                             # Persistence directory (auto-created)
│   ├── conversation_history.json      # History of all generated conversations
│   └── feedback_history.json          # User like/dislike feedback records
│
├── tests/
│   └── __init__.py
│
├── .env                              # Environment variables (GEMINI_API_KEY, etc.)
├── .env.example                      # Template for .env file
├── requirements.txt                  # Python dependencies
└── README.md                         # This file
```

---

## The AI Pipeline (Workflow)

### 1. Theme Extraction (DistilBERT)

**File**: `backend/services/event_analyzer.py`

When you enter an event description, the system uses **zero-shot classification** with a DistilBERT model to identify the most relevant themes. Unlike traditional classification that requires training on specific labels, zero-shot classification can categorize text into arbitrary categories without prior training.

**How it works:**

1. The event description is passed to Hugging Face's zero-shot classification pipeline.
2. The model compares the description against a default set of candidate labels (e.g., "artificial intelligence", "healthcare", "sustainability", "cybersecurity", etc.).
3. It returns confidence scores for each label and picks the top 3.
4. You can optionally supply custom candidate labels via the API.

**Why DistilBERT?** It's a distilled, faster version of BERT that retains ~97% of BERT's language understanding while being 40% smaller and 60% faster — ideal for real-time inference.

### 2. Conversation Generation (GPT-2)

**File**: `backend/services/topic_generator.py`

The extracted themes and your listed interests are combined into a structured prompt for **GPT-2**, a transformer-based language model released by OpenAI. The model generates natural-sounding conversation starters.

**How it works:**

1. The system constructs a prompt like: *"I am attending a networking event about AI, sustainability. My interests include climate change, urban planning. Here are three conversation starters I could use: 1."*
2. GPT-2 continues the text, generating numbered conversation starters.
3. A post-processing step cleans the output by stripping numbering, bullet points, and empty lines.
4. Up to 3 suggestions are returned.

**Limitations**: GPT-2 is an older model (2019) with 124M parameters. Its outputs can sometimes be repetitive or less contextually nuanced. This is why the Gemini integration exists as an upgrade path.

### 3. Fact Checking (Wikipedia)

**File**: `backend/services/fact_checker.py`

For quick factual verification before networking conversations, the system queries the **Wikipedia REST API** (`/api/rest_v1/page/summary/`). This returns a concise summary extract from the most relevant Wikipedia article.

**Error handling**: The service gracefully handles timeouts, missing articles, and network errors with user-friendly fallback messages.

### 4. Gemini-Powered Features (Optional)

**File**: `backend/services/gemini_service.py`

The Gemini integration adds two advanced features that go beyond the capabilities of the local models:

#### a. Smart Suggestions (`/api/gemini/smart-suggestions`)

Uses **Google Gemini 2.0 Flash** to generate high-quality, context-aware conversation starters. Unlike GPT-2, Gemini:
- Understands the deeper context of the event description
- Produces more creative, human-sounding suggestions
- Better connects the event's themes with the user's interests

The API accepts a `temperature` parameter (0.0–1.0) to control creativity.

#### b. Networking Tips (`/api/gemini/networking-tips`)

Generates personalized, actionable networking strategy advice:
- What key questions to ask other attendees
- How to connect event themes to personal interests in conversation
- Follow-up angles after meeting someone
- What to mention when introducing yourself

**API key required**: These features require a `GEMINI_API_KEY` in your `.env` file. Get a free key at [aistudio.google.com/apikey](https://aistudio.google.com/apikey).

---

## API Endpoints

All endpoints are prefixed with `/api` and documented via auto-generated OpenAPI/Swagger docs at `http://localhost:8000/docs`.

### Core Endpoints

| Method | Endpoint | Description | Request Body |
|--------|----------|-------------|-------------|
| `POST` | `/api/analyze-event` | Extract themes from event description | `EventRequest { description, candidate_labels? }` |
| `POST` | `/api/generate-conversation` | Full pipeline: themes → suggestions → log | `ConversationRequest { description, interests }` |
| `POST` | `/api/fact-check` | Look up topic on Wikipedia | `FactCheckRequest { query }` |
| `POST` | `/api/feedback` | Log like/dislike feedback | `FeedbackRequest { suggestion, action }` |
| `GET` | `/api/history` | Get all conversation history | — |
| `GET` | `/api/feedback-history` | Get all feedback records | — |

### Gemini Endpoints

| Method | Endpoint | Description | Request Body |
|--------|----------|-------------|-------------|
| `GET` | `/api/gemini/status` | Check if Gemini API is configured | — |
| `POST` | `/api/gemini/smart-suggestions` | Generate Gemini-powered suggestions | `GeminiSuggestionsRequest { description, interests, temperature? }` |
| `POST` | `/api/gemini/networking-tips` | Get personalized networking tips | `GeminiNetworkingTipsRequest { description, interests }` |

### Health Check

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Root health-check: `{ "status": "healthy" }` |

---

## Prerequisites

- **Python 3.10+** installed on your system
- **pip** (Python package manager)
- **Git** (optional, for version control)
- **Google Gemini API key** (optional, for Gemini features — get one free at [aistudio.google.com/apikey](https://aistudio.google.com/apikey))

---

## Setup & Installation

### Step 1: Clone or navigate to the project

```bash
cd "D:\VS Code Folder\Personlized Networking Assistant"
```

### Step 2: (Recommended) Create a virtual environment

Isolating dependencies prevents conflicts with other Python projects.

**On Windows (Command Prompt)**:
```bash
python -m venv venv
venv\Scripts\activate
```

**On Windows (PowerShell)**:
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**On macOS/Linux**:
```bash
python3 -m venv venv
source venv/bin/activate
```

You should see `(venv)` appear in your terminal prompt.

### Step 3: Install dependencies

```bash
pip install -r requirements.txt
```

This installs:
- **FastAPI** + **uvicorn** — web framework and ASGI server
- **Pydantic** — data validation and serialization
- **transformers** + **torch** — Hugging Face AI models (DistilBERT, GPT-2)
- **Streamlit** — frontend UI framework
- **requests** + **httpx** — HTTP clients
- **google-genai** — Google Gemini SDK
- **python-dotenv** — environment variable loading
- **pytest** — testing framework

> **Note on model downloads**: The first time you run the app, Hugging Face will automatically download the DistilBERT and GPT-2 models. This is a one-time download of approximately 500MB total. Ensure you have a stable internet connection.

### Step 4: Configure environment variables

Copy the template and add your Gemini API key:

```bash
copy .env.example .env
```

Then edit `.env` and replace `your-api-key-here` with your actual key:

```env
# Google Gemini API Key
# Get your key at: https://aistudio.google.com/apikey
GEMINI_API_KEY=AIzaSy...
```

The Gemini features will gracefully show a warning if the key is missing — they are optional and the core app works without them.

---

## Running the Application

You need **two terminal windows** — one for the backend server, one for the frontend UI.

### Terminal 1: Start the FastAPI Backend

```bash
cd "D:\VS Code Folder\Personlized Networking Assistant"

# Activate virtual environment (if using one):
# venv\Scripts\activate

uvicorn backend.main:app --reload --port 8000
```

**Expected output:**
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete.
```

**Flags explained:**
- `--reload` — Auto-restarts the server when you edit code (development mode)
- `--port 8000` — Runs on port 8000 (the frontend expects this)

**Verify the backend is running:**
Open [http://127.0.0.1:8000](http://127.0.0.1:8000) in your browser. You should see:
```json
{ "status": "healthy", "service": "Personalized Networking Assistant" }
```

The interactive API documentation is available at [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) (Swagger UI).

### Terminal 2: Start the Streamlit Frontend

Open a **new terminal window**, then:

```bash
cd "D:\VS Code Folder\Personlized Networking Assistant"

# Activate virtual environment (if using one):
# venv\Scripts\activate

streamlit run frontend/app.py
```

**Expected output:**
```
  You can now view your Streamlit app in your browser.

  Local URL: http://localhost:8501
```

The frontend will automatically open in your default browser. If it doesn't, navigate to [http://localhost:8501](http://localhost:8501).

### What's happening behind the scenes:

1. **Backend startup**: FastAPI loads all modules, importing DistilBERT and GPT-2 pipelines into memory. This takes 10–30 seconds on first run (model download may take longer). The `load_dotenv()` call in `main.py` reads your `.env` file so `GEMINI_API_KEY` is available globally.

2. **Frontend startup**: Streamlit loads `frontend/app.py`, renders the UI shell, and waits for user interaction. It periodically polls the backend health endpoint to show a connection indicator in the sidebar.

3. **On first request**: When you click "Generate Conversation Starters", the backend makes its first inference call. DistilBERT and GPT-2 are already loaded in memory, so the response is fast (~1–3 seconds).

---

## Usage Guide

### 🎯 Generate Conversation Starters (GPT-2)

1. Select the **"🎯 Generate"** tab from the sidebar.
2. Enter an **event description** (e.g., *"AI for Sustainable Cities conference..."*).
3. Enter your **interests** (comma-separated, e.g., *"climate change, urban planning, AI ethics"*).
4. Click **"🚀 Generate Conversation Starters"**.
5. The system extracts themes (displayed as blue tags) and generates 3 conversation starters.
6. You can **like 👍** or **dislike 👎** each suggestion to provide feedback.

### ✨ Gemini Smart Suggestions

1. Select the **"✨ Gemini"** tab from the sidebar.
2. Enter the same event description and interests.
3. Adjust the **Creativity** slider (higher = more creative but less predictable).
4. Click **"🚀 Generate Smart Suggestions"** for Gemini-powered conversation starters, or **"💡 Get Networking Tips"** for personalized networking advice.
5. Compare results with the GPT-2 tab to see the difference.

### 🔍 Quick Fact Verification

1. Select the **"🔍 Fact Check"** tab.
2. Enter a topic to look up (e.g., *"quantum computing"*).
3. Click **"🔎 Verify Fact"**.
4. A Wikipedia summary is displayed for reference.

### 📜 Conversation History

- Select the **"📜 History"** tab to browse all previously generated conversations.
- Entries are displayed in reverse chronological order with expandable details.

### 📊 Feedback History

- Select the **"📊 Feedback"** tab to view all likes and dislikes you've submitted.
- Summary metrics show total feedback, likes, and dislikes.

---

## Data Persistence

The application stores data in two JSON files under the `data/` directory:

| File | Purpose | Format |
|------|---------|--------|
| `data/conversation_history.json` | Every generated conversation (description, interests, themes, suggestions, timestamp) | JSON array of objects |
| `data/feedback_history.json` | User feedback (suggestion text, like/dislike, timestamp) | JSON array of objects |

These files are automatically created when the first entry is logged. They can be manually inspected, deleted (to reset history), or backed up.

---

## Troubleshooting

### Backend won't start

| Error | Likely Cause | Solution |
|-------|-------------|----------|
| `No module named 'backend'` | Wrong working directory | `cd` into the project root folder first |
| `ModuleNotFoundError: No module named 'torch'` | Dependencies not installed | Run `pip install -r requirements.txt` |
| `Address already in use` | Port 8000 is occupied | Kill the other process or use a different port: `uvicorn backend.main:app --reload --port 8001` (then update `frontend/app.py` `BACKEND_URL`) |
| Model download is slow | First-time download of DistilBERT/GPT-2 | Wait for it to complete (500MB total); subsequent starts will be fast |

### Frontend shows "Backend disconnected"

1. Ensure the backend is running: check `http://127.0.0.1:8000/` in your browser.
2. Verify the port — the frontend connects to port 8000 by default.
3. Check both terminals for error messages.

### Gemini features show "Not configured"

1. Ensure you've created a `.env` file with `GEMINI_API_KEY=your-key`.
2. Restart the backend after adding/updating `.env`.
3. Verify your API key at [aistudio.google.com/apikey](https://aistudio.google.com/apikey).

### DistilBERT/GPT-2 errors

If you see errors related to model loading, try clearing the Hugging Face cache:
```bash
rm -rf ~/.cache/huggingface/hub/
```
(On Windows: `rmdir /s %USERPROFILE%\.cache\huggingface\hub`)

---

## Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Backend Framework** | FastAPI (Python) | High-performance async web framework with auto-generated OpenAPI docs |
| **Frontend Framework** | Streamlit (Python) | Rapid UI development for data apps — renders as a web app |
| **AI — Theme Extraction** | DistilBERT (via Hugging Face Transformers) | Zero-shot classification for event theme detection |
| **AI — Conversation Generation** | GPT-2 (via Hugging Face Transformers) | Text generation for conversation starters |
| **AI — Advanced Features** | Google Gemini 2.0 Flash (via google-genai SDK) | Smart suggestions and networking tips |
| **Fact Checking** | Wikipedia REST API | Quick topic summaries |
| **Data Validation** | Pydantic v2 | Request/response type safety and validation |
| **Persistence** | Local JSON files | Conversation history and feedback storage |
| **Server** | Uvicorn | ASGI server for FastAPI |
| **Testing** | pytest | Unit testing |

---

## License

This project is for educational and personal use. Built with FastAPI, Streamlit, Hugging Face Transformers, and Google Gemini.
