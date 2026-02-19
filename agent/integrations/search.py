"""
agent/integrations/search.py — Web search using DuckDuckGo and page reading via trafilatura.
No credentials required.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional


def search_web(query: str, max_results: int = 5) -> List[Dict[str, str]]:
    """Return up to max_results DuckDuckGo search results."""
    from duckduckgo_search import DDGS
    results: List[Dict[str, str]] = []
    with DDGS() as ddgs:
        for r in ddgs.text(query, max_results=max_results):
            results.append({
                "title": r.get("title", ""),
                "url": r.get("href", ""),
                "snippet": r.get("body", ""),
            })
    return results


def read_webpage(url: str) -> Optional[str]:
    """Fetch and extract clean article text from a URL using trafilatura."""
    import trafilatura
    downloaded = trafilatura.fetch_url(url)
    if not downloaded:
        return None
    return trafilatura.extract(downloaded)
