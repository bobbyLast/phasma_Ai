"""Shared Kalshi API rate limiter — time-based budget (not per-cycle reset abuse)."""

from __future__ import annotations

import threading
import time
from typing import Any, Dict, Optional

import requests


class KalshiRateLimiter:
    """Process-wide token-bucket + 429 cooldown for Kalshi HTTP GETs."""

    def __init__(
        self,
        *,
        min_interval_seconds: float = 1.25,
        max_requests_per_minute: int = 25,
        max_requests_per_cycle: int = 40,
        cooldown_on_429_seconds: float = 45.0,
        cycle_window_seconds: float = 120.0,
        token_capacity: float = 40.0,
        token_refill_per_second: float = 0.4,
    ):
        self.min_interval = max(0.25, float(min_interval_seconds))
        self.max_per_minute = max(1, int(max_requests_per_minute))
        self.max_per_cycle = max(1, int(max_requests_per_cycle))
        self.cooldown_on_429 = max(5.0, float(cooldown_on_429_seconds))
        self.cycle_window = max(30.0, float(cycle_window_seconds))
        self.token_capacity = max(1.0, float(token_capacity))
        self.token_refill = max(0.01, float(token_refill_per_second))
        self._tokens = self.token_capacity
        self._token_ts = time.time()
        self._lock = threading.Lock()
        self._last_ts = 0.0
        self._minute_ts: list = []
        self._cycle_ts: list = []
        self._blocked_until = 0.0
        self._cache: Dict[str, Any] = {}
        self._backoff_exp = 0

    def begin_cycle(self) -> None:
        """Mark a logical cycle start — does NOT wipe the rolling request budget."""
        pass

    def _refill_tokens(self, now: float) -> None:
        elapsed = max(0.0, now - self._token_ts)
        self._tokens = min(self.token_capacity, self._tokens + elapsed * self.token_refill)
        self._token_ts = now

    def _prune_windows(self, now: float) -> None:
        self._minute_ts = [t for t in self._minute_ts if t >= now - 60.0]
        self._cycle_ts = [t for t in self._cycle_ts if t >= now - self.cycle_window]

    def _cache_key(self, url: str, params: Optional[Dict[str, Any]]) -> str:
        if not params:
            return url
        items = "&".join(f"{k}={params[k]}" for k in sorted(params))
        return f"{url}?{items}"

    def get_cached(self, url: str, params: Optional[Dict[str, Any]], ttl: float) -> Optional[Any]:
        key = self._cache_key(url, params)
        with self._lock:
            row = self._cache.get(key)
            if not row:
                return None
            if time.time() - row["ts"] > ttl:
                return None
            return row["data"]

    def set_cached(self, url: str, params: Optional[Dict[str, Any]], data: Any) -> None:
        key = self._cache_key(url, params)
        with self._lock:
            self._cache[key] = {"ts": time.time(), "data": data}

    def wait_turn(self) -> bool:
        """Block until a request is allowed. Returns False if rolling budget exhausted."""
        with self._lock:
            now = time.time()
            self._prune_windows(now)
            self._refill_tokens(now)
            if now < self._blocked_until:
                wait = self._blocked_until - now
            else:
                wait = 0.0

            if self._tokens < 1.0:
                need = (1.0 - self._tokens) / self.token_refill
                wait = max(wait, need)

            if len(self._cycle_ts) >= self.max_per_cycle:
                wait = max(wait, self._cycle_ts[0] + self.cycle_window - now + 0.05)
                if wait > 30.0:
                    return False

            if len(self._minute_ts) >= self.max_per_minute:
                wait = max(wait, 60.0 - (now - self._minute_ts[0]) + 0.05)

            since = now - self._last_ts
            if since < self.min_interval:
                wait = max(wait, self.min_interval - since)

        if wait > 0:
            time.sleep(min(wait, 90.0))

        with self._lock:
            now = time.time()
            self._prune_windows(now)
            self._refill_tokens(now)
            if len(self._cycle_ts) >= self.max_per_cycle or self._tokens < 1.0:
                return False
            self._tokens -= 1.0
            self._last_ts = now
            self._minute_ts.append(now)
            self._cycle_ts.append(now)
            return True

    def trip_429(self, retry_after: Optional[float] = None) -> None:
        wait = self.cooldown_on_429
        if retry_after is not None:
            try:
                wait = max(wait, float(retry_after))
            except (TypeError, ValueError):
                pass
        self._backoff_exp = min(self._backoff_exp + 1, 5)
        wait = min(wait * (2 ** (self._backoff_exp - 1)), 120.0)
        with self._lock:
            self._blocked_until = time.time() + wait
            self._tokens = max(0.0, self._tokens - 2.0)
        print(f"WARNING Kalshi rate-limit cooldown {wait:.1f}s (tokens={self._tokens:.1f})")

    @property
    def cycle_requests(self) -> int:
        with self._lock:
            self._prune_windows(time.time())
            return len(self._cycle_ts)


