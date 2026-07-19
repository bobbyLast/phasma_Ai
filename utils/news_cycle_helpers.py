"""Single-pass news cycle helpers — one ingest, targeted deep dives only."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Union

ConfigLike = Union[Dict[str, Any], Any]

_DEFAULT_PIPELINE = {
    "single_ingest_per_cycle": True,
    "deep_investigate_enabled": True,
    "deep_investigate_max_items": 3,
    "deep_investigate_min_score": 0.55,
}


def news_pipeline_config(config: ConfigLike) -> Dict[str, Any]:
    if config is None:
        return dict(_DEFAULT_PIPELINE)
    data = config.data if hasattr(config, "data") else config
    if not isinstance(data, dict):
        return dict(_DEFAULT_PIPELINE)
    merged = dict(_DEFAULT_PIPELINE)
    merged.update(data.get("news_pipeline") or {})
    return merged


def news_item_key(item: Dict[str, Any]) -> str:
    sym = str(item.get("symbol") or "").upper().strip()
    title = str(item.get("title") or "")[:64].strip().lower()
    return f"{sym}::{title}"


def score_news_potential(item: Dict[str, Any]) -> float:
    """Higher = more worth a targeted follow-up fetch."""
    score = 0.0
    for field in ("confidence", "catalyst_score", "sentiment"):
        raw = item.get(field)
        if raw is None:
            continue
        try:
            val = float(raw)
            if field == "sentiment":
                val = abs(val)
            if val > 1.0:
                val = val / 100.0
            score = max(score, val)
        except (TypeError, ValueError):
            pass
    conf = item.get("confluence_score")
    if conf is not None:
        try:
            score = max(score, float(conf) / 100.0)
        except (TypeError, ValueError):
            pass
    if item.get("trade_type") in ("UNIFIED_CONVERGENCE", "catalyst_event"):
        score += 0.15
    if item.get("source") == "UnifiedMetaBrain":
        score += 0.1
    hype = item.get("hype_score") or item.get("mention_count")
    if hype is not None:
        try:
            score = max(score, min(float(hype) / 10.0, 1.0))
        except (TypeError, ValueError):
            pass
    return min(score, 1.0)


def merge_cycle_news_items(
    cycle_data: Any,
    priority_items: Optional[List[Dict[str, Any]]] = None,
) -> List[Dict[str, Any]]:
    """Build one news list from the cycle ingest snapshot + optional priority rows."""
    merged: List[Dict[str, Any]] = []
    seen: set = set()

    for item in priority_items or []:
        if not isinstance(item, dict):
            continue
        key = news_item_key(item)
        if key in seen:
            continue
        seen.add(key)
        merged.append(dict(item))

    ingested = getattr(cycle_data, "ingested_news", None) if cycle_data else None
    if ingested:
        for item in ingested:
            if not isinstance(item, dict):
                continue
            key = news_item_key(item)
            if key in seen:
                continue
            seen.add(key)
            merged.append(dict(item))

    return merged


async def deep_investigate_high_potential(
    news_engine: Any,
    items: List[Dict[str, Any]],
    *,
    config: ConfigLike,
) -> List[Dict[str, Any]]:
    """Targeted supplemental fetch for a few high-potential symbols — not a full news cycle."""
    cfg = news_pipeline_config(config)
    if not cfg.get("deep_investigate_enabled", True):
        return []

    max_items = int(cfg.get("deep_investigate_max_items", 3))
    min_score = float(cfg.get("deep_investigate_min_score", 0.55))

    ranked: List[tuple] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        sym = str(item.get("symbol") or "").upper().strip()
        if not sym or sym.startswith("KX"):
            continue
        pot = score_news_potential(item)
        if pot >= min_score:
            ranked.append((pot, sym, item))

    ranked.sort(key=lambda row: row[0], reverse=True)
    symbols: List[str] = []
    seen_syms: set = set()
    for pot, sym, _ in ranked:
        if sym in seen_syms:
            continue
        seen_syms.add(sym)
        symbols.append(sym)
        if len(symbols) >= max_items:
            break

    if not symbols:
        return []

    print(
        f"\n🔬 Deep news investigation: {len(symbols)} high-potential symbols "
        f"({', '.join(symbols)}) — targeted lines only, not a full re-scan"
    )

    apis = getattr(news_engine, "apis", None)
    if apis is None:
        return []

    supplemental: List[Dict[str, Any]] = []
    seen_keys: set = {news_item_key(i) for i in items if isinstance(i, dict)}

    for sym in symbols:
        try:
            rows = await apis.scan_yahoo_rss([sym])
            for row in rows or []:
                if not isinstance(row, dict):
                    continue
                row = dict(row)
                row["source"] = row.get("source") or "deep_investigation"
                row["deep_investigation"] = True
                key = news_item_key(row)
                if key in seen_keys:
                    continue
                seen_keys.add(key)
                supplemental.append(row)
        except Exception as exc:
            print(f"   ⚠️ Deep investigation fetch failed for {sym}: {exc}")

    if supplemental:
        print(f"   ✅ Added {len(supplemental)} supplemental articles from follow-up fetch")
    return supplemental
