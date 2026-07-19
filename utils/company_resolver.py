"""
Central symbol → company metadata resolver.
Eliminates UNKNOWN/empty placeholders in signals, summaries, and JSON outputs.
"""

from __future__ import annotations

import csv
import logging
import os
import re
import time
from typing import Any, Callable, Dict, Optional

from utils.web_search_resolver import get_web_search_resolver, is_sector_category_name

logger = logging.getLogger(__name__)

RESOLVER_TRUSTED_STATUSES = frozenset({
    "sec_exact",
    "quote_exact",
    "cache_exact",
})

_PLACEHOLDER_VALUES = frozenset({
    "", "unknown", "UNKNOWN", "Unknown", "n/a", "N/A", "null", "None", "none",
})

# Headline company names -> tickers when symbol field is empty
_HEADLINE_COMPANY_TICKERS = (
    (re.compile(r"\bTarget\b", re.I), "TGT"),
    (re.compile(r"\bUbisoft\b", re.I), "UBI"),
    (re.compile(r"\bIMAX\b", re.I), "IMAX"),
    (re.compile(r"\bCurtiss-Wright\b", re.I), "CW"),
)

_PARENS_TICKER_RE = re.compile(r"\(([A-Z]{1,5})\)")


def is_placeholder(value: Any) -> bool:
    if value is None:
        return True
    text = str(value).strip()
    return text in _PLACEHOLDER_VALUES


def _clean_symbol(symbol: Any) -> str:
    if not symbol:
        return ""
    return str(symbol).upper().strip()


def _title_snippet(title: Optional[str], max_len: int = 72) -> str:
    if not title:
        return ""
    text = re.sub(r"\s+", " ", str(title)).strip()
    if len(text) > max_len:
        return text[: max_len - 3].rstrip() + "..."
    return text


