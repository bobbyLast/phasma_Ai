"""Ranked Symbol Coalition — news tickers first, resolve/enrich only top-N."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from engines.news_engine_utils import NewsUtils
from utils.discovery_limits import discovery_limit


@dataclass
class CoalitionEntry:
    symbol: str
    rank_score: float
    headline_count: int = 0
    sample_titles: List[str] = field(default_factory=list)
    sources: List[str] = field(default_factory=list)
    from_news: bool = True
    company_name: str = ""
    news_match_score: float = 0.0
    sector: str = "Equities"
    industry: str = "Equities"
    resolver_status: str = ""
    coalition_resolved: bool = False


@dataclass
class SymbolCoalition:
    entries: List[CoalitionEntry] = field(default_factory=list)
    history_batch: Dict[str, Any] = field(default_factory=dict)
    prices: Dict[str, float] = field(default_factory=dict)

    @property
    def symbols(self) -> List[str]:
        return [e.symbol for e in self.entries]

    def entry_map(self) -> Dict[str, CoalitionEntry]:
        return {e.symbol: e for e in self.entries}

    def boost_for_symbol(self, symbol: str) -> float:
        entry = self.entry_map().get(str(symbol or "").upper())
        if not entry:
            return 1.0
        # Mild boost so news-ranked names float above equal movers
        return 1.0 + min(0.5, entry.rank_score / 20.0)


def build_symbol_coalition(
    cycle_data: Any,
    *,
    config: Any = None,
    limit: Optional[int] = None,
) -> SymbolCoalition:
    """Rank tickers from ingest headlines before expensive resolve/enrich."""
    if cycle_data is None:
        print("   [COALITION] No cycle_data — empty coalition")
        return SymbolCoalition()

    cap = int(limit if limit is not None else discovery_limit(config, "news_symbol_limit", 25))
    ingested = list(getattr(cycle_data, "ingested_news", None) or [])
    company_names = dict(getattr(cycle_data, "company_names", None) or {})
    prices = dict(getattr(cycle_data, "prices", None) or {})

    buckets: Dict[str, Dict[str, Any]] = {}

    def _bucket(sym: str) -> Optional[Dict[str, Any]]:
        sym_u = str(sym or "").upper().strip()
        if not sym_u or sym_u.startswith("KX"):
            return None
        if not NewsUtils.is_valid_extracted_ticker(sym_u):
            return None
        if sym_u not in buckets:
            buckets[sym_u] = {
                "symbol": sym_u,
                "headline_count": 0,
                "sample_titles": [],
                "sources": [],
                "news_match_score": 0.0,
                "company_name": company_names.get(sym_u, ""),
            }
        return buckets[sym_u]

    for item in ingested:
        if not isinstance(item, dict):
            continue
        sym = str(item.get("symbol") or "").upper().strip()
        if not sym:
            continue
        b = _bucket(sym)
        if b is None:
            continue
        b["headline_count"] += 1
        title = str(item.get("title") or "").strip()
        if title and title not in b["sample_titles"] and len(b["sample_titles"]) < 3:
            b["sample_titles"].append(title)
        source = str(item.get("source") or "").strip()
        if source and source not in b["sources"]:
            b["sources"].append(source)
        match = float(item.get("news_match_score") or 0)
        if match > b["news_match_score"]:
            b["news_match_score"] = match
        name = item.get("company_name") or item.get("company") or ""
        if name and not b["company_name"]:
            b["company_name"] = str(name)

    # Prefer universe order as a light prior when headlines are sparse
    for sym in getattr(cycle_data, "symbol_universe", None) or []:
        b = _bucket(sym)
        if b is None:
            continue
        if b["headline_count"] == 0:
            b["headline_count"] = 1

    entries: List[CoalitionEntry] = []
    for b in buckets.values():
        # Rank: mentions dominate; prediction-news match adds secondary weight
        rank = float(b["headline_count"]) * 2.0 + float(b["news_match_score"]) * 3.0
        if b["company_name"]:
            rank += 0.5
        entries.append(
            CoalitionEntry(
                symbol=b["symbol"],
                rank_score=round(rank, 3),
                headline_count=int(b["headline_count"]),
                sample_titles=list(b["sample_titles"]),
                sources=list(b["sources"])[:8],
                from_news=True,
                company_name=str(b["company_name"] or ""),
                news_match_score=float(b["news_match_score"]),
            )
        )

    entries.sort(key=lambda e: (e.rank_score, e.headline_count), reverse=True)
    ranked = entries[:cap]
    print(
        f"   [COALITION] Ranked {len(ranked)} symbols "
        f"(from {len(buckets)} unique, cap={cap})"
    )
    return SymbolCoalition(entries=ranked, prices=prices)


def resolve_coalition_local(
    coalition: SymbolCoalition,
    *,
    cycle_data: Any = None,
) -> SymbolCoalition:
    """Fill company metadata for top-N using CSV/local maps only (no web)."""
    from utils.company_resolver import get_resolver

    resolver = get_resolver()
    cycle_names = dict(getattr(cycle_data, "company_names", None) or {}) if cycle_data else {}

    for entry in coalition.entries:
        if cycle_names.get(entry.symbol) and not entry.company_name:
            entry.company_name = cycle_names[entry.symbol]

        resolved = resolver.resolve(
            entry.symbol,
            entry.sample_titles[0] if entry.sample_titles else None,
            allow_yf=False,
            allow_web=False,
        )
        if not entry.company_name:
            entry.company_name = resolved.get("company_name") or entry.symbol
        entry.sector = resolved.get("sector") or "Equities"
        entry.industry = resolved.get("industry") or entry.sector or "Equities"
        entry.resolver_status = str(resolved.get("resolver_status") or resolved.get("source") or "local")
        # Trusted if CSV/static hit; derived ticker-only still usable without re-fact-check spam
        entry.coalition_resolved = entry.resolver_status in (
            "company_reference.csv",
            "cache_exact",
            "sec_exact",
            "local",
            "derived",
        ) or bool(entry.company_name)
        if entry.resolver_status == "company_reference.csv":
            entry.resolver_status = "cache_exact"

    resolved_n = sum(1 for e in coalition.entries if e.coalition_resolved)
    print(f"   [COALITION] Local-resolved {resolved_n}/{len(coalition.entries)} (no web)")
    return coalition


def fetch_coalition_market_batch(
    coalition: SymbolCoalition,
    market_cache: Any,
    *,
    period: str = "5d",
) -> Dict[str, Any]:
    """One shared history/price batch for movers + buy scoring."""
    batch: Dict[str, Any] = {}
    if not coalition.entries:
        return batch

    symbols = coalition.symbols
    if market_cache is not None:
        try:
            prices = market_cache.fetch_prices(symbols) or {}
            for sym, price in prices.items():
                try:
                    coalition.prices[str(sym).upper()] = float(price)
                except (TypeError, ValueError):
                    pass
        except Exception as exc:
            print(f"   [COALITION] Price batch failed: {exc}")

        for sym in symbols:
            try:
                hist = market_cache.fetch_history(sym, period=period)
                if hist is not None and hasattr(hist, "empty") and not hist.empty:
                    batch[sym] = hist
            except Exception:
                continue
    else:
        # Lightweight yfinance fallback when no market cache is wired
        try:
            import yfinance as yf

            for sym in symbols:
                try:
                    hist = yf.Ticker(sym).history(period=period, interval="1d")
                    if hist is not None and not hist.empty:
                        batch[sym] = hist
                except Exception:
                    continue
        except Exception as exc:
            print(f"   [COALITION] History fallback failed: {exc}")

    coalition.history_batch = batch
    print(f"   [COALITION] Market batch: {len(batch)} histories, {len(coalition.prices)} prices")
    return batch


def apply_coalition_to_news_item(item: Dict[str, Any], coalition: SymbolCoalition) -> Dict[str, Any]:
    """Stamp a news/candidate row with coalition resolve metadata."""
    if not isinstance(item, dict):
        return item
    sym = str(item.get("symbol") or "").upper().strip()
    entry = coalition.entry_map().get(sym)
    if not entry:
        return item
    item["symbol"] = sym
    if not item.get("company_name") and entry.company_name:
        item["company_name"] = entry.company_name
    if not item.get("sector"):
        item["sector"] = entry.sector
    if not item.get("industry"):
        item["industry"] = entry.industry
    item["coalition_resolved"] = bool(entry.coalition_resolved)
    item["coalition_rank_score"] = entry.rank_score
    item["resolver_status"] = entry.resolver_status or item.get("resolver_status")
    if entry.coalition_resolved and not item.get("fact_check"):
        item["fact_check"] = {
            "is_valid": True,
            "validation_score": 0.7,
            "risk_level": "MEDIUM",
            "company_info": {
                "symbol": sym,
                "name": entry.company_name or sym,
                "company_name": entry.company_name or sym,
                "full_name": entry.company_name or sym,
                "sector": entry.sector,
                "industry": entry.industry,
                "resolver_status": entry.resolver_status or "coalition_local",
            },
        }
    return item
