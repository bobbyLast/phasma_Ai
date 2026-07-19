"""Central discovery limits for normal vs max_discovery mode."""

from typing import Any, Dict, Optional, Union

ConfigLike = Union[Dict[str, Any], Any]

_NORMAL = {
    "news_symbol_limit": 25,
    "prediction_market_limit": 25,
    "news_cache_minutes": 5,
    "market_cache_minutes": 10,
    "cache_prefetch_symbols": 20,
    "underground_signal_cap": 20,
    "partnership_symbol_scan": 3,
    "social_reddit_limit": 10,
    "intelligence_timeouts": {
        "universal_opportunities": 180,
        "bull_runs": 180,
        "hot_stocks": 180,
        "social_signals": 60,
        "partnership_opportunities": 90,
        "underground_stocks": 120,
    },
}

_MAX = {
    "news_symbol_limit": 75,
    "prediction_market_limit": 75,
    "news_cache_minutes": 2,
    "market_cache_minutes": 5,
    "cache_prefetch_symbols": 50,
    "underground_signal_cap": 50,
    "partnership_symbol_scan": 15,
    "social_reddit_limit": 25,
    "intelligence_timeouts": {
        "universal_opportunities": 300,
        "bull_runs": 300,
        "hot_stocks": 300,
        "social_signals": 120,
        "partnership_opportunities": 180,
        "underground_stocks": 240,
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
