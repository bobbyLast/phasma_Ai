"""Units-based position sizing with zero-bankroll guard."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from utils.confidence_utils import normalize_confidence_to_pct


def apply_units_sizing(
    system: Any,
    signals: List[Dict[str, Any]],
    cfg: Any,
    *,
    status: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Apply units sizing or disable when bankroll <= 0."""
    if not signals:
        return {"sizing_status": "NO_SIGNALS", "bankroll": 0.0, "applied": 0}

    try:
        bankroll = float((status or {}).get("bankroll", cfg.get("bankroll", 2000)))
    except (TypeError, ValueError):
        bankroll = 0.0

    if bankroll <= 0:
        print("[UNITS] Sizing disabled: bankroll <= 0")
        for s in signals:
            s["position_size"] = 0
            s["units"] = 0
            s["sizing_status"] = "DISABLED_ZERO_BANKROLL"
            s["paper_eligible"] = False
            if not s.get("decision_status"):
                s["decision_status"] = "WATCHLIST_ONLY"
        return {
            "sizing_status": "DISABLED_ZERO_BANKROLL",
            "bankroll": bankroll,
            "applied": 0,
        }

    print(f"[UNITS SIZING] Calculating units-based positions for {len(signals)} signals...")
    system.unit_value = bankroll * (system.unit_size_percent / 100)
    system.standard_trade_size = system.unit_value * system.standard_units
    print(
        f"[UNITS SIZING] 1 Unit = ${system.unit_value:.2f} "
        f"({system.unit_size_percent}% of ${bankroll:.0f} bankroll)"
    )
    print(
        f"[UNITS SIZING] Standard Trade = {system.standard_units} units "
        f"= ${system.standard_trade_size:.2f}"
    )

    performance_scale = 1.0
    try:
        recent_pnl = float((status or {}).get("daily_pnl", 0.0) or 0.0)
        if recent_pnl <= 0:
            performance_scale = 0.5
        elif recent_pnl < bankroll * 0.01:
            performance_scale = 0.7
    except Exception:
        performance_scale = 0.5

    max_conf_pct = max(
        (normalize_confidence_to_pct(s.get("confidence", 0.0)) for s in signals),
        default=0.0,
    )
    if max_conf_pct <= 0:
        max_conf_pct = 100.0

    applied = 0
    for s in signals:
        raw_size = safe_float(s.get("position_size", 0.0))
        if raw_size <= 0:
            continue

        conf_pct = normalize_confidence_to_pct(s.get("confidence", 0.0))
        conf_weight = 0.5 + 0.5 * (conf_pct / max_conf_pct)
        units = max(system.min_units, min(system.max_units, round(conf_weight * system.standard_units)))
        position_size = units * system.unit_value * performance_scale

        symbol = str(s.get("symbol") or "N/A")
        s["position_size"] = position_size
        s["units"] = units
        s["sizing_status"] = "OK"
        applied += 1
        print(f"[UNITS] {symbol}: {units} units = ${position_size:.2f} (confidence {conf_pct:.0f}%)")

    return {
        "sizing_status": "OK",
        "bankroll": bankroll,
        "applied": applied,
    }


def safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default
