"""Event ontology — normalize news/SEC/macro into typed trade-relevant events."""

from __future__ import annotations

import hashlib
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from utils.news_cycle_helpers import classify_news_freshness, parse_news_timestamp

# keyword → (event_type, direction_hint, default_materiality)
_EVENT_PATTERNS = (
    (r"\bguidance\s+(cut|lower|reduced|slash)", "guidance_cut", "down", 0.85),
    (r"\bguidance\s+(raise|raised|lift|boost|higher)", "guidance_raise", "up", 0.8),
    (r"\bearnings\s+miss|\bmiss(es|ed)?\s+estimates", "earnings_miss", "down", 0.8),
    (r"\bearnings\s+beat|\bbeats?\s+estimates", "earnings_beat", "up", 0.75),
    (r"\bcontract\s+(loss|lost|cancelled|canceled)", "contract_loss", "down", 0.85),
    (r"\bcontract\s+(award|won|win|lands?)", "contract_award", "up", 0.8),
    (r"\b(fda)\s+(reject|rejection|crl|complete response)", "fda_rejection", "down", 0.9),
    (r"\b(fda)\s+(approv|clearance)", "fda_approval", "up", 0.85),
    (r"\b(recall|cyberattack|outage|lawsuit|bankrupt)", "operational_negative", "down", 0.7),
    (r"\b(acquisition|acquire[sd]?|merger|buyout)", "m_and_a", "up", 0.65),
    (r"\b(offering|dilution|atm\s+program|convertible)", "dilution", "down", 0.7),
    (r"\b(buyback|repurchase)", "buyback", "up", 0.55),
    (r"\b(downgrade)", "downgrade", "down", 0.55),
    (r"\b(upgrade)", "upgrade", "up", 0.55),
)

_SOURCE_TIER = {
    "sec edgar": 1,
    "sec": 1,
    "fred": 1,
    "bls": 1,
    "bea": 1,
    "eia": 1,
    "reuters": 3,
    "bloomberg": 3,
    "wsj": 3,
    "financial times": 3,
    "cnbc": 4,
    "yahoo": 4,
    "seeking alpha": 4,
    "reddit": 6,
    "twitter": 6,
}


def source_tier(source: str) -> int:
    s = str(source or "").lower()
    for key, tier in _SOURCE_TIER.items():
        if key in s:
            return tier
    return 4


def classify_event_type(title: str, summary: str = "") -> tuple:
    blob = f"{title} {summary}".lower()
    for pattern, etype, direction, mat in _EVENT_PATTERNS:
        if re.search(pattern, blob, re.I):
            return etype, direction, mat
    return "unclassified_news", "unknown", 0.35


def normalize_event(item: Dict[str, Any], *, cycle_detected_at: Optional[str] = None) -> Dict[str, Any]:
    """Convert a raw news/SEC/macro row into a NormalizedEvent dict."""
    title = str(item.get("title") or "")
    summary = str(item.get("summary") or item.get("article_body") or "")
    etype, direction, mat = classify_event_type(title, summary)
    if item.get("event_type"):
        etype = str(item["event_type"])
    if item.get("filing_type"):
        mat = max(mat, 0.6)
    published = parse_news_timestamp(item)
    published_at = published.isoformat() if published else item.get("timestamp")
    now = cycle_detected_at or datetime.now(timezone.utc).isoformat()
    entities = []
    sym = str(item.get("symbol") or "").upper().strip()
    if sym:
        entities.append(sym)
    if item.get("company_name"):
        entities.append(str(item["company_name"]))
    raw_id = f"{etype}|{sym}|{title[:80]}|{published_at}"
    event_id = "evt_" + hashlib.sha1(raw_id.encode("utf-8")).hexdigest()[:12]

    surprise = item.get("surprise")
    actual = item.get("actual")
    consensus = item.get("consensus")
    previous = item.get("previous")
    already_priced = item.get("already_priced_probability")
    if already_priced is None:
        already_priced = None  # explicit unknown

    scope = "company_specific" if sym else "macroeconomic" if item.get("series_id") else "unconfirmed"
    if etype.startswith("fda") or "trial" in etype:
        scope = "product_specific"

    return {
        "event_id": event_id,
        "event_type": etype,
        "entities": entities,
        "symbol": sym,
        "timestamp": published_at or now,
        "published_at": published_at,
        "first_seen_at": item.get("first_seen_at") or now,
        "provider_received_at": item.get("provider_received_at") or published_at,
        "cycle_detected_at": now,
        "source": item.get("source"),
        "source_tier": source_tier(str(item.get("source") or "")),
        "scope": scope,
        "materiality": float(item.get("materiality") or mat),
        "surprise": surprise,
        "actual": actual,
        "consensus": consensus,
        "previous": previous,
        "already_priced_probability": already_priced,
        "directional_interpretation": direction,
        "sentiment": item.get("sentiment"),
        "freshness_class": item.get("freshness_class") or classify_news_freshness(item),
        "facts": [title] if title else [],
        "inferences": [],
        "contradictions": [],
        "title": title,
        "url": item.get("url"),
        "raw_ref": item.get("event_fingerprint"),
    }


def normalize_event_batch(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    now = datetime.now(timezone.utc).isoformat()
    out = []
    seen = set()
    for item in items or []:
        if not isinstance(item, dict):
            continue
        if item.get("prediction_market"):
            continue  # never treat prediction markets as news events
        ev = normalize_event(item, cycle_detected_at=now)
        if ev["event_id"] in seen:
            continue
        seen.add(ev["event_id"])
        out.append(ev)
    return out