_GLOBAL: Optional[KalshiRateLimiter] = None
_GLOBAL_LOCK = threading.Lock()


def get_kalshi_rate_limiter(config: Any = None) -> KalshiRateLimiter:
    global _GLOBAL
    with _GLOBAL_LOCK:
        if _GLOBAL is not None:
            return _GLOBAL
        scan = {}
        if config is not None:
            if hasattr(config, "get"):
                scan = config.get("kalshi_scan") or {}
            elif isinstance(config, dict):
                scan = config.get("kalshi_scan") or {}
        _GLOBAL = KalshiRateLimiter(
            min_interval_seconds=float(scan.get("min_request_interval_seconds", 1.25)),
            max_requests_per_minute=int(scan.get("max_requests_per_minute", 25)),
            max_requests_per_cycle=int(scan.get("max_requests_per_cycle", 40)),
            cooldown_on_429_seconds=float(scan.get("cooldown_on_429_seconds", 45)),
            cycle_window_seconds=float(scan.get("cycle_window_seconds", 120)),
            token_capacity=float(scan.get("token_capacity", 40)),
            token_refill_per_second=float(scan.get("token_refill_per_second", 0.4)),
        )
        return _GLOBAL


def kalshi_get_json(
    session: requests.Session,
    url: str,
    *,
    params: Optional[Dict[str, Any]] = None,
    headers: Optional[Dict[str, str]] = None,
    timeout: float = 12,
    config: Any = None,
    cache_ttl: float = 0,
    retries: int = 3,
) -> Optional[Dict[str, Any]]:
    """Rate-limited GET returning JSON dict, or None on failure/budget."""
    limiter = get_kalshi_rate_limiter(config)
    if cache_ttl > 0:
        cached = limiter.get_cached(url, params, cache_ttl)
        if cached is not None:
            return cached

    last_err: Optional[Exception] = None
    for attempt in range(max(1, retries)):
        if not limiter.wait_turn():
            print(f"WARNING Kalshi cycle request budget exhausted — skip {url}")
            return None
        try:
            resp = session.get(url, params=params, headers=headers, timeout=timeout)
            if resp.status_code == 429:
                retry_after = resp.headers.get("Retry-After")
                try:
                    ra = float(retry_after) if retry_after else None
                except (TypeError, ValueError):
                    ra = None
                limiter.trip_429(ra)
                continue
            if resp.status_code >= 400:
                last_err = requests.HTTPError(f"{resp.status_code} {url}")
                if attempt < retries - 1:
                    time.sleep(1.0 * (attempt + 1))
                    continue
                print(f"WARNING Kalshi GET {resp.status_code} for {url}")
                return None
            data = resp.json()
            if cache_ttl > 0 and isinstance(data, dict):
                limiter.set_cached(url, params, data)
            return data if isinstance(data, dict) else None
        except Exception as exc:
            last_err = exc
            if attempt < retries - 1:
                time.sleep(1.0 * (attempt + 1))
                continue
    if last_err:
        print(f"WARNING Kalshi GET error for {url}: {last_err}")
    return None
