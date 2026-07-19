"""Fast-cycle runtime budget enforcement."""

from __future__ import annotations

import time
from typing import Any, Dict, List, Optional, Set


OPTIONAL_GROUP_KEYS: Set[str] = {
    "discovery_deep",
    "partnership",
    "underground",
    "thematic",
    "monte_carlo_deep",
    "politician",
    "insider",
    "revisit_monte_carlo",
    "geopolitical_secondary",
}


class RuntimeBudgetEnforcer:
    """Track cycle elapsed time and skip optional work when over budget."""

    def __init__(self, config: Dict[str, Any]):
        budget = config.get("runtime_budget") or {}
        self.max_cycle_seconds = float(budget.get("max_cycle_seconds", 240) or 240)
        self.skip_optional = bool(budget.get("skip_low_value_engines_when_over_budget", True))
        self.max_monte_carlo = int(budget.get("max_candidates_monte_carlo", 5) or 5)
        self._start: Optional[float] = None
        self.degraded = False
        self.skipped_groups: List[str] = []
        self.monte_carlo_count = 0

    def begin_cycle(self) -> None:
        self._start = time.perf_counter()
        self.degraded = False
        self.skipped_groups = []
        self.monte_carlo_count = 0

    def elapsed(self) -> float:
        if self._start is None:
            return 0.0
        return time.perf_counter() - self._start

    def remaining(self) -> float:
        return max(0.0, self.max_cycle_seconds - self.elapsed())

    def is_over_budget(self) -> bool:
        return self.elapsed() > self.max_cycle_seconds

    def should_skip_optional(self, group_key: str) -> bool:
        if not self.skip_optional:
            return False
        if group_key not in OPTIONAL_GROUP_KEYS:
            return False
        if self.is_over_budget():
            if group_key not in self.skipped_groups:
                self.skipped_groups.append(group_key)
            self.degraded = True
            return True
        return False

    def allow_monte_carlo(self) -> bool:
        if self.should_skip_optional("monte_carlo_deep"):
            return False
        if self.monte_carlo_count >= self.max_monte_carlo:
            return False
        self.monte_carlo_count += 1
        return True

    def print_exceeded_if_needed(self) -> None:
        if not self.degraded and not self.is_over_budget():
            return
        self.degraded = True
        skipped = list(dict.fromkeys(self.skipped_groups))
        if not skipped:
            skipped = [
                "DiscoveryGroup deep",
                "Partnership",
                "Underground",
                "Thematic",
                "MonteCarlo deep",
                "Politician",
                "Insider",
            ]
        print("[RUNTIME BUDGET] exceeded fast-cycle budget")
        print("Skipped optional groups:")
        for item in skipped:
            label = item if item[0].isupper() else item.replace("_", " ").title()
            print(f"* {label}")
        print("Status: DEGRADED_BUDGET_EXCEEDED")
