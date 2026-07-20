"""Central discovery limits for normal vs max_discovery mode."""

from typing import Any, Dict, Optional, Union

ConfigLike = Union[Dict[str, Any], Any]

# Conservative defaults (max_discovery=false)
_NORMAL = {
    "news_symbol_limit": 25,
    "prediction_market_limit": 25,
    "news_cache_minutes": 5,
    "market_cache_minutes": 10,
    "cache_prefetch_symbols": 20,
    "underground_signal_cap": 20,
    "partnership_symbol_scan": 3,
    "social_reddit_limit": 10,
    "news_articles_per_api": 10,
    "news_entries_per_rss": 5,
    "day_trade_dynamic_limit": 20,
    "day_trade_momentum_limit": 30,
    "heavy_mover_limit": 10,
    "fresh_opportunity_limit": 25,
    "kalshi_priority_series": 20,
    "intelligence_timeouts": {
        "universal_opportunities": 180,
        "bull_runs": 180,
        "hot_stocks": 180,
        "social_signals": 60,
        "partnership_opportunities": 90,
        "underground_stocks": 120,
    },
}

# Competitive discovery — cast a wide net across news + liquid US names
_MAX = {
    "news_symbol_limit": 250,
    "prediction_market_limit": 150,
    "news_cache_minutes": 2,
    "market_cache_minutes": 5,
    "cache_prefetch_symbols": 120,
    "underground_signal_cap": 80,
    "partnership_symbol_scan": 25,
    "social_reddit_limit": 50,
    "news_articles_per_api": 25,
    "news_entries_per_rss": 15,
    "day_trade_dynamic_limit": 80,
    "day_trade_momentum_limit": 80,
    "heavy_mover_limit": 30,
    "fresh_opportunity_limit": 100,
    "kalshi_priority_series": 80,
    "intelligence_timeouts": {
        "universal_opportunities": 420,
        "bull_runs": 420,
        "hot_stocks": 420,
        "social_signals": 180,
        "partnership_opportunities": 240,
        "underground_stocks": 300,
    },
}


def _config_get(config: ConfigLike, key: str, default: Any = None) -> Any:
    if config is None:
        return default
    if hasattr(config, "get"):
        return config.get(key, default)
    if isinstance(config, dict):
        return config.get(key, default)
    return getattr(config, key, default)


def is_max_discovery(config: ConfigLike) -> bool:
    return bool(_config_get(config, "max_discovery", False))


def discovery_limit(config: ConfigLike, key: str, default: Any = None) -> Any:
    """Return a limit value for the active discovery mode."""
    base = _MAX if is_max_discovery(config) else _NORMAL
    mode_key = "max" if is_max_discovery(config) else "normal"
    overrides = _config_get(config, "discovery_limits", {}) or {}
    mode_overrides = overrides.get(mode_key, {}) if isinstance(overrides, dict) else {}
    if key in mode_overrides:
        return mode_overrides[key]
    if key in base:
        return base[key]
    return default


def intelligence_timeout(config: ConfigLike, task_name: str) -> int:
    timeouts = discovery_limit(config, "intelligence_timeouts", {})
    if isinstance(timeouts, dict) and task_name in timeouts:
        return int(timeouts[task_name])
    fallback = _MAX if is_max_discovery(config) else _NORMAL
    return int(fallback["intelligence_timeouts"].get(task_name, 120))
