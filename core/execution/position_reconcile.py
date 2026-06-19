"""Reconcile open positions on startup from broker or local JSON."""

from __future__ import annotations

import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)


def reconcile_positions_on_startup(system) -> Dict[str, Any]:
    """
    Load open positions without wiping meta-brain state.

    - PAPER_ALPACA: sync from Alpaca paper API when connected
    - PAPER_INTERNAL: load from internal paper portfolio JSON
    - Otherwise: preserve loaded meta-brain state
    """
    summary: Dict[str, Any] = {
        "source": "meta_brain_preserved",
        "positions_count": 0,
        "errors": [],
    }

    config = system.config
    exec_cfg = config.get("execution") or {}
    mode = str(exec_cfg.get("mode", "ALERT_ONLY")).upper()

    risk_manager = getattr(system.meta_brain, "risk_manager", None)
    open_positions = getattr(risk_manager, "open_positions", None) if risk_manager else None
    if open_positions is None:
        summary["errors"].append("no_risk_manager_open_positions")
        return summary

    summary["positions_count"] = len(open_positions)
    logger.info(
        "Startup reconcile: preserving %d meta-brain positions (mode=%s)",
        len(open_positions),
        mode,
    )

    if mode == "PAPER_ALPACA":
        trader = getattr(system, "alpaca_paper_trader", None)
        if trader and getattr(trader, "alpaca", None):
            try:
                alpaca_positions = trader.alpaca.list_positions()
                synced = 0
                for pos in alpaca_positions:
                    sym = pos.symbol
                    if sym not in open_positions:
                        open_positions[sym] = {
                            "symbol": sym,
                            "quantity": int(float(pos.qty)),
                            "entry_price": float(pos.avg_entry_price),
                            "source": "alpaca_reconcile",
                        }
                        synced += 1
                summary["source"] = "alpaca_paper_reconcile"
                summary["synced_from_alpaca"] = synced
                summary["positions_count"] = len(open_positions)
                print(f"  ♻️ Reconciled {synced} positions from Alpaca paper")
            except Exception as err:
                msg = f"alpaca_reconcile_failed: {err}"
                summary["errors"].append(msg)
                logger.warning(msg)
        else:
            summary["errors"].append("alpaca_not_connected_preserved_meta_brain")

    elif mode == "PAPER_INTERNAL":
        portfolio = getattr(system, "paper_portfolio", None)
        if portfolio and portfolio.state:
            try:
                internal = portfolio.state.get("open_positions", {}) or {}
                synced = 0
                for sym, pos in internal.items():
                    if sym not in open_positions:
                        open_positions[sym] = {
                            "symbol": sym,
                            "quantity": pos.get("quantity", 0),
                            "entry_price": pos.get("avg_cost", 0),
                            "source": "internal_paper_reconcile",
                        }
                        synced += 1
                summary["source"] = "internal_paper_reconcile"
                summary["synced_from_internal"] = synced
                summary["positions_count"] = len(open_positions)
                print(f"  ♻️ Reconciled {synced} positions from internal paper JSON")
            except Exception as err:
                msg = f"internal_paper_reconcile_failed: {err}"
                summary["errors"].append(msg)
                logger.warning(msg)
        else:
            summary["errors"].append("internal_paper_unavailable_preserved_meta_brain")

    return summary
