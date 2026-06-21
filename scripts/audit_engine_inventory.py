#!/usr/bin/env python3
"""Scan Phasma source + logs for engine/stage inventory."""

from __future__ import annotations

import ast
import json
import os
import re
import sys
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Set

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from scripts.inventory_analysis import (
    compute_dedup_summary,
    infer_group,
    is_import_banner,
    is_logical_engine,
    normalize_symbol,
)

SCAN_DIRS = ("main.py", "engines", "brain", "core", "utils", "scripts")
NAME_RE = re.compile(
    r"(Engine|Detector|Monitor|Scanner|Analyzer|Intelligence|Brain|Worker|"
    r"Integrator|Tracker|Manager|Service|Jury|Convergence|Router|Guard|Reporter|Grader)",
    re.I,
)
BANNER_RE = re.compile(
    r"(PHASE|STAGE|ANALYZE|SYNTHESIZE|INTELLIGENCE|META BRAIN|UNIFIED|DETECTOR|"
    r"SCANNER|DISCOVERY|CONVERGENCE|JURY|RISK|TELEGRAM|KALSHI|UNDERGROUND|"
    r"THEMATIC|PARTNERSHIP|POLITICIAN|INSIDER|EXIT MANAGER|WORKER HEALTH|GROUP HEALTH)",
    re.I,
)

GROUP_MAP = {
    "ingest": "IngestGroup",
    "news": "IngestGroup",
    "rss": "IngestGroup",
    "market": "MarketGroup",
    "cache": "MarketGroup",
    "fred": "MarketGroup",
    "regime": "MarketGroup",
    "crash": "RiskGroup",
    "macro": "RiskGroup",
    "risk": "RiskGroup",
    "discovery": "DiscoveryGroup",
    "universal": "DiscoveryGroup",
    "bull": "DiscoveryGroup",
    "social": "DiscoveryGroup",
    "partnership": "DiscoveryGroup",
    "underground": "DiscoveryGroup",
    "thematic": "DiscoveryGroup",
    "sector": "DiscoveryGroup",
    "insider": "DiscoveryGroup",
    "politician": "DiscoveryGroup",
    "geo": "DiscoveryGroup",
    "kalshi": "DiscoveryGroup",
    "convergence": "DiscoveryGroup",
    "resolver": "EnrichmentGroup",
    "validation": "EnrichmentGroup",
    "monte": "SignalGroup",
    "simulation": "SignalGroup",
    "options": "SignalGroup",
    "decision": "DecisionGroup",
    "confluence": "DecisionGroup",
    "jury": "DecisionGroup",
    "gate": "DecisionGroup",
    "execution": "ExecutionGroup",
    "paper": "ExecutionGroup",
    "telegram": "ReportingGroup",
    "gallery": "ReportingGroup",
    "outcome": "LearningGroup",
    "grader": "LearningGroup",
    "exit": "LearningGroup",
}

KNOWN_SYSTEMS = [
    ("unified_meta_brain", "Unified Meta Brain", "brain/unified_meta_brain.py", "DiscoveryGroup"),
    ("universal_trading_intelligence", "Universal Trading Intelligence", "brain/universal_trading_intelligence.py", "DiscoveryGroup"),
    ("signal_convergence", "Signal Convergence Engine", "brain/signal_convergence_engine.py", "DiscoveryGroup"),
    ("market_crash_detector_v2", "Market Crash Detector V2", "engines/market_crash_detector_v2.py", "RiskGroup"),
    ("execution_router", "Execution Router", "core/execution/execution_router.py", "ExecutionGroup"),
    ("paper_readiness_guard", "Paper Readiness Guard", "core/execution/paper_readiness_guard.py", "ExecutionGroup"),
    ("worker_supervisor", "Worker Supervisor", "core/supervisor/supervisor.py", "ReportingGroup"),
    ("group_coordinator", "Group Coordinator", "core/supervisor/group_coordinator.py", "ReportingGroup"),
    ("signal_decision", "SignalDecision Pipeline", "core/signals/signal_decision.py", "DecisionGroup"),
    ("strategy_router", "Strategy Router", "core/signals/strategy_router.py", "DecisionGroup"),
]


def _infer_group(name: str, path: str) -> str:
    return infer_group(name, path)


