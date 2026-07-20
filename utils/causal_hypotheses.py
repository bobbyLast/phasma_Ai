"""Causal hypothesis generator — evidence-backed, never hard-coded trade facts."""

from __future__ import annotations

from typing import Any, Dict, List, Optional


def generate_causal_hypotheses(
    event: Dict[str, Any],
    *,
    market_snapshot: Optional[Dict[str, Dict[str, Any]]] = None,
    peer_moves: Optional[Dict[str, float]] = None,
) -> Dict[str, Any]:
    """Build ranked hypotheses for why a name might move — not trade instructions."""
    sym = str(event.get("symbol") or "").upper()
    etype = str(event.get("event_type") or "unknown")
    direction = str(event.get("directional_interpretation") or "unknown")
    materiality = float(event.get("materiality") or 0.4)
    tier = int(event.get("source_tier") or 4)

    hypotheses: List[Dict[str, Any]] = []
    primary_conf = min(0.92, 0.45 + 0.1 * (5 - min(tier, 5)) + 0.25 * materiality)

    if etype != "unclassified_news":
        hypotheses.append({
            "cause": etype,
            "status": "probable_primary",
            "confidence": round(primary_conf, 3),
            "mechanism": event.get("title") or etype,
            "predicted_direction": direction,
        })

    # Sector secondary if peers moving same way
    peer_moves = peer_moves or {}
    same_dir = 0
    for peer, ch in peer_moves.items():
        if direction == "down" and ch < -1:
            same_dir += 1
        if direction == "up" and ch > 1:
            same_dir += 1
    if same_dir >= 2:
        hypotheses.append({
            "cause": "sector_weakness" if direction == "down" else "sector_strength",
            "status": "secondary_contributor",
            "confidence": round(min(0.7, 0.25 + 0.1 * same_dir), 3),
            "mechanism": f"{same_dir} peers moved similarly",
            "predicted_direction": direction,
        })

    # Market confirmation
    obs_move = None
    if market_snapshot and sym in market_snapshot:
        try:
            obs_move = float((market_snapshot[sym] or {}).get("change_pct") or 0)
        except (TypeError, ValueError):
            obs_move = None

    contradictions = []
    if obs_move is not None and direction == "down" and obs_move > 1.5:
        contradictions.append("price up despite negative event interpretation")
        for h in hypotheses:
            if h.get("status") == "probable_primary":
                h["confidence"] = round(float(h["confidence"]) * 0.7, 3)
    if obs_move is not None and direction == "up" and obs_move < -1.5:
        contradictions.append("price down despite positive event interpretation")

    unknown = max(0.05, 1.0 - sum(float(h["confidence"]) for h in hypotheses) / max(len(hypotheses), 1))
    if not hypotheses:
        hypotheses.append({
            "cause": "unknown",
            "status": "unknown",
            "confidence": 0.2,
            "mechanism": "insufficient evidence",
            "predicted_direction": "unknown",
        })
        unknown = 0.8

    return {
        "event_id": event.get("event_id"),
        "affected_ticker": sym,
        "observed_move": f"{sym} {obs_move:+.2f}%" if obs_move is not None else None,
        "hypotheses": hypotheses,
        "contradictions": contradictions,
        "unknown_component": round(min(0.95, unknown), 3),
        "trade_control": False,  # NEVER direct-control trades
        "status": hypotheses[0].get("status"),
        "confidence": hypotheses[0].get("confidence"),
        "predicted_direction": hypotheses[0].get("predicted_direction"),
        "mechanism": hypotheses[0].get("mechanism"),
        "expected_horizon": "1d",
        "supporting_evidence": list(event.get("facts") or []),
        "contradicting_evidence": contradictions,
    }


def hypotheses_for_events(
    events: List[Dict[str, Any]],
    *,
    market_snapshot: Optional[Dict[str, Dict[str, Any]]] = None,
    limit: int = 25,
) -> List[Dict[str, Any]]:
    peer_moves = {}
    if market_snapshot:
        for s, row in list(market_snapshot.items())[:200]:
            try:
                peer_moves[s] = float((row or {}).get("change_pct") or 0)
            except (TypeError, ValueError):
                continue
    out = []
    for ev in (events or [])[:limit]:
        if not ev.get("symbol") and ev.get("scope") == "macroeconomic":
            continue
        out.append(generate_causal_hypotheses(ev, market_snapshot=market_snapshot, peer_moves=peer_moves))
    return out
