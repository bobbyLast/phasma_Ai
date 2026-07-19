"""Local ledger portfolio normalization and honest labeling."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


POSITION_OPEN = "OPEN"
POSITION_EXPIRED = "EXPIRED"
POSITION_CLOSED = "CLOSED"
POSITION_SIMULATED = "SIMULATED"
POSITION_ALERT_ONLY = "ALERT_ONLY"
POSITION_INVALID_SIZE = "INVALID_SIZE"


def portfolio_status_label(*, broker_backed: bool = False) -> str:
    return "REAL PORTFOLIO STATUS" if broker_backed else "LOCAL LEDGER STATUS"


def normalize_position(pos: Dict[str, Any], *, now: Optional[datetime] = None) -> Dict[str, Any]:
    """Clean position record: size, expiry, status."""
    now = now or datetime.now(timezone.utc)
    out = dict(pos)
    qty = float(out.get("quantity") or out.get("shares") or out.get("size") or 0)
    notional = float(out.get("notional") or out.get("position_size") or 0)
    avg_cost = float(out.get("avg_cost") or out.get("entry_price") or out.get("cost_basis") or 0)

    if qty <= 0 and notional <= 0:
        out["status"] = POSITION_INVALID_SIZE
        out["active_trade"] = False
        return out

    days_left = out.get("days_left")
    if days_left is None:
        days_left = out.get("days_to_expiry")
    try:
        days_left_i = int(days_left) if days_left is not None else None
    except (TypeError, ValueError):
        days_left_i = None

    if days_left_i is not None and days_left_i <= 0:
        out["status"] = POSITION_EXPIRED
        out["active_trade"] = False
        return out

    if out.get("alert_only") or out.get("execution_mode") == "ALERT_ONLY":
        out["status"] = POSITION_ALERT_ONLY
        out["active_trade"] = False
        return out

    if out.get("simulated") or out.get("source") == "simulated":
        out["status"] = POSITION_SIMULATED
    else:
        out["status"] = POSITION_OPEN
    out["active_trade"] = True
    return out


def filter_active_positions(positions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    normalized = [normalize_position(p) for p in positions]
    return [p for p in normalized if p.get("active_trade")]


def compute_direction_pnl(entry: float, exit: float, action: str) -> float:
    """BUY: win if exit > entry. SELL/SHORT: win if exit < entry."""
    action_u = str(action or "BUY").upper()
    if action_u in ("SELL", "SHORT", "SELL_SHORT"):
        return entry - exit
    return exit - entry


def summarize_ledger(portfolio: Dict[str, Any], *, broker_backed: bool = False) -> str:
    label = portfolio_status_label(broker_backed=broker_backed)
    open_positions = filter_active_positions(portfolio.get("open_positions") or [])
    lines = [
        f"\n💼 {label}:",
        f"   Starting Capital: ${portfolio.get('starting_capital', 0):.2f}",
        f"   Available Cash: ${portfolio.get('available_capital', 0):.2f}",
        f"   Realized P&L: ${portfolio.get('realized_pnl', 0):.2f}",
        f"   Unrealized P&L: ${portfolio.get('unrealized_pnl', 0):.2f}",
        f"   Total Portfolio Value: ${portfolio.get('total_portfolio_value', 0):.2f}",
        f"   Active Positions: {len(open_positions)}",
    ]
    for pos in open_positions[:3]:
        sym = pos.get("symbol", "N/A")
        qty = pos.get("quantity") or pos.get("shares") or 0
        cost = pos.get("avg_cost") or pos.get("entry_price") or 0
        pnl = pos.get("unrealized_pnl", 0)
        lines.append(f"   • {sym}: {qty} @ ${float(cost):.2f} | P&L ${float(pnl):.2f}")
    return "\n".join(lines)
