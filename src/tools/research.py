import asyncio
import re
from typing import List, Dict, Any, Optional

from rank_bm25 import BM25Plus
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from bs4 import BeautifulSoup

from src.tools.web_search import search as web_search

try:
    nltk.data.find("tokenizers/punkt_tab")
    nltk.data.find("corpora/stopwords")
except LookupError:
    nltk.download("punkt_tab", quiet=True)
    nltk.download("stopwords", quiet=True)

_stop_words = set(stopwords.words("english"))


def _tokenize(text: str) -> List[str]:
    try:
        return [
            w.lower()
            for w in word_tokenize(text)
            if w.lower() not in _stop_words and w.isalnum()
        ]
    except Exception:
        return [w.lower() for w in text.split() if len(w) > 2]


def chunk_text(text: str, chunk_size: int = 1500, overlap: int = 200) -> List[str]:
    paragraphs = re.split(r"\n\n+", text.strip())
    chunks: List[str] = []
    current = ""
    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
        if len(current) + len(para) > chunk_size and current:
            chunks.append(current.strip())
            current = para[:overlap] if overlap and len(para) > overlap else ""
        else:
            current = (current + "\n\n" + para).strip()
    if current.strip():
        chunks.append(current.strip())
    return chunks if chunks else [text[:chunk_size]]


def _to_arxiv_html_url(url: str) -> str:
    return url.replace("/abs/", "/html/").replace("/pdf/", "/html/")


def _is_arxiv_url(url: str) -> bool:
    return "arxiv.org" in url.lower()


def _dedup_arxiv_results(results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    seen: Dict[str, Dict[str, Any]] = {}
    for r in results:
        url = r.get("url", "")
        key = _to_arxiv_html_url(url)
        if key not in seen:
            seen[key] = r
    return list(seen.values())


async def _fetch_arxiv_html(url: str) -> Optional[str]:
    import httpx

    html_url = _to_arxiv_html_url(url)
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=30.0) as client:
            resp = await client.get(html_url, headers=headers)
            resp.raise_for_status()
    except Exception:
        return None

    soup = BeautifulSoup(resp.text, "html.parser")

    parts: List[str] = []

    title_tags = soup.select(".ltx_title")
    for t in title_tags:
        text = t.get_text(strip=True)
        if text:
            parts.append(f"# {text}")

    abstract_tags = soup.select(".ltx_abstract")
    for a in abstract_tags:
        text = a.get_text(strip=True)
        if text:
            parts.append(f"## Abstract\n\n{text}")

    section_tags = soup.select(".ltx_section")
    for s in section_tags:
        sec_title = s.select_one(".ltx_title")
        title_text = sec_title.get_text(strip=True) if sec_title else "Section"
        body_text = s.get_text(strip=True)
        if body_text:
            parts.append(f"## {title_text}\n\n{body_text}")

    toc_tags = soup.select(".ltx_toclist")
    for t in toc_tags:
        text = t.get_text(strip=True)
        if text:
            parts.append(f"## Table of Contents\n\n{text}")

    bib_tags = soup.select(".ltx_bibliography")
    for b in bib_tags:
        text = b.get_text(strip=True)
        if text:
            parts.append(f"## Bibliography\n\n{text}")

    appendix_tags = soup.select(".ltx_appendix")
    for a in appendix_tags:
        text = a.get_text(strip=True)
        if text:
            parts.append(f"## Appendix\n\n{text}")

    if parts:
        return "\n\n".join(parts)

    fallback = soup.get_text(strip=True)
    return fallback if fallback else None


async def research(
    query: str,
    max_search_results: int = 15,
    max_papers: int = 3,
    max_chunks: int = 15,
    chunk_size: int = 3000,
) -> Dict[str, Any]:
    """Research ArXiv papers: search arxiv.org, fetch paper HTML, chunk content, and return the most relevant chunks ranked by BM25.

    Args:
        query: The research query.
        max_search_results: Number of ArXiv search results to consider.
        max_papers: Number of papers to fetch and analyze.
        max_chunks: Number of top relevant chunks to return.
        chunk_size: Approximate size of each content chunk in characters.
    """
    # Step 1: Search ArXiv via DDG with site:arxiv.org
    search_results = web_search(
        f"{query} site:arxiv.org", max_results=max_search_results
    )
    if not search_results:
        return {
            "query": query,
            "sources": [],
            "chunks": [],
            "summary": "No ArXiv search results found.",
        }

    # Step 2: Filter to arxiv.org URLs only and deduplicate
    arxiv_results = [r for r in search_results if _is_arxiv_url(r.get("url", ""))]
    arxiv_results = _dedup_arxiv_results(arxiv_results)

    if not arxiv_results:
        return {
            "query": query,
            "sources": [{"title": r["title"], "url": r["url"]} for r in search_results],
            "chunks": [],
            "summary": "No ArXiv papers found in search results.",
        }

    # Step 3: Fetch ArXiv paper HTML content concurrently
    papers_to_fetch = arxiv_results[:max_papers]
    fetch_tasks = [_fetch_arxiv_html(r["url"]) for r in papers_to_fetch]
    contents = await asyncio.gather(*fetch_tasks, return_exceptions=True)

    papers: List[Dict[str, Any]] = []
    for i, content in enumerate(contents):
        if isinstance(content, Exception) or not content:
            continue
        papers.append(
            {
                "title": papers_to_fetch[i]["title"],
                "url": papers_to_fetch[i]["url"],
                "html_url": _to_arxiv_html_url(papers_to_fetch[i]["url"]),
                "abstract": papers_to_fetch[i].get("description", ""),
                "content": content,
            }
        )

    if not papers:
        return {
            "query": query,
            "sources": [{"title": r["title"], "url": r["url"]} for r in arxiv_results],
            "chunks": [],
            "summary": "Failed to fetch content from any ArXiv papers.",
        }

    # Step 4: Chunk all paper content
    all_chunks: List[Dict[str, Any]] = []
    for paper in papers:
        chunks = chunk_text(paper["content"], chunk_size=chunk_size)
        for idx, chunk in enumerate(chunks):
            all_chunks.append(
                {
                    "content": chunk,
                    "source_title": paper["title"],
                    "source_url": paper["url"],
                    "source_html_url": paper["html_url"],
                    "chunk_index": idx,
                }
            )

    if not all_chunks:
        return {
            "query": query,
            "sources": [{"title": p["title"], "url": p["url"]} for p in papers],
            "chunks": [],
            "summary": "No content chunks extracted from papers.",
        }

    # Step 5: BM25 ranking against query
    corpus = [_tokenize(c["content"]) for c in all_chunks]
    query_tokens = _tokenize(query)

    if not query_tokens or not any(corpus):
        top_chunks = all_chunks[:max_chunks]
    else:
        bm25 = BM25Plus(corpus)
        scores = bm25.get_scores(query_tokens)
        scored = sorted(enumerate(scores), key=lambda x: x[1], reverse=True)
        top_chunks = [all_chunks[i] for i, _ in scored[:max_chunks]]

    # Step 6: Build response
    sources = [
        {
            "title": p["title"],
            "url": p["url"],
            "abstract": p.get("abstract", ""),
        }
        for p in papers
    ]

    result_chunks = []
    for chunk in top_chunks:
        result_chunks.append(
            {
                "content": chunk["content"],
                "source": chunk["source_title"],
                "url": chunk["source_url"],
            }
        )

    return {
        "query": query,
        "sources": sources,
        "chunks": result_chunks,
        "total_chunks_analyzed": len(all_chunks),
    }
