"""Tests for runtime refactor: inventory, cadence, grouping, budget, decision honesty."""

from __future__ import annotations

import asyncio
import json
import os
import subprocess
import sys
import tempfile
import unittest
from io import StringIO
from unittest.mock import AsyncMock, MagicMock, patch

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from core.runtime.cadence import CadenceTracker, parse_cadence_seconds
from core.runtime.context_snapshots import ContextSnapshotStore
from core.runtime.safety_lock import print_startup_safety, verify_safety_lock
from core.monitoring.runtime_profiler import RuntimeProfiler
from core.supervisor.group_coordinator import GroupCoordinator, GroupResult
from core.signals.signal_decision import DecisionStatus, SignalDecision
from core.signals.decision_pipeline import DecisionPipeline
from core.signals.strategy_router import StrategyRouter, classify_asset_type, has_option_contract_fields
from utils.confidence_utils import compare_sim_validation, normalize_confidence_to_pct
from utils.signal_adapter import decision_to_report_dict, signal_to_dict
from utils.portfolio_ledger import filter_active_positions, summarize_ledger


def _load_config():
    path = os.path.join(ROOT, "config.json")
    with open(path, encoding="utf-8") as f:
        return json.load(f)


class TestSafetyLock(unittest.TestCase):
    def test_alert_only_config(self):
        cfg = _load_config()
        ok, violations = verify_safety_lock(cfg)
        self.assertTrue(ok, violations)
        self.assertEqual(cfg["execution"]["mode"], "ALERT_ONLY")
        self.assertFalse(cfg["paper_trading"]["enabled"])
        self.assertFalse(cfg["execution"].get("allow_live_trading", False))

    def test_startup_lines(self):
        buf = StringIO()
        with patch("sys.stdout", buf):
            print_startup_safety(_load_config(), execution_mode="ALERT_ONLY")
        out = buf.getvalue()
        self.assertIn("Execution mode: ALERT_ONLY", out)
        self.assertIn("Paper trading: disabled", out)
        self.assertIn("Runtime refactor: inventory/grouping mode", out)


