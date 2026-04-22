"""Web search — Tavily (preferred on cloud hosts) + DuckDuckGo fallbacks.

Backends, tried in order:
    1. Tavily API — https://tavily.com — if `TAVILY_API_KEY` is set.
       Cloud-IP friendly, purpose-built for AI agents, free tier is
       1000 searches/month.
    2. DuckDuckGo Lite — `lite.duckduckgo.com/lite/`.
    3. DuckDuckGo HTML — `html.duckduckgo.com/html/`.

DDG serves datacenter IPs (e.g. Render, Fly, Vercel serverless) either a
stripped-down captcha page or a zero-result shell. Tavily works reliably
from everywhere, at the cost of requiring a free API key.

If all backends return empty, we log the response status + first bytes of
the body so the failure mode is visible from the dashboard log tail and
from the `GET /api/agent/debug-search` diagnostic endpoint.
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

_TAVILY_URL = "https://api.tavily.com/search"
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

_BLACKLIST_HOSTS = {
    "youtube.com", "www.youtube.com", "youtu.be",
    "vimeo.com", "tiktok.com",
    "x.com", "twitter.com", "mobile.twitter.com",
    "facebook.com", "www.facebook.com",
    "instagram.com", "www.instagram.com",
    "linkedin.com", "www.linkedin.com",
    "pinterest.com", "reddit.com",
    "duckduckgo.com",
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
    if href.startswith("//"):
        href = "https:" + href
    if "duckduckgo.com/l/" in href or href.startswith("/l/"):
        parsed = urlparse(href if href.startswith("http") else "https:" + href)
        qs = parse_qs(parsed.query)
        if "uddg" in qs:
            return unquote(qs["uddg"][0])
    return href


# ─────────────────────────── Tavily ───────────────────────────


def tavily_search(query: str, max_results: int = 6) -> list[SearchResult]:
    """Call Tavily Search API. Returns [] if the API key is missing or the
    request fails. Never raises — the caller will try fallbacks."""
    s = get_settings()
    if not s.tavily_api_key:
        return []
    try:
        resp = requests.post(
            _TAVILY_URL,
            json={
                "api_key": s.tavily_api_key,
                "query": query,
                "max_results": max_results,
                "search_depth": "basic",
                "include_answer": False,
            },
            timeout=s.request_timeout,
        )
        resp.raise_for_status()
    except requests.RequestException as e:
        logger.warning("Tavily search failed for %r: %s", query, e)
        return []

    try:
        data = resp.json()
    except ValueError:
        logger.warning("Tavily returned non-JSON for %r", query)
        return []

    results: list[SearchResult] = []
    seen: set[str] = set()
    for item in data.get("results", []):
        url = (item.get("url") or "").strip()
        if not url or url in seen or is_blacklisted(url):
            continue
        seen.add(url)
        results.append(
            SearchResult(
                url=url,
                title=(item.get("title") or "").strip(),
                snippet=(item.get("content") or "").strip()[:300],
            )
        )
        if len(results) >= max_results:
            break
    logger.info("Tavily %r → %d results", query, len(results))
    return results


# ─────────────────────────── DuckDuckGo ───────────────────────────


def _fetch(url: str, query: str, timeout: int) -> requests.Response | None:
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
    soup = BeautifulSoup(html, "lxml")
    results: list[SearchResult] = []
    seen: set[str] = set()

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


DDG_BACKENDS: list[tuple[str, str, Callable[[str, int], list[SearchResult]]]] = [
    (_DDG_LITE_URL, "lite", _parse_lite),
    (_DDG_HTML_URL, "html", _parse_html),
]


# ─────────────────────────── Public entry ───────────────────────────


def search_web(query: str, max_results: int = 6) -> list[SearchResult]:
    """Query the best available backend and return clean results."""
    if not query or not query.strip():
        return []

    q = query.strip()

    # 1. Tavily if configured — reliable from cloud IPs.
    results = tavily_search(q, max_results)
    if results:
        return results

    # 2. DuckDuckGo fallbacks.
    timeout = get_settings().request_timeout
    for url, variant, parser in DDG_BACKENDS:
        resp = _fetch(url, q, timeout)
        if resp is None:
            continue

        body = resp.text or ""
        results = parser(body, max_results)

        if results:
            logger.info("Search %r → %d results via ddg-%s", q, len(results), variant)
            return results

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
