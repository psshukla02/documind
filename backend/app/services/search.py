"""Web search — DuckDuckGo with Lite + HTML fallbacks.

DDG's `html.duckduckgo.com` endpoint serves datacenter IPs (like Render's)
a stripped-down / captcha-gated page, so scraping often returns zero
results in production even though it works locally.

Strategy:
    1. Try `lite.duckduckgo.com/lite/` — a text-browser layout that is
       significantly bot-friendlier and stable across cloud IPs.
    2. Fall back to `html.duckduckgo.com/html/` if Lite yields nothing.
    3. Log the response size and head on empty results so we can tell
       "DDG gave us a different page" apart from "our parser missed".

No API key required.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Callable, Iterable
from urllib.parse import parse_qs, unquote, urlparse

import requests
from bs4 import BeautifulSoup

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)

_DDG_LITE_URL = "https://lite.duckduckgo.com/lite/"
_DDG_HTML_URL = "https://html.duckduckgo.com/html/"

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://duckduckgo.com/",
}

# Domains/extensions that either block scraping or contain no useful text.
_BLACKLIST_HOSTS = {
    "youtube.com", "www.youtube.com", "youtu.be",
    "vimeo.com", "tiktok.com",
    "x.com", "twitter.com", "mobile.twitter.com",
    "facebook.com", "www.facebook.com",
    "instagram.com", "www.instagram.com",
    "linkedin.com", "www.linkedin.com",
    "pinterest.com", "reddit.com",
    "duckduckgo.com",  # self-links from the search page itself
}
_BLACKLIST_EXT = re.compile(
    r"\.(pdf|zip|ppt|pptx|doc|docx|xls|xlsx|mp4|mp3|mov|avi)(\?|$)", re.I
)


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


def _fetch(url: str, query: str, timeout: int) -> requests.Response | None:
    """POST the query to `url`. Returns None on network failure."""
    try:
        resp = requests.post(
            url,
            data={"q": query, "kl": "us-en"},
            headers=_HEADERS,
            timeout=timeout,
            allow_redirects=True,
        )
        resp.raise_for_status()
        return resp
    except requests.RequestException as e:
        logger.warning("DDG fetch failed for %s: %s", url, e)
        return None


def _parse_lite(html: str, max_results: int) -> list[SearchResult]:
    """Parse `lite.duckduckgo.com/lite/` output.

    Structure (simplified):
        <tr><td>1.</td><td><a rel="nofollow" href="...">Title</a></td></tr>
        <tr><td></td><td class="result-snippet">snippet...</td></tr>
    """
    soup = BeautifulSoup(html, "lxml")
    results: list[SearchResult] = []
    seen: set[str] = set()

    for a in soup.find_all("a", attrs={"rel": "nofollow"}):
        href = a.get("href", "")
        url = _unwrap_ddg(href)
        if not url.startswith(("http://", "https://")):
            continue
        if url in seen or is_blacklisted(url):
            continue

        title = a.get_text(strip=True)
        if not title or len(title) < 2:
            continue

        # Snippet lives in the next <tr> sibling's td.result-snippet
        snippet = ""
        parent_tr = a.find_parent("tr")
        if parent_tr:
            nxt = parent_tr.find_next_sibling("tr")
            if nxt:
                td = nxt.find("td", class_="result-snippet") or nxt.find("td")
                if td:
                    snippet = td.get_text(" ", strip=True)

        seen.add(url)
        results.append(SearchResult(url=url, title=title, snippet=snippet))
        if len(results) >= max_results:
            break

    return results


def _parse_html(html: str, max_results: int) -> list[SearchResult]:
    """Parse the classic `html.duckduckgo.com/html/` output."""
    soup = BeautifulSoup(html, "lxml")
    results: list[SearchResult] = []
    seen: set[str] = set()

    # DDG sometimes changes the container class; try multiple selectors.
    nodes = soup.select("div.result, div.result__body, div.results_links")
    for node in nodes:
        a = node.select_one("a.result__a") or node.select_one("a[href]")
        if not a or not a.get("href"):
            continue
        url = _unwrap_ddg(a["href"])
        if not url.startswith(("http://", "https://")):
            continue
        if url in seen or is_blacklisted(url):
            continue

        snippet_node = node.select_one(".result__snippet") or node.select_one(".snippet")
        results.append(
            SearchResult(
                url=url,
                title=a.get_text(strip=True),
                snippet=snippet_node.get_text(" ", strip=True) if snippet_node else "",
            )
        )
        seen.add(url)
        if len(results) >= max_results:
            break

    return results


_BACKENDS: list[tuple[str, str, Callable[[str, int], list[SearchResult]]]] = [
    (_DDG_LITE_URL, "lite", _parse_lite),
    (_DDG_HTML_URL, "html", _parse_html),
]


def search_web(query: str, max_results: int = 6) -> list[SearchResult]:
    """Query DuckDuckGo and return clean results. Network-bound."""
    if not query or not query.strip():
        return []

    q = query.strip()
    timeout = get_settings().request_timeout

    for url, variant, parser in _BACKENDS:
        resp = _fetch(url, q, timeout)
        if resp is None:
            continue

        body = resp.text or ""
        results = parser(body, max_results)

        if results:
            logger.info("Search %r → %d results via %s", q, len(results), variant)
            return results

        # Empty result — log diagnostic info so we can tell if DDG served
        # a captcha, an empty page, or something our parser missed.
        head = body[:200].replace("\n", " ").strip()
        logger.warning(
            "DDG %s returned 0 results for %r (len=%d, status=%d, head=%r)",
            variant, q, len(body), resp.status_code, head,
        )

    return []


def dedupe_urls(results: Iterable[SearchResult], seen: set[str]) -> list[SearchResult]:
    out = []
    for r in results:
        key = r.url.rstrip("/")
        if key in seen:
            continue
        seen.add(key)
        out.append(r)
    return out
