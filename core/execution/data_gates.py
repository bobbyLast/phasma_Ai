"""Hard data-quality and safety gates before any trade submission."""

from __future__ import annotations

import logging
import os
import re
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Tuple

from utils.company_resolver import is_placeholder
from utils.prediction_market_filters import kalshi_intel_only, post_prediction_trades_enabled
from core.source_status import signal_uses_fake_price

logger = logging.getLogger(__name__)

_PLACEHOLDER_KEY_PATTERNS = (
    re.compile(r"^your_.*_here$", re.I),
    re.compile(r"^YOUR_.*_KEY$"),
)


def is_placeholder_api_key(value: Any) -> bool:
    if value is None:
        return True
    text = str(value).strip()
    if is_placeholder(text):
        return True
    for pattern in _PLACEHOLDER_KEY_PATTERNS:
        if pattern.match(text):
            return True
    return False


def audit_api_keys(config: dict) -> Dict[str, str]:
    """Return map of api_name -> disabled reason for placeholder keys."""
    disabled: Dict[str, str] = {}
    apis = config.get("apis", {}) or {}
    for name, entry in apis.items():
        if not isinstance(entry, dict):
            continue
        key = entry.get("api_key", "")
        if is_placeholder_api_key(key):
            disabled[name] = "placeholder_api_key"
            logger.info("API %s disabled: placeholder key", name)
    for section in ("geopolitical_analysis", "unusual_whales", "sports_betting"):
        block = config.get(section, {}) or {}
        key = block.get("api_key") or block.get("news_api_key")
        if key and is_placeholder_api_key(key):
            disabled[section] = "placeholder_api_key"
            logger.info("%s disabled: placeholder key", section)
    return disabled


def _parse_timestamp(ts: Any) -> Optional[datetime]:
    if ts is None:
        return None
    if isinstance(ts, datetime):
        return ts if ts.tzinfo else ts.replace(tzinfo=timezone.utc)
    try:
        text = str(ts).replace("Z", "+00:00")
        dt = datetime.fromisoformat(text)
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    except (TypeError, ValueError):
        return None


def _data_age_seconds(price_timestamp: Any) -> Optional[float]:
    ts = _parse_timestamp(price_timestamp)
    if ts is None:
        return None
    now = datetime.now(timezone.utc)
    return (now - ts).total_seconds()


