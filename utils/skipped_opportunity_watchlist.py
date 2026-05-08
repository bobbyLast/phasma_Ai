"""
Skipped-opportunity revisit queue (persists to disk).

Complements in-memory ``ai_watchlist`` and ``NewsImpactTracker``:
records high-confidence ideas that failed to execute, re-injects them into
the news pipeline on later cycles, tracks follow-through vs the skip-time
reference price, and applies a small confidence boost when price action
validates the original thesis.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional, Set


def _utcnow_iso() -> str:
    return datetime.now().isoformat()


class SkippedOpportunityWatchlist:
    """
    Tracks symbols we passed on (e.g. execution failed) so later cycles can
    re-analyze them with fresh prices and light learning boosts.
    """

    def __init__(self, data_dir: str = "data", filename: str = "skipped_opportunities.json"):
        self.data_dir = data_dir
        self.path = os.path.join(data_dir, filename)
        self._entries: Dict[str, Dict[str, Any]] = {}
        self._max_symbols = 120
        self._max_age_days = 21
        self._revisit_inject_per_cycle = 15
        self._min_move_for_regret = 0.02  # 2% favorable vs ref at skip
        self._load()

    def _load(self) -> None:
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir, exist_ok=True)
        if os.path.isfile(self.path):
            try:
                with open(self.path, "r", encoding="utf-8") as f:
                    raw = json.load(f)
                if isinstance(raw, dict) and isinstance(raw.get("entries"), dict):
                    self._entries = raw["entries"]
                elif isinstance(raw, dict):
                    # legacy: plain symbol -> dict
                    self._entries = raw
                self._prune()
            except Exception:
                self._entries = {}
        else:
            self._entries = {}

    def _save(self) -> None:
        try:
            if not os.path.exists(self.data_dir):
                os.makedirs(self.data_dir, exist_ok=True)
            payload = {"updated": _utcnow_iso(), "entries": self._entries}
            with open(self.path, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2)
        except Exception:
            pass

    def _prune(self) -> None:
        cutoff = datetime.now() - timedelta(days=self._max_age_days)
        for sym in list(self._entries.keys()):
            row = self._entries.get(sym) or {}
            try:
                ts = datetime.fromisoformat(row.get("last_skip_at", row.get("first_skip_at", "")))
            except Exception:
                ts = None
            if ts is not None and ts < cutoff:
                del self._entries[sym]
        # cap count: drop oldest by first_skip_at
        if len(self._entries) > self._max_symbols:
            ranked = sorted(
                self._entries.items(),
                key=lambda kv: kv[1].get("first_skip_at", ""),
            )
            overflow = len(self._entries) - self._max_symbols
            for sym, _ in ranked[:overflow]:
                del self._entries[sym]

    def record_execution_skip(
        self,
        symbol: str,
        action: str,
        confidence: float,
        ref_price: float,
        reason: str,
        *,
        source: str = "monitor_execute",
    ) -> None:
        """Record that we saw a viable signal but did not complete execution."""
        sym = (symbol or "").upper().strip()
        if not sym or sym == "UNKNOWN":
            return
        act = (action or "BUY").upper()
        if ref_price is None or float(ref_price) <= 0:
            ref_price = 0.0
        else:
            ref_price = float(ref_price)
        now = _utcnow_iso()
        row = self._entries.get(sym)
        if row and row.get("last_skip_at"):
            try:
                last = datetime.fromisoformat(row["last_skip_at"])
                if datetime.now() - last < timedelta(hours=1):
                    row["skip_count"] = int(row.get("skip_count", 1)) + 1
                    row["last_reason"] = reason
                    row["last_skip_at"] = now
                    row["last_action"] = act
                    row["last_confidence"] = float(confidence)
                    if ref_price > 0:
                        row["ref_price"] = ref_price
                    self._entries[sym] = row
                    self._prune()
                    self._save()
                    return
            except Exception:
                pass

        self._entries[sym] = {
            "first_skip_at": row.get("first_skip_at", now) if row else now,
            "last_skip_at": now,
            "last_action": act,
            "last_confidence": float(confidence),
            "ref_price": ref_price,
            "skip_count": int(row.get("skip_count", 0)) + 1 if row else 1,
            "last_reason": reason,
            "source": source,
            "regret_events": int(row.get("regret_events", 0)) if row else 0,
            "favorable_pct_max": float(row.get("favorable_pct_max", 0.0)) if row else 0.0,
        }
        self._prune()
        self._save()

    def mark_cleared(self, symbol: str) -> None:
        """Remove symbol after a successful trade or explicit resolution."""
        sym = (symbol or "").upper().strip()
        if sym in self._entries:
            del self._entries[sym]
            self._save()

    def note_price_move(self, symbol: str, current_price: float, action: str) -> None:
        """
        When we later see a real price for a queued symbol, measure follow-through
        vs ``ref_price`` at skip time and count regret / validation events.
        """
        sym = (symbol or "").upper().strip()
        row = self._entries.get(sym)
        if not row or current_price is None or float(current_price) <= 0:
            return
        ref = float(row.get("ref_price") or 0.0)
        if ref <= 0:
            row["ref_price"] = float(current_price)
            self._entries[sym] = row
            self._save()
            return
        act = (action or row.get("last_action") or "BUY").upper()
        cur = float(current_price)
        move = (cur - ref) / ref
        favorable = False
        if "PUT" in act or "SHORT" in act or "SELL" in act:
            favorable = move <= -self._min_move_for_regret
        else:
            favorable = move >= self._min_move_for_regret
        if favorable:
            row["regret_events"] = int(row.get("regret_events", 0)) + 1
            row["favorable_pct_max"] = max(float(row.get("favorable_pct_max", 0.0)), abs(move))
            row["last_price_seen"] = cur
            row["last_price_at"] = _utcnow_iso()
            self._entries[sym] = row
            self._save()

    def get_confidence_delta(self, symbol: str, action: Optional[str] = None) -> float:
        """
        Small additive boost to unified confidence when follow-through validated
        a previously skipped idea (capped).
        """
        sym = (symbol or "").upper().strip()
        row = self._entries.get(sym)
        if not row:
            return 0.0
        events = int(row.get("regret_events", 0))
        if events <= 0:
            return 0.0
        base = 0.012 * min(events, 4)
        extra = 0.01 * min(float(row.get("favorable_pct_max", 0.0)) / 0.05, 2.0)
        return min(0.07, base + extra)

    def get_priority_symbols(self, limit: int = 40) -> List[str]:
        """Symbols to merge into crash tracking / discovery (most recent skips first)."""
        ranked = sorted(
            self._entries.items(),
            key=lambda kv: kv[1].get("last_skip_at", ""),
            reverse=True,
        )
        return [s for s, _ in ranked[:limit]]

    def get_revisit_news_items(
        self,
        existing_symbols: Set[str],
        price_fetcher: Any,
        *,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Build minimal pseudo-news rows so unified analysis runs again for symbols
        absent from the current headline batch.
        """
        lim = limit if limit is not None else self._revisit_inject_per_cycle
        existing = {str(x).upper() for x in existing_symbols if x}
        out: List[Dict[str, Any]] = []
        ranked = sorted(
            self._entries.items(),
            key=lambda kv: kv[1].get("last_skip_at", ""),
            reverse=True,
        )
        for sym, row in ranked:
            if len(out) >= lim:
                break
            if sym in existing:
                continue
            price = None
            if price_fetcher is not None and hasattr(price_fetcher, "get_real_price"):
                try:
                    price = price_fetcher.get_real_price(sym)
                except Exception:
                    price = None
            if price is None or float(price) <= 0:
                continue
            price_f = float(price)
            self.note_price_move(sym, price_f, row.get("last_action", "BUY"))
            out.append(
                {
                    "symbol": sym,
                    "title": f"Revisit: prior skip ({row.get('last_reason', 'unknown')})",
                    "summary": (
                        f"Previously passed at ~${float(row.get('ref_price') or price_f):.2f}; "
                        f"re-analyzing at ${price_f:.2f}. Skips: {row.get('skip_count', 1)}."
                    ),
                    "source": "skipped_opportunity_revisit",
                    "sentiment": 0.55,
                    "catalyst_score": min(0.95, float(row.get("last_confidence", 0.5)) + 0.05),
                    "sector": "RevisitQueue",
                    "current_price": price_f,
                    "action": row.get("last_action", "BUY"),
                }
            )
            existing.add(sym)
        return out

    def summary(self) -> Dict[str, Any]:
        return {
            "tracked_symbols": len(self._entries),
            "path": self.path,
        }


_watchlist: Optional[SkippedOpportunityWatchlist] = None


def get_skipped_opportunity_watchlist() -> SkippedOpportunityWatchlist:
    global _watchlist
    if _watchlist is None:
        _watchlist = SkippedOpportunityWatchlist()
    return _watchlist
