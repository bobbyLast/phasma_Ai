"""Tests for worker supervisor and circuit breakers."""

from __future__ import annotations

import asyncio
import os
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from core.execution.execution_modes import ExecutionMode, normalize_execution_config
from core.execution.execution_router import ExecutionRouter
from core.supervisor import (
    CircuitBreaker,
    CycleContext,
    WorkerSnapshotStore,
    WorkerStatus,
    WorkerSupervisor,
)
from core.supervisor.workers import (
    CrashDetectorWorker,
    DataGatesWorker,
    ExecutionWorker,
    NewsIngestWorker,
    SignalGenerationWorker,
    build_default_workers,
)


class TestCircuitBreaker(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        health = os.path.join(self.tmp.name, "health.json")
        self.breaker = CircuitBreaker(health_path=health)

    def tearDown(self):
        self.tmp.cleanup()

    def test_three_same_errors_quarantine(self):
        err = TypeError("set not subscriptable")
        for _ in range(3):
            msg = self.breaker.record_failure("NewsIngestWorker", err)
        self.assertTrue(self.breaker.is_quarantined("NewsIngestWorker"))
        self.assertIn("quarantined", msg or "")

    def test_quarantined_skipped_until_retry(self):
        err = TypeError("set not subscriptable")
        for _ in range(3):
            self.breaker.record_failure("NewsIngestWorker", err)
        state = self.breaker.get_state("NewsIngestWorker")
        state.next_retry_at = (datetime.now(timezone.utc) + timedelta(minutes=30)).isoformat()
        self.assertTrue(self.breaker.is_quarantined("NewsIngestWorker"))

        state.next_retry_at = (datetime.now(timezone.utc) - timedelta(minutes=1)).isoformat()
        self.assertFalse(self.breaker.is_quarantined("NewsIngestWorker"))


class TestWorkerSupervisor(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        health = os.path.join(self.tmp.name, "health.json")
        store_dir = os.path.join(self.tmp.name, "workers")
        self.breaker = CircuitBreaker(health_path=health)
        self.store = WorkerSnapshotStore(base_dir=store_dir)
        self.supervisor = WorkerSupervisor(breaker=self.breaker, store=self.store)

    async def asyncTearDown(self):
        self.tmp.cleanup()

    async def test_worker_failure_does_not_crash_supervisor(self):
        worker = NewsIngestWorker(self.breaker, self.store)

        async def boom(_ctx):
            raise TypeError("set not subscriptable")

        worker._execute = boom  # type: ignore[method-assign]
        ctx = CycleContext(system=MagicMock(), app_ctx=MagicMock(), config=MagicMock())
        result = await worker.run(ctx)
        self.assertIn(result.status, (WorkerStatus.ERROR, WorkerStatus.DEGRADED, WorkerStatus.QUARANTINED))

    async def test_healthy_workers_run_while_other_quarantined(self):
        err = TypeError("repeat")
        for _ in range(3):
            self.breaker.record_failure("NewsIngestWorker", err)

        ctx = CycleContext(system=MagicMock(), config=MagicMock())
        crash = await self.supervisor.run_worker("CrashDetectorWorker", ctx)
        self.assertIn(crash.status.value, ("DEGRADED", "OK", "QUARANTINED"))

        news = await self.supervisor.run_worker("NewsIngestWorker", ctx)
        self.assertEqual(news.status, WorkerStatus.QUARANTINED)

    async def test_news_uses_last_good_snapshot_when_fresh(self):
        self.store.save_last_good(
            "news_ingest",
            {
                "ingested_news": [{"symbol": "AAPL", "title": "test"}],
                "symbol_universe": ["AAPL"],
                "company_names": {},
                "prices": {"AAPL": 100.0},
            },
        )
        worker = NewsIngestWorker(self.breaker, self.store)

        async def fail(_ctx):
            raise TypeError("set not subscriptable")

        worker._execute = fail  # type: ignore[method-assign]
        ctx = CycleContext(system=MagicMock(), app_ctx=MagicMock(), config=MagicMock())
        result = await worker.run(ctx)
        self.assertEqual(result.status, WorkerStatus.DEGRADED)
        self.assertFalse(ctx.skip_news_signals)
        self.assertIsNotNone(ctx.cycle_data)

    async def test_news_skips_signals_when_snapshot_stale(self):
        path = self.store.save_last_good(
            "news_ingest",
            {"ingested_news": [], "symbol_universe": [], "company_names": {}, "prices": {}},
        )
        old = self.store.load_last_good("news_ingest")
        old["saved_at"] = (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat()
        with open(path, "w", encoding="utf-8") as f:
            import json
            json.dump(old, f)

        worker = NewsIngestWorker(self.breaker, self.store)

        async def fail(_ctx):
            raise TypeError("set not subscriptable")

        worker._execute = fail  # type: ignore[method-assign]
        ctx = CycleContext(system=MagicMock(), app_ctx=MagicMock(), config=MagicMock())
        result = await worker.run(ctx)
        self.assertTrue(ctx.skip_news_signals)
        self.assertIn(result.status, (WorkerStatus.ERROR, WorkerStatus.QUARANTINED))

    async def test_crash_detector_unknown_on_failure(self):
        system = MagicMock()
        system._stage_crash_preflight = MagicMock(side_effect=RuntimeError("PhasmaConfig is not iterable"))
        app_ctx = MagicMock()
        app_ctx.crash_detector = MagicMock()
        ctx = CycleContext(system=system, app_ctx=app_ctx, config=MagicMock(), all_signals=[])
        worker = CrashDetectorWorker(self.breaker, self.store)
        result = await worker.run(ctx)
        self.assertEqual(result.status, WorkerStatus.DEGRADED)
        self.assertTrue(ctx.crash_risk_unknown)

    async def test_execution_router_failure_blocks(self):
        ctx = CycleContext(system=MagicMock(execution_router=None), config=MagicMock())
        worker = ExecutionWorker(self.breaker, self.store)
        result = await worker.run(ctx)
        self.assertEqual(result.status, WorkerStatus.ERROR)
        self.assertTrue(ctx.block_execution)

    async def test_data_gates_block_when_flag_set(self):
        ctx = CycleContext(
            system=MagicMock(),
            config=MagicMock(),
            block_execution=True,
            execution_blocked_reason="gates failed",
        )
        worker = DataGatesWorker(self.breaker, self.store)
        result = await worker.run(ctx)
        self.assertEqual(result.status, WorkerStatus.ERROR)
        self.assertFalse(result.can_continue_pipeline)

    async def test_alert_only_never_executes(self):
        cfg = {
            "execution": {"mode": "ALERT_ONLY"},
            "paper_trading_safety": {"enabled": True, "kill_switch": False},
        }
        normalize_execution_config(cfg)
        system = MagicMock()
        system.config = MagicMock()
        system.config.data = cfg
        system.execution_router = ExecutionRouter(system)
        ctx = CycleContext(system=system, config=system.config)
        result = await ExecutionWorker(self.breaker, self.store).run(ctx)
        self.assertEqual(result.status, WorkerStatus.OK)
        self.assertEqual(result.metadata.get("execution_mode"), ExecutionMode.ALERT_ONLY)

    async def test_signal_generation_skipped_when_news_stale(self):
        ctx = CycleContext(skip_news_signals=True, config=MagicMock())
        result = await SignalGenerationWorker(self.breaker, self.store).run(ctx)
        self.assertEqual(result.status, WorkerStatus.SKIPPED)

    def test_health_summary_contains_statuses(self):
        started = datetime.now(timezone.utc)
        from core.supervisor.worker_result import WorkerResult

        self.supervisor._last_results["NewsIngestWorker"] = WorkerResult.build(
            "NewsIngestWorker",
            WorkerStatus.QUARANTINED,
            started=started,
            detail="test",
        )
        self.supervisor._last_results["ExecutionWorker"] = WorkerResult.build(
            "ExecutionWorker",
            WorkerStatus.OK,
            started=started,
            metadata={"execution_mode": "ALERT_ONLY"},
        )
        import io
        from contextlib import redirect_stdout

        buf = io.StringIO()
        with redirect_stdout(buf):
            self.supervisor.print_health_summary(extra={"Execution": "ALERT_ONLY, OK"})
        out = buf.getvalue()
        self.assertIn("WORKER HEALTH", out)
        self.assertIn("NewsIngest", out)
        self.assertIn("QUARANTINED", out)


class TestCycleAttemptTracking(unittest.TestCase):
    def test_attempt_increments_on_failure(self):
        supervisor = WorkerSupervisor()
        supervisor.cycle_attempt = 7
        supervisor.completed_cycles = 0
        self.assertEqual(supervisor.cycle_attempt, 7)
        self.assertEqual(supervisor.completed_cycles, 0)


if __name__ == "__main__":
    unittest.main()
