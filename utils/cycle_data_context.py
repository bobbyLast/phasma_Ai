"""Single-pass cycle ingest context — fetch once, analyze read-only."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from engines.news_engine_utils import NewsUtils
from utils.discovery_limits import discovery_limit


@dataclass
class CycleDataContext:
    """Phase-1 ingest snapshot shared by all intelligence branches."""

    ingested_news: List[Dict[str, Any]] = field(default_factory=list)
    symbol_universe: List[str] = field(default_factory=list)
    company_names: Dict[str, str] = field(default_factory=dict)
    prices: Dict[str, float] = field(default_factory=dict)

    @classmethod
    async def ingest(
        cls,
        news_sources,
        *,
        config=None,
        market_cache=None,
    ) -> "CycleDataContext":
        """Fetch integrated sources once and build the symbol universe."""
        raw = await news_sources.fetch_all_integrated_sources()
        ingested = [dict(item) for item in raw]
        NewsUtils.propagate_prices(ingested)

        seen: set = set()
        symbols: List[str] = []
        company_names: Dict[str, str] = {}
        prices: Dict[str, float] = {}

        symbol_limit = discovery_limit(config, "news_symbol_limit", 25)

        for item in ingested:
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
            symbols.append(sym)
            name = item.get("company_name") or item.get("company") or ""
            if name:
                company_names[sym] = str(name)
            price = item.get("price") if item.get("price") is not None else item.get("current_price")
            if price is not None:
                try:
                    prices[sym] = float(price)
                except (TypeError, ValueError):
                    pass
            if len(symbols) >= symbol_limit:
                break

        if hasattr(news_sources, "_extract_news_symbols"):
            for sym in news_sources._extract_news_symbols(ingested, limit=symbol_limit):
                if sym not in seen:
                    seen.add(sym)
                    symbols.append(sym)

        # Kalshi/Polymarket intel: news-matched tickers feed stock discovery, not trade posts
        for item in ingested:
            if not item.get("prediction_market"):
                continue
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
            symbols.append(sym)

        symbols = symbols[:symbol_limit]

        enriched = 0
        if market_cache and symbols:
            try:
                batch = market_cache.fetch_prices(symbols)
                for sym, pdata in (batch or {}).items():
                    sym_u = str(sym).upper()
                    price = None
                    if isinstance(pdata, dict):
                        price = pdata.get("current") or pdata.get("price") or pdata.get("regularMarketPrice")
                    elif pdata is not None:
                        try:
                            price = float(pdata)
                        except (TypeError, ValueError):
                            price = None
                    if price is not None:
                        prices[sym_u] = float(price)
                        enriched += 1
                for item in ingested:
                    sym = str(item.get("symbol") or "").upper().strip()
                    if sym and sym in prices and item.get("price") is None:
                        item["price"] = prices[sym]
                NewsUtils.propagate_prices(ingested)
            except Exception:
                pass

        if prices:
            from utils.robust_price_fetcher import register_cycle_prices
            register_cycle_prices(prices)

        ctx = cls(
            ingested_news=ingested,
            symbol_universe=symbols,
            company_names=company_names,
            prices=prices,
        )
        ctx._log_phase("phase1_ingest", {
            "items": len(ingested),
            "symbols": len(symbols),
            "enriched_prices": enriched or len(prices),
        })
        return ctx

    def _log_phase(self, phase: str, data: Dict[str, Any]) -> None:
        print(f"   [FLOOR] {phase}: items={data.get('items', len(self.ingested_news))} "
              f"symbols={data.get('symbols', len(self.symbol_universe))} "
              f"prices={data.get('enriched_prices', len(self.prices))}")
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
        except Exception:
            pass
