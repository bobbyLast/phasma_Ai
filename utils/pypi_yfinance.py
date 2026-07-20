"""Load the PyPI yfinance package — not the repo-root yfinance.py shim."""

from __future__ import annotations

import os
import sys
from types import ModuleType
from typing import Optional

_CACHED: Optional[ModuleType] = None


def get_pypi_yfinance() -> Optional[ModuleType]:
    """Return installed yfinance module, bypassing local project shim."""
    global _CACHED
    if _CACHED is not None:
        return _CACHED

    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    saved_path = list(sys.path)
    saved_module = sys.modules.pop("yfinance", None)

    try:
        # Drop repo root so `import yfinance` resolves to site-packages, not ./yfinance.py
        sys.path = [
            p for p in sys.path
            if os.path.abspath(p or ".") != project_root
        ]
        import yfinance as real_yf  # noqa: WPS433 — intentional shadow bypass

        mod_file = getattr(real_yf, "__file__", "") or ""
        if project_root.lower() in mod_file.lower().replace("/", os.sep):
            return None
        _CACHED = real_yf
        return real_yf
    except Exception:
        return None
    finally:
        sys.path = saved_path
        if saved_module is not None and "yfinance" not in sys.modules:
            sys.modules["yfinance"] = saved_module


def get_pypi_ticker(symbol: str):
    yf = get_pypi_yfinance()
    if yf is None:
        return None
    return yf.Ticker(str(symbol).upper().strip())
