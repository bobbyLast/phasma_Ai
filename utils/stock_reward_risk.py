"""Stock reward-to-risk helpers — minimum 5:1 angle ($1 risk → $5 upside)."""

from __future__ import annotations

from typing import Any, Dict, Optional, Tuple


DEFAULT_MIN_REWARD_RISK = 5.0


def min_reward_risk_ratio(config: Any = None) -> float:
    if config is None:
        return DEFAULT_MIN_REWARD_RISK
    data = config.data if hasattr(config, "data") else config
    if not isinstance(data, dict):
        if hasattr(config, "get"):
            stock = config.get("stock_trading") or {}
            if isinstance(stock, dict) and stock.get("min_reward_risk_ratio") is not None:
                return float(stock["min_reward_risk_ratio"])
        return DEFAULT_MIN_REWARD_RISK
    stock = data.get("stock_trading") or {}
    if isinstance(stock, dict) and stock.get("min_reward_risk_ratio") is not None:
        return float(stock["min_reward_risk_ratio"])
    return DEFAULT_MIN_REWARD_RISK


def compute_reward_risk(
    entry: Any,
    stop: Any,
    target: Any,
) -> Optional[float]:
    try:
        e = float(entry)
        s = float(stop)
        t = float(target)
    except (TypeError, ValueError):
        return None
    risk = abs(e - s)
    reward = abs(t - e)
    if risk <= 0:
        return None
    return reward / risk


def apply_stock_rr_targets(
    signal: Dict[str, Any],
    *,
    config: Any = None,
    stop_pct: float = 0.05,
    invent_target: bool = False,
) -> Dict[str, Any]:
    """Ensure entry/stop/target and reward_risk_ratio on a stock signal.

    If invent_target is False and existing target cannot meet min R:R, mark
    ``rr_gate_failed`` instead of fabricating an unrealistic target.
    """
    min_rr = min_reward_risk_ratio(config)
    try:
        entry = float(
            signal.get("entry_price")
            or signal.get("current_price")
            or signal.get("price")
            or 0
        )
    except (TypeError, ValueError):
        entry = 0.0
    if entry <= 0:
        signal["rr_gate_failed"] = True
        signal["rr_fail_reason"] = "missing entry"
        return signal

    action = str(signal.get("action") or "BUY").upper()
    is_short = action in ("SELL", "SHORT", "BUY_PUT")

    stop = signal.get("stop_loss") or signal.get("stop_price") or signal.get("stop")
    target = signal.get("target_price") or signal.get("take_profit") or signal.get("target")

    try:
        stop_f = float(stop) if stop is not None else None
    except (TypeError, ValueError):
        stop_f = None
    try:
        target_f = float(target) if target is not None else None
    except (TypeError, ValueError):
        target_f = None

    if stop_f is None or stop_f <= 0:
        if is_short:
            stop_f = entry * (1.0 + stop_pct)
        else:
            stop_f = entry * (1.0 - stop_pct)
        signal["stop_loss"] = round(stop_f, 4)
        signal["stop_price"] = round(stop_f, 4)

    rr = compute_reward_risk(entry, stop_f, target_f) if target_f else None
    if rr is not None and rr + 1e-9 >= min_rr:
        signal["reward_risk_ratio"] = round(rr, 2)
        signal["risk_reward_ratio"] = round(rr, 2)
        signal["rr_gate_failed"] = False
        return signal

    # Need a target at min_rr from stop distance
    risk = abs(entry - float(stop_f))
    needed_target = entry + (min_rr * risk) if not is_short else entry - (min_rr * risk)

    # Catalyst / expected move check — do not invent if signal already has a weaker target
    if target_f is not None and not invent_target:
        signal["reward_risk_ratio"] = round(rr or 0.0, 2)
        signal["risk_reward_ratio"] = round(rr or 0.0, 2)
        signal["rr_gate_failed"] = True
        signal["rr_fail_reason"] = f"reward:risk {rr:.2f} < {min_rr:.1f} required"
        return signal

    # Size target to exactly min_rr when no honest target was provided
    signal["target_price"] = round(needed_target, 4)
    signal["reward_risk_ratio"] = round(min_rr, 2)
    signal["risk_reward_ratio"] = round(min_rr, 2)
    signal["rr_gate_failed"] = False
    signal["rr_sized_to_min"] = True
    return signal


def passes_stock_rr_gate(signal: Any, config: Any = None) -> Tuple[bool, str]:
    """Return (ok, reason) for DecisionPipeline stock R:R gate."""
    min_rr = min_reward_risk_ratio(config)
    if isinstance(signal, dict):
        sig = signal
    elif hasattr(signal, "__dict__"):
        sig = vars(signal)
    else:
        return False, "invalid signal"

    asset = str(sig.get("asset_type") or sig.get("trade_type") or "STOCK").upper()
    if "KALSHI" in asset or sig.get("prediction_market"):
        return True, "kalshi_skip"
    if "OPTION" in asset and (sig.get("strike") or sig.get("option_type")):
        return True, "options_skip"

    apply_stock_rr_targets(sig, config=config, invent_target=False)
    if sig.get("rr_gate_failed"):
        return False, str(sig.get("rr_fail_reason") or "below min reward:risk")

    rr = compute_reward_risk(
        sig.get("entry_price") or sig.get("current_price"),
        sig.get("stop_loss") or sig.get("stop_price"),
        sig.get("target_price"),
    )
    if rr is None:
        return False, "missing entry/stop/target"
    if rr + 1e-9 < min_rr:
        return False, f"reward:risk {rr:.2f} < {min_rr:.1f}"
    return True, f"{rr:.2f}:1"
