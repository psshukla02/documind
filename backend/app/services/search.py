"""Web search — DuckDuckGo HTML endpoint, no API key required.

We POST to https://html.duckduckgo.com/html/ which returns static HTML
(no JS required), then parse the result list with BeautifulSoup. DDG wraps
outbound links in `/l/?uddg=<url>`; we unwrap them.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable
from urllib.parse import parse_qs, unquote, urlparse

import requests
from bs4 import BeautifulSoup

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)

_DDG_URL = "https://html.duckduckgo.com/html/"
_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml",
    "Accept-Language": "en-US,en;q=0.9",
}

# Domains/extensions that either block scraping or contain no useful text.
_BLACKLIST_HOSTS = {
    "youtube.com", "www.youtube.com", "youtu.be",
    "vimeo.com", "tiktok.com",
    "x.com", "twitter.com", "mobile.twitter.com",
    "facebook.com", "www.facebook.com",
    "instagram.com", "www.instagram.com",
    "linkedin.com", "www.linkedin.com",
    "pinterest.com", "reddit.com",  # reddit sometimes blocks; keep strict
}
_BLACKLIST_EXT = re.compile(r"\.(pdf|zip|ppt|pptx|doc|docx|xls|xlsx|mp4|mp3|mov|avi)(\?|$)", re.I)


@dataclass
class SearchResult:
    url: str
    title: str
    snippet: str


def is_blacklisted(url: str) -> bool:
    try:
        host = urlparse(url).hostname or ""
    except Exception:
        return True
    if host.lower() in _BLACKLIST_HOSTS:
        return True
    if _BLACKLIST_EXT.search(url):
        return True
    return False


def _unwrap_ddg(href: str) -> str:
    """DDG wraps outbound links — unwrap to the real target URL."""
    if href.startswith("//"):
        href = "https:" + href
    if "duckduckgo.com/l/" in href or href.startswith("/l/"):
        parsed = urlparse(href if href.startswith("http") else "https:" + href)
        qs = parse_qs(parsed.query)
        if "uddg" in qs:
            return unquote(qs["uddg"][0])
    return href


def search_web(query: str, max_results: int = 6) -> list[SearchResult]:
    """Query DuckDuckGo and return clean results. Network-bound."""
    if not query or not query.strip():
        return []

    s = get_settings()
    try:
        resp = requests.post(
            _DDG_URL,
            data={"q": query.strip(), "kl": "us-en"},
            headers=_HEADERS,
            timeout=s.request_timeout,
        )
        resp.raise_for_status()
    except requests.RequestException as e:
        logger.warning("DDG search failed for %r: %s", query, e)
        return []

    soup = BeautifulSoup(resp.text, "lxml")
    out: list[SearchResult] = []
    seen: set[str] = set()

    for node in soup.select("div.result, div.result__body"):
        a = node.select_one("a.result__a")
        if not a or not a.get("href"):
            continue
        url = _unwrap_ddg(a["href"])
        if url in seen or is_blacklisted(url):
            continue
        snippet_node = node.select_one(".result__snippet")
        out.append(
            SearchResult(
                url=url,
                title=a.get_text(strip=True),
                snippet=snippet_node.get_text(" ", strip=True) if snippet_node else "",
            )
        )
        seen.add(url)
        if len(out) >= max_results:
            break

    logger.info("Search %r → %d results", query, len(out))
    return out


def dedupe_urls(results: Iterable[SearchResult], seen: set[str]) -> list[SearchResult]:
    out = []
    for r in results:
        key = r.url.rstrip("/")
        if key in seen:
            continue
        seen.add(key)
        out.append(r)
    return out
