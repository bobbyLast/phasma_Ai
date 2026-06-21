"""Cadence tracking for engine groups (fast vs slow loop)."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from core.runtime_paths import runtime_path

_CADENCE_SECONDS = {
    "every_cycle": 0,
    "15min": 15 * 60,
    "30min": 30 * 60,
    "hourly": 60 * 60,
    "4h": 4 * 60 * 60,
    "daily": 24 * 60 * 60,
    "every_cycle_if_due": 0,
}


def parse_cadence_seconds(cadence: str) -> int:
    return _CADENCE_SECONDS.get(str(cadence or "every_cycle").lower(), 0)


class CadenceTracker:
    """Track last-run timestamps per group."""

    def __init__(self, state_path: Optional[str] = None):
        self.state_path = state_path or runtime_path("context", "cadence_state.json")
        os.makedirs(os.path.dirname(self.state_path), exist_ok=True)
        self._state: Dict[str, str] = {}
        self._load()

    def _load(self) -> None:
        if os.path.isfile(self.state_path):
            try:
                with open(self.state_path, encoding="utf-8") as f:
                    self._state = json.load(f)
            except Exception:
                self._state = {}

    def _save(self) -> None:
        with open(self.state_path, "w", encoding="utf-8") as f:
            json.dump(self._state, f, indent=2)

    def is_due(self, group_key: str, cadence: str, *, cycle_attempt: int = 1) -> bool:
        if cadence in ("every_cycle", "every_cycle_if_due"):
            return True
        interval = parse_cadence_seconds(cadence)
        if interval <= 0:
            return True
        last = self._state.get(group_key)
        if not last:
            return True
        try:
            last_dt = datetime.fromisoformat(last.replace("Z", "+00:00"))
        except ValueError:
            return True
        elapsed = (datetime.now(timezone.utc) - last_dt).total_seconds()
        return elapsed >= interval

    def mark_ran(self, group_key: str) -> None:
        self._state[group_key] = datetime.now(timezone.utc).isoformat()
        self._save()

    def next_run_at(self, group_key: str, cadence: str) -> Optional[str]:
        interval = parse_cadence_seconds(cadence)
        last = self._state.get(group_key)
        if not last or interval <= 0:
            return None
        try:
            last_dt = datetime.fromisoformat(last.replace("Z", "+00:00"))
            from datetime import timedelta
            return (last_dt + timedelta(seconds=interval)).isoformat()
        except ValueError:
            return None
