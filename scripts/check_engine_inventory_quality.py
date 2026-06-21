#!/usr/bin/env python3
"""Engine inventory quality gate — warn or fail on triage regressions."""

from __future__ import annotations

import argparse
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

INVENTORY_PATH = os.path.join(ROOT, "data", "runtime", "engine_inventory.json")
TRIAGE_PATH = os.path.join(ROOT, "data", "runtime", "unmapped_engine_triage.json")

CRITICAL_GROUPS = {
    "ExecutionGroup": ("execution", "paper", "broker", "alpaca", "trade_memory", "submit_signal"),
    "ReportingGroup": ("telegram", "report", "digest", "gallery"),
    "DecisionGroup": ("decision", "jury", "confluence", "gate", "approval", "strategy_router"),
}

HIGH_RISK_UNMAPPED_MAX = 100
UNMAPPED_REMAINING_MAX = 100


def load_json(path: str) -> dict:
    if not os.path.isfile(path):
        return {}
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def check(*, strict: bool = False) -> int:
    inv = load_json(INVENTORY_PATH)
    triage = load_json(TRIAGE_PATH)
    summary = triage.get("summary") or inv.get("triage_summary") or {}

    warnings: list[str] = []
    errors: list[str] = []

    if not inv:
        errors.append("engine_inventory.json missing — run audit + triage scripts")
        _report(warnings, errors, strict)
        return 1

    unmapped_remaining = summary.get(
        "final_unmapped_remaining",
        inv.get("unmapped_count", 9999),
    )
    if unmapped_remaining > UNMAPPED_REMAINING_MAX:
        msg = f"unmapped_remaining={unmapped_remaining} exceeds {UNMAPPED_REMAINING_MAX}"
        (errors if strict else warnings).append(msg)

    records = triage.get("records") or []
    high_risk = [r for r in records if r.get("high_risk")]
    high_risk_unmapped = [
        r for r in high_risk
        if r.get("classification") in ("UNKNOWN_NEEDS_REVIEW", "ACTIVE_LEGACY")
        and r.get("assigned_group") in ("Unmapped", "Unknown")
    ]
    if high_risk_unmapped:
        msg = f"{len(high_risk_unmapped)} high-risk items still unmapped/unknown"
        (errors if strict else warnings).append(msg)
        for r in high_risk_unmapped[:10]:
            warnings.append(f"  HIGH RISK: {r.get('name')} ({r.get('file_path')}) — {r.get('classification')}")

    # ACTIVE_CURRENT must have group
    for r in records:
        if r.get("classification") == "ACTIVE_CURRENT" and r.get("assigned_group") in ("Unmapped", "Unknown", None):
            errors.append(f"ACTIVE_CURRENT without group: {r.get('engine_id')}")

    # Critical domain unmapped in inventory
    for e in inv.get("entries", []):
        if e.get("recommended_group") != "Unmapped":
            continue
        if e.get("triage_classification") in (
            "UTILITY_NOT_ENGINE", "DUPLICATE_ALIAS", "TEST_ONLY", "DEMO_ONLY",
            "ORPHANED_UNCALLED", "REPLACED_BY_NEW_ENGINE",
        ):
            continue
        if e.get("inventory_bucket") in ("Utility", "DemoOnly", "Deprecated", "TestOnly"):
            continue
        text = f"{e.get('name', '')} {e.get('file_path', '')}".lower()
        for group, keywords in CRITICAL_GROUPS.items():
            if any(k in text for k in keywords):
                msg = f"Critical {group} item still unmapped: {e.get('name')} ({e.get('file_path')})"
                errors.append(msg)

    # Demo items must not be ACTIVE_CURRENT in Decision path
    for r in records:
        if r.get("classification") == "DEMO_ONLY" and r.get("assigned_group") == "DecisionGroup":
            errors.append(f"Demo item mapped to DecisionGroup: {r.get('name')}")

    # Unknown every_cycle
    for e in inv.get("entries", []):
        if e.get("triage_classification") != "UNKNOWN_NEEDS_REVIEW":
            continue
        if e.get("runs_every_cycle") == "yes":
            warnings.append(f"Unknown item marked every_cycle: {e.get('name')}")

    # Config safety
    cfg_path = os.path.join(ROOT, "config.json")
    if os.path.isfile(cfg_path):
        with open(cfg_path, encoding="utf-8") as f:
            cfg = json.load(f)
        if cfg.get("execution", {}).get("mode") != "ALERT_ONLY":
            errors.append("execution.mode is not ALERT_ONLY")
        if cfg.get("paper_trading", {}).get("enabled"):
            errors.append("paper_trading.enabled is true")
        if cfg.get("execution", {}).get("allow_live_trading"):
            errors.append("allow_live_trading is true")

    _report(warnings, errors, strict)
    if errors:
        return 1
    return 0


def _report(warnings: list[str], errors: list[str], strict: bool) -> None:
    print("ENGINE INVENTORY QUALITY CHECK")
    print(f"Mode: {'STRICT' if strict else 'warn'}")
    if warnings:
        print(f"\nWarnings ({len(warnings)}):")
        for w in warnings:
            print(f"  WARN: {w}")
    if errors:
        print(f"\nErrors ({len(errors)}):")
        for e in errors:
            print(f"  ERROR: {e}")
    if not warnings and not errors:
        print("\nOK: All quality checks passed")


def main() -> None:
    parser = argparse.ArgumentParser(description="Engine inventory quality gate")
    parser.add_argument("--strict", action="store_true", help="Fail on warnings thresholds")
    args = parser.parse_args()
    sys.exit(check(strict=args.strict))


if __name__ == "__main__":
    main()
