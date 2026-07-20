"""Signal data quality assessment for honest gating."""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, Optional

from utils.company_resolver import is_placeholder


class SignalDataQuality(str, Enum):
    COMPLETE = "COMPLETE"
    PARTIAL_PRICE_ONLY = "PARTIAL_PRICE_ONLY"
    MISSING_PRICE = "MISSING_PRICE"
    MISSING_VOLUME = "MISSING_VOLUME"
    INVALID_COMPANY = "INVALID_COMPANY"
    INVALID_ASSET_TYPE = "INVALID_ASSET_TYPE"
    DEMO_SOURCE = "DEMO_SOURCE"
    STALE_PRICE = "STALE_PRICE"
    NON_POSITIVE_PRICE = "NON_POSITIVE_PRICE"


def _has_price(signal: Dict[str, Any]) -> bool:
    for key in ("current_price", "entry_price", "price"):
        val = signal.get(key)
        try:
            if val is not None and float(val) > 0:
                return True
        except (TypeError, ValueError):
            continue
    return False


def _has_volume(signal: Dict[str, Any]) -> bool:
    fc = signal.get("fact_check") or {}
    info = fc.get("company_info") or {}
    for key in ("avg_volume", "volume"):
        val = signal.get(key) if key in signal else info.get(key)
        if val is None:
            continue
        if str(val).strip().upper() in ("N/A", "NA", "NONE", ""):
            continue
        try:
            if float(val) > 0:
                return True
        except (TypeError, ValueError):
            if val:
                return True
    return False


def assess_signal_data_quality(signal: Dict[str, Any]) -> SignalDataQuality:
    """Assess signal completeness for alert vs paper eligibility."""
    # Stamp identity from shared registry before judging company validity
    try:
        from utils.company_identity_registry import get_identity_registry
        get_identity_registry().stamp_item(signal)
    except Exception:
        pass

    fc = signal.get("fact_check") or {}
    if fc.get("is_valid") is False:
        # Soft unresolved: registry may still have a real name
        try:
            from utils.company_identity_registry import get_identity_registry
            if get_identity_registry().resolve_for_alert(signal):
                fc["is_valid"] = True
                signal["fact_check"] = fc
            else:
                return SignalDataQuality.INVALID_COMPANY
        except Exception:
            return SignalDataQuality.INVALID_COMPANY

    if not _has_price(signal):
        return SignalDataQuality.MISSING_PRICE

    for key in ("current_price", "entry_price", "price"):
        val = signal.get(key)
        try:
            if val is not None and float(val) <= 0:
                return SignalDataQuality.NON_POSITIVE_PRICE
        except (TypeError, ValueError):
            continue

    name = signal.get("company_name") or (fc.get("company_info") or {}).get("name")
    if is_placeholder(name) and fc.get("is_valid") is not True:
        try:
            from utils.company_identity_registry import get_identity_registry
            resolved = get_identity_registry().resolve_for_alert(signal)
            if resolved:
                signal["company_name"] = resolved
            else:
                return SignalDataQuality.INVALID_COMPANY
        except Exception:
            return SignalDataQuality.INVALID_COMPANY

    if not _has_volume(signal):
        return SignalDataQuality.PARTIAL_PRICE_ONLY

    return SignalDataQuality.COMPLETE


def is_paper_trade_eligible(quality: SignalDataQuality) -> bool:
    return quality == SignalDataQuality.COMPLETE


def is_alert_only_eligible(quality: SignalDataQuality) -> bool:
    return quality in (
        SignalDataQuality.COMPLETE,
        SignalDataQuality.PARTIAL_PRICE_ONLY,
    )


def apply_fetched_price(signal: Dict[str, Any], price: Optional[float]) -> None:
    """Update signal price fields after successful fetch."""
    if price is None:
        return
    try:
        p = float(price)
    except (TypeError, ValueError):
        return
    if p <= 0:
        return
    signal["current_price"] = p
    if not signal.get("entry_price"):
        signal["entry_price"] = p
    fc = signal.get("fact_check")
    if isinstance(fc, dict):
        info = fc.get("company_info")
        if isinstance(info, dict):
            info["price_range"] = f"${p:.2f}"


def apply_fetched_volume(signal: Dict[str, Any], volume: Optional[int]) -> None:
    """Update signal volume fields after successful fetch."""
    if volume is None:
        return
    try:
        v = int(volume)
    except (TypeError, ValueError):
        return
    if v <= 0:
        return
    signal["avg_volume"] = v
    fc = signal.get("fact_check")
    if not isinstance(fc, dict):
        fc = {}
        signal["fact_check"] = fc
    info = fc.get("company_info")
    if not isinstance(info, dict):
        info = {}
        fc["company_info"] = info
    info["avg_volume"] = v


def _positive_pct(value: Any) -> bool:
    if value is None:
        return False
    try:
        f = float(value)
        pct = f * 100.0 if 0 < f <= 1.0 else f
        return pct > 0
    except (TypeError, ValueError):
        return False