class CompanyResolver:
    """Resolve symbol → company name, sector, industry from CSV, cache, and yfinance."""

    _instance: Optional["CompanyResolver"] = None

    def __init__(self, project_root: Optional[str] = None):
        root = project_root or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self._csv_path = os.path.join(root, "data", "company_reference.csv")
        self._static: Dict[str, Dict[str, str]] = {}
        self._yf_cache: Dict[str, Dict[str, str]] = {}
        self._yf_cache_ttl = 6 * 3600
        self._load_reference_csv()

    @classmethod
    def get(cls) -> "CompanyResolver":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _load_reference_csv(self) -> None:
        if not os.path.isfile(self._csv_path):
            return
        try:
            with open(self._csv_path, newline="", encoding="utf-8") as f:
                for row in csv.DictReader(f):
                    ticker = _clean_symbol(row.get("ticker"))
                    if not ticker:
                        continue
                    self._static[ticker] = {
                        "company_name": (row.get("company_name") or ticker).strip(),
                        "sector": (row.get("sector") or "Equities").strip(),
                        "industry": (row.get("sector") or "Equities").strip(),
                        "source": "company_reference.csv",
                    }
        except Exception:
            pass

    def _yf_lookup(self, symbol: str) -> Optional[Dict[str, str]]:
        symbol = _clean_symbol(symbol)
        if not symbol:
            return None
        cached = self._yf_cache.get(symbol)
        if cached and time.time() - cached.get("_ts", 0) < self._yf_cache_ttl:
            return {k: v for k, v in cached.items() if not k.startswith("_")}

        try:
            import yfinance as yf

            info = yf.Ticker(symbol).info or {}
            name = (
                info.get("longName")
                or info.get("shortName")
                or info.get("displayName")
            )
            sector = info.get("sector") or info.get("quoteType") or ""
            industry = info.get("industry") or sector or ""
            if not name:
                return None
            record = {
                "company_name": str(name).strip(),
                "sector": str(sector).strip() if sector else "Equities",
                "industry": str(industry).strip() if industry else "Equities",
                "source": "yfinance",
                "_ts": time.time(),
            }
            self._yf_cache[symbol] = record
            return {k: v for k, v in record.items() if not k.startswith("_")}
        except Exception:
            return None

    def _web_lookup(self, symbol: str, title: Optional[str] = None) -> Optional[Dict[str, str]]:
        try:
            return get_web_search_resolver().lookup(symbol, title)
        except Exception as exc:
            logger.debug("Web search lookup failed for %s: %s", symbol, exc)
            return None

    def resolve(
        self,
        symbol: Any,
        title: Optional[str] = None,
        *,
        allow_yf: bool = True,
        allow_web: bool = True,
    ) -> Dict[str, str]:
        """Resolve symbol metadata. Hot path should use allow_yf=False, allow_web=False."""
        sym = _clean_symbol(symbol)
        if sym in self._static:
            row = self._static[sym]
            return {
                "symbol": sym,
                "company_name": row["company_name"],
                "full_name": row["company_name"],
                "sector": row["sector"],
                "industry": row["industry"],
                "source": row["source"],
                "resolver_status": "cache_exact",
            }

        if allow_yf:
            yf_row = self._yf_lookup(sym) if sym else None
            if yf_row:
                return {
                    "symbol": sym,
                    "company_name": yf_row["company_name"],
                    "full_name": yf_row["company_name"],
                    "sector": yf_row["sector"],
                    "industry": yf_row["industry"],
                    "source": yf_row["source"],
                    "resolver_status": "quote_exact",
                }

        if allow_web:
            web_row = self._web_lookup(sym, title) if sym else None
            if web_row and not is_sector_category_name(web_row.get("company_name")):
                return {
                    "symbol": sym,
                    "company_name": web_row["company_name"],
                    "full_name": web_row["company_name"],
                    "sector": web_row["sector"],
                    "industry": web_row["industry"],
                    "source": web_row["source"],
                    "resolver_status": "web_suggested",
                }

        snippet = _title_snippet(title)
        if sym and snippet:
            label = f"${sym} - {snippet}"
        elif sym:
            label = sym
        elif snippet:
            label = snippet
        else:
            label = "Market headline"

        return {
            "symbol": sym,
            "company_name": label,
            "full_name": label,
            "sector": "Equities",
            "industry": "Equities",
            "source": "derived",
            "resolver_status": "derived" if sym else "unknown",
        }

    def resolve_local(self, symbol: Any, title: Optional[str] = None) -> Dict[str, str]:
        """CSV/static-only resolve — never hits yfinance or web search."""
        return self.resolve(symbol, title, allow_yf=False, allow_web=False)

    def company_name(self, symbol: Any, title: Optional[str] = None) -> str:
        return self.resolve(symbol, title)["company_name"]

    def sector(self, symbol: Any, title: Optional[str] = None) -> str:
        return self.resolve(symbol, title)["sector"]

    def coalesce(self, *values: Any, symbol: Any = None, title: Optional[str] = None) -> str:
        for value in values:
            if not is_placeholder(value):
                return str(value).strip()
        resolved = self.resolve(symbol, title)
        return resolved["company_name"]

    def enrich_company_info(
        self, company_info: Optional[Dict], symbol: Any, title: Optional[str] = None
    ) -> Dict[str, str]:
        info = dict(company_info or {})
        sym = _clean_symbol(symbol or info.get("symbol"))
        status = str(info.get("resolver_status") or info.get("validation_method") or "").lower()
        trusted = status in RESOLVER_TRUSTED_STATUSES or status in (
            "sec_edgar", "alpha_vantage", "financial_modeling_prep", "polygon_io", "validation_cache",
        )

        if trusted and not is_placeholder(info.get("name")):
            if sym:
                info["symbol"] = sym
            if is_placeholder(info.get("full_name")):
                info["full_name"] = info.get("name") or info.get("company_name")
            if is_placeholder(info.get("company_name")):
                info["company_name"] = info.get("name") or info.get("full_name")
            return info

        resolved = self.resolve(sym or info.get("symbol"), title)
        resolved_status = str(resolved.get("resolver_status") or "").lower()
        if resolved_status == "web_suggested" and trusted:
            if is_placeholder(info.get("sector")) and resolved.get("sector"):
                info["sector"] = resolved["sector"]
            if is_placeholder(info.get("industry")) and resolved.get("industry"):
                info["industry"] = resolved["industry"]
            if sym:
                info["symbol"] = sym
            return info

        if is_placeholder(info.get("name")):
            info["name"] = resolved["company_name"]
        if is_placeholder(info.get("full_name")):
            info["full_name"] = resolved["full_name"]
        if is_placeholder(info.get("sector")):
            info["sector"] = resolved["sector"]
        if is_placeholder(info.get("industry")):
            info["industry"] = resolved["industry"]
        if sym:
            info["symbol"] = sym
        if not info.get("resolver_status"):
            info["resolver_status"] = resolved.get("resolver_status", "unknown")
        return info

    def enrich_fact_check(
        self, fact_check: Optional[Dict], symbol: Any, title: Optional[str] = None
    ) -> Dict:
        fc = dict(fact_check or {})
        info = self.enrich_company_info(fc.get("company_info"), symbol, title)
        fc["company_info"] = info
        if is_placeholder(fc.get("risk_level")):
            fc["risk_level"] = "HIGH" if not fc.get("is_valid") else "MEDIUM"
        return fc

    def enrich_news_item(
        self,
        item: Dict,
        *,
        allow_yf: bool = True,
        allow_web: bool = True,
        local_only: bool = False,
    ) -> Dict:
        if not isinstance(item, dict):
            return item
        if local_only:
            allow_yf = False
            allow_web = False
        sym = _clean_symbol(item.get("symbol"))
        title = item.get("title") or item.get("summary")
        # Hot-path local enrich: only stamp known CSV tickers
        if not allow_yf and not allow_web and sym and sym not in self._static:
            if sym:
                item["symbol"] = sym
            return item

        resolved = self.resolve(sym, title, allow_yf=allow_yf, allow_web=allow_web)

        if sym:
            item["symbol"] = sym
        if is_placeholder(item.get("company_name")):
            item["company_name"] = resolved["company_name"]
        if is_placeholder(item.get("sector")):
            item["sector"] = resolved["sector"]
        if is_placeholder(item.get("industry")):
            item["industry"] = resolved["industry"]
        if is_placeholder(item.get("source")) and item.get("source"):
            pass
        elif is_placeholder(item.get("source")):
            item["source"] = resolved.get("source", "news")

        fc = item.get("fact_check")
        if isinstance(fc, dict) and (allow_yf or allow_web or sym in self._static):
            item["fact_check"] = self.enrich_fact_check(fc, sym or item.get("symbol"), title)
        return item

    def enrich_signal(self, signal: Dict) -> Dict:
        if not isinstance(signal, dict):
            return signal
        sym = _clean_symbol(signal.get("symbol") or signal.get("ticker"))
        title = signal.get("title") or signal.get("rationale")
        resolved = self.resolve(sym, title)

        if sym:
            signal["symbol"] = sym
            signal["ticker"] = sym
        fc_info = (signal.get("fact_check") or {}).get("company_info") or {}
        trusted_name = fc_info.get("name") or fc_info.get("company_name")
        resolver_status = str(fc_info.get("resolver_status") or fc_info.get("validation_method") or "").lower()
        name_is_trusted = resolver_status in RESOLVER_TRUSTED_STATUSES or resolver_status in (
            "sec_edgar", "alpha_vantage", "financial_modeling_prep", "polygon_io", "validation_cache",
        )
        if is_placeholder(signal.get("company_name")):
            if name_is_trusted and not is_placeholder(trusted_name):
                signal["company_name"] = trusted_name
            else:
                signal["company_name"] = resolved["company_name"]
        if is_placeholder(signal.get("sector")):
            signal["sector"] = resolved["sector"]
        if is_placeholder(signal.get("industry")):
            signal["industry"] = resolved["industry"]

        fc = signal.get("fact_check")
        if isinstance(fc, dict):
            signal["fact_check"] = self.enrich_fact_check(fc, sym, title)
        return signal


