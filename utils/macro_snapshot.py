"""Macro release snapshots — FRED-first with honest failure logging."""

from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import requests

logger = logging.getLogger(__name__)

# Core series for regime / surprise (vintage-aware when ALFRED available)
_CORE_SERIES = (
    ("CPIAUCSL", "cpi", "CPI"),
    ("UNRATE", "unemployment", "Unemployment Rate"),
    ("PAYEMS", "payrolls", "Nonfarm Payrolls"),
    ("DFF", "fed_funds", "Fed Funds Rate"),
    ("T10Y2Y", "yield_curve", "10Y-2Y Spread"),
    ("VIXCLS", "vix", "VIX"),
    ("DTWEXBGS", "dollar", "Trade Weighted Dollar"),
    ("DCOILWTICO", "oil", "WTI Oil"),
)


def fetch_macro_snapshot(api_key: Optional[str] = None) -> List[Dict[str, Any]]:
    """Pull latest FRED observations. Returns empty list on missing key/failure."""
    key = api_key or os.getenv("FRED_API_KEY") or os.getenv("FRED_KEY")
    events: List[Dict[str, Any]] = []
    if not key:
        logger.warning("MACRO_SKIP: no FRED_API_KEY configured")
        return events

    now = datetime.now(timezone.utc).isoformat()
    for series_id, event_type, label in _CORE_SERIES:
        try:
            resp = requests.get(
                "https://api.stlouisfed.org/fred/series/observations",
                params={
                    "series_id": series_id,
                    "api_key": key,
                    "file_type": "json",
                    "sort_order": "desc",
                    "limit": 3,
                },
                timeout=12,
            )
            if resp.status_code != 200:
                logger.warning("FRED %s status %s", series_id, resp.status_code)
                continue
            obs = (resp.json().get("observations") or [])
            if not obs:
                continue
            latest = obs[0]
            prev = obs[1] if len(obs) > 1 else None
            try:
                actual = float(latest.get("value"))
            except (TypeError, ValueError):
                continue
            previous = None
            if prev:
                try:
                    previous = float(prev.get("value"))
                except (TypeError, ValueError):
                    previous = None
            surprise = None
            if previous is not None:
                surprise = actual - previous
            events.append({
                "title": f"{label}: {actual}",
                "source": "FRED",
                "symbol": "",
                "timestamp": latest.get("date") or now,
                "summary": f"{label} ({series_id}) latest={actual} previous={previous}",
                "event_type": event_type,
                "source_tier": 1,
                "actual": actual,
                "previous": previous,
                "consensus": None,
                "surprise": surprise,
                "series_id": series_id,
                "vintage_note": "FRED latest release; ALFRED vintage recommended for backtests",
            })
        except Exception as exc:
            logger.error("MACRO_FETCH_FAILED %s: %s", series_id, exc)
            print(f"ERROR MACRO_FETCH_FAILED {series_id}: {exc}")
    return events
