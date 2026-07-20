"""Tests for PaperReadinessGuard — fail-closed checks before PAPER_ALPACA."""

from __future__ import annotations

import os
import sys
import tempfile
import unittest
from unittest.mock import MagicMock, patch

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from core.execution.execution_modes import ExecutionMode, normalize_execution_config
from core.execution.execution_router import ExecutionRouter
from core.execution.outcome_grader import OutcomeGrader
from core.execution.paper_readiness_guard import (
    PAPER_ALPACA_URL,
    PaperReadinessGuard,
    normalize_paper_trading_safety,
)
from core.execution.signal_outcome_tracker import SignalOutcomeTracker
from utils.trade_memory import TradeMemory


def _base_signal(**overrides):
    sig = {
        "symbol": "AAPL",
        "action": "BUY",
        "confidence": 75,
        "current_price": 150.0,
        "entry_price": 150.0,
        "trade_type": "STOCK",
        "position_size": 1,
        "source": "test",
    }
    sig.update(overrides)
    return sig


def _safe_paper_config(**overrides):
    cfg = {
        "execution": {
            "mode": "PAPER_ALPACA",
            "allow_live_trading": False,
            "kalshi_execution_enabled": False,
            "require_price": True,
            "require_fresh_data": True,
            "max_data_age_seconds": 900,
        },
        "paper_trading_safety": {
            "enabled": True,
            "max_orders_per_cycle": 3,
            "max_orders_per_day": 10,
            "max_notional_per_order": 1000,
            "max_total_daily_notional": 5000,
            "cooldown_minutes_per_symbol": 120,
            "stock_only": True,
            "block_low_confidence_below": 65,
            "require_outcome_tracking": True,
            "require_fresh_price": True,
            "kill_switch": False,
        },
        "paper_trading": {"min_confidence_threshold": 50},
    }
    cfg.update(overrides)
    normalize_execution_config(cfg)
    normalize_paper_trading_safety(cfg)
    return cfg


def _mock_alpaca_client():
    client = MagicMock()
    client.api_key = "test-key"
    client.api_secret = "test-secret"
    client.base_url = PAPER_ALPACA_URL
    return client


def _guard_with_temp_storage(tmp_dir: str) -> PaperReadinessGuard:
    mem = TradeMemory(memory_file=os.path.join(tmp_dir, "trade_memory.json"), cooldown_days=7)
    tracker = SignalOutcomeTracker(storage_file=os.path.join(tmp_dir, "signals.json"))
    grader = OutcomeGrader(tracker=tracker)
    return PaperReadinessGuard(trade_memory=mem, outcome_tracker=tracker, outcome_grader=grader)


def _mock_system(config: dict):
    system = MagicMock()
    system.config = MagicMock()
    system.config.data = config
    system.alpaca_paper_trader = None
    system.paper_portfolio = None
    system.daily_learning_tracker = None
    system.alert_learning_loop = None
    return system


