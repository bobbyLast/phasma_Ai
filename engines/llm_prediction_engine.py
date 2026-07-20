"""LLM prediction step — compact context + Brave grounding + skill fusion."""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Union

from utils.brave_llm_context import BraveLLMContextClient
from utils.prediction_context import build_llm_query, compact_signal_context

ConfigLike = Union[Dict[str, Any], Any]

_DEFAULT = {
    "enabled": True,
    "max_predictions_per_cycle": 12,
    "min_prediction_score": 42,
    "confidence_blend_weight": 0.25,
    "require_grounding_for_reject": False,
    "brave": {
        "maximum_number_of_tokens": 2048,
        "maximum_number_of_urls": 3,
        "count": 5,
        "timeout_seconds": 20,
    },
}

_BULLISH = re.compile(
    r"\b(beat|beats|surge|rally|upgrade|raised|growth|record|strong|bullish|"
    r"outperform|buy|accelerat|profit|gain|soar|jump|breakout|positive)\b",
    re.I,
)
_BEARISH = re.compile(
    r"\b(miss|misses|fall|falls|drop|downgrade|cut|weak|bearish|sell|"
    r"loss|decline|probe|investigation|lawsuit|warning|negative|crash|layoff)\b",
    re.I,
)


def llm_prediction_config(config: ConfigLike = None) -> Dict[str, Any]:
    if config is None:
        return dict(_DEFAULT)
    data = config.data if hasattr(config, "data") else config
    if not isinstance(data, dict):
        return dict(_DEFAULT)
    merged = dict(_DEFAULT)
    raw = data.get("llm_prediction") or {}
    if isinstance(raw, dict):
        merged.update(raw)
        if isinstance(raw.get("brave"), dict):
            brave = dict(merged.get("brave") or {})
            brave.update(raw["brave"])
            merged["brave"] = brave
    return merged


def _get(obj: Any, key: str, default: Any = None) -> Any:
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


def _set(obj: Any, key: str, value: Any) -> None:
    if isinstance(obj, dict):
        obj[key] = value
    else:
        try:
            setattr(obj, key, value)
        except Exception:
            pass


