"""Shared cycle context passed between workers."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class CycleContext:
    """Mutable pipeline state for one supervised cycle attempt."""

    cycle_attempt: int = 0
    completed_cycles: int = 0
    system: Any = None
    app_ctx: Any = None
    config: Any = None

    cycle_data: Any = None
    news_items: Optional[List[Dict]] = None
    skip_news_signals: bool = False
    news_snapshot_stale: bool = False

    crash_assessment: Optional[Dict] = None
    market_safe: bool = True
    index_crash: Optional[Dict] = None
    crypto_assessments: List[Dict] = field(default_factory=list)
    crash_risk_unknown: bool = False

    all_signals: List[Any] = field(default_factory=list)
    approved_signals: List[Any] = field(default_factory=list)

    block_execution: bool = False
    execution_blocked_reason: str = ""

    worker_results: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
