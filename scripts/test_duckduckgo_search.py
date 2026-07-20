#!/usr/bin/env python3
"""Standalone test for DuckDuckGo HTML + Instant API search paths."""

from __future__ import annotations

import sys
from pathlib import Path

import requests
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
load_dotenv(ROOT / ".env")

TEST_QUERY = "AAPL Apple Inc stock company"
_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)


def test_html_path() -> None:
    print("=== HTML path (html.duckduckgo.com) ===")
    try:
        from bs4 import BeautifulSoup
    except ImportError as exc:
        print(f"  bs4 import: FAIL - {exc}")
        return

    try:
        resp = requests.post(
            "https://html.duckduckgo.com/html/",
            data={"q": TEST_QUERY},
            headers={"User-Agent": _USER_AGENT},
            timeout=12,
        )
        print(f"  status: {resp.status_code}")
        soup = BeautifulSoup(resp.text, "lxml")
        blocks = soup.select(".result")
        print(f"  .result blocks: {len(blocks)}")
        if blocks:
            a = blocks[0].select_one("a.result__a")
            title = a.get_text(" ", strip=True) if a else "(no a.result__a)"
            print(f"  first title (legacy selector): {title!r}")
        else:
            # Probe alternate selectors
            for sel in (".results_links", "article[data-testid]", ".nrn-react-div"):
                alt = soup.select(sel)
                if alt:
                    print(f"  alt selector {sel!r}: {len(alt)} nodes")
            if "captcha" in resp.text.lower() or "bot" in resp.text.lower():
                print("  note: response may indicate bot/captcha block")
            print(f"  body preview (200 chars): {resp.text[:200]!r}")
    except Exception as exc:
        print(f"  exception: {type(exc).__name__}: {exc}")


def test_instant_api() -> None:
    print("=== Instant API path (api.duckduckgo.com) ===")
    try:
        resp = requests.get(
            "https://api.duckduckgo.com/",
            params={"q": TEST_QUERY, "format": "json", "no_redirect": 1},
            headers={"User-Agent": _USER_AGENT},
            timeout=10,
        )
        print(f"  status: {resp.status_code}")
        data = resp.json()
        abstract = (data.get("AbstractText") or "").strip()
        heading = (data.get("Heading") or "").strip()
        print(f"  AbstractText present: {bool(abstract)}")
        print(f"  Heading present: {bool(heading)}")
        if heading:
            print(f"  Heading: {heading!r}")
        if abstract:
            print(f"  AbstractText: {abstract[:120]!r}...")
    except Exception as exc:
        print(f"  exception: {type(exc).__name__}: {exc}")


def test_library_path() -> None:
    print("=== Library path (ddgs / duckduckgo_search) ===")
    try:
        import warnings

        try:
            from ddgs import DDGS
            pkg = "ddgs"
        except ImportError:
            from duckduckgo_search import DDGS
            pkg = "duckduckgo_search"

        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", category=RuntimeWarning)
            results = list(DDGS().text(TEST_QUERY, max_results=8))
        print(f"  package: {pkg}")
        print(f"  results: {len(results)}")
        if results:
            print(f"  first title: {results[0].get('title', '')!r}")
    except ImportError as exc:
        print(f"  ddgs not installed: {exc}")
    except Exception as exc:
        print(f"  exception: {type(exc).__name__}: {exc}")


def test_resolver() -> None:
    print("=== WebSearchResolver._search_duckduckgo ===")
    try:
        from utils.web_search_resolver import WebSearchResolver

        resolver = WebSearchResolver()
        hits = resolver._search_duckduckgo(TEST_QUERY)
        print(f"  hits: {len(hits)}")
        for i, h in enumerate(hits[:3]):
            print(f"  [{i}] title={h.get('title')!r}")
    except Exception as exc:
        print(f"  exception: {type(exc).__name__}: {exc}")


def main() -> int:
    print("DuckDuckGo search test")
    print(f"Query: {TEST_QUERY!r}")
    print("-" * 72)
    test_html_path()
    print()
    test_instant_api()
    print()
    test_library_path()
    print()
    test_resolver()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
