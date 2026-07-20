"""Tests for display/reporting guards, zero bankroll, demo geo firewall, runtime budget."""

from __future__ import annotations

import os
import sys
import time
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from core.runtime.budget_enforcer import RuntimeBudgetEnforcer
from core.signals.decision_pipeline import DecisionPipeline
from core.signals.signal_decision import DecisionStatus
from core.source_status import block_demo_geo_from_decision, is_demo_geo_event
from utils import display_safe
from utils.units_sizing import apply_units_sizing


class TestDisplaySafe(unittest.TestCase):
    def test_entry_action_missing_returns_na(self):
        self.assertEqual(display_safe.entry_action({}), "N/A")

    def test_win_rate_label_zero_guard(self):
        self.assertEqual(display_safe.win_rate_label(0), "N/A (sim win rate 0%)")
        self.assertIn("1 in", display_safe.win_rate_label(50))

    def test_position_size_missing_returns_na(self):
        self.assertEqual(display_safe.position_size_label({}), "N/A")

    def test_rationale_missing_returns_unknown(self):
        self.assertEqual(display_safe.rationale_text({}), "unknown")


class TestZeroBankrollSizing(unittest.TestCase):
    def test_bankroll_zero_disables_sizing(self):
        system = SimpleNamespace(
            unit_size_percent=1.0,
            standard_units=2,
            min_units=1,
            max_units=10,
        )
        signals = [
            {"symbol": "AAPL", "position_size": 100, "confidence": 0.8, "paper_eligible": True},
        ]
        cfg = {"bankroll": 0}
        result = apply_units_sizing(system, signals, cfg, status={"bankroll": 0})
        self.assertEqual(result["sizing_status"], "DISABLED_ZERO_BANKROLL")
        self.assertEqual(signals[0]["position_size"], 0)
        self.assertFalse(signals[0]["paper_eligible"])
        self.assertEqual(signals[0]["sizing_status"], "DISABLED_ZERO_BANKROLL")


class TestDemoGeoFirewall(unittest.TestCase):
    def test_demo_geo_blocked_from_decision(self):
        event = {"title": "Demo conflict", "source": "geopolitical_demo", "is_demo": True}
        cfg = {"demo_data": {"allow_in_live_pipeline": False}}
        self.assertTrue(is_demo_geo_event(event))
        self.assertTrue(block_demo_geo_from_decision(event, cfg))

    def test_demo_geo_cannot_create_signal_via_pipeline(self):
        pipeline = DecisionPipeline({"demo_data": {"allow_in_live_pipeline": False}})
        signal = {
            "symbol": "XOM",
            "action": "BUY",
            "confidence": 0.9,
            "geopolitical_event": {"source": "geopolitical_demo", "is_demo": True},
        }
        decision = pipeline.evaluate(signal)
        self.assertEqual(decision.status, DecisionStatus.WATCHLIST_ONLY)
        self.assertIn("demo_firewall", decision.gates_failed)
        self.assertFalse(decision.is_final_approved())


class TestRuntimeBudgetEnforcer(unittest.TestCase):
    def test_budget_exceeded_skips_optional_groups(self):
        enforcer = RuntimeBudgetEnforcer({"runtime_budget": {"max_cycle_seconds": 0.01}})
        enforcer.begin_cycle()
        time.sleep(0.02)
        self.assertTrue(enforcer.should_skip_optional("discovery_deep"))
        self.assertTrue(enforcer.should_skip_optional("monte_carlo_deep"))
        self.assertIn("discovery_deep", enforcer.skipped_groups)

    def test_monte_carlo_cap(self):
        enforcer = RuntimeBudgetEnforcer(
            {"runtime_budget": {"max_cycle_seconds": 999, "max_candidates_monte_carlo": 2}}
        )
        enforcer.begin_cycle()
        self.assertTrue(enforcer.allow_monte_carlo())
        self.assertTrue(enforcer.allow_monte_carlo())
        self.assertFalse(enforcer.allow_monte_carlo())


if __name__ == "__main__":
    unittest.main()
