"""
Central directory for generated JSON, caches, and signal history (not versioned).

Legacy layout wrote many of these at the repository root or under ./phasma_core_memory/.
On first use we copy/move those into data/runtime/ so the repo root stays clean.
"""
from __future__ import annotations

import glob
import os
import shutil

_migrated: bool = False


def project_root() -> str:
    return os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def runtime_dir() -> str:
    global _migrated
    rd = os.path.join(project_root(), "data", "runtime")
    os.makedirs(rd, exist_ok=True)
    if not _migrated:
        _migrate_legacy_into_runtime(rd)
        _migrated = True
    return rd


def runtime_path(*parts: str) -> str:
    return os.path.join(runtime_dir(), *parts)


def engine_state_path(*parts: str) -> str:
    """Persistent engine state JSON (profiles, analyses, thresholds, etc.)."""
    d = os.path.join(runtime_dir(), "engine_state")
    os.makedirs(d, exist_ok=True)
    return os.path.join(d, *parts)


def memory_base_dir() -> str:
    """Same role as old ./phasma_core_memory — now under data/runtime/."""
    d = os.path.join(runtime_dir(), "phasma_core_memory")
    os.makedirs(d, exist_ok=True)
    return d


def memory_path(*parts: str) -> str:
    return os.path.join(memory_base_dir(), *parts)


def phasma_state_file() -> str:
    return runtime_path("phasma_state.json")


def logs_dir() -> str:
    """Persistent main process logs (session + latest mirror)."""
    d = os.path.join(runtime_dir(), "logs")
    os.makedirs(d, exist_ok=True)
    return d


def _migrate_legacy_into_runtime(rd: str) -> None:
    root = project_root()

    for basename in (
        "phasma_state.json",
        "trade_memory.json",
        "scenario_graph.json",
        "discovery_history.json",
    ):
        legacy = os.path.join(root, basename)
        target = os.path.join(rd, basename)
        if os.path.isfile(legacy) and not os.path.exists(target):
            try:
                shutil.copy2(legacy, target)
            except OSError:
                pass

    engine_state = os.path.join(rd, "engine_state")
    os.makedirs(engine_state, exist_ok=True)
    for basename in (
        "volatility_profiles.json",
        "range_barrier_analyses.json",
        "adaptive_threshold_performance.json",
        "macro_indicators.json",
        "macro_analyses.json",
        "microstructure_profiles.json",
        "microstructure_analyses.json",
        "corporate_patterns.json",
        "corporate_analyses.json",
        "calendar_patterns.json",
        "calendar_analyses.json",
        "earnings_patterns.json",
        "earnings_analyses.json",
        "volatility_edge_data.json",
        "volatility_edge_signals.json",
        "prediction_records.json",
        "calibration_adjustments.json",
        "scoring_history.json",
        "causal_graph.json",
        "counterfactual_scenarios.json",
        "top_10_dashboard.json",
        "mispricing_radar.json",
    ):
        legacy = os.path.join(root, basename)
        target = os.path.join(engine_state, basename)
        if os.path.isfile(legacy) and not os.path.exists(target):
            try:
                shutil.move(legacy, target)
            except OSError:
                pass

    risk_guardian_dir = os.path.join(engine_state, "risk_guardian")
    os.makedirs(risk_guardian_dir, exist_ok=True)
    legacy_guardian = os.path.join(root, "risk_guardian_state.json")
    target_guardian = os.path.join(risk_guardian_dir, "risk_guardian_state.json")
    if os.path.isfile(legacy_guardian) and not os.path.exists(target_guardian):
        try:
            shutil.move(legacy_guardian, target_guardian)
        except OSError:
            pass
    for pattern in ("emergency_kill_switch_*.json", "kill_switch_deactivation_*.json"):
        for legacy in glob.glob(os.path.join(root, pattern)):
            target = os.path.join(risk_guardian_dir, os.path.basename(legacy))
            if not os.path.exists(target):
                try:
                    shutil.move(legacy, target)
                except OSError:
                    pass

    diagnostics_scan = os.path.join(rd, "diagnostics", "multi_platform_scan")
    os.makedirs(diagnostics_scan, exist_ok=True)
    for legacy in glob.glob(os.path.join(root, "multi_platform_scan_*.json")):
        target = os.path.join(diagnostics_scan, os.path.basename(legacy))
        if not os.path.exists(target):
            try:
                shutil.move(legacy, target)
            except OSError:
                pass

    legacy_mem = os.path.join(root, "phasma_core_memory")
    new_mem = os.path.join(rd, "phasma_core_memory")
    if os.path.isdir(legacy_mem) and not os.path.exists(new_mem):
        try:
            shutil.move(legacy_mem, new_mem)
        except OSError:
            os.makedirs(new_mem, exist_ok=True)
