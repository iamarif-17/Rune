"""
Web search tool, using Tavily (https://tavily.com) — a search API built for
LLM/agent use cases. Returns clean, pre-summarized results instead of raw HTML.
"""
import os
import httpx

SEARCH_API_KEY = os.getenv("SEARCH_API_KEY")


def web_search(query: str, max_results: int = 3) -> list[dict]:
    """
    Returns a list of {"snippet": str, "url": str} dicts.
    """
    if not SEARCH_API_KEY:
        # no key configured - return empty rather than crashing, so local dev
        # without a search key doesn't break the whole pipeline
        return []

    try:
        resp = httpx.post(
            "https://api.tavily.com/search",
            json={
                "api_key": SEARCH_API_KEY,
                "query": query,
                "max_results": max_results,
                "search_depth": "basic",
            },
            timeout=15.0,
        )
        resp.raise_for_status()
        data = resp.json()
        return [
            {"snippet": item.get("content", ""), "url": item.get("url")}
            for item in data.get("results", [])[:max_results]
        ]
    except httpx.HTTPError as e:
        print(f"[web_search] Tavily request failed: {e}")
        return []