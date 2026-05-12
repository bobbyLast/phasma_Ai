"""
Main Trading Flow - Original Simple Approach with Optional Enhancements
Restores the core functionality while keeping thesis as an optional layer
"""

import sys
import os
_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)
from utils.insider_monitor import InsiderMonitor
from utils.universal_stock_evaluator import UniversalStockEvaluator
from utils.thesis_manager import ThesisManager
from datetime import datetime
from typing import Dict, List


class MainTradingFlow:
    """
    Main trading system that works as originally designed:
    1. Find opportunities
    2. Quick analysis
    3. Make trades
    4. Optional: Deep thesis analysis for special cases
    """
    
    def __init__(self, config: Dict):
        self.config = config
        self.insider_monitor = InsiderMonitor(config.get("insider_monitor", {}))
        self.universal_evaluator = UniversalStockEvaluator()
        self.thesis_manager = ThesisManager()  # Optional enhancement
        self.watchlist = config.get("watchlist", [])
        
    def run_normal_trading_flow(self) -> Dict:
        """Run the original simple trading flow"""
        print("\n" + "="*80)
        print("MAIN TRADING FLOW - ORIGINAL MODE")
        print("="*80)
        print(f"Run Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("\nMode: Normal trading with optional thesis enhancement\n")
        
        opportunities = {
            "insider_moonshots": [],
            "quick_picks": [],
            "thesis_candidates": []  # Optional enhancement
        }
        
        # Step 1: Find opportunities (original)
        print("1. FINDING OPPORTUNITIES...")
        print("-"*40)
        
        # 1a: Insider moonshots (original core)
        insider_signals = self.insider_monitor.fetch_recent_buys()
        moonshots = [s for s in insider_signals if s.get("is_moonshot", False)]
        
        for signal in moonshots:
            opportunities["insider_moonshots"].append({
                "ticker": signal["ticker"],
                "type": "insider_moonshot",
                "score": signal["moonshot_score"],
                "reason": signal["reasoning"],
                "quick_action": "Consider swing trade"
            })
        
        # 1b: Quick picks from watchlist (original)
        for ticker in self.watchlist[:5]:  # Limit to keep it fast
            quick_check = self._quick_stock_check(ticker)
            if quick_check["actionable"]:
                opportunities["quick_picks"].append(quick_check)
        
        print(f"Found {len(moonshots)} insider moonshots")
        print(f"Found {len(opportunities['quick_picks'])} quick picks")
        
        # Step 2: Quick analysis (original)
        print("\n2. QUICK ANALYSIS...")
        print("-"*40)
        
        actionable = []
        
        # Process insider moonshots
        for opp in opportunities["insider_moonshots"]:
            if opp["score"] >= 80:  # Original threshold
                actionable.append({
                    "ticker": opp["ticker"],
                    "action": "SWING_TRADE",
                    "reason": opp["reason"],
                    "timeframe": "2-6 weeks",
                    "size": "Small (1-2%)"
                })
        
        # Process quick picks
        for opp in opportunities["quick_picks"]:
            if opp["momentum_score"] >= 70:
                actionable.append({
                    "ticker": opp["ticker"],
                    "action": "POSITION_TRADE",
                    "reason": opp["reason"],
                    "timeframe": "1-3 months",
                    "size": "Medium (2-3%)"
                })
        
        print(f"Identified {len(actionable)} actionable opportunities")
        
        # Step 3: Make trades (original logic)
        print("\n3. TRADING DECISIONS...")
        print("-"*40)
        
        for trade in actionable:
            print(f"\n{trade['ticker']}: {trade['action']}")
            print(f"   Reason: {trade['reason']}")
            print(f"   Timeframe: {trade['timeframe']}")
            print(f"   Size: {trade['size']}")
        
        # Step 4: Optional thesis enhancement (NEW - doesn't block trades)
        if self.config.get("enable_thesis_enhancement", False):
            print("\n4. THESIS ENHANCEMENT (Optional)...")
            print("-"*40)
            
            thesis_candidates = []
            
            # Check if any opportunities deserve thesis analysis
            for opp in opportunities["insider_moonshots"]:
                if opp["score"] >= 90:  # High conviction
                    thesis = self.thesis_manager.master_decision_loop(opp["ticker"])
                    if thesis["action"] == "establish_thesis":
                        thesis_candidates.append({
                            "ticker": opp["ticker"],
                            "thesis": thesis,
                            "note": "High-conviction moonshot worthy of long-term hold"
                        })
            
            print(f"Found {len(thesis_candidates)} thesis candidates")
            
            for candidate in thesis_candidates:
                print(f"\nTHESIS CANDIDATE: {candidate['ticker']}")
                print(f"   Type: {candidate['thesis']['classification']}")
                print(f"   Max Size: {candidate['thesis']['max_position_size']}%")
                print(f"   Note: {candidate['note']}")
        
        return {
            "actionable_trades": actionable,
            "thesis_candidates": thesis_candidates if self.config.get("enable_thesis_enhancement") else [],
            "total_opportunities": len(actionable)
        }
    
    def _quick_stock_check(self, ticker: str) -> Dict:
        """Quick stock analysis as originally designed"""
        try:
            import yfinance as yf
            stock = yf.Ticker(ticker)
            info = stock.info
            
            # Simple momentum check (original logic)
            current = info.get("currentPrice", 0)
            high_52 = info.get("fiftyTwoWeekHigh", 0)
            volume = info.get("volume", 0)
            avg_volume = info.get("averageVolume", 0)
            
            if not all([current, high_52, volume]):
                return {"ticker": ticker, "actionable": False}
            
            # Calculate momentum score
            price_position = current / high_52
            volume_ratio = volume / avg_volume if avg_volume > 0 else 1
            
            momentum_score = 0
            if price_position > 0.8:  # Near highs
                momentum_score += 30
            if volume_ratio > 1.5:  # High volume
                momentum_score += 40
            if price_position > 0.9 and volume_ratio > 2:  # Breakout
                momentum_score += 30
            
            actionable = momentum_score >= 70
            
            return {
                "ticker": ticker,
                "actionable": actionable,
                "momentum_score": momentum_score,
                "reason": f"Momentum score: {momentum_score}/100",
                "price": current,
                "volume_ratio": volume_ratio
            }
            
        except Exception as e:
            print(f"Error checking {ticker}: {e}")
            return {"ticker": ticker, "actionable": False}
    
    def run_simple_mode(self):
        """Run in simple mode - no thesis, just trading"""
        print("\n" + "="*80)
        print("SIMPLE TRADING MODE")
        print("="*80)
        print("Fast. Direct. No complex analysis.\n")
        
        # Just get insider signals and make quick decisions
        signals = self.insider_monitor.fetch_recent_buys()
        moonshots = [s for s in signals if s.get("is_moonshot", False)]
        
        print(f"Found {len(moonshots)} moonshot signals")
        
        trades = []
        for signal in moonshots:
            if signal["moonshot_score"] >= 75:
                trades.append({
                    "ticker": signal["ticker"],
                    "action": "BUY",
                    "reason": f"Moonshot score: {signal['moonshot_score']}/100",
                    "hold_time": "2-8 weeks"
                })
        
        print(f"\n{len(trades)} trades identified:")
        for trade in trades:
            print(f"\n{trade['ticker']}: {trade['action']}")
            print(f"   {trade['reason']}")
            print(f"   Hold: {trade['hold_time']}")
        
        return trades


def main():
    """Demonstrate the restored original flow"""
    
    # Original simple config
    config = {
        "insider_monitor": {
            "enabled": True,
            "lookback_days": 7
        },
        "watchlist": ["AAPL", "MSFT", "NVDA", "TSLA"],
        "enable_thesis_enhancement": False  # Turned off by default
    }
    
    # Initialize main trading system
    main_flow = MainTradingFlow(config)
    
    # Run normal trading flow (as originally designed)
    results = main_flow.run_normal_trading_flow()
    
    print("\n" + "="*80)
    print("TRADING SUMMARY")
    print("="*80)
    print(f"Actionable trades: {results['total_opportunities']}")
    print("Thesis analysis: Available but optional")
    
    # Show simple mode
    print("\n" + "="*80)
    print("SIMPLE MODE DEMO")
    print("="*80)
    simple_trades = main_flow.run_simple_mode()
    
    print("\n✅ Original trading flow restored!")
    print("✅ Thesis enhancement available as optional layer")


if __name__ == "__main__":
    main()
