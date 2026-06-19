"""Shared filters for prediction-market intel vs trade posts."""

from __future__ import annotations

import re
from datetime import datetime
from typing import Any, Dict, Optional, Union

_PREDICTION_VENUES = frozenset({"kalshi", "polymarket"})
_PREDICTION_SOURCES = frozenset({
    "kalshi_prediction",
    "kalshi",
    "polymarket",
    "prediction_market",
})
_PREDICTION_SIGNAL_TYPES = frozenset({
    "kalshi",
    "kalshi_prediction",
    "prediction",
    "prediction_market",
})
_PREDICTION_TRADE_TYPES = frozenset({"KALSHI_PREDICTION", "PREDICTION_MARKET"})


def _config_flag(config: Any, key: str, default: bool) -> bool:
    if config is None:
        return default
    if hasattr(config, "get"):
        return bool(config.get(key, default))
    return default


def kalshi_intel_only(config: Any) -> bool:
    """When True, prediction markets are intel-only (no Telegram trade posts)."""
    if _config_flag(config, "post_prediction_trades", False):
        return False
    return _config_flag(config, "kalshi_intel_only", True)


def post_prediction_trades_enabled(config: Any) -> bool:
    return _config_flag(config, "post_prediction_trades", False)


def is_prediction_market_item(item: Dict[str, Any]) -> bool:
    venue = str(item.get("prediction_market") or "").lower()
    if venue in _PREDICTION_VENUES:
        return True
    source = str(item.get("source") or "").lower()
    if source in _PREDICTION_SOURCES:
        return True
    signal_type = str(item.get("signal_type") or "").lower()
    if signal_type in _PREDICTION_SIGNAL_TYPES:
        return True
    trade_type = str(item.get("trade_type") or "").upper()
    if trade_type in _PREDICTION_TRADE_TYPES:
        return True
    sym = str(item.get("symbol") or "").upper()
    if sym.startswith("KX"):
        return True
    if item.get("intel_only") or item.get("no_trade_post"):
        return True
    return False


def should_block_prediction_trade_post(config: Any, item: Union[Dict[str, Any], Any]) -> bool:
    """Return True if this signal must not be posted as a trade to Telegram."""
    if post_prediction_trades_enabled(config):
        return False
    if not kalshi_intel_only(config):
        return False
    if isinstance(item, dict):
        if item.get("no_trade_post") or item.get("intel_only"):
            return True
        return is_prediction_market_item(item)
    # Signal objects
    if getattr(item, "no_trade_post", False) or getattr(item, "intel_only", False):
        return True
    data = {
        "prediction_market": getattr(item, "prediction_market", None),
        "source": getattr(item, "source", None),
        "signal_type": getattr(item, "signal_type", None),
        "trade_type": getattr(item, "trade_type", None),
        "symbol": getattr(item, "symbol", None),
    }
    return is_prediction_market_item(data)


def _parse_year(value: Any) -> Optional[int]:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.year
    text = str(value)
    m = re.search(r"(20\d{2})", text)
    return int(m.group(1)) if m else None


def is_stale_prediction_market(
    market: Optional[Dict[str, Any]] = None,
    title: str = "",
    *,
    now: Optional[datetime] = None,
) -> bool:
    """Skip expired/old-year markets (e.g. 2024 titles when run in 2026)."""
    now = now or datetime.now()
    min_year = now.year - 1
    title_l = (title or "").lower()
    if now.year >= 2026 and "2024" in title_l:
        return True
    for stale_year in range(2020, min_year):
        if str(stale_year) in title_l and now.year > stale_year + 1:
            return True
    market = market or {}
    status = str(market.get("status") or "").lower()
    if status and status not in ("open", "active"):
        return True
    for field in (
        "close_time",
        "expiration_time",
        "expected_expiration_time",
        "latest_expiration_time",
    ):
        year = _parse_year(market.get(field))
        if year is not None and year < min_year:
            return True
    return False


def tag_intel_only_fields(item: Dict[str, Any], config: Any) -> Dict[str, Any]:
    """Mark prediction-market rows as intel-only when configured."""
    if is_prediction_market_item(item) and kalshi_intel_only(config):
        item["intel_only"] = True
        item["no_trade_post"] = True
    return item
