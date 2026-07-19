#!/usr/bin/env python3
"""Deprecated — use `python main.py` for 24/7 continuous mode."""

import os
import sys

_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
os.chdir(_ROOT)
main_py = os.path.join(_ROOT, "main.py")
print("Redirecting to main.py (single 24/7 entry point)...")
os.execv(sys.executable, [sys.executable, main_py, "--interval", "5"])
