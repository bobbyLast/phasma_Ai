"""
Trade Logger for Phasma AI
Formats and logs final trade decisions in a standardized format
"""
import os
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional
import pandas as pd
from enum import Enum

class TradeDirection(str, Enum):
    BUY_CALL = "BUY_CALL"
    BUY_PUT = "BUY_PUT"
    SELL_CALL = "SELL_CALL"
    SELL_PUT = "SELL_PUT"

class TradeLogger:
    """
    Handles formatting and logging of final trade decisions
    """
    
    def __init__(self, base_dir: str = "phasma_core_memory/signals"):
        """
        Initialize the trade logger
        
        Args:
            base_dir: Base directory for storing trade logs
        """
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
    
    def log_trade(
        self,
        symbol: str,
        trade_type: str,
        entry_price: float,
        target_price: float,
        stop_price: float,
        confidence: float,
        simulations_run: int,
        success_rate: float,
        reason: str,
        modules: list,
        trade_class: str,
        asset_type: str = "crypto",
        min_hold_days: int = 7,
        max_hold_days: int = 35,
        review_cadence_hours: int = 72,
        risk_reward_ratio: Optional[float] = None,
        metadata: Optional[Dict] = None
    ) -> str:
        """
        Log a final trade decision
        
        Returns:
            Path to the saved trade file
        """
        # Validate trade type
        try:
            trade_direction = TradeDirection(trade_type)
        except ValueError:
            raise ValueError(f"Invalid trade type: {trade_type}")
        
        # Calculate percentages
        price_diff = target_price - entry_price
        target_pct = (price_diff / entry_price) * 100
        stop_pct = ((stop_price - entry_price) / entry_price) * 100
        
        # Format current timestamp
        now = datetime.now(timezone.utc)
        timestamp_str = now.strftime("%Y-%m-%d %H:%M:%S %Z")
        
        # Create output directory
        date_dir = self.base_dir / now.strftime("%Y-%m-%d")
        date_dir.mkdir(exist_ok=True)
        
        # Generate filename
        trade_side = trade_direction.value.lower()
        filename = f"{symbol.lower()}_{trade_side}_{trade_class.lower()}_{now.strftime('%H%M')}.json"
        filepath = date_dir / filename
        
        # Prepare trade data
        trade_data = {
            "timestamp": now.isoformat(),
            "class": trade_class,
            "symbol": symbol.upper(),
            "asset_type": asset_type.lower(),
            "trade_type": trade_direction.value,
            "entry": round(float(entry_price), 2),
            "target": round(float(target_price), 2),
            "stop": round(float(stop_price), 2),
            "confidence": round(float(confidence), 2),
            "simulations_run": int(simulations_run),
            "success_rate": round(float(success_rate), 2),
            "min_hold_days": int(min_hold_days),
            "max_hold_days": int(max_hold_days),
            "review_cadence_hours": int(review_cadence_hours),
            "risk_reward_ratio": round(float(risk_reward_ratio), 2) if risk_reward_ratio else None,
            "reason": reason,
            "modules": modules,
            "metadata": metadata or {}
        }
        
        # Save to JSON
        with open(filepath, 'w') as f:
            json.dump(trade_data, f, indent=2)
        
        # Format console output
        self._print_trade_console(
            timestamp=timestamp_str,
            trade_class=trade_class,
            symbol=symbol.upper(),
            asset_type=asset_type,
            trade_type=trade_direction.value,
            entry_price=entry_price,
            target_price=target_price,
            stop_price=stop_price,
            target_pct=target_pct,
            stop_pct=stop_pct,
            confidence=confidence,
            simulations_run=simulations_run,
            success_rate=success_rate,
            min_hold_days=min_hold_days,
            max_hold_days=max_hold_days,
            review_cadence_hours=review_cadence_hours,
            reason=reason,
            filepath=str(filepath)
        )
        
        return str(filepath)
    
    def _print_trade_console(
        self,
        timestamp: str,
        trade_class: str,
        symbol: str,
        asset_type: str,
        trade_type: str,
        entry_price: float,
        target_price: float,
        stop_price: float,
        target_pct: float,
        stop_pct: float,
        confidence: float,
        simulations_run: int,
        success_rate: float,
        min_hold_days: int,
        max_hold_days: int,
        review_cadence_hours: int,
        reason: str,
        filepath: str
    ) -> None:
        """Format and print trade to console with ASCII formatting"""
        try:
            # Helper function to safely convert to ASCII
            def safe_str(s):
                if not isinstance(s, str):
                    s = str(s)
                return s.encode('ascii', 'replace').decode('ascii')

            # Format the output with ASCII characters only
            output = []
            output.append(f"\n[{safe_str(timestamp)}] [!] PHASMA FINAL TRADE")
            output.append("=" * 55)
            output.append(f"CLASS: {safe_str(trade_class)}")
            output.append(f"ASSET: {safe_str(symbol)} ({'CRYPTO' if str(asset_type).lower() == 'crypto' else 'STOCK'})")
            output.append(f"TRADE: {safe_str(trade_type)}")
            
            output.append(f"ENTRY PRICE: ${float(entry_price):.2f}")
            output.append(f"TARGET PRICE: ${float(target_price):.2f}  (+{float(target_pct):.1f}%)")
            output.append(f"STOP PRICE: ${float(stop_price):.2f}  (-{abs(float(stop_pct)):.1f}%)")
            output.append("")
            
            confidence_pct = int(float(confidence) * 100)
            success_pct = int(float(success_rate) * 100)
            output.append(f"CONFIDENCE: {confidence_pct}%  |  SIMULATIONS: {int(simulations_run)}  |  SUCCESS RATE: {success_pct}%")
            output.append("")
            
            output.append(f"MIN HOLD: {int(min_hold_days)} days  |  MAX HOLD: {int(max_hold_days)} days  |  REVIEW: Every {int(review_cadence_hours)}h")
            output.append("")
            
            output.append("WHY THIS WINS:")
            if reason:
                for line in str(reason).split('\n'):
                    if line.strip():
                        output.append(f"* {safe_str(line.strip())}")
            else:
                output.append("* No specific reason provided")
            
            output.append("")
            output.append(f"Stored: {safe_str(filepath)}")
            output.append("=" * 55)
            
            # Print the output line by line
            for line in output:
                try:
                    print(line)
                except UnicodeEncodeError:
                    print(safe_str(line))

        except Exception as e:
            error_msg = f"Error printing trade to console: {str(e)}\n"
            print(error_msg.encode('ascii', 'replace').decode('ascii'))

# Example usage
if __name__ == "__main__":
    logger = TradeLogger()
    
    # Example BTC trade
    logger.log_trade(
        symbol="BTC",
        trade_type="BUY_PUT",
        entry_price=101900.0,
        target_price=91300.0,
        stop_price=109000.0,
        confidence=0.87,
        simulations_run=500,
        success_rate=0.71,
        trade_class="SWING_30D",
        asset_type="crypto",
        min_hold_days=7,
        max_hold_days=35,
        review_cadence_hours=72,
        risk_reward_ratio=2.5,
        reason="""Momentum breakdown confirmed — MACD cross + volume divergence
Whale outflows detected on-chain, consistent with distribution phase
Funding rate negative three days straight — leverage unwinding
Price rejected at 20DMA ceiling and failed retest of 105K
Sentiment cooled off after record inflows; volatility spike +6%""",
        modules=["market_crash_detector", "simulation_engine", "volatility_model"]
    )
