"""Pytest hooks — isolate asyncio/event loop between test modules."""

from __future__ import annotations

import asyncio
import sys

import pytest


@pytest.fixture(autouse=True)
def _reset_asyncio_loop():
    """Prevent pytest-asyncio strict mode from breaking sync tests that call asyncio.run."""
    yield
    try:
        loop = asyncio.get_event_loop_policy().get_event_loop()
        if not loop.is_closed() and not loop.is_running():
            loop.close()
    except RuntimeError:
        pass
    asyncio.set_event_loop(asyncio.new_event_loop())


@pytest.fixture(autouse=True)
def _preserve_excepthook():
    """main.py import must not permanently break pytest's error reporting."""
    original = sys.excepthook
    yield
    sys.excepthook = original