def _f(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def score_grounding_sentiment(snippets: List[str]) -> float:
    """Return -1..+1 sentiment from grounded snippets."""
    if not snippets:
        return 0.0
    bull = bear = 0
    for text in snippets:
        bull += len(_BULLISH.findall(text))
        bear += len(_BEARISH.findall(text))
    total = bull + bear
    if total == 0:
        return 0.0
    return max(-1.0, min(1.0, (bull - bear) / total))


def infer_prediction(
    prediction_context: Dict[str, Any],
    grounding: Dict[str, Any],
    *,
    config: ConfigLike = None,
) -> Dict[str, Any]:
    """Fuse compact skills context with Brave grounding into a prediction."""
    cfg = llm_prediction_config(config)
    pc = prediction_context or {}
    sim = pc.get("simulation") if isinstance(pc.get("simulation"), dict) else {}
    intel = pc.get("intel") if isinstance(pc.get("intel"), dict) else {}
    technical = pc.get("technical") if isinstance(pc.get("technical"), dict) else {}
    skills = list(pc.get("skills_tags") or [])

    win_rate = _f(sim.get("win_rate"), 0.0)
    if win_rate <= 1.0:
        win_rate *= 100.0
    base_conf = _f(pc.get("confidence"), 0.0)
    if base_conf <= 1.0:
        base_conf *= 100.0

    score = 0.0
    if win_rate > 0:
        score += 0.45 * win_rate
    elif base_conf > 0:
        score += 0.35 * base_conf

    intel_strength = _f(intel.get("strength"), 0.0)
    if intel_strength > 0:
        score += 0.15 * intel_strength

    div = _f(technical.get("divergence_score"), 0.0)
    if div > 0:
        score += min(12.0, div * 20.0)

    score += min(12.0, len(skills) * 3.0)

    snippets = list(grounding.get("snippets") or [])
    sentiment = score_grounding_sentiment(snippets)
    score += sentiment * 12.0

    sym = str(pc.get("symbol") or "").upper()
    catalyst = pc.get("catalyst") if isinstance(pc.get("catalyst"), dict) else {}
    title = str(catalyst.get("title") or "").lower()
    if sym and any(sym.lower() in s.lower() for s in snippets):
        score += 4.0
    if title and snippets:
        score += 2.0

    score = max(0.0, min(100.0, score))

    action = str(pc.get("action") or "BUY").upper()
    if score >= 58:
        direction = action if action in ("BUY", "SELL", "HOLD") else "BUY"
        verdict = "BULLISH" if "BUY" in direction else "BEARISH"
    elif score >= 42:
        direction = "HOLD"
        verdict = "NEUTRAL"
    else:
        direction = "SELL" if "BUY" in action else "HOLD"
        verdict = "BEARISH"

    reasons: List[str] = []
    if win_rate > 0:
        reasons.append(f"Monte Carlo win rate {win_rate:.0f}%")
    if skills:
        reasons.append(f"Skills corroborate: {', '.join(skills[:4])}")
    if snippets:
        reasons.append(
            f"Brave grounding {len(snippets)} snippet(s), sentiment {sentiment:+.2f}"
        )
    else:
        reasons.append("No Brave grounding — skills-only prediction")
    if intel_strength > 0:
        reasons.append(f"Market intel strength {intel_strength:.0f}/100")

    min_score = float(cfg.get("min_prediction_score", 42))
    hard_reject = score < min_score and grounding.get("status") in ("ok", "ok_web")

    return {
        "direction": direction,
        "verdict": verdict,
        "prediction_score": round(score, 1),
        "confidence": round(score / 100.0, 4),
        "grounding_sentiment": round(sentiment, 3),
        "grounding_snippets": snippets[:3],
        "grounding_sources": list(grounding.get("sources") or [])[:3],
        "skills_used": skills,
        "reasoning": reasons,
        "provider": "brave_context+skills" if grounding.get("provider") == "brave_context" else "brave_web+skills",
        "grounding_status": grounding.get("status"),
        "hard_reject": hard_reject,
        "query": build_llm_query(pc),
    }


class LLMPredictionEngine:
    """Run compact-context predictions with optional Brave grounding."""

    def __init__(self, config: ConfigLike = None):
        self.config = config
        self.cfg = llm_prediction_config(config)
        self.brave = BraveLLMContextClient(self.cfg)

    @property
    def enabled(self) -> bool:
        return bool(self.cfg.get("enabled", True))

    def predict(self, signal: Any) -> Optional[Dict[str, Any]]:
        if not self.enabled:
            return None

        pc = _get(signal, "prediction_context")
        if not isinstance(pc, dict) or not pc.get("symbol"):
            pc = compact_signal_context(signal, config=self.config)

        query = build_llm_query(pc)
        grounding = self.brave.fetch_grounding(query)
        result = infer_prediction(pc, grounding, config=self.config)
        result["prediction_context"] = pc
        return result

    def apply_to_signal(self, signal: Any, result: Dict[str, Any]) -> None:
        """Stamp LLM prediction fields and optionally blend confidence."""
        if not result:
            return

        _set(signal, "llm_prediction", result)
        _set(signal, "llm_prediction_score", result.get("prediction_score"))
        _set(signal, "llm_prediction_verdict", result.get("verdict"))
        _set(signal, "llm_grounding_status", result.get("grounding_status"))
        _set(signal, "confidence_type", "llm_blended")

        weight = float(self.cfg.get("confidence_blend_weight") or 0.0)
        weight = max(0.0, min(0.5, weight))
        if weight <= 0:
            return

        old_conf = _f(_get(signal, "confidence"), 0.0)
        if old_conf > 1.0:
            old_conf /= 100.0
        new_conf = _f(result.get("confidence"), 0.0)
        blended = (1.0 - weight) * old_conf + weight * new_conf
        _set(signal, "confidence", round(max(0.01, min(0.99, blended)), 4))
        _set(signal, "llm_confidence_blend", {"weight": weight, "before": old_conf, "after": blended})
