"""Technical pattern & indicator families — features, not auto-trades."""

from __future__ import annotations

from typing import Any, Dict, List, Optional


PATTERN_FAMILIES = (
    "reversal",
    "continuation",
    "consolidation",
    "breakout",
    "failed_breakout",
    "candlestick_rejection",
    "vol_contraction",
    "gap",
)

INDICATOR_FAMILIES = (
    "momentum",
    "trend",
    "volume",
    "volatility",
    "relative_strength",
    "breadth",
    "structure",
)


def classify_pattern_family(bars: Optional[List[Dict[str, float]]] = None, meta: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Lightweight geometry flags from recent OHLCV — no triple-counted oscillators."""
    meta = meta or {}
    if meta.get("pattern_family"):
        return {
            "family": meta["pattern_family"],
            "geometry": meta.get("geometry") or {},
            "volume_confirm": bool(meta.get("volume_confirm")),
            "invalidation": meta.get("invalidation"),
            "horizon": meta.get("horizon") or "1d",
            "regime_compatible": meta.get("regime_compatible", True),
        }

    family = "consolidation"
    geometry: Dict[str, Any] = {}
    volume_confirm = False
    invalidation = None
    horizon = "1d"

    if bars and len(bars) >= 5:
        closes = [float(b.get("close") or b.get("c") or 0) for b in bars[-10:]]
        highs = [float(b.get("high") or b.get("h") or 0) for b in bars[-10:]]
        lows = [float(b.get("low") or b.get("l") or 0) for b in bars[-10:]]
        vols = [float(b.get("volume") or b.get("v") or 0) for b in bars[-10:]]
        if closes and closes[0] > 0:
            ret = (closes[-1] - closes[0]) / closes[0]
            rng = (max(highs) - min(lows)) / closes[-1] if closes[-1] else 0
            geometry = {"return": round(ret, 4), "range_pct": round(rng, 4)}
            avg_vol = sum(vols[:-1]) / max(len(vols) - 1, 1) if vols else 0
            volume_confirm = bool(vols and avg_vol and vols[-1] > 1.5 * avg_vol)
            if abs(ret) < 0.01 and rng < 0.03:
                family = "consolidation"
                horizon = "1d"
            elif ret > 0.02 and volume_confirm:
                family = "breakout"
                invalidation = min(lows[-3:]) if lows else None
                horizon = "same_session"
            elif ret < -0.02 and volume_confirm:
                family = "failed_breakout" if ret > -0.05 else "reversal"
                invalidation = max(highs[-3:]) if highs else None
                horizon = "1d"
            elif abs(ret) > 0.03:
                family = "continuation" if ret > 0 else "reversal"
                horizon = "1d"
            # Gap heuristic
            if len(closes) >= 2 and closes[-2] > 0:
                gap = (closes[-1] - closes[-2]) / closes[-2]
                if abs(gap) > 0.02:
                    family = "gap"
                    geometry["gap_pct"] = round(gap, 4)

    return {
        "family": family if family in PATTERN_FAMILIES else "consolidation",
        "geometry": geometry,
        "volume_confirm": volume_confirm,
        "invalidation": invalidation,
        "horizon": horizon,
        "regime_compatible": True,
    }


def indicator_family_confirmations(features: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Independent confirmation count per family — no RSI+stoch+%R triple-count.
    Each family contributes at most one confirmation.
    """
    features = features or {}
    confirms: Dict[str, bool] = {f: False for f in INDICATOR_FAMILIES}

    mom = features.get("momentum") or features.get("rsi") or features.get("change_pct")
    try:
        m = float(mom)
        if abs(m) > 50:  # rsi-like
            confirms["momentum"] = m > 55 or m < 45
        else:
            confirms["momentum"] = abs(m) >= 1.5  # day change %
    except (TypeError, ValueError):
        pass

    trend = features.get("trend") or features.get("sma_slope") or features.get("above_sma")
    if trend is not None:
        confirms["trend"] = bool(trend) if isinstance(trend, bool) else abs(float(trend)) > 0

    rvol = features.get("relative_volume") or features.get("rvol") or features.get("volume_ratio")
    try:
        confirms["volume"] = float(rvol) >= 1.3
    except (TypeError, ValueError):
        if features.get("volume_spike"):
            confirms["volume"] = True

    vol = features.get("atr_pct") or features.get("volatility")
    try:
        confirms["volatility"] = float(vol) > 0
    except (TypeError, ValueError):
        pass

    rs = features.get("relative_strength") or features.get("rs_vs_spy")
    try:
        confirms["relative_strength"] = abs(float(rs)) > 0.5
    except (TypeError, ValueError):
        pass

    if features.get("breadth") is not None:
        confirms["breadth"] = bool(features.get("breadth"))
    if features.get("structure") or features.get("higher_high") or features.get("support_hold"):
        confirms["structure"] = True

    count = sum(1 for v in confirms.values() if v)
    return {
        "families": confirms,
        "confirmation_count": count,
        "max_families": len(INDICATOR_FAMILIES),
        # Cap so RSI-like stacks can't inflate past one momentum slot
        "independent_confirmations": count,
    }


def attach_pattern_features(signal: Dict[str, Any], bars=None, features=None) -> Dict[str, Any]:
    pattern = classify_pattern_family(bars, meta=signal.get("pattern_meta"))
    indicators = indicator_family_confirmations(features or signal.get("features"))
    signal["pattern_family"] = pattern
    signal["indicator_families"] = indicators
    if not signal.get("horizon") and pattern.get("horizon"):
        signal.setdefault("forecast_horizon", pattern["horizon"])
    return signal
