"""
Web search fallback for symbol → company name resolution.
Provider chain (default): DuckDuckGo (no key) → Brave → Google CSE when env keys exist.
"""

from __future__ import annotations

import json
import logging
import os
import re
import time
import warnings
from typing import Any, Dict, List, Optional, Tuple
import requests

logger = logging.getLogger(__name__)

_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)
_DEFAULT_PROVIDERS = (
    "duckduckgo",
    "yahoo_finance",
    "google_finance",
    "brave",
    "google",
    "searxng",
)
_CACHE_TTL = 6 * 3600
_SEARCH_CACHE: Dict[str, Dict[str, Any]] = {}

_PLACEHOLDER_NAMES = frozenset({
    "", "unknown", "UNKNOWN", "n/a", "N/A", "null", "None",
})

_JUNK_SUFFIXES = re.compile(
    r"\s*[-|–:]\s*(?:Stock\s+Price|Quote|Overview|Profile|News|Chart|"
    r"NYSE|NASDAQ|AMEX|Investor\s+Relations).*$",
    re.IGNORECASE,
)
_STOCK_NOISE = re.compile(
    r"\b(?:stock|ticker|quote|share\s+price|market\s+cap|NYSE|NASDAQ|AMEX)\b",
    re.IGNORECASE,
)

_SECTOR_CATEGORY_NAMES = frozenset({
    "technology", "healthcare", "financial services", "communication services",
    "consumer cyclical", "consumer defensive", "industrials", "energy",
    "utilities", "real estate", "basic materials", "equities", "financials",
    "consumer discretionary", "consumer staples", "materials", "information technology",
})


def is_sector_category_name(name: Optional[str]) -> bool:
    if not name:
        return False
    normalized = re.sub(r"\s+", " ", str(name).strip().lower())
    if normalized in _SECTOR_CATEGORY_NAMES:
        return True
    for sector in _SECTOR_CATEGORY_NAMES:
        if normalized == sector or normalized.startswith(f"{sector} "):
            return True
        if normalized.endswith(f" {sector}") and len(normalized.split()) <= 4:
            return True
    return False


_SECTOR_KEYWORDS: Tuple[Tuple[str, Tuple[str, ...]], ...] = (
    ("Technology", ("technology", "software", "semiconductor", " cloud ", " ai ", " cyber")),
    ("Healthcare", ("healthcare", "pharmaceutical", "biotech", " medical ", " therapeutics")),
    ("Financial Services", ("bank", "financial", "insurance", " asset management", " capital ")),
    ("Energy", (" oil ", " gas ", "energy", " petroleum", " renewable")),
    ("Consumer Cyclical", ("retail", " e-commerce", " automotive", " consumer ")),
    ("Industrials", ("industrial", " aerospace", " defense", " manufacturing")),
    ("Real Estate", (" reit", " real estate", " property ")),
    ("Utilities", (" utility", " utilities", " electric ")),
    ("Communication Services", (" telecom", " media ", " streaming")),
    ("Basic Materials", (" mining", " metals", " chemicals", " materials")),
)


def _parse_env_bool(name: str) -> Optional[bool]:
    raw = os.getenv(name)
    if raw is None or not str(raw).strip():
        return None
    return str(raw).strip().lower() in ("1", "true", "yes", "on")


def _parse_env_providers(name: str) -> Optional[List[str]]:
    raw = os.getenv(name)
    if raw is None or not str(raw).strip():
        return None
    return [p.strip() for p in raw.split(",") if p.strip()]


def _log_safe_text(text: str, max_len: int = 120) -> str:
    """ASCII-safe preview for Windows console logging (cp1252)."""
    snippet = (text or "")[:max_len]
    return snippet.encode("ascii", errors="replace").decode("ascii")


def _parse_env_float(name: str) -> Optional[float]:
    raw = os.getenv(name)
    if raw is None or not str(raw).strip():
        return None
    try:
        return float(str(raw).strip())
    except ValueError:
        return None


def _ddgs_backend() -> str:
    """ddgs metasearch backend(s); default avoids slow/unreliable auto engines (e.g. mojeek)."""
    raw = os.getenv("DDGS_BACKEND", "duckduckgo").strip()
    return raw or "duckduckgo"


def _ddgs_timeout() -> int:
    raw = os.getenv("DDGS_TIMEOUT", "8").strip()
    try:
        return max(1, int(float(raw)))
    except ValueError:
        return 8


