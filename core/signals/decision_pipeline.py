"""Honest multi-gate signal decision pipeline."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from core.signals.signal_decision import (
    DecisionStatus,
    DecisionSummary,
    SignalDecision,
)
from core.signals.strategy_router import StrategyRouter, classify_asset_type, has_option_contract_fields
from core.source_status import block_demo_signal, is_demo_source
from utils.confidence_utils import normalize_confidence_to_pct
from utils.signal_data_quality import (
    SignalDataQuality,
    assess_signal_data_quality,
    is_alert_only_eligible,
    is_paper_trade_eligible,
)


class DecisionPipeline:
    """Evaluate signals through ordered gates — single source of truth."""

    def __init__(self, config: Dict[str, Any], *, execution_mode: str = "ALERT_ONLY"):
        self.config = config
        self.execution_mode = execution_mode
        self.router = StrategyRouter()
        self.summary = DecisionSummary()

    def evaluate(
        self,
        signal: Any,
        *,
        confluence_result: Any = None,
        confluence_filtered: bool = False,
        intelligence_strength: Optional[float] = None,
        market_intel_available: bool = True,
        jury_verdict: Optional[str] = None,
        has_catalyst: bool = True,
    ) -> SignalDecision:
        decision = SignalDecision.from_signal(signal, execution_mode=self.execution_mode)
        self.summary.raw_candidates += 1

        sig_dict = signal if isinstance(signal, dict) else vars(signal) if hasattr(signal, "__dict__") else {}

        # Gate: demo firewall
        if block_demo_signal(sig_dict, self.config) or is_demo_source(decision.source):
            decision.fail_gate("demo_firewall", "demo/sample source blocked from trade pipeline")
            decision.set_status(DecisionStatus.WATCHLIST_ONLY, "demo source — diagnostics only")
            self.summary.record(decision)
            decision.apply_to_signal()
            return decision
        decision.pass_gate("demo_firewall")

        # Gate: strategy routing
        route = self.router.route(signal)
        decision.strategy = route["strategy"]
        decision.asset_type = route["asset_type"]
        if route.get("watchlist_only") and decision.strategy in ("thematic_watchlist", "social_trend_watchlist", "kalshi_intel"):
            decision.fail_gate("strategy_route", f"strategy {decision.strategy} is watchlist-only")
            decision.set_status(DecisionStatus.WATCHLIST_ONLY, f"{decision.strategy} — not trade-approved")
            self.summary.record(decision)
            decision.apply_to_signal()
            return decision
        decision.pass_gate("strategy_route")

        # Reclassify options: unusual_whales without contract fields = stock/intel
        if decision.asset_type == "OPTION" and not has_option_contract_fields(signal):
            decision.asset_type = "STOCK"
            decision.warnings.append("unusual flow source without contract fields — treated as stock/intel")

        # Gate: price / data quality (before jury)
        price = decision.current_price
        try:
            price_ok = price is not None and float(price) > 0
        except (TypeError, ValueError):
            price_ok = False
        if not price_ok:
            decision.fail_gate("price", "missing or non-positive current_price")
            decision.set_status(DecisionStatus.REJECTED, "missing or non-positive price")
            self.summary.record(decision)
            decision.apply_to_signal()
            return decision
        decision.pass_gate("price")

        quality = assess_signal_data_quality(sig_dict if isinstance(signal, dict) else _signal_to_dict(signal))
        if quality == SignalDataQuality.INVALID_COMPANY:
            decision.fail_gate("company", "invalid company identity")
            decision.set_status(DecisionStatus.REJECTED, "invalid company")
            self.summary.record(decision)
            decision.apply_to_signal()
            return decision
        if quality in (SignalDataQuality.MISSING_PRICE, SignalDataQuality.NON_POSITIVE_PRICE):
            decision.fail_gate("data_quality", quality.value)
            decision.set_status(DecisionStatus.REJECTED, quality.value)
            self.summary.record(decision)
            decision.apply_to_signal()
            return decision
        decision.pass_gate("data_quality")

        # Gate: position size
        if decision.position_size <= 0:
            decision.fail_gate("position_size", "position_size <= 0")
            decision.set_status(DecisionStatus.WATCHLIST_ONLY, "zero position size — not trade-approved")
            self.summary.record(decision)
            decision.apply_to_signal()
            return decision
        decision.pass_gate("position_size")

        # Gate: catalyst
        if not has_catalyst and decision.strategy in ("swing_news", "penny_moonshot"):
            decision.fail_gate("catalyst", "missing catalyst/news")
            decision.set_status(DecisionStatus.REJECTED, "no catalyst/news required by strategy")
            self.summary.record(decision)
            decision.apply_to_signal()
            return decision
        decision.pass_gate("catalyst")

        # Gate: confluence
        if confluence_filtered:
            decision.fail_gate("confluence", "strategy requirements not met")
            decision.set_status(DecisionStatus.WATCHLIST_ONLY, "failed confluence gate")
            self.summary.record(decision)
            decision.apply_to_signal()
            return decision

        requires_confluence = self.router.confluence_required(decision.strategy, self.config)
        if requires_confluence and confluence_result is None:
            decision.fail_gate("confluence", "no confluence data for strategy requiring confluence")
            decision.set_status(DecisionStatus.WATCHLIST_ONLY, "no confluence data")
            self.summary.record(decision)
            decision.apply_to_signal()
            return decision
        if confluence_result is not None:
            decision.pass_gate("confluence")

        # Gate: confidence floor
        conf = decision.confidence_pct or 0
        if conf < 30:
            decision.fail_gate("confidence", f"confidence {conf:.1f}% below 30% floor")
            decision.set_status(DecisionStatus.REJECTED, "confidence below floor")
            self.summary.record(decision)
            decision.apply_to_signal()
            return decision
        decision.pass_gate("confidence")

        # Gate: POP — 0% cannot BUY_NOW
        pop = decision.pop_pct
        action = str(getattr(signal, "action", None) or sig_dict.get("action", "")).upper()
        if pop is not None and pop <= 0 and "BUY" in action:
            decision.fail_gate("pop", "POP 0% — cannot recommend BUY_NOW")
            decision.set_status(DecisionStatus.WATCHLIST_ONLY, "POP 0% — low edge watchlist")
            self.summary.record(decision)
            decision.apply_to_signal()
            return decision
        if pop is not None and pop > 0:
            decision.pass_gate("pop")

        # Gate: market intel
        if not market_intel_available:
            decision.warnings.append("market intel unavailable — no default approval boost")
            if intelligence_strength is None:
                intelligence_strength = 0
        else:
            intel = intelligence_strength if intelligence_strength is not None else 50
            if intel < 30:
                decision.fail_gate("market_intel", f"intelligence {intel}/100 below threshold")
                decision.set_status(DecisionStatus.REJECTED, "market intelligence below threshold")
                self.summary.record(decision)
                decision.apply_to_signal()
                return decision
            decision.pass_gate("market_intel")

        # Gate: jury
        if jury_verdict == "REJECT":
            decision.fail_gate("jury", "jury rejected")
            decision.set_status(DecisionStatus.REJECTED, "jury rejected")
            self.summary.record(decision)
            decision.apply_to_signal()
            return decision
        if jury_verdict == "CONDITIONAL":
            decision.fail_gate("jury_final", "jury conditional — not final approval")
            decision.set_status(DecisionStatus.CONDITIONAL, "jury conditional — not final approval")
            self.summary.record(decision)
            decision.apply_to_signal()
            return decision
        if jury_verdict:
            decision.pass_gate("jury")

        # Final approval tier
        decision.can_alert = is_alert_only_eligible(quality)
        decision.can_paper_trade = is_paper_trade_eligible(quality) and self.execution_mode == "PAPER_ALPACA"
        decision.can_live_trade = False

        if quality == SignalDataQuality.PARTIAL_PRICE_ONLY:
            decision.set_status(DecisionStatus.WATCHLIST_ONLY, "partial data — volume missing")
        elif self.execution_mode == "ALERT_ONLY":
            decision.set_status(DecisionStatus.APPROVED_ALERT_ONLY, "passed required gates — alert only")
            decision.can_alert = True
        elif decision.can_paper_trade:
            decision.set_status(DecisionStatus.APPROVED_PAPER_ELIGIBLE, "passed all gates — paper eligible")
        else:
            decision.set_status(DecisionStatus.APPROVED_ALERT_ONLY, "passed gates — alert only (paper blocked)")

        self.summary.record(decision)
        decision.apply_to_signal()
        return decision

    def finalize_execution(self, decisions: List[SignalDecision]) -> None:
        for d in decisions:
            if d.status == DecisionStatus.APPROVED_ALERT_ONLY and self.execution_mode == "ALERT_ONLY":
                d.set_status(DecisionStatus.EXECUTION_SKIPPED, "ALERT_ONLY — execution skipped")
                d.can_paper_trade = False
                self.summary.execution_skipped += 1


def _signal_to_dict(signal: Any) -> Dict[str, Any]:
    if isinstance(signal, dict):
        return signal
    out = {}
    for key in dir(signal):
        if key.startswith("_"):
            continue
        val = getattr(signal, key, None)
        if callable(val):
            continue
        out[key] = val
    return out


def evaluate_batch(
    signals: List[Any],
    config: Dict[str, Any],
    *,
    execution_mode: str = "ALERT_ONLY",
    eval_kwargs: Optional[Dict[str, Any]] = None,
) -> Tuple[List[SignalDecision], List[Any], DecisionSummary]:
    """Evaluate signals; return decisions, approved signals, summary."""
    pipeline = DecisionPipeline(config, execution_mode=execution_mode)
    kwargs = eval_kwargs or {}
    approved: List[Any] = []
    decisions: List[SignalDecision] = []

    for signal in signals:
        d = pipeline.evaluate(signal, **kwargs)
        decisions.append(d)
        if d.status in (
            DecisionStatus.APPROVED_ALERT_ONLY,
            DecisionStatus.APPROVED_PAPER_ELIGIBLE,
        ):
            approved.append(signal)

    pipeline.finalize_execution(decisions)
    return decisions, approved, pipeline.summary
