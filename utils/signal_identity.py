"""Ensure every trade/alert signal has a real company identity and usable levels.

Root cause of Unknown / n/a on Telegram: signals often never get a trusted
company_name (fact_check blank, social rows bare ticker, derived "$SYM - headline"),
and formatters defaulted missing levels/win-rates to N/A.

This module fills identity + levels in place before post/gate.
"""

from __future__ import annotations

from typing import Any, Dict, Optional, Tuple

from utils.company_resolver import CompanyResolver, is_placeholder, get_resolver

_CRYPTO_NAMES = {
    "BTC": "Bitcoin",
    "ETH": "Ethereum",
    "SOL": "Solana",
    "XRP": "XRP",
    "DOGE": "Dogecoin",
    "ADA": "Cardano",
    "DOT": "Polkadot",
    "MATIC": "Polygon",
    "AVAX": "Avalanche",
    "LINK": "Chainlink",
    "UNI": "Uniswap",
    "ATOM": "Cosmos",
    "BTC-USD": "Bitcoin",
    "ETH-USD": "Ethereum",
}


def _clean_sym(symbol: Any) -> str:
    return str(symbol or "").upper().strip()


def _is_usable_company_name(name: Any, symbol: str = "") -> bool:
    if is_placeholder(name):
        return False
    text = str(name).strip()
    if not text:
        return False
    low = text.lower()
    if low in ("unknown", "n/a", "none", "null", "equities", "market headline"):
        return False
    if "wikipedia" in low or "http://" in low or "https://" in low:
        return False
    if len(text) > 80:
        return False
    if text.startswith("$") and " - " in text:
        return False  # derived "$SYM - headline"
    if symbol and text.upper() == symbol.upper() and len(text) <= 5:
        return False  # bare ticker is not a company name
    return True


def _shorten_name(name: str) -> str:
    text = str(name).strip()
    if len(text) > 80:
        text = text[:77].rstrip() + "..."
    # Prefer first clause of long legal names when bloated
    if " - Wikipedia" in text:
        text = text.split(" - Wikipedia")[0].strip()
    return text


