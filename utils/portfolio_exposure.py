"""Portfolio-aware exposure checks for DecisionPipeline."""

from __future__ import annotations

from collections import defaultdict
from typing import Any, Dict, List, Optional, Tuple


def sector_of(symbol: str, sector_map: Optional[Dict[str, str]] = None) -> str:
    if sector_map and symbol in sector_map:
        return str(sector_map[symbol])
    try:
        from engines.sector_intelligence_engine import SectorIntelligenceEngine
        eng = SectorIntelligenceEngine({})
        for sector, data in (eng.sector_mappings or {}).items():
            if symbol in (data.get("tickers") or []):
                return str(sector)
    except Exception:
        pass
    return "UNKNOWN"


def portfolio_exposure_gate(
    signal: Dict[str, Any],
    *,
    open_positions: Optional[List[Dict[str, Any]]] = None,
    config: Optional[Dict[str, Any]] = None,
) -> Tuple[bool, str]:
    """
    Block when adding would exceed sector / event-cluster / correlated exposure caps.
    Influences candidate creation — fail closed with a reason.
    """
    cfg = (config or {}).get("portfolio_exposure") or {}
    max_sector = float(cfg.get("max_sector_pct", 0.35))
    max_names = int(cfg.get("max_correlated_names", 4))
    max_cluster = int(cfg.get("max_event_cluster", 3))

    sym = str(signal.get("symbol") or signal.get("ticker") or "").upper()
    if not sym:
        return False, "missing symbol for exposure check"

    positions = list(open_positions or [])
    if not positions:
        return True, "no open positions"

    sector_map = cfg.get("sector_map") if isinstance(cfg.get("sector_map"), dict) else None
    my_sector = str(signal.get("sector") or sector_of(sym, sector_map))
    event_cluster = str(signal.get("event_cluster") or signal.get("event_type") or "")

    sector_notional = 0.0
    total_notional = 0.0
    same_sector = 0
    same_cluster = 0
    for pos in positions:
        psym = str(pos.get("symbol") or pos.get("ticker") or "").upper()
        try:
            notional = abs(float(pos.get("notional") or pos.get("market_value") or pos.get("qty", 0)) )
        except (TypeError, ValueError):
            notional = 1.0
        total_notional += notional
        psec = str(pos.get("sector") or sector_of(psym, sector_map))
        if psec == my_sector and my_sector != "UNKNOWN":
            sector_notional += notional
            same_sector += 1
        if event_cluster and str(pos.get("event_cluster") or pos.get("event_type") or "") == event_cluster:
            same_cluster += 1

    if total_notional > 0 and (sector_notional / total_notional) >= max_sector and same_sector >= 1:
        return False, f"sector exposure {my_sector} >= {max_sector:.0%}"
    if same_sector >= max_names:
        return False, f"too many correlated names in {my_sector} ({same_sector})"
    if event_cluster and same_cluster >= max_cluster:
        return False, f"event cluster {event_cluster} already has {same_cluster} positions"
    return True, "exposure_ok"


def kalshi_stock_bridge(
    kalshi_shifts: List[Dict[str, Any]],
    *,
    market_snapshot: Optional[Dict[str, Dict[str, Any]]] = None,
    limit: int = 10,
) -> List[Dict[str, Any]]:
    """
    Map Kalshi probability shifts → exposed equities via relationship graph.
    STOCK bucket only — does not place Kalshi orders.
    """
    from utils.relationship_graph import expand_relationship_candidates

    out: List[Dict[str, Any]] = []
    for shift in kalshi_shifts or []:
        tickers = shift.get("exposed_tickers") or shift.get("tickers") or []
        title = str(shift.get("title") or shift.get("ticker") or "kalshi")
        try:
            delta = abs(float(shift.get("prob_delta") or shift.get("probability_change") or 0))
        except (TypeError, ValueError):
            delta = 0.0
        if delta < 0.03 and not tickers:
            continue
        for t in tickers:
            sym = str(t).upper()
            cands = expand_relationship_candidates(
                sym,
                event_type="kalshi_probability_shift",
                expected_direction="positive" if float(shift.get("prob_delta") or 0) > 0 else "negative",
                event_materiality=min(0.9, 0.4 + delta),
                evidence=[f"Kalshi shift on {title}: Δp={delta:.3f}"],
                market_snapshot=market_snapshot,
                already_priced_probability=None,
                limit=3,
            )
            for c in cands:
                c["source_bucket"] = "STOCK"
                c["kalshi_bridge"] = True
                c["kalshi_contract"] = shift.get("ticker") or shift.get("contract_id")
                out.append(c)
                if len(out) >= limit:
                    return out
    return out[:limit]
