"""Unified trade performance ledger — stocks, day trades, and Kalshi virtual bets."""

from __future__ import annotations

import json
import os
import threading
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from core.runtime_paths import runtime_path

ASSET_STOCK = "STOCK"
ASSET_DAY_TRADE = "DAY_TRADE"
ASSET_KALSHI = "KALSHI"
_VALID_ASSETS = frozenset({ASSET_STOCK, ASSET_DAY_TRADE, ASSET_KALSHI})


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def _infer_asset_class(signal: Dict[str, Any]) -> str:
    explicit = str(signal.get("asset_class") or signal.get("ledger_asset_class") or "").upper()
    if explicit in _VALID_ASSETS:
        return explicit
    sym = str(signal.get("symbol") or signal.get("ticker") or "").upper()
    if sym.startswith("KX") or signal.get("prediction_market") or signal.get("source") == "kalshi_prediction":
        return ASSET_KALSHI
    source = str(signal.get("source") or "").lower()
    strategy = str(signal.get("strategy") or signal.get("trade_class") or "").lower()
    if source in ("day_trading", "heavy_mover", "heavy_mover_watch") or "day" in strategy or "scalp" in strategy:
        return ASSET_DAY_TRADE
    return ASSET_STOCK


class TradePerformanceLedger:
    """Append-only JSONL of opens/closes with rolling win-rate stats."""

    def __init__(self, path: Optional[str] = None):
        self.path = path or runtime_path("performance", "trade_ledger.jsonl")
        self._lock = threading.Lock()
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        self._opens: Dict[str, Dict[str, Any]] = {}
        self._closed: List[Dict[str, Any]] = []
        self._load()

    def _load(self) -> None:
        if not os.path.exists(self.path):
            return
        try:
            with open(self.path, "r", encoding="utf-8") as fh:
                for line in fh:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        row = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    event = row.get("event")
                    if event == "open":
                        tid = row.get("trade_id")
                        if tid:
                            self._opens[tid] = row
                    elif event == "close":
                        tid = row.get("trade_id")
                        if tid and tid in self._opens:
                            del self._opens[tid]
                        self._closed.append(row)
        except OSError:
            pass

    def _append(self, row: Dict[str, Any]) -> None:
        with self._lock:
            with open(self.path, "a", encoding="utf-8") as fh:
                fh.write(json.dumps(row, default=str) + "\n")

    def record_open(
        self,
        signal: Dict[str, Any],
        *,
        fill: Optional[Dict[str, Any]] = None,
        virtual: bool = False,
    ) -> str:
        trade_id = str(uuid.uuid4())
        fill = fill or {}
        asset = _infer_asset_class(signal)
        entry_price = (
            fill.get("price")
            or signal.get("entry_price")
            or signal.get("current_price")
            or signal.get("implied_probability")
        )
        row = {
            "event": "open",
            "trade_id": trade_id,
            "timestamp": _utcnow(),
            "asset_class": asset,
            "symbol": str(signal.get("symbol") or signal.get("ticker") or "").upper(),
            "action": signal.get("action") or signal.get("kalshi_signal") or "BUY",
            "entry_price": entry_price,
            "quantity": fill.get("quantity") or signal.get("quantity") or signal.get("position_size"),
            "confidence": signal.get("confidence"),
            "source": signal.get("source"),
            "strategy": signal.get("strategy") or signal.get("trade_class"),
            "sector": signal.get("sector"),
            "industry": signal.get("industry"),
            "catalyst_type": signal.get("catalyst_type") or signal.get("timeframe_type"),
            "virtual": virtual or asset == ASSET_KALSHI,
            "setup_tags": list(signal.get("setup_tags") or []),
            "news_fingerprint": signal.get("news_fingerprint") or signal.get("title"),
            "weather_forecast": signal.get("weather_forecast"),
            "implied_probability": signal.get("implied_probability") or signal.get("prediction_probability"),
            "trade_link": signal.get("trade_link"),
            "metadata": {
                "rsi": signal.get("rsi"),
                "volume_ratio": signal.get("volume_ratio"),
                "change_pct": signal.get("change_pct"),
                "pop_from_sim": signal.get("pop_from_sim") or signal.get("simulation_pop"),
                "broker_order_id": fill.get("order_id"),
            },
        }
        self._opens[trade_id] = row
        self._append(row)
        return trade_id

    def record_close(
        self,
        trade_id: str,
        *,
        exit_price: float,
        win: Optional[bool] = None,
        pnl: Optional[float] = None,
        pnl_pct: Optional[float] = None,
        reason: str = "",
        weather_actual: Any = None,
        weather_correct: Optional[bool] = None,
        settled_result: Any = None,
    ) -> Optional[Dict[str, Any]]:
        open_row = self._opens.get(trade_id)
        if not open_row:
            # Allow close-by-symbol lookup for Alpaca exits without open id
            return None
        entry = open_row.get("entry_price")
        try:
            entry_f = float(entry) if entry is not None else None
            exit_f = float(exit_price)
        except (TypeError, ValueError):
            entry_f, exit_f = None, None

        if pnl is None and entry_f is not None and exit_f is not None and entry_f > 0:
            action = str(open_row.get("action") or "BUY").upper()
            if "PUT" in action or "NO" in action or action == "SELL":
                pnl_pct = (entry_f - exit_f) / entry_f
            else:
                pnl_pct = (exit_f - entry_f) / entry_f
            qty = open_row.get("quantity") or 1
            try:
                pnl = float(qty) * (exit_f - entry_f) * (-1 if ("PUT" in action or "NO" in action) else 1)
            except (TypeError, ValueError):
                pnl = None

        if win is None and pnl_pct is not None:
            win = pnl_pct > 0
        elif win is None and pnl is not None:
            win = float(pnl) > 0

        close_row = {
            "event": "close",
            "trade_id": trade_id,
            "timestamp": _utcnow(),
            "asset_class": open_row.get("asset_class"),
            "symbol": open_row.get("symbol"),
            "action": open_row.get("action"),
            "entry_price": entry,
            "exit_price": exit_price,
            "pnl": pnl,
            "pnl_pct": pnl_pct,
            "win": bool(win) if win is not None else None,
            "reason": reason,
            "virtual": open_row.get("virtual", False),
            "source": open_row.get("source"),
            "strategy": open_row.get("strategy"),
            "sector": open_row.get("sector"),
            "catalyst_type": open_row.get("catalyst_type"),
            "setup_tags": open_row.get("setup_tags"),
            "news_fingerprint": open_row.get("news_fingerprint"),
            "weather_forecast": open_row.get("weather_forecast"),
            "weather_actual": weather_actual,
            "weather_correct": weather_correct,
            "settled_result": settled_result,
            "metadata": open_row.get("metadata") or {},
            "opened_at": open_row.get("timestamp"),
        }
        if trade_id in self._opens:
            del self._opens[trade_id]
        self._closed.append(close_row)
        self._append(close_row)
        return close_row

    def record_close_by_symbol(
        self,
        symbol: str,
        *,
        exit_price: float,
        **kwargs: Any,
    ) -> Optional[Dict[str, Any]]:
        sym = str(symbol or "").upper()
        match_id = None
        for tid, row in self._opens.items():
            if str(row.get("symbol") or "").upper() == sym:
                match_id = tid
                break
        if not match_id:
            return None
        return self.record_close(match_id, exit_price=exit_price, **kwargs)

    def closed_trades(
        self,
        *,
        asset_class: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        rows = self._closed
        if asset_class:
            ac = asset_class.upper()
            rows = [r for r in rows if str(r.get("asset_class") or "").upper() == ac]
        if limit is not None:
            rows = rows[-limit:]
        return list(rows)

    def open_trades(self, *, asset_class: Optional[str] = None) -> List[Dict[str, Any]]:
        rows = list(self._opens.values())
        if asset_class:
            ac = asset_class.upper()
            rows = [r for r in rows if str(r.get("asset_class") or "").upper() == ac]
        return rows

    def win_rate(
        self,
        *,
        asset_class: Optional[str] = None,
        min_samples: int = 1,
    ) -> Dict[str, Any]:
        rows = [r for r in self.closed_trades(asset_class=asset_class) if r.get("win") is not None]
        n = len(rows)
        if n < min_samples:
            return {
                "win_rate": None,
                "wins": sum(1 for r in rows if r.get("win")),
                "losses": sum(1 for r in rows if r.get("win") is False),
                "samples": n,
                "label": f"building sample ({n} closed)",
                "asset_class": asset_class or "ALL",
            }
        wins = sum(1 for r in rows if r.get("win"))
        rate = wins / n
        return {
            "win_rate": rate,
            "wins": wins,
            "losses": n - wins,
            "samples": n,
            "label": f"{rate * 100:.1f}% ({wins}/{n})",
            "asset_class": asset_class or "ALL",
        }

    def expectancy(self, *, asset_class: Optional[str] = None) -> Optional[float]:
        rows = [r for r in self.closed_trades(asset_class=asset_class) if r.get("pnl_pct") is not None]
        if not rows:
            return None
        return sum(float(r["pnl_pct"]) for r in rows) / len(rows)

    def summary_report(self) -> str:
        lines = ["PERFORMANCE LEDGER"]
        for label, ac in (("Overall", None), ("Stocks", ASSET_STOCK), ("Day trades", ASSET_DAY_TRADE), ("Kalshi", ASSET_KALSHI)):
            wr = self.win_rate(asset_class=ac)
            lines.append(f"  {label}: {wr['label']} | open={len(self.open_trades(asset_class=ac))}")
        exp = self.expectancy()
        if exp is not None:
            lines.append(f"  Expectancy (pnl%): {exp * 100:+.2f}%")
        return "\n".join(lines)

    def winning_setups(self, *, limit: int = 50) -> List[Dict[str, Any]]:
        wins = [r for r in self._closed if r.get("win") is True]
        wins.sort(key=lambda r: float(r.get("pnl_pct") or 0), reverse=True)
        return wins[:limit]


_LEDGER: Optional[TradePerformanceLedger] = None


def get_trade_performance_ledger() -> TradePerformanceLedger:
    global _LEDGER
    if _LEDGER is None:
        _LEDGER = TradePerformanceLedger()
    return _LEDGER
