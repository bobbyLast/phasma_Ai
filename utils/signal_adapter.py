"""Convert Signal, SignalDecision, or dict to a plain dict for Telegram/reporting."""

from __future__ import annotations

from typing import Any, Dict, Optional

from core.signals.signal_decision import DecisionStatus, SignalDecision


def signal_to_dict(obj: Any) -> Dict[str, Any]:
    """Normalize any signal-like object to a dict (Telegram-safe)."""
    if obj is None:
        return {}
    if isinstance(obj, dict):
        return dict(obj)
    if isinstance(obj, SignalDecision):
        return decision_to_report_dict(obj)
    if hasattr(obj, "to_dict") and callable(obj.to_dict):
        return dict(obj.to_dict())
    out: Dict[str, Any] = {}
    for key in (
        "symbol", "action", "confidence", "current_price", "entry_price",
        "position_size", "source", "strategy", "trade_type", "pop", "pop_from_sim",
        "title", "sector", "catalyst_type", "decision_status", "signal_id",
    ):
        val = getattr(obj, key, None)
        if val is not None:
            out[key] = val
    return out


def decision_to_report_dict(decision: SignalDecision) -> Dict[str, Any]:
    """Build report dict from SignalDecision."""
    base = signal_to_dict(decision.raw_signal) if decision.raw_signal else {}
    base.update({
        "symbol": decision.symbol,
        "source": decision.source,
        "strategy": decision.strategy,
        "trade_type": decision.asset_type,
        "current_price": decision.current_price,
        "entry_price": decision.current_price,
        "position_size": decision.position_size,
        "confidence": (decision.confidence_pct or 0) / 100.0 if decision.confidence_pct else 0,
        "pop_from_sim": decision.pop_pct,
        "decision_status": decision.status.value,
        "can_alert": decision.can_alert,
        "can_paper_trade": decision.can_paper_trade,
        "final_decision_reason": decision.final_decision_reason,
        "signal_id": decision.signal_id,
    })
    if decision.status == DecisionStatus.EXECUTION_SKIPPED:
        base["execution_decision"] = "skipped"
        base["execution_mode"] = decision.execution_mode
    return base


def get_symbol(obj: Any) -> str:
    d = signal_to_dict(obj)
    return str(d.get("symbol") or getattr(obj, "symbol", "") or "").upper()
