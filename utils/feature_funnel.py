"""Fast 500-symbol numerical feature scan — no LLM, no per-ticker news."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class FeatureRow:
    symbol: str
    price: float = 0.0
    volume: float = 0.0
    change_pct: float = 0.0
    rel_volume: float = 0.0
    abs_move: float = 0.0
    score: float = 0.0
    flags: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "symbol": self.symbol,
            "price": self.price,
            "volume": self.volume,
            "change_pct": self.change_pct,
            "rel_volume": self.rel_volume,
            "abs_move": self.abs_move,
            "score": self.score,
            "flags": list(self.flags),
        }


def build_feature_matrix(
    market_snapshot: Dict[str, Dict[str, Any]],
    *,
    base_universe: Optional[List[str]] = None,
) -> List[FeatureRow]:
    """Compute cheap numerical features for all symbols in snapshot/universe."""
    rows: List[FeatureRow] = []
    symbols = list(base_universe or []) or list(market_snapshot.keys())
    vols = []
    for sym in symbols:
        row = market_snapshot.get(str(sym).upper()) or {}
        try:
            vol = float(row.get("volume") or 0)
        except (TypeError, ValueError):
            vol = 0.0
        if vol > 0:
            vols.append(vol)
    median_vol = sorted(vols)[len(vols) // 2] if vols else 1.0

    for sym in symbols:
        su = str(sym).upper()
        row = market_snapshot.get(su) or {}
        try:
            price = float(row.get("price") or 0)
        except (TypeError, ValueError):
            price = 0.0
        try:
            volume = float(row.get("volume") or 0)
        except (TypeError, ValueError):
            volume = 0.0
        try:
            change = float(row.get("change_pct") or 0)
        except (TypeError, ValueError):
            change = 0.0
        rel = (volume / median_vol) if median_vol > 0 else 0.0
        flags = []
        if abs(change) >= 3.0:
            flags.append("big_move")
        if rel >= 2.0:
            flags.append("volume_spike")
        if abs(change) >= 5.0 and rel >= 1.5:
            flags.append("confirmed_mover")
        score = abs(change) * 0.6 + min(rel, 5.0) * 0.4
        rows.append(
            FeatureRow(
                symbol=su,
                price=price,
                volume=volume,
                change_pct=change,
                rel_volume=round(rel, 3),
                abs_move=abs(change),
                score=round(score, 3),
                flags=flags,
            )
        )
    rows.sort(key=lambda r: r.score, reverse=True)
    return rows


def funnel_candidates(
    features: List[FeatureRow],
    *,
    event_universe: Optional[List[str]] = None,
    relationship_universe: Optional[List[str]] = None,
    top_numerical: int = 50,
    top_event_graph: int = 40,
    top_ensemble: int = 20,
    top_deep_ai: int = 12,
) -> Dict[str, List[str]]:
    """Funnel: 500 numerical → event/graph → ensemble → deep AI finalists."""
    numerical = [r.symbol for r in features[:top_numerical] if r.price > 0 or r.score > 0]
    boost = set(str(s).upper() for s in (event_universe or []))
    boost |= set(str(s).upper() for s in (relationship_universe or []))
    # Prefer boosted symbols that also appear in features
    feat_map = {r.symbol: r for r in features}
    event_graph = []
    seen = set()
    for sym in list(boost) + numerical:
        if sym in seen:
            continue
        if sym not in feat_map and sym not in boost:
            continue
        seen.add(sym)
        event_graph.append(sym)
        if len(event_graph) >= top_event_graph:
            break
    ensemble = event_graph[:top_ensemble]
    deep_ai = event_graph[:top_deep_ai]
    return {
        "numerical_top": numerical,
        "event_graph_top": event_graph,
        "ensemble_top": ensemble,
        "deep_ai_finalists": deep_ai,
    }
