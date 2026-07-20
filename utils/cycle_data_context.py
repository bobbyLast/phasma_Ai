"""Typed cycle ingest context — frozen snapshots for Observer → Decision path."""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from engines.news_engine_utils import NewsUtils
from utils.discovery_limits import discovery_limit
from utils.context_mode import (
    build_source_health,
    compute_snapshot_ages,
    derive_context_mode,
    execution_allowed,
)

logger = logging.getLogger(__name__)


@dataclass
class CycleDataContext:
    """Versioned typed snapshots shared by all intelligence branches.

    Prediction markets are NEVER mixed into news confirmation paths.
    ``context_mode`` is derived from real ages/failures — never hardcoded NORMAL.
    """

    cycle_id: str = ""
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    # Legacy alias (news+sec+social only — no prediction markets)
    ingested_news: List[Dict[str, Any]] = field(default_factory=list)

    news_events: List[Dict[str, Any]] = field(default_factory=list)
    sec_events: List[Dict[str, Any]] = field(default_factory=list)
    social_events: List[Dict[str, Any]] = field(default_factory=list)
    macro_events: List[Dict[str, Any]] = field(default_factory=list)
    prediction_markets: List[Dict[str, Any]] = field(default_factory=list)
    options_snapshot: Optional[Dict[str, Any]] = None
    market_snapshot: Dict[str, Dict[str, Any]] = field(default_factory=dict)

    base_universe: List[str] = field(default_factory=list)
    event_universe: List[str] = field(default_factory=list)
    relationship_universe: List[str] = field(default_factory=list)
    relationship_candidates: List[Dict[str, Any]] = field(default_factory=list)
    normalized_events: List[Dict[str, Any]] = field(default_factory=list)
    causal_hypotheses: List[Dict[str, Any]] = field(default_factory=list)
    symbol_universe: List[str] = field(default_factory=list)

    company_names: Dict[str, str] = field(default_factory=dict)
    prices: Dict[str, float] = field(default_factory=dict)

    context_mode: str = "EXECUTION_BLOCKED"
    snapshot_ages: Dict[str, float] = field(default_factory=dict)
    source_health: Dict[str, Any] = field(default_factory=dict)
    freshness_status: Dict[str, Any] = field(default_factory=dict)
    relationship_graph_version: str = "1"
    feature_snapshot_version: str = "1"
    price_fetch_failed: bool = False
    news_from_stale_fallback: bool = False

    def allows_execution(self) -> bool:
        return execution_allowed(self.context_mode) and not self.news_from_stale_fallback

    @classmethod
    async def ingest(
        cls,
        news_sources,
        *,
        config=None,
        market_cache=None,
        kalshi_markets: Optional[List[Dict[str, Any]]] = None,
        base_universe: Optional[List[str]] = None,
        market_snapshot: Optional[Dict[str, Dict[str, Any]]] = None,
        macro_events: Optional[List[Dict[str, Any]]] = None,
        news_from_stale_fallback: bool = False,
    ) -> "CycleDataContext":
        """Fetch integrated sources once and build typed snapshots."""
        created_at = datetime.now(timezone.utc).isoformat()
        cycle_id = created_at.replace(":", "").replace("-", "")[:18]
        price_fetch_failed = False
        news_failed = False
        kalshi_failed = False

        try:
            raw = await news_sources.fetch_all_integrated_sources()
            ingested_all = [dict(item) for item in raw]
        except Exception as exc:
            news_failed = True
            logger.error("NEWS_INGEST_FAILED: %s", exc)
            print(f"ERROR NEWS_INGEST_FAILED: {exc}")
            ingested_all = []

        news_events: List[Dict[str, Any]] = []
        sec_events: List[Dict[str, Any]] = []
        social_events: List[Dict[str, Any]] = []
        prediction_from_news: List[Dict[str, Any]] = []

        for item in ingested_all:
            if item.get("prediction_market"):
                # Keep for optional event-ticker hints only — not news confirmation
                prediction_from_news.append(item)
                continue
            src = str(item.get("source") or "").lower()
            if "sec" in src or "edgar" in src or "form 4" in str(item.get("title") or "").lower():
                sec_events.append(item)
            elif src in ("reddit", "twitter", "social", "social_media") or item.get("social"):
                social_events.append(item)
            else:
                title = str(item.get("title") or "")
                if title.endswith("API Status") or title.endswith("API Ready") or "Scraper Active" in title:
                    continue
                news_events.append(item)

        prediction_markets: List[Dict[str, Any]] = []
        if kalshi_markets:
            for m in kalshi_markets:
                if isinstance(m, dict):
                    prediction_markets.append(dict(m))
        elif prediction_from_news:
            # Prefer raw market objects; news-shaped prediction rows are intel-only fallback
            prediction_markets = list(prediction_from_news)
            kalshi_failed = False
        else:
            kalshi_failed = kalshi_markets is None

        try:
            from utils.company_identity_registry import get_identity_registry
            reg = get_identity_registry()
            for bucket in (news_events, sec_events, social_events):
                for item in bucket:
                    reg.stamp_item(item)
        except Exception as exc:
            logger.warning("identity stamp failed: %s", exc)

        NewsUtils.propagate_prices(news_events)

        seen: set = set()
        event_symbols: List[str] = []
        company_names: Dict[str, str] = {}
        prices: Dict[str, float] = {}

        symbol_limit = discovery_limit(config, "news_symbol_limit", 25)
        event_items = news_events + sec_events + social_events

        for item in event_items:
            sym = str(item.get("symbol") or "").upper().strip()
            if not sym and hasattr(news_sources, "_extract_symbol"):
                text = f"{item.get('title', '')} {item.get('summary', '')}"
                sym = str(news_sources._extract_symbol(text) or "").upper().strip()
            if hasattr(news_sources, "_clean_symbol"):
                sym = news_sources._clean_symbol(sym) or sym
            if not sym or sym in seen:
                continue
            if not NewsUtils.is_valid_extracted_ticker(sym):
                continue
            seen.add(sym)
            event_symbols.append(sym)
            name = item.get("company_name") or item.get("company") or ""
            if name:
                company_names[sym] = str(name)
            price = item.get("price") if item.get("price") is not None else item.get("current_price")
            if price is not None:
                try:
                    prices[sym] = float(price)
                except (TypeError, ValueError):
                    logger.debug("bad price on %s: %r", sym, price)
            if len(event_symbols) >= symbol_limit:
                break

        if hasattr(news_sources, "_extract_news_symbols"):
            for sym in news_sources._extract_news_symbols(event_items, limit=symbol_limit):
                if sym not in seen:
                    seen.add(sym)
                    event_symbols.append(sym)

        # Prediction-aligned tickers may expand event universe (intel) but not news confirmation
        for item in prediction_from_news:
            if float(item.get("news_match_score") or 0) <= 0:
                continue
            sym = str(item.get("symbol") or "").upper().strip()
            if not sym and hasattr(news_sources, "_extract_symbol"):
                text = f"{item.get('title', '')} {item.get('summary', '')}"
                sym = str(news_sources._extract_symbol(text) or "").upper().strip()
            if hasattr(news_sources, "_clean_symbol"):
                sym = news_sources._clean_symbol(sym) or sym
            if not sym or sym in seen or not NewsUtils.is_valid_extracted_ticker(sym):
                continue
            seen.add(sym)
            event_symbols.append(sym)

        event_symbols = event_symbols[:symbol_limit]

        base = list(base_universe or [])
        if not base:
            try:
                from utils.infinite_symbol_provider import get_symbol_provider
                base = list(get_symbol_provider().get_symbols(limit=500) or [])
            except Exception as exc:
                logger.error("BASE_UNIVERSE_FAILED: %s", exc)
                print(f"ERROR BASE_UNIVERSE_FAILED: {exc}")
                base = []

        snap = dict(market_snapshot or {})
        if market_cache and (base or event_symbols):
            to_fetch: List[str] = []
            seen_fetch: set = set()
            for sym in list(base) + list(event_symbols):
                su = str(sym).upper()
                if su and su not in seen_fetch and su not in snap:
                    seen_fetch.add(su)
                    to_fetch.append(su)
            fetch_cap = min(len(to_fetch), max(len(event_symbols) + 50, 120))
            try:
                batch = market_cache.fetch_prices(to_fetch[:fetch_cap])
                if not batch and to_fetch[:fetch_cap]:
                    price_fetch_failed = True
                    logger.error(
                        "PRICE_ENRICH_EMPTY: requested=%d returned=0",
                        len(to_fetch[:fetch_cap]),
                    )
                    print(
                        f"ERROR PRICE_ENRICH_EMPTY: requested={len(to_fetch[:fetch_cap])} returned=0"
                    )
                for sym, pdata in (batch or {}).items():
                    sym_u = str(sym).upper()
                    price = None
                    volume = None
                    change = None
                    if isinstance(pdata, dict):
                        price = pdata.get("current") or pdata.get("price") or pdata.get("regularMarketPrice")
                        volume = pdata.get("volume") or pdata.get("avg_volume")
                        change = pdata.get("change_pct") or pdata.get("day_change_pct")
                    elif pdata is not None:
                        try:
                            price = float(pdata)
                        except (TypeError, ValueError):
                            price = None
                    if price is None:
                        continue
                    try:
                        prices[sym_u] = float(price)
                        snap[sym_u] = {
                            "price": float(price),
                            "volume": volume,
                            "change_pct": change,
                            "ts": datetime.now(timezone.utc).isoformat(),
                        }
                    except (TypeError, ValueError) as exc:
                        logger.warning("PRICE_PARSE_FAILED %s: %s", sym_u, exc)
            except Exception as exc:
                price_fetch_failed = True
                logger.error("PRICE_ENRICH_FAILED: %s", exc)
                print(f"ERROR PRICE_ENRICH_FAILED: {exc}")

        for item in event_items:
            sym = str(item.get("symbol") or "").upper().strip()
            if sym and sym in prices and item.get("price") is None:
                item["price"] = prices[sym]
                item["current_price"] = prices[sym]
        NewsUtils.propagate_prices(event_items)

        union: List[str] = []
        u_seen: set = set()
        for sym in list(base) + list(event_symbols):
            su = str(sym).upper().strip()
            if su and su not in u_seen:
                u_seen.add(su)
                union.append(su)

        try:
            from utils.company_identity_registry import get_identity_registry
            reg = get_identity_registry()
            for sym, name in list(company_names.items()):
                reg.remember(sym, company_name=name, source="cycle_ingest", resolver_status="cache_exact")
            for sym, p in prices.items():
                reg.remember(sym, last_price=p, source="market_snapshot")
                if sym not in company_names:
                    cn = reg.company_name(sym)
                    if cn:
                        company_names[sym] = cn
            reg.save()
        except Exception as exc:
            logger.warning("identity registry persist failed: %s", exc)

        if prices:
            from utils.robust_price_fetcher import register_cycle_prices
            register_cycle_prices(prices)

        ingested_news = list(news_events) + list(sec_events) + list(social_events)
        macros = list(macro_events or [])

        ages = compute_snapshot_ages(
            market_snapshot=snap,
            news_events=news_events,
            prediction_markets=prediction_markets,
            created_at=created_at,
        )
        health = build_source_health(
            news_count=len(news_events),
            sec_count=len(sec_events),
            market_count=len(snap),
            kalshi_count=len(prediction_markets),
            price_fetch_failed=price_fetch_failed,
            news_failed=news_failed,
            kalshi_failed=kalshi_failed and not prediction_markets,
        )
        mode = derive_context_mode(
            market_snapshot=snap,
            prices=prices,
            snapshot_ages=ages,
            source_health=health,
            price_fetch_failed=price_fetch_failed,
            news_from_stale_fallback=news_from_stale_fallback,
        )

        freshness_status = {
            "news_count": len(news_events),
            "sec_count": len(sec_events),
            "market_symbols": len(snap),
            "mode": mode,
        }

        ctx = cls(
            cycle_id=cycle_id,
            created_at=created_at,
            ingested_news=ingested_news,
            news_events=news_events,
            sec_events=sec_events,
            social_events=social_events,
            macro_events=macros,
            prediction_markets=prediction_markets,
            market_snapshot=snap,
            base_universe=[str(s).upper() for s in base],
            event_universe=event_symbols,
            relationship_universe=[],
            relationship_candidates=[],
            normalized_events=[],
            causal_hypotheses=[],
            symbol_universe=union,
            company_names=company_names,
            prices=prices,
            context_mode=mode,
            snapshot_ages=ages,
            source_health=health.to_dict(),
            freshness_status=freshness_status,
            price_fetch_failed=price_fetch_failed,
            news_from_stale_fallback=news_from_stale_fallback,
        )
        ctx._log_phase("phase1_ingest", {
            "items": len(ingested_news),
            "news": len(news_events),
            "sec": len(sec_events),
            "social": len(social_events),
            "prediction": len(prediction_markets),
            "symbols": len(union),
            "base": len(base),
            "event": len(event_symbols),
            "enriched_prices": len(prices),
            "context_mode": mode,
            "price_fetch_failed": price_fetch_failed,
        })
        print(f"   [FLOOR] context_mode={mode} market={len(snap)} prices={len(prices)}")
        return ctx

    def _log_phase(self, phase: str, data: Dict[str, Any]) -> None:
        print(
            f"   [FLOOR] {phase}: news={data.get('news', len(self.news_events))} "
            f"sec={data.get('sec', len(self.sec_events))} "
            f"pred={data.get('prediction', len(self.prediction_markets))} "
            f"base={data.get('base', len(self.base_universe))} "
            f"event={data.get('event', len(self.event_universe))} "
            f"prices={data.get('enriched_prices', len(self.prices))} "
            f"mode={data.get('context_mode', self.context_mode)}"
        )
        try:
            payload = {
                "sessionId": "28cc99",
                "runId": "floor-workflow",
                "hypothesisId": "FLOOR",
                "location": f"utils/cycle_data_context.py:{phase}",
                "message": phase,
                "data": data,
                "pid": os.getpid(),
                "timestamp": int(datetime.now().timestamp() * 1000),
            }
            with open("debug-28cc99.log", "a", encoding="utf-8") as f:
                f.write(json.dumps(payload, default=str) + "\n")
        except OSError as exc:
            logger.debug("debug log write failed: %s", exc)


# Alias for plan naming
UnifiedCycleContext = CycleDataContext
