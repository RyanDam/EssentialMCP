import asyncio

from ddgs import DDGS


def _search_sync(query: str, max_results: int) -> list[dict]:
    max_results = min(max_results, 30)
    results = []
    with DDGS() as ddgs:
        for result in ddgs.text(query, max_results=max_results):
            results.append({
                "title": result.get("title", ""),
                "url": result.get("href", ""),
                "description": result.get("body", ""),
            })
    return results


async def search(query: str, max_results: int = 10) -> list[dict]:
    """Search the web using DuckDuckGo."""
    return await asyncio.to_thread(_search_sync, query, max_results)
