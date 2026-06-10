# EssentialMCP — Agent Notes

## Run the server
```bash
uv run python -m src.server        # SSE transport (default)
TRANSPORT=streamable-http uv run python -m src.server   # streamable-http
```
Entrypoint: `src/server.py:main`. The `web-mcp` console script is equivalent.

## Package management
- **Manager:** `uv` (lockfile: `uv.lock`). Run `uv sync` to install deps.
- No dev dependencies, no linting, no formatting, no type checking configured.
- No test suite exists.

## Architecture
- **`src/server.py`** — FastMCP server; registers all tools and the `deep_research` prompt.
- **`src/tools/web_search.py`** — DuckDuckGo search via `ddgs`. Sync call wrapped in `asyncio.to_thread`.
- **`src/tools/web_fetch.py`** — HTTP fetch + HTML→markdown. Cleans non-content tags, extracts main body.
- **`src/tools/research.py`** — ArXiv research: DDG `site:arxiv.org` search → fetch ArXiv HTML → chunk → BM25 rank. Downloads NLTK `punkt_tab` and `stopwords` corpora on first import.
- **`src/tools/current_time.py`** — Returns datetime in `Asia/Jakarta` timezone with a monthly calendar.
- **`src/utils/html.py`** — Title extraction (og:title → twitter:title → `<title>`).

## Env vars
| Var | Default | Purpose |
|---|---|---|
| `HOST` | `0.0.0.0` | Bind address |
| `PORT` | `8642` | Server port |
| `TRANSPORT` | `sse` | `sse` or `streamable-http` |

## Transport endpoints
- SSE: `http://localhost:8642/sse`
- Streamable HTTP: `http://localhost:8642/mcp`
- Health check: `http://localhost:8642/` → `{"status": "ok"}`

## Docker
Build runs streamable-http transport. Uses `uv sync --frozen --no-dev`.

## Quirks
- `research` tool uses DDG with `site:arxiv.org`, **not** the ArXiv API or `arxiv` Python package.
- `web_search` is synchronous underneath; the async wrapper is `asyncio.to_thread`.
- `__init__.py` files are empty — imports are direct path references from `server.py`.
- `current_time` timezone is hardcoded to `Asia/Jakarta`.