def validate_execution_gates(
    signal: Dict[str, Any],
    config: dict,
    *,
    trade_memory=None,
    posted_signals: Optional[set] = None,
    signal_key: Optional[str] = None,
) -> Tuple[bool, str, Dict[str, Any]]:
    """
    Run all pre-execution gates.

    Returns (passed, reason, details).
    """
    details: Dict[str, Any] = {}
    exec_cfg = config.get("execution", {}) or {}

    symbol = str(signal.get("symbol") or "").upper().strip()
    is_kalshi = (
        symbol.startswith("KX")
        or bool(signal.get("kalshi_signal"))
        or str(signal.get("source") or "").lower() in ("kalshi_prediction", "kalshi")
        or str(signal.get("trade_type") or "").upper() in ("KALSHI_PREDICTION", "PREDICTION_MARKET")
        or bool(signal.get("prediction_market"))
    )
    # Virtual Kalshi Telegram trades are allowed without live Kalshi API orders
    kalshi_virtual_ok = post_prediction_trades_enabled(config) and not exec_cfg.get(
        "kalshi_execution_enabled", False
    )

    if exec_cfg.get("require_valid_symbol", True):
        if is_kalshi:
            if kalshi_intel_only(config) and not kalshi_virtual_ok:
                return False, "kalshi_intel_only", {"symbol": symbol}
            if not symbol:
                return False, "invalid_symbol", {"symbol": symbol}
            # KX tickers are longer than 6 chars — do not apply equity length rule
        elif not symbol or len(symbol) > 6:
            return False, "invalid_symbol", {"symbol": symbol}

    if is_kalshi and kalshi_intel_only(config) and not kalshi_virtual_ok:
        if not exec_cfg.get("kalshi_execution_enabled", False):
            return False, "kalshi_intel_only", {"symbol": symbol}

    action = str(signal.get("action") or "").upper()
    if not action or action in ("HOLD", "NONE", "WATCH"):
        return False, "missing_side", {"action": action}

    trade_type = str(signal.get("trade_type") or "STOCK").upper()
    supported = {"STOCK", "CRYPTO", "OPTION", "OPTIONS", "KALSHI_PREDICTION", "PREDICTION_MARKET", "KALSHI"}
    if trade_type not in supported and not symbol.endswith("USD") and not is_kalshi:
        return False, "unsupported_trade_type", {"trade_type": trade_type}

    confidence = signal.get("confidence", 0)
    if isinstance(confidence, (int, float)) and confidence > 1:
        confidence = confidence / 100.0
    if confidence is None or confidence <= 0:
        return False, "missing_confidence", {}
    details["confidence"] = confidence

    current_price = signal.get("current_price")
    if current_price is None:
        current_price = signal.get("entry_price")
    try:
        current_price = float(current_price) if current_price is not None else None
    except (TypeError, ValueError):
        current_price = None

    if exec_cfg.get("require_price", True):
        if current_price is None or current_price <= 0:
            return False, "missing_price", {"current_price": current_price}

    if not is_kalshi and signal_uses_fake_price(signal):
        return False, "fake_price_source", {"symbol": symbol}

    price_ts = signal.get("price_timestamp") or signal.get("data_timestamp")
    data_age = _data_age_seconds(price_ts)
    details["data_age_seconds"] = data_age
    details["price_source"] = signal.get("price_source", "unknown")

    if exec_cfg.get("require_fresh_data", True) and data_age is not None:
        max_age = int(exec_cfg.get("max_data_age_seconds", 900))
        if data_age > max_age:
            return False, "stale_price", {"data_age_seconds": data_age, "max_age": max_age}

    position_size = signal.get("position_size")
    quantity = signal.get("quantity") or signal.get("shares_to_buy")
    if position_size is None and quantity is None and current_price:
        position_size = signal.get("position_cost")
    if position_size is None and quantity is None:
        return False, "position_sizing_failed", {}

    if trade_memory is not None and symbol and trade_memory.is_recently_traded(symbol):
        return False, "recently_traded", {"symbol": symbol}

    if posted_signals is not None and signal_key and signal_key in posted_signals:
        return False, "duplicate_signal", {"signal_key": signal_key}

    details["symbol"] = symbol
    details["current_price"] = current_price
    details["action"] = action
    return True, "passed", details


class GateResult:
    """Result of data-quality gate validation."""

    def __init__(self, passed: bool, reason: str, alert_label: str = "", details: Optional[Dict] = None):
        self.passed = passed
        self.reason = reason
        self.alert_label = alert_label
        self.details = details or {}

    @classmethod
    def ok(cls) -> "GateResult":
        return cls(True, "passed")

    @classmethod
    def fail(cls, reason: str, alert_label: str = "", details: Optional[Dict] = None) -> "GateResult":
        label = alert_label or f"NO TRADE — {reason.replace('_', ' ')}"
        return cls(False, reason, label, details)


class DataQualityGates:
    """Pre-execution validation gates."""

    def __init__(self, config: dict, trade_memory=None):
        self.config = config
        self.trade_memory = trade_memory

    def validate(self, signal: Dict[str, Any], *, posted_keys: Optional[set] = None) -> GateResult:
        signal_key = signal.get("dedup_key")
        passed, reason, details = validate_execution_gates(
            signal,
            self.config,
            trade_memory=self.trade_memory,
            posted_signals=posted_keys,
            signal_key=signal_key,
        )
        if passed:
            signal["data_age_seconds"] = details.get("data_age_seconds")
            signal["price_source"] = details.get("price_source", signal.get("price_source"))
            return GateResult.ok()
        alert_labels = {
            "missing_price": "NO TRADE — missing price",
            "stale_price": "NO TRADE — stale price",
            "kalshi_intel_only": "NO TRADE — Kalshi intel-only",
            "recently_traded": "NO TRADE — recently traded",
            "duplicate_signal": "NO TRADE — duplicate signal",
        }
        return GateResult.fail(reason, alert_labels.get(reason, ""), details)
