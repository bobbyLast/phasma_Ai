"""Tests for quality/honesty fixes (confidence, resolver, health, sim validation)."""

from __future__ import annotations

import os
import sys
import unittest
from io import StringIO
from unittest.mock import MagicMock, patch

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from utils.confidence_utils import (
    compare_sim_validation,
    format_confidence_fields,
    format_sim_validation_message,
    normalize_confidence_to_pct,
)
from utils.company_resolver import CompanyResolver, RESOLVER_TRUSTED_STATUSES
from utils.web_search_resolver import is_sector_category_name, parse_search_hits
from core.system_health import aggregate_system_health, format_system_health_report
from utils.signal_data_quality import (
    SignalDataQuality,
    apply_fetched_price,
    apply_fetched_volume,
    assess_signal_data_quality,
    is_alert_only_eligible,
    is_display_eligible,
    is_paper_trade_eligible,
    resolve_pop_pct,
)
from core.execution.paper_readiness_guard import PaperReadinessGuard
from engines.kalshi_engine import KalshiPredictionEngine


class TestConfidenceUtils(unittest.TestCase):
    def test_never_displays_above_100(self):
        fields = format_confidence_fields(1300)
        self.assertLessEqual(fields["confidence_pct"], 100.0)
        self.assertEqual(fields["confidence_label"], "MAXED/CAPPED")

    def test_raw_score_can_exceed_100_but_pct_cannot(self):
        fields = format_confidence_fields(1300)
        self.assertGreater(fields["raw_score"], 100)
        self.assertEqual(fields["confidence_pct"], 100.0)

    def test_negative_floors_at_zero(self):
        self.assertEqual(normalize_confidence_to_pct(-5), 0.0)

    def test_normalize_decimal_and_percent(self):
        self.assertEqual(normalize_confidence_to_pct(0.56), 56.0)
        self.assertEqual(normalize_confidence_to_pct(56), 56.0)
        self.assertEqual(normalize_confidence_to_pct(1.0), 100.0)
        self.assertEqual(normalize_confidence_to_pct(100), 100.0)
        self.assertEqual(normalize_confidence_to_pct(1300), 100.0)

    def test_sim_match_56_vs_54(self):
        v = compare_sim_validation(56, 54)
        self.assertEqual(v["status"], "MATCH")

    def test_sim_mismatch_56_vs_41(self):
        v = compare_sim_validation(56, 41)
        self.assertIn(v["status"], ("SOFT_MISMATCH", "MISMATCH"))
        msg = format_sim_validation_message("HD", v)
        self.assertNotIn("matches simulation reality", msg.lower())
        self.assertIn("MISMATCH", msg.upper())

    def test_sim_match_wording(self):
        v = compare_sim_validation(0.56, 0.54)
        msg = format_sim_validation_message("AAPL", v)
        self.assertIn("MATCH", msg)


class TestResolverPrecedence(unittest.TestCase):
    def test_bz_sec_not_overwritten_by_web(self):
        resolver = CompanyResolver()
        info = {
            "name": "Kanzhun Ltd",
            "company_name": "Kanzhun Ltd",
            "symbol": "BZ",
            "resolver_status": "sec_exact",
            "validation_method": "sec_edgar",
        }
        enriched = resolver.enrich_company_info(info, "BZ", "some headline")
        self.assertEqual(enriched["name"], "Kanzhun Ltd")
        self.assertEqual(enriched.get("company_name", enriched["name"]), "Kanzhun Ltd")

    def test_web_cannot_overwrite_sec_in_enrich(self):
        resolver = CompanyResolver()
        with patch.object(resolver, "resolve", return_value={
            "company_name": "Communication Services",
            "sector": "Communication Services",
            "industry": "Communication Services",
            "resolver_status": "web_suggested",
        }):
            info = {"name": "Kanzhun Ltd", "resolver_status": "sec_exact"}
            enriched = resolver.enrich_company_info(info, "BZ")
            self.assertEqual(enriched["name"], "Kanzhun Ltd")

    def test_sector_names_rejected(self):
        self.assertTrue(is_sector_category_name("Communication Services"))
        self.assertTrue(is_sector_category_name("Technology"))
        self.assertFalse(is_sector_category_name("Kanzhun Ltd"))

    def test_parse_search_rejects_sector_only_name(self):
        hits = [{"title": "BZ stock", "snippet": "Communication Services sector overview"}]
        self.assertIsNone(parse_search_hits("BZ", hits))

    def test_trusted_statuses_frozen(self):
        self.assertIn("sec_exact", RESOLVER_TRUSTED_STATUSES)


class TestSystemHealth(unittest.TestCase):
    def test_missing_vendor_causes_degraded(self):
        system = MagicMock()
        system.execution_router = MagicMock(mode="ALERT_ONLY")
        system.config = MagicMock()
        system.config.get = lambda k, d=None: True if k == "kalshi_intel_only" else d
        ud = MagicMock()
        ud.get_feed_status.return_value = {
            "sec_edgar": "OK",
            "news_rss": "NOT_CONFIGURED",
            "options_flow": "DISABLED",
            "job_scraper": "DISABLED",
        }
        system.underground_discovery = ud
        system.outcome_grader = MagicMock()
        health = aggregate_system_health(system)
        self.assertEqual(health["overall"], "DEGRADED")

    def test_all_operational_only_when_ok(self):
        system = MagicMock()
        system.execution_router = MagicMock(mode="ALERT_ONLY")
        system.config = MagicMock()
        system.config.get = lambda k, d=None: d
        system.config.data = {"demo_data": {"allow_in_live_pipeline": True}}
        system.worker_supervisor = None
        ud = MagicMock()
        ud.get_feed_status.return_value = {
            "sec_edgar": "OK",
            "news_rss": "OK",
            "options_flow": "OK",
            "job_scraper": "OK",
        }
        system.underground_discovery = ud
        system.outcome_grader = MagicMock()
        health = aggregate_system_health(system)
        self.assertEqual(health["overall"], "OK")
        report = format_system_health_report(health)
        self.assertIn("SYSTEM STATUS: OK", report)

    def test_disabled_optional_does_not_crash(self):
        system = MagicMock()
        system.execution_router = MagicMock(mode="ALERT_ONLY")
        system.config = MagicMock()
        system.config.get = lambda k, d=None: d
        system.underground_discovery = None
        system.outcome_grader = None
        health = aggregate_system_health(system)
        self.assertIn(health["overall"], ("OK", "DEGRADED"))


