"""Pattern-transfer learning: winning trade setups boost similar candidates."""

from __future__ import annotations

import json
import os
import re
from typing import Any, Dict, List, Optional, Tuple

from core.runtime_paths import engine_state_path
from utils.trade_performance_ledger import get_trade_performance_ledger


def _band(value: Optional[float], edges: List[float], labels: List[str]) -> str:
    if value is None:
        return "unknown"
    try:
        v = float(value)
    except (TypeError, ValueError):
        return "unknown"
    for edge, label in zip(edges, labels):
        if v < edge:
            return label
    return labels[-1] if labels else "unknown"


def _tokens(text: str, limit: int = 8) -> List[str]:
    words = re.findall(r"[a-z]{3,}", (text or "").lower())
    stop = {"the", "and", "for", "with", "from", "that", "this", "will", "have", "been"}
    out = []
    for w in words:
        if w in stop:
            continue
        if w not in out:
            out.append(w)
        if len(out) >= limit:
            break
    return out


def extract_setup_features(row: Dict[str, Any]) -> Dict[str, Any]:
    meta = row.get("metadata") if isinstance(row.get("metadata"), dict) else {}
    conf = row.get("confidence")
    try:
        conf_f = float(conf) if conf is not None else None
        if conf_f is not None and conf_f > 1:
            conf_f /= 100.0
    except (TypeError, ValueError):
        conf_f = None
    rsi = meta.get("rsi") if meta.get("rsi") is not None else row.get("rsi")
    vol = meta.get("volume_ratio") if meta.get("volume_ratio") is not None else row.get("volume_ratio")
    chg = meta.get("change_pct") if meta.get("change_pct") is not None else row.get("change_pct")
    news = str(row.get("news_fingerprint") or row.get("title") or "")
    return {
        "sector": str(row.get("sector") or "Unknown").strip() or "Unknown",
        "industry": str(row.get("industry") or "").strip(),
        "catalyst_type": str(row.get("catalyst_type") or "Unknown").strip() or "Unknown",
        "asset_class": str(row.get("asset_class") or "STOCK").upper(),
        "hold_style": "day" if str(row.get("asset_class") or "").upper() == "DAY_TRADE" else "swing",
        "rsi_band": _band(rsi, [30, 45, 55, 70], ["oversold", "low", "mid", "high", "overbought"]),
        "vol_band": _band(vol, [1.2, 1.8, 3.0, 5.0], ["normal", "elevated", "high", "extreme", "blowoff"]),
        "move_band": _band(abs(float(chg)) if chg is not None else None, [2, 4, 8, 15], ["quiet", "modest", "strong", "hot", "parabolic"]),
        "conf_band": _band(conf_f, [0.4, 0.55, 0.7, 0.85], ["low", "mid", "solid", "high", "elite"]),
        "news_tokens": _tokens(news),
        "source": str(row.get("source") or ""),
    }


def similarity(a: Dict[str, Any], b: Dict[str, Any]) -> float:
    score = 0.0
    weight = 0.0

    def add(cond: bool, w: float) -> None:
        nonlocal score, weight
        weight += w
        if cond:
            score += w

    add(a.get("sector") == b.get("sector") and a.get("sector") not in ("", "Unknown"), 0.25)
    add(a.get("catalyst_type") == b.get("catalyst_type") and a.get("catalyst_type") not in ("", "Unknown"), 0.2)
    add(a.get("hold_style") == b.get("hold_style"), 0.1)
    add(a.get("rsi_band") == b.get("rsi_band"), 0.1)
    add(a.get("vol_band") == b.get("vol_band"), 0.15)
    add(a.get("move_band") == b.get("move_band"), 0.1)
    add(a.get("conf_band") == b.get("conf_band"), 0.05)
    toks_a = set(a.get("news_tokens") or [])
    toks_b = set(b.get("news_tokens") or [])
    if toks_a and toks_b:
        jacc = len(toks_a & toks_b) / max(1, len(toks_a | toks_b))
        score += 0.15 * jacc
        weight += 0.15
    if weight <= 0:
        return 0.0
    return score / weight


