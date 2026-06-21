"""Shared context snapshots between engine groups."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from core.runtime_paths import runtime_path


class ContextSnapshotStore:
    """Read/write group snapshots under data/runtime/context/."""

    SNAPSHOT_FILES = {
        "ingest": "latest_ingest.json",
        "market": "latest_market.json",
        "risk": "latest_risk.json",
        "candidates": "latest_candidates.json",
        "enriched": "latest_enriched_candidates.json",
        "signals": "latest_signals.json",
        "decisions": "latest_decisions.json",
        "execution": "latest_execution_results.json",
        "reports": "latest_reports.json",
        "learning": "latest_learning.json",
    }

    def __init__(self, base_dir: Optional[str] = None):
        self.base_dir = base_dir or runtime_path("context")
        os.makedirs(self.base_dir, exist_ok=True)

    def _path(self, key: str) -> str:
        name = self.SNAPSHOT_FILES.get(key, f"latest_{key}.json")
        return os.path.join(self.base_dir, name)

    def save(
        self,
        key: str,
        payload: Any,
        *,
        source_group: str,
        ttl_seconds: int = 900,
        item_count: Optional[int] = None,
        data_quality: str = "OK",
    ) -> str:
        if item_count is None:
            try:
                item_count = len(payload) if hasattr(payload, "__len__") else 0
            except TypeError:
                item_count = 0
        now = datetime.now(timezone.utc)
        record = {
            "generated_at": now.isoformat(),
            "ttl_seconds": ttl_seconds,
            "source_group": source_group,
            "item_count": item_count,
            "stale_after": (now.timestamp() + ttl_seconds),
            "data_quality": data_quality,
            "payload": payload,
        }
        path = self._path(key)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(record, f, indent=2, default=str)
        return path

    def load(self, key: str) -> Optional[Dict[str, Any]]:
        path = self._path(key)
        if not os.path.isfile(path):
            return None
        try:
            with open(path, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return None

    def is_fresh(self, key: str) -> bool:
        snap = self.load(key)
        if not snap:
            return False
        stale_after = snap.get("stale_after")
        if stale_after is None:
            return True
        try:
            return datetime.now(timezone.utc).timestamp() < float(stale_after)
        except (TypeError, ValueError):
            return False

    def get_payload(self, key: str) -> Any:
        snap = self.load(key)
        return (snap or {}).get("payload")
