"""Web search — Brave Search via headless Chromium, DDG HTTP fallback.

Why this file is the way it is:

DuckDuckGo aggressively blocks cloud-datacenter IPs (Render, Fly, AWS).
Its `/html/` endpoint returns a stub; its SPA redirects us to a
`static-pages/418.html` bot-detection page. Plain HTTP scraping and
even headless Playwright against DDG both return 0 results in
production.

Brave Search (`search.brave.com`) is tool-friendly by design, doesn't
fingerprint-block headless Chromium, and returns a clean, parseable
DOM with stable selectors. We use Playwright to render the JS SPA,
then parse with BeautifulSoup.

Strategy, in order:
    1. Try DDG HTML via plain `requests` — fast path that often works
       on a home IP during local dev.
    2. If (1) yields zero results, launch (or reuse) headless Chromium
       and query Brave Search; parse the rendered DOM.

Engineering notes:
    - Browser launched lazily and reused across calls. Cold launch
      ~2 s; warm calls ~1–1.5 s.
    - A `threading.Lock` serializes access — Playwright's sync API is
      not thread-safe.
    - Chromium args tuned for Render's 512 MB free tier:
      `--single-process`, `--disable-dev-shm-usage`, `--no-sandbox`.
    - If Playwright isn't installed locally (import fails) we silently
      skip the headless path — keeps dev install simple.
"""
from __future__ import annotations

import re
import threading
from dataclasses import dataclass
from typing import Iterable
from urllib.parse import parse_qs, quote, unquote, urlparse

import requests
from bs4 import BeautifulSoup

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)

_DDG_HTML_URL = "https://html.duckduckgo.com/html/"
_BRAVE_SEARCH_URL = "https://search.brave.com/search"

_UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)
_HTTP_HEADERS = {
    "User-Agent": _UA,
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
    "duckduckgo.com", "search.brave.com", "brave.com",
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


# ─────────────────────────── HTTP DDG (fast path) ───────────────────────────


def _parse_ddg_html(html: str, max_results: int) -> list[SearchResult]:
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


def _ddg_http_search(query: str, max_results: int) -> list[SearchResult]:
    timeout = get_settings().request_timeout
    try:
        resp = requests.post(
            _DDG_HTML_URL,
            data={"q": query, "kl": "us-en"},
            headers=_HTTP_HEADERS,
            timeout=timeout,
            allow_redirects=True,
        )
        resp.raise_for_status()
    except requests.RequestException as e:
        logger.info("DDG HTTP fetch failed: %s", e)
        return []
    return _parse_ddg_html(resp.text or "", max_results)


# ─────────────────────────── Brave via Playwright ───────────────────────────


def _parse_brave(html: str, max_results: int) -> list[SearchResult]:
    """Parse Brave Search SSR output.

    Structure:
        <div data-type="web">
            <a class="l1" href="https://...">...</a>
            <div class="title">Result title</div>
            <div class="snippet-description ... t-primary">snippet text</div>
        </div>
    """
    soup = BeautifulSoup(html, "lxml")
    results: list[SearchResult] = []
    seen: set[str] = set()

    for node in soup.select('div[data-type="web"]'):
        a = node.select_one("a.l1") or node.select_one("a[href^=http]")
        if not a or not a.get("href"):
            continue
        url = a["href"].strip()
        if not url.startswith(("http://", "https://")):
            continue
        if url in seen or is_blacklisted(url):
            continue

        title_el = node.select_one(".title")
        snippet_el = node.select_one(".t-primary") or node.select_one(".snippet-description")
        title = title_el.get_text(" ", strip=True) if title_el else a.get_text(strip=True)
        snippet = snippet_el.get_text(" ", strip=True) if snippet_el else ""

        results.append(
            SearchResult(url=url, title=title[:200], snippet=snippet[:400])
        )
        seen.add(url)
        if len(results) >= max_results:
            break
    return results


_pw_lock = threading.Lock()
_pw_ctx = None       # sync_playwright handle
_pw_browser = None   # Browser instance
_pw_unavailable = False


def _ensure_browser():
    """Return a live Chromium Browser, launching it the first time.

    Returns None if Playwright is not installed or Chromium failed to
    launch. Never raises.
    """
    global _pw_ctx, _pw_browser, _pw_unavailable
    if _pw_unavailable:
        return None
    if _pw_browser is not None:
        try:
            if _pw_browser.is_connected():
                return _pw_browser
        except Exception:
            pass
        _pw_browser = None

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        logger.warning(
            "playwright not installed; headless search disabled. "
            "Install with: pip install playwright && playwright install chromium"
        )
        _pw_unavailable = True
        return None

    try:
        if _pw_ctx is None:
            _pw_ctx = sync_playwright().start()
        _pw_browser = _pw_ctx.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
                "--single-process",
                "--no-zygote",
            ],
        )
        logger.info("Playwright Chromium launched")
        return _pw_browser
    except Exception as e:
        logger.warning("Playwright launch failed: %s", e)
        _pw_unavailable = True
        return None


def _brave_playwright_search(query: str, max_results: int) -> list[SearchResult]:
    browser = _ensure_browser()
    if browser is None:
        return []

    context = None
    try:
        context = browser.new_context(
            user_agent=_UA,
            viewport={"width": 1280, "height": 800},
            locale="en-US",
        )
        # Hide the webdriver flag to reduce bot-detection signal.
        context.add_init_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined});"
        )
        page = context.new_page()

        url = f"{_BRAVE_SEARCH_URL}?q={quote(query)}"
        page.goto(url, wait_until="domcontentloaded", timeout=25_000)

        try:
            page.wait_for_selector(
                'div[data-type="web"]', timeout=10_000, state="attached"
            )
        except Exception:
            # Try a small nudge — sometimes the SPA finishes after DOMContentLoaded.
            page.wait_for_timeout(1500)

        html = page.content()
        return _parse_brave(html, max_results)
    except Exception as e:
        logger.warning("Brave/Playwright search failed for %r: %s", query, e)
        return []
    finally:
        if context is not None:
            try:
                context.close()
            except Exception:
                pass


def shutdown_playwright():
    """Called by FastAPI shutdown event to close Chromium cleanly."""
    global _pw_ctx, _pw_browser
    try:
        if _pw_browser is not None:
            _pw_browser.close()
    except Exception:
        pass
    try:
        if _pw_ctx is not None:
            _pw_ctx.stop()
    except Exception:
        pass
    _pw_browser = None
    _pw_ctx = None


# ─────────────────────────── Public entry ───────────────────────────


def search_web(query: str, max_results: int = 6) -> list[SearchResult]:
    """Query the best available backend. Never raises."""
    if not query or not query.strip():
        return []
    q = query.strip()

    # 1. Fast HTTP path via DDG. On a home IP this often works and we
    #    skip spinning up Chromium entirely.
    results = _ddg_http_search(q, max_results)
    if results:
        logger.info("Search %r → %d results (ddg-http)", q, len(results))
        return results

    # 2. Headless-browser path via Brave. Reliable from cloud IPs.
    with _pw_lock:
        results = _brave_playwright_search(q, max_results)
    if results:
        logger.info("Search %r → %d results (brave-headless)", q, len(results))
    else:
        logger.warning("Search %r → 0 results from all backends", q)
    return results


def dedupe_urls(results: Iterable[SearchResult], seen: set[str]) -> list[SearchResult]:
    out = []
    for r in results:
        key = r.url.rstrip("/")
        if key in seen:
            continue
        seen.add(key)
        out.append(r)
    return out
