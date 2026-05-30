import os

from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from mcp.server.fastmcp import FastMCP

from src.tools import web_fetch, web_search, research


def get_mcp_server() -> FastMCP:
    """Create and configure the MCP server with all tools."""
    mcp = FastMCP(
        "WebTools",
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", "8642")),
    )
    for app in (mcp.sse_app(), mcp.streamable_http_app()):
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_methods=["*"],
            allow_headers=["*"],
        )

    @mcp.custom_route("/", methods=["GET"])
    async def health_check(request: Request) -> JSONResponse:
        return JSONResponse({"status": "ok"})

    @mcp.tool()
    async def web_search_tool(query: str, max_results: int = 10) -> list[dict]:
        """Search the web using DuckDuckGo and return results.

        Args:
            query: The search query string.
            max_results: Maximum number of results to return (default 10, max 30).
        """
        return web_search.search(query, max_results=max_results)

    @mcp.tool()
    async def web_fetch_tool(url: str, max_length: int = -1) -> dict:
        """Fetch full content from a URL and return it as markdown.

        Args:
            url: The URL to fetch.
            max_length: Maximum characters of markdown output to return. Default -1 means no limit.
        """
        return await web_fetch.fetch(url, max_length=max_length)

    @mcp.tool()
    async def research_tool(
        query: str,
        max_search_results: int = 15,
        max_papers: int = 3,
        max_chunks: int = 15,
    ) -> dict:
        """Research ArXiv papers: search arxiv.org, fetch paper HTML, chunk content, and return the most relevant chunks ranked by BM25.

        Args:
            query: The research query.
            max_search_results: Number of ArXiv search results to consider (default 15).
            max_papers: Number of papers to fetch and analyze (default 3).
            max_chunks: Number of top relevant chunks to return (default 15).
        """
        return await research.research(
            query,
            max_search_results=max_search_results,
            max_papers=max_papers,
            max_chunks=max_chunks,
        )

    return mcp


def main():
    mcp = get_mcp_server()
    transport = os.getenv("TRANSPORT", "sse")
    mcp.run(transport=transport)


if __name__ == "__main__":
    main()