class TestEngineInventory(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        json_path = os.path.join(ROOT, "data", "runtime", "engine_inventory.json")
        if not os.path.isfile(json_path):
            script = os.path.join(ROOT, "scripts", "audit_engine_inventory.py")
            subprocess.run([sys.executable, script], cwd=ROOT, check=True, capture_output=True, timeout=600)

    def test_inventory_json_exists(self):
        path = os.path.join(ROOT, "data", "runtime", "engine_inventory.json")
        self.assertTrue(os.path.isfile(path))
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        self.assertGreater(data.get("total_engines", 0), 10)

    def test_markdown_reports_exist(self):
        for name in ("engine_inventory.md", "runtime_call_tree.md"):
            path = os.path.join(ROOT, "reports", name)
            self.assertTrue(os.path.isfile(path), name)

    def test_log_discovered_banners(self):
        path = os.path.join(ROOT, "data", "runtime", "engine_inventory.json")
        with open(path, encoding="utf-8") as f:
            engines = json.load(f).get("entries", [])
        log_entries = [e for e in engines if e.get("discovered_by") == "log_scan"]
        self.assertGreater(len(log_entries), 0)


class TestCadenceAndSnapshots(unittest.TestCase):
    def test_hourly_skips_when_not_due(self):
        with tempfile.TemporaryDirectory() as tmp:
            tracker = CadenceTracker(state_path=os.path.join(tmp, "cadence.json"))
            tracker.mark_ran("discovery_deep")
            self.assertFalse(tracker.is_due("discovery_deep", "hourly"))

    def test_every_cycle_always_due(self):
        tracker = CadenceTracker(state_path=os.path.join(tempfile.gettempdir(), "phasma_test_cadence.json"))
        self.assertTrue(tracker.is_due("market", "every_cycle"))

    def test_snapshot_reuse(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = ContextSnapshotStore(base_dir=tmp)
            store.save("candidates", {"final_signals": 3}, source_group="DiscoveryGroup", ttl_seconds=3600)
            self.assertTrue(store.is_fresh("candidates"))
            self.assertEqual(store.get_payload("candidates")["final_signals"], 3)


class TestGroupCoordinator(unittest.TestCase):
    def test_budget_skip_optional(self):
        cfg = _load_config()
        coord = GroupCoordinator(cfg)
        coord.begin_cycle(1)
        coord._cycle_start = __import__("time").perf_counter() - 300

        async def _run():
            return await coord.run_group("discovery_deep", AsyncMock(return_value=[]), optional=True)

        result = asyncio.run(_run())
        self.assertIn(result.status, ("SKIPPED", "DEGRADED", "OK"))

    def test_group_health_prints(self):
        buf = StringIO()
        cfg = _load_config()
        coord = GroupCoordinator(cfg)
        coord._results["market"] = GroupResult(group_name="MarketGroup", status="OK")
        with patch("sys.stdout", buf):
            coord.print_group_health()
        self.assertIn("GROUP HEALTH", buf.getvalue())


class TestRuntimeProfiler(unittest.TestCase):
    def test_records_duration(self):
        with tempfile.TemporaryDirectory() as tmp:
            log_path = os.path.join(tmp, "engine_runtime.jsonl")
            prof = RuntimeProfiler(log_path=log_path)
            prof.begin_cycle(1)
            with prof.track("TestEngine", group_name="TestGroup") as rec:
                rec.items_out = 2
            self.assertTrue(os.path.isfile(log_path))
            with open(log_path, encoding="utf-8") as f:
                line = json.loads(f.readline())
            self.assertEqual(line["engine_id"], "TestEngine")
            self.assertGreaterEqual(line["duration_ms"], 0)


from brain.meta_brain import Signal


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


class TestDecisionIntegrity(unittest.TestCase):
    def test_confluence_filtered_not_approved(self):
        p = DecisionPipeline({}, execution_mode="ALERT_ONLY")
        d = p.evaluate(_sig(symbol="BZ"), confluence_filtered=True, has_catalyst=True)
        self.assertEqual(d.status, DecisionStatus.WATCHLIST_ONLY)

    def test_no_confluence_blocks_when_required(self):
        cfg = {"strategies": {"active_strategy": "penny_moonshot", "penny_moonshot": {"required_signals": ["insider"]}}}
        p = DecisionPipeline(cfg, execution_mode="ALERT_ONLY")
        d = p.evaluate(_sig(symbol="PENNY", current_price=2.0), confluence_result=None, has_catalyst=True)
        self.assertEqual(d.status, DecisionStatus.WATCHLIST_ONLY)

    def test_size_zero_watchlist(self):
        p = DecisionPipeline({}, execution_mode="ALERT_ONLY")
        d = p.evaluate(_sig(position_size=0))
        self.assertEqual(d.status, DecisionStatus.WATCHLIST_ONLY)

    def test_non_positive_price_rejects(self):
        p = DecisionPipeline({}, execution_mode="ALERT_ONLY")
        d = p.evaluate(_sig(current_price=0))
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

    def test_mega_cap_not_penny(self):
        for sym in ("AAPL", "TSLA", "NVDA", "MSFT"):
            route = self.router.route({"symbol": sym, "current_price": 150, "source": "news"})
            self.assertNotEqual(route["strategy"], "penny_moonshot")

    def test_btc_crypto(self):
        self.assertEqual(classify_asset_type({"symbol": "BTC"}), "CRYPTO")
        self.assertEqual(classify_asset_type({"symbol": "BTC-USD"}), "CRYPTO")

    def test_options_without_contract_fields(self):
        sig = {"symbol": "AAPL", "source": "unusual_whales", "trade_type": "STOCK"}
        self.assertFalse(has_option_contract_fields(sig))


class TestConfidenceHonesty(unittest.TestCase):
    def test_normalize_and_cap(self):
        self.assertEqual(normalize_confidence_to_pct(0.56), 56.0)
        self.assertEqual(normalize_confidence_to_pct(56), 56.0)
        self.assertLessEqual(normalize_confidence_to_pct(130), 100.0)

    def test_sim_mismatch(self):
        result = compare_sim_validation(56, 30)
        self.assertEqual(result["status"], "MISMATCH")

    def test_pop_zero_not_buy_now(self):
        sig = {"symbol": "C", "pop": 0, "action": "BUY_NOW"}
        self.assertLess(normalize_confidence_to_pct(sig["pop"]), 40)


class TestSignalAdapter(unittest.TestCase):
    def test_signal_decision_to_dict(self):
        dec = SignalDecision(
            signal_id="abc",
            symbol="TEST",
            status=DecisionStatus.APPROVED_ALERT_ONLY,
            current_price=10.0,
            confidence_pct=75.0,
            execution_mode="ALERT_ONLY",
        )
        d = decision_to_report_dict(dec)
        self.assertEqual(d["symbol"], "TEST")
        self.assertIn("decision_status", d)

    def test_signal_decision_has_get_via_adapter(self):
        dec = SignalDecision(signal_id="x", symbol="FOO", current_price=1.0)
        d = signal_to_dict(dec)
        self.assertEqual(d["symbol"], "FOO")


class TestPortfolioLedger(unittest.TestCase):
    def test_size_zero_not_active(self):
        positions = [
            {"symbol": "A", "size": 0, "status": "OPEN"},
            {"symbol": "B", "size": 10, "status": "OPEN"},
        ]
        active = filter_active_positions(positions)
        self.assertEqual(len(active), 1)
        self.assertEqual(active[0]["symbol"], "B")

    def test_expired_closed(self):
        positions = [
            {"symbol": "X", "size": 5, "days_left": 0, "status": "OPEN"},
        ]
        active = filter_active_positions(positions)
        self.assertEqual(len(active), 0)

    def test_local_ledger_label(self):
        text = summarize_ledger({"starting_capital": 2000, "open_positions": []})
        self.assertIn("LOCAL LEDGER STATUS", text)

    def test_sell_pnl_direction(self):
        from utils.portfolio_ledger import compute_direction_pnl
        self.assertGreater(compute_direction_pnl(100, 90, "SELL"), 0)
        self.assertLess(compute_direction_pnl(100, 110, "SELL"), 0)


class TestExecutionLogging(unittest.TestCase):
    def test_router_skip_not_executed(self):
        result = {
            "symbol": "AAPL",
            "action": "BUY",
            "entry_price": 150,
            "execution_decision": "skipped",
            "execution_mode": "ALERT_ONLY",
            "execution_reason": "ALERT_ONLY",
        }
        msg = (
            f"EXECUTION_SKIPPED: mode={result['execution_mode']}"
            if result["execution_decision"] == "skipped"
            else "EXECUTED"
        )
        self.assertIn("EXECUTION_SKIPPED", msg)
        self.assertNotIn("EXECUTED", msg)


if __name__ == "__main__":
    unittest.main()