def _has_real_company_name(signal: Dict[str, Any]) -> bool:
    fc = signal.get("fact_check") or {}
    info = fc.get("company_info") or {}
    name = signal.get("company_name") or info.get("name") or info.get("full_name")
    return not is_placeholder(name)


def _sim_stats_valid(signal: Dict[str, Any]) -> bool:
    """When simulation ran, win rate and avg P&L must be positive."""
    sim = signal.get("simulation_results")
    if not isinstance(sim, dict) or not sim:
        return True
    if not _positive_pct(signal.get("sim_win_rate", sim.get("win_rate"))):
        return False
    try:
        avg_pnl = float(sim.get("avg_pnl", 0))
    except (TypeError, ValueError):
        return False
    return avg_pnl > 0


def resolve_pop_pct(signal: Any) -> Optional[float]:
    """Real probability-of-profit % from simulation — never invent a default."""
    raw = None
    sim = None
    if isinstance(signal, dict):
        raw = signal.get("pop_from_sim")
        sim = signal.get("simulation_results")
    else:
        raw = getattr(signal, "pop_from_sim", None)
        sim = getattr(signal, "simulation_results", None)
    if raw is None and isinstance(sim, dict):
        raw = sim.get("pop_from_sim")
    if raw is None:
        if isinstance(signal, dict):
            raw = signal.get("pop")
        else:
            raw = getattr(signal, "pop", None)
    if raw is None:
        return None
    try:
        val = float(raw)
    except (TypeError, ValueError):
        return None
    if val <= 0:
        return None
    pct = val * 100.0 if val <= 1.0 else val
    return pct if pct > 0 else None


def volume_from_history(hist: Any) -> Optional[int]:
    """Average volume from a shared coalition/market history frame."""
    if hist is None:
        return None
    try:
        if getattr(hist, "empty", False):
            return None
        if "Volume" not in getattr(hist, "columns", []):
            return None
        avg = int(float(hist["Volume"].mean()))
        return avg if avg > 0 else None
    except Exception:
        return None


def price_from_history(hist: Any) -> Optional[float]:
    """Last close from a shared history frame."""
    if hist is None:
        return None
    try:
        if getattr(hist, "empty", False):
            return None
        if "Close" not in getattr(hist, "columns", []):
            return None
        price = float(hist["Close"].iloc[-1])
        return price if price > 0 else None
    except Exception:
        return None


def enrich_signal_market_fields(
    signal: Dict[str, Any],
    *,
    market_cache: Any = None,
    price_fetcher: Any = None,
    coalition: Any = None,
) -> bool:
    """Fetch missing price/volume so signal can reach COMPLETE quality.

    Prefer cycle SymbolCoalition batch (already fetched) before external APIs.
    """
    sym = str(signal.get("symbol") or signal.get("ticker") or "").upper().strip()
    if not sym:
        return False

    # 1) Reuse coalition prices / histories when available
    if coalition is not None:
        prices = getattr(coalition, "prices", None) or {}
        if not _has_price(signal) and sym in prices:
            apply_fetched_price(signal, prices.get(sym))
            signal["_price_source"] = "coalition_prices"

        batch = getattr(coalition, "history_batch", None) or {}
        hist = batch.get(sym)
        if hist is not None:
            if not _has_price(signal):
                apply_fetched_price(signal, price_from_history(hist))
                if _has_price(signal):
                    signal["_price_source"] = "coalition_history"
            if not _has_volume(signal):
                vol = volume_from_history(hist)
                if vol:
                    apply_fetched_volume(signal, vol)
                    signal["_volume_source"] = "coalition_history"

    if not _has_price(signal) and price_fetcher is not None:
        try:
            apply_fetched_price(signal, price_fetcher.get_real_price(sym))
            if _has_price(signal):
                signal["_price_source"] = "price_fetcher"
        except Exception:
            pass

    if not _has_volume(signal) and market_cache is not None:
        getter = getattr(market_cache, "get_avg_volume", None)
        if callable(getter):
            apply_fetched_volume(signal, getter(sym))
            if _has_volume(signal):
                signal["_volume_source"] = "market_cache"

    return assess_signal_data_quality(signal) == SignalDataQuality.COMPLETE


def is_display_eligible(signal: Dict[str, Any]) -> bool:
    """Minimum bar for showing a signal: real company, price, volume, confidence."""
    if assess_signal_data_quality(signal) != SignalDataQuality.COMPLETE:
        return False
    fc = signal.get("fact_check") or {}
    if fc.get("is_valid") is not True and not signal.get("company_validation"):
        return False
    sym = str(signal.get("symbol") or "").strip().upper()
    if not sym or is_placeholder(sym):
        return False
    if not _has_real_company_name(signal):
        return False
    if not _positive_pct(signal.get("confidence") or signal.get("unified_confidence")):
        return False
    if not _sim_stats_valid(signal):
        return False
    return True
