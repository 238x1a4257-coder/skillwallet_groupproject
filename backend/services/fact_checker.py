"""
Fact Checker Service

Provides quick fact verification by querying the Wikipedia REST API.
Returns a summarized extract from the most relevant Wikipedia article.
"""

import requests

WIKIPEDIA_API_URL = "https://en.wikipedia.org/api/rest_v1/page/summary/"

# Wikipedia requires a User-Agent header for API requests
HEADERS = {
    "User-Agent": "PersonalizedNetworkingAssistant/1.0 (https://github.com/example; contact@example.com)"
}


def fact_check(query: str) -> str:
    """
    Look up a topic on Wikipedia and return a summary extract.

    Args:
        query: The search query string to look up on Wikipedia.

    Returns:
        A summary string from Wikipedia, or a fallback error message.
    """
    try:
        # URL-encode spaces for the API request
        encoded_query = query.replace(" ", "%20")
        url = f"{WIKIPEDIA_API_URL}{encoded_query}"

        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()

        data = response.json()
        summary = data.get("extract", "No summary available for this topic.")

        return summary

    except requests.exceptions.Timeout:
        return "The request to Wikipedia timed out. Please try again later."

    except requests.exceptions.HTTPError:
        return f"Could not find a Wikipedia article for '{query}'. Please check the spelling or try a different search term."

    except requests.exceptions.RequestException:
        return "An error occurred while connecting to Wikipedia. Please check your internet connection and try again."

    except (KeyError, ValueError):
        return "Received an unexpected response from Wikipedia. Please try again later."
