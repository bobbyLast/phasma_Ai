"""Automated outcome grader — track and grade approved signals without executing trades."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

from core.execution.signal_outcome_tracker import SignalOutcomeTracker

logger = logging.getLogger(__name__)

CONFIDENCE_BUCKETS: List[Tuple[str, float, float]] = [
    ("0-50", 0.0, 50.0),
    ("50-65", 50.0, 65.0),
    ("65-75", 65.0, 75.0),
    ("75-85", 75.0, 85.0),
    ("85-100", 85.0, 100.01),
]

WIN_THRESHOLD_PCT = 0.5
NEUTRAL_BAND_PCT = 0.25


def _parse_ts(value: Any) -> datetime:
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    text = str(value or "").replace("Z", "+00:00")
    dt = datetime.fromisoformat(text)
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def _normalize_side(side: Any) -> str:
    text = str(side or "BUY").upper()
    if text in ("SELL", "SHORT", "PUT", "BEARISH"):
        return "SELL"
    return "BUY"


def _signed_return_pct(entry: float, price: float, side: str) -> float:
    if entry <= 0:
        return 0.0
    raw = ((price - entry) / entry) * 100.0
    return -raw if side == "SELL" else raw


def _direction_correct(signed_return_pct: float) -> bool:
    return signed_return_pct > NEUTRAL_BAND_PCT


def _outcome_label(signed_return_pct: float) -> str:
    if signed_return_pct >= WIN_THRESHOLD_PCT:
        return "win"
    if signed_return_pct <= -WIN_THRESHOLD_PCT:
        return "loss"
    return "neutral"


def _timing_quality(signed_returns: List[float]) -> str:
    """Heuristic: how quickly the favorable move appeared in the window."""
    if not signed_returns:
        return "unknown"
    peak_idx = max(range(len(signed_returns)), key=lambda i: signed_returns[i])
    progress = peak_idx / max(len(signed_returns) - 1, 1)
    peak = signed_returns[peak_idx]
    if peak <= NEUTRAL_BAND_PCT:
        return "poor"
    if progress <= 0.25:
        return "excellent"
    if progress <= 0.5:
        return "good"
    if progress <= 0.75:
        return "fair"
    return "late"


def _horizon_due(entry_ts: datetime, horizon: str, now: datetime) -> bool:
    if horizon == "1h":
        return now >= entry_ts + timedelta(hours=1)
    if horizon == "eod":
        # Grade after US cash session close (21:00 UTC ≈ 4pm ET standard time)
        entry_day = entry_ts.astimezone(timezone.utc).date()
        close_today = datetime(
            entry_day.year, entry_day.month, entry_day.day, 21, 0, tzinfo=timezone.utc
        )
        if entry_ts > close_today:
            close_today += timedelta(days=1)
        return now >= close_today
    days = {"1d": 1, "3d": 3, "5d": 5}.get(horizon)
    if days is None:
        return False
    return now >= entry_ts + timedelta(days=days)


def _horizon_end(entry_ts: datetime, horizon: str, now: datetime) -> datetime:
    if horizon == "1h":
        return min(now, entry_ts + timedelta(hours=1))
    if horizon == "eod":
        entry_day = entry_ts.astimezone(timezone.utc).date()
        close = datetime(entry_day.year, entry_day.month, entry_day.day, 21, 0, tzinfo=timezone.utc)
        if entry_ts > close:
            close += timedelta(days=1)
        return min(now, close)
    days = {"1d": 1, "3d": 3, "5d": 5}.get(horizon, 1)
    return min(now, entry_ts + timedelta(days=days))


class OutcomeGrader:
    """Scheduler + grading logic for approved signals (alert-only and paper)."""

    def __init__(
        self,
        tracker: Optional[SignalOutcomeTracker] = None,
        price_fetcher=None,
    ):
        self.tracker = tracker or SignalOutcomeTracker()
        self._price_fetcher = price_fetcher

    @property
    def price_fetcher(self):
        if self._price_fetcher is None:
            from utils.robust_price_fetcher import get_robust_price_fetcher
            self._price_fetcher = get_robust_price_fetcher()
        return self._price_fetcher

    def record_signal(
        self,
        signal: Dict[str, Any],
        *,
        execution_mode: str,
        execution_decision: str,
        alerted_only: bool = False,
        paper_traded: bool = False,
    ) -> str:
        """Store signal snapshot at alert/approval time."""
        return self.tracker.record_approved_signal(
            signal,
            execution_mode=execution_mode,
            execution_decision=execution_decision,
            alerted_only=alerted_only,
            paper_traded=paper_traded,
        )

    def _fetch_bars(self, ticker: str, start: datetime, end: datetime) -> List[Dict[str, float]]:
        try:
            import yfinance as yf

            sym = str(ticker or "").upper()
            if sym.startswith("KX"):
                return []
            data = yf.Ticker(sym).history(start=start, end=end + timedelta(minutes=5), interval="30m")
            if data is None or data.empty:
                data = yf.Ticker(sym).history(period="5d", interval="1h")
            if data is None or data.empty:
                return []
            bars = []
            for idx, row in data.iterrows():
                ts = idx.to_pydatetime()
                if ts.tzinfo is None:
                    ts = ts.replace(tzinfo=timezone.utc)
                if start <= ts <= end:
                    bars.append({
                        "ts": ts,
                        "high": float(row["High"]),
                        "low": float(row["Low"]),
                        "close": float(row["Close"]),
                    })
            return bars
        except Exception as exc:
            logger.debug("Bar fetch failed for %s: %s", ticker, exc)
            return []

    def _grade_horizon(
        self,
        record: Dict[str, Any],
        horizon: str,
        now: datetime,
    ) -> Optional[Dict[str, Any]]:
        entry_ts = _parse_ts(record.get("timestamp"))
        if not _horizon_due(entry_ts, horizon, now):
            return None

        try:
            entry = float(record.get("entry_reference_price") or 0)
        except (TypeError, ValueError):
            entry = 0.0
        if entry <= 0:
            return None

        ticker = record.get("ticker")
        side = _normalize_side(record.get("side"))
        end = _horizon_end(entry_ts, horizon, now)
        bars = self._fetch_bars(ticker, entry_ts, end)

        if bars:
            highs = [b["high"] for b in bars]
            lows = [b["low"] for b in bars]
            closes = [b["close"] for b in bars]
            final_price = closes[-1]
            if side == "BUY":
                mfe_price = max(highs)
                mae_price = min(lows)
            else:
                mfe_price = min(lows)
                mae_price = max(highs)
            mfe = _signed_return_pct(entry, mfe_price, side)
            mae = _signed_return_pct(entry, mae_price, side)
            signed_series = [_signed_return_pct(entry, c, side) for c in closes]
        else:
            final_price = self.price_fetcher.get_real_price(str(ticker))
            if final_price is None:
                return None
            mfe = mae = _signed_return_pct(entry, final_price, side)
            signed_series = [mfe]

        signed_final = _signed_return_pct(entry, final_price, side)
        return {
            "horizon": horizon,
            "graded_at": now.isoformat(),
            "entry_price": entry,
            "final_price": final_price,
            "return_pct": round(signed_final, 4),
            "mfe_pct": round(mfe, 4),
            "mae_pct": round(mae, 4),
            "direction_correct": _direction_correct(signed_final),
            "timing_quality": _timing_quality(signed_series),
            "outcome": _outcome_label(signed_final),
        }

    def grade_pending(self) -> Dict[str, int]:
        """Grade all signals whose horizons are due."""
        now = datetime.now(timezone.utc)
        stats = {"graded_horizons": 0, "records_touched": 0}

        for record in self.tracker.get_pending_grading():
            touched = False
            grading = record.setdefault("grading", {})
            horizons = grading.setdefault("horizons", {})
            for horizon in SignalOutcomeTracker.HORIZONS:
                if horizons.get(horizon) is not None:
                    continue
                result = self._grade_horizon(record, horizon, now)
                if result is None:
                    continue
                horizons[horizon] = result
                stats["graded_horizons"] += 1
                touched = True

            if touched:
                best = horizons.get("5d") or horizons.get("3d") or horizons.get("1d") or horizons.get("1h")
                if best:
                    grading["mfe"] = best.get("mfe_pct")
                    grading["mae"] = best.get("mae_pct")
                    grading["was_direction_correct"] = best.get("direction_correct")
                    grading["was_timing_good"] = best.get("timing_quality") in ("excellent", "good")
                    grading["final_outcome"] = best.get("outcome")
                stats["records_touched"] += 1

        if stats["records_touched"]:
            self.tracker._save()
        return stats

    @staticmethod
    def _confidence_bucket(confidence: Any) -> str:
        try:
            val = float(confidence)
        except (TypeError, ValueError):
            return "unknown"
        for label, low, high in CONFIDENCE_BUCKETS:
            if low <= val < high:
                return label
        return "unknown"

    def get_calibration_report(self) -> Dict[str, Any]:
        """Compare claimed confidence vs actual hit rate by bucket."""
        records = self.tracker.get_all_records()
        buckets: Dict[str, Dict[str, Any]] = {
            label: {"count": 0, "hits": 0, "returns": []} for label, _, _ in CONFIDENCE_BUCKETS
        }
        buckets["unknown"] = {"count": 0, "hits": 0, "returns": []}

        by_source: Dict[str, Dict[str, Any]] = {}
        by_ticker: Dict[str, Dict[str, Any]] = {}
        by_strategy: Dict[str, Dict[str, Any]] = {}
        alert_only = {"count": 0, "hits": 0, "returns": []}
        paper_traded = {"count": 0, "hits": 0, "returns": []}

        for record in records:
            grading = record.get("grading") or {}
            horizons = grading.get("horizons") or {}
            grade = horizons.get("1d") or horizons.get("1h") or horizons.get("eod")
            if not grade:
                continue

            ret = grade.get("return_pct", 0.0)
            hit = bool(grade.get("direction_correct"))
            bucket = self._confidence_bucket(record.get("confidence"))
            buckets.setdefault(bucket, {"count": 0, "hits": 0, "returns": []})
            buckets[bucket]["count"] += 1
            buckets[bucket]["hits"] += int(hit)
            buckets[bucket]["returns"].append(ret)

            source = str(record.get("source_type") or "unknown")
            by_source.setdefault(source, {"count": 0, "hits": 0, "returns": []})
            by_source[source]["count"] += 1
            by_source[source]["hits"] += int(hit)
            by_source[source]["returns"].append(ret)

            ticker = str(record.get("ticker") or "unknown")
            by_ticker.setdefault(ticker, {"count": 0, "hits": 0, "returns": []})
            by_ticker[ticker]["count"] += 1
            by_ticker[ticker]["hits"] += int(hit)
            by_ticker[ticker]["returns"].append(ret)

            strategy = str(record.get("strategy") or "unknown")
            by_strategy.setdefault(strategy, {"count": 0, "hits": 0, "returns": []})
            by_strategy[strategy]["count"] += 1
            by_strategy[strategy]["hits"] += int(hit)
            by_strategy[strategy]["returns"].append(ret)

            split = alert_only if record.get("alerted_only") else paper_traded
            split["count"] += 1
            split["hits"] += int(hit)
            split["returns"].append(ret)

        def _finalize(group: Dict[str, Any]) -> Dict[str, Any]:
            count = group["count"]
            returns = group["returns"]
            return {
                "count": count,
                "hit_rate": round(group["hits"] / count, 4) if count else 0.0,
                "avg_return_pct": round(sum(returns) / len(returns), 4) if returns else 0.0,
            }

        calibration = {k: _finalize(v) for k, v in buckets.items() if v["count"]}
        ticker_rank = sorted(
            ((t, _finalize(v)) for t, v in by_ticker.items() if v["count"]),
            key=lambda x: x[1]["avg_return_pct"],
            reverse=True,
        )

        return {
            "total_graded": sum(v["count"] for v in buckets.values()),
            "by_confidence_bucket": calibration,
            "by_source_type": {k: _finalize(v) for k, v in by_source.items()},
            "by_strategy": {k: _finalize(v) for k, v in by_strategy.items()},
            "by_ticker_top": ticker_rank[:5],
            "by_ticker_bottom": ticker_rank[-5:] if len(ticker_rank) >= 5 else [],
            "alert_only": _finalize(alert_only),
            "paper_traded": _finalize(paper_traded),
        }

    def print_console_summary(self) -> None:
        """Print performance summary to console."""
        report = self.get_calibration_report()
        print("\n" + "=" * 72)
        print("OUTCOME GRADER — CALIBRATION SUMMARY")
        print("=" * 72)
        print(f"Graded signals: {report['total_graded']}")

        print("\nBy confidence bucket (count, hit rate, avg return %):")
        for bucket, stats in sorted(report.get("by_confidence_bucket", {}).items()):
            print(
                f"  {bucket:>8}: n={stats['count']:3d}  "
                f"hit={stats['hit_rate']:.1%}  avg_ret={stats['avg_return_pct']:+.2f}%"
            )

        print("\nBy source type:")
        for source, stats in report.get("by_source_type", {}).items():
            print(
                f"  {source}: n={stats['count']} hit={stats['hit_rate']:.1%} "
                f"avg_ret={stats['avg_return_pct']:+.2f}%"
            )

        print("\nBy strategy:")
        for strategy, stats in report.get("by_strategy", {}).items():
            print(
                f"  {strategy}: n={stats['count']} hit={stats['hit_rate']:.1%} "
                f"avg_ret={stats['avg_return_pct']:+.2f}%"
            )

        print("\nAlert-only vs paper-traded:")
        ao = report.get("alert_only", {})
        pt = report.get("paper_traded", {})
        print(
            f"  alert-only:   n={ao.get('count', 0)} hit={ao.get('hit_rate', 0):.1%} "
            f"avg_ret={ao.get('avg_return_pct', 0):+.2f}%"
        )
        print(
            f"  paper-traded: n={pt.get('count', 0)} hit={pt.get('hit_rate', 0):.1%} "
            f"avg_ret={pt.get('avg_return_pct', 0):+.2f}%"
        )

        if report.get("by_ticker_top"):
            print("\nTop tickers (by avg return):")
            for ticker, stats in report["by_ticker_top"]:
                print(f"  {ticker}: n={stats['count']} avg_ret={stats['avg_return_pct']:+.2f}%")
        if report.get("by_ticker_bottom"):
            print("\nBottom tickers:")
            for ticker, stats in report["by_ticker_bottom"]:
                print(f"  {ticker}: n={stats['count']} avg_ret={stats['avg_return_pct']:+.2f}%")
        print("=" * 72 + "\n")

    def multi_axis_grade(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """
        Grade event/cause/relationship/timing/probability/execution separately.

        Winning trade + bad reasoning must NOT strengthen causal rules.
        Losing trade + good thesis + bad fill must NOT weaken event model.
        """
        grading = record.get("grading") or {}
        horizons = grading.get("horizons") or {}
        best = horizons.get("1d") or horizons.get("eod") or horizons.get("1h") or {}
        pnl_outcome = best.get("outcome") or grading.get("final_outcome") or "unknown"
        direction_ok = bool(best.get("direction_correct") or grading.get("was_direction_correct"))
        timing = best.get("timing_quality") or grading.get("was_timing_good")

        thesis = record.get("thesis") or record.get("causal_hypothesis") or {}
        if isinstance(thesis, str):
            thesis = {"mechanism": thesis}
        causal_status = str(thesis.get("status") or record.get("causal_status") or "unknown")
        event_type = str(record.get("event_type") or "unknown")
        edge_valid = record.get("relationship_edge_valid")
        claimed_prob = record.get("calibrated_probability") or (record.get("forecast") or {}).get("probability")
        fill_quality = str(record.get("fill_quality") or "unknown")
        research_only = bool(record.get("research_only"))

        axes = {
            "event_detection": {
                "grade": "pass" if event_type and event_type != "unknown" else "unknown",
                "feeds_event_model": True,
                "feeds_causal_model": False,
            },
            "classification": {
                "grade": "pass" if record.get("event_scope") or event_type else "unknown",
                "feeds_event_model": True,
                "feeds_causal_model": False,
            },
            "cause": {
                # PnL win does not validate cause; require explicit postmortem or contradiction-free
                "grade": (
                    "pass" if causal_status in ("probable_primary", "confirmed") and not record.get("causal_contradicted")
                    else "fail" if record.get("causal_contradicted") or causal_status == "contradicted"
                    else "unknown"
                ),
                "feeds_event_model": False,
                "feeds_causal_model": pnl_outcome != "win" or causal_status in ("probable_primary", "confirmed"),
                "note": "win+bad_reasoning_does_not_strengthen",
            },
            "relationship": {
                "grade": "pass" if edge_valid is True else "fail" if edge_valid is False else "unknown",
                "feeds_event_model": False,
                "feeds_causal_model": False,
                "feeds_relationship_graph": edge_valid is True and not research_only,
            },
            "direction_timing": {
                "grade": "pass" if direction_ok and timing in ("excellent", "good", True) else (
                    "fail" if best else "unknown"
                ),
                "feeds_event_model": False,
                "feeds_causal_model": False,
            },
            "probability": {
                "grade": "calibrated" if claimed_prob is not None and best else "unknown",
                "claimed": claimed_prob,
                "realized_hit": direction_ok if best else None,
                "feeds_calibration": True,
            },
            "entry_execution_exit": {
                "grade": fill_quality if fill_quality != "unknown" else (
                    "pass" if pnl_outcome == "win" else "unknown"
                ),
                # Bad fill on good thesis: do not weaken event model
                "feeds_event_model": fill_quality not in ("poor", "slippage_bad"),
                "feeds_causal_model": False,
            },
            "risk_sizing": {
                "grade": "pass" if not record.get("risk_breach") else "fail",
                "feeds_event_model": False,
                "feeds_causal_model": False,
            },
            "pnl_outcome": pnl_outcome,
        }
        return axes

    def apply_learning_updates(self) -> Dict[str, Any]:
        """Push multi-axis grades into AdaptiveConfidenceThreshold with decay / champion-challenger."""
        updates = {
            "threshold_records": 0,
            "causal_updates_skipped_bad_reasoning_wins": 0,
            "calibration_samples": 0,
            "champion_challenger": None,
        }
        try:
            from engines.adaptive_confidence_threshold import AdaptiveConfidenceThreshold
            act = AdaptiveConfidenceThreshold()
        except Exception as exc:
            logger.warning("AdaptiveConfidenceThreshold unavailable: %s", exc)
            return updates

        for record in self.tracker.get_all_records():
            grading = record.get("grading") or {}
            if not grading.get("horizons"):
                continue
            axes = self.multi_axis_grade(record)
            record.setdefault("grading", {})["multi_axis"] = axes

            # Probability / PnL feed thresholds; causal only when cause axis allows
            conf = record.get("confidence")
            best = (grading.get("horizons") or {}).get("1d") or {}
            ret = float(best.get("return_pct") or 0)
            is_win = best.get("outcome") == "win" or bool(best.get("direction_correct"))
            try:
                act.record_trade_outcome(float(conf or 55), ret, bool(is_win))
                updates["threshold_records"] += 1
            except Exception:
                pass

            if axes["cause"].get("grade") == "pass" and axes["pnl_outcome"] == "loss":
                # Good thesis, bad outcome — do not punish event detection
                pass
            if axes["pnl_outcome"] == "win" and axes["cause"].get("grade") != "pass":
                updates["causal_updates_skipped_bad_reasoning_wins"] += 1

            if axes["probability"].get("feeds_calibration") and axes["probability"].get("claimed") is not None:
                updates["calibration_samples"] += 1

        # Champion/challenger: compare current vs challenger floor (+2 pts if hit rate better)
        try:
            report = self.get_calibration_report()
            hit = float((report.get("paper_traded") or {}).get("hit_rate") or 0)
            current = float(act.current_threshold)
            challenger = min(act.max_threshold, current + 2.0)
            champion = current
            if hit < 0.45:
                champion = challenger  # raise bar when underperforming
            elif hit > 0.58:
                champion = max(act.min_threshold, current - 1.0)
            updates["champion_challenger"] = {
                "current": current,
                "challenger": challenger,
                "selected": champion,
                "paper_hit_rate": hit,
            }
            if abs(champion - current) >= 0.5:
                act.current_threshold = champion
                act.save_performance_data()
                try:
                    act.update_config_threshold()
                except Exception:
                    pass
        except Exception as exc:
            logger.debug("champion/challenger skipped: %s", exc)

        try:
            self.tracker._save()
        except Exception:
            pass
        return updates
