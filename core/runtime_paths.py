"""
Central directory for generated JSON, caches, and signal history (not versioned).

Legacy layout wrote many of these at the repository root or under ./phasma_core_memory/.
On first use we copy/move those into data/runtime/ so the repo root stays clean.
"""
from __future__ import annotations

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


def memory_base_dir() -> str:
    """Same role as old ./phasma_core_memory — now under data/runtime/."""
    d = os.path.join(runtime_dir(), "phasma_core_memory")
    os.makedirs(d, exist_ok=True)
    return d


def memory_path(*parts: str) -> str:
    return os.path.join(memory_base_dir(), *parts)


def phasma_state_file() -> str:
    return runtime_path("phasma_state.json")


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

    legacy_mem = os.path.join(root, "phasma_core_memory")
    new_mem = os.path.join(rd, "phasma_core_memory")
    if os.path.isdir(legacy_mem) and not os.path.exists(new_mem):
        try:
            shutil.move(legacy_mem, new_mem)
        except OSError:
            os.makedirs(new_mem, exist_ok=True)
