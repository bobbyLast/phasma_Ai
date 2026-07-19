"""Safe display helpers — missing fields must not crash cycles."""

from __future__ import annotations

from typing import Any, Dict, Optional, Union

SignalLike = Union[Dict[str, Any], Any]


def as_dict(signal: SignalLike) -> Dict[str, Any]:
    if isinstance(signal, dict):
        return signal
    if hasattr(signal, "__dict__"):
        return dict(vars(signal))
    return {}


def safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def safe_str(value: Any, default: str = "unknown") -> str:
    if value is None:
        return default
    text = str(value).strip()
    return text if text else default


def entry_action(signal: SignalLike) -> str:
    et = as_dict(signal).get("entry_timing")
    if isinstance(et, dict):
        return safe_str(et.get("recommended_action"), "N/A")
    return "N/A"


def exit_stop_label(signal: SignalLike) -> str:
    et = as_dict(signal).get("exit_timing")
    if isinstance(et, dict):
        stop = safe_float(et.get("stop_loss"), -1.0)
        if stop >= 0:
            return f"{stop:.1%}"
    return "N/A"


def position_size_label(signal: SignalLike) -> str:
    size = safe_float(as_dict(signal).get("position_size"), -1.0)
    if size < 0:
        return "N/A"
    return f"${size:.0f}"


def win_rate_label(sim_win_pct: float) -> str:
    if sim_win_pct and sim_win_pct > 0:
        return f"1 in {100 / sim_win_pct:.1f} trades"
    return "N/A (sim win rate 0%)"


def rationale_text(signal: SignalLike) -> str:
    return safe_str(as_dict(signal).get("rationale"), "unknown")


def patterns_text(signal: SignalLike) -> str:
    patterns = as_dict(signal).get("patterns") or []
    if isinstance(patterns, (list, tuple)):
        cleaned = [str(p) for p in patterns if p]
        return ", ".join(cleaned) if cleaned else "N/A"
    return safe_str(patterns, "N/A")
