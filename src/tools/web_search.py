from ddgs import DDGS


def search(query: str, max_results: int = 10) -> list[dict]:
    """Search the web using DuckDuckGo."""
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
