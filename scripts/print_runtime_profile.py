#!/usr/bin/env python3
"""Print latest runtime profile from JSONL log."""

from __future__ import annotations

import json
import os
import sys
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from core.runtime_paths import runtime_path


def main() -> None:
    log_path = runtime_path("performance", "engine_runtime.jsonl")
    if not os.path.isfile(log_path):
        print("No runtime profile data yet.")
        return
    by_cycle: dict = defaultdict(list)
    with open(log_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
                by_cycle[rec.get("cycle_attempt", 0)].append(rec)
            except json.JSONDecodeError:
                continue
    if not by_cycle:
        print("No records.")
        return
    last_cycle = max(by_cycle.keys())
    recs = by_cycle[last_cycle]
    total = sum(r.get("duration_ms", 0) for r in recs)
    print(f"RUNTIME PROFILE (cycle {last_cycle})")
    print(f"Total tracked engine time: {total:.0f} ms")
    for r in sorted(recs, key=lambda x: x.get("duration_ms", 0), reverse=True)[:15]:
        print(f"  {r.get('engine_id')}: {r.get('duration_ms', 0):.0f} ms [{r.get('status')}]")


if __name__ == "__main__":
    main()
