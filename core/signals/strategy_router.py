"""Route signals to appropriate strategy profiles."""

from __future__ import annotations

import re
from typing import Any, Dict, Optional, Set

MEGA_LARGE_CAP: Set[str] = {
    "AAPL", "MSFT", "GOOGL", "GOOG", "AMZN", "NVDA", "TSLA", "META", "BRK.A", "BRK.B",
    "JPM", "V", "UNH", "XOM", "LLY", "AVGO", "MA", "HD", "PG", "COST", "JNJ", "MRK",
    "ABBV", "PEP", "KO", "WMT", "BAC", "CRM", "NFLX", "AMD", "INTC", "QQQ", "SPY", "IWM",
    "DIA", "VOO", "VTI",
}

CRYPTO_SYMBOLS: Set[str] = {
    "BTC", "BTC-USD", "ETH", "ETH-USD", "SOL", "SOL-USD", "DOGE", "DOGE-USD",
    "XRP", "XRP-USD", "ADA", "ADA-USD", "BNB", "BNB-USD",
}

STRATEGY_PENNY_MOONSHOT = "penny_moonshot"
STRATEGY_LARGE_CAP_OPTIONS = "large_cap_unusual_options"
STRATEGY_SWING_NEWS = "swing_news"
STRATEGY_THEMATIC = "thematic_watchlist"
STRATEGY_SOCIAL = "social_trend_watchlist"
STRATEGY_KALSHI = "kalshi_intel"
STRATEGY_CRYPTO = "crypto_watchlist"
STRATEGY_OPTIONS = "options_contract"
STRATEGY_UNKNOWN = "unknown"


def _sym(signal: Any) -> str:
    if isinstance(signal, dict):
        return str(signal.get("symbol") or signal.get("ticker") or "").upper().strip()
    return str(getattr(signal, "symbol", None) or getattr(signal, "ticker", "") or "").upper().strip()


def _source(signal: Any) -> str:
    if isinstance(signal, dict):
        return str(signal.get("source") or "").lower()
    return str(getattr(signal, "source", "") or "").lower()


def is_crypto_symbol(symbol: str) -> bool:
    sym = symbol.upper().strip()
    if sym in CRYPTO_SYMBOLS:
        return True
    return sym.endswith("-USD") and sym.split("-")[0] in {"BTC", "ETH", "SOL", "DOGE", "XRP", "ADA", "BNB"}


def has_option_contract_fields(signal: Any) -> bool:
    """True only when strike, expiry, and contract type are present."""
    if isinstance(signal, dict):
        strike = signal.get("strike") or signal.get("strike_price")
        expiry = signal.get("expiration_date") or signal.get("expiry") or signal.get("days_to_expiry")
        action = str(signal.get("action") or "").upper()
        contract = signal.get("contract_type") or signal.get("option_type")
    else:
        strike = getattr(signal, "strike", None) or getattr(signal, "strike_price", None)
        expiry = getattr(signal, "expiration_date", None) or getattr(signal, "expiry", None) or getattr(signal, "days_to_expiry", None)
        action = str(getattr(signal, "action", "") or "").upper()
        contract = getattr(signal, "contract_type", None) or getattr(signal, "option_type", None)

    has_strike = strike is not None and float(strike or 0) > 0
    has_expiry = expiry is not None and str(expiry).strip() not in ("", "0", "None")
    has_contract = bool(contract) or ("CALL" in action or "PUT" in action)
    return has_strike and has_expiry and has_contract


def classify_asset_type(signal: Any) -> str:
    sym = _sym(signal)
    trade_type = ""
    if isinstance(signal, dict):
        trade_type = str(signal.get("trade_type") or "").upper()
    else:
        trade_type = str(getattr(signal, "trade_type", "") or "").upper()

    if trade_type == "KALSHI_PREDICTION" or sym.startswith("KX"):
        return "KALSHI"
    if is_crypto_symbol(sym):
        return "CRYPTO"
    if has_option_contract_fields(signal):
        return "OPTION"
    return "STOCK"


class StrategyRouter:
    """Assign strategy route; prevent penny rules on mega-caps."""

    def route(self, signal: Any) -> Dict[str, Any]:
        sym = _sym(signal)
        source = _source(signal)
        asset = classify_asset_type(signal)

        if asset == "KALSHI":
            return {"strategy": STRATEGY_KALSHI, "asset_type": asset, "watchlist_only": True}

        if asset == "CRYPTO":
            return {"strategy": STRATEGY_CRYPTO, "asset_type": asset, "watchlist_only": source in ("social_engine", "thematic_analysis")}

        if asset == "OPTION":
            return {"strategy": STRATEGY_OPTIONS, "asset_type": asset, "watchlist_only": False}

        price = None
        if isinstance(signal, dict):
            price = signal.get("current_price") or signal.get("entry_price")
        else:
            price = getattr(signal, "current_price", None) or getattr(signal, "entry_price", None)
        try:
            price_f = float(price) if price is not None else None
        except (TypeError, ValueError):
            price_f = None

        if sym in MEGA_LARGE_CAP:
            return {"strategy": STRATEGY_SWING_NEWS, "asset_type": "STOCK", "watchlist_only": False}

        if is_crypto_symbol(sym):
            return {"strategy": STRATEGY_CRYPTO, "asset_type": "CRYPTO", "watchlist_only": source in ("social_engine", "thematic_analysis")}

        if source in ("thematic_analysis",):
            return {"strategy": STRATEGY_THEMATIC, "asset_type": "STOCK", "watchlist_only": True}

        if source in ("social_engine", "social_trend"):
            return {"strategy": STRATEGY_SOCIAL, "asset_type": "STOCK", "watchlist_only": True}

        if source in ("unusual_whales", "options_flow") and sym in MEGA_LARGE_CAP:
            return {"strategy": STRATEGY_LARGE_CAP_OPTIONS, "asset_type": "STOCK", "watchlist_only": False}

        if price_f is not None and price_f < 5.0:
            return {"strategy": STRATEGY_PENNY_MOONSHOT, "asset_type": "STOCK", "watchlist_only": False}

        if source in ("news_engine", "unified_analysis", "news"):
            return {"strategy": STRATEGY_SWING_NEWS, "asset_type": "STOCK", "watchlist_only": False}

        return {"strategy": STRATEGY_SWING_NEWS, "asset_type": "STOCK", "watchlist_only": False}

    def confluence_required(self, strategy: str, config: Dict[str, Any]) -> bool:
        strategies = config.get("strategies") or {}
        active = strategies.get(strategies.get("active_strategy", "penny_moonshot"), {})
        if strategy == STRATEGY_PENNY_MOONSHOT:
            required = active.get("required_signals") or []
            return bool(required)
        if strategy in (STRATEGY_LARGE_CAP_OPTIONS, STRATEGY_SWING_NEWS):
            return False
        return strategy == STRATEGY_PENNY_MOONSHOT

    def penny_rules_apply(self, strategy: str, symbol: str) -> bool:
        if symbol.upper() in MEGA_LARGE_CAP:
            return False
        if is_crypto_symbol(symbol):
            return False
        return strategy == STRATEGY_PENNY_MOONSHOT
