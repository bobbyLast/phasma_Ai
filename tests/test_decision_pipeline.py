"""Tests for decision pipeline, strategy router, worker supervisor, portfolio ledger."""

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

from brain.meta_brain import Signal
from core.signals.decision_pipeline import DecisionPipeline
from core.signals.signal_decision import DecisionStatus
from core.signals.strategy_router import StrategyRouter, classify_asset_type, has_option_contract_fields
from core.source_status import block_demo_signal, is_demo_source
from core.supervisor import CircuitBreaker, CycleContext, WorkerSupervisor, WorkerStatus
from core.supervisor.workers import NewsIngestWorker, build_default_workers
from engines.kalshi_engine import KalshiPredictionEngine
from engines.news_engine_integrated import IntegratedNewsSources
from utils.confidence_utils import compare_sim_validation, normalize_confidence_to_pct
from utils.config_helpers import config_get
from utils.portfolio_ledger import compute_direction_pnl, filter_active_positions, normalize_position


def _sig(**kwargs):
    base = {
        "symbol": "TEST",
        "action": "BUY",
        "confidence": 0.75,
        "position_size": 100,
        "current_price": 10.0,
        "rationale": "news catalyst",
        "source": "news_engine",
        "trade_type": "STOCK",
        "company_name": "Test Corp",
        "fact_check": {"is_valid": True, "company_info": {"name": "Test Corp", "avg_volume": 1000000}},
        "avg_volume": 1000000,
    }
    base.update(kwargs)
    return Signal(**base)


class TestWorkerSupervisor(unittest.IsolatedAsyncioTestCase):
    async def test_failure_does_not_crash_supervisor(self):
        breaker = CircuitBreaker()
        store_dir = tempfile.mkdtemp()
        from core.supervisor.snapshot_store import WorkerSnapshotStore
        store = WorkerSnapshotStore(base_dir=store_dir)
        sup = WorkerSupervisor(breaker=breaker, store=store)
        worker = NewsIngestWorker(breaker, store)
        worker._execute = AsyncMock(side_effect=TypeError("set not subscriptable"))
        sup.workers["NewsIngestWorker"] = worker
        ctx = CycleContext(cycle_attempt=1, system=MagicMock(), app_ctx=MagicMock())
        result = await sup.run_worker("NewsIngestWorker", ctx)
        self.assertIn(result.status.value, ("ERROR", "QUARANTINED", "DEGRADED"))

    async def test_three_failures_quarantine(self):
        breaker = CircuitBreaker()
        for _ in range(3):
            breaker.record_failure("W", TypeError("same"))
        self.assertTrue(breaker.is_quarantined("W"))

    async def test_healthy_workers_continue(self):
        from core.supervisor.snapshot_store import WorkerSnapshotStore
        workers = build_default_workers(CircuitBreaker(), WorkerSnapshotStore(base_dir=tempfile.mkdtemp()))
        names = list(workers.keys())
        self.assertIn("MarketDataWorker", names)
        self.assertIn("KalshiIntelWorker", names)


class TestRuntimeFixes(unittest.TestCase):
    def test_normalize_ticker_list_set(self):
        engine = object.__new__(IntegratedNewsSources)
        engine._news_symbol_limit = 5
        out = IntegratedNewsSources._normalize_ticker_list(engine, {"BZ", "AAPL", "BZ"})
        self.assertEqual(out, ["AAPL", "BZ"])

    def test_config_get_phasma_config(self):
        cfg = MagicMock()
        cfg.get = MagicMock(side_effect=lambda k, d=None: {"shadow_mode": True}.get(k, d))
        self.assertTrue(config_get(cfg, "shadow_mode", False))

    def test_silver_monitor_guard(self):
        s = MagicMock(spec=[])
        self.assertIsNone(getattr(s, "silver_monitor", None))


