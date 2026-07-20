#!/usr/bin/env python3
"""Standalone test for Google Custom Search (company lookup)."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import requests
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")

TEST_QUERY = "AAPL Apple Inc stock company"
ENDPOINT = "https://www.googleapis.com/customsearch/v1"
REQUEST_TIMEOUT = 30


def _api_error_message(data: dict) -> str:
    err = data.get("error") or {}
    if isinstance(err, dict):
        msg = err.get("message") or ""
        code = err.get("code")
        status = err.get("status") or ""
        reasons = []
        for d in err.get("errors") or []:
            if isinstance(d, dict) and d.get("reason"):
                reasons.append(str(d["reason"]))
        parts = [p for p in (status, str(code) if code is not None else "", msg) if p]
        if reasons:
            parts.append("reasons=" + ", ".join(reasons))
        return " | ".join(parts) if parts else json.dumps(err)[:400]
    return str(err)[:400]


def main() -> int:
    print("Google Custom Search API - Phasma company lookup test")
    print(f"Project root: {ROOT}")
    print(f"Endpoint:     {ENDPOINT}")
    print(f"Query:        {TEST_QUERY!r}")
    print("-" * 72)

    api_key = os.getenv("GOOGLE_API_KEY", "").strip()
    cse_id = os.getenv("GOOGLE_CSE_ID", "").strip()

    if not api_key:
        print("FAIL: GOOGLE_API_KEY is not set in .env")
        return 1
    if not cse_id:
        print("FAIL: GOOGLE_CSE_ID is not set in .env")
        return 1

    print("GOOGLE_API_KEY:  configured")
    print("GOOGLE_CSE_ID:   configured")

    try:
        resp = requests.get(
            ENDPOINT,
            params={"key": api_key, "cx": cse_id, "q": TEST_QUERY, "num": 8},
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
        print(f"FAIL: {_api_error_message(data)}")
        err = data.get("error")
        if isinstance(err, dict):
            diag = {k: err.get(k) for k in ("code", "message", "status", "errors", "details") if k in err}
            if diag:
                print("error payload:", json.dumps(diag, indent=2))
        return 1

    items = data.get("items") or []
    if not items:
        print("FAIL: HTTP 200 but no items in response (check CSE scope / query)")
        return 1

    print("OK: Google CSE returned results")
    print("Top titles:")
    for i, item in enumerate(items[:3], start=1):
        title = (item.get("title") or "(no title)").strip()
        snippet = (item.get("snippet") or "").strip()
        if len(snippet) > 120:
            snippet = snippet[:117] + "..."
        print(f"  {i}. {title}")
        if snippet:
            print(f"     {snippet}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