def _scan_python_file(path: str) -> List[Dict[str, Any]]:
    found = []
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            source = f.read()
        tree = ast.parse(source, filename=path)
    except Exception:
        return found

    rel = os.path.relpath(path, ROOT).replace("\\", "/")
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            if NAME_RE.search(node.name):
                found.append({"kind": "class", "name": node.name, "path": rel, "line": node.lineno})
        elif isinstance(node, ast.FunctionDef):
            if NAME_RE.search(node.name) and not node.name.startswith("_"):
                found.append({"kind": "function", "name": node.name, "path": rel, "line": node.lineno})

    for m in BANNER_RE.finditer(source):
        line_no = source[: m.start()].count("\n") + 1
        line = source.splitlines()[line_no - 1].strip()[:120]
        found.append({"kind": "banner", "name": line, "path": rel, "line": line_no})
    return found


def _scan_logs() -> Set[str]:
    banners: Set[str] = set()
    log_dirs = [
        os.path.join(ROOT, "data", "runtime", "logs"),
        os.path.join(ROOT, "data", "runtime"),
    ]
    for d in log_dirs:
        if not os.path.isdir(d):
            continue
        for fn in os.listdir(d):
            if not fn.endswith((".log", ".txt")):
                continue
            fp = os.path.join(d, fn)
            try:
                with open(fp, encoding="utf-8", errors="replace") as f:
                    for line in f:
                        if BANNER_RE.search(line):
                            banners.add(line.strip()[:120])
            except Exception:
                pass
    return banners


def build_inventory() -> Dict[str, Any]:
    entries: Dict[str, Dict[str, Any]] = {}
    for rel_root in SCAN_DIRS:
        base = os.path.join(ROOT, rel_root)
        if os.path.isfile(base):
            files = [base]
        elif os.path.isdir(base):
            files = []
            for dirpath, _, filenames in os.walk(base):
                for fn in filenames:
                    if fn.endswith(".py"):
                        files.append(os.path.join(dirpath, fn))
        else:
            continue
        for fp in files:
            for item in _scan_python_file(fp):
                eid = f"{item['path']}:{item['name']}"
                if eid not in entries:
                    entries[eid] = {
                        "engine_id": eid,
                        "name": item["name"],
                        "class_or_banner": item["name"],
                        "file_path": item["path"],
                        "discovered_by": "source_scan",
                        "line": item.get("line"),
                        "category": item["kind"],
                        "recommended_group": _infer_group(item["name"], item["path"]),
                        "creates_signals": "unknown",
                        "approves_decisions": "yes" if "jury" in item["name"].lower() or "decision" in item["name"].lower() else "unknown",
                        "executes_trades": "yes" if "execution" in item["name"].lower() and "router" in item["name"].lower() else "no",
                        "runs_every_cycle": "unknown",
                        "estimated_runtime_cost": "MEDIUM",
                    }

    for eid, label, path, group in KNOWN_SYSTEMS:
        if eid not in entries:
            entries[eid] = {
                "engine_id": eid,
                "name": label,
                "file_path": path,
                "discovered_by": "known_list",
                "recommended_group": group,
                "runs_every_cycle": "yes" if group in ("IngestGroup", "MarketGroup", "DecisionGroup") else "no",
                "estimated_runtime_cost": "HIGH" if "universal" in eid or "unified" in eid else "MEDIUM",
            }

    log_banners = _scan_logs()
    for i, banner in enumerate(sorted(log_banners)):
        eid = f"log_banner:{i}"
        entries[eid] = {
            "engine_id": eid,
            "name": banner,
            "log_banner": banner,
            "discovered_by": "log_scan",
            "recommended_group": _infer_group(banner, ""),
        }

    by_group: Dict[str, List[str]] = defaultdict(list)
    for eid, e in entries.items():
        by_group[e.get("recommended_group", "Unmapped")].append(e.get("name", eid))

    call_tree = {
        "Unified Meta Brain": {
            "Phase 1 Ingest": ["CycleDataContext", "NewsIngestWorker"],
            "Phase 2 Analyze": [
                "Universal Trading Intelligence",
                "Bull Run Detector",
                "News Scanner",
                "Social Engine",
                "Partnership Monitor",
                "Underground Discovery",
            ],
            "Phase 3 Synthesize": [
                "Thematic Analysis",
                "Sector Intelligence",
                "Expansion Engine",
                "Bias Breaker",
                "Convergence Engine",
            ],
            "Phase 4 Final Selection": [
                "Data Gates",
                "Strategy Router",
                "Confluence",
                "Jury",
                "Execution Router",
            ],
        },
        "GroupCoordinator": {
            "IngestGroup": by_group.get("IngestGroup", [])[:10],
            "MarketGroup": by_group.get("MarketGroup", [])[:10],
            "RiskGroup": by_group.get("RiskGroup", [])[:10],
            "DiscoveryGroup": by_group.get("DiscoveryGroup", [])[:10],
            "DecisionGroup": by_group.get("DecisionGroup", [])[:10],
            "ExecutionGroup": by_group.get("ExecutionGroup", [])[:10],
            "ReportingGroup": by_group.get("ReportingGroup", [])[:10],
            "LearningGroup": by_group.get("LearningGroup", [])[:10],
        },
    }

    entry_list = list(entries.values())

    # Mark import-line banners as non-engines upfront
    for e in entry_list:
        if is_import_banner(str(e.get("name", "")), str(e.get("category", ""))):
            e["pre_classification"] = "UTILITY_NOT_ENGINE"
            e["inventory_bucket"] = "Utility"

    dedup = compute_dedup_summary(entry_list)
    # Count logical engines only
    logical_count = dedup["unique_logical_engines"]

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total_engines": len(entry_list),
        "raw_items_found": dedup["raw_items_found"],
        "unique_log_banners": dedup["unique_log_banners"],
        "unique_source_symbols": dedup["unique_source_symbols"],
        "unique_logical_engines": logical_count,
        "utilities_excluded": dedup["utilities_excluded"],
        "duplicates_merged": dedup["duplicates_merged"],
        "dedup_summary": dedup,
        "engines_by_group": {k: len(v) for k, v in by_group.items()},
        "unmapped_count": len(by_group.get("Unmapped", [])),
        "entries": entry_list,
        "call_tree": call_tree,
    }


