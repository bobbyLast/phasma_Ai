#!/usr/bin/env python3
"""Standalone test harness for Brave Search API subscription keys."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

import requests
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")

TEST_QUERY = "AAPL Apple Inc stock company"
PREVIEW_CHARS = 500
REQUEST_TIMEOUT = 30

COMMON_HEADERS = {
    "Accept": "application/json",
    "Accept-Encoding": "gzip",
}


def _truncate(text: str, limit: int = PREVIEW_CHARS) -> str:
    text = text.strip()
    if len(text) <= limit:
        return text
    return text[: limit - 3] + "..."


def _preview_web(data: Dict[str, Any]) -> str:
    results = (data.get("web") or {}).get("results") or []
    if not results:
        return _truncate(json.dumps(data, indent=2, default=str))
    lines: List[str] = []
    for i, item in enumerate(results[:3], start=1):
        title = item.get("title") or "(no title)"
        url = item.get("url") or ""
        desc = (item.get("description") or "")[:120]
        lines.append(f"{i}. {title}\n   {url}\n   {desc}")
    return _truncate("\n".join(lines))


def _preview_llm_context(data: Dict[str, Any]) -> str:
    generic = (data.get("grounding") or {}).get("generic") or []
    if not generic:
        return _truncate(json.dumps(data, indent=2, default=str))
    lines: List[str] = []
    for i, item in enumerate(generic[:3], start=1):
        title = item.get("title") or "(no title)"
        url = item.get("url") or ""
        snippets = item.get("snippets") or []
        snippet = (snippets[0] if snippets else "")[:120]
        lines.append(f"{i}. {title}\n   {url}\n   {snippet}")
    return _truncate("\n".join(lines))


def _preview_suggest_or_spell(data: Dict[str, Any]) -> str:
    results = data.get("results") or []
    if not results:
        original = (data.get("query") or {}).get("original", TEST_QUERY)
        return f"(no suggestions; query accepted as-is: {original!r})"
    lines = [f"{i}. {r.get('query', r)}" for i, r in enumerate(results[:3], start=1)]
    return _truncate("\n".join(lines))


def _call_get(url: str, key: str, params: Dict[str, Any]) -> requests.Response:
    return requests.get(
        url,
        params=params,
        headers={**COMMON_HEADERS, "X-Subscription-Token": key},
        timeout=REQUEST_TIMEOUT,
    )


PLANS: List[Dict[str, Any]] = [
    {
        "plan": "Free (Web Search) - 2000 req/mo",
        "env": "BRAVE_SEARCH_API_KEY",
        "url": "https://api.search.brave.com/res/v1/web/search",
        "params": {"q": TEST_QUERY, "count": 3},
        "preview": _preview_web,
    },
    {
        "plan": "Free AI (LLM Context)",
        "env": "BRAVE_AI_API_KEY",
        "url": "https://api.search.brave.com/res/v1/llm/context",
        "params": {
            "q": TEST_QUERY,
            "count": 5,
            "maximum_number_of_tokens": 2048,
            "maximum_number_of_urls": 3,
        },
        "preview": _preview_llm_context,
    },
    {
        "plan": "Free Autosuggest",
        "env": "BRAVE_AUTOSUGGEST_API_KEY",
        "url": "https://api.search.brave.com/res/v1/suggest/search",
        "params": {"q": TEST_QUERY, "country": "US", "count": 5},
        "preview": _preview_suggest_or_spell,
    },
    {
        "plan": "Free Spellcheck",
        "env": "BRAVE_SPELLCHECK_API_KEY",
        "url": "https://api.search.brave.com/res/v1/spellcheck/search",
        "params": {"q": TEST_QUERY, "country": "US"},
        "preview": _preview_suggest_or_spell,
    },
]


def run_plan(spec: Dict[str, Any]) -> bool:
    plan = spec["plan"]
    env_name = spec["env"]
    url = spec["url"]
    preview_fn: Callable[[Dict[str, Any]], str] = spec["preview"]

    print()
    print("=" * 72)
    print(plan)
    print(f"  Env:      {env_name}")
    print(f"  Endpoint: {url}")
    print(f"  Query:    {TEST_QUERY!r}")
    print("-" * 72)

    key = os.getenv(env_name, "").strip()
    if not key:
        print(f"  SKIP: {env_name} is not set in .env")
        return False

    print("  Key:      configured")

    try:
        resp = _call_get(url, key, spec["params"])
    except requests.RequestException as exc:
        print(f"  Status:   request failed - {exc}")
        return False

    print(f"  Status:   {resp.status_code}")

    body_preview = ""
    try:
        data = resp.json()
        if resp.ok:
            body_preview = preview_fn(data)
        else:
            body_preview = _truncate(json.dumps(data, indent=2, default=str))
    except ValueError:
        body_preview = _truncate(resp.text)

    if body_preview:
        print("  Preview:")
        for line in body_preview.splitlines():
            print(f"    {line}")

    if not resp.ok:
        print(f"  Note:     HTTP {resp.status_code} - check key/plan matches this endpoint")

    return resp.ok


def main() -> int:
    print("Brave Search API - subscription key test")
    print(f"Project root: {ROOT}")
    print(f"Test query:   {TEST_QUERY!r}")

    configured = [s["env"] for s in PLANS if os.getenv(s["env"], "").strip()]
    missing = [s["env"] for s in PLANS if not os.getenv(s["env"], "").strip()]
    print(f"Keys set:     {', '.join(configured) if configured else '(none)'}")
    if missing:
        print(f"Keys missing: {', '.join(missing)}")

    if not configured:
        print("\nNo Brave API keys found. Add keys to .env - see .env.example")
        return 1

    ok_count = sum(1 for spec in PLANS if run_plan(spec))
    ran = len(configured)
    print()
    print("=" * 72)
    print(f"Done: {ok_count}/{ran} configured endpoint(s) returned HTTP 2xx")
    return 0 if ok_count == ran else 1


if __name__ == "__main__":
    sys.exit(main())
