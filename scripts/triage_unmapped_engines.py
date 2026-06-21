#!/usr/bin/env python3
"""Triage all unmapped engine inventory items — classify without deleting."""

from __future__ import annotations

import json
import os
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from typing import Any, Dict, List

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from scripts.inventory_analysis import (
    ReferenceIndex,
    build_canonical_map,
    classify_entry,
    compute_dedup_summary,
    infer_group,
    is_logical_engine,
    normalize_symbol,
)

INVENTORY_PATH = os.path.join(ROOT, "data", "runtime", "engine_inventory.json")
TRIAGE_JSON = os.path.join(ROOT, "data", "runtime", "unmapped_engine_triage.json")
TRIAGE_MD = os.path.join(ROOT, "reports", "unmapped_engine_triage.md")
QUARANTINE_MD = os.path.join(ROOT, "reports", "deprecated_orphaned_candidates.md")


def load_inventory() -> Dict[str, Any]:
    with open(INVENTORY_PATH, encoding="utf-8") as f:
        return json.load(f)


def triage_all(inventory: Dict[str, Any]) -> Dict[str, Any]:
    entries: List[Dict[str, Any]] = inventory.get("entries", [])
    unmapped = [e for e in entries if e.get("recommended_group") == "Unmapped"]
    starting_unmapped = len(unmapped)

    print(f"Building reference index...")
    refs = ReferenceIndex(ROOT)
    canon = build_canonical_map(entries)

    triage_records: List[Dict[str, Any]] = []
    entry_by_id = {e["engine_id"]: e for e in entries}

    print(f"Triaging {starting_unmapped} unmapped items...")
    for i, entry in enumerate(unmapped):
        if (i + 1) % 100 == 0:
            print(f"  {i + 1}/{starting_unmapped}")
        record = classify_entry(entry, refs, canon)
        triage_records.append(record)

        # Update inventory entry in place
        e = entry_by_id[entry["engine_id"]]
        e["triage_classification"] = record["classification"]
        e["triage_confidence"] = record["confidence"]
        e["recommended_action"] = record["recommended_action"]
        ag = record["assigned_group"]
        cls = record["classification"]

        if ag == "Utility" or cls == "UTILITY_NOT_ENGINE":
            e["inventory_bucket"] = "Utility"
            e["recommended_group"] = "Utility"
        elif ag in ("TestOnly", "DemoOnly") or cls in ("TEST_ONLY", "DEMO_ONLY"):
            e["inventory_bucket"] = ag
            e["recommended_group"] = ag
        elif ag == "Deprecated" or cls in ("ORPHANED_UNCALLED", "REPLACED_BY_NEW_ENGINE"):
            e["inventory_bucket"] = "Deprecated"
            e["recommended_group"] = "Deprecated"
        elif cls == "DUPLICATE_ALIAS":
            e["inventory_bucket"] = "Utility"
            e["recommended_group"] = "Utility"
        elif ag not in ("Unmapped", "Unknown", None):
            e["recommended_group"] = ag
        if record.get("possible_replacement"):
            e["possible_replacement"] = record["possible_replacement"]

    # Re-triage counts for ALL entries (utilities/duplicates among mapped too)
    all_classifications: Counter = Counter()
    for e in entries:
        cls = e.get("triage_classification")
        if not cls and e.get("recommended_group") != "Unmapped":
            cls = "ALREADY_MAPPED"
            e["triage_classification"] = cls
        if cls:
            all_classifications[cls] += 1

    triage_class_counter = Counter(r["classification"] for r in triage_records)
    assigned_counter = Counter(r["assigned_group"] for r in triage_records)
    high_risk = [r for r in triage_records if r.get("high_risk")]

    # Final unmapped = inventory entries still without production group
    final_unmapped = sum(
        1 for e in entries
        if e.get("recommended_group") == "Unmapped"
    )

    dedup = compute_dedup_summary(entries)

    # Rebuild group counts
    by_group: Dict[str, int] = defaultdict(int)
    for e in entries:
        if e.get("triage_classification") in ("UTILITY_NOT_ENGINE", "DUPLICATE_ALIAS", "TEST_ONLY"):
            by_group["Utility"] += 1
        elif e.get("inventory_bucket"):
            by_group[e["inventory_bucket"]] += 1
        else:
            by_group[e.get("recommended_group", "Unmapped")] += 1

    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "starting_unmapped": starting_unmapped,
        "utility_not_engine": triage_class_counter.get("UTILITY_NOT_ENGINE", 0),
        "duplicate_aliases": triage_class_counter.get("DUPLICATE_ALIAS", 0),
        "active_current": triage_class_counter.get("ACTIVE_CURRENT", 0),
        "active_legacy": triage_class_counter.get("ACTIVE_LEGACY", 0),
        "replaced_by_new_engine": triage_class_counter.get("REPLACED_BY_NEW_ENGINE", 0),
        "orphaned_uncalled": triage_class_counter.get("ORPHANED_UNCALLED", 0),
        "demo_only": triage_class_counter.get("DEMO_ONLY", 0),
        "test_only": triage_class_counter.get("TEST_ONLY", 0),
        "unknown_needs_review": triage_class_counter.get("UNKNOWN_NEEDS_REVIEW", 0),
        "final_unmapped_remaining": final_unmapped,
        "high_risk_unmapped_count": len(high_risk),
        "dedup_summary": dedup,
        "assigned_groups": dict(assigned_counter),
        "all_classifications_in_inventory": dict(all_classifications),
        "engines_by_group_after_triage": dict(by_group),
    }

    return {
        "summary": summary,
        "triage_records": triage_records,
        "high_risk_items": sorted(high_risk, key=lambda x: -x.get("confidence", 0)),
        "updated_entries": entries,
    }


