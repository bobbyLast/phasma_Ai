"""Drop-in yfinance compatibility shim backed by real API providers."""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import pandas as pd
import requests


def _alpha_key() -> Optional[str]:
    return os.getenv("ALPHA_VANTAGE_KEY") or os.getenv("ALPHA_VANTAGE_API_KEY")


def _finnhub_key() -> Optional[str]:
    return os.getenv("FINNHUB_API_KEY")


def _map_symbol(symbol: str) -> str:
    symbol_map = {
        "^VIX": "TVC:VIX",
        "^TNX": "TVC:US10Y",
        "^IRX": "TVC:US03MY",
        "^N225": "INDEX:NKY",
        "^JP10Y": "TVC:JP10Y",
        "JPY=X": "OANDA:USD_JPY",
        "DX-Y.NYB": "TVC:DXY",
    }
    return symbol_map.get(symbol, symbol)


def _period_days(period: str) -> int:
    period = (period or "1mo").lower()
    mapping = {
        "1d": 1,
        "2d": 2,
        "5d": 5,
        "7d": 7,
        "14d": 14,
        "1mo": 30,
        "2mo": 60,
        "3mo": 90,
        "6mo": 180,
        "1y": 365,
        "5y": 365 * 5,
    }
    return mapping.get(period, 30)


def _to_history_df(rows: List[Dict]) -> pd.DataFrame:
    if not rows:
        return pd.DataFrame(columns=["Open", "High", "Low", "Close", "Volume"])
    hist = pd.DataFrame(rows)
    hist["Date"] = pd.to_datetime(hist["Date"])
    hist = hist.sort_values("Date").set_index("Date")
    return hist[["Open", "High", "Low", "Close", "Volume"]]


def _fetch_finnhub_history(symbol: str, period: str, interval: str = "1d") -> pd.DataFrame:
    key = _finnhub_key()
    if not key:
        return pd.DataFrame()

    now_ts = int(datetime.now().timestamp())
    lookback_days = _period_days(period)
    from_ts = int((datetime.now() - timedelta(days=lookback_days)).timestamp())
    resolution = "1" if interval == "1m" else "D"

    try:
        resp = requests.get(
            "https://finnhub.io/api/v1/stock/candle",
            params={
                "symbol": _map_symbol(symbol),
                "resolution": resolution,
                "from": from_ts,
                "to": now_ts,
                "token": key,
            },
            timeout=10,
        )
        data = resp.json()
        if data.get("s") != "ok":
            return pd.DataFrame()
        rows = []
        for idx, ts in enumerate(data.get("t", [])):
            rows.append(
                {
                    "Date": datetime.fromtimestamp(ts),
                    "Open": float(data.get("o", [0])[idx]),
                    "High": float(data.get("h", [0])[idx]),
                    "Low": float(data.get("l", [0])[idx]),
                    "Close": float(data.get("c", [0])[idx]),
                    "Volume": float(data.get("v", [0])[idx]),
                }
            )
        return _to_history_df(rows)
    except Exception:
        return pd.DataFrame()


def _fetch_alpha_history(symbol: str, period: str) -> pd.DataFrame:
    key = _alpha_key()
    if not key:
        return pd.DataFrame()
    try:
        resp = requests.get(
            "https://www.alphavantage.co/query",
            params={
                "function": "TIME_SERIES_DAILY",
                "symbol": symbol,
                "apikey": key,
                "outputsize": "full" if _period_days(period) > 30 else "compact",
            },
            timeout=10,
        )
        data = resp.json()
        series = data.get("Time Series (Daily)", {})
        rows = []
        for date_str, values in series.items():
            rows.append(
                {
                    "Date": date_str,
                    "Open": float(values.get("1. open", 0.0)),
                    "High": float(values.get("2. high", 0.0)),
                    "Low": float(values.get("3. low", 0.0)),
                    "Close": float(values.get("4. close", 0.0)),
                    "Volume": float(values.get("5. volume", 0.0)),
                }
            )
        hist = _to_history_df(rows)
        return hist.tail(_period_days(period))
    except Exception:
        return pd.DataFrame()


