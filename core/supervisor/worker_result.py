"""Worker result types for the Phasma supervisor."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional


class WorkerStatus(str, Enum):
    OK = "OK"
    SKIPPED = "SKIPPED"
    DEGRADED = "DEGRADED"
    ERROR = "ERROR"
    QUARANTINED = "QUARANTINED"
    DISABLED = "DISABLED"


@dataclass
class WorkerResult:
    worker_name: str
    status: WorkerStatus
    started_at: str
    finished_at: str
    duration_seconds: float = 0.0
    error_type: Optional[str] = None
    error_message: Optional[str] = None
    error_hash: Optional[str] = None
    fail_count: int = 0
    output_snapshot_path: Optional[str] = None
    next_retry_at: Optional[str] = None
    can_continue_pipeline: bool = True
    stale_data_allowed: bool = False
    detail: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def build(
        cls,
        worker_name: str,
        status: WorkerStatus,
        *,
        started: datetime,
        error: Optional[BaseException] = None,
        error_hash: Optional[str] = None,
        fail_count: int = 0,
        can_continue_pipeline: bool = True,
        stale_data_allowed: bool = False,
        detail: str = "",
        output_snapshot_path: Optional[str] = None,
        next_retry_at: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> "WorkerResult":
        finished = datetime.now(timezone.utc)
        return cls(
            worker_name=worker_name,
            status=status,
            started_at=started.isoformat(),
            finished_at=finished.isoformat(),
            duration_seconds=max(0.0, (finished - started).total_seconds()),
            error_type=type(error).__name__ if error else None,
            error_message=str(error) if error else None,
            error_hash=error_hash,
            fail_count=fail_count,
            output_snapshot_path=output_snapshot_path,
            next_retry_at=next_retry_at,
            can_continue_pipeline=can_continue_pipeline,
            stale_data_allowed=stale_data_allowed,
            detail=detail,
            metadata=metadata or {},
        )