class TestSignalDataQuality(unittest.TestCase):
    def test_missing_price_blocks(self):
        q = assess_signal_data_quality({"symbol": "AAPL", "fact_check": {"is_valid": True}})
        self.assertEqual(q, SignalDataQuality.MISSING_PRICE)

    def test_fetched_price_updates_signal(self):
        sig = {"symbol": "AAPL"}
        apply_fetched_price(sig, 150.0)
        self.assertEqual(sig["current_price"], 150.0)

    def test_missing_volume_partial(self):
        sig = {
            "symbol": "AAPL",
            "current_price": 100,
            "fact_check": {"is_valid": True, "company_info": {"name": "Apple Inc"}},
        }
        self.assertEqual(assess_signal_data_quality(sig), SignalDataQuality.PARTIAL_PRICE_ONLY)

    def test_partial_alert_only_not_paper_eligible(self):
        q = SignalDataQuality.PARTIAL_PRICE_ONLY
        self.assertTrue(is_alert_only_eligible(q))
        self.assertFalse(is_paper_trade_eligible(q))

    def test_complete_signal_display_eligible(self):
        sig = {
            "symbol": "AAPL",
            "company_name": "Apple Inc",
            "current_price": 100,
            "confidence": 0.65,
            "fact_check": {
                "is_valid": True,
                "company_info": {"name": "Apple Inc", "avg_volume": 50_000_000},
            },
            "avg_volume": 50_000_000,
        }
        self.assertEqual(assess_signal_data_quality(sig), SignalDataQuality.COMPLETE)
        self.assertTrue(is_display_eligible(sig))

    def test_display_blocked_without_volume(self):
        sig = {
            "symbol": "AAPL",
            "company_name": "Apple Inc",
            "current_price": 100,
            "confidence": 0.65,
            "fact_check": {"is_valid": True, "company_info": {"name": "Apple Inc"}},
        }
        self.assertFalse(is_display_eligible(sig))

    def test_apply_fetched_volume(self):
        sig = {"symbol": "AAPL", "fact_check": {"company_info": {}}}
        apply_fetched_volume(sig, 1_250_000)
        self.assertEqual(sig["avg_volume"], 1_250_000)
        self.assertEqual(sig["fact_check"]["company_info"]["avg_volume"], 1_250_000)

    def test_resolve_pop_pct_no_default(self):
        self.assertIsNone(resolve_pop_pct({"symbol": "AAPL"}))
        self.assertIsNone(resolve_pop_pct({"symbol": "AAPL", "pop_from_sim": 0}))
        self.assertEqual(resolve_pop_pct({"symbol": "AAPL", "pop_from_sim": 0.62}), 62.0)
        self.assertEqual(resolve_pop_pct({"symbol": "AAPL", "pop_from_sim": 72}), 72.0)

    def test_paper_guard_blocks_partial_signal(self):
        guard = PaperReadinessGuard()
        signal = {
            "symbol": "AAPL",
            "current_price": 100.0,
            "confidence": 0.75,
            "data_quality": SignalDataQuality.PARTIAL_PRICE_ONLY.value,
        }
        config = {
            "execution": {"mode": "PAPER_ALPACA"},
            "paper_trading_safety": {"enabled": True, "block_low_confidence_below": 50},
        }
        ok, failures = guard.can_submit_paper_order(
            config,
            signal,
            context={"simulate_paper_mode": True},
        )
        self.assertFalse(ok)
        self.assertIn("signal_data_quality_not_complete", failures)


class TestKalshiDebug(unittest.TestCase):
    @patch("engines.kalshi_engine.NewsAPIIntegration", None)
    @patch("engines.kalshi_engine.WeatherValidationEngine", None)
    @patch("engines.kalshi_engine.WeatherConsistencyEngine", None)
    def test_debug_hidden_by_default(self, *_mocks):
        engine = KalshiPredictionEngine({"debug": {"kalshi_expiry_debug": False}})
        buf = StringIO()
        with patch("sys.stdout", buf):
            engine._calculate_days_to_expiry("2026-12-31")
        self.assertNotIn("SCANNING DEBUG", buf.getvalue())

    @patch("engines.kalshi_engine.NewsAPIIntegration", None)
    @patch("engines.kalshi_engine.WeatherValidationEngine", None)
    @patch("engines.kalshi_engine.WeatherConsistencyEngine", None)
    def test_debug_prints_when_enabled(self, *_mocks):
        engine = KalshiPredictionEngine({"debug": {"kalshi_expiry_debug": True}})
        buf = StringIO()
        with patch("sys.stdout", buf):
            engine._calculate_days_to_expiry("2026-12-31")
        self.assertIn("SCANNING DEBUG", buf.getvalue())


if __name__ == "__main__":
    unittest.main()
