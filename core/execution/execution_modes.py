"""Execution mode constants and normalization helpers."""

from __future__ import annotations

import logging
import os
import re
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

_PLACEHOLDER_KEY_PATTERNS = (
    re.compile(r"^your_.*_here$", re.I),
    re.compile(r"^YOUR_.*_KEY$"),
    re.compile(r"^placeholder$", re.I),
)


class ExecutionMode:
    OFF = "OFF"
    ALERT_ONLY = "ALERT_ONLY"
    PAPER_ALPACA = "PAPER_ALPACA"
    PAPER_INTERNAL = "PAPER_INTERNAL"
    LIVE_ALPACA = "LIVE_ALPACA"

    ALL = frozenset({OFF, ALERT_ONLY, PAPER_ALPACA, PAPER_INTERNAL, LIVE_ALPACA})
    SAFE_DEFAULTS = frozenset({OFF, ALERT_ONLY})


class ExecutionDecision:
    SKIPPED = "skipped"
    SUBMITTED = "submitted"
    FILLED = "filled"
    REJECTED = "rejected"


def _has_alpaca_paper_creds() -> bool:
    key = os.getenv("ALPACA_API_KEY") or os.getenv("ALPACA_KEY")
    secret = os.getenv("ALPACA_API_SECRET") or os.getenv("ALPACA_SECRET_KEY")
    base = os.getenv("ALPACA_BASE_URL", "https://paper-api.alpaca.markets")
    if not key or not secret:
        return False
    # Never treat live endpoint as paper credentials for auto-mapping
    if "api.alpaca.markets" in base and "paper" not in base:
        return False
    return True


def is_placeholder_api_key(value: Any) -> bool:
    if value is None:
        return True
    text = str(value).strip()
    if not text:
        return True
    if text in ("YOUR_FMP_KEY", "YOUR_POLYGON_KEY", "YOUR_UNUSUAL_WHALES_API_KEY"):
        return True
    for pat in _PLACEHOLDER_KEY_PATTERNS:
        if pat.match(text):
            return True
    return False


def normalize_execution_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize execution settings from explicit ``execution`` block and legacy keys.

    ``paper_trading.enabled`` is legacy — when ``execution.mode`` is set explicitly,
    it always wins over the legacy paper flag.
    Default is ALERT_ONLY — never silently enables live trading.
    """
    raw = dict(config.get("execution") or {})
    paper = config.get("paper_trading") or {}

    explicit_mode = str(raw.get("mode") or "").upper().strip()
    mode = explicit_mode if explicit_mode in ExecutionMode.ALL else ""

    legacy_paper_enabled = bool(paper.get("enabled", False))
    legacy_derived_mode: Optional[str] = None
    if not mode:
        if legacy_paper_enabled:
            if _has_alpaca_paper_creds():
                legacy_derived_mode = ExecutionMode.PAPER_ALPACA
            elif paper.get("track_ai_performance", True):
                legacy_derived_mode = ExecutionMode.PAPER_INTERNAL
            else:
                legacy_derived_mode = ExecutionMode.ALERT_ONLY
            mode = legacy_derived_mode
        else:
            mode = ExecutionMode.ALERT_ONLY

    allow_live = bool(raw.get("allow_live_trading", False))
    if mode == ExecutionMode.LIVE_ALPACA and not allow_live:
        mode = ExecutionMode.ALERT_ONLY

    if explicit_mode in ExecutionMode.ALL and legacy_paper_enabled and mode not in (
        ExecutionMode.PAPER_ALPACA,
        ExecutionMode.PAPER_INTERNAL,
    ):
        logger.info(
            "execution.mode=%s overrides legacy paper_trading.enabled=true",
            mode,
        )
    elif explicit_mode in ExecutionMode.ALL:
        logger.info(
            "execution.mode=%s (legacy paper_trading.enabled=%s)",
            mode,
            str(legacy_paper_enabled).lower(),
        )

    normalized = {
        "mode": mode,
        "allow_live_trading": allow_live,
        "kalshi_execution_enabled": bool(raw.get("kalshi_execution_enabled", False)),
        "require_price": bool(raw.get("require_price", True)),
        "require_valid_symbol": bool(raw.get("require_valid_symbol", True)),
        "require_fresh_data": bool(raw.get("require_fresh_data", True)),
        "max_data_age_seconds": int(raw.get("max_data_age_seconds", 900)),
        "min_confidence_threshold": float(
            raw.get("min_confidence_threshold")
            or paper.get("min_confidence_threshold", 55)
        ),
        "max_position_size": float(
            raw.get("max_position_size") or paper.get("max_position_size", 1000)
        ),
    }
    return normalized


def get_execution_mode(config: Dict[str, Any]) -> str:
    return normalize_execution_config(config)["mode"]


def format_execution_startup_message(config: Dict[str, Any]) -> str:
    """Human-readable startup line for execution mode vs legacy paper flag."""
    raw = dict(config.get("execution") or {})
    paper = config.get("paper_trading") or {}
    exec_cfg = normalize_execution_config(config)
    mode = exec_cfg["mode"]
    legacy = bool(paper.get("enabled", False))
    explicit_mode = str(raw.get("mode") or "").upper().strip()
    if explicit_mode in ExecutionMode.ALL:
        return (
            f"Execution mode: {mode} "
            f"(overrides legacy paper_trading.enabled={str(legacy).lower()})"
        )
    return f"Execution mode: {mode} (from legacy paper_trading.enabled={str(legacy).lower()})"
