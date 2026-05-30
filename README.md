# web-mcp-server

MCP server that exposes `web_search` and `web_fetch` tools, allowing LLM applications to search the web and fetch page content.

## Tools

### `web_search`

Search the web via DuckDuckGo.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `query` | `str` | — | Search query |
| `max_results` | `int` | `10` | Max results to return (capped at 30) |

Returns a list of `{title, url, description}`.

### `web_fetch`

Fetch a URL and return cleaned markdown content.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `url` | `str` | — | URL to fetch |
| `max_length` | `int` | `-1` | Max characters of markdown output to return. `-1` means no limit (full content). |

Returns `{content, title, url, content_type}`.

## Quickstart

```bash
# Install dependencies
uv sync

# Run the server (streamable HTTP on port 8000)
uv run python -m src.server
```

## Connect via Claude Code

```bash
claude mcp add --transport http web-tools http://localhost:8000/mcp
```

## Connect via MCP Inspector

```bash
npx -y @modelcontextprotocol/inspector
# Connect to http://localhost:8000/mcp in the UI
```

## Project Structure

```
src/
├── server.py            # MCP server setup + tool registration
├── tools/
│   ├── web_search.py    # DuckDuckGo search logic
│   └── web_fetch.py     # URL fetch, HTML cleaning, markdown conversion
└── utils/
    └── html.py          # HTML title extraction
```

## Requirements

- Python >= 3.10
- [uv](https://docs.astral.sh/uv/) (recommended) or pip

## Dependencies

| Package | Purpose |
|---|---|
| `mcp[cli]` | Official MCP Python SDK |
| `ddgs` | DuckDuckGo search |
| `httpx` | Async HTTP client |
| `beautifulsoup4` | HTML parsing and cleaning |
| `markdownify` | HTML-to-markdown conversion |
