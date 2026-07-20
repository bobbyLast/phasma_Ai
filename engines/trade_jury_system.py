#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Trade Jury System — multi-chamber, evidence-only arbitration.

Design goals (explicitly non-partisan):
- No “bloc voting”: chambers score independent numeric rubrics from the same signal facts.
- Hard vetoes exist only for missing/invalid trade data (not opinions, not symbol popularity).
- A composite score merges chambers with configurable weights; disagreement reduces confidence.

Chambers
---------
1) Evidence — data completeness and corroboration strength (confluence, rationale density).
2) Risk alignment — crash regime, capital fit, volatility proxy (defensive posture under stress).
3) Outcome quality — simulation POP / win-rate proxies already attached to the signal.

This module does not fetch new external data; it only interprets fields already on the Signal.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple


def _f(x: Any, default: float = 0.0) -> float:
    try:
        if x is None:
            return default
        return float(x)
    except (TypeError, ValueError):
        return default


def _clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))


@dataclass
class JuryOutcome:
    verdict: str  # APPROVE | CONDITIONAL | REJECT
    hard_veto: bool
    veto_reason: str
    evidence_score: float
    risk_score: float
    outcome_score: float
    composite: float
    reasons: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "verdict": self.verdict,
            "hard_veto": self.hard_veto,
            "veto_reason": self.veto_reason,
            "evidence_score": self.evidence_score,
            "risk_score": self.risk_score,
            "outcome_score": self.outcome_score,
            "composite": self.composite,
            "reasons": list(self.reasons),
        }


