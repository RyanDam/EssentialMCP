import re

from bs4 import BeautifulSoup, Tag
import httpx
import markdownify

from src.utils.html import extract_title


def _fix_lazy_images(tag: Tag) -> None:
    """Replace lazy-loaded placeholder src with the real image URL."""
    placeholder = "R0lGODlhAQABAAAAACH5BAEKAAEALAAAAAABAAEAAAICTAEAOw=="
    lazy_attrs = ("data-src", "data-lazy-src", "data-original", "data-real-src",
                  "data-echo-src", "data-lazy-srcset")

    for img in tag.find_all("img"):
        src = img.get("src", "")
        if src.startswith("data:image") and placeholder in src:
            for attr in lazy_attrs:
                real = img.get(attr)
                if real:
                    img["src"] = real
                    break
            else:
                for attr, val in img.attrs.items():
                    if attr.startswith("data") and ("src" in attr or "img" in attr):
                        if not str(val).startswith("data:image"):
                            img["src"] = val
                            break


def _clean_soup(soup: BeautifulSoup) -> Tag:
    """Remove non-content elements and return the main content tag."""
    for tag_name in ("script", "style", "noscript", "link", "meta", "svg", "head"):
        for el in soup.find_all(tag_name):
            el.decompose()

    for tag_name in ("nav", "footer", "header", "aside", "form", "iframe"):
        for el in soup.find_all(tag_name):
            el.decompose()

    body = soup.find("body") or soup

    content = None
    for sel in ("article", "main", '[role="main"]', "#content", "#main",
                ".article-body", ".post-content", ".entry-content", ".story-body",
                ".content-body", "#article-body", ".article__body"):
        content = body.select_one(sel)
        if content:
            break

    if content:
        _fix_lazy_images(content)
        return content

    for el in body.find_all(True):
        text_len = len(el.get_text(strip=True))
        child_text = sum(len(c.get_text(strip=True)) for c in el.find_all(True, recursive=False))
        if text_len > 100 and child_text > text_len * 0.6 and el.name not in ("a", "script", "style"):
            _fix_lazy_images(el)
            return el

    return body


async def fetch(url: str, max_length: int = -1) -> dict:
    """Fetch a URL and return content as markdown."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    async with httpx.AsyncClient(follow_redirects=True, timeout=30.0) as client:
        response = await client.get(url, headers=headers)
        response.raise_for_status()

        content_type = response.headers.get("content-type", "")

        if "text/html" not in content_type:
            text = response.text
            if max_length > 0:
                text = text[:max_length]
            return {
                "content": text,
                "title": url,
                "url": url,
                "content_type": content_type,
            }

        title = extract_title(response.text)
        soup = BeautifulSoup(response.text, "html.parser")
        content = _clean_soup(soup)

        md = markdownify.markdownify(str(content), heading_style="ATX", bullets="-")
        md = re.sub(r"\n{3,}", "\n\n", md)
        md = md.strip()

        if max_length > 0 and len(md) > max_length:
            md = md[:max_length] + "\n\n... (truncated)"

        return {
            "content": md,
            "title": title,
            "url": url,
            "content_type": "text/html",
        }
