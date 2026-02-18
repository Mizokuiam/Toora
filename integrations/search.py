"""
Web search via duckduckgo-search and article extraction via trafilatura.
No credentials required.
"""

from __future__ import annotations

from typing import Any, Dict, List

try:
    from duckduckgo_search import DDGS
except ImportError:
    DDGS = None

import trafilatura


def search_web(query: str, max_results: int = 5) -> List[Dict[str, Any]]:
    """
    Search using duckduckgo-search. Returns list of dicts: title, url, snippet.
    """
    if DDGS is None:
        return [{"error": "duckduckgo-search not installed"}]
    results: List[Dict[str, Any]] = []
    try:
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=max_results):
                results.append({
                    "title": r.get("title", ""),
                    "url": r.get("href", r.get("link", "")),
                    "snippet": r.get("body", ""),
                })
    except Exception as e:
        results = [{"error": str(e)}]
    return results


def read_webpage(url: str) -> str:
    """
    Fetch URL and extract main article text using trafilatura.
    Returns plain text or error message.
    """
    try:
        import urllib.request
        req = urllib.request.Request(url, headers={"User-Agent": "TooraBot/1.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            html = resp.read().decode("utf-8", errors="replace")
        text = trafilatura.extract(html)
        return text or "No main content extracted."
    except Exception as e:
        return f"Error: {e}"
