"""Web search — Brave Search via headless Chromium, DDG HTTP fallback.

Why this file is the way it is:

DuckDuckGo aggressively blocks cloud-datacenter IPs. `/html/` returns
a stub; the SPA redirects to a `static-pages/418.html` bot page; even
Playwright doesn't get through. Brave Search (`search.brave.com`) is
tool-friendly and returns a clean parseable SPA when driven by
Playwright.

Concurrency is the subtle part. Playwright's SYNC API is locked to the
thread that called `sync_playwright().start()` — touching it from any
other thread raises "cannot switch to a different thread (which happens
to have exited)". FastAPI/Starlette dispatches sync routes on a thread
pool whose workers come and go, so a naive `global browser` breaks on
the second request.

Solution: a dedicated **worker thread** owns Playwright for the life
of the process. Request threads submit `Job`s to an inbound queue and
block on a per-job reply queue. The browser never crosses threads.

Strategy:
    1. Fast path: plain HTTP to DDG `/html/` (works from home IPs).
    2. On zero results, hand the query to the Playwright worker
       thread, which opens a new browser context per job on Brave.

Engineering notes:
    - Worker thread is daemon=True; it dies with the process.
    - If the worker thread dies or errors at startup, `_ensure_worker`
      restarts it on the next request.
    - Chromium args tuned for Render's 512 MB free tier.
    - If Playwright isn't installed (local dev without install), the
      headless path silently returns [] — tests and local dev are
      unaffected.
"""
from __future__ import annotations

import queue
import re
import threading
from dataclasses import dataclass
from typing import Iterable, Any
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
    if href.startswith("//"):
        href = "https:" + href
    if "duckduckgo.com/l/" in href or href.startswith("/l/"):
        parsed = urlparse(href if href.startswith("http") else "https:" + href)
        qs = parse_qs(parsed.query)
        if "uddg" in qs:
            return unquote(qs["uddg"][0])
    return href


# ─────────────────────────── HTML parsers ───────────────────────────


def _parse_ddg_html(html: str, max_results: int) -> list[SearchResult]:
    soup = BeautifulSoup(html, "lxml")
    results: list[SearchResult] = []
    seen: set[str] = set()

    for node in soup.select("div.result, div.result__body, div.results_links"):
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


def _parse_brave(html: str, max_results: int) -> list[SearchResult]:
    """Parse Brave Search SSR output.

    Structure:
        <div data-type="web">
            <a class="l1" href="https://...">...</a>
            <div class="title">Result title</div>
            <div class="... t-primary">snippet text</div>
        </div>
    """
    # Detect Brave's anti-bot PoW CAPTCHA page early and bail cleanly.
    # The title is literally "PoW Captcha - Brave Search".
    if "<title>PoW Captcha" in html or "PoW Captcha - Brave Search" in html:
        logger.warning(
            "Brave returned a PoW CAPTCHA — this IP has been flagged. "
            "Typical recovery: 5–15 minutes of no requests. On Render, "
            "try again later or switch to a keyed search API."
        )
        return []

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
        snippet_el = (
            node.select_one(".t-primary")
            or node.select_one(".snippet-description")
        )
        title = title_el.get_text(" ", strip=True) if title_el else a.get_text(strip=True)
        snippet = snippet_el.get_text(" ", strip=True) if snippet_el else ""

        results.append(SearchResult(url=url, title=title[:200], snippet=snippet[:400]))
        seen.add(url)
        if len(results) >= max_results:
            break
    return results


# ─────────────────────────── HTTP (fast path) ───────────────────────────


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


# ─────────────────────────── Playwright worker thread ───────────────────────────
#
# One thread owns Playwright and a persistent browser for the lifetime
# of the process. Requests submit jobs to `_in_queue`; the worker replies
# on a per-job `queue.Queue(maxsize=1)`.

_SHUTDOWN = object()

_in_queue: "queue.Queue[Any]" = queue.Queue()
_worker_lock = threading.Lock()
_worker_thread: threading.Thread | None = None
_worker_ready = threading.Event()
_worker_fatal: Exception | None = None


