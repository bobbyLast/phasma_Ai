#!/usr/bin/env python3
"""Standalone test for SearXNG JSON search (company lookup)."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from urllib.parse import urljoin

import requests
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")

TEST_QUERY = "AAPL Apple Inc"
REQUEST_TIMEOUT = 30
_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)


def _search_endpoint(base: str) -> str:
    return urljoin(base.rstrip("/") + "/", "search")


def main() -> int:
    print("SearXNG JSON search - Phasma company lookup test")
    print(f"Project root: {ROOT}")
    print(f"Query:        {TEST_QUERY!r}")
    print("-" * 72)

    base = os.getenv("SEARXNG_URL", "").strip()
    if not base:
        print("FAIL: SEARXNG_URL is not set in .env")
        print()
        print("Setup:")
        print("  1. Open https://searx.space and pick an instance with JSON enabled.")
        print("  2. Set SEARXNG_URL to the instance base URL (no /search path).")
        print("     Example: SEARXNG_URL=https://searx.example.org")
        print("  3. Add searxng to WEB_SEARCH_PROVIDERS if not already present.")
        print("  4. Re-run: python scripts/test_searxng_search.py")
        return 1

    endpoint = _search_endpoint(base)
    print(f"SEARXNG_URL:  configured ({base.rstrip('/')})")
    print(f"Endpoint:     GET {endpoint}")
    print("Params:       q, format=json, categories=general")
    print("-" * 72)

    try:
        resp = requests.get(
            endpoint,
            params={"q": TEST_QUERY, "format": "json", "categories": "general"},
            headers={"User-Agent": _USER_AGENT},
            timeout=REQUEST_TIMEOUT,
        )
    except requests.RequestException as exc:
        print(f"Status:   request failed - {exc}")
        return 1

    print(f"Status:   {resp.status_code}")

    try:
        data = resp.json()
    except ValueError:
        print(f"FAIL: non-JSON response (first 200 chars): {resp.text[:200]!r}")
        return 1

    if not resp.ok:
        detail = data if isinstance(data, dict) else {"body": str(data)[:400]}
        print(f"FAIL: HTTP {resp.status_code}")
        print(json.dumps(detail, indent=2)[:500])
        return 1

    results = data.get("results") or []
    if not results:
        print("FAIL: HTTP 200 but no results (instance may block JSON or rate-limit)")
        return 1

    print("OK: SearXNG returned results")
    print("Top titles:")
    for i, item in enumerate(results[:3], start=1):
        title = (item.get("title") or "(no title)").strip()
        snippet = (item.get("content") or item.get("snippet") or "").strip()
        if len(snippet) > 120:
            snippet = snippet[:117] + "..."
        print(f"  {i}. {title}")
        if snippet:
            print(f"     {snippet}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