def _load_web_search_config(project_root: Optional[str] = None) -> Dict[str, Any]:
    """Load web search behavior: env vars override config.json (legacy)."""
    cfg: Dict[str, Any] = {
        "enabled": True,
        "providers": list(_DEFAULT_PROVIDERS),
        "cache_ttl_hours": 6,
    }

    root = project_root or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    path = os.path.join(root, "config.json")
    if os.path.isfile(path):
        try:
            with open(path, encoding="utf-8") as f:
                file_cfg = json.load(f)
            ws = file_cfg.get("web_search") or {}
            if isinstance(ws, dict):
                cfg.update({k: v for k, v in ws.items() if v is not None})
        except Exception:
            pass

    enabled = _parse_env_bool("WEB_SEARCH_ENABLED")
    if enabled is not None:
        cfg["enabled"] = enabled

    providers = _parse_env_providers("WEB_SEARCH_PROVIDERS")
    if providers:
        cfg["providers"] = providers

    ttl = _parse_env_float("WEB_SEARCH_CACHE_TTL_HOURS")
    if ttl is not None:
        cfg["cache_ttl_hours"] = ttl

    return cfg


def _title_snippet(title: Optional[str], max_len: int = 50) -> str:
    if not title:
        return ""
    text = re.sub(r"\s+", " ", str(title)).strip()
    if len(text) > max_len:
        return text[: max_len - 3].rstrip() + "..."
    return text


def build_queries(symbol: str, title: Optional[str] = None) -> List[str]:
    sym = symbol.upper().strip()
    if not sym:
        return []
    queries = [
        f'"{sym}" stock ticker company name',
        f'"{sym}" NYSE company',
        f"{sym} stock company name sector",
    ]
    snippet = _title_snippet(title)
    if snippet:
        queries.append(f'"{sym}" {snippet}')
    return queries


def _guess_sector(text: str) -> str:
    lower = f" {text.lower()} "
    for sector, keywords in _SECTOR_KEYWORDS:
        if any(kw in lower for kw in keywords):
            return sector
    return "Equities"


def _clean_company_name(name: str, symbol: str) -> str:
    text = re.sub(r"\s+", " ", (name or "").strip())
    if not text:
        return ""
    text = _JUNK_SUFFIXES.sub("", text).strip()
    text = _STOCK_NOISE.sub("", text).strip(" -|–:")
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) < 2 or text.upper() in _PLACEHOLDER_NAMES:
        return ""
    if text.upper() == symbol.upper() and len(text) <= 6:
        return ""
    return text


def _extract_name_from_text(text: str, symbol: str) -> str:
    if not text:
        return ""
    sym = symbol.upper()
    patterns = [
        rf"{re.escape(sym)}\s*[|\-–:]\s*(.+?)(?:\s*[\(\[]|\s+Stock|\s+Quote|$)",
        rf"(.+?)\s*\(\s*{re.escape(sym)}\s*\)",
        rf"(.+?)\s+-\s+{re.escape(sym)}\b",
        rf"{re.escape(sym)}\s+is\s+(.+?)(?:\.|,|\s+—|\s+-|$)",
        rf"(?:NYSE|NASDAQ|AMEX):\s*{re.escape(sym)}\s*[-–]\s*(.+?)(?:\.|$)",
    ]
    for pat in patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            candidate = _clean_company_name(m.group(1), sym)
            if candidate and len(candidate) >= 3:
                return candidate

    # Title before parenthetical ticker, e.g. "Acme Corp (ACME) Stock"
    m = re.match(rf"^(.{{3,80}}?)\s*\(\s*{re.escape(sym)}\s*\)", text, re.IGNORECASE)
    if m:
        candidate = _clean_company_name(m.group(1), sym)
        if candidate:
            return candidate

    # Strip leading ticker and separators
    stripped = re.sub(rf"^{re.escape(sym)}\s*[-|–:\s]+", "", text, flags=re.IGNORECASE)
    candidate = _clean_company_name(stripped, sym)
    if candidate and len(candidate) >= 3:
        return candidate
    return ""


