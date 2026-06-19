"""
Centralized execution router — single submission path for all trades.

Flow: Signal → data gates → risk gate → router → broker/paper → memory/state
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Set

from core.execution.data_gates import DataQualityGates, GateResult
from core.execution.execution_modes import ExecutionDecision, ExecutionMode, normalize_execution_config
from core.execution.paper_readiness_guard import PaperReadinessGuard, normalize_paper_trading_safety
from core.execution.signal_outcome_tracker import SignalOutcomeTracker
from core.execution.outcome_grader import OutcomeGrader
from utils.trade_memory import get_trade_memory

logger = logging.getLogger(__name__)


@dataclass
class ExecutionResult:
    decision: str
    reason: str
    mode: str
    symbol: str = ""
    success: bool = False
    fill: Optional[Dict[str, Any]] = None
    alert_label: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "execution_mode": self.mode,
            "execution_decision": self.decision,
            "execution_reason": self.reason,
            "symbol": self.symbol,
            "success": self.success,
            "fill": self.fill,
            "alert_label": self.alert_label,
            **self.metadata,
        }


def normalize_monte_carlo_fields(signal: Dict[str, Any]) -> Dict[str, Any]:
    """Rename MC fields to honest simulation-only labels; cap influence on confidence."""
    out = dict(signal)
    pop = out.get("pop_from_sim") or out.get("simulation_pop")
    if pop is not None:
        out["simulation_pop"] = pop
        out["monte_carlo_sim_score"] = pop
        out["assumption_based_simulation"] = True
    sim_conf = out.get("sim_scaled_confidence")
    if sim_conf is not None:
        out["monte_carlo_sim_score"] = sim_conf
    # Cap MC influence: keep heuristic confidence separate
    base_conf = out.get("confidence", 0)
    try:
        conf = float(base_conf)
        if conf > 1:
            conf /= 100.0
    except (TypeError, ValueError):
        conf = 0.0
    mc = out.get("monte_carlo_sim_score")
    if mc is not None:
        try:
            mc_val = float(mc)
            if mc_val > 1:
                mc_val /= 100.0
            # MC may contribute at most 15% of displayed confidence blend
            out["confidence_type"] = "heuristic+simulation"
            out["confidence"] = min(1.0, conf * 0.85 + mc_val * 0.15)
        except (TypeError, ValueError):
            out["confidence_type"] = "heuristic"
    else:
        out["confidence_type"] = out.get("confidence_type", "heuristic")
    return out


class ExecutionRouter:
    """Single execution path — Telegram and other callers must use this."""

    def __init__(self, system):
        self.system = system
        self.config = system.config.data if hasattr(system.config, "data") else system.config
        self.exec_cfg = normalize_execution_config(self.config)
        self.config["execution"] = self.exec_cfg
        self.config["paper_trading_safety"] = normalize_paper_trading_safety(self.config)
        self.trade_memory = get_trade_memory()
        self.gates = DataQualityGates(self.config, self.trade_memory)
        self.outcome_tracker = SignalOutcomeTracker()
        self.outcome_grader = OutcomeGrader(tracker=self.outcome_tracker)
        self.paper_guard = PaperReadinessGuard(
            trade_memory=self.trade_memory,
            outcome_tracker=self.outcome_tracker,
            outcome_grader=self.outcome_grader,
        )
        self._submitted_keys: Set[str] = set()
        self._paper_cycle_orders = 0
        self._paper_daily_orders = 0
        self._paper_daily_notional = 0.0

    @property
    def mode(self) -> str:
        return self.exec_cfg.get("mode", ExecutionMode.ALERT_ONLY)

    def _log(self, decision: str, reason: str, symbol: str = "") -> None:
        logger.info(
            "execution_mode=%s execution_decision=%s execution_reason=%s symbol=%s",
            self.mode,
            decision,
            reason,
            symbol,
        )

    def submit_signal(
        self,
        signal_dict: Dict[str, Any],
        *,
        risk_ok: bool = True,
        posted_keys: Optional[Set[str]] = None,
        skip_gates: bool = False,
    ) -> ExecutionResult:
        """Single submit point for all trade execution."""
        signal_dict = normalize_monte_carlo_fields(signal_dict)
        symbol = str(signal_dict.get("symbol") or "").upper()
        mode = self.mode

        if not risk_ok:
            self._log(ExecutionDecision.SKIPPED, "risk gate blocked", symbol)
            return self._skip("risk gate blocked", symbol, alert_label="NO TRADE — risk gate")

        if mode in (ExecutionMode.OFF, ExecutionMode.ALERT_ONLY):
            self._log(ExecutionDecision.SKIPPED, f"mode={mode}", symbol)
            self._record_outcome(signal_dict, mode, ExecutionDecision.SKIPPED, alerted_only=True)
            return ExecutionResult(
                decision=ExecutionDecision.SKIPPED,
                reason=f"mode={mode}",
                mode=mode,
                symbol=symbol,
                alert_label="NO TRADE" if mode == ExecutionMode.OFF else "ALERT ONLY",
            )

        if not skip_gates:
            gate: GateResult = self.gates.validate(signal_dict, posted_keys=posted_keys)
            if not gate.passed:
                self._log(ExecutionDecision.SKIPPED, gate.reason, symbol)
                self._record_outcome(signal_dict, mode, ExecutionDecision.SKIPPED, alerted_only=True)
                return ExecutionResult(
                    decision=ExecutionDecision.SKIPPED,
                    reason=gate.reason,
                    mode=mode,
                    symbol=symbol,
                    alert_label=gate.alert_label,
                )

        dedup_key = signal_dict.get("dedup_key") or f"{symbol}:{signal_dict.get('action', 'BUY')}"
        if dedup_key in self._submitted_keys:
            self._log(ExecutionDecision.SKIPPED, "duplicate submit in session", symbol)
            return self._skip("duplicate submit in session", symbol)

        if mode == ExecutionMode.LIVE_ALPACA:
            if not self.exec_cfg.get("allow_live_trading"):
                self._log(ExecutionDecision.REJECTED, "live trading disabled", symbol)
                return ExecutionResult(
                    decision=ExecutionDecision.REJECTED,
                    reason="live trading disabled (fail-closed)",
                    mode=mode,
                    symbol=symbol,
                    alert_label="NO TRADE — live disabled",
                )
            return self._execute_alpaca(signal_dict, live=True)

        if mode == ExecutionMode.PAPER_ALPACA:
            guard_ok, guard_failures = self.paper_guard.can_submit_paper_order(
                self.config,
                signal_dict,
                context=self._paper_guard_context(posted_keys=posted_keys),
            )
            if not guard_ok:
                reason = "; ".join(guard_failures)
                alert = f"PAPER TRADE BLOCKED — readiness guard failed: {reason}"
                self._log(ExecutionDecision.REJECTED, reason, symbol)
                self._record_outcome(
                    signal_dict,
                    mode,
                    ExecutionDecision.REJECTED,
                    alerted_only=True,
                )
                return ExecutionResult(
                    decision=ExecutionDecision.REJECTED,
                    reason=reason,
                    mode=mode,
                    symbol=symbol,
                    alert_label=alert,
                    metadata={"readiness_guard_failures": guard_failures},
                )
            return self._execute_alpaca(signal_dict, live=False)

        if mode == ExecutionMode.PAPER_INTERNAL:
            return self._execute_internal_paper(signal_dict)

        return self._skip(f"unknown mode {mode}", symbol)

    def _paper_guard_context(self, *, posted_keys: Optional[Set[str]] = None) -> Dict[str, Any]:
        trader = getattr(self.system, "alpaca_paper_trader", None)
        return {
            "alpaca_client": trader,
            "trade_memory": self.trade_memory,
            "outcome_tracker": self.outcome_tracker,
            "outcome_grader": self.outcome_grader,
            "submitted_keys": self._submitted_keys,
            "posted_keys": posted_keys or set(),
            "daily_stats": {
                "cycle_order_count": self._paper_cycle_orders,
                "daily_order_count": self._paper_daily_orders,
                "daily_notional": self._paper_daily_notional,
            },
        }

    def reset_paper_cycle_stats(self) -> None:
        """Reset per-cycle paper order counters."""
        self._paper_cycle_orders = 0

    def _record_paper_order_stats(self, signal_dict: Dict[str, Any], fill: Dict[str, Any]) -> None:
        price = fill.get("price") or signal_dict.get("current_price") or signal_dict.get("entry_price")
        quantity = fill.get("quantity") or signal_dict.get("quantity") or signal_dict.get("position_size") or 1
        try:
            notional = abs(float(price) * float(quantity))
        except (TypeError, ValueError):
            notional = 0.0
        if signal_dict.get("position_cost") is not None:
            try:
                notional = float(signal_dict["position_cost"])
            except (TypeError, ValueError):
                pass
        self._paper_cycle_orders += 1
        self._paper_daily_orders += 1
        self._paper_daily_notional += notional

    def _skip(self, reason: str, symbol: str, alert_label: str = "") -> ExecutionResult:
        return ExecutionResult(
            decision=ExecutionDecision.SKIPPED,
            reason=reason,
            mode=self.mode,
            symbol=symbol,
            alert_label=alert_label or f"NO TRADE — {reason}",
        )

    def _record_outcome(
        self,
        signal: Dict[str, Any],
        mode: str,
        decision: str,
        *,
        alerted_only: bool = False,
        paper_traded: bool = False,
    ) -> None:
        try:
            self.outcome_tracker.record_approved_signal(
                signal,
                execution_mode=mode,
                execution_decision=decision,
                alerted_only=alerted_only,
                paper_traded=paper_traded,
            )
        except Exception as exc:
            logger.warning("signal outcome record failed: %s", exc)

    def _on_fill(self, signal_dict: Dict[str, Any], fill: Dict[str, Any]) -> None:
        symbol = fill.get("symbol") or signal_dict.get("symbol", "")
        try:
            self.trade_memory.add_trade(
                symbol,
                metadata={
                    "side": signal_dict.get("action"),
                    "confidence": signal_dict.get("confidence"),
                    "execution_mode": self.mode,
                    "fill_price": fill.get("price"),
                    "quantity": fill.get("quantity"),
                    "broker_order_id": fill.get("order_id"),
                    "source": signal_dict.get("source"),
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                },
            )
        except TypeError:
            self.trade_memory.add_trade(symbol)

        s = self.system
        if hasattr(s, "daily_learning_tracker") and s.daily_learning_tracker:
            try:
                s.daily_learning_tracker.record_trade({
                    "symbol": symbol,
                    "action": signal_dict.get("action"),
                    "quantity": fill.get("quantity"),
                    "entry_price": fill.get("price"),
                    "confidence": signal_dict.get("confidence"),
                    "source": signal_dict.get("source"),
                    "execution_mode": self.mode,
                })
            except Exception:
                pass

        if hasattr(s, "alert_learning_loop") and s.alert_learning_loop:
            try:
                s.alert_learning_loop.record_alert_outcome(
                    {"symbol": symbol, **fill},
                    outcome="filled",
                    outcome_details=fill,
                )
            except Exception:
                pass

    def _execute_alpaca(self, signal_dict: Dict[str, Any], *, live: bool) -> ExecutionResult:
        symbol = str(signal_dict.get("symbol") or "").upper()
        s = self.system
        trader = getattr(s, "alpaca_paper_trader", None)
        if not trader or not getattr(trader, "alpaca", None):
            self._log(ExecutionDecision.REJECTED, "alpaca not connected", symbol)
            return ExecutionResult(
                decision=ExecutionDecision.REJECTED,
                reason="alpaca not connected",
                mode=self.mode,
                symbol=symbol,
            )

        result = s._alpaca_submit_from_signal(signal_dict, trader=trader)
        dedup_key = signal_dict.get("dedup_key") or f"{symbol}:{signal_dict.get('action', 'BUY')}"

        if result and result.get("success"):
            self._submitted_keys.add(dedup_key)
            self._record_paper_order_stats(signal_dict, result)
            decision = ExecutionDecision.FILLED if result.get("price") else ExecutionDecision.SUBMITTED
            self._log(decision, "alpaca order placed", symbol)
            self._on_fill(signal_dict, result)
            self._record_outcome(signal_dict, self.mode, decision, paper_traded=True)
            return ExecutionResult(
                decision=decision,
                reason="alpaca order placed",
                mode=self.mode,
                symbol=symbol,
                success=True,
                fill=result,
                alert_label="PAPER TRADE (Alpaca)" if not live else "LIVE TRADE",
                metadata={"platform": "Alpaca", "paper": not live},
            )

        err = (result or {}).get("error", "unknown")
        self._log(ExecutionDecision.REJECTED, err, symbol)
        return ExecutionResult(
            decision=ExecutionDecision.REJECTED,
            reason=err,
            mode=self.mode,
            symbol=symbol,
            alert_label=f"NO TRADE — {err}",
        )

    def _execute_internal_paper(self, signal_dict: Dict[str, Any]) -> ExecutionResult:
        symbol = str(signal_dict.get("symbol") or "").upper()
        s = self.system
        portfolio = getattr(s, "paper_portfolio", None)
        if not portfolio:
            self._log(ExecutionDecision.REJECTED, "internal paper not available", symbol)
            return ExecutionResult(
                decision=ExecutionDecision.REJECTED,
                reason="internal paper not available",
                mode=self.mode,
                symbol=symbol,
            )

        result = s._internal_paper_submit_from_signal(signal_dict, portfolio=portfolio)
        dedup_key = signal_dict.get("dedup_key") or f"{symbol}:{signal_dict.get('action', 'BUY')}"

        if result and result.get("success"):
            self._submitted_keys.add(dedup_key)
            self._log(ExecutionDecision.FILLED, "internal paper fill", symbol)
            self._on_fill(signal_dict, result)
            self._record_outcome(signal_dict, self.mode, ExecutionDecision.FILLED, paper_traded=True)
            return ExecutionResult(
                decision=ExecutionDecision.FILLED,
                reason="internal paper simulated fill",
                mode=self.mode,
                symbol=symbol,
                success=True,
                fill=result,
                alert_label="PAPER TRADE (internal simulation)",
                metadata={"platform": "internal_json", "paper": True},
            )

        err = (result or {}).get("error", "unknown")
        self._log(ExecutionDecision.REJECTED, err, symbol)
        return ExecutionResult(
            decision=ExecutionDecision.REJECTED,
            reason=err,
            mode=self.mode,
            symbol=symbol,
            alert_label=f"NO TRADE — {err}",
        )

    def enrich_signal_for_report(self, signal_dict: Dict[str, Any], result: ExecutionResult) -> Dict[str, Any]:
        """Attach honest execution/reporting fields for Telegram."""
        enriched = dict(signal_dict)
        enriched["execution_mode"] = result.mode
        enriched["execution_decision"] = result.decision
        enriched["execution_reason"] = result.reason
        enriched["execution_alert_label"] = result.alert_label
        enriched["data_age_seconds"] = signal_dict.get("data_age_seconds")
        enriched["price_source"] = signal_dict.get("price_source", "signal")
        enriched["kalshi_intel_only"] = bool(
            (self.config.get("kalshi_intel_only") or self.config.get("post_prediction_trades") is False)
        )
        sym = str(signal_dict.get("symbol") or "").upper()
        enriched["memory_recently_traded"] = self.trade_memory.is_recently_traded(sym)
        enriched["risk_gate"] = "passed" if result.decision != ExecutionDecision.SKIPPED or "risk" not in result.reason else "blocked"
        if result.decision in (ExecutionDecision.SKIPPED, ExecutionDecision.REJECTED):
            enriched["skip_reason"] = result.reason
        return enriched