def get_resolver() -> CompanyResolver:
    return CompanyResolver.get()


def enrich_metadata(obj: Dict) -> Dict:
    """Enrich a news item or signal dict in place."""
    resolver = get_resolver()
    if "fact_check" in obj or "summary" in obj and "title" in obj:
        return resolver.enrich_news_item(obj)
    return resolver.enrich_signal(obj)


def _valid_ticker(symbol: str) -> bool:
    from engines.news_engine_utils import NewsUtils

    return NewsUtils.is_valid_extracted_ticker(symbol)


def resolve_symbol_from_news_item(
    news_item: Dict,
    *,
    news_extractor: Optional[Callable[[str], str]] = None,
    company_db: Optional[Dict] = None,
) -> str:
    """
    Resolve a tradeable symbol from a news row (mutates news_item['symbol'] on success).
    Handles empty-string placeholders and title-derived tickers.
    """
    if not isinstance(news_item, dict):
        return ""

    sym = _clean_symbol(news_item.get("symbol"))
    if sym and not is_placeholder(sym):
        news_item["symbol"] = sym
        return sym

    title = str(news_item.get("title") or "")
    summary = str(news_item.get("summary") or "")
    text = f"{title} {summary}".strip()
    if not text:
        return ""

    for match in _PARENS_TICKER_RE.finditer(text):
        candidate = _clean_symbol(match.group(1))
        if candidate and _valid_ticker(candidate):
            news_item["symbol"] = candidate
            return candidate

    if news_extractor:
        try:
            extracted = _clean_symbol(news_extractor(text))
            if extracted and _valid_ticker(extracted):
                news_item["symbol"] = extracted
                return extracted
        except Exception:
            pass

    if company_db:
        try:
            from engines.news_engine_utils import NewsUtils

            found = NewsUtils.extract_symbol_from_text(text, company_db)
            if found:
                candidate = _clean_symbol(found)
                if candidate and _valid_ticker(candidate):
                    news_item["symbol"] = candidate
                    return candidate
        except Exception:
            pass

    for pattern, ticker in _HEADLINE_COMPANY_TICKERS:
        if pattern.search(text):
            candidate = _clean_symbol(ticker)
            if candidate and _valid_ticker(candidate):
                news_item["symbol"] = candidate
                return candidate

    return ""