def _fetch_quote(symbol: str) -> Dict:
    key = _finnhub_key()
    if key:
        try:
            resp = requests.get(
                "https://finnhub.io/api/v1/quote",
                params={"symbol": _map_symbol(symbol), "token": key},
                timeout=8,
            )
            q = resp.json()
            if q.get("c"):
                return {
                    "currentPrice": float(q.get("c", 0.0)),
                    "regularMarketPrice": float(q.get("c", 0.0)),
                    "previousClose": float(q.get("pc", 0.0)),
                    "open": float(q.get("o", 0.0)),
                    "dayHigh": float(q.get("h", 0.0)),
                    "dayLow": float(q.get("l", 0.0)),
                }
        except Exception:
            pass

    alpha = _alpha_key()
    if alpha:
        try:
            resp = requests.get(
                "https://www.alphavantage.co/query",
                params={"function": "GLOBAL_QUOTE", "symbol": symbol, "apikey": alpha},
                timeout=8,
            )
            q = resp.json().get("Global Quote", {})
            if q.get("05. price"):
                price = float(q.get("05. price", 0.0))
                return {
                    "currentPrice": price,
                    "regularMarketPrice": price,
                    "previousClose": float(q.get("08. previous close", price)),
                    "open": float(q.get("02. open", price)),
                    "dayHigh": float(q.get("03. high", price)),
                    "dayLow": float(q.get("04. low", price)),
                    "volume": float(q.get("06. volume", 0.0)),
                }
        except Exception:
            pass
    return {}


@dataclass
class _OptionChain:
    calls: pd.DataFrame
    puts: pd.DataFrame


class Ticker:
    """Minimal yfinance.Ticker-compatible object."""

    def __init__(self, symbol: str):
        self.symbol = symbol
        self._info: Optional[Dict] = None

    @property
    def info(self) -> Dict:
        if self._info is not None:
            return self._info

        info = _fetch_quote(self.symbol)
        key = _finnhub_key()
        if key:
            try:
                resp = requests.get(
                    "https://finnhub.io/api/v1/stock/profile2",
                    params={"symbol": _map_symbol(self.symbol), "token": key},
                    timeout=8,
                )
                prof = resp.json()
                if prof:
                    info.setdefault("longName", prof.get("name"))
                    info.setdefault("marketCap", prof.get("marketCapitalization"))
                    info.setdefault("currency", prof.get("currency"))
                    info.setdefault("country", prof.get("country"))
                    info.setdefault("exchange", prof.get("exchange"))
            except Exception:
                pass
        self._info = info
        return info

    def history(
        self,
        period: str = "1mo",
        interval: str = "1d",
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        **kwargs,
    ) -> pd.DataFrame:
        if start and end:
            days = max((end - start).days, 1)
            period = f"{days}d"

        hist = _fetch_finnhub_history(self.symbol, period=period, interval=interval)
        if hist.empty:
            hist = _fetch_alpha_history(self.symbol, period=period)
        return hist

    @property
    def options(self) -> List[str]:
        # Conservative default: no options data unless a dedicated provider is wired.
        return []

    def option_chain(self, date: Optional[str] = None):
        calls = pd.DataFrame(columns=["strike", "bid", "ask", "volume", "openInterest", "impliedVolatility"])
        puts = pd.DataFrame(columns=["strike", "bid", "ask", "volume", "openInterest", "impliedVolatility"])
        return _OptionChain(calls=calls, puts=puts)


def download(
    tickers: str,
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
    period: str = "1mo",
    interval: str = "1d",
    progress: bool = False,
    **kwargs,
) -> pd.DataFrame:
    symbol = tickers.split()[0].split(",")[0]
    ticker = Ticker(symbol)
    return ticker.history(period=period, interval=interval, start=start, end=end)