def parse_search_hits(
    symbol: str, hits: List[Dict[str, str]]
) -> Optional[Dict[str, str]]:
    sym = symbol.upper().strip()
    if not sym or not hits:
        return None

    best_name = ""
    best_score = 0
    combined_text = []

    for hit in hits:
        title = (hit.get("title") or "").strip()
        snippet = (hit.get("snippet") or "").strip()
        combined_text.append(f"{title} {snippet}")

        for text in (title, snippet, f"{title} {snippet}"):
            if sym not in text.upper() and sym not in (hit.get("url") or "").upper():
                continue
            name = _extract_name_from_text(text, sym)
            if not name:
                continue
            score = len(name)
            if " inc" in name.lower() or " corp" in name.lower() or " ltd" in name.lower():
                score += 10
            if score > best_score:
                best_score = score
                best_name = name

    if not best_name or is_sector_category_name(best_name):
        return None

    sector = _guess_sector(" ".join(combined_text[:5]))
    return {
        "company_name": best_name,
        "sector": sector,
        "industry": sector,
    }


class WebSearchResolver:
    """Multi-provider web search for company metadata."""

    def __init__(self, project_root: Optional[str] = None):
        self._cfg = _load_web_search_config(project_root)
        ttl_hours = float(self._cfg.get("cache_ttl_hours", 6))
        self._cache_ttl = int(ttl_hours * 3600)
        self._providers = self._normalize_providers(self._cfg.get("providers"))

    @staticmethod
    def _normalize_providers(raw: Any) -> List[str]:
        if not raw:
            return list(_DEFAULT_PROVIDERS)
        if isinstance(raw, str):
            raw = [raw]
        out = []
        for p in raw:
            key = str(p).strip().lower()
            if key and key not in out:
                out.append(key)
        return out or list(_DEFAULT_PROVIDERS)

    @property
    def enabled(self) -> bool:
        return bool(self._cfg.get("enabled", True))

    def _cache_get(self, symbol: str) -> Optional[Dict[str, str]]:
        cached = _SEARCH_CACHE.get(symbol.upper())
        if not cached:
            return None
        if time.time() - cached.get("_ts", 0) >= self._cache_ttl:
            _SEARCH_CACHE.pop(symbol.upper(), None)
            return None
        return {k: v for k, v in cached.items() if not k.startswith("_")}

    def _cache_set(self, symbol: str, record: Dict[str, str]) -> None:
        _SEARCH_CACHE[symbol.upper()] = {**record, "_ts": time.time()}

    def _provider_available(self, name: str) -> bool:
        if name in ("duckduckgo", "yahoo_finance", "google_finance"):
            return True
        if name == "brave":
            return bool(os.getenv("BRAVE_SEARCH_API_KEY", "").strip())
        if name == "google":
            return bool(
                os.getenv("GOOGLE_API_KEY", "").strip()
                and os.getenv("GOOGLE_CSE_ID", "").strip()
            )
        if name in ("searx", "searxng"):
            return bool(os.getenv("SEARXNG_URL", "").strip())
        return False

    def _search_yahoo_finance(self, symbol: str, query: str) -> List[Dict[str, str]]:
        hits: List[Dict[str, str]] = []
        try:
            resp = requests.get(
                "https://query2.finance.yahoo.com/v1/finance/search",
                params={"q": symbol},
                headers={"User-Agent": _USER_AGENT},
                timeout=12,
            )
            resp.raise_for_status()
            for item in (resp.json().get("quotes") or [])[:6]:
                if str(item.get("symbol", "")).upper() != symbol.upper():
                    continue
                name = (
                    item.get("longname")
                    or item.get("shortname")
                    or item.get("quoteType")
                )
                if not name:
                    continue
                sector = item.get("sector") or item.get("industry") or ""
                hits.append({
                    "title": f"{name} ({symbol})",
                    "snippet": f"{sector} {item.get('exchDisp', '')}".strip(),
                    "url": f"https://finance.yahoo.com/quote/{symbol}",
                })
                break
        except Exception as exc:
            logger.debug("Yahoo Finance search failed for %s: %s", symbol, exc)
        return hits

    def _search_google_finance(self, symbol: str, query: str) -> List[Dict[str, str]]:
        hits: List[Dict[str, str]] = []
        exchanges = ("NASDAQ", "NYSE", "AMEX")
        for exch in exchanges:
            url = f"https://www.google.com/finance/quote/{symbol}:{exch}"
            try:
                resp = requests.get(
                    url,
                    headers={"User-Agent": _USER_AGENT},
                    timeout=12,
                )
                if resp.status_code != 200:
                    continue
                title = ""
                m = re.search(r"<title[^>]*>([^<]+)</title>", resp.text, re.IGNORECASE)
                if m:
                    title = re.sub(r"\s+", " ", m.group(1)).strip()
                if symbol.upper() not in title.upper():
                    continue
                hits.append({
                    "title": title,
                    "snippet": query,
                    "url": url,
                })
                break
            except Exception as exc:
                logger.debug("Google Finance fetch failed for %s:%s: %s", symbol, exch, exc)
        return hits

    def _search_duckduckgo(self, query: str) -> List[Dict[str, str]]:
        hits: List[Dict[str, str]] = []

        try:
            try:
                from ddgs import DDGS
            except ImportError:
                from duckduckgo_search import DDGS  # type: ignore[no-redef]

            backend = _ddgs_backend()
            timeout = _ddgs_timeout()
            ddgs_logger = logging.getLogger("ddgs")
            prev_level = ddgs_logger.level
            ddgs_logger.setLevel(logging.WARNING)
            try:
                with warnings.catch_warnings():
                    warnings.filterwarnings("ignore", category=RuntimeWarning)
                    for item in DDGS(timeout=timeout).text(
                        query, max_results=8, backend=backend
                    ) or []:
                        title = (item.get("title") or "").strip()
                        if not title:
                            continue
                        hits.append({
                            "title": title,
                            "snippet": (item.get("body") or "").strip(),
                            "url": item.get("href") or item.get("url") or "",
                        })
            finally:
                ddgs_logger.setLevel(prev_level)
            if hits:
                return hits
        except ImportError:
            pass
        except Exception as exc:
            logger.debug(
                "ddgs search failed for %r (backend=%s): %s",
                query,
                _ddgs_backend(),
                exc,
            )

        try:
            from bs4 import BeautifulSoup
        except ImportError:
            return self._search_duckduckgo_instant(query, hits)

        try:
            resp = requests.post(
                "https://html.duckduckgo.com/html/",
                data={"q": query},
                headers={
                    "User-Agent": _USER_AGENT,
                    "Accept": "text/html,application/xhtml+xml",
                    "Accept-Language": "en-US,en;q=0.9",
                },
                timeout=12,
            )
            if resp.status_code != 200:
                logger.debug(
                    "DuckDuckGo HTML returned %s for %r (often bot challenge)",
                    resp.status_code,
                    query,
                )
            else:
                soup = BeautifulSoup(resp.text, "lxml")
                for block in soup.select(".result, article[data-testid='result']")[:8]:
                    a = block.select_one(
                        "a.result__a, a[data-testid='result-title-a'], h2 a"
                    )
                    sn = block.select_one(
                        ".result__snippet, [data-result='snippet'], .result-snippet"
                    )
                    if not a:
                        continue
                    hits.append({
                        "title": a.get_text(" ", strip=True),
                        "snippet": sn.get_text(" ", strip=True) if sn else "",
                        "url": a.get("href", ""),
                    })
        except Exception as exc:
            logger.debug("DuckDuckGo HTML search failed for %r: %s", query, exc)

        if hits:
            return hits
        return self._search_duckduckgo_instant(query, hits)

    def _search_duckduckgo_instant(
        self, query: str, hits: Optional[List[Dict[str, str]]] = None
    ) -> List[Dict[str, str]]:
        out: List[Dict[str, str]] = list(hits or [])
        instant_query = re.sub(r'["\']', "", query).strip()
        instant_query = re.sub(
            r"\b(?:stock|ticker|company name|sector)\b", "", instant_query, flags=re.I
        )
        instant_query = re.sub(r"\s+", " ", instant_query).strip() or query
        try:
            resp = requests.get(
                "https://api.duckduckgo.com/",
                params={"q": instant_query, "format": "json", "no_redirect": 1},
                headers={"User-Agent": _USER_AGENT},
                timeout=10,
            )
            resp.raise_for_status()
            data = resp.json()
            abstract = (data.get("AbstractText") or "").strip()
            heading = (data.get("Heading") or "").strip()
            if heading or abstract:
                out.append({
                    "title": heading or query,
                    "snippet": abstract,
                    "url": data.get("AbstractURL") or "",
                })
        except Exception as exc:
            logger.debug("DuckDuckGo instant API failed for %r: %s", query, exc)
        return out

    def _search_brave(self, query: str) -> List[Dict[str, str]]:
        key = os.getenv("BRAVE_SEARCH_API_KEY", "").strip()
        if not key:
            return []
        hits: List[Dict[str, str]] = []
        try:
            resp = requests.get(
                "https://api.search.brave.com/res/v1/web/search",
                params={"q": query, "count": 8},
                headers={
                    "Accept": "application/json",
                    "X-Subscription-Token": key,
                },
                timeout=12,
            )
            resp.raise_for_status()
            data = resp.json()
            for item in (data.get("web") or {}).get("results") or []:
                hits.append({
                    "title": item.get("title") or "",
                    "snippet": item.get("description") or "",
                    "url": item.get("url") or "",
                })
        except Exception as exc:
            logger.debug("Brave search failed for %r: %s", query, exc)
        return hits

    def _search_google(self, query: str) -> List[Dict[str, str]]:
        api_key = os.getenv("GOOGLE_API_KEY", "").strip()
        cse_id = os.getenv("GOOGLE_CSE_ID", "").strip()
        if not api_key or not cse_id:
            return []
        hits: List[Dict[str, str]] = []
        try:
            resp = requests.get(
                "https://www.googleapis.com/customsearch/v1",
                params={"key": api_key, "cx": cse_id, "q": query, "num": 8},
                timeout=12,
            )
            resp.raise_for_status()
            data = resp.json()
            for item in data.get("items") or []:
                hits.append({
                    "title": item.get("title") or "",
                    "snippet": item.get("snippet") or "",
                    "url": item.get("link") or "",
                })
        except Exception as exc:
            logger.debug("Google CSE search failed for %r: %s", query, exc)
        return hits

    def _search_searxng(self, query: str) -> List[Dict[str, str]]:
        base = os.getenv("SEARXNG_URL", "").strip().rstrip("/")
        if not base:
            return []
        hits: List[Dict[str, str]] = []
        try:
            resp = requests.get(
                f"{base}/search",
                params={"q": query, "format": "json", "categories": "general"},
                headers={"User-Agent": _USER_AGENT},
                timeout=12,
            )
            resp.raise_for_status()
            data = resp.json()
            for item in (data.get("results") or [])[:8]:
                hits.append({
                    "title": item.get("title") or "",
                    "snippet": item.get("content") or item.get("snippet") or "",
                    "url": item.get("url") or "",
                })
        except Exception as exc:
            logger.debug("SearXNG search failed for %r: %s", query, exc)
        return hits

    def _run_provider(
        self, provider: str, symbol: str, query: str
    ) -> List[Dict[str, str]]:
        if provider == "yahoo_finance":
            return self._search_yahoo_finance(symbol, query)
        if provider == "google_finance":
            return self._search_google_finance(symbol, query)
        if provider == "duckduckgo":
            return self._search_duckduckgo(query)
        if provider == "brave":
            return self._search_brave(query)
        if provider == "google":
            return self._search_google(query)
        if provider in ("searx", "searxng"):
            return self._search_searxng(query)
        return []

    def lookup(self, symbol: str, title: Optional[str] = None) -> Optional[Dict[str, str]]:
        sym = symbol.upper().strip()
        if not sym or not self.enabled:
            return None

        cached = self._cache_get(sym)
        if cached:
            return cached

        active_providers = [
            p for p in self._providers if self._provider_available(p)
        ]
        if not active_providers:
            return None

        for query in build_queries(sym, title):
            for provider in active_providers:
                hits = self._run_provider(provider, sym, query)
                parsed = parse_search_hits(sym, hits)
                if parsed:
                    record = {
                        "company_name": parsed["company_name"],
                        "sector": parsed["sector"],
                        "industry": parsed["industry"],
                        "source": f"web_search:{provider}",
                    }
                    self._cache_set(sym, record)
                    logger.info(
                        "Resolved %s via web search: %s (provider=%s)",
                        sym,
                        _log_safe_text(record["company_name"]),
                        provider,
                    )
                    return record
        return None


_resolver_instance: Optional[WebSearchResolver] = None


def get_web_search_resolver() -> WebSearchResolver:
    global _resolver_instance
    if _resolver_instance is None:
        _resolver_instance = WebSearchResolver()
    return _resolver_instance


def web_search_lookup(symbol: str, title: Optional[str] = None) -> Optional[Dict[str, str]]:
    return get_web_search_resolver().lookup(symbol, title)
