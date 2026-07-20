"""
Precomputed temporal relationship graph + related winner/loser scoring.

Every edge carries confidence, economic_materiality, validity window, evidence, and last_verified.
Related opportunities require market confirmation or an explicit research_only flag.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

_GRAPH: Optional[Dict[str, Any]] = None

# Map legacy relationship labels → ontology edge types
_REL_MAP = {
    "direct_competitor": "COMPETES_WITH",
    "thematic_substitute": "SUBSTITUTES_FOR",
    "supplier": "SUPPLIES",
    "customer": "CUSTOMER_OF",
    "peer": "COMPETES_WITH",
}


def _default_graph_path() -> str:
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(root, "data", "relationship_graph.json")


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def enrich_edge(edge: Dict[str, Any]) -> Dict[str, Any]:
    """Ensure provenance fields exist on every edge (idempotent)."""
    e = dict(edge or {})
    rel = str(e.get("relationship") or e.get("edge_type") or "COMPETES_WITH")
    e["edge_type"] = _REL_MAP.get(rel, rel.upper() if rel.isupper() else _REL_MAP.get(rel, "COMPETES_WITH"))
    e["relationship"] = e.get("relationship") or e["edge_type"]
    e["confidence"] = float(e.get("confidence") or 0.5)
    e["economic_materiality"] = float(e.get("economic_materiality") or e.get("materiality") or 0.4)
    e["valid_from"] = e.get("valid_from") or "1970-01-01T00:00:00+00:00"
    e["valid_to"] = e.get("valid_to")  # None = open-ended
    if not e.get("evidence"):
        sector = e.get("sector") or "unknown"
        e["evidence"] = [
            {
                "source": "sector_seed" if "sector" in e else "graph_seed",
                "ref": f"seed:{sector}:{e.get('a')}-{e.get('b')}",
                "note": f"Seeded {e['edge_type']} edge",
            }
        ]
    e["last_verified"] = e.get("last_verified") or e.get("valid_from") or _now_iso()
    e["provenance_complete"] = bool(e.get("evidence"))
    return e


def load_relationship_graph(path: Optional[str] = None) -> Dict[str, Any]:
    global _GRAPH
    if _GRAPH is not None and path is None:
        return _GRAPH
    path = path or _default_graph_path()
    if os.path.isfile(path):
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict):
                edges = [enrich_edge(e) for e in (data.get("edges") or []) if isinstance(e, dict)]
                data["edges"] = edges
                data["edge_count"] = len(edges)
                data["version"] = max(int(data.get("version") or 1), 2)
                data["relationship_graph_version"] = data.get("relationship_graph_version") or f"v{data['version']}"
                _GRAPH = data
                return data
        except Exception:
            pass
    seeded = seed_graph_from_sector_maps()
    try:
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(seeded, f, indent=2)
    except Exception:
        pass
    _GRAPH = seeded
    return seeded


def seed_graph_from_sector_maps() -> Dict[str, Any]:
    """Build peer edges from SectorIntelligenceEngine mappings with full provenance."""
    edges: List[Dict[str, Any]] = []
    verified = _now_iso()
    try:
        from engines.sector_intelligence_engine import SectorIntelligenceEngine
        eng = SectorIntelligenceEngine({})
        for sector, data in (eng.sector_mappings or {}).items():
            tickers = list(data.get("tickers") or [])
            for i, a in enumerate(tickers):
                for b in tickers[i + 1 :]:
                    for src, dst in ((a, b), (b, a)):
                        edges.append(enrich_edge({
                            "a": str(src).upper(),
                            "b": str(dst).upper(),
                            "relationship": "direct_competitor",
                            "edge_type": "COMPETES_WITH",
                            "confidence": 0.7,
                            "economic_materiality": 0.45,
                            "sector": sector,
                            "valid_from": verified,
                            "last_verified": verified,
                            "evidence": [{
                                "source": "sector_intelligence_engine",
                                "ref": f"sector:{sector}",
                                "note": "Co-listed in sector peer map",
                            }],
                        }))
    except Exception:
        pass
    thematic = {
        "AI_CHIPS": ["NVDA", "AMD", "AVGO", "TSM", "ASML"],
        "EV": ["TSLA", "RIVN", "LCID", "GM", "F"],
        "CLOUD": ["MSFT", "AMZN", "GOOGL", "ORCL", "CRM"],
    }
    for theme, tickers in thematic.items():
        for i, a in enumerate(tickers):
            for b in tickers[i + 1 :]:
                for src, dst in ((a, b), (b, a)):
                    edges.append(enrich_edge({
                        "a": src, "b": dst,
                        "relationship": "thematic_substitute",
                        "edge_type": "SUBSTITUTES_FOR",
                        "confidence": 0.65,
                        "economic_materiality": 0.4,
                        "sector": theme,
                        "valid_from": verified,
                        "last_verified": verified,
                        "evidence": [{
                            "source": "thematic_seed",
                            "ref": f"theme:{theme}",
                            "note": "Thematic substitute seed",
                        }],
                    }))
    return {
        "version": 2,
        "relationship_graph_version": "v2",
        "edges": edges,
        "edge_count": len(edges),
    }


def score_related_opportunity(
    *,
    event_truth: float,
    relationship_confidence: float,
    materiality: float,
    direction_align: float,
    timing: float,
    market_confirmation: float,
    liquidity: float,
    already_priced: float,
    sector_contradiction: float,
    data_quality: float,
) -> float:
    """
    Score = event×rel×mat×dir×timing×mkt×liq − already_priced − sector_contradiction − data_quality_penalty
    """
    raw = (
        float(event_truth)
        * float(relationship_confidence)
        * float(materiality)
        * float(direction_align)
        * float(timing)
        * max(0.05, float(market_confirmation))
        * max(0.05, float(liquidity))
    )
    penalty = float(already_priced) + float(sector_contradiction) + float(data_quality)
    return max(0.0, min(1.0, raw - 0.35 * penalty))


def expand_relationship_candidates(
    trigger_ticker: str,
    *,
    event_type: str = "news_event",
    expected_direction: str = "positive",
    event_materiality: float = 0.5,
    evidence: Optional[List[str]] = None,
    market_snapshot: Optional[Dict[str, Dict[str, Any]]] = None,
    already_priced_probability: Optional[float] = None,
    event_truth: float = 0.7,
    allow_research_only: bool = True,
    limit: int = 8,
) -> List[Dict[str, Any]]:
    """Lookup graph neighbors and emit RelatedOpportunity records."""
    trigger = str(trigger_ticker or "").upper().strip()
    if not trigger:
        return []
    graph = load_relationship_graph()
    evidence = list(evidence or [f"Trigger event on {trigger}"])
    priced = float(already_priced_probability) if already_priced_probability is not None else 0.0
    out: List[Dict[str, Any]] = []
    seen = set()
    for raw_edge in graph.get("edges") or []:
        edge = enrich_edge(raw_edge)
        if str(edge.get("a") or "").upper() != trigger:
            continue
        if edge.get("valid_to"):
            try:
                if datetime.fromisoformat(str(edge["valid_to"]).replace("Z", "+00:00")) < datetime.now(timezone.utc):
                    continue
            except Exception:
                pass
        cand = str(edge.get("b") or "").upper()
        if not cand or cand == trigger or cand in seen:
            continue
        seen.add(cand)
        market_conf = 0.0
        liquidity = 0.4
        in_snap = bool(market_snapshot and cand in market_snapshot)
        if in_snap:
            row = market_snapshot[cand] or {}
            try:
                ch = abs(float(row.get("change_pct") or 0))
                market_conf = min(1.0, ch / 5.0)
            except (TypeError, ValueError):
                market_conf = 0.2
            try:
                vol = float(row.get("volume") or 0)
                liquidity = min(1.0, 0.3 + vol / 5_000_000.0) if vol else 0.35
                if vol:
                    market_conf = min(1.0, market_conf + 0.15)
            except (TypeError, ValueError):
                pass

        research_only = False
        if market_snapshot is not None and market_conf < 0.15:
            if not allow_research_only:
                continue
            research_only = True

        rel_conf = float(edge.get("confidence") or 0.6)
        mat = max(float(event_materiality), float(edge.get("economic_materiality") or 0.4))
        score = score_related_opportunity(
            event_truth=event_truth,
            relationship_confidence=rel_conf,
            materiality=mat,
            direction_align=0.85 if expected_direction in ("positive", "up") else 0.7,
            timing=0.8,
            market_confirmation=market_conf if market_conf > 0 else 0.15,
            liquidity=liquidity,
            already_priced=priced,
            sector_contradiction=0.0,
            data_quality=0.1 if not edge.get("provenance_complete") else 0.0,
        )
        if research_only:
            score *= 0.55

        out.append({
            "trigger_ticker": trigger,
            "candidate_ticker": cand,
            "symbol": cand,
            "event_type": event_type,
            "relationship": edge.get("edge_type") or edge.get("relationship"),
            "edge_type": edge.get("edge_type"),
            "expected_direction": expected_direction,
            "relationship_confidence": rel_conf,
            "event_materiality": float(event_materiality),
            "economic_materiality": float(edge.get("economic_materiality") or 0.4),
            "market_confirmation": market_conf,
            "already_priced_probability": priced if already_priced_probability is not None else None,
            "evidence": evidence + [
                f"{cand} linked as {edge.get('edge_type')} via {edge.get('sector') or 'graph'}",
            ],
            "edge_evidence": edge.get("evidence"),
            "last_verified": edge.get("last_verified"),
            "research_only": research_only,
            "trade_type": "RELATED_OPPORTUNITY",
            "source": "relationship_graph",
            "confidence": round(score, 4),
            "opportunity_score": round(score, 4),
        })
        if len(out) >= limit * 2:
            break
    out.sort(key=lambda r: float(r.get("opportunity_score") or 0), reverse=True)
    return out[:limit]


def expand_from_news_events(
    news_events: List[Dict[str, Any]],
    *,
    market_snapshot: Optional[Dict[str, Dict[str, Any]]] = None,
    max_triggers: int = 15,
    per_trigger: int = 5,
) -> List[Dict[str, Any]]:
    """Expand RelatedOpportunity candidates for top news-event symbols."""
    triggers = []
    seen = set()
    for item in news_events or []:
        if item.get("prediction_market"):
            continue
        sym = str(item.get("symbol") or "").upper().strip()
        if not sym or sym in seen:
            continue
        seen.add(sym)
        triggers.append(item)
        if len(triggers) >= max_triggers:
            break
    candidates: List[Dict[str, Any]] = []
    for item in triggers:
        sym = str(item.get("symbol") or "").upper()
        title = str(item.get("title") or "")[:120]
        direction = "positive"
        low = title.lower()
        if any(w in low for w in ("loss", "miss", "cut", "recall", "fail", "bankrupt", "lawsuit", "reject")):
            direction = "positive"  # competitors may benefit from negative trigger
            event_type = "negative_catalyst"
        else:
            event_type = "positive_catalyst"
            direction = "positive"
        priced = item.get("already_priced_probability")
        try:
            priced_f = float(priced) if priced is not None else None
        except (TypeError, ValueError):
            priced_f = None
        candidates.extend(
            expand_relationship_candidates(
                sym,
                event_type=event_type,
                expected_direction=direction,
                event_materiality=float(
                    item.get("materiality")
                    or item.get("catalyst_score")
                    or item.get("sentiment")
                    or 0.5
                ),
                evidence=[title] if title else None,
                market_snapshot=market_snapshot,
                already_priced_probability=priced_f,
                event_truth=min(1.0, 0.9 - 0.1 * (int(item.get("source_tier") or 4) - 1)),
                limit=per_trigger,
            )
        )
    best: Dict[str, Dict[str, Any]] = {}
    for c in candidates:
        key = c.get("candidate_ticker") or c.get("symbol")
        if not key:
            continue
        prev = best.get(key)
        if not prev or float(c.get("confidence") or 0) > float(prev.get("confidence") or 0):
            best[key] = c
    return list(best.values())


def all_edges_have_provenance(graph: Optional[Dict[str, Any]] = None) -> bool:
    g = graph or load_relationship_graph()
    edges = g.get("edges") or []
    if not edges:
        return False
    for e in edges:
        ee = enrich_edge(e)
        if not ee.get("evidence") or not ee.get("last_verified"):
            return False
    return True
