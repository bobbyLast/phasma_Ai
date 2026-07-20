"""Shared helpers for news ingest diagnostics and snapshot refresh."""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from core.execution.data_gates import audit_api_keys
from core.runtime_paths import runtime_path
from core.source_status import block_demo_signal, is_demo_source
from core.supervisor.circuit_breaker import CircuitBreaker
from core.supervisor.snapshot_store import WorkerSnapshotStore

REFRESH_OK_MARKER = runtime_path("workers", "news_refresh_ok.json")
STATUS_STUB_TITLES = (
    "API Ready",
    "API Status",
    "Scraper Active",
    "API configured",
)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _parse_iso(ts: Optional[str]) -> Optional[datetime]:
    if not ts:
        return None
    try:
        dt = datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except (TypeError, ValueError):
        return None


def load_config_data() -> Dict[str, Any]:
    from core.config import PhasmaConfig
    cfg = PhasmaConfig("config.json")
    return cfg.data if hasattr(cfg, "data") else dict(cfg)


def source_coverage(config: Dict[str, Any]) -> Tuple[List[str], List[str], List[str]]:
    """Return (available, disabled, working) source labels."""
    disabled_map = audit_api_keys(config)
    disabled = sorted(disabled_map.keys())
    available = [
        "rss_feeds",
        "sec_edgar",
        "yahoo_chart",
        "kalshi_intel",
        "polymarket_intel",
        "github_status",
    ]
    for name in ("world_news_api", "gnews_api", "mediastack_api", "currents_api", "alpha_vantage"):
        key = name.replace("_api", "_key") if name != "alpha_vantage" else "alpha_vantage_key"
        apis = config.get("apis") or {}
        val = apis.get(name) if isinstance(apis, dict) else None
        if val and name not in disabled_map:
            available.append(name)
    working = [s for s in available if s not in disabled and s not in ("github_status",)]
    if "rss_feeds" not in working:
        working.insert(0, "rss_feeds")
    return available, disabled, working


def is_status_stub(item: Dict[str, Any]) -> bool:
    title = str(item.get("title") or "")
    return any(token in title for token in STATUS_STUB_TITLES)


def filter_decision_grade_news(
    items: List[Dict[str, Any]], config: Dict[str, Any]
) -> Tuple[List[Dict[str, Any]], int]:
    """Drop demo/sample/status-only items unsuitable for DecisionGroup."""
    kept: List[Dict[str, Any]] = []
    blocked = 0
    for item in items:
        if block_demo_signal(item, config) or is_demo_source(item.get("source")):
            blocked += 1
            continue
        if item.get("is_demo") or item.get("demo_only"):
            blocked += 1
            continue
        if is_status_stub(item):
            blocked += 1
            continue
        kept.append(item)
    return kept, blocked


def count_by_source(items: List[Dict[str, Any]]) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for item in items:
        src = str(item.get("source") or "unknown").lower()
        if "rss" in src or src in (
            "seeking alpha", "marketwatch", "yahoo finance", "financial times",
            "cnbc markets", "bbc business", "economic times", "bloomberg",
            "reuters business", "wsj",
        ):
            bucket = "rss"
        elif "kalshi" in src:
            bucket = "kalshi"
        elif "github" in src or "feedbin" in src:
            bucket = "github"
        elif "api" in src or src in ("world news api", "gnews api", "mediastack api", "currents api"):
            bucket = "news_api"
        else:
            bucket = src
        counts[bucket] = counts.get(bucket, 0) + 1
    return counts


def snapshot_age_seconds(store: WorkerSnapshotStore, key: str = "news_ingest") -> Optional[float]:
    snap = store.load_last_good(key)
    if not snap or not snap.get("saved_at"):
        return None
    saved = _parse_iso(snap["saved_at"])
    if not saved:
        return None
    return (_now() - saved).total_seconds()


def build_news_ingest_diagnostic() -> Dict[str, Any]:
    breaker = CircuitBreaker()
    store = WorkerSnapshotStore()
    config = load_config_data()
    state = breaker.get_state("NewsIngestWorker")
    snap = store.load_last_good("news_ingest")
    age = snapshot_age_seconds(store)
    stale = store.is_stale("news_ingest", 900)
    available, disabled, working = source_coverage(config)

    stale_reason = ""
    if not snap:
        stale_reason = "no snapshot on disk"
    elif stale:
        stale_reason = f"snapshot older than 900s (age={int(age or 0)}s)"
    elif state.status == "QUARANTINED":
        stale_reason = f"worker quarantined: {state.last_error_message}"

    return {
        "status": state.status,
        "last_success": state.last_success_at,
        "last_error": state.last_error_message,
        "fail_count": state.fail_count,
        "quarantine_until": state.next_retry_at,
        "latest_snapshot": store._snapshot_path("news_ingest"),
        "snapshot_age": int(age) if age is not None else None,
        "snapshot_ttl": 900,
        "stale_reason": stale_reason,
        "available_sources": available,
        "disabled_sources": disabled,
        "working_sources": working,
        "next_retry_at": state.next_retry_at,
        "snapshot_items": (snap or {}).get("metadata", {}).get("items"),
    }


def print_news_ingest_diagnostic(diag: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    diag = diag or build_news_ingest_diagnostic()
    print("NEWS INGEST DIAGNOSTIC")
    print(f"* status: {diag['status']}")
    print(f"* last_success: {diag['last_success']}")
    print(f"* last_error: {diag['last_error']}")
    print(f"* fail_count: {diag['fail_count']}")
    print(f"* quarantine_until: {diag['quarantine_until']}")
    print(f"* latest_snapshot: {diag['latest_snapshot']}")
    print(f"* snapshot_age: {diag['snapshot_age']}")
    print(f"* snapshot_ttl: {diag['snapshot_ttl']}")
    print(f"* stale_reason: {diag['stale_reason']}")
    print(f"* available_sources: {', '.join(diag['available_sources'])}")
    print(f"* disabled_sources: {', '.join(diag['disabled_sources']) or 'none'}")
    print(f"* working_sources: {', '.join(diag['working_sources'])}")
    print(f"* next_retry_at: {diag['next_retry_at']}")
    return diag


def write_refresh_ok_marker(payload: Dict[str, Any]) -> str:
    os.makedirs(os.path.dirname(REFRESH_OK_MARKER), exist_ok=True)
    with open(REFRESH_OK_MARKER, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
    return REFRESH_OK_MARKER


def refresh_ok_recent(max_age_seconds: int = 3600) -> Tuple[bool, Optional[Dict[str, Any]]]:
    if not os.path.isfile(REFRESH_OK_MARKER):
        return False, None
    try:
        with open(REFRESH_OK_MARKER, encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return False, None
    at = _parse_iso(data.get("refreshed_at"))
    if not at:
        return False, data
    age = (_now() - at).total_seconds()
    if age > max_age_seconds:
        return False, data
    if not data.get("success"):
        return False, data
    return True, data
