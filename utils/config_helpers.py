"""Safe config access for dict-like and PhasmaConfig objects."""

from __future__ import annotations

from typing import Any, Optional


def config_get(config: Any, key: str, default: Any = None) -> Any:
    """Read config value from dict-like or object-style config."""
    if config is None:
        return default
    if isinstance(config, dict):
        return config.get(key, default)
    getter = getattr(config, "get", None)
    if callable(getter):
        try:
            return getter(key, default)
        except TypeError:
            pass
    if "." in key:
        value = config
        for part in key.split("."):
            if isinstance(value, dict):
                if part not in value:
                    return default
                value = value[part]
            elif hasattr(value, part):
                value = getattr(value, part)
            else:
                return default
        return value
    return getattr(config, key, default)
