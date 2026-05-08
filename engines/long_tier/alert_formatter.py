"""
Alert Formatter for Long-Tier Investment Alerts
Formats trading alerts with tiered profit projections and strategy guidance
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union
from dataclasses import dataclass
import math

@dataclass
class AlertComponents:
    symbol: str
    current_price: float
    target_price: float
    catalyst: str
    partner_tier: str = ""
    time_horizon: str = "multi-year"
    confidence: float = 0.0  # 0-10 scale
    risk_level: str = "Medium"
    volume_7d_avg: int = 0
    market_cap: float = 0.0
    current_time: datetime = None

class AlertFormatter:
    """Formats trading alerts with tiered profit projections and strategy guidance"""
    
    def __init__(self):
        self.current_time = datetime.utcnow()
    
    def format_alert(self, components: AlertComponents) -> str:
        """Format a complete alert with all components"""
        # Calculate key metrics
        upside_pct = ((components.target_price / components.current_price) - 1) * 100
        upside_multiple = components.target_price / components.current_price
        
        # Format current and target prices
        current_price_fmt = f"${components.current_price:.2f}"
        target_price_fmt = f"${components.target_price:.0f}" if components.target_price >= 10 else f"${components.target_price:.2f}"
        
        # Generate tiered profit projections
        profit_projections = self._generate_profit_projections(
            components.current_price, 
            components.target_price
        )
        
        # Generate strategy guidance
        strategy = self._generate_strategy_guidance(
            components.partner_tier,
            upside_multiple,
            components.risk_level
        )
        
        # Format the alert
        alert_lines = [
            f"🚀 **LONG-TIER ALERT — ${components.symbol.upper()}**",
            f"Entry: {current_price_fmt}  |  Target: {target_price_fmt}  |  Upside: {upside_pct:.0f}% ({components.time_horizon})\n",
            "💰 **Potential Profits:**",
        ]
        
        # Add profit projections
        for tier, projection in profit_projections.items():
            alert_lines.append(
                f"{tier}: ${projection['investment']:,.0f} → "
                f"${projection['potential']:,.0f} "
                f"(+${projection['profit']:,.0f})"
            )
        
        # Add AI forecast and strategy
        alert_lines.extend([
            f"\n📈 **AI Forecast:**",
            f"{components.catalyst}",
            f"Confidence: {components.confidence:.1f}/10.0",
            f"Risk Level: {components.risk_level}",
            f"Volume (7d avg): {self._format_number(components.volume_7d_avg)} shares",
            f"Market Cap: ${self._format_number(components.market_cap)}\n",
            "🧠 **AI Strategy:**",
            strategy,
            "\n🚨 **Exit Advisory:**",
            "- AI monitors real-time filings + headlines",
            "- 🔴 exit only if structural news + downtrend confirm",
            "- 🟡 watch if temporary dip or FUD headline",
            "- 🟢 hold if continuation signals intact\n",
            "📅 **Monitoring:**",
            f"Continuous NLP + volume tracking. Last updated: {self._format_timestamp(components.current_time or self.current_time)}",
            "\n📝 **TL;DR:**",
            self._generate_tldr(components, upside_multiple, profit_projections)
        ])
        
        return "\n".join(alert_lines)
    
    def _generate_profit_projections(self, entry_price: float, target_price: float) -> Dict[str, Dict[str, float]]:
        """Generate profit projections for each investment tier"""
        # Define investment tiers (in dollars)
        tiers = {
            'Micro ($100)': 100,
            'Standard ($500)': 500,
            'Heavy ($1,000)': 1000,
            'Whale ($5,000)': 5000
        }
        
        # Calculate profit multiples
        profit_multiple = target_price / entry_price
        
        # Generate projections for each tier
        projections = {}
        for name, investment in tiers.items():
            potential = investment * profit_multiple
            profit = potential - investment
            projections[name] = {
                'investment': investment,
                'potential': potential,
                'profit': profit
            }
            
        return projections
    
    def _generate_strategy_guidance(self, partner_tier: str, upside_multiple: float, risk_level: str) -> str:
        """Generate strategy guidance based on the opportunity"""
        guidance = []
        
        # Add tier-specific guidance
        if partner_tier == "TIER_1":
            guidance.append("✅ Tier-1 partnership confirmed. Maximum allocation recommended.")
        elif partner_tier == "TIER_2":
            guidance.append("✅ Strong partnership. Above-average allocation recommended.")
        else:
            guidance.append("ℹ️ Standard allocation. Monitor for partnership confirmation.")
        
        # Add upside-based guidance
        if upside_multiple >= 10:
            guidance.append("💎 10×+ upside potential. Consider holding through volatility.")
        elif upside_multiple >= 5:
            guidance.append("🚀 5×+ upside potential. Look for strong volume confirmation.")
        
        # Add risk-based guidance
        if risk_level == "High":
            guidance.append("⚠️ Higher risk. Position size accordingly and use tight stops.")
        elif risk_level == "Low":
            guidance.append("🛡️ Lower risk. Can scale in more aggressively.")
        
        # Add general guidance
        guidance.extend([
            "📊 Monitor volume and price action for confirmation.",
            "🔍 Watch for follow-up news and institutional accumulation."
        ])
        
        return "\n".join(guidance)
    
    def _generate_tldr(self, components: AlertComponents, upside_multiple: float, 
                      profit_projections: Dict) -> str:
        """Generate a TL;DR summary of the alert"""
        # Format key metrics
        entry = components.current_price
        target = components.target_price
        upside_pct = ((target / entry) - 1) * 100
        
        # Get profit examples
        micro_profit = profit_projections.get('Micro ($100)', {}).get('profit', 0)
        standard_profit = profit_projections.get('Standard ($500)', {}).get('profit', 0)
        heavy_profit = profit_projections.get('Heavy ($1,000)', {}).get('profit', 0)
        
        # Format TL;DR
        tldr = [
            f"${entry:.2f} → ${target:.0f} ({upside_pct:.0f}% upside). ",
            f"$100 → ${100 + micro_profit:,.0f} | ",
            f"$500 → ${500 + standard_profit:,.0f} | ",
            f"$1,000 → ${1000 + heavy_profit:,.0f}."
        ]
        
        return "".join(tldr)
    
    def _format_number(self, num: float) -> str:
        """Format large numbers with K/M/B/T suffixes"""
        if num >= 1e12:
            return f"{num/1e12:.1f}T"
        elif num >= 1e9:
            return f"{num/1e9:.1f}B"
        elif num >= 1e6:
            return f"{num/1e6:.1f}M"
        elif num >= 1e3:
            return f"{num/1e3:.1f}K"
        return f"{num:.0f}"
    
    def _format_timestamp(self, dt: datetime) -> str:
        """Format timestamp in a human-readable way"""
        now = self.current_time
        delta = now - dt
        
        if delta < timedelta(minutes=1):
            return "just now"
        elif delta < timedelta(hours=1):
            mins = int(delta.seconds / 60)
            return f"{mins} minute{'s' if mins > 1 else ''} ago"
        elif delta < timedelta(days=1):
            hours = int(delta.seconds / 3600)
            return f"{hours} hour{'s' if hours > 1 else ''} ago"
        elif delta < timedelta(days=30):
            days = delta.days
            return f"{days} day{'s' if days > 1 else ''} ago"
        else:
            return dt.strftime("%Y-%m-%d")
