"""Compact prediction context — rank noisy inputs, distill signals for decision skills.

Raw cycle data can be hundreds of news rows plus nested market-intelligence dicts.
Prediction/jury/Monte Carlo skills need a small, structured view of what matters.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence, Union

from utils.news_cycle_helpers import classify_news_freshness, score_news_potential

ConfigLike = Union[Dict[str, Any], Any]

_DEFAULT = {
    "enabled": True,
    "max_unified_analysis_items": 20,
    "max_thematic_news_items": 80,
    "max_rationale_chars": 200,
    "max_title_chars": 120,
    "max_summary_chars": 240,
    "max_patterns": 4,
    "max_news_triggers": 3,
    "max_risk_factors": 3,
}


def prediction_context_config(config: ConfigLike = None) -> Dict[str, Any]:
    if config is None:
        return dict(_DEFAULT)
    data = config.data if hasattr(config, "data") else config
    if not isinstance(data, dict):
        return dict(_DEFAULT)
    merged = dict(_DEFAULT)
    merged.update(data.get("prediction_context") or {})
    return merged


def _clip(text: Any, limit: int) -> str:
    raw = str(text or "").strip()
    if not raw:
        return ""
    if len(raw) <= limit:
        return raw
    return raw[: max(0, limit - 3)].rstrip() + "..."


def _get(obj: Any, key: str, default: Any = None) -> Any:
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


def _set(obj: Any, key: str, value: Any) -> None:
    if isinstance(obj, dict):
        obj[key] = value
    else:
        try:
            setattr(obj, key, value)
        except Exception:
            pass


def rank_news_for_analysis(
    items: Sequence[Dict[str, Any]],
    *,
    config: ConfigLike = None,
    boost_symbols: Optional[Sequence[str]] = None,
) -> List[Dict[str, Any]]:
    """Rank news rows by catalyst potential + freshness; optional funnel boost."""
    boost = {str(s or "").upper().strip() for s in (boost_symbols or []) if s}
    ranked: List[tuple] = []
    for item in items or []:
        if not isinstance(item, dict):
            continue
        cls = classify_news_freshness(item, config)
        if cls in ("STALE",):
            continue
        pot = score_news_potential(item)
        sym = str(item.get("symbol") or "").upper().strip()
        if sym in boost:
            pot += 0.25
        if item.get("deep_investigation"):
            pot += 0.1
        ranked.append((pot, item))
    ranked.sort(key=lambda row: row[0], reverse=True)
    return [item for _, item in ranked]


def select_news_for_analysis(
    items: Sequence[Dict[str, Any]],
    *,
    config: ConfigLike = None,
    boost_symbols: Optional[Sequence[str]] = None,
) -> List[Dict[str, Any]]:
    cfg = prediction_context_config(config)
    cap = int(cfg.get("max_unified_analysis_items", 20))
    ranked = rank_news_for_analysis(items, config=config, boost_symbols=boost_symbols)
    return ranked[: max(1, cap)]


def select_thematic_news_items(
    items: Sequence[Dict[str, Any]],
    *,
    config: ConfigLike = None,
) -> List[Dict[str, Any]]:
    """Cap thematic analyzer input — highest-potential headlines only."""
    cfg = prediction_context_config(config)
    cap = int(cfg.get("max_thematic_news_items", 80))
    rows: List[Dict[str, Any]] = []
    for item in items or []:
        if not isinstance(item, dict):
            continue
        if not (item.get("title") or item.get("summary")):
            continue
        rows.append(
            {
                "title": _clip(item.get("title"), int(cfg.get("max_title_chars", 120))),
                "summary": _clip(item.get("summary"), int(cfg.get("max_summary_chars", 240))),
                "url": item.get("url", ""),
                "published": item.get("published") or item.get("timestamp", ""),
                "sentiment": item.get("sentiment", 0),
                "symbol": item.get("symbol", ""),
                "freshness_class": classify_news_freshness(item, config),
            }
        )
    ranked = rank_news_for_analysis(rows, config=config)
    return ranked[: max(1, cap)]


def compact_market_intelligence(intelligence: Dict[str, Any], *, config: ConfigLike = None) -> Dict[str, Any]:
    """Keep scores + top triggers; drop bulky subtrees."""
    if not isinstance(intelligence, dict):
        return {"opportunity_strength": 0, "source": "invalid"}
    cfg = prediction_context_config(config)
    sector = intelligence.get("sector_context") or {}
    fundamentals = intelligence.get("fundamental_analysis") or {}
    momentum = intelligence.get("momentum_analysis") or {}
    psychology = intelligence.get("market_psychology") or {}
    predictive = intelligence.get("predictive_intelligence") or {}
    triggers = intelligence.get("news_triggers") or []
    risks = intelligence.get("risk_factors") or []

    compact_triggers = []
    for trig in triggers[: int(cfg.get("max_news_triggers", 3))]:
        if isinstance(trig, dict):
            compact_triggers.append(
                {
                    "title": _clip(trig.get("title") or trig.get("headline"), cfg["max_title_chars"]),
                    "impact": trig.get("impact") or trig.get("relevance"),
                    "sentiment": trig.get("sentiment"),
                }
            )
        elif trig:
            compact_triggers.append(_clip(trig, cfg["max_title_chars"]))

    compact_risks = []
    for risk in risks[: int(cfg.get("max_risk_factors", 3))]:
        if isinstance(risk, dict):
            compact_risks.append(_clip(risk.get("description") or risk.get("factor") or risk, 120))
        elif risk:
            compact_risks.append(_clip(risk, 120))

    return {
        "symbol": intelligence.get("symbol"),
        "signal_type": intelligence.get("signal_type"),
        "opportunity_strength": intelligence.get("opportunity_strength", 0),
        "sector": sector.get("sector") or sector.get("name"),
        "sector_trend": sector.get("trend") or sector.get("momentum"),
        "valuation": fundamentals.get("valuation_level") or fundamentals.get("assessment"),
        "momentum": momentum.get("trend") or momentum.get("direction"),
        "sentiment": psychology.get("overall_sentiment") or psychology.get("sentiment"),
        "prediction": _clip(
            predictive.get("outlook") or predictive.get("summary") or predictive.get("direction"),
            cfg["max_summary_chars"],
        ),
        "news_triggers": compact_triggers,
        "risk_factors": compact_risks,
        "source": "compact_market_intel",
    }


def compact_signal_context(signal: Any, *, config: ConfigLike = None) -> Dict[str, Any]:
    """Structured, token-light view for prediction/jury/Monte Carlo skills."""
    cfg = prediction_context_config(config)
    sym = str(_get(signal, "symbol") or _get(signal, "ticker") or "").upper().strip()
    company = (
        _get(signal, "company_name")
        or (_get(signal, "fact_check") or {}).get("company_info", {}).get("name")
        or sym
    )
    latent = _get(signal, "latent_news_context") or {}
    if not isinstance(latent, dict):
        latent = {}
    divergence = _get(signal, "divergence_analysis") or {}
    if not isinstance(divergence, dict):
        divergence = {}
    sim = _get(signal, "simulation_results") or {}
    if not isinstance(sim, dict):
        sim = {}
    intel = _get(signal, "market_intelligence") or {}
    if not isinstance(intel, dict):
        intel = {}

    patterns = _get(signal, "patterns") or []
    if not isinstance(patterns, list):
        patterns = []
    patterns = [_clip(p, 40) for p in patterns[: int(cfg.get("max_patterns", 4))] if p]

    skills: List[str] = []
    if patterns:
        skills.append("pattern")
    if divergence.get("divergence_score"):
        skills.append("divergence")
    if sim.get("win_rate") is not None:
        skills.append("monte_carlo")
    if latent.get("summary") or latent.get("latent_risk_score"):
        skills.append("latent_memory")
    if _get(signal, "intelligence_strength"):
        skills.append("market_intel")
    if _get(signal, "confluence_score"):
        skills.append("confluence")

    return {
        "symbol": sym,
        "company": _clip(company, 80),
        "sector": _get(signal, "sector") or "Equities",
        "action": str(_get(signal, "action") or "BUY").upper(),
        "source": _get(signal, "source") or "signal",
        "confidence": round(float(_get(signal, "confidence") or 0), 4),
        "freshness": _get(signal, "freshness_class") or classify_news_freshness(signal, config),
        "catalyst": {
            "title": _clip(_get(signal, "title"), cfg["max_title_chars"]),
            "summary": _clip(_get(signal, "summary") or _get(signal, "rationale"), cfg["max_rationale_chars"]),
        },
        "technical": {
            "patterns": patterns,
            "bias": _get(signal, "technical_bias"),
            "divergence_score": divergence.get("divergence_score"),
        },
        "simulation": {
            "win_rate": sim.get("win_rate"),
            "pop": _get(signal, "pop_from_sim") or sim.get("pop_from_sim"),
            "target": sim.get("target_price") or _get(signal, "target_price"),
            "stop": sim.get("stop_loss") or _get(signal, "stop_loss") or _get(signal, "stop_price"),
            "horizon_days": sim.get("holding_days") or _get(signal, "days_to_expiry"),
        },
        "memory": {
            "latent_risk": latent.get("latent_risk_score"),
            "summary": _clip(latent.get("summary"), cfg["max_summary_chars"]),
        },
        "intel": {
            "strength": _get(signal, "intelligence_strength") or intel.get("opportunity_strength"),
            "sector_trend": intel.get("sector_trend") or (intel.get("sector_context") or {}).get("trend"),
            "prediction": _clip(
                intel.get("prediction")
                or (intel.get("predictive_intelligence") or {}).get("outlook"),
                cfg["max_summary_chars"],
            ),
        },
        "confluence": {
            "score": _get(signal, "confluence_score"),
            "sources": _get(signal, "unique_sources") or _get(signal, "source_count"),
        },
        "skills_tags": skills,
    }


def attach_prediction_context(signal: Any, *, config: ConfigLike = None) -> Dict[str, Any]:
    """Stamp compact prediction context on a signal dict or Signal object."""
    cfg = prediction_context_config(config)
    if not cfg.get("enabled", True):
        return {}
    compact = compact_signal_context(signal, config=config)
    _set(signal, "prediction_context", compact)
    return compact


def build_llm_query(prediction_context: Dict[str, Any]) -> str:
    """Focused Brave LLM context query from compact signal context."""
    pc = prediction_context or {}
    sym = str(pc.get("symbol") or "").upper().strip()
    company = str(pc.get("company") or sym).strip()
    catalyst = pc.get("catalyst") if isinstance(pc.get("catalyst"), dict) else {}
    title = str(catalyst.get("title") or "").strip()
    sector = str(pc.get("sector") or "").strip()
    parts = [sym, company]
    if title:
        parts.append(title)
    elif sector:
        parts.append(sector)
    parts.append("stock outlook catalyst")
    query = " ".join(p for p in parts if p)
    return query[:220]
