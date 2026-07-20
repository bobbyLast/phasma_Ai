"""Source honesty and demo-data firewall."""

from __future__ import annotations

from typing import Any, Dict, Set

DEMO_SOURCES: Set[str] = {
    "demo",
    "sample",
    "demonstration",
    "geopolitical_demo",
    "politician_sample",
    "simulated",
    "mock",
    "test_fixture",
}

DEMO_SOURCE_PREFIXES = ("demo_", "sample_")

FAKE_PRICE_SOURCES: Set[str] = {
    "simulated",
    "mock",
    "demo",
    "fake",
    "test",
    "sample",
    "placeholder",
}


def is_demo_geo_event(event: Dict[str, Any]) -> bool:
    """True for synthetic/demo geopolitical events."""
    if not isinstance(event, dict):
        return False
    if event.get("is_demo") or event.get("demo_only"):
        return True
    source = str(event.get("source") or "").strip().lower()
    if source in ("geopolitical_demo", "geopolitical_monitor_demo", "demo"):
        return True
    if source.startswith("geopolitical_demo"):
        return True
    return is_demo_source(source)


def block_demo_geo_from_decision(event: Dict[str, Any], config: Dict[str, Any]) -> bool:
    """Return True if demo geo must not reach DecisionGroup."""
    if demo_allowed_in_pipeline(config):
        return False
    return is_demo_geo_event(event)


def normalize_demo_config(config: Dict[str, Any]) -> Dict[str, Any]:
    raw = dict(config.get("demo_data") or {})
    return {
        "allow_in_live_pipeline": bool(raw.get("allow_in_live_pipeline", False)),
    }


def is_demo_source(source: Any) -> bool:
    if not source:
        return False
    text = str(source).strip().lower()
    if text in DEMO_SOURCES:
        return True
    return any(text.startswith(prefix) for prefix in DEMO_SOURCE_PREFIXES)


def demo_allowed_in_pipeline(config: Dict[str, Any]) -> bool:
    return normalize_demo_config(config).get("allow_in_live_pipeline", False)


def is_fake_price_source(source: Any) -> bool:
    if not source:
        return False
    text = str(source).strip().lower()
    if text in FAKE_PRICE_SOURCES:
        return True
    return is_demo_source(text)


def signal_uses_fake_price(signal: Dict[str, Any]) -> bool:
    """True when price metadata indicates simulated/mock/demo data."""
    if not isinstance(signal, dict):
        return False
    for key in ("source", "price_source", "_price_source", "data_source", "market_data_source"):
        if is_fake_price_source(signal.get(key)):
            return True
    if signal.get("is_demo") or signal.get("demo_only"):
        return True
    return False


def block_demo_signal(signal: Dict[str, Any], config: Dict[str, Any]) -> bool:
    """Return True if demo signal must be blocked from trade pipeline."""
    if demo_allowed_in_pipeline(config):
        return False
    source = signal.get("source") or getattr(signal, "source", "")
    if is_demo_source(source):
        return True
    if signal.get("is_demo") or signal.get("demo_only"):
        return True
    return False
