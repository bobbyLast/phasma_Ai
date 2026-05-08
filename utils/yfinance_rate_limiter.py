"""Shared market-data rate limiter to avoid request bursts."""

import os
import threading
import time

_MIN_INTERVAL = float(os.getenv("MARKET_DATA_MIN_INTERVAL", os.getenv("YFINANCE_MIN_INTERVAL", "1.5")))
_last_call = 0.0
_lock = threading.Lock()


def set_min_interval(seconds: float) -> None:
    """Override the global market-data minimum interval in seconds."""
    global _MIN_INTERVAL
    _MIN_INTERVAL = max(0.1, float(seconds))


def rate_limit() -> None:
    """Block until the global market-data rate limit window has passed."""
    global _last_call
    with _lock:
        now = time.time()
        wait_time = _MIN_INTERVAL - (now - _last_call)
        if wait_time > 0:
            time.sleep(wait_time)
        _last_call = time.time()


def throttled_history(symbol: str, **kwargs):
    """Fetch ticker history with global rate limiting."""
    rate_limit()
    import yfinance as yf

    return yf.Ticker(symbol).history(**kwargs)


def throttled_info(symbol: str):
    """Fetch ticker info with global rate limiting."""
    rate_limit()
    import yfinance as yf

    return yf.Ticker(symbol).info
