"""SEC filings worker helpers — Form 4 + 8-K / 6-K / S-3 / 13D/G via EDGAR current."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List

import requests

logger = logging.getLogger(__name__)

_SEC_HEADERS = {
    "User-Agent": "Phasma-AI/1.0 (research@example.com)",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

_FILING_TYPES = ("4", "8-K", "6-K", "S-3", "SC 13D", "SC 13G", "13D", "13G")


def fetch_recent_sec_filings(limit_per_type: int = 8) -> List[Dict[str, Any]]:
    """Incremental pull of recent EDGAR filings by type (HTML browse feed)."""
    events: List[Dict[str, Any]] = []
    for form in _FILING_TYPES:
        try:
            url = (
                "https://www.sec.gov/cgi-bin/browse-edgar"
                f"?action=getcurrent&type={form.replace(' ', '+')}&company="
                "&dateb=&owner=include&count=10&output=atom"
            )
            resp = requests.get(url, headers=_SEC_HEADERS, timeout=12)
            if resp.status_code != 200:
                logger.warning("SEC feed %s status %s", form, resp.status_code)
                continue
            text = resp.text
            # Lightweight atom entry scrape
            chunks = text.split("<entry>")[1 : limit_per_type + 1]
            for chunk in chunks:
                title = _between(chunk, "<title>", "</title>") or f"SEC {form}"
                link = _between(chunk, 'href="', '"') or ""
                updated = _between(chunk, "<updated>", "</updated>") or datetime.now(timezone.utc).isoformat()
                events.append({
                    "title": title.strip(),
                    "source": "SEC EDGAR",
                    "filing_type": form,
                    "symbol": "",
                    "timestamp": updated,
                    "url": link,
                    "summary": f"SEC {form} filing",
                    "event_type": _map_form_event(form),
                    "source_tier": 1,
                    "prediction_market": None,
                })
        except Exception as exc:
            logger.error("SEC_FETCH_FAILED type=%s: %s", form, exc)
            print(f"ERROR SEC_FETCH_FAILED type={form}: {exc}")
    return events


def _map_form_event(form: str) -> str:
    f = form.upper()
    if f == "4":
        return "insider_transaction"
    if f in ("8-K", "6-K"):
        return "material_event"
    if "13D" in f or "13G" in f:
        return "activist_or_passive_stake"
    if "S-3" in f:
        return "shelf_registration"
    return "sec_filing"


def _between(text: str, a: str, b: str) -> str:
    i = text.find(a)
    if i < 0:
        return ""
    i += len(a)
    j = text.find(b, i)
    if j < 0:
        return ""
    return text[i:j]