class TradeJurySystem:
    """Fact-only jury over a single Signal + lightweight runtime context."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        cfg = dict(config or {})
        weights = cfg.get("weights") or {}
        self.w_evidence = _f(weights.get("evidence"), 0.34)
        self.w_risk = _f(weights.get("risk"), 0.33)
        self.w_outcome = _f(weights.get("outcome"), 0.33)
        wsum = self.w_evidence + self.w_risk + self.w_outcome
        if wsum <= 0:
            self.w_evidence = self.w_risk = self.w_outcome = 1.0 / 3.0
        else:
            self.w_evidence /= wsum
            self.w_risk /= wsum
            self.w_outcome /= wsum

        self.approve_composite_min = _f(cfg.get("approve_composite_min"), 58.0)
        self.conditional_composite_min = _f(cfg.get("conditional_composite_min"), 44.0)
        self.chamber_pass_min = _f(cfg.get("chamber_pass_min"), 45.0)
        self.min_chambers_passing_for_approve = int(cfg.get("min_chambers_passing_for_approve", 2))
        self.max_chamber_spread = _f(cfg.get("max_chamber_spread"), 55.0)
        self.disagreement_penalty = _f(cfg.get("disagreement_penalty"), 8.0)  # points off composite
        self.conditional_size_multiplier = _f(cfg.get("conditional_size_multiplier"), 0.55)

    def evaluate(self, signal: Any, context: Optional[Dict[str, Any]] = None) -> JuryOutcome:
        ctx = dict(context or {})
        reasons: List[str] = []

        hard, veto = self._hard_veto(signal)
        if hard:
            return JuryOutcome(
                verdict="REJECT",
                hard_veto=True,
                veto_reason=veto,
                evidence_score=0.0,
                risk_score=0.0,
                outcome_score=0.0,
                composite=0.0,
                reasons=[veto],
            )

        ev = self._score_evidence(signal, reasons)
        rk = self._score_risk(signal, ctx, reasons)
        oc = self._score_outcome(signal, reasons)

        spread = max(ev, rk, oc) - min(ev, rk, oc)
        composite = self.w_evidence * ev + self.w_risk * rk + self.w_outcome * oc
        if spread > self.max_chamber_spread:
            composite -= self.disagreement_penalty
            reasons.append(
                f"Chamber disagreement spread {spread:.1f} > {self.max_chamber_spread:.1f}; "
                f"applied -{self.disagreement_penalty:.1f} composite penalty"
            )
        composite = _clamp(composite, 0.0, 100.0)

        passing = sum(1 for s in (ev, rk, oc) if s >= self.chamber_pass_min)

        if composite >= self.approve_composite_min and passing >= self.min_chambers_passing_for_approve:
            verdict = "APPROVE"
            reasons.append(
                f"APPROVE composite={composite:.1f} (ev={ev:.1f}, risk={rk:.1f}, out={oc:.1f}; "
                f"{passing}/3 chambers >= {self.chamber_pass_min:.0f})"
            )
        elif composite >= self.conditional_composite_min:
            verdict = "CONDITIONAL"
            reasons.append(
                f"CONDITIONAL composite={composite:.1f} (ev={ev:.1f}, risk={rk:.1f}, out={oc:.1f}; "
                f"{passing}/3 chambers >= {self.chamber_pass_min:.0f})"
            )
        else:
            verdict = "REJECT"
            reasons.append(
                f"REJECT composite={composite:.1f} below conditional floor "
                f"{self.conditional_composite_min:.1f}"
            )

        return JuryOutcome(
            verdict=verdict,
            hard_veto=False,
            veto_reason="",
            evidence_score=ev,
            risk_score=rk,
            outcome_score=oc,
            composite=composite,
            reasons=reasons,
        )

    def _hard_veto(self, signal: Any) -> Tuple[bool, str]:
        sym = str(getattr(signal, "symbol", "") or "").strip().upper()
        if not sym or sym == "UNKNOWN":
            return True, "Hard veto: missing or UNKNOWN symbol"

        trade_type = str(getattr(signal, "trade_type", "") or "").upper()
        if trade_type == "KALSHI_PREDICTION":
            try:
                psz = _f(getattr(signal, "position_size", 0), 0.0)
            except Exception:
                psz = 0.0
            if psz <= 0:
                return True, "Hard veto: Kalshi signal has non-positive position_size"
            if not sym.startswith("KX"):
                return True, "Hard veto: Kalshi ticker missing KX prefix"
            return False, ""

        # Stocks / default: require a positive price if the field exists; if absent, do not veto
        price = getattr(signal, "current_price", None)
        if price is not None:
            p = _f(price, 0.0)
            if p <= 0:
                return True, "Hard veto: non-positive current_price on equity signal"

        return False, ""

    def _score_evidence(self, signal: Any, reasons: List[str]) -> float:
        score = 35.0
        rationale = str(getattr(signal, "rationale", "") or "").strip()
        if len(rationale) >= 40:
            score += 12.0
        elif len(rationale) >= 12:
            score += 6.0
        else:
            reasons.append("Evidence: short rationale")

        src = str(getattr(signal, "source", "") or "").strip()
        if src:
            score += 6.0

        conf = _clamp(_f(getattr(signal, "confidence", 0), 0.0), 0.0, 1.0)
        score += 20.0 * conf

        cscore = getattr(signal, "confluence_score", None)
        if cscore is not None:
            score += 15.0 * _clamp(_f(cscore, 0.0), 0.0, 1.0)
            reasons.append(f"Evidence: confluence_score={_f(cscore, 0.0):.2f}")

        intel_raw = getattr(signal, "intelligence_strength", None)
        if intel_raw is not None:
            score += 10.0 * _clamp(_f(intel_raw, 0.0) / 100.0, 0.0, 1.0)

        pc = getattr(signal, "prediction_context", None)
        if isinstance(pc, dict):
            skills = pc.get("skills_tags") or []
            if len(skills) >= 3:
                score += 8.0
                reasons.append(f"Evidence: {len(skills)} prediction skills corroborate ({', '.join(skills[:4])})")
            elif len(skills) >= 2:
                score += 4.0
            catalyst = pc.get("catalyst") if isinstance(pc.get("catalyst"), dict) else {}
            if catalyst.get("title"):
                score += 3.0

        lp = getattr(signal, "llm_prediction", None)
        if isinstance(lp, dict):
            ps = _f(lp.get("prediction_score"), 0.0)
            if ps >= 55:
                score += 10.0
                reasons.append(f"Evidence: LLM prediction score {ps:.0f}/100 ({lp.get('verdict')})")
            elif ps >= 42:
                score += 4.0
            gs = lp.get("grounding_status")
            if gs in ("ok", "ok_web") and lp.get("grounding_snippets"):
                score += 3.0

        return _clamp(score, 0.0, 100.0)

    def _score_risk(self, signal: Any, ctx: Dict[str, Any], reasons: List[str]) -> float:
        score = 55.0
        alert = int(ctx.get("crash_alert_level", 0) or 0)
        if alert >= 3:
            score -= 30.0
            reasons.append("Risk: crash_alert_level>=3 (defensive)")
        elif alert == 2:
            score -= 15.0
            reasons.append("Risk: crash_alert_level==2")
        elif alert == 1:
            score -= 7.0

        cap = _f(ctx.get("available_capital"), 0.0)
        price = _f(getattr(signal, "current_price", 0), 0.0)
        psz = _f(getattr(signal, "position_size", 0), 0.0)
        if cap > 0 and price > 0 and psz > 0:
            notional = price * psz
            util = notional / cap
            if util > 0.25:
                score -= 20.0
                reasons.append(f"Risk: high notional vs capital util={util:.2%}")
            elif util > 0.12:
                score -= 10.0
                reasons.append(f"Risk: elevated util={util:.2%}")

        vol = getattr(signal, "volatility", None)
        if vol is not None:
            vv = _f(vol, 0.0)
            if vv >= 0.8:
                score -= 10.0
                reasons.append(f"Risk: high volatility={vv:.2f}")

        return _clamp(score, 0.0, 100.0)

    def _score_outcome(self, signal: Any, reasons: List[str]) -> float:
        score = 40.0

        pop = getattr(signal, "pop_from_sim", None)
        if pop is None:
            pop = _f(getattr(signal, "confidence", 0), 0.0) * 100.0
        pop = _f(pop, 0.0)
        if pop > 1.5:
            score += 0.35 * _clamp(pop, 0.0, 100.0)
        else:
            score += 100.0 * _clamp(pop, 0.0, 1.0) * 0.35

        lp = getattr(signal, "llm_prediction", None)
        if isinstance(lp, dict):
            ps = _f(lp.get("prediction_score"), 0.0)
            score += 0.2 * _clamp(ps, 0.0, 100.0)
            if lp.get("verdict") == "BEARISH" and ps < 40:
                score -= 8.0
                reasons.append(f"Outcome: bearish LLM prediction {ps:.0f}/100")
            elif lp.get("verdict") == "BULLISH" and ps >= 55:
                reasons.append(f"Outcome: bullish LLM prediction {ps:.0f}/100")

        sim = getattr(signal, "simulation_results", None) or {}
        if isinstance(sim, dict):
            wr_raw = sim.get("win_rate")
            if wr_raw is not None:
                wr = _f(wr_raw, 0.0)
                if wr <= 1.0:
                    score += 25.0 * _clamp(wr, 0.0, 1.0)
                else:
                    score += 25.0 * _clamp(wr / 100.0, 0.0, 1.0)
                reasons.append(f"Outcome: sim win_rate present ({wr})")

            p10 = sim.get("percentile_10")
            if p10 is not None:
                reasons.append("Outcome: sim distribution includes percentile_10")

        ps = getattr(signal, "pro_pop_score", None)
        if ps is not None:
            score += 10.0 * _clamp(_f(ps, 0.0) / 100.0, 0.0, 1.0)

        return _clamp(score, 0.0, 100.0)

    @staticmethod
    def apply_conditional_sizing(signal: Any, jury: JuryOutcome, multiplier: float) -> None:
        if jury.verdict != "CONDITIONAL":
            return
        try:
            psz = _f(getattr(signal, "position_size", 0), 0.0)
            if psz > 0:
                setattr(signal, "position_size", max(1.0, psz * multiplier))
        except Exception:
            pass
