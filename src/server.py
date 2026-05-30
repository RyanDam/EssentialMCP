from mcp.server.fastmcp import FastMCP

from src.tools import web_fetch, web_search


def get_mcp_server() -> FastMCP:
    """Create and configure the MCP server with all tools."""
    mcp = FastMCP("WebTools")

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

    return mcp


def main():
    mcp = get_mcp_server()
    mcp.run(transport="streamable-http")


if __name__ == "__main__":
    main()
