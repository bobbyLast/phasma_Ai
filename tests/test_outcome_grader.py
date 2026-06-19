"""Tests for OutcomeGrader — tracking and calibration without execution."""

from __future__ import annotations

import os
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from core.execution.outcome_grader import OutcomeGrader, _direction_correct, _signed_return_pct
from core.execution.signal_outcome_tracker import SignalOutcomeTracker


def _sample_signal(**overrides):
    sig = {
        "symbol": "AAPL",
        "action": "BUY",
        "confidence": 72,
        "current_price": 100.0,
        "entry_price": 100.0,
        "source": "test_source",
        "strategy": "momentum",
    }
    sig.update(overrides)
    return sig


class TestOutcomeGrader(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        storage = os.path.join(self.tmp.name, "signals.json")
        self.tracker = SignalOutcomeTracker(storage_file=storage)
        self.fetcher = MagicMock()
        self.grader = OutcomeGrader(tracker=self.tracker, price_fetcher=self.fetcher)

    def tearDown(self):
        self.tmp.cleanup()

    def test_signal_recorded_on_alert(self):
        record_id = self.grader.record_signal(
            _sample_signal(),
            execution_mode="ALERT_ONLY",
            execution_decision="skipped",
            alerted_only=True,
            paper_traded=False,
        )
        self.assertTrue(record_id)
        records = self.tracker.get_all_records()
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["ticker"], "AAPL")
        self.assertTrue(records[0]["alerted_only"])
        self.assertFalse(records[0]["paper_traded"])
        self.assertIn("signal_snapshot", records[0])

    def test_grading_computes_direction_correct(self):
        entry = 100.0
        up = 101.0
        down = 99.0
        self.assertTrue(_direction_correct(_signed_return_pct(entry, up, "BUY")))
        self.assertFalse(_direction_correct(_signed_return_pct(entry, down, "BUY")))
        self.assertTrue(_direction_correct(_signed_return_pct(entry, down, "SELL")))

    def test_grade_pending_uses_price_fetcher_not_router(self):
        self.grader.record_signal(
            _sample_signal(),
            execution_mode="ALERT_ONLY",
            execution_decision="skipped",
            alerted_only=True,
        )
        record = self.tracker.get_all_records()[0]
        old_ts = datetime.now(timezone.utc) - timedelta(hours=2)
        record["timestamp"] = old_ts.isoformat()
        self.tracker._save()

        self.fetcher.get_real_price.return_value = 102.0
        with patch.object(self.grader, "_fetch_bars", return_value=[]):
            stats = self.grader.grade_pending()

        self.fetcher.get_real_price.assert_called()
        self.assertGreater(stats["graded_horizons"], 0)
        graded = self.tracker.get_all_records()[0]["grading"]["horizons"]["1h"]
        self.assertIsNotNone(graded)
        self.assertTrue(graded["direction_correct"])
        self.assertEqual(graded["outcome"], "win")
        import core.execution.outcome_grader as og_module
        self.assertFalse(hasattr(og_module, "ExecutionRouter"))

    def test_calibration_buckets_aggregate(self):
        for conf, final_price in ((40, 98.0), (72, 101.0), (88, 103.0)):
            rid = self.grader.record_signal(
                _sample_signal(confidence=conf),
                execution_mode="ALERT_ONLY",
                execution_decision="skipped",
                alerted_only=True,
            )
            record = self.tracker.get_record(rid)
            record["grading"]["horizons"]["1h"] = {
                "return_pct": (final_price - 100.0),
                "direction_correct": final_price > 100.0,
                "outcome": "win" if final_price > 100.5 else "loss",
            }
        self.tracker._save()

        report = self.grader.get_calibration_report()
        buckets = report["by_confidence_bucket"]
        self.assertIn("0-50", buckets)
        self.assertIn("65-75", buckets)
        self.assertIn("85-100", buckets)
        self.assertEqual(buckets["65-75"]["count"], 1)
        self.assertGreaterEqual(report["total_graded"], 3)

    def test_alert_only_vs_paper_traded_separation(self):
        self.grader.record_signal(
            _sample_signal(symbol="MSFT"),
            execution_mode="ALERT_ONLY",
            execution_decision="skipped",
            alerted_only=True,
        )
        self.grader.record_signal(
            _sample_signal(symbol="NVDA"),
            execution_mode="PAPER_INTERNAL",
            execution_decision="filled",
            paper_traded=True,
        )
        for record in self.tracker.get_all_records():
            record["grading"]["horizons"]["1h"] = {
                "return_pct": 1.0,
                "direction_correct": True,
                "outcome": "win",
            }
        self.tracker._save()

        report = self.grader.get_calibration_report()
        self.assertEqual(report["alert_only"]["count"], 1)
        self.assertEqual(report["paper_traded"]["count"], 1)


if __name__ == "__main__":
    unittest.main()
