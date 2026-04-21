"""HTML scraping and cleanup.

Kept intentionally simple: requests + BeautifulSoup. Strips scripts, styles,
nav/footer/aside, and returns (title, clean_text). Safe to use for public
docs sites; respects basic timeout.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

import requests
from bs4 import BeautifulSoup

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (compatible; AI-Doc-Assistant/1.0; +https://example.com/bot)"
    )
}

_JUNK_TAGS = ("script", "style", "noscript", "iframe", "svg", "nav", "footer", "aside", "form")


@dataclass
class ScrapedPage:
    url: str
    title: str
    text: str


def scrape_url(url: str) -> ScrapedPage:
    s = get_settings()
    try:
        resp = requests.get(url, headers=_HEADERS, timeout=s.request_timeout)
        resp.raise_for_status()
    except requests.RequestException as e:
        raise ValueError(f"Failed to fetch {url}: {e}") from e

    soup = BeautifulSoup(resp.text, "lxml")

    for tag_name in _JUNK_TAGS:
        for tag in soup.find_all(tag_name):
            tag.decompose()

    title = (soup.title.string.strip() if soup.title and soup.title.string else url)

    main = soup.find("main") or soup.find("article") or soup.body or soup
    raw = main.get_text("\n", strip=True)

    text = re.sub(r"\n{3,}", "\n\n", raw)
    text = re.sub(r"[ \t]{2,}", " ", text).strip()

    if len(text) < 40:
        raise ValueError(f"No meaningful content extracted from {url}")

    logger.info("Scraped %s (%d chars)", url, len(text))
    return ScrapedPage(url=url, title=title, text=text)
