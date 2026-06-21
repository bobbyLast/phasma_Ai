"""Per-engine/group runtime profiling."""

from __future__ import annotations

import json
import os
import time
from contextlib import contextmanager
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Iterator, List, Optional

from core.runtime_paths import runtime_path


@dataclass
class ProfileRecord:
    cycle_attempt: int = 0
    group_name: str = ""
    engine_id: str = ""
    stage: str = ""
    started_at: str = ""
    finished_at: str = ""
    duration_ms: float = 0.0
    status: str = "OK"
    items_in: int = 0
    items_out: int = 0
    symbols_checked: int = 0
    signals_created: int = 0
    network_calls: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    skipped_reason: str = ""
    error: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


class RuntimeProfiler:
    """Append-only JSONL profiler with in-memory cycle summary."""

    def __init__(self, log_path: Optional[str] = None):
        perf_dir = runtime_path("performance")
        os.makedirs(perf_dir, exist_ok=True)
        self.log_path = log_path or os.path.join(perf_dir, "engine_runtime.jsonl")
        self._cycle_records: List[ProfileRecord] = []
        self._cycle_attempt = 0
        self._cycle_start: Optional[float] = None

    def begin_cycle(self, cycle_attempt: int) -> None:
        self._cycle_attempt = cycle_attempt
        self._cycle_records = []
        self._cycle_start = time.perf_counter()

    @contextmanager
    def track(
        self,
        engine_id: str,
        *,
        group_name: str = "",
        stage: str = "",
        items_in: int = 0,
    ) -> Iterator[ProfileRecord]:
        rec = ProfileRecord(
            cycle_attempt=self._cycle_attempt,
            group_name=group_name,
            engine_id=engine_id,
            stage=stage,
            items_in=items_in,
            started_at=datetime.now(timezone.utc).isoformat(),
        )
        t0 = time.perf_counter()
        try:
            yield rec
            rec.status = rec.status or "OK"
        except Exception as exc:
            rec.status = "ERROR"
            rec.error = str(exc)[:500]
            raise
        finally:
            rec.finished_at = datetime.now(timezone.utc).isoformat()
            rec.duration_ms = round((time.perf_counter() - t0) * 1000, 2)
            self._cycle_records.append(rec)
            self._append(rec)

    def _append(self, rec: ProfileRecord) -> None:
        with open(self.log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(asdict(rec), default=str) + "\n")

    def print_cycle_summary(self) -> None:
        if not self._cycle_records:
            print("\nRUNTIME PROFILE\n(no engine timings recorded)")
            return
        total_ms = 0.0
        if self._cycle_start:
            total_ms = round((time.perf_counter() - self._cycle_start) * 1000, 2)
        sorted_recs = sorted(self._cycle_records, key=lambda r: r.duration_ms, reverse=True)
        zero_out = [r for r in self._cycle_records if r.items_out == 0 and r.status == "OK" and not r.skipped_reason]
        skipped = [r for r in self._cycle_records if r.skipped_reason]
        demo = [r for r in self._cycle_records if r.metadata.get("demo")]

        print("\nRUNTIME PROFILE")
        print(f"Total cycle time: {total_ms:.0f} ms")
        print("Slowest engines:")
        for r in sorted_recs[:8]:
            print(f"  • {r.engine_id}: {r.duration_ms:.0f} ms ({r.status})")
        if zero_out:
            print("Engines that ran but produced 0 usable outputs:")
            for r in zero_out[:6]:
                print(f"  • {r.engine_id}")
        if demo:
            print("Engines using demo/TODO data:")
            for r in demo[:6]:
                print(f"  • {r.engine_id}: {r.metadata.get('demo', 'demo')}")
        if skipped:
            print("Engines skipped due cadence/budget:")
            for r in skipped[:8]:
                print(f"  • {r.engine_id}: {r.skipped_reason}")


_profiler: Optional[RuntimeProfiler] = None


def get_runtime_profiler() -> RuntimeProfiler:
    global _profiler
    if _profiler is None:
        _profiler = RuntimeProfiler()
    return _profiler
