"""Source health + cycle context mode — honest status for trading gates."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional


class ContextMode(str, Enum):
    NORMAL = "NORMAL"
    DEGRADED_RESEARCH = "DEGRADED_RESEARCH"
    STALE_CONTEXT = "STALE_CONTEXT"
    EXECUTION_BLOCKED = "EXECUTION_BLOCKED"


class SourceStatus(str, Enum):
    CONFIGURED = "configured"
    HEALTHY = "healthy"
    RETURNING_EVIDENCE = "returning_evidence"
    STATUS_ONLY = "status_only"
    FAILED = "failed"
    PLACEHOLDER = "placeholder"
    STALE = "stale"
    MISSING = "missing"


@dataclass
class SourceHealthEntry:
    name: str
    status: str
    last_success_at: Optional[str] = None
    age_seconds: Optional[float] = None
    detail: str = ""
    items: int = 0


@dataclass
class SourceHealthSnapshot:
    entries: List[SourceHealthEntry] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "created_at": self.created_at,
            "entries": [
                {
                    "name": e.name,
                    "status": e.status,
                    "last_success_at": e.last_success_at,
                    "age_seconds": e.age_seconds,
                    "detail": e.detail,
                    "items": e.items,
                }
                for e in self.entries
            ],
        }

    @classmethod
    def from_dict(cls, data: Optional[Dict[str, Any]]) -> "SourceHealthSnapshot":
        if not data:
            return cls()
        entries = []
        for row in data.get("entries") or []:
            if isinstance(row, dict):
                entries.append(
                    SourceHealthEntry(
                        name=str(row.get("name") or ""),
                        status=str(row.get("status") or SourceStatus.MISSING.value),
                        last_success_at=row.get("last_success_at"),
                        age_seconds=row.get("age_seconds"),
                        detail=str(row.get("detail") or ""),
                        items=int(row.get("items") or 0),
                    )
                )
        return cls(entries=entries, created_at=str(data.get("created_at") or ""))


def _age_from_ts(ts: Any) -> Optional[float]:
    if ts is None:
        return None
    try:
        if isinstance(ts, (int, float)):
            return max(0.0, datetime.now(timezone.utc).timestamp() - float(ts))
        text = str(ts).replace("Z", "+00:00")
        dt = datetime.fromisoformat(text)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return max(0.0, (datetime.now(timezone.utc) - dt).total_seconds())
    except Exception:
        return None


def compute_snapshot_ages(
    *,
    market_snapshot: Optional[Dict[str, Any]] = None,
    news_events: Optional[List] = None,
    prediction_markets: Optional[List] = None,
    created_at: Optional[str] = None,
) -> Dict[str, float]:
    """Best-effort ages in seconds for each snapshot plane."""
    ages: Dict[str, float] = {}
    cycle_age = _age_from_ts(created_at) or 0.0

    market_ts = None
    if market_snapshot:
        for row in market_snapshot.values():
            if isinstance(row, dict) and row.get("ts"):
                market_ts = row.get("ts")
                break
    ages["market"] = _age_from_ts(market_ts) if market_ts else (99999.0 if not market_snapshot else cycle_age)
    ages["news"] = cycle_age if news_events else 99999.0
    ages["kalshi"] = cycle_age if prediction_markets else 99999.0
    return ages


def derive_context_mode(
    *,
    market_snapshot: Optional[Dict[str, Any]],
    prices: Optional[Dict[str, float]],
    snapshot_ages: Optional[Dict[str, float]],
    source_health: Optional[SourceHealthSnapshot] = None,
    price_fetch_failed: bool = False,
    news_from_stale_fallback: bool = False,
    max_market_age_seconds: float = 900.0,
    max_news_age_seconds: float = 600.0,
) -> str:
    """Drive execution eligibility from real data health — never fake NORMAL."""
    ages = snapshot_ages or {}
    market_count = len(market_snapshot or {})
    price_count = len(prices or {})

    if price_fetch_failed and market_count == 0 and price_count == 0:
        return ContextMode.EXECUTION_BLOCKED.value

    if news_from_stale_fallback:
        return ContextMode.STALE_CONTEXT.value

    market_age = float(ages.get("market") or 99999.0)
    if market_count == 0 and price_count == 0:
        return ContextMode.EXECUTION_BLOCKED.value
    if market_age > max_market_age_seconds * 2:
        return ContextMode.EXECUTION_BLOCKED.value
    if market_age > max_market_age_seconds:
        return ContextMode.STALE_CONTEXT.value

    failed = 0
    if source_health:
        for e in source_health.entries:
            if e.status in (SourceStatus.FAILED.value, SourceStatus.MISSING.value):
                failed += 1
    if failed >= 2 or price_fetch_failed:
        return ContextMode.DEGRADED_RESEARCH.value

    news_age = float(ages.get("news") or 0.0)
    if news_age > max_news_age_seconds and news_age < 99999.0:
        return ContextMode.DEGRADED_RESEARCH.value

    return ContextMode.NORMAL.value


def execution_allowed(context_mode: str) -> bool:
    return str(context_mode or "") == ContextMode.NORMAL.value


def research_allowed(context_mode: str) -> bool:
    return str(context_mode or "") in (
        ContextMode.NORMAL.value,
        ContextMode.DEGRADED_RESEARCH.value,
        ContextMode.STALE_CONTEXT.value,
    )


def build_source_health(
    *,
    news_count: int = 0,
    sec_count: int = 0,
    market_count: int = 0,
    kalshi_count: int = 0,
    price_fetch_failed: bool = False,
    news_failed: bool = False,
    kalshi_failed: bool = False,
) -> SourceHealthSnapshot:
    now = datetime.now(timezone.utc).isoformat()
    entries = [
        SourceHealthEntry(
            name="news",
            status=(
                SourceStatus.FAILED.value if news_failed
                else SourceStatus.RETURNING_EVIDENCE.value if news_count > 0
                else SourceStatus.MISSING.value
            ),
            last_success_at=now if news_count > 0 else None,
            items=news_count,
            detail=f"{news_count} news events",
        ),
        SourceHealthEntry(
            name="sec",
            status=SourceStatus.RETURNING_EVIDENCE.value if sec_count > 0 else SourceStatus.MISSING.value,
            last_success_at=now if sec_count > 0 else None,
            items=sec_count,
        ),
        SourceHealthEntry(
            name="market",
            status=(
                SourceStatus.FAILED.value if price_fetch_failed and market_count == 0
                else SourceStatus.HEALTHY.value if market_count > 0
                else SourceStatus.MISSING.value
            ),
            last_success_at=now if market_count > 0 else None,
            items=market_count,
            detail="price_fetch_failed" if price_fetch_failed else "",
        ),
        SourceHealthEntry(
            name="kalshi",
            status=(
                SourceStatus.FAILED.value if kalshi_failed
                else SourceStatus.RETURNING_EVIDENCE.value if kalshi_count > 0
                else SourceStatus.MISSING.value
            ),
            last_success_at=now if kalshi_count > 0 else None,
            items=kalshi_count,
        ),
    ]
    return SourceHealthSnapshot(entries=entries)