def write_triage_md(result: Dict[str, Any]) -> None:
    s = result["summary"]
    lines = [
        "# Unmapped Engine Triage Report",
        f"\nGenerated: {s['generated_at']}",
        "\n## UNMAPPED TRIAGE SUMMARY\n",
        f"- **Starting unmapped:** {s['starting_unmapped']}",
        f"- **Utility/not-engine:** {s['utility_not_engine']}",
        f"- **Duplicate aliases:** {s['duplicate_aliases']}",
        f"- **Active current:** {s['active_current']}",
        f"- **Active legacy:** {s['active_legacy']}",
        f"- **Replaced by new engine:** {s['replaced_by_new_engine']}",
        f"- **Orphaned uncalled:** {s['orphaned_uncalled']}",
        f"- **Demo only:** {s['demo_only']}",
        f"- **Test only:** {s['test_only']}",
        f"- **Unknown needs review:** {s['unknown_needs_review']}",
        f"- **Final unmapped remaining:** {s['final_unmapped_remaining']}",
        "\n## Deduped Inventory Quality\n",
    ]
    for k, v in s["dedup_summary"].items():
        lines.append(f"- **{k}:** {v}")

    lines.append("\n## TOP PRIORITY UNMAPPED (High Risk)\n")
    for r in result["high_risk_items"][:40]:
        lines.append(
            f"- `{r['name']}` ({r['file_path']}:{r.get('line', '?')}) — "
            f"**{r['classification']}** → {r['assigned_group']} "
            f"(action: {r['recommended_action']}, confidence: {r['confidence']:.0%})"
        )

    lines.append("\n## Classification Breakdown\n")
    for cls, count in Counter(r["classification"] for r in result["triage_records"]).most_common():
        lines.append(f"- **{cls}:** {count}")

    lines.append("\n## Sample: Active Current (mapped to groups)\n")
    for r in result["triage_records"]:
        if r["classification"] == "ACTIVE_CURRENT":
            lines.append(
                f"- `{r['name']}` → **{r['assigned_group']}** ({r['file_path']}) "
                f"callers: {', '.join(r['callers'][:3]) or 'none'}"
            )
        if len([x for x in lines if "ACTIVE_CURRENT" in x or "→ **" in x]) > 50:
            break

    lines.append("\n## Sample: Orphaned / Replaced\n")
    shown = 0
    for r in result["triage_records"]:
        if r["classification"] in ("ORPHANED_UNCALLED", "REPLACED_BY_NEW_ENGINE"):
            rep = f" → replacement: {r['possible_replacement']}" if r.get("possible_replacement") else ""
            lines.append(f"- `{r['name']}` ({r['file_path']}) — {r['classification']}{rep}")
            shown += 1
        if shown >= 30:
            break

    os.makedirs(os.path.dirname(TRIAGE_MD), exist_ok=True)
    with open(TRIAGE_MD, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def write_quarantine_md(result: Dict[str, Any]) -> None:
    lines = [
        "# Deprecated / Orphaned Candidates",
        f"\nGenerated: {result['summary']['generated_at']}",
        "\nNo files deleted or moved in this pass.\n",
        "## Quarantine Recommendations\n",
    ]
    action_map = {
        "ORPHANED_UNCALLED": "QUARANTINE",
        "REPLACED_BY_NEW_ENGINE": "DEPRECATE",
        "ACTIVE_LEGACY": "MANUAL_REVIEW",
        "DEMO_ONLY": "KEEP (diagnostics only)",
    }
    for cls in ("REPLACED_BY_NEW_ENGINE", "ORPHANED_UNCALLED", "ACTIVE_LEGACY", "DEMO_ONLY"):
        items = [r for r in result["triage_records"] if r["classification"] == cls]
        if not items:
            continue
        lines.append(f"\n### {cls} ({len(items)} items)\n")
        for r in items[:50]:
            action = action_map.get(cls, r["recommended_action"])
            rep = ""
            if r.get("possible_replacement"):
                rep = f" | replacement: `{r['possible_replacement']}`"
            lines.append(
                f"- **{action}** — `{r['file_path']}` `{r['name']}`{rep}"
            )
        if len(items) > 50:
            lines.append(f"- ... and {len(items) - 50} more")

    with open(QUARANTINE_MD, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def update_inventory_file(result: Dict[str, Any]) -> None:
    inv = load_inventory()
    inv["entries"] = result["updated_entries"]
    inv["triage_summary"] = result["summary"]
    inv["dedup_summary"] = result["summary"]["dedup_summary"]
    inv["unmapped_count"] = result["summary"]["final_unmapped_remaining"]
    inv["engines_by_group"] = result["summary"]["engines_by_group_after_triage"]
    inv["triaged_at"] = result["summary"]["generated_at"]
    inv["unique_logical_engines"] = result["summary"]["dedup_summary"]["unique_logical_engines"]
    with open(INVENTORY_PATH, "w", encoding="utf-8") as f:
        json.dump(inv, f, indent=2, default=str)


def main() -> None:
    if not os.path.isfile(INVENTORY_PATH):
        print("Run scripts/audit_engine_inventory.py first.")
        sys.exit(1)

    inventory = load_inventory()
    result = triage_all(inventory)

    os.makedirs(os.path.dirname(TRIAGE_JSON), exist_ok=True)
    with open(TRIAGE_JSON, "w", encoding="utf-8") as f:
        json.dump(
            {"summary": result["summary"], "records": result["triage_records"]},
            f, indent=2, default=str,
        )

    write_triage_md(result)
    write_quarantine_md(result)
    update_inventory_file(result)

    s = result["summary"]
    print(f"\nWrote {TRIAGE_MD}")
    print(f"Wrote {TRIAGE_JSON}")
    print(f"Wrote {QUARANTINE_MD}")
    print(f"Updated {INVENTORY_PATH}")
    print("\nUNMAPPED TRIAGE SUMMARY")
    print(f"  Starting unmapped: {s['starting_unmapped']}")
    print(f"  Utility/not-engine: {s['utility_not_engine']}")
    print(f"  Duplicate aliases: {s['duplicate_aliases']}")
    print(f"  Active current: {s['active_current']}")
    print(f"  Active legacy: {s['active_legacy']}")
    print(f"  Replaced: {s['replaced_by_new_engine']}")
    print(f"  Orphaned: {s['orphaned_uncalled']}")
    print(f"  Demo only: {s['demo_only']}")
    print(f"  Test only: {s['test_only']}")
    print(f"  Unknown needs review: {s['unknown_needs_review']}")
    print(f"  Final unmapped remaining: {s['final_unmapped_remaining']}")
    print(f"  High-risk unmapped: {s['high_risk_unmapped_count']}")


if __name__ == "__main__":
    main()
