#!/usr/bin/env python3
"""Reset worker quarantine only after a verified successful news refresh."""

from __future__ import annotations

import argparse
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from core.supervisor.circuit_breaker import CircuitBreaker
from core.supervisor.snapshot_store import WorkerSnapshotStore
from scripts.news_ingest_ops import print_news_ingest_diagnostic, refresh_ok_recent


def main() -> int:
    parser = argparse.ArgumentParser(description="Reset worker quarantine after verified refresh")
    parser.add_argument("--worker", default="NewsIngestWorker")
    parser.add_argument(
        "--only-if-refresh-ok",
        action="store_true",
        help="Only clear quarantine when refresh_news_snapshot.py succeeded recently",
    )
    args = parser.parse_args()

    print_news_ingest_diagnostic()
    print()

    if args.only_if_refresh_ok:
        ok, marker = refresh_ok_recent()
        store = WorkerSnapshotStore()
        if not ok or store.is_stale("news_ingest", 900):
            print("QUARANTINE RESET")
            print("* skipped: no recent successful refresh or snapshot still stale")
            if marker:
                print(f"* last refresh marker: {marker.get('refreshed_at')} items={marker.get('items')}")
            return 1

    breaker = CircuitBreaker()
    state = breaker.get_state(args.worker)
    if state.status != "QUARANTINED" and not state.next_retry_at:
        print("QUARANTINE RESET")
        print(f"* {args.worker} is not quarantined — no action taken")
        return 0

    cleared = breaker.clear_quarantine(
        args.worker,
        reason="manual reset after successful real news snapshot refresh",
    )
    print("QUARANTINE RESET")
    print(f"* worker: {args.worker}")
    print(f"* cleared: {'yes' if cleared else 'no'}")
    print("* reason: manual reset after successful real news snapshot refresh")
    return 0 if cleared else 1


if __name__ == "__main__":
    raise SystemExit(main())
