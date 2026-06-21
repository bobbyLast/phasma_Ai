"""Single source of truth for signal approval state."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

from utils.confidence_utils import normalize_confidence_to_pct


class DecisionStatus(str, Enum):
    RAW_CANDIDATE = "RAW_CANDIDATE"
    ENRICHED = "ENRICHED"
    WATCHLIST_ONLY = "WATCHLIST_ONLY"
    CONDITIONAL = "CONDITIONAL"
    REJECTED = "REJECTED"
    APPROVED_ALERT_ONLY = "APPROVED_ALERT_ONLY"
    APPROVED_PAPER_ELIGIBLE = "APPROVED_PAPER_ELIGIBLE"
    EXECUTION_SKIPPED = "EXECUTION_SKIPPED"
    EXECUTION_SUBMITTED = "EXECUTION_SUBMITTED"
    EXECUTION_FILLED = "EXECUTION_FILLED"


FINAL_APPROVED_STATUSES = frozenset({
    DecisionStatus.APPROVED_ALERT_ONLY,
    DecisionStatus.APPROVED_PAPER_ELIGIBLE,
    DecisionStatus.EXECUTION_SKIPPED,
    DecisionStatus.EXECUTION_SUBMITTED,
    DecisionStatus.EXECUTION_FILLED,
})

EXECUTION_ELIGIBLE_STATUSES = frozenset({
    DecisionStatus.APPROVED_PAPER_ELIGIBLE,
    DecisionStatus.EXECUTION_SUBMITTED,
    DecisionStatus.EXECUTION_FILLED,
})


@dataclass
class SignalDecision:
    signal_id: str
    symbol: str
    asset_type: str = "STOCK"
    source: str = ""
    strategy: str = ""
    status: DecisionStatus = DecisionStatus.RAW_CANDIDATE
    current_price: Optional[float] = None
    position_size: float = 0.0
    confidence_pct: Optional[float] = None
    pop_pct: Optional[float] = None
    sim_win_rate_pct: Optional[float] = None
    gates_passed: List[str] = field(default_factory=list)
    gates_failed: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    reject_reason: str = ""
    can_alert: bool = False
    can_paper_trade: bool = False
    can_live_trade: bool = False
    execution_mode: str = "ALERT_ONLY"
    final_decision_reason: str = ""
    raw_signal: Any = None

    @classmethod
    def from_signal(cls, signal: Any, *, execution_mode: str = "ALERT_ONLY") -> "SignalDecision":
        sym = str(getattr(signal, "symbol", None) or signal.get("symbol", "") if isinstance(signal, dict) else "")
        source = getattr(signal, "source", None) or (signal.get("source") if isinstance(signal, dict) else "")
        strategy = getattr(signal, "strategy", None) or (signal.get("strategy") if isinstance(signal, dict) else "")
        price = getattr(signal, "current_price", None)
        if price is None and isinstance(signal, dict):
            price = signal.get("current_price") or signal.get("entry_price")
        pos = getattr(signal, "position_size", None)
        if pos is None and isinstance(signal, dict):
            pos = signal.get("position_size", 0)
        conf = getattr(signal, "confidence", None)
        if conf is None and isinstance(signal, dict):
            conf = signal.get("confidence")
        pop = getattr(signal, "pop_from_sim", None)
        if pop is None and isinstance(signal, dict):
            pop = signal.get("pop_from_sim")
        if pop is None:
            pop = getattr(signal, "pop", None)
        if pop is None and isinstance(signal, dict):
            pop = signal.get("pop")
        sim_wr = getattr(signal, "sim_win_rate", None)
        if sim_wr is None and isinstance(signal, dict):
            sim_wr = signal.get("sim_win_rate")
        trade_type = getattr(signal, "trade_type", None) or (signal.get("trade_type") if isinstance(signal, dict) else "STOCK")

        return cls(
            signal_id=str(getattr(signal, "signal_id", None) or uuid.uuid4().hex[:12]),
            symbol=sym.upper(),
            asset_type=str(trade_type or "STOCK").upper(),
            source=str(source or ""),
            strategy=str(strategy or ""),
            status=DecisionStatus.RAW_CANDIDATE,
            current_price=float(price) if price is not None else None,
            position_size=float(pos or 0),
            confidence_pct=normalize_confidence_to_pct(conf) if conf is not None else None,
            pop_pct=normalize_confidence_to_pct(pop) if pop is not None else None,
            sim_win_rate_pct=normalize_confidence_to_pct(sim_wr) if sim_wr is not None else None,
            execution_mode=execution_mode,
            raw_signal=signal,
        )

    def pass_gate(self, name: str) -> None:
        if name not in self.gates_passed:
            self.gates_passed.append(name)

    def fail_gate(self, name: str, reason: str) -> None:
        if name not in self.gates_failed:
            self.gates_failed.append(name)
        if reason and reason not in self.warnings:
            self.warnings.append(reason)

    def set_status(self, status: DecisionStatus, reason: str = "") -> None:
        self.status = status
        if reason:
            self.final_decision_reason = reason

    def is_final_approved(self) -> bool:
        return self.status in FINAL_APPROVED_STATUSES

    def is_execution_eligible(self) -> bool:
        return self.status in EXECUTION_ELIGIBLE_STATUSES and self.execution_mode == "PAPER_ALPACA"

    def summary_line(self) -> str:
        prefix = {
            DecisionStatus.REJECTED: "❌ REJECTED",
            DecisionStatus.WATCHLIST_ONLY: "⚠️ WATCHLIST_ONLY",
            DecisionStatus.CONDITIONAL: "⚠️ CONDITIONAL",
            DecisionStatus.APPROVED_ALERT_ONLY: "✅ ALERT_APPROVED",
            DecisionStatus.APPROVED_PAPER_ELIGIBLE: "✅ PAPER_ELIGIBLE",
            DecisionStatus.EXECUTION_SKIPPED: "⏭️ EXECUTION_SKIPPED",
        }.get(self.status, f"• {self.status.value}")
        reason = self.final_decision_reason or self.reject_reason or "; ".join(self.warnings[:2])
        conf = f"{self.confidence_pct:.1f}%" if self.confidence_pct is not None else "N/A"
        return f"{prefix}: {self.symbol} ({conf}) — {reason}" if reason else f"{prefix}: {self.symbol} ({conf})"

    def apply_to_signal(self) -> None:
        sig = self.raw_signal
        if sig is None:
            return
        attrs = {
            "decision_status": self.status.value,
            "can_alert": self.can_alert,
            "can_paper_trade": self.can_paper_trade,
            "strategy": self.strategy,
            "signal_id": self.signal_id,
        }
        for key, val in attrs.items():
            if isinstance(sig, dict):
                sig[key] = val
            else:
                setattr(sig, key, val)


@dataclass
class DecisionSummary:
    raw_candidates: int = 0
    rejected: int = 0
    watchlist_only: int = 0
    conditional: int = 0
    alert_approved: int = 0
    paper_eligible: int = 0
    execution_skipped: int = 0

    def record(self, decision: SignalDecision) -> None:
        if decision.status == DecisionStatus.REJECTED:
            self.rejected += 1
        elif decision.status == DecisionStatus.WATCHLIST_ONLY:
            self.watchlist_only += 1
        elif decision.status == DecisionStatus.CONDITIONAL:
            self.conditional += 1
        elif decision.status == DecisionStatus.APPROVED_ALERT_ONLY:
            self.alert_approved += 1
        elif decision.status == DecisionStatus.APPROVED_PAPER_ELIGIBLE:
            self.paper_eligible += 1
        elif decision.status == DecisionStatus.EXECUTION_SKIPPED:
            self.execution_skipped += 1

    def format_report(self) -> str:
        lines = [
            "Decision summary:",
            f"* Raw candidates: {self.raw_candidates}",
            f"* Rejected: {self.rejected}",
            f"* Watchlist only: {self.watchlist_only}",
            f"* Conditional: {self.conditional}",
            f"* Alert approved: {self.alert_approved}",
            f"* Paper eligible: {self.paper_eligible}",
            f"* Execution skipped (ALERT_ONLY): {self.execution_skipped}",
        ]
        return "\n".join(lines)
