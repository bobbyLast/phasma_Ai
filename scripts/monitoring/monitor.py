#!/usr/bin/env python3
"""Deprecated launcher — all 24/7 monitoring runs through main.py only."""

import os
import sys

def main() -> int:
    _here = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(_here, "..", ".."))
    os.chdir(project_root)
    main_py = os.path.join(project_root, "main.py")

    interval = "5"
    if len(sys.argv) > 1 and str(sys.argv[1]).isdigit():
        interval = str(sys.argv[1])

    print("Redirecting to main.py (single 24/7 entry point)...")
    os.execv(sys.executable, [sys.executable, main_py, "--interval", interval])
    return 0  # unreachable


if __name__ == "__main__":
    sys.exit(main())
