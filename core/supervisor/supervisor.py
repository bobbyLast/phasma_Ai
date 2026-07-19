"""Ghost-style worker supervisor — isolate failures, quarantine repeat offenders."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from core.supervisor.circuit_breaker import CircuitBreaker
from core.supervisor.cycle_context import CycleContext
from core.supervisor.snapshot_store import WorkerSnapshotStore
from core.supervisor.worker_result import WorkerResult, WorkerStatus
from core.supervisor.workers import build_default_workers

logger = logging.getLogger(__name__)


class CriticalWorkerError(RuntimeError):
    """Raised when a critical worker failure should stop the cycle."""


class WorkerSupervisor:
    """Run workers independently with circuit breaking and health tracking."""

    def __init__(
        self,
        *,
        breaker: Optional[CircuitBreaker] = None,
        store: Optional[WorkerSnapshotStore] = None,
        workers: Optional[Dict[str, Any]] = None,
    ):
        self.breaker = breaker or CircuitBreaker()
        self.store = store or WorkerSnapshotStore()
        self.workers = workers or build_default_workers(self.breaker, self.store)
        self.cycle_attempt = 0
        self.completed_cycles = 0
        self._last_results: Dict[str, WorkerResult] = {}

    async def run_worker(self, name: str, ctx: CycleContext) -> WorkerResult:
        worker = self.workers.get(name)
        if not worker:
            started = datetime.now(timezone.utc)
            result = WorkerResult.build(
                name,
                WorkerStatus.SKIPPED,
                started=started,
                detail="worker not registered",
            )
        else:
            result = await worker.run(ctx)
        ctx.worker_results[name] = result
        self._last_results[name] = result
        logger.info(
            "worker=%s status=%s duration=%.2fs detail=%s can_continue=%s",
            name,
            result.status.value,
            result.duration_seconds,
            result.detail or result.error_message or "",
            result.can_continue_pipeline,
        )
        if not result.can_continue_pipeline and getattr(worker, "critical", False):
            raise CriticalWorkerError(
                f"{name} blocked pipeline: {result.detail or result.error_message}"
            )
        return result

    async def run_preflight_workers(self, ctx: CycleContext) -> None:
        await self.run_worker("MarketDataWorker", ctx)
        await self.run_worker("CrashDetectorWorker", ctx)

    async def run_ingest_workers(self, ctx: CycleContext) -> None:
        await self.run_worker("NewsIngestWorker", ctx)

    async def run_post_cycle_workers(self, ctx: CycleContext) -> None:
        await self.run_worker("OutcomeGraderWorker", ctx)

    async def validate_execution_gate(self, ctx: CycleContext) -> WorkerResult:
        gates = await self.run_worker("DataGatesWorker", ctx)
        execution = await self.run_worker("ExecutionWorker", ctx)
        if gates.status == WorkerStatus.ERROR or execution.status == WorkerStatus.ERROR:
            ctx.block_execution = True
        return execution

    def print_health_summary(self, *, extra: Optional[Dict[str, str]] = None) -> None:
        lines = ["", "WORKER HEALTH"]
        display_order = [
            "NewsIngestWorker",
            "MarketDataWorker",
            "CrashDetectorWorker",
            "SignalGenerationWorker",
            "UndergroundWorker",
            "KalshiIntelWorker",
            "SocialWorker",
            "GeopoliticalWorker",
            "JuryWorker",
            "ExecutionWorker",
            "OutcomeGraderWorker",
            "TelegramWorker",
            "DataGatesWorker",
        ]
        for name in display_order:
            result = self._last_results.get(name)
            state = self.breaker.get_state(name)
            if result:
                status = result.status.value
                detail_parts = []
                if state.fail_count:
                    detail_parts.append(f"fail_count={state.fail_count}")
                if state.last_success_at and status == "OK":
                    detail_parts.append(f"last_success={state.last_success_at}")
                if result.error_message and status != "OK":
                    detail_parts.append(f"last_error={result.error_message[:80]}")
                if result.detail:
                    detail_parts.append(f"reason={result.detail}")
                if state.next_retry_at and status == "QUARANTINED":
                    detail_parts.append(f"next_retry={state.next_retry_at}")
                suffix = ", ".join(detail_parts) if detail_parts else ""
                lines.append(f"{name.replace('Worker', '')}: {status}" + (f", {suffix}" if suffix else ""))
            elif state.status != "OK":
                lines.append(f"{name.replace('Worker', '')}: {state.status}, fail_count={state.fail_count}")

        if extra:
            for key, val in extra.items():
                lines.append(f"{key}: {val}")

        quarantined = self.breaker.quarantined_workers()
        if quarantined:
            lines.append(f"Quarantined workers: {', '.join(quarantined.keys())}")

        summary = "\n".join(lines)
        print(summary)
        logger.info(summary)

    def quarantined_worker_names(self) -> List[str]:
        return list(self.breaker.quarantined_workers().keys())
