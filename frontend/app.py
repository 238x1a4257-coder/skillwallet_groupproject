"""
Personalized Networking Assistant — Streamlit Frontend

Provides an intuitive user interface for:
  - Generating personalized conversation starters
  - Fact-checking topics via Wikipedia
  - Reviewing conversation history
  - Viewing feedback history

Connects to the FastAPI backend at BACKEND_URL.
"""

import json
from datetime import datetime

import requests
import streamlit as st

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

BACKEND_URL = "http://127.0.0.1:8000"
API_PREFIX = f"{BACKEND_URL}/api"

# ---------------------------------------------------------------------------
# Page configuration (must be the first Streamlit command)
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="Personalized Networking Assistant",
    page_icon="🤝",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Custom CSS for a polished look
# ---------------------------------------------------------------------------

st.markdown(
    """
<style>
    /* Main container styling */
    .main > .block-container {
        padding-top: 2rem;
    }

    /* Header styles */
    .app-header {
        padding: 1.5rem 0 0.5rem 0;
        border-bottom: 2px solid #f0f2f6;
        margin-bottom: 1.5rem;
    }
    .app-header h1 {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1a1a2e;
        margin-bottom: 0.25rem;
    }
    .app-header p {
        font-size: 1rem;
        color: #6c757d;
    }

    /* Card-like containers */
    .result-card {
        background: #ffffff;
        border: 1px solid #e9ecef;
        border-radius: 12px;
        padding: 1.25rem 1.5rem;
        margin: 0.75rem 0;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
        transition: box-shadow 0.2s ease, transform 0.15s ease;
    }
    .result-card:hover {
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
        transform: translateY(-1px);
    }
    .result-card .suggestion-text {
        font-size: 1rem;
        line-height: 1.5;
        color: #212529;
    }

    /* Feedback badges */
    .badge-like {
        color: #2e7d32;
        font-weight: 600;
        background: #e8f5e9;
        padding: 0.2rem 0.6rem;
        border-radius: 20px;
        font-size: 0.8rem;
    }
    .badge-dislike {
        color: #c62828;
        font-weight: 600;
        background: #ffebee;
        padding: 0.2rem 0.6rem;
        border-radius: 20px;
        font-size: 0.8rem;
    }

    /* Theme tags */
    .theme-tag {
        display: inline-block;
        background: #e3f2fd;
        color: #1565c0;
        padding: 0.2rem 0.7rem;
        border-radius: 16px;
        font-size: 0.8rem;
        font-weight: 500;
        margin: 0.15rem 0.25rem;
    }

    /* Success / info boxes */
    .success-box {
        background: #e8f5e9;
        border-left: 4px solid #2e7d32;
        padding: 0.75rem 1rem;
        border-radius: 6px;
        margin: 0.5rem 0;
    }

    /* Spinner replacement */
    .stSpinner > div {
        border-top-color: #1565c0 !important;
    }

    /* Sidebar tweaks */
    .css-1d391kg, .css-1lcbmhc {
        padding-top: 1rem;
    }
    .sidebar-greeting {
        font-size: 0.9rem;
        color: #6c757d;
        margin-top: 1rem;
        padding: 0 0.5rem;
    }

    /* Metric cards */
    .metric-card {
        background: #f8f9fa;
        border-radius: 10px;
        padding: 1rem;
        text-align: center;
        border: 1px solid #e9ecef;
    }
    .metric-card .metric-value {
        font-size: 1.8rem;
        font-weight: 700;
        color: #1a1a2e;
    }
    .metric-card .metric-label {
        font-size: 0.8rem;
        color: #6c757d;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0.5rem;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px 8px 0 0;
        padding: 0.5rem 1rem;
    }
</style>
""",
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Session-state initialisation
# ---------------------------------------------------------------------------

_DEFAULT_STATE = {
    "generated_suggestions": [],
    "generated_themes": [],
    "last_event_description": "",
    "last_interests": [],
    "fact_check_result": None,
    "feedback_sent_for": set(),  # track which suggestions already had feedback
}

for key, default in _DEFAULT_STATE.items():
    if key not in st.session_state:
        st.session_state[key] = default


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------


def _safe_api_post(endpoint: str, payload: dict) -> dict | None:
    """POST to the backend and return parsed JSON, or None on error."""
    url = f"{API_PREFIX}/{endpoint}"
    try:
        resp = requests.post(url, json=payload, timeout=60)
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.ConnectionError:
        st.error(
            f"⚠️ Could not connect to the backend at **{BACKEND_URL}**. "
            "Make sure the FastAPI server is running."
        )
    except requests.exceptions.Timeout:
        st.error("⏱️ The request timed out. Please try again.")
    except requests.exceptions.HTTPError as exc:
        status = exc.response.status_code
        detail = exc.response.text
        st.error(f"❌ Server error ({status}): {detail}")
    except ValueError:
        st.error("❌ Received an invalid response from the server.")
    return None


def _safe_api_get(endpoint: str) -> list | None:
    """GET from the backend and return parsed JSON list, or None on error."""
    url = f"{API_PREFIX}/{endpoint}"
    try:
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.ConnectionError:
        st.error(
            f"⚠️ Could not connect to the backend at **{BACKEND_URL}**. "
            "Make sure the FastAPI server is running."
        )
    except requests.exceptions.Timeout:
        st.error("⏱️ The request timed out. Please try again.")
    except ValueError:
        return []
    return []


def _build_theme_tags(themes: list[str]) -> str:
    """Return an HTML string of theme tag badges."""
    if not themes:
        return ""
    tags = "".join(
        f'<span class="theme-tag">{theme}</span>' for theme in themes
    )
    return f'<div style="margin: 0.5rem 0;">{tags}</div>'


def _format_timestamp(ts: str) -> str:
    """Format an ISO timestamp to a human-friendly string."""
    try:
        dt = datetime.fromisoformat(ts)
        return dt.strftime("%b %d, %Y · %I:%M %p")
    except (ValueError, TypeError):
        return ts or "Unknown"


# ---------------------------------------------------------------------------
# UI Sections
# ---------------------------------------------------------------------------


def render_header():
    """Render the application header."""
    st.markdown(
        '<div class="app-header">'
        '<h1>🤝 Personalized Networking Assistant</h1>'
        "<p>Generate smart, tailored conversation starters for professional "
        "and social networking events — powered by AI.</p>"
        "</div>",
        unsafe_allow_html=True,
    )


def render_generate_section():
    """Story 2 & 3: Input section + generation flow + results + feedback."""
    st.markdown("### 🎯 Generate Conversation Starters")

    col1, col2 = st.columns([3, 2])

    with col1:
        event_description = st.text_area(
            "📋 **Event Description**",
            placeholder=(
                'e.g. "AI for Sustainable Cities: A summit bringing together '
                "urban planners, technologists, and environmentalists to "
                'explore how AI can shape the cities of tomorrow."'
            ),
            height=130,
            key="event_desc_input",
        )

    with col2:
        interests_input = st.text_input(
            "💡 **Your Interests**",
            placeholder="e.g. climate change, urban planning, AI ethics",
            help="Separate multiple interests with commas",
            key="interests_input",
        )
        interests = (
            [i.strip() for i in interests_input.split(",") if i.strip()]
            if interests_input
            else []
        )

    generate_btn = st.button(
        "🚀 Generate Conversation Starters",
        type="primary",
        use_container_width=True,
        disabled=not (event_description and interests),
    )

    # --- Generation ---------------------------------------------------------
    if generate_btn:
        if not event_description or not interests:
            st.warning("Please provide both an event description and your interests.")
        else:
            with st.spinner("🧠 Analyzing event themes with DistilBERT …"):
                result = _safe_api_post(
                    "generate-conversation",
                    {
                        "description": event_description,
                        "interests": interests,
                    },
                )

            if result:
                st.session_state.generated_themes = result.get("themes", [])
                st.session_state.generated_suggestions = result.get(
                    "suggestions", []
                )
                st.session_state.last_event_description = event_description
                st.session_state.last_interests = interests
                # Reset feedback tracking for new suggestions
                st.session_state.feedback_sent_for = set()

                # Show success animation
                st.balloons()

    # --- Results ------------------------------------------------------------
    if st.session_state.generated_suggestions:
        themes = st.session_state.generated_themes
        suggestions = st.session_state.generated_suggestions

        st.markdown("---")
        st.markdown("### ✨ Your Personalized Conversation Starters")

        # Show extracted themes
        if themes:
            st.markdown(
                f"**Detected Themes:** {_build_theme_tags(themes)}",
                unsafe_allow_html=True,
            )

        # Display each suggestion with a feedback row
        for idx, suggestion in enumerate(suggestions):
            card_id = f"suggestion_{idx}"

            with st.container():
                st.markdown(
                    f'<div class="result-card">'
                    f'<div class="suggestion-text">💬 {suggestion}</div>'
                    f"</div>",
                    unsafe_allow_html=True,
                )

                # Feedback row (like / dislike)
                if suggestion not in st.session_state.feedback_sent_for:
                    fb_col1, fb_col2, _ = st.columns([0.5, 0.5, 9])
                    with fb_col1:
                        if st.button(
                            "👍 Useful",
                            key=f"like_{idx}",
                            use_container_width=True,
                        ):
                            _safe_api_post(
                                "feedback",
                                {"suggestion": suggestion, "action": "like"},
                            )
                            st.session_state.feedback_sent_for.add(suggestion)
                            st.rerun()
                    with fb_col2:
                        if st.button(
                            "👎 Not Useful",
                            key=f"dislike_{idx}",
                            use_container_width=True,
                        ):
                            _safe_api_post(
                                "feedback",
                                {
                                    "suggestion": suggestion,
                                    "action": "dislike",
                                },
                            )
                            st.session_state.feedback_sent_for.add(suggestion)
                            st.rerun()
                else:
                    st.markdown(
                        '<div class="success-box">✅ Thanks for your feedback!</div>',
                        unsafe_allow_html=True,
                    )

        # Clear button
        if st.button("🔄 Clear Results", type="secondary"):
            for key in [
                "generated_suggestions",
                "generated_themes",
                "last_event_description",
                "last_interests",
                "feedback_sent_for",
            ]:
                st.session_state[key] = (
                    set() if key == "feedback_sent_for" else []
                    if isinstance(st.session_state[key], list)
                    else ""
                )
            st.rerun()


def render_fact_check_section():
    """Story 4: Fact-checking using Wikipedia."""
    st.markdown("### 🔍 Quick Fact Verification")
    st.markdown(
        "Look up a topic to get a quick, reliable summary from Wikipedia "
        "before your next networking conversation."
    )

    query = st.text_input(
        "**Search Topic**",
        placeholder='e.g. "blockchain in healthcare" or "quantum computing"',
        key="factcheck_input",
    )

    if st.button("🔎 Verify Fact", type="primary", use_container_width=True):
        if not query:
            st.warning("Please enter a topic to look up.")
        else:
            with st.spinner(f"📚 Looking up '{query}' on Wikipedia …"):
                result = _safe_api_post("fact-check", {"query": query})
            if result:
                st.session_state.fact_check_result = {
                    "query": query,
                    "summary": result.get("summary", ""),
                }

    # Display result
    if st.session_state.fact_check_result:
        fc = st.session_state.fact_check_result
        st.markdown("---")
        st.markdown(f"#### 📖 {fc['query']}")
        st.markdown(
            f'<div style="background: #f8f9fa; color: #212529; padding: 1.25rem; '
            f'border-radius: 10px; border-left: 4px solid #1565c0; '
            f'line-height: 1.6;">{fc["summary"]}</div>',
            unsafe_allow_html=True,
        )

        if st.button("🔄 Clear Result", key="clear_factcheck"):
            st.session_state.fact_check_result = None
            st.rerun()


def render_history_section():
    """Story 5: Conversation history view."""
    st.markdown("### 📜 Conversation History")
    st.markdown(
        "Review your previously generated conversations and see which "
        "ones you found most useful."
    )

    with st.spinner("Loading conversation history …"):
        history = _safe_api_get("history")

    if not history:
        st.info(
            "📭 No conversation history yet. Generate some conversation "
            "starters to see them here!"
        )
        return

    # Summary metrics
    total = len(history)
    st.markdown(
        f'<div style="display:flex; gap:1rem; margin-bottom:1rem;">'
        f'<div class="metric-card"><div class="metric-value">{total}</div>'
        f'<div class="metric-label">Total Conversations</div></div>'
        f"</div>",
        unsafe_allow_html=True,
    )

    # Display each entry in reverse chronological order
    for entry in reversed(history):
        timestamp = _format_timestamp(entry.get("timestamp", ""))
        description = entry.get("description", "")
        interests = entry.get("interests", [])
        themes = entry.get("themes", [])
        suggestions = entry.get("suggestions", [])

        with st.expander(
            f"🗓️ **{timestamp}** — "
            f"{description[:80]}{'…' if len(description) > 80 else ''}",
            expanded=False,
        ):
            st.markdown(f"**Event:** {description}")
            if interests:
                st.markdown(
                    f"**Interests:** {', '.join(interests)}"
                )
            if themes:
                st.markdown(
                    f"Themes: {', '.join(themes)}"
                )
            if suggestions:
                st.markdown("**Suggestions:**")
                for s in suggestions:
                    st.markdown(f"- 💬 {s}")


def render_feedback_section():
    """Story 6: Feedback history view."""
    st.markdown("### 📊 Feedback History")
    st.markdown(
        "View all likes and dislikes you've submitted on conversation "
        "suggestions."
    )

    with st.spinner("Loading feedback history …"):
        feedback = _safe_api_get("feedback-history")

    if not feedback:
        st.info(
            "📭 No feedback recorded yet. Like or dislike a suggestion "
            "to see it here!"
        )
        return

    # Summary metrics
    total_fb = len(feedback)
    likes = sum(1 for f in feedback if f.get("action") == "like")
    dislikes = sum(1 for f in feedback if f.get("action") == "dislike")

    cols = st.columns(3)
    for col, val, label in zip(
        cols,
        [total_fb, likes, dislikes],
        ["Total Feedback", "👍 Likes", "👎 Dislikes"],
    ):
        with col:
            st.markdown(
                f'<div class="metric-card">'
                f'<div class="metric-value">{val}</div>'
                f'<div class="metric-label">{label}</div>'
                f"</div>",
                unsafe_allow_html=True,
            )

    st.markdown("---")

    # Display each feedback entry
    for entry in reversed(feedback):
        suggestion = entry.get("suggestion", "")
        action = entry.get("action", "")
        timestamp = _format_timestamp(entry.get("timestamp", ""))

        badge = (
            '<span class="badge-like">👍 Liked</span>'
            if action == "like"
            else '<span class="badge-dislike">👎 Disliked</span>'
        )

        st.markdown(
            f'<div class="result-card">'
            f'<div style="display:flex; justify-content:space-between; '
            f'align-items:center;">'
            f'<span style="font-size:0.85rem; color:#6c757d;">{timestamp}</span>'
            f"{badge}"
            f"</div>"
            f'<div style="margin-top:0.5rem;">💬 {suggestion}</div>'
            f"</div>",
            unsafe_allow_html=True,
        )


# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# Gemini helpers
# ---------------------------------------------------------------------------


def _check_gemini_status() -> dict:
    """Check if Gemini API is configured."""
    try:
        resp = requests.get(f"{API_PREFIX}/gemini/status", timeout=5)
        if resp.status_code == 200:
            return resp.json()
        return {"configured": False, "message": "Backend unavailable"}
    except requests.exceptions.RequestException:
        return {"configured": False, "message": "Backend unavailable"}


def render_gemini_section():
    """Gemini-powered smart suggestions and networking tips."""
    st.markdown("### ✨ Gemini Smart Suggestions")
    st.markdown(
        "Leverage **Google Gemini** for more creative, context-aware conversation "
        "starters and personalized networking tips — beyond the standard GPT-2 generation."
    )

    # Check Gemini status
    gemini_status = _check_gemini_status()
    if not gemini_status.get("configured"):
        st.warning(
            "⚠️ **Gemini API not configured.** "
            "Set the `GEMINI_API_KEY` environment variable in your `.env` file. "
            "Get a free key at [aistudio.google.com/apikey](https://aistudio.google.com/apikey)."
        )
        return

    st.success("✅ Gemini API is connected and ready!")

    # --- Input form ---
    col1, col2 = st.columns([3, 2])

    with col1:
        event_description = st.text_area(
            "📋 **Event Description**",
            placeholder=(
                'e.g. "AI for Sustainable Cities: A summit bringing together '
                "urban planners, technologists, and environmentalists to "
                'explore how AI can shape the cities of tomorrow."'
            ),
            height=130,
            key="gemini_event_desc",
        )

    with col2:
        interests_input = st.text_input(
            "💡 **Your Interests**",
            placeholder="e.g. climate change, urban planning, AI ethics",
            help="Separate multiple interests with commas",
            key="gemini_interests",
        )
        interests = (
            [i.strip() for i in interests_input.split(",") if i.strip()]
            if interests_input
            else []
        )

        temperature = st.slider(
            "🎨 Creativity",
            min_value=0.0,
            max_value=1.0,
            value=0.8,
            step=0.1,
            help="Higher values produce more creative but less predictable suggestions",
            key="gemini_temp",
        )

    # --- Action buttons ---
    action_col1, action_col2 = st.columns(2)

    with action_col1:
        generate_btn = st.button(
            "🚀 Generate Smart Suggestions",
            type="primary",
            use_container_width=True,
            disabled=not (event_description and interests),
        )

    with action_col2:
        tips_btn = st.button(
            "💡 Get Networking Tips",
            type="secondary",
            use_container_width=True,
            disabled=not (event_description and interests),
        )

    # --- Smart Suggestions ---
    if generate_btn:
        if not event_description or not interests:
            st.warning("Please provide both an event description and your interests.")
        else:
            with st.spinner("🧠 Gemini is crafting your conversation starters …"):
                result = _safe_api_post(
                    "gemini/smart-suggestions",
                    {
                        "description": event_description,
                        "interests": interests,
                        "temperature": temperature,
                    },
                )

            if result and "suggestions" in result:
                st.markdown("---")
                st.markdown("### 💬 Gemini Suggestions")

                for idx, suggestion in enumerate(result["suggestions"]):
                    st.markdown(
                        f'<div class="result-card">'
                        f'<div style="display:flex; gap:0.75rem; align-items:flex-start;">'
                        f'<span style="background:#1565c0; color:white; '
                        f'border-radius:50%; width:28px; height:28px; '
                        f'display:flex; align-items:center; justify-content:center; '
                        f'font-size:0.8rem; font-weight:600; flex-shrink:0;">'
                        f"{idx + 1}</span>"
                        f'<div class="suggestion-text">{suggestion}</div>'
                        f"</div></div>",
                        unsafe_allow_html=True,
                    )

                # Compare with GPT-2 option
                st.markdown(
                    '<div style="background:#f3f4f6; padding:0.75rem 1rem; '
                    'border-radius:8px; margin-top:0.5rem; font-size:0.85rem; '
                    'color:#6c757d;">'
                    '💡 <strong>Tip:</strong> Try the "Generate" tab to compare '
                    'these Gemini results with the standard GPT-2 suggestions.'
                    "</div>",
                    unsafe_allow_html=True,
                )

    # --- Networking Tips ---
    if tips_btn:
        if not event_description or not interests:
            st.warning("Please provide both an event description and your interests.")
        else:
            with st.spinner("🧠 Gemini is preparing your networking tips …"):
                result = _safe_api_post(
                    "gemini/networking-tips",
                    {
                        "description": event_description,
                        "interests": interests,
                    },
                )

            if result and "tips" in result:
                st.markdown("---")
                st.markdown("### 🎯 Networking Tips")

                tip_icons = ["❓", "🔗", "📧", "👋"]
                for idx, tip in enumerate(result["tips"]):
                    icon = tip_icons[idx] if idx < len(tip_icons) else "💡"
                    st.markdown(
                        f'<div class="result-card">'
                        f'<div style="display:flex; gap:0.75rem; align-items:flex-start;">'
                        f'<span style="font-size:1.5rem;">{icon}</span>'
                        f'<div class="suggestion-text">{tip}</div>'
                        f"</div></div>",
                        unsafe_allow_html=True,
                    )


# Sidebar navigation
# ---------------------------------------------------------------------------

st.sidebar.markdown(
    "<h2 style='text-align:center;'>🤝 Networking<br>Assistant</h2>",
    unsafe_allow_html=True,
)
st.sidebar.markdown("---")

NAV_OPTIONS = {
    "🎯 Generate": "generate",
    "✨ Gemini": "gemini",
    "🔍 Fact Check": "factcheck",
    "📜 History": "history",
    "📊 Feedback": "feedback",
}

selected = st.sidebar.radio("Navigation", list(NAV_OPTIONS.keys()), label_visibility="collapsed")
page = NAV_OPTIONS[selected]

st.sidebar.markdown("---")
st.sidebar.markdown(
    f'<div class="sidebar-greeting">'
    f"Powered by DistilBERT + GPT-2 + Gemini<br>"
    f"FastAPI backend · Streamlit UI<br>"
    f'<span style="font-size:0.75rem;">{datetime.now().strftime("%Y")}</span>'
    f"</div>",
    unsafe_allow_html=True,
)

# Backend connection status indicator
try:
    resp = requests.get(f"{BACKEND_URL}/", timeout=3)
    if resp.status_code == 200:
        st.sidebar.markdown(
            '<div style="padding:0.5rem; text-align:center;">'
            '<span style="color:#2e7d32;">●</span> Backend connected'
            "</div>",
            unsafe_allow_html=True,
        )
    else:
        st.sidebar.markdown(
            '<div style="padding:0.5rem; text-align:center;">'
            '<span style="color:#c62828;">●</span> Backend error'
            "</div>",
            unsafe_allow_html=True,
        )
except requests.exceptions.RequestException:
    st.sidebar.markdown(
        '<div style="padding:0.5rem; text-align:center;">'
        '<span style="color:#c62828;">●</span> Backend disconnected'
        "</div>",
        unsafe_allow_html=True,
    )

# ---------------------------------------------------------------------------
# Page router
# ---------------------------------------------------------------------------

render_header()

if page == "generate":
    render_generate_section()
elif page == "gemini":
    render_gemini_section()
elif page == "factcheck":
    render_fact_check_section()
elif page == "history":
    render_history_section()
elif page == "feedback":
    render_feedback_section()

# ---------------------------------------------------------------------------
# Footer
# ---------------------------------------------------------------------------

st.markdown("---")
st.markdown(
    "<div style='text-align:center; color:#adb5bd; font-size:0.8rem;'>"
    "<strong>Personalized Networking Assistant</strong> · "
    "Built with FastAPI + Streamlit · "
    "DistilBERT for theme extraction · GPT-2 for conversation generation"
    "</div>",
    unsafe_allow_html=True,
)
