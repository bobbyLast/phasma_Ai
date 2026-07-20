"""Virtual Kalshi book — research P&L with news context + weather fact-check."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from core.runtime_paths import engine_state_path
from utils.trade_performance_ledger import ASSET_KALSHI, get_trade_performance_ledger
from utils.weather_factcheck import evaluate_settlement, forecast_snapshot


def _news_fingerprint(news_items: List[Dict[str, Any]], limit: int = 5) -> str:
    parts = []
    for item in news_items[:limit]:
        title = str(item.get("title") or "").strip()
        if title:
            parts.append(title[:80])
    return " | ".join(parts)


def _weather_related_news(news_items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    keys = ("weather", "temperature", "storm", "hurricane", "rain", "snow", "heat", "cold", "flood")
    out = []
    for item in news_items or []:
        blob = f"{item.get('title', '')} {item.get('summary', '')}".lower()
        if any(k in blob for k in keys):
            out.append(item)
    return out


class KalshiVirtualBook:
    """Open virtual Kalshi bets from cycle signals; settle via API result or weather truth."""

    def __init__(self, path: Optional[str] = None):
        self.path = path or engine_state_path("kalshi_virtual_book.json")
        self.state: Dict[str, Any] = {"open": {}, "settled_count": 0}
        self._load()

    def _load(self) -> None:
        if not os.path.exists(self.path):
            return
        try:
            with open(self.path, "r", encoding="utf-8") as fh:
                self.state = json.load(fh)
        except (OSError, json.JSONDecodeError):
            self.state = {"open": {}, "settled_count": 0}

    def _save(self) -> None:
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        try:
            with open(self.path, "w", encoding="utf-8") as fh:
                json.dump(self.state, fh, indent=2, default=str)
        except OSError:
            pass

    def open_from_opportunity(
        self,
        opportunity: Dict[str, Any],
        *,
        news_items: Optional[List[Dict[str, Any]]] = None,
    ) -> Optional[str]:
        conf = opportunity.get("confidence", 0)
        try:
            conf_f = float(conf or 0)
        except (TypeError, ValueError):
            conf_f = 0.0
        if conf_f <= 0:
            return None
        signal = opportunity.get("kalshi_signal") or opportunity.get("action")
        if not signal:
            return None

        symbol = str(opportunity.get("symbol") or opportunity.get("ticker") or "").upper()
        if not symbol:
            return None
        # Dedup open by symbol
        for tid, row in (self.state.get("open") or {}).items():
            if str(row.get("symbol") or "").upper() == symbol:
                return tid

        news_items = news_items or []
        weather_news = _weather_related_news(news_items)
        title = str(opportunity.get("title") or opportunity.get("market_title") or "")
        market = opportunity.get("kalshi_market_data") or {}
        if isinstance(market, dict) and market.get("title"):
            title = market.get("title") or title

        weather_forecast = None
        title_l = title.lower()
        if any(w in title_l for w in ("temp", "°", "weather", "high ", "low ")) or "HIGH" in symbol or "TEMP" in symbol:
            weather_forecast = forecast_snapshot(title, symbol)

        ledger = get_trade_performance_ledger()
        payload = {
            "symbol": symbol,
            "ticker": symbol,
            "action": signal,
            "kalshi_signal": signal,
            "confidence": conf_f,
            "source": "kalshi_prediction",
            "asset_class": ASSET_KALSHI,
            "prediction_market": "kalshi",
            "title": title,
            "market_title": title,
            "implied_probability": opportunity.get("prediction_probability")
            or opportunity.get("implied_probability"),
            "entry_price": opportunity.get("prediction_probability")
            or opportunity.get("implied_probability")
            or opportunity.get("current_price"),
            "trade_link": opportunity.get("trade_link"),
            "sector": "Prediction Markets",
            "catalyst_type": "weather" if weather_forecast else "prediction",
            "news_fingerprint": _news_fingerprint(weather_news or news_items),
            "weather_forecast": weather_forecast,
            "setup_tags": ["kalshi_virtual", "weather" if weather_forecast else "event"],
        }
        trade_id = ledger.record_open(payload, virtual=True)
        self.state.setdefault("open", {})[trade_id] = {
            "trade_id": trade_id,
            "symbol": symbol,
            "side": signal,
            "opened_at": datetime.now(timezone.utc).isoformat(),
            "weather_forecast": weather_forecast,
            "title": title,
        }
        self._save()
        return trade_id

    def settle_pending(self, kalshi_engine: Any = None) -> List[Dict[str, Any]]:
        """Attempt to settle open virtual bets via weather fact-check or Kalshi market status."""
        ledger = get_trade_performance_ledger()
        settled: List[Dict[str, Any]] = []
        open_copy = dict(self.state.get("open") or {})
        for trade_id, row in open_copy.items():
            win = None
            details: Dict[str, Any] = {}
            exit_price = 0.0
            weather_actual = None
            weather_correct = None

            wf = row.get("weather_forecast")
            if wf:
                win, details = evaluate_settlement(wf, side=str(row.get("side") or "BUY_YES"))
                weather_actual = details.get("weather_actual_high_f")
                weather_correct = details.get("weather_correct")
                if win is True:
                    exit_price = 1.0
                elif win is False:
                    exit_price = 0.0

            if win is None and kalshi_engine is not None:
                try:
                    ticker = row.get("symbol")
                    getter = getattr(kalshi_engine, "_get", None)
                    market = None
                    if callable(getter):
                        market = getter(f"markets/{ticker}")
                    if isinstance(market, dict):
                        status = str(market.get("status") or "").lower()
                        result = market.get("result") or market.get("settlement_value")
                        if status in ("settled", "finalized", "closed") and result is not None:
                            # YES settled → 1, NO → 0 typically
                            res_s = str(result).upper()
                            yes_won = res_s in ("YES", "1", "TRUE")
                            side = str(row.get("side") or "BUY_YES").upper()
                            win = yes_won if "YES" in side else (not yes_won)
                            exit_price = 1.0 if win else 0.0
                            details["settled_result"] = result
                except Exception:
                    pass

            if win is None:
                continue

            close_row = ledger.record_close(
                trade_id,
                exit_price=exit_price,
                win=win,
                reason="kalshi_virtual_settle",
                weather_actual=weather_actual,
                weather_correct=weather_correct,
                settled_result=details.get("settled_result"),
            )
            if close_row:
                settled.append(close_row)
                self.state["open"].pop(trade_id, None)
                self.state["settled_count"] = int(self.state.get("settled_count") or 0) + 1
        self._save()
        return settled

    def win_rate_label(self) -> str:
        wr = get_trade_performance_ledger().win_rate(asset_class=ASSET_KALSHI)
        return wr.get("label") or "n/a"


_BOOK: Optional[KalshiVirtualBook] = None


def get_kalshi_virtual_book() -> KalshiVirtualBook:
    global _BOOK
    if _BOOK is None:
        _BOOK = KalshiVirtualBook()
    return _BOOK
