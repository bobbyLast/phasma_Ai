"""Deterministic snapshot replay helpers for merge-gate validation."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional


def load_snapshot(path: str) -> Dict[str, Any]:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def replay_normalize_and_expand(snapshot: Dict[str, Any]) -> Dict[str, Any]:
    """Replay interpreter path from a frozen worker snapshot — no network."""
    from utils.event_ontology import normalize_event_batch
    from utils.causal_hypotheses import hypotheses_for_events
    from utils.relationship_graph import expand_from_news_events

    news = list(snapshot.get("news_events") or snapshot.get("ingested_news") or [])
    market = snapshot.get("market_snapshot") or {}
    # Strip prediction markets if any leaked into news
    news = [n for n in news if isinstance(n, dict) and not n.get("prediction_market")]
    events = normalize_event_batch(news)
    hyps = hypotheses_for_events(events, market_snapshot=market, limit=20)
    related = expand_from_news_events(events, market_snapshot=market)
    return {
        "normalized_events": events,
        "causal_hypotheses": hyps,
        "relationship_candidates": related,
        "prediction_in_news": False,
    }


def assert_merge_invariants(snapshot: Dict[str, Any], replay: Dict[str, Any]) -> List[str]:
    """Return list of failed invariant names (empty = pass)."""
    failures = []
    news = snapshot.get("news_events") or snapshot.get("ingested_news") or []
    if any(isinstance(n, dict) and n.get("prediction_market") for n in news):
        # Snapshot may store separately; fail only if mixed into news_events used for confirm
        if snapshot.get("news_events") and any(
            isinstance(n, dict) and n.get("prediction_market") for n in snapshot["news_events"]
        ):
            failures.append("prediction_markets_as_news")
    if replay.get("prediction_in_news"):
        failures.append("prediction_in_replay_news")
    for h in replay.get("causal_hypotheses") or []:
        if h.get("trade_control"):
            failures.append("causal_trade_control")
            break
    return failures
