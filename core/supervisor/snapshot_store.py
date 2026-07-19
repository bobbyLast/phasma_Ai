"""Persistent worker snapshots and pending queues."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from core.runtime_paths import runtime_path


class WorkerSnapshotStore:
    """Read/write last-good worker outputs and pending telegram alerts."""

    def __init__(self, base_dir: Optional[str] = None):
        self.base_dir = base_dir or runtime_path("workers")
        self.last_good_dir = os.path.join(self.base_dir, "last_good")
        self.pending_telegram_path = os.path.join(self.base_dir, "pending_telegram.json")
        os.makedirs(self.last_good_dir, exist_ok=True)

    def _snapshot_path(self, worker_key: str) -> str:
        return os.path.join(self.last_good_dir, f"{worker_key}.json")

    def save_last_good(self, worker_key: str, data: Any, *, metadata: Optional[Dict[str, Any]] = None) -> str:
        path = self._snapshot_path(worker_key)
        payload = {
            "saved_at": datetime.now(timezone.utc).isoformat(),
            "data": data,
            "metadata": metadata or {},
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
        return path

    def load_last_good(self, worker_key: str) -> Optional[Dict[str, Any]]:
        path = self._snapshot_path(worker_key)
        if not os.path.exists(path):
            return None
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return None

    def is_stale(self, worker_key: str, max_age_seconds: int = 900) -> bool:
        snap = self.load_last_good(worker_key)
        if not snap or not snap.get("saved_at"):
            return True
        try:
            saved = datetime.fromisoformat(str(snap["saved_at"]).replace("Z", "+00:00"))
            if saved.tzinfo is None:
                saved = saved.replace(tzinfo=timezone.utc)
            age = (datetime.now(timezone.utc) - saved).total_seconds()
            return age > max_age_seconds
        except (TypeError, ValueError):
            return True

    def append_pending_telegram(self, alert: Dict[str, Any]) -> None:
        pending = self.load_pending_telegram()
        pending.append({**alert, "queued_at": datetime.now(timezone.utc).isoformat()})
        with open(self.pending_telegram_path, "w", encoding="utf-8") as f:
            json.dump(pending, f, indent=2)

    def load_pending_telegram(self) -> List[Dict[str, Any]]:
        if not os.path.exists(self.pending_telegram_path):
            return []
        try:
            with open(self.pending_telegram_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data if isinstance(data, list) else []
        except (json.JSONDecodeError, OSError):
            return []

    def clear_pending_telegram(self) -> None:
        with open(self.pending_telegram_path, "w", encoding="utf-8") as f:
            json.dump([], f)