class TestDecisionIntegrity(unittest.TestCase):
    def setUp(self):
        self.cfg = {"strategies": {"active_strategy": "penny_moonshot", "penny_moonshot": {"required_signals": ["insider"]}}}

    def test_confluence_filtered_not_approved(self):
        p = DecisionPipeline(self.cfg, execution_mode="ALERT_ONLY")
        d = p.evaluate(_sig(symbol="BZ"), confluence_filtered=True, has_catalyst=True)
        self.assertEqual(d.status, DecisionStatus.WATCHLIST_ONLY)

    def test_no_confluence_blocks_penny_strategy(self):
        p = DecisionPipeline(self.cfg, execution_mode="ALERT_ONLY")
        d = p.evaluate(_sig(symbol="PENNY", current_price=2.0), confluence_result=None, confluence_filtered=False, has_catalyst=True)
        self.assertEqual(d.status, DecisionStatus.WATCHLIST_ONLY)

    def test_zero_size_watchlist(self):
        p = DecisionPipeline({}, execution_mode="ALERT_ONLY")
        d = p.evaluate(_sig(position_size=0))
        self.assertEqual(d.status, DecisionStatus.WATCHLIST_ONLY)

    def test_non_positive_price_rejected(self):
        p = DecisionPipeline({}, execution_mode="ALERT_ONLY")
        d = p.evaluate(_sig(current_price=0))
        self.assertEqual(d.status, DecisionStatus.REJECTED)

    def test_missing_catalyst_rejected(self):
        p = DecisionPipeline({}, execution_mode="ALERT_ONLY")
        s = _sig(rationale="", source="unknown")
        d = p.evaluate(s, has_catalyst=False)
        self.assertEqual(d.status, DecisionStatus.REJECTED)

    def test_jury_conditional_not_final(self):
        p = DecisionPipeline({}, execution_mode="ALERT_ONLY")
        d = p.evaluate(_sig(), jury_verdict="CONDITIONAL", market_intel_available=True, intelligence_strength=60, has_catalyst=True)
        self.assertEqual(d.status, DecisionStatus.CONDITIONAL)

    def test_alert_only_execution_skipped(self):
        p = DecisionPipeline({}, execution_mode="ALERT_ONLY")
        d = p.evaluate(_sig(), market_intel_available=True, intelligence_strength=60, has_catalyst=True)
        self.assertEqual(d.status, DecisionStatus.APPROVED_ALERT_ONLY)
        p.finalize_execution([d])
        self.assertEqual(d.status, DecisionStatus.EXECUTION_SKIPPED)


class TestStrategyRouter(unittest.TestCase):
    def setUp(self):
        self.router = StrategyRouter()

    def test_aapl_not_penny_moonshot(self):
        route = self.router.route(_sig(symbol="AAPL", current_price=150))
        self.assertNotEqual(route["strategy"], "penny_moonshot")

    def test_btc_crypto(self):
        self.assertEqual(classify_asset_type(_sig(symbol="BTC-USD")), "CRYPTO")

    def test_unusual_whales_without_contract_not_option(self):
        s = _sig(symbol="AAPL", source="unusual_whales", trade_type="OPTION")
        self.assertFalse(has_option_contract_fields(s))
        self.assertEqual(classify_asset_type(s), "STOCK")


class TestConfidenceAndPop(unittest.TestCase):
    def test_confidence_cap(self):
        self.assertEqual(normalize_confidence_to_pct(1300), 100.0)

    def test_confidence_decimal(self):
        self.assertEqual(normalize_confidence_to_pct(0.56), 56.0)
        self.assertEqual(normalize_confidence_to_pct(56), 56.0)

    def test_sim_mismatch(self):
        v = compare_sim_validation(56, 41)
        self.assertIn(v["status"], ("SOFT_MISMATCH", "MISMATCH"))

    def test_pop_zero_no_buy_now(self):
        p = DecisionPipeline({}, execution_mode="ALERT_ONLY")
        d = p.evaluate(_sig(pop_from_sim=0), market_intel_available=True, intelligence_strength=60, has_catalyst=True)
        setattr(d.raw_signal, "pop_from_sim", 0)
        d2 = p.evaluate(
            Signal(
                "X", "BUY_NOW", 0.8, 100, "catalyst", "news",
                pop_from_sim=0, current_price=10,
                company_name="X Corp",
                fact_check={"is_valid": True, "company_info": {"name": "X Corp", "avg_volume": 1e6}},
            ),
            market_intel_available=True,
            intelligence_strength=60,
            has_catalyst=True,
        )
        self.assertEqual(d2.status, DecisionStatus.WATCHLIST_ONLY)


class TestSourceHonesty(unittest.TestCase):
    def test_demo_blocked(self):
        self.assertTrue(block_demo_signal({"source": "demo"}, {"demo_data": {"allow_in_live_pipeline": False}}))

    def test_demo_source_detected(self):
        self.assertTrue(is_demo_source("geopolitical_demo"))


class TestPortfolio(unittest.TestCase):
    def test_zero_size_not_active(self):
        pos = normalize_position({"symbol": "X", "quantity": 0, "position_size": 0})
        self.assertFalse(pos.get("active_trade"))

    def test_expired_closed(self):
        pos = normalize_position({"symbol": "X", "quantity": 10, "days_left": 0})
        self.assertEqual(pos["status"], "EXPIRED")

    def test_sell_pnl_direction(self):
        self.assertGreater(compute_direction_pnl(100, 90, "SELL"), 0)
        self.assertGreater(compute_direction_pnl(100, 110, "BUY"), 0)


class TestKalshiDebug(unittest.TestCase):
    @patch("engines.kalshi_engine.NewsAPIIntegration", None)
    @patch("engines.kalshi_engine.WeatherValidationEngine", None)
    @patch("engines.kalshi_engine.WeatherConsistencyEngine", None)
    def test_debug_hidden(self, *_):
        from io import StringIO
        engine = KalshiPredictionEngine({"debug": {"kalshi_expiry_debug": False}})
        buf = StringIO()
        with patch("sys.stdout", buf):
            engine._calculate_days_to_expiry("2026-12-31")
        self.assertNotIn("SCANNING DEBUG", buf.getvalue())


if __name__ == "__main__":
    unittest.main()