def ensure_signal_identity(signal: Any) -> Tuple[bool, str]:
    """
    Fill company_name / sector / fact_check in place with real values.

    Returns (ok, company_name). ok=False only when symbol missing or unresolvable
    after registry + CSV + yfinance (+ crypto/kalshi specials).
    """
    if signal is None:
        return False, ""
    if not isinstance(signal, dict):
        if hasattr(signal, "__dict__"):
            # Work on a shallow dict view of attrs we care about, write back
            data = {}
            for k in (
                "symbol", "ticker", "company_name", "sector", "industry", "title",
                "rationale", "source", "fact_check", "prediction_market", "trade_type",
                "market_title", "kalshi_signal", "entry_price", "current_price",
                "stop_loss", "stop_price", "target_price",
            ):
                if hasattr(signal, k):
                    data[k] = getattr(signal, k)
            ok, name = ensure_signal_identity(data)
            for k, v in data.items():
                try:
                    setattr(signal, k, v)
                except Exception:
                    pass
            return ok, name
        return False, ""

    sym = _clean_sym(signal.get("symbol") or signal.get("ticker"))
    if not sym:
        return False, ""

    signal["symbol"] = sym
    signal.setdefault("ticker", sym)

    # Kalshi / prediction markets — identity is the market title, not a company
    is_kalshi = (
        sym.startswith("KX")
        or bool(signal.get("kalshi_signal"))
        or str(signal.get("source") or "").lower() in ("kalshi_prediction", "kalshi")
        or str(signal.get("trade_type") or "").upper().startswith("KALSHI")
        or bool(signal.get("prediction_market"))
    )
    if is_kalshi:
        title = (
            signal.get("market_title")
            or signal.get("title")
            or (signal.get("kalshi_analysis") or {}).get("market_title")
            or (signal.get("kalshi_market_data") or {}).get("title")
            or f"Kalshi market {sym}"
        )
        name = _shorten_name(str(title))
        signal["company_name"] = name
        signal["sector"] = "Prediction Markets"
        signal["industry"] = "Prediction Markets"
        fc = signal.get("fact_check") if isinstance(signal.get("fact_check"), dict) else {}
        info = fc.get("company_info") if isinstance(fc.get("company_info"), dict) else {}
        info.update({"name": name, "full_name": name, "company_name": name, "sector": "Prediction Markets"})
        fc["company_info"] = info
        fc["is_valid"] = True
        signal["fact_check"] = fc
        return True, name

    # Crypto
    crypto_key = sym if sym in _CRYPTO_NAMES else (sym.replace("-USD", "") if sym.endswith("-USD") else "")
    if crypto_key in _CRYPTO_NAMES or (sym.endswith("-USD") and crypto_key in _CRYPTO_NAMES):
        name = _CRYPTO_NAMES.get(crypto_key) or _CRYPTO_NAMES.get(sym)
        if name:
            signal["company_name"] = name
            signal["sector"] = "Cryptocurrency"
            signal["industry"] = "Cryptocurrency"
            _stamp_fact_check(signal, name, "Cryptocurrency")
            try:
                from utils.company_identity_registry import get_identity_registry
                get_identity_registry().remember(
                    sym, company_name=name, sector="Cryptocurrency",
                    source="crypto_map", resolver_status="cache_exact",
                )
            except Exception:
                pass
            return True, name

    # Already good?
    existing = signal.get("company_name")
    fc = signal.get("fact_check") if isinstance(signal.get("fact_check"), dict) else {}
    info = fc.get("company_info") if isinstance(fc.get("company_info"), dict) else {}
    for candidate in (existing, info.get("name"), info.get("full_name"), info.get("company_name")):
        if _is_usable_company_name(candidate, sym):
            name = _shorten_name(str(candidate))
            signal["company_name"] = name
            if is_placeholder(signal.get("sector")) or str(signal.get("sector")).lower() == "unknown":
                signal["sector"] = info.get("sector") or signal.get("sector") or "Equities"
            if str(signal.get("sector") or "").lower() == "unknown":
                signal["sector"] = "Equities"
            _stamp_fact_check(signal, name, signal.get("sector") or "Equities")
            return True, name

    # Registry + resolver (yfinance enabled)
    title = signal.get("title") or signal.get("rationale")
    try:
        from utils.company_identity_registry import get_identity_registry
        reg = get_identity_registry()
        reg.stamp_item(signal)
        resolved_alert = reg.resolve_for_alert(signal)
        if _is_usable_company_name(resolved_alert, sym):
            name = _shorten_name(resolved_alert)
            signal["company_name"] = name
            if is_placeholder(signal.get("sector")) or str(signal.get("sector")).lower() == "unknown":
                row = reg.get(sym) or {}
                signal["sector"] = row.get("sector") or "Equities"
            if str(signal.get("sector") or "").lower() == "unknown":
                signal["sector"] = "Equities"
            _stamp_fact_check(signal, name, signal.get("sector") or "Equities")
            return True, name
    except Exception:
        pass

    resolver = get_resolver()
    resolved = resolver.resolve(sym, title, allow_yf=True, allow_web=False)
    name = resolved.get("company_name")
    sector = resolved.get("sector") or "Equities"
    if not _is_usable_company_name(name, sym):
        # Force fresh yfinance (bypass bad cache entries)
        yf_row = resolver._yf_lookup(sym)
        if yf_row and _is_usable_company_name(yf_row.get("company_name"), sym):
            name = yf_row["company_name"]
            sector = yf_row.get("sector") or sector
        else:
            # Last resort: web, then reject wiki blobs
            resolved_web = resolver.resolve(sym, title, allow_yf=True, allow_web=True)
            cand = resolved_web.get("company_name")
            if _is_usable_company_name(cand, sym):
                name = cand
                sector = resolved_web.get("sector") or sector

    if str(sector).lower() in ("unknown", "n/a", ""):
        sector = "Equities"

    if not _is_usable_company_name(name, sym):
        return False, ""

    name = _shorten_name(str(name))
    signal["company_name"] = name
    signal["sector"] = sector
    if is_placeholder(signal.get("industry")) or str(signal.get("industry")).lower() == "unknown":
        signal["industry"] = resolved.get("industry") or sector
    _stamp_fact_check(signal, name, sector)

    try:
        from utils.company_identity_registry import get_identity_registry
        get_identity_registry().remember(
            sym,
            company_name=name,
            sector=sector,
            source="ensure_signal_identity",
            resolver_status=str(resolved.get("resolver_status") or "quote_exact"),
        )
    except Exception:
        pass

    return True, name


