"""Central config for per-share max price filtering."""

from typing import Any, Dict, Optional, Tuple

DEFAULT_MAX_PRICE = 10000.0


def _as_dict(config: Any) -> Dict:
    if config is None:
        return {}
    if isinstance(config, dict):
        return config
    if hasattr(config, "get") and callable(getattr(config, "get")):
        try:
            return dict(config)
        except (TypeError, ValueError):
            pass
    return getattr(config, "__dict__", {}) or {}


def resolve_price_filter(config: Any) -> Tuple[bool, Optional[float]]:
    """Return (enabled, max_price). When disabled, max_price is None."""
    cfg = _as_dict(config)
    enabled = cfg.get("price_filter_enabled")
    if enabled is None:
        enabled = False

    if not enabled:
        return False, None

    max_price = cfg.get("max_stock_price")
    if max_price is None:
        max_price = cfg.get("trading_budget", {}).get("max_price_per_share")
    if max_price is None:
        active = cfg.get("strategies", {}).get("active_strategy", "penny_moonshot")
        max_price = cfg.get("strategies", {}).get(active, {}).get("max_price")
    if max_price is None:
        max_price = DEFAULT_MAX_PRICE
    return True, float(max_price)


def apply_price_threshold(config: Any, target: Any) -> None:
    """Set price_filter_enabled and price_threshold on a component instance."""
    enabled, cap = resolve_price_filter(config)
    target.price_filter_enabled = enabled
    target.price_threshold = cap


def exceeds_price_cap(price: Any, config: Any) -> bool:
    enabled, cap = resolve_price_filter(config)
    if not enabled or cap is None:
        return False
    try:
        return float(price) > cap
    except (TypeError, ValueError):
        return False


def within_price_cap(price: Any, config: Any) -> bool:
    return not exceeds_price_cap(price, config)


def max_price_label(config: Any) -> str:
    enabled, cap = resolve_price_filter(config)
    if not enabled:
        return "disabled"
    return f"${cap:,.0f}"