def write_reports(data: Dict[str, Any]) -> None:
    reports = os.path.join(ROOT, "reports")
    os.makedirs(reports, exist_ok=True)
    runtime = os.path.join(ROOT, "data", "runtime")
    os.makedirs(runtime, exist_ok=True)

    json_path = os.path.join(runtime, "engine_inventory.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, default=str)

    md_lines = [
        "# Phasma Engine Inventory",
        f"\nGenerated: {data['generated_at']}",
        f"\nRaw items found: **{data.get('raw_items_found', data['total_engines'])}**",
        f"Unique logical engines: **{data.get('unique_logical_engines', '?')}**",
        f"Utilities excluded: **{data.get('utilities_excluded', 0)}**",
        f"Unmapped (pre-triage): **{data['unmapped_count']}**",
        "\n## By Group\n",
    ]
    for group, count in sorted(data["engines_by_group"].items(), key=lambda x: -x[1]):
        md_lines.append(f"- **{group}**: {count}")
    md_lines.append("\n## Sample Entries\n")
    for e in data["entries"][:40]:
        md_lines.append(f"- `{e.get('name')}` — {e.get('file_path', 'log')} → {e.get('recommended_group', '?')}")
    with open(os.path.join(reports, "engine_inventory.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(md_lines))

    tree_lines = ["# Runtime Call Tree\n"]
    def _render(node: Any, indent: int = 0) -> None:
        if isinstance(node, dict):
            for k, v in node.items():
                tree_lines.append("  " * indent + f"- {k}")
                _render(v, indent + 1)
        elif isinstance(node, list):
            for item in node[:15]:
                tree_lines.append("  " * indent + f"- {item}")
    _render(data["call_tree"])
    with open(os.path.join(reports, "runtime_call_tree.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(tree_lines))

    print(f"Wrote {json_path}")
    print(f"Wrote reports/engine_inventory.md")
    print(f"Wrote reports/runtime_call_tree.md")
    print(f"Total engines: {data['total_engines']}")


def main() -> None:
    data = build_inventory()
    write_reports(data)


if __name__ == "__main__":
    main()