def _stamp_fact_check(signal: Dict[str, Any], name: str, sector: str) -> None:
    fc = signal.get("fact_check") if isinstance(signal.get("fact_check"), dict) else {}
    info = fc.get("company_info") if isinstance(fc.get("company_info"), dict) else {}
    info["name"] = name
    info["full_name"] = name
    info["company_name"] = name
    info["sector"] = sector
    fc["company_info"] = info
    fc["is_valid"] = True
    signal["fact_check"] = fc


def ensure_trade_levels(signal: Dict[str, Any]) -> Dict[str, Any]:
    """Fill entry/stop/target so Telegram never prints N/A for levels when price exists."""
    if not isinstance(signal, dict):
        return signal
    try:
        entry = float(
            signal.get("entry_price")
            or signal.get("current_price")
            or signal.get("price")
            or 0
        )
    except (TypeError, ValueError):
        entry = 0.0

    if entry <= 0:
        sym = _clean_sym(signal.get("symbol") or signal.get("ticker"))
        if sym and not sym.startswith("KX"):
            try:
                from utils.robust_price_fetcher import get_robust_price_fetcher
                px = get_robust_price_fetcher().get_real_price(sym)
                if px and float(px) > 0:
                    entry = float(px)
                    signal["current_price"] = entry
                    signal["entry_price"] = entry
            except Exception:
                pass

    if entry > 0:
        signal["entry_price"] = signal.get("entry_price") or entry
        signal["current_price"] = signal.get("current_price") or entry
        try:
            from utils.stock_reward_risk import apply_stock_rr_targets
            apply_stock_rr_targets(signal, invent_target=True)
        except Exception:
            if not signal.get("stop_loss") and not signal.get("stop_price"):
                signal["stop_loss"] = round(entry * 0.95, 4)
                signal["stop_price"] = signal["stop_loss"]
            if not signal.get("target_price"):
                risk = abs(entry - float(signal.get("stop_loss") or entry * 0.95))
                signal["target_price"] = round(entry + 5.0 * risk, 4)
    return signal


def format_money(value: Any) -> str:
    """Format a price for Telegram — never 'N/A' when numeric; else 'price pending'."""
    try:
        v = float(value)
        if v > 0:
            if v >= 100:
                return f"{v:.2f}"
            if v >= 1:
                return f"{v:.2f}"
            return f"{v:.4f}"
    except (TypeError, ValueError):
        pass
    return "price pending"


def format_sample_label(label: Any, *, empty: str = "building sample") -> str:
    """Win-rate / sample labels — never bare n/a or Unknown."""
    if label is None:
        return empty
    text = str(label).strip()
    if not text:
        return empty
    low = text.lower()
    if low in ("n/a", "na", "unknown", "none"):
        return empty
    # Ledger often returns "n/a - building sample" — strip the n/a prefix
    for prefix in ("n/a - ", "n/a – ", "n/a — ", "na - ", "unknown - "):
        if low.startswith(prefix):
            rest = text[len(prefix):].strip()
            return rest if rest else empty
    if low.startswith("n/a"):
        return empty
    return text
