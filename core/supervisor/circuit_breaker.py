"""Circuit breaker — quarantine workers after repeated identical failures."""

from __future__ import annotations

import hashlib
import json
import logging
import os
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

from core.runtime_paths import runtime_path

logger = logging.getLogger(__name__)

DEFAULT_FAILURE_THRESHOLD = 3
DEFAULT_QUARANTINE_MINUTES = 30


def hash_error(error: BaseException) -> str:
    msg = f"{type(error).__name__}:{error}"
    return hashlib.sha256(msg.encode("utf-8")).hexdigest()[:16]


@dataclass
class WorkerHealthState:
    worker_name: str
    status: str = "OK"
    fail_count: int = 0
    consecutive_failures: int = 0
    last_error_type: Optional[str] = None
    last_error_message: Optional[str] = None
    last_error_hash: Optional[str] = None
    repeated_error_hash: Optional[str] = None
    repeated_error_count: int = 0
    last_success_at: Optional[str] = None
    last_failure_at: Optional[str] = None
    next_retry_at: Optional[str] = None
    quarantine_count: int = 0
    quarantine_minutes: int = DEFAULT_QUARANTINE_MINUTES
    metadata: Dict[str, Any] = field(default_factory=dict)


class CircuitBreaker:
    """Track per-worker failures and apply quarantine/backoff."""

    def __init__(
        self,
        *,
        failure_threshold: int = DEFAULT_FAILURE_THRESHOLD,
        quarantine_minutes: int = DEFAULT_QUARANTINE_MINUTES,
        health_path: Optional[str] = None,
    ):
        self.failure_threshold = failure_threshold
        self.quarantine_minutes = quarantine_minutes
        self.health_path = health_path or runtime_path("workers", "health.json")
        self._states: Dict[str, WorkerHealthState] = {}
        self._load()

    def get_state(self, worker_name: str) -> WorkerHealthState:
        if worker_name not in self._states:
            self._states[worker_name] = WorkerHealthState(worker_name=worker_name)
        return self._states[worker_name]

    def is_quarantined(self, worker_name: str, *, now: Optional[datetime] = None) -> bool:
        state = self.get_state(worker_name)
        if state.status != "QUARANTINED" or not state.next_retry_at:
            return False
        now = now or datetime.now(timezone.utc)
        retry_at = datetime.fromisoformat(state.next_retry_at.replace("Z", "+00:00"))
        if retry_at.tzinfo is None:
            retry_at = retry_at.replace(tzinfo=timezone.utc)
        if now >= retry_at:
            state.status = "DEGRADED"
            state.next_retry_at = None
            self._save()
            return False
        return True

    def record_success(self, worker_name: str) -> None:
        state = self.get_state(worker_name)
        state.status = "OK"
        state.fail_count = 0
        state.consecutive_failures = 0
        state.repeated_error_count = 0
        state.repeated_error_hash = None
        state.next_retry_at = None
        state.last_success_at = datetime.now(timezone.utc).isoformat()
        self._save()

    def clear_quarantine(self, worker_name: str, *, reason: str = "") -> bool:
        """Clear quarantine after verified recovery; preserve failure history fields."""
        state = self.get_state(worker_name)
        if state.status != "QUARANTINED" and not state.next_retry_at:
            return False
        state.status = "OK"
        state.next_retry_at = None
        state.consecutive_failures = 0
        state.repeated_error_count = 0
        state.repeated_error_hash = None
        if reason:
            state.metadata = dict(state.metadata or {})
            state.metadata["last_quarantine_clear_reason"] = reason
            state.metadata["last_quarantine_cleared_at"] = datetime.now(timezone.utc).isoformat()
        self._save()
        logger.info("Cleared quarantine for %s: %s", worker_name, reason or "manual reset")
        return True

    def record_failure(
        self,
        worker_name: str,
        error: BaseException,
    ) -> Optional[str]:
        """Record failure; return quarantine log message if worker was quarantined."""
        state = self.get_state(worker_name)
        err_hash = hash_error(error)
        now = datetime.now(timezone.utc)

        state.fail_count += 1
        state.consecutive_failures += 1
        state.last_error_type = type(error).__name__
        state.last_error_message = str(error)
        state.last_error_hash = err_hash
        state.last_failure_at = now.isoformat()

        if state.repeated_error_hash == err_hash:
            state.repeated_error_count += 1
        else:
            state.repeated_error_hash = err_hash
            state.repeated_error_count = 1

        quarantine_msg = None
        if state.repeated_error_count >= self.failure_threshold:
            state.quarantine_count += 1
            minutes = self.quarantine_minutes * (2 ** min(state.quarantine_count - 1, 3))
            retry_at = now + timedelta(minutes=minutes)
            state.status = "QUARANTINED"
            state.next_retry_at = retry_at.isoformat()
            quarantine_msg = (
                f"{worker_name} quarantined for {minutes}m after "
                f"{state.repeated_error_count} repeated failures: "
                f"{state.last_error_type} {state.last_error_message}"
            )
            logger.warning(quarantine_msg)
        else:
            state.status = "ERROR"

        self._save()
        return quarantine_msg

    def all_states(self) -> Dict[str, WorkerHealthState]:
        return dict(self._states)

    def quarantined_workers(self) -> Dict[str, WorkerHealthState]:
        return {
            name: state
            for name, state in self._states.items()
            if state.status == "QUARANTINED"
        }

    def _load(self) -> None:
        if not os.path.exists(self.health_path):
            return
        try:
            with open(self.health_path, "r", encoding="utf-8") as f:
                raw = json.load(f)
            for name, payload in (raw or {}).items():
                self._states[name] = WorkerHealthState(worker_name=name, **payload)
        except (json.JSONDecodeError, OSError, TypeError):
            logger.warning("Could not load worker health from %s", self.health_path)

    def _save(self) -> None:
        os.makedirs(os.path.dirname(self.health_path) or ".", exist_ok=True)
        payload = {
            name: {
                "status": s.status,
                "fail_count": s.fail_count,
                "consecutive_failures": s.consecutive_failures,
                "last_error_type": s.last_error_type,
                "last_error_message": s.last_error_message,
                "last_error_hash": s.last_error_hash,
                "repeated_error_hash": s.repeated_error_hash,
                "repeated_error_count": s.repeated_error_count,
                "last_success_at": s.last_success_at,
                "last_failure_at": s.last_failure_at,
                "next_retry_at": s.next_retry_at,
                "quarantine_count": s.quarantine_count,
                "quarantine_minutes": s.quarantine_minutes,
                "metadata": s.metadata,
            }
            for name, s in self._states.items()
        }
        with open(self.health_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
