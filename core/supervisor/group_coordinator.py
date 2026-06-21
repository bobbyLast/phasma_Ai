"""Engine group coordinator — cadence, snapshots, budget."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Awaitable, Callable, Dict, List, Optional

from core.monitoring.runtime_profiler import RuntimeProfiler, get_runtime_profiler
from core.runtime.cadence import CadenceTracker
from core.runtime.context_snapshots import ContextSnapshotStore

GroupRunner = Callable[[], Awaitable[Any]]


@dataclass
class GroupResult:
    group_name: str
    status: str = "OK"
    started_at: str = ""
    finished_at: str = ""
    duration_ms: float = 0.0
    children_ran: List[str] = field(default_factory=list)
    children_skipped: List[str] = field(default_factory=list)
    outputs_path: str = ""
    stale_ok: bool = False
    next_run_at: Optional[str] = None
    error: str = ""
    warnings: List[str] = field(default_factory=list)
    reused_snapshot: bool = False


GROUP_FAMILY_MAP = {
    "ingest": "IngestGroup",
    "market": "MarketGroup",
    "risk_fast": "RiskGroup",
    "risk_deep": "RiskGroup",
    "discovery_fast": "DiscoveryGroup",
    "discovery_deep": "DiscoveryGroup",
    "partnership": "DiscoveryGroup",
    "underground": "DiscoveryGroup",
    "politician": "DiscoveryGroup",
    "insider": "DiscoveryGroup",
    "decision": "DecisionGroup",
    "execution": "ExecutionGroup",
    "reporting": "ReportingGroup",
    "learning": "LearningGroup",
}


class GroupCoordinator:
    """Run engine groups on cadence with snapshot reuse and budget enforcement."""

    SNAPSHOT_KEY = {
        "ingest": "ingest",
        "market": "market",
        "risk_fast": "risk",
        "risk_deep": "risk",
        "discovery_fast": "candidates",
        "discovery_deep": "candidates",
        "decision": "decisions",
        "execution": "execution",
        "reporting": "reports",
        "learning": "learning",
    }

    def __init__(
        self,
        config: Dict[str, Any],
        *,
        cadence: Optional[CadenceTracker] = None,
        snapshots: Optional[ContextSnapshotStore] = None,
        profiler: Optional[RuntimeProfiler] = None,
    ):
        self.config = config
        self.groups_cfg = config.get("engine_groups") or {}
        self.budget_cfg = config.get("runtime_budget") or {}
        self.cadence = cadence or CadenceTracker()
        self.snapshots = snapshots or ContextSnapshotStore()
        self.profiler = profiler or get_runtime_profiler()
        self._results: Dict[str, GroupResult] = {}
        self._cycle_attempt = 1
        self._cycle_start: Optional[float] = None
        self._network_calls = 0

    def begin_cycle(self, cycle_attempt: int) -> None:
        self._cycle_attempt = cycle_attempt
        self._cycle_start = time.perf_counter()
        self._results = {}
        self._network_calls = 0
        self.profiler.begin_cycle(cycle_attempt)

    def _over_budget(self) -> bool:
        max_sec = float(self.budget_cfg.get("max_cycle_seconds", 240) or 240)
        if not self._cycle_start:
            return False
        return (time.perf_counter() - self._cycle_start) >= max_sec

    def _group_cfg(self, key: str) -> Dict[str, Any]:
        return dict(self.groups_cfg.get(key) or {})

    async def run_group(
        self,
        key: str,
        runner: GroupRunner,
        *,
        snapshot_payload: Any = None,
        optional: bool = False,
        items_in: int = 0,
    ) -> GroupResult:
        family = GROUP_FAMILY_MAP.get(key, key)
        gcfg = self._group_cfg(key)
        cadence = gcfg.get("cadence", "every_cycle")
        max_sec = float(gcfg.get("max_seconds", 60) or 60)
        snap_key = self.SNAPSHOT_KEY.get(key)

        started = datetime.now(timezone.utc)
        result = GroupResult(group_name=family, started_at=started.isoformat())

        if optional and self._over_budget() and self.budget_cfg.get("skip_low_value_engines_when_over_budget", True):
            result.status = "SKIPPED"
            result.warnings.append("runtime budget exceeded")
            if snap_key and self.snapshots.is_fresh(snap_key):
                result.reused_snapshot = True
                result.stale_ok = True
                result.status = "DEGRADED"
            self._results[key] = result
            return result

        if not self.cadence.is_due(key, cadence, cycle_attempt=self._cycle_attempt):
            result.status = "SKIPPED"
            result.next_run_at = self.cadence.next_run_at(key, cadence)
            result.warnings.append(f"not due (cadence={cadence})")
            if snap_key:
                cached = self.snapshots.load(snap_key)
                if cached:
                    result.reused_snapshot = True
                    result.stale_ok = self.snapshots.is_fresh(snap_key)
                    result.outputs_path = self.snapshots._path(snap_key)
                    result.status = "DEGRADED" if not result.stale_ok else "OK"
            self._results[key] = result
            return result

        t0 = time.perf_counter()
        items_out = 0
        try:
            with self.profiler.track(key, group_name=family, items_in=items_in) as rec:
                rec.metadata["cadence"] = cadence
                payload = await runner()
                items_out = len(payload) if hasattr(payload, "__len__") else (1 if payload else 0)
                rec.items_out = items_out
            if snap_key is not None and payload is not None:
                ttl = parse_ttl_seconds(cadence)
                result.outputs_path = self.snapshots.save(
                    snap_key, payload, source_group=family, ttl_seconds=ttl,
                    item_count=items_out,
                )
            elif snapshot_payload is not None and snap_key:
                result.outputs_path = self.snapshots.save(
                    snap_key, snapshot_payload, source_group=family, ttl_seconds=900,
                )
            self.cadence.mark_ran(key)
            result.status = "OK"
            result.children_ran.append(key)
        except Exception as exc:
            result.status = "ERROR"
            result.error = str(exc)[:300]
            if snap_key and self.snapshots.is_fresh(snap_key):
                result.reused_snapshot = True
                result.stale_ok = True
                result.status = "DEGRADED"
        finally:
            elapsed = (time.perf_counter() - t0) * 1000
            result.duration_ms = round(elapsed, 2)
            result.finished_at = datetime.now(timezone.utc).isoformat()
            if elapsed > max_sec * 1000:
                result.warnings.append(f"exceeded max_seconds={max_sec}")
        self._results[key] = result
        return result

    def get_cached(self, key: str) -> Any:
        snap_key = self.SNAPSHOT_KEY.get(key, key)
        return self.snapshots.get_payload(snap_key)

    def print_group_health(self) -> None:
        print("\nGROUP HEALTH")
        order = [
            "ingest", "market", "risk_fast", "discovery_fast", "discovery_deep",
            "decision", "execution", "reporting", "learning",
        ]
        for key in order:
            r = self._results.get(key)
            if not r:
                continue
            parts = [f"{r.group_name}: {r.status}"]
            if r.reused_snapshot:
                parts.append("reused snapshot")
            if r.duration_ms:
                parts.append(f"{r.duration_ms:.0f}ms")
            if r.warnings:
                parts.append(r.warnings[0])
            print("  " + ", ".join(parts))
        self.profiler.print_cycle_summary()


def parse_ttl_seconds(cadence: str) -> int:
    from core.runtime.cadence import parse_cadence_seconds
    sec = parse_cadence_seconds(cadence)
    return sec if sec > 0 else 900
