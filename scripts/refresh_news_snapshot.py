#!/usr/bin/env python3
"""Refresh real news ingest snapshot and clear NewsIngestWorker quarantine on success."""

from __future__ import annotations

import asyncio
import os
import sys
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from core.config import PhasmaConfig
from core.runtime.context_snapshots import ContextSnapshotStore
from core.supervisor.circuit_breaker import CircuitBreaker
from core.supervisor.snapshot_store import WorkerSnapshotStore
from engines.news_engine_integrated import IntegratedNewsSources
from scripts.news_ingest_ops import (
    count_by_source,
    filter_decision_grade_news,
    print_news_ingest_diagnostic,
    write_refresh_ok_marker,
)
from utils.cycle_data_context import CycleDataContext


async def refresh_news_snapshot() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")

    print_news_ingest_diagnostic()
    print()

    config = PhasmaConfig("config.json")
    config_data = config.data
    breaker = CircuitBreaker()
    store = WorkerSnapshotStore()
    ctx_store = ContextSnapshotStore()

    # Clear shared cache so refresh pulls live RSS/API data
    from engines.news_engine_integrated import IntegratedNewsSources
    IntegratedNewsSources._shared_news_cache = None
    IntegratedNewsSources._shared_news_cache_time = None

    news_sources = IntegratedNewsSources(config)

    try:
        cycle_data = await CycleDataContext.ingest(
            news_sources,
            config=config,
            market_cache=None,
        )
    except Exception as exc:
        print("NEWS SNAPSHOT REFRESH")
        print(f"* FAILED: {exc}")
        print("* Worker health updated: no")
        print("* Quarantine cleared: no")
        return 1

    filtered, demo_blocked = filter_decision_grade_news(cycle_data.ingested_news, config_data)
    if not filtered:
        print("NEWS SNAPSHOT REFRESH")
        print("* FAILED: no real decision-grade news items after filtering")
        print(f"* demo/status items blocked: {demo_blocked}")
        print("* Worker health updated: no")
        print("* Quarantine cleared: no")
        return 1

    cycle_data.ingested_news = filtered
    counts = count_by_source(filtered)
    rss_n = counts.get("rss", 0)
    api_n = counts.get("news_api", 0)
    kalshi_n = counts.get("kalshi", 0)
    github_n = counts.get("github", 0)

    payload = {
        "ingested_news": cycle_data.ingested_news,
        "symbol_universe": cycle_data.symbol_universe,
        "company_names": cycle_data.company_names,
        "prices": cycle_data.prices,
    }
    snap_path = store.save_last_good(
        "news_ingest",
        payload,
        metadata={
            "items": len(filtered),
            "demo_blocked": demo_blocked,
            "source_counts": counts,
            "refreshed_by": "scripts/refresh_news_snapshot.py",
        },
    )
    ttl = int((config_data.get("engine_groups") or {}).get("ingest", {}).get("ttl_seconds", 900))
    ingest_ctx_path = ctx_store.save(
        "ingest",
        payload,
        source_group="IngestGroup",
        ttl_seconds=ttl,
        item_count=len(filtered),
        data_quality="PARTIAL" if api_n == 0 else "OK",
    )
    news_ctx_path = ctx_store.save(
        "news",
        {"items": filtered, "symbol_universe": cycle_data.symbol_universe},
        source_group="IngestGroup",
        ttl_seconds=ttl,
        item_count=len(filtered),
        data_quality="PARTIAL" if api_n == 0 else "OK",
    )

    breaker.clear_quarantine(
        "NewsIngestWorker",
        reason="manual reset after successful real news snapshot refresh",
    )
    breaker.record_success("NewsIngestWorker")
    cleared = breaker.get_state("NewsIngestWorker").status == "OK"

    marker = write_refresh_ok_marker({
        "success": True,
        "refreshed_at": datetime.now(timezone.utc).isoformat(),
        "items": len(filtered),
        "demo_blocked": demo_blocked,
        "snapshot_path": snap_path,
        "worker": "NewsIngestWorker",
    })

    print("NEWS SNAPSHOT REFRESH")
    print(f"* RSS items: {rss_n}")
    print(f"* News API items: {api_n}")
    print(f"* Kalshi items: {kalshi_n}")
    print(f"* GitHub items: {github_n}")
    print(f"* Total items: {len(filtered)}")
    print(f"* Symbols found: {len(cycle_data.symbol_universe)}")
    print(f"* Prices attached: {len(cycle_data.prices)}")
    print(f"* Demo/status blocked: {demo_blocked}")
    print(f"* Snapshot path: {snap_path}")
    print(f"* Context ingest: {ingest_ctx_path}")
    print(f"* Context news: {news_ctx_path}")
    print(f"* Refresh marker: {marker}")
    print("* Worker health updated: yes")
    print(f"* Quarantine cleared: {'yes' if cleared else 'no (was not quarantined)'}")
    return 0


def main() -> int:
    return asyncio.run(refresh_news_snapshot())


if __name__ == "__main__":
    raise SystemExit(main())
