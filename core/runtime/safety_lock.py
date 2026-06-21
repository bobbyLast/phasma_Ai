"""Startup safety lock — confirm ALERT_ONLY before any cycle work."""

from __future__ import annotations

from typing import Any, Dict, Tuple


def verify_safety_lock(config: Dict[str, Any]) -> Tuple[bool, list]:
    """Return (ok, violations). Fail-closed on unsafe modes."""
    violations = []
    exec_cfg = config.get("execution") or {}
    mode = str(exec_cfg.get("mode", "ALERT_ONLY")).upper()
    if mode != "ALERT_ONLY":
        violations.append(f"execution.mode={mode} (expected ALERT_ONLY)")
    if exec_cfg.get("allow_live_trading"):
        violations.append("allow_live_trading=true")
    paper = config.get("paper_trading") or {}
    if paper.get("enabled"):
        violations.append("paper_trading.enabled=true")
    if exec_cfg.get("kalshi_execution_enabled"):
        violations.append("kalshi_execution_enabled=true")
    return len(violations) == 0, violations


def print_startup_safety(config: Dict[str, Any], *, execution_mode: str = "ALERT_ONLY") -> None:
    """Print mandatory startup safety lines."""
    paper_enabled = bool((config.get("paper_trading") or {}).get("enabled", False))
    live_allowed = bool((config.get("execution") or {}).get("allow_live_trading", False))
    kalshi_exec = bool((config.get("execution") or {}).get("kalshi_execution_enabled", False))
    kalshi_label = "INTEL_ONLY" if not kalshi_exec else "EXECUTION_ENABLED"

    print("=" * 50)
    print(f"Execution mode: {execution_mode}")
    print(f"Paper trading: {'enabled' if paper_enabled else 'disabled'}")
    print(f"Live trading: {'enabled' if live_allowed else 'disabled'}")
    print(f"Kalshi: {kalshi_label}")
    print("Runtime refactor: inventory/grouping mode")
    print("=" * 50)

    ok, violations = verify_safety_lock(config)
    if not ok:
        print("⚠️ SAFETY LOCK violations (non-fatal in ALERT_ONLY):")
        for v in violations:
            print(f"   • {v}")