def _worker_loop() -> None:
    """Body of the dedicated Playwright thread."""
    global _worker_fatal

    browser = None
    pw_ctx = None
    context = None
    page = None
    last_query_ts = 0.0

    # Import and launch inside this thread — sync Playwright pins to
    # whichever thread calls .start().
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as e:
        _worker_fatal = e
        logger.warning("Playwright not installed; headless search disabled")
        _worker_ready.set()
        return

    try:
        pw_ctx = sync_playwright().start()
        # NOTE: `--single-process` / `--no-zygote` save memory but make
        # Chromium crash when a page/context closes (the browser process
        # itself dies). Trading those for stability — ~200 MB multi-
        # process instead of ~120 MB single-process is still fine on
        # Render's 512 MB tier with FAISS + uvicorn.
        browser = pw_ctx.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
                "--disable-extensions",
                "--disable-background-networking",
                "--disable-renderer-backgrounding",
            ],
        )
        # A SINGLE persistent browser context + page, reused for every
        # query. Brave's rate-limit keys off "this looks like a bunch
        # of freshly-minted anonymous users" — same context means
        # same cookies + same session, avoiding that heuristic.
        context = browser.new_context(
            user_agent=_UA,
            viewport={"width": 1280, "height": 800},
            locale="en-US",
        )
        context.add_init_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined});"
        )
        page = context.new_page()
        logger.info("Playwright worker thread ready (Chromium launched)")
    except Exception as e:
        _worker_fatal = e
        logger.warning("Playwright worker failed to launch Chromium: %s", e)
        _worker_ready.set()
        try:
            if context is not None:
                context.close()
        except Exception:
            pass
        try:
            if browser is not None:
                browser.close()
        except Exception:
            pass
        if pw_ctx is not None:
            try:
                pw_ctx.stop()
            except Exception:
                pass
        return

    _worker_ready.set()

    try:
        while True:
            msg = _in_queue.get()
            if msg is _SHUTDOWN:
                break
            query, max_results, reply = msg
            try:
                # Gentle throttle: keep successive queries ≥ 700 ms apart
                # to avoid Brave's "too-many-rapid-anonymous-hits" filter.
                import time
                gap = time.time() - last_query_ts
                if gap < 0.7:
                    time.sleep(0.7 - gap)
                results = _do_brave_search(page, query, max_results)
                last_query_ts = time.time()
                reply.put(("ok", results))
            except Exception as e:
                logger.warning("Brave search error for %r: %s", query, e)
                reply.put(("err", e))
    finally:
        try:
            if context is not None:
                context.close()
        except Exception:
            pass
        try:
            if browser is not None:
                browser.close()
        except Exception:
            pass
        try:
            if pw_ctx is not None:
                pw_ctx.stop()
        except Exception:
            pass
        logger.info("Playwright worker thread exited")


def _ensure_worker() -> bool:
    """Start the worker thread if needed. Returns True iff the worker is
    ready and Chromium launched."""
    global _worker_thread, _worker_fatal
    with _worker_lock:
        if _worker_thread is not None and _worker_thread.is_alive():
            return _worker_fatal is None
        _worker_ready.clear()
        _worker_fatal = None
        _worker_thread = threading.Thread(
            target=_worker_loop, daemon=True, name="playwright-worker"
        )
        _worker_thread.start()

    # Wait for the worker to finish launching (or fail).
    _worker_ready.wait(timeout=30)
    return _worker_fatal is None


def _do_brave_search(page, query: str, max_results: int) -> list[SearchResult]:
    """Runs ON the worker thread only. Uses the persistent page.

    Receives the shared `page` from the worker — does NOT create a new
    context, so cookies and session state persist across calls. This
    significantly reduces Brave's bot-detection rate.
    """
    url = f"{_BRAVE_SEARCH_URL}?q={quote(query)}"
    page.goto(url, wait_until="domcontentloaded", timeout=25_000)

    try:
        page.wait_for_selector(
            'div[data-type="web"]', timeout=10_000, state="attached"
        )
    except Exception:
        page.wait_for_timeout(1200)

    html = page.content()
    return _parse_brave(html, max_results)


def _brave_worker_search(query: str, max_results: int) -> list[SearchResult]:
    """Public sync wrapper: any thread can call this."""
    if not _ensure_worker():
        return []

    reply: "queue.Queue[tuple[str, Any]]" = queue.Queue(maxsize=1)
    _in_queue.put((query, max_results, reply))

    try:
        status, payload = reply.get(timeout=45)
    except queue.Empty:
        logger.warning("Playwright worker timed out on %r", query)
        return []
    return payload if status == "ok" else []


def shutdown_playwright() -> None:
    """FastAPI shutdown hook — asks the worker to exit cleanly."""
    global _worker_thread
    with _worker_lock:
        t = _worker_thread
        _worker_thread = None
    if t is not None and t.is_alive():
        _in_queue.put(_SHUTDOWN)
        t.join(timeout=5)


# ─────────────────────────── Public entry ───────────────────────────


def search_web(query: str, max_results: int = 6) -> list[SearchResult]:
    """Query the best available backend. Never raises."""
    if not query or not query.strip():
        return []
    q = query.strip()

    # 1. Fast HTTP path via DDG (works on a home IP; skips Chromium).
    results = _ddg_http_search(q, max_results)
    if results:
        logger.info("Search %r → %d results (ddg-http)", q, len(results))
        return results

    # 2. Headless Brave via the dedicated worker thread.
    results = _brave_worker_search(q, max_results)
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