class TestPaperReadinessGuard(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.guard = _guard_with_temp_storage(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    @patch.dict(os.environ, {}, clear=True)
    def test_blocked_missing_alpaca_credentials(self):
        cfg = _safe_paper_config()
        result = self.guard.check_all(cfg, simulate_paper_mode=True)
        self.assertFalse(result.passed)
        self.assertIn("alpaca_credentials_missing", result.failed_checks)

    @patch.dict(
        os.environ,
        {
            "ALPACA_API_KEY": "k",
            "ALPACA_API_SECRET": "s",
            "ALPACA_BASE_URL": "https://api.alpaca.markets",
        },
        clear=True,
    )
    def test_blocked_non_paper_alpaca_url(self):
        cfg = _safe_paper_config()
        result = self.guard.check_all(cfg, simulate_paper_mode=True)
        self.assertFalse(result.passed)
        self.assertIn("alpaca_url_not_paper_endpoint", result.failed_checks)

    @patch.dict(
        os.environ,
        {"ALPACA_API_KEY": "k", "ALPACA_API_SECRET": "s", "ALPACA_BASE_URL": PAPER_ALPACA_URL},
        clear=True,
    )
    def test_allow_live_trading_does_not_block_paper_readiness(self):
        cfg = _safe_paper_config()
        cfg["execution"]["allow_live_trading"] = True
        normalize_execution_config(cfg)
        result = self.guard.check_all(cfg, alpaca_client=_mock_alpaca_client(), simulate_paper_mode=True)
        self.assertTrue(result.passed, result.failed_checks)
        self.assertNotIn("allow_live_trading_enabled", result.failed_checks)

    @patch.dict(
        os.environ,
        {"ALPACA_API_KEY": "k", "ALPACA_API_SECRET": "s", "ALPACA_BASE_URL": PAPER_ALPACA_URL},
        clear=True,
    )
    def test_blocked_kill_switch(self):
        cfg = _safe_paper_config()
        cfg["paper_trading_safety"]["kill_switch"] = True
        normalize_paper_trading_safety(cfg)
        result = self.guard.check_all(cfg, simulate_paper_mode=True)
        self.assertFalse(result.passed)
        self.assertIn("paper_trading_safety.kill_switch_active", result.failed_checks)

    @patch.dict(
        os.environ,
        {"ALPACA_API_KEY": "k", "ALPACA_API_SECRET": "s", "ALPACA_BASE_URL": PAPER_ALPACA_URL},
        clear=True,
    )
    def test_kalshi_execution_enabled_does_not_block_paper_readiness(self):
        cfg = _safe_paper_config()
        cfg["execution"]["kalshi_execution_enabled"] = True
        normalize_execution_config(cfg)
        result = self.guard.check_all(cfg, alpaca_client=_mock_alpaca_client(), simulate_paper_mode=True)
        self.assertTrue(result.passed, result.failed_checks)
        self.assertNotIn("kalshi_execution_enabled", result.failed_checks)

    @patch.dict(
        os.environ,
        {"ALPACA_API_KEY": "k", "ALPACA_API_SECRET": "s", "ALPACA_BASE_URL": PAPER_ALPACA_URL},
        clear=True,
    )
    def test_blocked_missing_order_day_caps(self):
        cfg = _safe_paper_config()
        cfg["paper_trading_safety"]["max_orders_per_day"] = 0
        normalize_paper_trading_safety(cfg)
        result = self.guard.check_all(cfg, simulate_paper_mode=True)
        self.assertFalse(result.passed)
        self.assertIn("max_orders_per_day_missing", result.failed_checks)

    @patch.dict(
        os.environ,
        {"ALPACA_API_KEY": "k", "ALPACA_API_SECRET": "s", "ALPACA_BASE_URL": PAPER_ALPACA_URL},
        clear=True,
    )
    def test_passes_when_all_requirements_met(self):
        cfg = _safe_paper_config()
        result = self.guard.check_all(cfg, alpaca_client=_mock_alpaca_client(), simulate_paper_mode=True)
        self.assertTrue(result.passed, result.failed_checks)

    @patch.dict(
        os.environ,
        {"ALPACA_API_KEY": "k", "ALPACA_API_SECRET": "s", "ALPACA_BASE_URL": PAPER_ALPACA_URL},
        clear=True,
    )
    def test_execution_router_refuses_when_guard_fails(self):
        cfg = _safe_paper_config()
        cfg["paper_trading_safety"]["kill_switch"] = True
        normalize_paper_trading_safety(cfg)
        system = _mock_system(cfg)
        trader = MagicMock()
        trader.alpaca = MagicMock()
        trader.api_key = "k"
        trader.api_secret = "s"
        trader.base_url = PAPER_ALPACA_URL
        system.alpaca_paper_trader = trader
        system._alpaca_submit_from_signal = MagicMock(
            return_value={"success": True, "order_id": "x", "price": 150.0, "quantity": 1}
        )
        router = ExecutionRouter(system)
        router.trade_memory = self.guard.trade_memory
        router.outcome_tracker = self.guard.outcome_tracker
        router.outcome_grader = self.guard.outcome_grader
        router.paper_guard = self.guard
        result = router.submit_signal(_base_signal(), skip_gates=True)
        self.assertEqual(result.decision, "rejected")
        system._alpaca_submit_from_signal.assert_not_called()

    @patch.dict(
        os.environ,
        {"ALPACA_API_KEY": "k", "ALPACA_API_SECRET": "s", "ALPACA_BASE_URL": PAPER_ALPACA_URL},
        clear=True,
    )
    def test_rejection_reason_visible_in_result(self):
        cfg = _safe_paper_config()
        cfg["paper_trading_safety"]["kill_switch"] = True
        normalize_paper_trading_safety(cfg)
        system = _mock_system(cfg)
        router = ExecutionRouter(system)
        router.paper_guard = self.guard
        router.trade_memory = self.guard.trade_memory
        router.outcome_tracker = self.guard.outcome_tracker
        router.outcome_grader = self.guard.outcome_grader
        result = router.submit_signal(_base_signal(), skip_gates=True)
        self.assertEqual(result.decision, "rejected")
        self.assertIn("paper_trading_safety.kill_switch_active", result.reason)
        self.assertIn("readiness guard failed", result.alert_label.lower())
        self.assertIn("paper_trading_safety.kill_switch_active", result.metadata.get("readiness_guard_failures", []))

    def test_alert_only_does_not_require_readiness_guard(self):
        cfg = {"execution": {"mode": "ALERT_ONLY"}, "paper_trading_safety": {"enabled": True, "kill_switch": True}}
        normalize_execution_config(cfg)
        normalize_paper_trading_safety(cfg)
        system = _mock_system(cfg)
        system._alpaca_submit_from_signal = MagicMock()
        router = ExecutionRouter(system)
        result = router.submit_signal(_base_signal())
        self.assertEqual(result.mode, ExecutionMode.ALERT_ONLY)
        self.assertEqual(result.decision, "skipped")
        system._alpaca_submit_from_signal.assert_not_called()


if __name__ == "__main__":
    unittest.main()
