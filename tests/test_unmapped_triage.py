"""Tests for unmapped engine triage and inventory quality gate."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from scripts.inventory_analysis import (
    classify_entry,
    compute_dedup_summary,
    infer_group,
    is_import_banner,
    is_logical_engine,
    normalize_symbol,
)


class TestInventoryAnalysis(unittest.TestCase):
    def test_import_banner_not_engine(self):
        self.assertTrue(is_import_banner("from foo import Bar", "banner"))
        self.assertFalse(is_logical_engine({
            "name": "from foo import Bar",
            "category": "banner",
            "file_path": "main.py",
            "triage_classification": "UTILITY_NOT_ENGINE",
        }))

    def test_normalize_symbol_import(self):
        sym = normalize_symbol("from brain.unified_meta_brain import UnifiedMetaBrain")
        self.assertEqual(sym, "unifiedmetabrain")

    def test_infer_group_execution(self):
        self.assertEqual(infer_group("ExecutionRouter", "core/execution/execution_router.py"), "ExecutionGroup")

    def test_dedup_summary_structure(self):
        entries = [
            {"name": "from x import Y", "category": "banner", "file_path": "main.py",
             "triage_classification": "UTILITY_NOT_ENGINE"},
            {"name": "MarketCrashDetectorV2", "category": "class", "file_path": "engines/market_crash_detector_v2.py"},
        ]
        d = compute_dedup_summary(entries)
        self.assertIn("raw_items_found", d)
        self.assertEqual(d["raw_items_found"], 2)


class TestTriageArtifacts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        inv = os.path.join(ROOT, "data", "runtime", "engine_inventory.json")
        if not os.path.isfile(inv):
            subprocess.run([sys.executable, os.path.join(ROOT, "scripts", "audit_engine_inventory.py")],
                           cwd=ROOT, check=True, timeout=600)
        triage_script = os.path.join(ROOT, "scripts", "triage_unmapped_engines.py")
        if not os.path.isfile(os.path.join(ROOT, "data", "runtime", "unmapped_engine_triage.json")):
            subprocess.run([sys.executable, triage_script], cwd=ROOT, check=True, timeout=900)

    def test_triage_json_exists(self):
        path = os.path.join(ROOT, "data", "runtime", "unmapped_engine_triage.json")
        self.assertTrue(os.path.isfile(path))
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        self.assertGreater(data["summary"]["starting_unmapped"], 0)
        self.assertEqual(len(data["records"]), data["summary"]["starting_unmapped"])

    def test_triage_md_exists(self):
        self.assertTrue(os.path.isfile(os.path.join(ROOT, "reports", "unmapped_engine_triage.md")))

    def test_quarantine_md_exists(self):
        self.assertTrue(os.path.isfile(os.path.join(ROOT, "reports", "deprecated_orphaned_candidates.md")))

    def test_all_unmapped_classified(self):
        path = os.path.join(ROOT, "data", "runtime", "unmapped_engine_triage.json")
        with open(path, encoding="utf-8") as f:
            records = json.load(f)["records"]
        valid = {
            "ACTIVE_CURRENT", "ACTIVE_LEGACY", "REPLACED_BY_NEW_ENGINE",
            "ORPHANED_UNCALLED", "DEMO_ONLY", "TEST_ONLY", "UTILITY_NOT_ENGINE",
            "DUPLICATE_ALIAS", "UNKNOWN_NEEDS_REVIEW",
        }
        for r in records:
            self.assertIn(r["classification"], valid, r.get("name"))

    def test_dedup_summary_in_inventory(self):
        path = os.path.join(ROOT, "data", "runtime", "engine_inventory.json")
        with open(path, encoding="utf-8") as f:
            inv = json.load(f)
        self.assertIn("dedup_summary", inv)
        self.assertIn("unique_logical_engines", inv)

    def test_quality_check_runs(self):
        script = os.path.join(ROOT, "scripts", "check_engine_inventory_quality.py")
        r = subprocess.run([sys.executable, script], cwd=ROOT, capture_output=True, text=True, timeout=60)
        self.assertIn("ENGINE INVENTORY QUALITY CHECK", r.stdout)


class TestConfigSafety(unittest.TestCase):
    def test_alert_only_unchanged(self):
        with open(os.path.join(ROOT, "config.json"), encoding="utf-8") as f:
            cfg = json.load(f)
        self.assertEqual(cfg["execution"]["mode"], "ALERT_ONLY")
        self.assertFalse(cfg["paper_trading"]["enabled"])


if __name__ == "__main__":
    unittest.main()
