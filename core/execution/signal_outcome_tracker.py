"""Persist approved signal snapshots for later outcome grading."""

from __future__ import annotations

import json
import os
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from core.runtime_paths import runtime_path


class SignalOutcomeTracker:
    """Storage for signal outcome grading (1h, EOD, 1D, 3D, 5D, MFE/MAE)."""

    HORIZONS = ("1h", "eod", "1d", "3d", "5d")

    def __init__(self, storage_file: Optional[str] = None):
        self.storage_file = storage_file or runtime_path("outcomes", "signals.json")
        self._records: List[Dict[str, Any]] = self._load()

    def _load(self) -> List[Dict[str, Any]]:
        if os.path.exists(self.storage_file):
            try:
                with open(self.storage_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                return data if isinstance(data, list) else []
            except (json.JSONDecodeError, OSError):
                return []
        return []

    def _save(self) -> None:
        os.makedirs(os.path.dirname(self.storage_file) or ".", exist_ok=True)
        with open(self.storage_file, "w", encoding="utf-8") as f:
            json.dump(self._records, f, indent=2)

    def _empty_horizon_grades(self) -> Dict[str, Any]:
        return {h: None for h in self.HORIZONS}

    def record_approved_signal(
        self,
        signal: Dict[str, Any],
        *,
        execution_mode: str,
        execution_decision: str,
        alerted_only: bool = False,
        paper_traded: bool = False,
    ) -> str:
        return self.record_signal(
            signal,
            {
                "execution_mode": execution_mode,
                "execution_decision": execution_decision,
                "execution_reason": execution_decision,
            },
            alerted_only=alerted_only,
            executed=paper_traded,
        )

    def record_signal(
        self,
        signal: Dict[str, Any],
        execution: Dict[str, Any],
        *,
        alerted_only: bool = False,
        executed: bool = False,
    ) -> str:
        record_id = str(uuid.uuid4())
        entry_price = signal.get("entry_price") or signal.get("current_price")
        confidence = signal.get("confidence")
        if isinstance(confidence, (int, float)) and confidence <= 1:
            confidence_pct = float(confidence) * 100.0
        else:
            try:
                confidence_pct = float(confidence) if confidence is not None else None
            except (TypeError, ValueError):
                confidence_pct = None

        record = {
            "id": record_id,
            "timestamp": datetime.now().isoformat(),
            "ticker": signal.get("symbol"),
            "side": signal.get("action"),
            "entry_reference_price": entry_price,
            "confidence": confidence_pct,
            "score_components": {
                "pop_from_sim": signal.get("pop_from_sim"),
                "monte_carlo_sim_score": signal.get("monte_carlo_sim_score"),
                "simulation_pop": signal.get("simulation_pop"),
                "pattern_strength": signal.get("pattern_strength"),
                "divergence_score": signal.get("divergence_score"),
                "win_rate": signal.get("win_rate"),
            },
            "source_type": signal.get("source"),
            "strategy": signal.get("strategy"),
            "market_regime": signal.get("market_regime"),
            "execution_mode": execution.get("execution_mode"),
            "execution_decision": execution.get("execution_decision"),
            "execution_reason": execution.get("execution_reason"),
            "alerted_only": alerted_only,
            "paper_traded": executed,
            "signal_snapshot": dict(signal),
            "grading": {
                "horizons": self._empty_horizon_grades(),
                "mfe": None,
                "mae": None,
                "final_outcome": None,
                "was_direction_correct": None,
                "was_timing_good": None,
            },
        }
        self._records.append(record)
        if len(self._records) > 5000:
            self._records = self._records[-5000:]
        self._save()
        return record_id

    def get_all_records(self) -> List[Dict[str, Any]]:
        return list(self._records)

    def get_record(self, record_id: str) -> Optional[Dict[str, Any]]:
        for record in self._records:
            if record.get("id") == record_id:
                return record
        return None

    def update_record(self, record_id: str, updates: Dict[str, Any]) -> bool:
        for record in self._records:
            if record.get("id") == record_id:
                record.update(updates)
                self._save()
                return True
        return False

    def get_pending_grading(self) -> List[Dict[str, Any]]:
        pending = []
        for record in self._records:
            horizons = (record.get("grading") or {}).get("horizons") or {}
            if any(horizons.get(h) is None for h in self.HORIZONS):
                pending.append(record)
        return pending
