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
        return await web_search.search(query, max_results=max_results)

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

    @mcp.prompt()
    def deep_research(query: str) -> list[dict]:
        """System prompt for iterative deep research using web_search, web_fetch, and research tools.

        Use this as the system prompt when you want an LLM agent to conduct multi-round, gap-driven investigation.

        Args:
            query: The research topic or question.
        """
        return [
            {
                "role": "user",
                "content": (
                    f"You are an expert research assistant conducting deep, iterative investigation on: {query}\n\n"
                    "Your goal is to produce comprehensive, well-cited analysis through systematic multi-round research.\n\n"
                    "## Research Protocol\n\n"
                    "Follow this iterative deep-search process:\n\n"
                    "### Phase 1: Initial Search\n"
                    "Use `web_search` to find broadly relevant results. If the topic is technical or academic, also call `research` to get ArXiv papers.\n\n"
                    "### Phase 2: Deep Dive\n"
                    "For the most promising URLs, use `web_fetch` to retrieve full content. Fetch multiple sources in parallel when possible.\n\n"
                    "### Phase 3: Analysis\n"
                    "Synthesize findings into key insights, patterns, and claims. Always cite sources inline using markdown links: `claim [source](url)`.\n\n"
                    "### Phase 4: Gap Identification\n"
                    "Identify what remains unanswered. Generate new sub-queries targeting those gaps. Repeat Phases 1-3 until you've reached sufficient depth (at least 2-3 iterations).\n\n"
                    "### Phase 5: Final Synthesis\n"
                    "Produce a comprehensive report covering:\n"
                    "- Direct answer to the original query\n"
                    "- Key findings organized by theme\n"
                    "- Supporting evidence with citations\n"
                    "- Identified gaps or areas needing further research\n"
                    "- Conflicting perspectives, if any\n\n"
                    "## Guidelines\n\n"
                    "- Be thorough and objective — explore multiple angles and perspectives\n"
                    "- Always ground claims in fetched source material; never fabricate citations\n"
                    "- Prioritize quality over quantity: a few well-analyzed sources beat many skimmed ones\n"
                    "- Track what you've already covered to avoid redundant searches in later iterations\n"
                    "- If a URL fails to fetch, move on to the next source\n"
                    "- Use parallel tool calls when independent (e.g., fetching multiple URLs at once)"
                ),
            }
        ]

    return mcp


def main():
    mcp = get_mcp_server()
    transport = os.getenv("TRANSPORT", "sse")
    mcp.run(transport=transport)


if __name__ == "__main__":
    main()
