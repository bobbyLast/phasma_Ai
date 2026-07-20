"""Idempotent paper order keys — restart-safe submission identity."""

from __future__ import annotations

import hashlib
from typing import Any, Dict, Optional, Set


def order_idempotency_key(signal: Dict[str, Any], *, cycle_id: str = "") -> str:
    sym = str(signal.get("symbol") or signal.get("ticker") or "").upper()
    side = str(signal.get("side") or signal.get("action") or "BUY").upper()
    strategy = str(signal.get("strategy") or "")
    entry = signal.get("entry") or signal.get("current_price") or ""
    horizon = ""
    fc = signal.get("forecast")
    if isinstance(fc, dict):
        horizon = str(fc.get("horizon") or "")
    raw = f"{cycle_id}|{sym}|{side}|{strategy}|{entry}|{horizon}"
    return "oid_" + hashlib.sha1(raw.encode("utf-8")).hexdigest()[:16]


class IdempotentOrderLedger:
    """In-memory + optional set of submitted keys for restart-safe paper submits."""

    def __init__(self, initial: Optional[Set[str]] = None):
        self._keys: Set[str] = set(initial or [])

    def already_submitted(self, key: str) -> bool:
        return key in self._keys

    def mark_submitted(self, key: str) -> None:
        self._keys.add(key)

    def try_claim(self, signal: Dict[str, Any], *, cycle_id: str = "") -> tuple:
        key = order_idempotency_key(signal, cycle_id=cycle_id)
        if key in self._keys:
            return False, key, "duplicate_idempotency_key"
        self._keys.add(key)
        signal["idempotency_key"] = key
        return True, key, "claimed"
