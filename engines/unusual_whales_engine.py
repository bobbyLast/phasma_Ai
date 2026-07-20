#!/usr/bin/env python3
"""
Unusual Whales Engine - Tracks unusual options activity and institutional flow.

HONESTY RULE: never emit canned demo AAPL/TSLA/NVDA flows into the live pipeline.
Without a real non-placeholder API key, the engine stays disabled and returns [].
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

from core.execution.data_gates import is_placeholder_api_key


@dataclass
class UnusualOptionsFlow:
    """Represents unusual options activity"""
    symbol: str
    action: str  # BUY or SELL
    option_type: str  # CALL or PUT
    strike: float
    expiration: str
    volume: int
    volume_avg: int
    oi: int
    sentiment: str  # BULLISH or BEARISH
    confidence: float
    timestamp: datetime
    price: float


class UnusualWhalesEngine:
    """Engine for tracking unusual options activity and institutional flow"""

    def __init__(self, config: Dict):
        self.config = config if isinstance(config, dict) else getattr(config, "data", {}) or {}
        self.logger = logging.getLogger(__name__)
        self.base_url = "https://api.unusualwhales.com/v1"
        block = self.config.get("unusual_whales", {}) or {}
        self.api_key = block.get("api_key") or block.get("key")
        self.enabled = bool(block.get("enabled", False))

        self.unusual_activity_cache = {}
        self.last_update = None

        self.min_volume_multiplier = block.get("min_volume_multiplier", 3)
        self.min_confidence = block.get("min_confidence", 60)

        if not self.enabled:
            self.logger.info("Unusual Whales engine disabled (config)")
            return

        if not self.api_key or is_placeholder_api_key(self.api_key):
            self.logger.warning(
                "Unusual Whales: placeholder API key — engine stays enabled in config "
                "but returns no flows until a real key is set"
            )
            return

        self.logger.info("Unusual Whales Engine initialized (live key present)")

    async def get_unusual_options_flow(self, limit: int = 20) -> List[UnusualOptionsFlow]:
        """Get recent unusual options activity — real API only, never demo."""
        if not self.enabled:
            return []

        # Live HTTP integration not yet wired; fail closed (no fake mega-caps).
        self.logger.warning(
            "Unusual Whales API key present but live client not implemented — "
            "returning empty (no demo data)"
        )
        return []

    async def get_institutional_flow(self, limit: int = 20) -> List[Dict]:
        """Get institutional flow — real API only, never demo."""
        if not self.enabled:
            return []
        self.logger.warning(
            "Unusual Whales institutional flow: live client not implemented — returning empty"
        )
        return []

    def convert_to_trading_signals(self, unusual_flows: List[UnusualOptionsFlow]) -> List[Dict]:
        signals = []
        for flow in unusual_flows:
            if flow.option_type == "CALL" and flow.sentiment == "BULLISH":
                action = "BUY"
            elif flow.option_type == "PUT" and flow.sentiment == "BEARISH":
                action = "SELL"
            else:
                continue

            volume_multiplier = flow.volume / max(flow.volume_avg, 1)
            confidence = min(95, flow.confidence + (volume_multiplier * 5))
            signals.append({
                "symbol": flow.symbol,
                "action": action,
                "confidence": confidence / 100,
                "source": "unusual_whales",
                "is_demo": False,
                "rationale": (
                    f"Unusual {flow.option_type} activity: {flow.volume:,} contracts "
                    f"vs avg {flow.volume_avg:,} ({volume_multiplier:.1f}x normal)"
                ),
                "details": {
                    "option_type": flow.option_type,
                    "strike": flow.strike,
                    "expiration": flow.expiration,
                    "volume": flow.volume,
                    "volume_multiplier": volume_multiplier,
                    "sentiment": flow.sentiment,
                },
                "timestamp": flow.timestamp.isoformat(),
                "entry_price": flow.price,
                "signal_type": "options_flow",
            })
        return signals

    def convert_institutional_to_signals(self, institutional_flows: List[Dict]) -> List[Dict]:
        signals = []
        for flow in institutional_flows:
            if flow.get("size", 0) < 10_000_000:
                continue
            signals.append({
                "symbol": flow["symbol"],
                "action": flow["action"],
                "confidence": flow["confidence"] / 100,
                "source": "unusual_whales",
                "is_demo": False,
                "rationale": f"Institutional {flow['type']}: ${flow['size']:,} at ${flow['price']:.2f}",
                "details": {
                    "flow_type": flow["type"],
                    "size": flow["size"],
                    "sentiment": flow["sentiment"],
                },
                "timestamp": flow["timestamp"].isoformat()
                if hasattr(flow["timestamp"], "isoformat")
                else str(flow["timestamp"]),
                "entry_price": flow["price"],
                "signal_type": "institutional_flow",
            })
        return signals

    async def get_signals(self) -> List[Dict]:
        if not self.enabled:
            return []
        unusual_flows = await self.get_unusual_options_flow()
        all_signals = self.convert_to_trading_signals(unusual_flows)
        institutional_flows = await self.get_institutional_flow()
        all_signals.extend(self.convert_institutional_to_signals(institutional_flows))
        all_signals.sort(key=lambda x: x.get("confidence", 0), reverse=True)
        self.logger.info("Generated %s live unusual-whales signals", len(all_signals))
        return all_signals

    def analyze_flow_sentiment(self, symbol: str, days_back: int = 5) -> Dict:
        return {
            "symbol": symbol,
            "sentiment": "unknown",
            "confidence": 0,
            "note": "live flow history not available",
            "days_back": days_back,
        }
