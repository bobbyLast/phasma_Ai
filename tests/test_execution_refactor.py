"""Tests for Phasma execution refactor — 15 required safety cases."""

from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

# Project root on path
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from core.execution.execution_modes import ExecutionMode, normalize_execution_config, is_placeholder_api_key
from core.execution.execution_router import ExecutionRouter, normalize_monte_carlo_fields
from core.execution.data_gates import DataQualityGates, audit_api_keys, validate_execution_gates
from core.execution.position_reconcile import reconcile_positions_on_startup
from utils.trade_memory import TradeMemory


def _base_signal(**overrides):
    sig = {
        "symbol": "AAPL",
        "action": "BUY",
        "confidence": 0.75,
        "current_price": 150.0,
        "entry_price": 150.0,
        "trade_type": "STOCK",
        "position_size": 1,
        "source": "test",
    }
    sig.update(overrides)
    return sig


def _mock_system(config: dict):
    system = MagicMock()
    system.config = MagicMock()
    system.config.data = config
    system.alpaca_paper_trader = None
    system.paper_portfolio = None
    system.daily_learning_tracker = None
    system.alert_learning_loop = None
    return system


class TestExecutionModes(unittest.TestCase):
    def test_off_mode_never_submits(self):
        cfg = {"execution": {"mode": "OFF"}}
        normalize_execution_config(cfg)
        system = _mock_system(cfg)
        router = ExecutionRouter(system)
        result = router.submit_signal(_base_signal())
        self.assertEqual(result.mode, "OFF")
        self.assertEqual(result.decision, "skipped")

    def test_alert_only_never_submits(self):
        cfg = {"execution": {"mode": "ALERT_ONLY"}}
        normalize_execution_config(cfg)
        system = _mock_system(cfg)
        router = ExecutionRouter(system)
        result = router.submit_signal(_base_signal())
        self.assertEqual(result.mode, "ALERT_ONLY")
        self.assertEqual(result.decision, "skipped")
        self.assertIn("ALERT", result.alert_label.upper())

    def test_paper_alpaca_submits_once(self):
        cfg = {"execution": {"mode": "PAPER_ALPACA"}, "paper_trading": {"min_confidence_threshold": 50}}
        normalize_execution_config(cfg)
        system = _mock_system(cfg)
        trader = MagicMock()
        trader.alpaca = MagicMock()
        system.alpaca_paper_trader = trader
        system._alpaca_submit_from_signal = MagicMock(
            return_value={"success": True, "order_id": "oid1", "price": 150.0, "quantity": 1, "symbol": "AAPL"}
        )
        router = ExecutionRouter(system)
        r1 = router.submit_signal(_base_signal(), skip_gates=True)
        r2 = router.submit_signal(_base_signal(), skip_gates=True)
        self.assertEqual(r1.decision, "filled")
        self.assertEqual(system._alpaca_submit_from_signal.call_count, 1)
        self.assertEqual(r2.decision, "skipped")
        self.assertIn("duplicate", r2.reason)

    def test_telegram_does_not_execute_trades(self):
        """Router path: telegram formatting must not call broker submit."""
        cfg = {"execution": {"mode": "ALERT_ONLY"}}
        normalize_execution_config(cfg)
        system = _mock_system(cfg)
        router = ExecutionRouter(system)
        system._alpaca_submit_from_signal = MagicMock()
        result = router.submit_signal(_base_signal())
        system._alpaca_submit_from_signal.assert_not_called()
        self.assertEqual(result.decision, "skipped")

    def test_execute_classified_no_duplicate_path(self):
        """execute_classified_trade uses router only — no direct portfolio.execute_buy."""
        cfg = {"execution": {"mode": "ALERT_ONLY"}, "bankroll": 1000, "risk_per_trade": 0.01}
        normalize_execution_config(cfg)
        system = _mock_system(cfg)
        system.paper_portfolio = MagicMock()
        system.paper_portfolio.execute_buy = MagicMock()
        system.execution_router = ExecutionRouter(system)
        system.skipped_opportunity_watchlist = MagicMock()
        system.classify_trade = MagicMock(return_value={"stop_pct": 0.05, "trade_class": "SWING_30D"})
        system.log_final_trade_decision = MagicMock(return_value="log.json")
        system.trade_db = None

        from main import PhasmaTradingSystem

        class SignalStub:
            symbol = "AAPL"
            action = "BUY"
            confidence = 0.8
            current_price = 100.0
            source = "test"

        with patch.object(PhasmaTradingSystem, "__init__", lambda self, *a, **k: None):
            pts = PhasmaTradingSystem.__new__(PhasmaTradingSystem)
            cfg_obj = MagicMock()
            cfg_obj.data = cfg
            cfg_obj.get = lambda key, default=None: cfg.get(key, default) if isinstance(key, str) and "." not in key else default
            pts.config = cfg_obj
            pts.ai_watchlist = set()
            pts.ai_symbol_categories = {}
            pts.execution_router = system.execution_router
            pts.skipped_opportunity_watchlist = system.skipped_opportunity_watchlist
            pts.classify_trade = system.classify_trade
            pts.log_final_trade_decision = system.log_final_trade_decision
            pts.trade_db = None
            pts.paper_portfolio = system.paper_portfolio
            pts.config = MagicMock()
            pts.config.get = lambda k, d=None: cfg.get(k, d)
            pts.config.data = cfg

        import asyncio
        from core.application_context import ApplicationContext

        pts.ai_watchlist = set()
        pts.ai_analyzed_history = {}
        pts.ai_symbol_categories = {}
        pts.ai_symbol_last_seen = {}
        ctx = ApplicationContext.bind(pts, {"config": cfg})
        ctx.system = pts
        ctx.config = cfg
        out = asyncio.run(pts.execute_classified_trade(SignalStub(), ctx=ctx))
        system.paper_portfolio.execute_buy.assert_not_called()
        self.assertIsNotNone(out)
        self.assertEqual(out.get("execution_mode"), "ALERT_ONLY")

    def test_missing_price_blocks_execution(self):
        cfg = {"execution": {"mode": "PAPER_ALPACA", "require_price": True}}
        normalize_execution_config(cfg)
        gates = DataQualityGates(cfg)
        gate = gates.validate(_base_signal(current_price=None, entry_price=None))
        self.assertFalse(gate.passed)
        self.assertEqual(gate.reason, "missing_price")

    def test_stale_price_blocks_execution(self):
        old = (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat()
        cfg = {"execution": {"mode": "PAPER_ALPACA", "require_fresh_data": True, "max_data_age_seconds": 900}}
        normalize_execution_config(cfg)
        gates = DataQualityGates(cfg)
        gate = gates.validate(_base_signal(price_timestamp=old))
        self.assertFalse(gate.passed)
        self.assertEqual(gate.reason, "stale_price")

    def test_placeholder_api_key_disabled(self):
        cfg = {"apis": {"financial_modeling_prep": {"api_key": "YOUR_FMP_KEY"}}}
        disabled = audit_api_keys(cfg)
        self.assertIn("financial_modeling_prep", disabled)
        self.assertTrue(is_placeholder_api_key("your_newsapi_key_here"))

    def test_kalshi_intel_only_blocks_execution(self):
        cfg = {
            "execution": {"mode": "PAPER_ALPACA", "kalshi_execution_enabled": False},
            "kalshi_intel_only": True,
            "post_prediction_trades": False,
        }
        gates = DataQualityGates(cfg)
        gate = gates.validate(_base_signal(symbol="KXTEST", source="kalshi_prediction"))
        self.assertFalse(gate.passed)
        self.assertEqual(gate.reason, "kalshi_intel_only")

    def test_filled_paper_calls_trade_memory(self):
        with tempfile.TemporaryDirectory() as tmp:
            mem_file = os.path.join(tmp, "trade_memory.json")
            tm = TradeMemory(memory_file=mem_file, cooldown_days=7)
            cfg = {"execution": {"mode": "PAPER_INTERNAL"}, "paper_trading": {"min_confidence_threshold": 50, "max_position_size": 1000}}
            normalize_execution_config(cfg)
            system = _mock_system(cfg)
            portfolio = MagicMock()
            portfolio.state = {"available_capital": 10000}
            system.paper_portfolio = portfolio
            system._internal_paper_submit_from_signal = MagicMock(
                return_value={"success": True, "price": 10.0, "quantity": 1, "symbol": "AAPL"}
            )
            router = ExecutionRouter(system)
            router.trade_memory = tm
            result = router.submit_signal(_base_signal(symbol="AAPL", confidence=80), skip_gates=True)
            self.assertEqual(result.decision, "filled")
            self.assertTrue(tm.is_recently_traded("AAPL"))

    def test_restart_does_not_wipe_positions(self):
        system = MagicMock()
        system.config = MagicMock()
        system.config.get = lambda k, d=None: ({"execution": {"mode": "ALERT_ONLY"}}.get("execution") if k == "execution" else d)
        system.config.data = {"execution": {"mode": "ALERT_ONLY"}}
        rm = MagicMock()
        rm.open_positions = {"AAPL": {"quantity": 1}}
        system.meta_brain = MagicMock()
        system.meta_brain.risk_manager = rm
        summary = reconcile_positions_on_startup(system)
        self.assertEqual(len(rm.open_positions), 1)
        self.assertGreaterEqual(summary["positions_count"], 1)

    def test_duplicate_signal_no_double_buy(self):
        cfg = {"execution": {"mode": "PAPER_ALPACA"}}
        normalize_execution_config(cfg)
        system = _mock_system(cfg)
        trader = MagicMock()
        trader.alpaca = MagicMock()
        system.alpaca_paper_trader = trader
        system._alpaca_submit_from_signal = MagicMock(
            return_value={"success": True, "order_id": "x", "price": 1, "quantity": 1}
        )
        router = ExecutionRouter(system)
        router.trade_memory = TradeMemory(cooldown_days=7)
        sig = _base_signal(dedup_key="dup:1")
        router.submit_signal(sig, skip_gates=True)
        router.submit_signal(sig, skip_gates=True)
        self.assertEqual(system._alpaca_submit_from_signal.call_count, 1)

    def test_internal_paper_honest_fill(self):
        cfg = {"execution": {"mode": "PAPER_INTERNAL"}}
        normalize_execution_config(cfg)
        system = _mock_system(cfg)
        system.paper_portfolio = MagicMock()
        system._internal_paper_submit_from_signal = MagicMock(
            return_value={"success": True, "price": 5.0, "quantity": 2, "total_cost": 10.0}
        )
        router = ExecutionRouter(system)
        result = router.submit_signal(_base_signal(), skip_gates=True)
        self.assertEqual(result.decision, "filled")
        self.assertIn("internal", result.alert_label.lower())

    def test_monte_carlo_labeled_simulation_only(self):
        sig = {"confidence": 0.8, "pop_from_sim": 72}
        out = normalize_monte_carlo_fields(sig)
        self.assertTrue(out.get("assumption_based_simulation"))
        self.assertIn("monte_carlo_sim_score", out)
        self.assertEqual(out.get("simulation_pop"), 72)

    def test_no_random_in_day_trading_scanner(self):
        import inspect
        from engines import day_trading_scanner as dts
        source = inspect.getsource(dts.DayTradingScanner.scan_momentum_stocks)
        self.assertNotIn("random.randint", source)
        self.assertNotIn("random.uniform", source)


if __name__ == "__main__":
    unittest.main()
