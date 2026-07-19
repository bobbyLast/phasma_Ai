"""Normalize and label confidence values for honest display (0–100%)."""

from __future__ import annotations

from typing import Any, Dict, Optional


def normalize_confidence_to_pct(value: Any) -> float:
    """
    Convert confidence to 0–100 percent.

    Rules:
    - None / invalid → 0
    - value <= 1.0 → multiply by 100 (decimal fraction)
    - value > 1.0 → treat as already percent
    - cap 0–100
    """
    if value is None:
        return 0.0
    try:
        v = float(value)
    except (TypeError, ValueError):
        return 0.0
    if v <= 1.0:
        v *= 100.0
    return round(max(0.0, min(100.0, v)), 2)


def format_confidence_fields(raw_score: Any, *, is_sum: bool = False, count: int = 1) -> Dict[str, Any]:
    """
    Build honest confidence display fields from a raw score.

    When is_sum=True, divide by count to get average before capping.
    """
    try:
        raw = float(raw_score or 0)
    except (TypeError, ValueError):
        raw = 0.0

    if is_sum and count > 0:
        raw = raw / count

    if 0 < raw <= 1.0:
        raw_display = raw * 100.0
    else:
        raw_display = raw

    confidence_pct = max(0.0, min(100.0, raw_display if raw_display > 1.0 else raw_display * 100.0))
    if raw_display > 100.0:
        label = "MAXED/CAPPED"
    elif confidence_pct >= 70:
        label = "HIGH"
    elif confidence_pct >= 40:
        label = "MODERATE"
    else:
        label = "LOW"

    return {
        "raw_score": round(raw_display, 2),
        "confidence_pct": round(confidence_pct, 2),
        "confidence_label": label,
    }


def format_confidence_display(confidence_pct: float) -> str:
    """Log/report friendly percent string."""
    return f"{normalize_confidence_to_pct(confidence_pct):.1f}%"


def compare_sim_validation(ai_confidence: Any, simulation_win_rate: Any) -> Dict[str, Any]:
    """
    Compare AI confidence vs simulation win rate.

    Returns status: MATCH | SOFT_MISMATCH | MISMATCH
    """
    ai_pct = normalize_confidence_to_pct(ai_confidence)
    sim_pct = normalize_confidence_to_pct(simulation_win_rate)
    gap = abs(ai_pct - sim_pct)

    if gap <= 5.0:
        status = "MATCH"
    elif gap <= 15.0:
        status = "SOFT_MISMATCH"
    else:
        status = "MISMATCH"

    return {
        "status": status,
        "ai_confidence_pct": ai_pct,
        "sim_win_rate_pct": sim_pct,
        "gap_pct": round(gap, 2),
    }


def format_sim_validation_message(symbol: str, validation: Dict[str, Any]) -> str:
    """Honest SIM VALIDATION log line."""
    sym = symbol or "N/A"
    ai = validation["ai_confidence_pct"]
    sim = validation["sim_win_rate_pct"]
    status = validation["status"]
    gap = validation["gap_pct"]

    if status == "MATCH":
        return (
            f"SIM VALIDATION: {sym} - MATCH. "
            f"AI confidence {ai:.1f}% vs sim win rate {sim:.1f}%."
        )
    direction = "exceeds" if ai > sim else "below"
    return (
        f"SIM VALIDATION: {sym} - {status}. "
        f"AI confidence {ai:.1f}% vs sim win rate {sim:.1f}% "
        f"(gap {gap:.1f}%, AI {direction} simulation). "
        f"Confidence capped/downshifted."
    )


def apply_sim_validation_adjustment(
    initial_confidence: float,
    sim_win_rate: float,
    validation: Dict[str, Any],
) -> float:
    """Cap/downshift confidence on mismatch."""
    final = float(initial_confidence)
    if validation["status"] == "MISMATCH":
        sim_frac = normalize_confidence_to_pct(sim_win_rate) / 100.0
        final = min(final, sim_frac + 0.05)
        final = max(0.1, final * 0.85)
    elif validation["status"] == "SOFT_MISMATCH":
        sim_frac = normalize_confidence_to_pct(sim_win_rate) / 100.0
        final = min(final, max(sim_frac, final * 0.9))
    return max(0.01, min(0.99, final))
