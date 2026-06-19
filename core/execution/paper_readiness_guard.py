"""Paper trading readiness guard — fail-closed checks before PAPER_ALPACA submit."""

from __future__ import annotations

import os
import tempfile
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from core.execution.execution_modes import ExecutionMode, normalize_execution_config
from core.execution.outcome_grader import OutcomeGrader
from core.execution.signal_outcome_tracker import SignalOutcomeTracker
from utils.trade_memory import TradeMemory, get_trade_memory

PAPER_ALPACA_URL = "https://paper-api.alpaca.markets"


def normalize_paper_trading_safety(config: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize paper_trading_safety block with safe defaults."""
    raw = dict(config.get("paper_trading_safety") or {})
    return {
        "enabled": bool(raw.get("enabled", False)),
        "max_orders_per_cycle": int(raw.get("max_orders_per_cycle", 0) or 0),
        "max_orders_per_day": int(raw.get("max_orders_per_day", 0) or 0),
        "max_notional_per_order": float(raw.get("max_notional_per_order", 0) or 0),
        "max_total_daily_notional": float(raw.get("max_total_daily_notional", 0) or 0),
        "cooldown_minutes_per_symbol": int(raw.get("cooldown_minutes_per_symbol", 0) or 0),
        "stock_only": bool(raw.get("stock_only", True)),
        "block_low_confidence_below": float(raw.get("block_low_confidence_below", 65)),
        "require_outcome_tracking": bool(raw.get("require_outcome_tracking", True)),
        "require_fresh_price": bool(raw.get("require_fresh_price", True)),
        "kill_switch": bool(raw.get("kill_switch", False)),
        "duplicate_protection": bool(raw.get("duplicate_protection", True)),
        "require_recently_traded_cooldown": bool(raw.get("require_recently_traded_cooldown", True)),
    }


@dataclass
class ReadinessResult:
    passed: bool
    failed_checks: List[str] = field(default_factory=list)


def _normalize_confidence_pct(confidence: Any) -> Optional[float]:
    if confidence is None:
        return None
    try:
        val = float(confidence)
    except (TypeError, ValueError):
        return None
    if val <= 1:
        val *= 100.0
    return val


def _alpaca_creds_from_env() -> Tuple[Optional[str], Optional[str], str]:
    key = os.getenv("ALPACA_API_KEY") or os.getenv("ALPACA_KEY")
    secret = os.getenv("ALPACA_API_SECRET") or os.getenv("ALPACA_SECRET_KEY")
    base = os.getenv("ALPACA_BASE_URL", PAPER_ALPACA_URL).rstrip("/")
    return key, secret, base


def _is_writable_path(path: str) -> bool:
    directory = os.path.dirname(os.path.abspath(path)) or "."
    if not os.path.isdir(directory):
        try:
            os.makedirs(directory, exist_ok=True)
        except OSError:
            return False
    if os.path.exists(path):
        return os.access(path, os.W_OK)
    try:
        fd, tmp = tempfile.mkstemp(dir=directory, prefix=".write_test_")
        os.close(fd)
        os.remove(tmp)
        return True
    except OSError:
        return False


def _estimate_notional(signal: Dict[str, Any]) -> float:
    price = signal.get("current_price") or signal.get("entry_price")
    qty = signal.get("quantity") or signal.get("shares_to_buy") or signal.get("position_size") or 1
    try:
        return float(price) * float(qty)
    except (TypeError, ValueError):
        return 0.0


class PaperReadinessGuard:
    """Validate system readiness and per-order safety before PAPER_ALPACA execution."""

    def __init__(
        self,
        *,
        trade_memory: Optional[TradeMemory] = None,
        outcome_tracker: Optional[SignalOutcomeTracker] = None,
        outcome_grader: Optional[OutcomeGrader] = None,
    ):
        self.trade_memory = trade_memory or get_trade_memory()
        self.outcome_tracker = outcome_tracker or SignalOutcomeTracker()
        self.outcome_grader = outcome_grader or OutcomeGrader(tracker=self.outcome_tracker)

    def check_all(
        self,
        config: Dict[str, Any],
        alpaca_client: Any = None,
        *,
        simulate_paper_mode: bool = False,
    ) -> ReadinessResult:
        """Run config/system readiness checks. Use simulate_paper_mode for ALERT_ONLY dry-run."""
        failed: List[str] = []
        exec_cfg = normalize_execution_config(config)
        safety = normalize_paper_trading_safety(config)
        mode = exec_cfg.get("mode", ExecutionMode.ALERT_ONLY)

        if not safety.get("enabled"):
            failed.append("paper_trading_safety_disabled")

        if simulate_paper_mode or mode == ExecutionMode.PAPER_ALPACA:
            if mode != ExecutionMode.PAPER_ALPACA and not simulate_paper_mode:
                failed.append("execution_mode_not_paper_alpaca")
        elif mode != ExecutionMode.PAPER_ALPACA:
            return ReadinessResult(passed=not failed, failed_checks=failed)

        if exec_cfg.get("allow_live_trading"):
            failed.append("allow_live_trading_enabled")

        if exec_cfg.get("kalshi_execution_enabled"):
            failed.append("kalshi_execution_enabled")

        if safety.get("kill_switch"):
            failed.append("paper_trading_safety.kill_switch_active")

        key, secret, base_url = self._resolve_alpaca(alpaca_client)
        if not key or not secret:
            failed.append("alpaca_credentials_missing")
        if base_url.rstrip("/") != PAPER_ALPACA_URL:
            failed.append("alpaca_url_not_paper_endpoint")

        if not exec_cfg.get("require_price", True):
            failed.append("require_price_disabled")
        if not exec_cfg.get("require_fresh_data", True):
            failed.append("require_fresh_data_disabled")
        if not exec_cfg.get("max_data_age_seconds"):
            failed.append("max_data_age_seconds_missing")

        if safety.get("require_fresh_price") and not exec_cfg.get("require_fresh_data", True):
            failed.append("require_fresh_price_mismatch")

        for cap_key in (
            "max_orders_per_cycle",
            "max_orders_per_day",
            "max_notional_per_order",
            "max_total_daily_notional",
        ):
            if not safety.get(cap_key):
                failed.append(f"{cap_key}_missing")

        if safety.get("stock_only") is not True:
            failed.append("stock_only_not_enforced")

        if not safety.get("duplicate_protection", True):
            failed.append("duplicate_protection_disabled")

        if safety.get("require_recently_traded_cooldown") and not safety.get("cooldown_minutes_per_symbol"):
            failed.append("recently_traded_cooldown_disabled")

        if not _is_writable_path(getattr(self.trade_memory, "memory_file", "")):
            failed.append("trade_memory_not_writable")

        tracker_path = getattr(self.outcome_tracker, "storage_file", "")
        if not _is_writable_path(tracker_path):
            failed.append("signal_outcome_tracker_not_writable")

        if safety.get("require_outcome_tracking"):
            if self.outcome_grader is None or not isinstance(self.outcome_grader, OutcomeGrader):
                failed.append("outcome_grader_missing")

        return ReadinessResult(passed=len(failed) == 0, failed_checks=failed)

    def can_submit_paper_order(
        self,
        config: Dict[str, Any],
        signal: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
    ) -> Tuple[bool, List[str]]:
        """Combined readiness + signal-level checks for a single paper order."""
        ctx = context or {}
        simulate = bool(ctx.get("simulate_paper_mode"))
        readiness = self.check_all(
            config,
            alpaca_client=ctx.get("alpaca_client"),
            simulate_paper_mode=simulate,
        )
        failures = list(readiness.failed_checks)

        exec_cfg = normalize_execution_config(config)
        safety = normalize_paper_trading_safety(config)
        mode = exec_cfg.get("mode", ExecutionMode.ALERT_ONLY)
        if mode != ExecutionMode.PAPER_ALPACA and not simulate:
            return True, []

        symbol = str(signal.get("symbol") or "").upper()
        trade_type = str(signal.get("trade_type") or "STOCK").upper()
        if safety.get("stock_only") and trade_type not in ("STOCK", ""):
            failures.append("unsupported_trade_type_not_stock")

        price = signal.get("current_price")
        if price is None:
            price = signal.get("entry_price")
        if exec_cfg.get("require_price", True) and (price is None or float(price) <= 0):
            failures.append("current_price_missing")

        conf = _normalize_confidence_pct(signal.get("confidence"))
        floor = safety.get("block_low_confidence_below", 65)
        if conf is not None and conf < floor:
            failures.append("confidence_below_floor")

        dedup_key = signal.get("dedup_key") or f"{symbol}:{signal.get('action', 'BUY')}"
        submitted_keys = ctx.get("submitted_keys") or set()
        posted_keys = ctx.get("posted_keys") or set()
        if safety.get("duplicate_protection"):
            if dedup_key in submitted_keys:
                failures.append("duplicate_submit_in_session")
            if dedup_key in posted_keys:
                failures.append("duplicate_signal")

        if safety.get("require_recently_traded_cooldown") and symbol:
            if self.trade_memory.is_recently_traded(symbol):
                failures.append("recently_traded_cooldown")

        cap_ok, cap_reason = self.enforce_risk_caps(
            config,
            signal,
            ctx.get("daily_stats")
            or {
                "cycle_order_count": ctx.get("cycle_order_count", 0),
                "daily_order_count": ctx.get("daily_order_count", 0),
                "daily_notional": ctx.get("daily_notional", 0.0),
            },
        )
        if not cap_ok:
            failures.append(cap_reason)

        return len(failures) == 0, failures

    def enforce_risk_caps(
        self,
        config: Dict[str, Any],
        signal: Dict[str, Any],
        daily_stats: Dict[str, Any],
    ) -> Tuple[bool, str]:
        """Runtime risk caps for paper submit."""
        safety = normalize_paper_trading_safety(config)
        cycle_count = int(daily_stats.get("cycle_order_count", 0) or 0)
        daily_count = int(daily_stats.get("daily_order_count", 0) or 0)
        daily_notional = float(daily_stats.get("daily_notional", 0.0) or 0.0)
        order_notional = _estimate_notional(signal)

        max_cycle = safety.get("max_orders_per_cycle", 0)
        if max_cycle and cycle_count >= max_cycle:
            return False, "max_orders_per_cycle_exceeded"

        max_day = safety.get("max_orders_per_day", 0)
        if max_day and daily_count >= max_day:
            return False, "max_orders_per_day_exceeded"

        max_order = safety.get("max_notional_per_order", 0)
        if max_order and order_notional > max_order:
            return False, "max_notional_per_order_exceeded"

        max_daily = safety.get("max_total_daily_notional", 0)
        if max_daily and (daily_notional + order_notional) > max_daily:
            return False, "max_total_daily_notional_exceeded"

        return True, "passed"

    def _resolve_alpaca(self, alpaca_client: Any) -> Tuple[Optional[str], Optional[str], str]:
        if alpaca_client is not None:
            key = getattr(alpaca_client, "api_key", None) or getattr(alpaca_client, "key_id", None)
            secret = getattr(alpaca_client, "api_secret", None) or getattr(alpaca_client, "secret_key", None)
            base = getattr(alpaca_client, "base_url", PAPER_ALPACA_URL)
            if key and secret:
                return key, secret, str(base).rstrip("/")
        return _alpaca_creds_from_env()


def run_readiness_check(config_path: str = "config.json", *, simulate_paper_mode: bool = True) -> ReadinessResult:
    """Load config and run paper readiness check (programmatic entry point)."""
    import json

    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)
    config["execution"] = normalize_execution_config(config)
    config["paper_trading_safety"] = normalize_paper_trading_safety(config)
    mode = config["execution"].get("mode", ExecutionMode.ALERT_ONLY)
    simulate = simulate_paper_mode or mode == ExecutionMode.ALERT_ONLY
    guard = PaperReadinessGuard()
    return guard.check_all(config, simulate_paper_mode=simulate)


def _print_readiness_result(result: ReadinessResult) -> None:
    status = "PASS" if result.passed else "FAIL"
    print(f"PAPER READINESS: {status}")
    if result.failed_checks:
        print("Failed checks:")
        for check in result.failed_checks:
            print(f"  - {check}")


if __name__ == "__main__":
    outcome = run_readiness_check()
    _print_readiness_result(outcome)
