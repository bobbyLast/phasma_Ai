#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ApplicationContext — shared cycle state and subsystem handles.

Option C (incremental): pipeline stages gradually read dependencies from
`ApplicationContext` instead of reaching through `PhasmaTradingSystem` for
everything. Preflight stages were migrated first; extend `bind()` as more
stages move over.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class ApplicationContext:
    """Per-cycle context: config, caches, and handles used by staged pipeline."""

    system: Any
    config: Any
    market_cache: Any
    global_macro_monitor: Any
    fred_filter: Any
    crash_detector: Any
    partnership_engine: Any
    ai_watchlist: Any
    ai_symbol_categories: Any
    cycle_stage_timings: Dict[str, float]
    fred_regime: str = "NEUTRAL"
    fred_adjustments: Dict[str, Any] = field(default_factory=dict)
    cycle_data: Optional[Any] = None
    symbol_coalition: Optional[Any] = None
    run_deep_discovery: bool = True

    @classmethod
    def bind(cls, system: Any, cycle_stage_timings: Optional[Dict[str, float]] = None) -> ApplicationContext:
        """Build context from a live PhasmaTradingSystem instance."""
        timings: Dict[str, float] = cycle_stage_timings if cycle_stage_timings is not None else {}
        return cls(
            system=system,
            config=system.config,
            market_cache=getattr(system, "market_cache", None),
            global_macro_monitor=getattr(system, "global_macro_monitor", None),
            fred_filter=getattr(system, "fred_filter", None),
            crash_detector=getattr(system, "crash_detector", None),
            partnership_engine=getattr(system, "partnership_engine", None),
            ai_watchlist=system.ai_watchlist,
            ai_symbol_categories=system.ai_symbol_categories,
            cycle_stage_timings=timings,
            fred_regime="NEUTRAL",
            fred_adjustments={},
        )

    def track_symbol(self, symbol: str, source: str = "news") -> None:
        self.system._track_symbol(symbol, source)

    def categorize_symbol(self, symbol: str) -> str:
        return self.system._categorize_symbol(symbol)

    def sync_fred_to_system(self) -> None:
        """Keep legacy attributes on the trading system for code not yet on ctx."""
        setattr(self.system, "_fred_regime", self.fred_regime)
        setattr(self.system, "_fred_adjustments", dict(self.fred_adjustments))
