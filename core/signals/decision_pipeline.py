"""Honest multi-gate signal decision pipeline."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from core.signals.signal_decision import (
    DecisionStatus,
    DecisionSummary,
    SignalDecision,
)
from core.signals.strategy_router import StrategyRouter, classify_asset_type, has_option_contract_fields
from core.source_status import block_demo_geo_from_decision, block_demo_signal, is_demo_source
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
        geo_event = sig_dict.get("geopolitical_event")
        if isinstance(geo_event, dict) and block_demo_geo_from_decision(geo_event, self.config):
            decision.fail_gate("demo_firewall", "demo geopolitical event blocked from DecisionGroup")
            decision.set_status(DecisionStatus.WATCHLIST_ONLY, "demo geo — diagnostics only")
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

        # Gate: cycle context mode — empty/stale market cannot approve trades
        cycle_data = None
        try:
            cycle_data = (self.config or {}).get("_cycle_data") if isinstance(self.config, dict) else None
        except Exception:
            cycle_data = None
        ctx_mode = str(sig_dict.get("context_mode") or "")
        if not ctx_mode and cycle_data is not None:
            ctx_mode = str(getattr(cycle_data, "context_mode", "") or "")
        if ctx_mode in ("EXECUTION_BLOCKED", "STALE_CONTEXT"):
            decision.fail_gate("context_mode", f"context_mode={ctx_mode}")
            decision.set_status(DecisionStatus.WATCHLIST_ONLY, f"context {ctx_mode} — no trade approval")
            self.summary.record(decision)
            decision.apply_to_signal()
            return decision
        if ctx_mode == "DEGRADED_RESEARCH":
            decision.warnings.append("DEGRADED_RESEARCH — alerts only")
            decision.can_paper_trade = False
        # Empty market snapshot / prices block stock paper eligibility
        try:
            px = float(decision.current_price or 0)
        except (TypeError, ValueError):
            px = 0.0
        if px <= 0 and decision.asset_type == "STOCK":
            decision.fail_gate("context_mode", "missing market price")
            decision.set_status(DecisionStatus.REJECTED, "missing market price")
            self.summary.record(decision)
            decision.apply_to_signal()
            return decision
        decision.pass_gate("context_mode")

        # Gate: stock minimum 5:1 reward-to-risk
        from utils.stock_reward_risk import apply_stock_rr_targets, passes_stock_rr_gate
        if isinstance(signal, dict):
            apply_stock_rr_targets(signal, config=self.config, invent_target=False)
        elif hasattr(signal, "__dict__"):
            apply_stock_rr_targets(vars(signal), config=self.config, invent_target=False)
        rr_ok, rr_reason = passes_stock_rr_gate(
            signal if isinstance(signal, dict) else sig_dict,
            config=self.config,
        )
        if not rr_ok:
            decision.fail_gate("reward_risk", rr_reason)
            decision.set_status(DecisionStatus.WATCHLIST_ONLY, f"R:R gate — {rr_reason}")
            self.summary.record(decision)
            decision.apply_to_signal()
            return decision
        decision.pass_gate("reward_risk")
        decision.warnings.append(f"reward:risk {rr_reason}")

        # Gate: forecast contract (horizon + calibrated probability)
        from utils.forecast_contract import (
            apply_forecast_to_signal,
            apply_freshness_to_day_trade_confidence,
            forecast_gate_ok,
        )
        from utils.pattern_families import attach_pattern_features

        work = signal if isinstance(signal, dict) else sig_dict
        if isinstance(signal, dict):
            apply_freshness_to_day_trade_confidence(signal)
            attach_pattern_features(signal)
            apply_forecast_to_signal(signal)
        else:
            apply_freshness_to_day_trade_confidence(work)
            attach_pattern_features(work)
            apply_forecast_to_signal(work)

        if work.get("day_trade_blocked_by_freshness"):
            decision.fail_gate("freshness", "BACKGROUND/STALE cannot inflate day-trade confidence")
            decision.set_status(DecisionStatus.WATCHLIST_ONLY, "freshness blocks day-trade")
            self.summary.record(decision)
            decision.apply_to_signal()
            return decision
        decision.pass_gate("freshness")

        if decision.asset_type == "STOCK":
            fok, freason = forecast_gate_ok(work, require_probability=True)
            if not fok:
                decision.fail_gate("forecast", freason)
                decision.set_status(DecisionStatus.WATCHLIST_ONLY, f"forecast — {freason}")
                self.summary.record(decision)
                decision.apply_to_signal()
                return decision
        decision.pass_gate("forecast")

        # Gate: regime compatibility (soft — watchlist when incompatible)
        regime = str(work.get("market_regime") or work.get("regime") or "")
        if not regime:
            try:
                from engines.market_regime import PhasmaMarketRegimeDetector
                det = PhasmaMarketRegimeDetector(self.config or {})
                regime = str(det.detect_current_regime() or "")
                if isinstance(signal, dict):
                    signal["market_regime"] = regime
            except Exception:
                regime = ""
        incompatible = set((self.config or {}).get("regime_incompatible_strategies") or [])
        if regime.lower() in ("bear", "crisis", "high_volatility") and decision.strategy in (
            "penny_moonshot", "scalp",
        ):
            decision.fail_gate("regime", f"strategy {decision.strategy} incompatible with {regime}")
            decision.set_status(DecisionStatus.WATCHLIST_ONLY, f"regime {regime}")
            self.summary.record(decision)
            decision.apply_to_signal()
            return decision
        if decision.strategy in incompatible:
            decision.fail_gate("regime", f"strategy listed incompatible: {decision.strategy}")
            decision.set_status(DecisionStatus.WATCHLIST_ONLY, "regime strategy block")
            self.summary.record(decision)
            decision.apply_to_signal()
            return decision
        decision.pass_gate("regime")

        # Gate: portfolio exposure (sector / event cluster)
        try:
            from utils.portfolio_exposure import portfolio_exposure_gate
            positions = []
            if isinstance(self.config, dict):
                positions = list(self.config.get("_open_positions") or [])
            exp_ok, exp_reason = portfolio_exposure_gate(work, open_positions=positions, config=self.config)
            if not exp_ok:
                decision.fail_gate("portfolio_exposure", exp_reason)
                decision.set_status(DecisionStatus.WATCHLIST_ONLY, f"exposure — {exp_reason}")
                self.summary.record(decision)
                decision.apply_to_signal()
                return decision
            decision.pass_gate("portfolio_exposure")
        except Exception as exp_err:
            decision.warnings.append(f"exposure check skipped: {exp_err}")

        # Related opportunities marked research_only cannot paper-trade
        if work.get("research_only"):
            decision.can_paper_trade = False
            decision.warnings.append("related opportunity research_only")

        # Microstructure: limited quotes degrade size / block aggressive
        try:
            from engines.microstructure_engine import MicrostructureEngine
            ms = MicrostructureEngine(None, None)  # type: ignore
            ms_result = ms.assess_entry_permission({
                "symbol": work.get("symbol") or work.get("ticker"),
                "bid": work.get("bid") or work.get("bid_price"),
                "ask": work.get("ask") or work.get("ask_price"),
                "spread_bps": work.get("spread_bps"),
                "capability": "limited_quote_microstructure",
            })
            if isinstance(signal, dict):
                signal["microstructure"] = ms_result
            if ms_result.get("block_aggressive") and str(work.get("entry_style") or "").lower() == "aggressive":
                decision.fail_gate("microstructure", ms_result.get("rationale") or "aggressive blocked")
                decision.set_status(DecisionStatus.WATCHLIST_ONLY, "microstructure block")
                self.summary.record(decision)
                decision.apply_to_signal()
                return decision
            decision.pass_gate("microstructure")
        except Exception:
            decision.pass_gate("microstructure")

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
