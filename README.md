# web-mcp-server

MCP server that exposes `web_search`, `web_fetch`, and `research` tools, allowing LLM applications to search the web, fetch page content, and research ArXiv papers.

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

### `research`

Search ArXiv papers, fetch HTML content, chunk, and return the most relevant chunks ranked by BM25.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `query` | `str` | — | Research query |
| `max_search_results` | `int` | `15` | Number of ArXiv search results to consider |
| `max_papers` | `int` | `3` | Number of papers to fetch and analyze |
| `max_chunks` | `int` | `15` | Number of top relevant chunks to return |

Returns `{query, sources, chunks, total_chunks_analyzed}`.

## Deep Research Prompt

The server exposes a `deep_research` prompt via the MCP protocol. Clients can discover and call it with a query parameter to get a system prompt for iterative deep research.

**Usage:** Call `deep_research(query="...")` to get a prompt that guides an LLM agent to orchestrate `web_search`, `web_fetch`, and `research` in multi-round investigation following the CoSearch deep search pattern.

## Quickstart

```bash
# Install dependencies
uv sync

# Run the server (SSE on port 8642, default)
uv run python -m src.server

# Run with streamable HTTP transport
TRANSPORT=streamable-http uv run python -m src.server
```

### Environment Variables

| Variable | Default | Description |
|---|---|---|
| `HOST` | `0.0.0.0` | Server bind address |
| `PORT` | `8642` | Server port |
| `TRANSPORT` | `sse` | Transport protocol: `sse` or `streamable-http` |

### Health Check

A health check endpoint is available at the root path:

```bash
curl http://localhost:8642/
# {"status": "ok"}
```

## Connect via Claude Code

```bash
# SSE (default)
claude mcp add web-tools http://localhost:8642/sse

# Streamable HTTP
claude mcp add --transport http web-tools http://localhost:8642/mcp
```

## Connect via MCP Inspector

```bash
npx -y @modelcontextprotocol/inspector
# Connect to http://localhost:8642/sse (SSE) or http://localhost:8642/mcp (streamable HTTP) in the UI
```

## Project Structure

```
src/
├── server.py            # MCP server setup + tool/prompt registration
├── tools/
│   ├── web_search.py    # DuckDuckGo search logic
│   ├── web_fetch.py     # URL fetch, HTML cleaning, markdown conversion
│   └── research.py      # ArXiv paper search, fetch, chunk, BM25 ranking
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
| `rank-bm25` | BM25 document ranking |
| `nltk` | Text tokenization |
