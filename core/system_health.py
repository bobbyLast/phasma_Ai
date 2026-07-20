"""Aggregate honest system health across Phasma engines."""

from __future__ import annotations

from typing import Any, Dict, List


HealthStatus = str  # OK | DEGRADED | DISABLED | NOT_CONFIGURED | ERROR | QUARANTINED

# Optional feeds that may be intentionally disabled without degrading overall health.
_INTENTIONALLY_DISABLED = frozenset({"Options Flow", "Job Scraper"})


def _status_worst(*statuses: str) -> str:
    order = {
        "ERROR": 0,
        "QUARANTINED": 1,
        "DEGRADED": 2,
        "NOT_CONFIGURED": 3,
        "DISABLED": 4,
        "OK": 5,
    }
    return min(statuses, key=lambda s: order.get(s, 99))


def _underground_status(system: Any) -> Dict[str, str]:
    ud = getattr(system, "underground_discovery", None)
    if ud is None:
        return {"status": "DISABLED", "detail": "not enabled"}
    if hasattr(ud, "get_feed_status"):
        feeds = ud.get_feed_status()
        bad = [k for k, v in feeds.items() if v not in ("OK",)]
        if bad:
            return {"status": "DEGRADED", "detail": "missing data feeds: " + ", ".join(bad)}
        return {"status": "OK", "detail": "feeds connected"}
    return {"status": "DEGRADED", "detail": "missing data feeds"}


def aggregate_system_health(system: Any) -> Dict[str, Any]:
    """Build component health map and overall status."""
    components: List[Dict[str, str]] = []

    exec_mode = getattr(getattr(system, "execution_router", None), "mode", "ALERT_ONLY")
    components.append({"name": "Execution", "status": "OK", "detail": exec_mode})

    components.append({"name": "News RSS", "status": "OK", "detail": "integrated sources"})

    ud = _underground_status(system)
    components.append({"name": "Underground Discovery", **ud})

    components.append({
        "name": "Options Flow",
        "status": "DISABLED",
        "detail": "vendor not connected",
    })
    components.append({
        "name": "Job Scraper",
        "status": "DISABLED",
        "detail": "scraper not connected",
    })

    kalshi_intel = bool(getattr(system, "config", None) and system.config.get("kalshi_intel_only", True))

    demo_allowed = False
    if getattr(system, "config", None):
        cfg = system.config.data if hasattr(system.config, "data") else {}
        from core.source_status import demo_allowed_in_pipeline
        demo_allowed = demo_allowed_in_pipeline(cfg if isinstance(cfg, dict) else {})

    components.append({
        "name": "Geopolitical",
        "status": "DEGRADED" if not demo_allowed else "OK",
        "detail": "DEMO_ONLY disabled from trade pipeline" if not demo_allowed else "live pipeline",
    })

    components.append({
        "name": "Kalshi",
        "status": "OK",
        "detail": "INTEL_ONLY" if kalshi_intel else "ENABLED",
    })

    grader = getattr(system, "outcome_grader", None)
    components.append({
        "name": "Outcome Grader",
        "status": "OK" if grader else "NOT_CONFIGURED",
        "detail": "tracking enabled" if grader else "not initialized",
    })

    supervisor = getattr(system, "worker_supervisor", None)
    if supervisor is not None and hasattr(supervisor, "quarantined_worker_names"):
        try:
            quarantined = supervisor.quarantined_worker_names() or []
        except Exception:
            quarantined = []
        if quarantined:
            components.append({
                "name": "Worker Supervisor",
                "status": "DEGRADED",
                "detail": "quarantined: " + ", ".join(quarantined),
            })

    affecting = [
        c["status"]
        for c in components
        if not (c["status"] == "DISABLED" and c["name"] in _INTENTIONALLY_DISABLED)
    ]
    overall = _status_worst(*(affecting or ["OK"]))

    return {"overall": overall, "components": components}


def format_system_health_report(health: Dict[str, Any]) -> str:
    lines = [f"SYSTEM STATUS: {health.get('overall', 'UNKNOWN')}", ""]
    for comp in health.get("components", []):
        detail = comp.get("detail", "")
        suffix = f", {detail}" if detail else ""
        lines.append(f"* {comp['name']}: {comp['status']}{suffix}")
    return "\n".join(lines)
