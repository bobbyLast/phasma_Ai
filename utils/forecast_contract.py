"""Horizon-explicit calibrated forecast contract for trade candidates."""

from __future__ import annotations

from typing import Any, Dict, Optional


VALID_OUTCOMES = {
    "close_above_entry",
    "close_below_entry",
    "hit_target_before_stop",
    "resolve_yes",
    "resolve_no",
}

VALID_HORIZONS = {
    "same_session",
    "1h",
    "eod",
    "1d",
    "3d",
    "5d",
    "catalyst_window",
}


def build_forecast_contract(
    signal: Dict[str, Any],
    *,
    default_horizon: str = "1d",
) -> Dict[str, Any]:
    """
    Separate forever:
      signal_strength ≠ P(win) ≠ expected_return ≠ data_confidence ≠ causal_confidence
    """
    existing = signal.get("forecast") if isinstance(signal.get("forecast"), dict) else {}
    side = str(signal.get("side") or signal.get("action") or "BUY").upper()
    outcome = existing.get("outcome") or signal.get("forecast_outcome")
    if not outcome:
        outcome = "close_above_entry" if side in ("BUY", "LONG", "CALL") else "close_below_entry"

    horizon = str(
        existing.get("horizon")
        or signal.get("horizon")
        or signal.get("forecast_horizon")
        or default_horizon
    )
    if horizon not in VALID_HORIZONS:
        horizon = default_horizon

    # Probability: prefer explicit calibrated fields; never invent from raw confidence alone without flag
    prob = existing.get("probability")
    if prob is None:
        prob = signal.get("calibrated_probability")
    if prob is None:
        pop = signal.get("pop_pct") or signal.get("probability_of_profit")
        try:
            pop_f = float(pop)
            prob = pop_f / 100.0 if pop_f > 1.0 else pop_f
        except (TypeError, ValueError):
            prob = None
    if prob is None:
        conf = signal.get("confidence")
        try:
            conf_f = float(conf)
            # Treat confidence as strength, map conservatively to probability with uncertainty flag
            if conf_f > 1.0:
                conf_f = conf_f / 100.0
            prob = max(0.35, min(0.72, 0.4 + 0.35 * conf_f))
            existing = dict(existing)
            existing["probability_from_confidence"] = True
        except (TypeError, ValueError):
            prob = None

    expected_return = existing.get("expected_return_after_costs")
    if expected_return is None:
        expected_return = signal.get("expected_return_after_costs")
    if expected_return is None:
        try:
            entry = float(signal.get("entry") or signal.get("current_price") or 0)
            target = float(signal.get("target") or signal.get("take_profit") or 0)
            if entry > 0 and target > 0:
                raw = (target - entry) / entry
                if side in ("SELL", "SHORT", "PUT"):
                    raw = -raw
                # Rough cost haircut
                expected_return = round(raw - 0.002, 4)
        except (TypeError, ValueError):
            expected_return = None

    downside = existing.get("downside_quantile")
    if downside is None:
        try:
            entry = float(signal.get("entry") or signal.get("current_price") or 0)
            stop = float(signal.get("stop") or signal.get("stop_loss") or 0)
            if entry > 0 and stop > 0:
                downside = round((stop - entry) / entry, 4)
                if side in ("SELL", "SHORT", "PUT"):
                    downside = -downside
        except (TypeError, ValueError):
            downside = None

    uncertainty = existing.get("uncertainty")
    if uncertainty is None:
        uncertainty = signal.get("uncertainty")
    if uncertainty is None:
        # Higher when probability came from confidence or freshness is BACKGROUND
        unc = 0.12
        if existing.get("probability_from_confidence"):
            unc += 0.08
        fc = str(signal.get("freshness_class") or "").upper()
        if fc in ("BACKGROUND", "STALE", "UNKNOWN"):
            unc += 0.1
        uncertainty = round(min(0.5, unc), 3)

    data_conf = signal.get("data_confidence")
    causal_conf = signal.get("causal_confidence")
    signal_strength = signal.get("signal_strength")
    if signal_strength is None:
        try:
            c = float(signal.get("confidence") or 0)
            signal_strength = c / 100.0 if c > 1 else c
        except (TypeError, ValueError):
            signal_strength = None

    contract = {
        "outcome": outcome,
        "horizon": horizon,
        "probability": round(float(prob), 4) if prob is not None else None,
        "expected_return_after_costs": expected_return,
        "downside_quantile": downside,
        "uncertainty": uncertainty,
        "signal_strength": signal_strength,
        "data_confidence": data_conf,
        "causal_confidence": causal_conf,
        "probability_from_confidence": bool(existing.get("probability_from_confidence")),
    }
    return contract


def apply_forecast_to_signal(signal: Dict[str, Any], **kwargs) -> Dict[str, Any]:
    contract = build_forecast_contract(signal, **kwargs)
    signal["forecast"] = contract
    if contract.get("horizon"):
        signal["horizon"] = contract["horizon"]
    if contract.get("probability") is not None and signal.get("calibrated_probability") is None:
        signal["calibrated_probability"] = contract["probability"]
    return signal


def forecast_gate_ok(signal: Dict[str, Any], *, require_probability: bool = True) -> tuple:
    """Return (ok, reason). Stock alerts need horizon + calibrated probability."""
    fc = signal.get("forecast") if isinstance(signal.get("forecast"), dict) else None
    if not fc:
        fc = build_forecast_contract(signal)
    horizon = fc.get("horizon")
    if not horizon or horizon not in VALID_HORIZONS:
        return False, "missing or invalid forecast horizon"
    if require_probability:
        prob = fc.get("probability")
        if prob is None:
            return False, "missing calibrated probability"
        try:
            p = float(prob)
        except (TypeError, ValueError):
            return False, "invalid probability"
        if not (0.0 < p < 1.0):
            return False, f"probability out of range: {p}"
        unc = float(fc.get("uncertainty") or 0)
        if unc >= 0.45:
            return False, f"abstain: uncertainty {unc:.2f} too high"
    return True, "forecast_ok"


def apply_freshness_to_day_trade_confidence(signal: Dict[str, Any]) -> Dict[str, Any]:
    """BACKGROUND freshness cannot inflate day-trade confidence."""
    from utils.news_cycle_helpers import freshness_confidence_multiplier

    fc = str(signal.get("freshness_class") or "UNKNOWN")
    day_trade = bool(
        signal.get("day_trade")
        or str(signal.get("strategy") or "").lower() in ("day_trade", "scalp", "intraday")
        or str(signal.get("horizon") or signal.get("forecast", {}).get("horizon") if isinstance(signal.get("forecast"), dict) else "")
        in ("same_session", "1h", "eod")
    )
    mult = freshness_confidence_multiplier(fc, day_trade=day_trade)
    signal["freshness_confidence_multiplier"] = mult
    if mult <= 0 and day_trade:
        signal["day_trade_blocked_by_freshness"] = True
        # Zero out any confidence inflation for day-trade path
        if "confidence" in signal:
            try:
                signal["confidence"] = float(signal["confidence"]) * 0.0
            except (TypeError, ValueError):
                pass
    elif mult < 1.0 and "confidence" in signal:
        try:
            c = float(signal["confidence"])
            # Only apply if not already applied
            if not signal.get("_freshness_mult_applied"):
                signal["confidence"] = c * mult if c <= 1.0 else c * mult
                signal["_freshness_mult_applied"] = True
        except (TypeError, ValueError):
            pass
    return signal