class PatternTransferLearner:
    """Boost candidates that resemble historically winning setups."""

    def __init__(self, state_path: Optional[str] = None):
        self.state_path = state_path or engine_state_path("pattern_transfer_state.json")
        self.winner_features: List[Dict[str, Any]] = []
        self._load()
        self.refresh_from_ledger()

    def _load(self) -> None:
        if not os.path.exists(self.state_path):
            return
        try:
            with open(self.state_path, "r", encoding="utf-8") as fh:
                data = json.load(fh)
            self.winner_features = list(data.get("winner_features") or [])
        except (OSError, json.JSONDecodeError):
            self.winner_features = []

    def _save(self) -> None:
        os.makedirs(os.path.dirname(self.state_path), exist_ok=True)
        try:
            with open(self.state_path, "w", encoding="utf-8") as fh:
                json.dump(
                    {"winner_features": self.winner_features[-200:], "updated": True},
                    fh,
                    indent=2,
                )
        except OSError:
            pass

    def refresh_from_ledger(self) -> int:
        ledger = get_trade_performance_ledger()
        wins = ledger.winning_setups(limit=100)
        features = [extract_setup_features(w) for w in wins]
        # Keep previously persisted + new
        merged = features + self.winner_features
        # Dedupe by sector+catalyst+vol_band+move_band
        seen = set()
        unique: List[Dict[str, Any]] = []
        for f in merged:
            key = (
                f.get("sector"),
                f.get("catalyst_type"),
                f.get("vol_band"),
                f.get("move_band"),
                f.get("hold_style"),
            )
            if key in seen:
                continue
            seen.add(key)
            unique.append(f)
        self.winner_features = unique[:200]
        self._save()
        return len(self.winner_features)

    def best_match(self, signal: Dict[str, Any]) -> Tuple[float, Optional[Dict[str, Any]]]:
        if not self.winner_features:
            return 0.0, None
        cand = extract_setup_features(signal)
        best_s = 0.0
        best_f = None
        for f in self.winner_features:
            s = similarity(cand, f)
            if s > best_s:
                best_s = s
                best_f = f
        return best_s, best_f

    def apply_boost(
        self,
        signal: Dict[str, Any],
        *,
        min_similarity: float = 0.55,
        max_boost: float = 0.12,
    ) -> Dict[str, Any]:
        """Mutate signal confidence upward when similar to a past winner. Returns signal."""
        score, match = self.best_match(signal)
        signal["pattern_similarity"] = round(score, 3)
        if match:
            signal["pattern_match"] = {
                "sector": match.get("sector"),
                "catalyst_type": match.get("catalyst_type"),
                "vol_band": match.get("vol_band"),
                "hold_style": match.get("hold_style"),
            }
        if score < min_similarity:
            signal["pattern_boost"] = 0.0
            return signal
        boost = min(max_boost, (score - min_similarity) / max(1e-6, 1.0 - min_similarity) * max_boost)
        signal["pattern_boost"] = round(boost, 4)
        conf = signal.get("confidence", 0)
        try:
            conf_f = float(conf)
        except (TypeError, ValueError):
            return signal
        if conf_f > 1:
            signal["confidence"] = min(95.0, conf_f + boost * 100.0)
        else:
            signal["confidence"] = min(0.95, conf_f + boost)
        # Soft POP nudge when present
        for key in ("pop_from_sim", "simulation_pop"):
            if signal.get(key) is not None:
                try:
                    pop = float(signal[key])
                    if pop > 1:
                        signal[key] = min(95.0, pop + boost * 100.0 * 0.5)
                    else:
                        signal[key] = min(0.95, pop + boost * 0.5)
                except (TypeError, ValueError):
                    pass
        return signal

    def apply_to_signal_object(self, signal: Any) -> Any:
        """Boost Meta-Brain Signal objects in place."""
        if isinstance(signal, dict):
            return self.apply_boost(signal)
        data = {}
        for key in (
            "symbol", "confidence", "source", "sector", "industry", "catalyst_type",
            "strategy", "trade_class", "title", "rationale", "rsi", "volume_ratio",
            "change_pct", "pop_from_sim", "simulation_pop", "asset_class",
        ):
            if hasattr(signal, key):
                data[key] = getattr(signal, key)
        boosted = self.apply_boost(data)
        if hasattr(signal, "confidence") and boosted.get("confidence") is not None:
            signal.confidence = boosted["confidence"]
        for attr in ("pattern_similarity", "pattern_boost", "pattern_match"):
            if attr in boosted:
                try:
                    setattr(signal, attr, boosted[attr])
                except Exception:
                    pass
        if boosted.get("pop_from_sim") is not None and hasattr(signal, "pop_from_sim"):
            signal.pop_from_sim = boosted["pop_from_sim"]
        return signal


_LEARNER: Optional[PatternTransferLearner] = None


def get_pattern_transfer_learner() -> PatternTransferLearner:
    global _LEARNER
    if _LEARNER is None:
        _LEARNER = PatternTransferLearner()
    return _LEARNER
