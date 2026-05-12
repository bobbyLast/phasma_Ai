"""
Unified Trading System - Combines Quick Trading and Thesis Analysis
One system that handles everything from fast swing trades to long-term theses
"""

import sys
import os

_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _root not in sys.path:
    sys.path.insert(0, _root)

from utils.insider_monitor import InsiderMonitor
from engines.insider_signal_integrator import InsiderSignalIntegrator
from utils.universal_stock_evaluator import UniversalStockEvaluator
from utils.thesis_manager import ThesisManager
from datetime import datetime
from typing import Dict, List, Tuple
import yfinance as yf


class UnifiedTradingSystem:
    """
    Unified system that intelligently routes opportunities:
    - Quick trades for immediate opportunities
    - Thesis analysis for high-potential long-term plays
    """
    
    def __init__(self, config: Dict):
        self.config = config
        # Use AI-aware insider signal integrator instead of basic monitor
        self.insider_monitor = InsiderMonitor(config.get("insider_monitor", {}))
        self.insider_integrator = InsiderSignalIntegrator(config)
        self.evaluator = UniversalStockEvaluator()
        self.thesis_manager = ThesisManager()
        self.watchlist = config.get("watchlist", [])
        self.quick_trade_threshold = config.get("quick_trade_threshold", 75)
        self.thesis_threshold = config.get("thesis_threshold", 85)
        self.enable_market_scan = config.get("enable_market_scan", False)
        
    def run_unified_analysis(self) -> Dict:
        """Run complete analysis with intelligent routing"""
        print("\n" + "="*80)
        print("UNIFIED TRADING SYSTEM")
        print("="*80)
        print(f"Run Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Quick Trade Threshold: {self.quick_trade_threshold}")
        print(f"Thesis Threshold: {self.thesis_threshold}")
        print("\nAnalyzing all opportunities and routing appropriately...\n")
        
        results = {
            "quick_trades": [],
            "thesis_positions": [],
            "monitor_list": [],
            "summary": {}
        }
        
        # 1. Gather all opportunities
        opportunities = self._gather_all_opportunities()
        
        # 2. Route each opportunity
        for opp in opportunities:
            route = self._route_opportunity(opp)
            
            if route["action"] == "QUICK_TRADE":
                trade = self._prepare_quick_trade(opp)
                results["quick_trades"].append(trade)
                
            elif route["action"] == "THESIS_ANALYSIS":
                thesis = self._prepare_thesis_position(opp)
                results["thesis_positions"].append(thesis)
                
            elif route["action"] == "MONITOR":
                results["monitor_list"].append(opp)
        
        # 3. Generate summary
        results["summary"] = {
            "total_opportunities": len(opportunities),
            "quick_trades": len(results["quick_trades"]),
            "thesis_positions": len(results["thesis_positions"]),
            "monitor": len(results["monitor_list"])
        }
        
        # 4. Display results
        self._display_results(results)
        
        return results
    
    def _gather_all_opportunities(self) -> List[Dict]:
        """Gather opportunities from all sources"""
        opportunities = []
        
        print("1. GATHERING OPPORTUNITIES...")
        print("-"*40)
        
        # Source 1: AI-aware insider signals with smart money and macro context
        print("   [AI-INSIDER] Analyzing smart money confluence...")
        insider_signals = self.insider_monitor.fetch_recent_buys()
        
        # Analyze each insider signal with AI-aware integrator
        for signal_data in insider_signals:
            ticker = signal_data['ticker']
            # Convert to format expected by integrator
            insider_data = {ticker: [signal_data]}
            
            # Get AI-aware analysis
            confluence_signal = self.insider_integrator.analyze_stock(ticker, insider_data)
            
            if confluence_signal and confluence_signal.confluence_score > 0.5:
                # Convert score to percentage
                score = confluence_signal.confluence_score * 100
                
                opportunities.append({
                    "ticker": ticker,
                    "source": "ai_insider_confluence",
                    "score": score,
                    "data": confluence_signal,
                    "reason": confluence_signal.reasoning
                })
                
                print(f"   ✓ {ticker}: {score:.0f} - {confluence_signal.reasoning[:50]}...")
        
        # Also check for moonshots from legacy monitor
        moonshots = [s for s in insider_signals if s.get("is_moonshot", False)]
        for signal in moonshots:
            opportunities.append({
                "ticker": signal["ticker"],
                "source": "insider_moonshot",
                "score": signal["moonshot_score"],
                "data": signal,
                "reason": signal["reasoning"]
            })
        
        # Source 2: Watchlist stocks
        for ticker in self.watchlist:
            quick_check = self._quick_stock_analysis(ticker)
            if quick_check["score"] > 60:
                opportunities.append({
                    "ticker": ticker,
                    "source": "watchlist",
                    "score": quick_check["score"],
                    "data": quick_check,
                    "reason": quick_check["reason"]
                })
        
        # Source 3: Market scan (optional)
        if self.config.get("enable_market_scan", False):
            scanned = self._scan_market()
            opportunities.extend(scanned)
        
        print(f"Found {len(opportunities)} total opportunities")
        return opportunities
    
    def _route_opportunity(self, opp: Dict) -> Dict:
        """Intelligently route opportunity based on score and source"""
        score = opp["score"]
        source = opp["source"]
        
        # High conviction AI confluence → Thesis (smart money + insider + macro)
        if source == "ai_insider_confluence" and score >= self.thesis_threshold:
            return {"action": "THESIS_ANALYSIS", "reason": "AI-aware high-conviction signal with macro context"}
        
        # Good AI confluence → Quick Trade
        elif source == "ai_insider_confluence" and score >= self.quick_trade_threshold:
            return {"action": "QUICK_TRADE", "reason": "AI-aware smart money confluence"}
        
        # High conviction insider buys → Thesis (legacy)
        if source == "insider_moonshot" and score >= self.thesis_threshold:
            return {"action": "THESIS_ANALYSIS", "reason": "High-conviction insider signal"}
        
        # Good insider buys → Quick Trade (legacy)
        elif source == "insider_moonshot" and score >= self.quick_trade_threshold:
            return {"action": "QUICK_TRADE", "reason": "Good insider signal"}
        
        # High momentum watchlist → Quick Trade
        elif source == "watchlist" and score >= self.quick_trade_threshold:
            return {"action": "QUICK_TRADE", "reason": "Strong momentum"}
        
        # Moderate scores → Monitor
        elif score >= 60:
            return {"action": "MONITOR", "reason": "Worth watching"}
        
        # Low scores → Ignore
        else:
            return {"action": "IGNORE", "reason": "Low score"}
    
    def _prepare_quick_trade(self, opp: Dict) -> Dict:
        """Prepare quick trade details"""
        ticker = opp["ticker"]
        
        # Determine trade parameters based on source
        if opp["source"] in ["ai_insider_confluence", "insider_moonshot"]:
            # AI-aware insider signals get higher priority
            size_pct = min(5.0, 10.0) if opp["source"] == "ai_insider_confluence" else min(1.0, 5.0)
            
            return {
                "ticker": ticker,
                "action": "SMART_MONEY_TRADE" if opp["source"] == "ai_insider_confluence" else "SWING_TRADE",
                "entry": "Market",
                "size": f"{size_pct}%",
                "hold_time": "2-6 weeks",
                "stop_loss": "-10%",
                "target": "+20-30%",
                "reason": opp["reason"],
                "confidence": opp["score"]
            }
        else:
            # Momentum trade - adjust for small bankroll
            size_pct = min(2.0, 3.0)  # Max 3% for $100 bankroll = $3
            
            return {
                "ticker": ticker,
                "action": "MOMENTUM_TRADE",
                "entry": "Current",
                "size": f"{size_pct}%",
                "hold_time": "1-3 months",
                "stop_loss": "-8%",
                "target": "+15-25%",
                "reason": opp["reason"],
                "confidence": opp["score"]
            }
    
    def _prepare_thesis_position(self, opp: Dict) -> Dict:
        """Prepare thesis position with full analysis"""
        ticker = opp["ticker"]
        
        # Run full thesis analysis
        thesis = self.thesis_manager.master_decision_loop(ticker)
        
        if thesis["action"] == "establish_thesis":
            # Establish the thesis
            self.thesis_manager.establish_thesis(ticker, thesis)
            
            # Adjust max_size for small bankroll
            original_max_size = thesis["max_position_size"]
            # For $100 bankroll, cap individual thesis at 10% ($10)
            adjusted_max_size = min(original_max_size, 10.0)
            
            return {
                "ticker": ticker,
                "action": "ESTABLISH_THESIS",
                "type": thesis["classification"],
                "max_size": adjusted_max_size,
                "review_schedule": f"Every {thesis['review_schedule']} months",
                "reason": thesis["reasoning"],
                "confidence": thesis.get("initial_confidence", 50),
                "source": opp["source"]
            }
        else:
            # Not thesis worthy, downgrade to monitor
            return {
                "ticker": ticker,
                "action": "MONITOR",
                "reason": f"Thesis analysis: {thesis['reasoning']}",
                "confidence": 0
            }
    
    def _quick_stock_analysis(self, ticker: str) -> Dict:
        """Quick stock analysis for routing"""
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            
            current = info.get("currentPrice", 0)
            high_52 = info.get("fiftyTwoWeekHigh", 0)
            volume = info.get("volume", 0)
            avg_volume = info.get("averageVolume", 0)
            
            if not all([current, high_52]):
                return {"score": 0, "reason": "Insufficient data"}
            
            # Calculate score
            score = 0
            reasons = []
            
            # Price momentum
            price_pos = current / high_52
            if price_pos > 0.9:
                score += 30
                reasons.append("Near 52-week high")
            elif price_pos > 0.8:
                score += 20
                reasons.append("Above 80% of 52-week high")
            
            # Volume momentum
            vol_ratio = volume / avg_volume if avg_volume > 0 else 1
            if vol_ratio > 2:
                score += 30
                reasons.append("High volume breakout")
            elif vol_ratio > 1.5:
                score += 20
                reasons.append("Above average volume")
            
            # Base score for being on watchlist
            score += 20
            reasons.append("Watchlist stock")
            
            return {
                "score": min(100, score),
                "reason": "; ".join(reasons),
                "price": current,
                "volume_ratio": vol_ratio
            }
            
        except Exception as e:
            return {"score": 0, "reason": f"Error: {str(e)}"}
    
    def _scan_market(self) -> List[Dict]:
        """Scan market for additional opportunities"""
        # Simple market scan - can be enhanced
        sectors = ["Technology", "Healthcare", "Energy"]
        opportunities = []
        
        for sector in sectors:
            # This would integrate with a screener API
            # For now, return empty
            pass
        
        return opportunities
    
    def _display_results(self, results: Dict):
        """Display all results clearly"""
        print("\n2. QUICK TRADES")
        print("-"*40)
        
        if results["quick_trades"]:
            for trade in results["quick_trades"]:
                print(f"\n{trade['ticker']}: {trade['action']}")
                print(f"   Size: {trade['size']} | Hold: {trade['hold_time']}")
                print(f"   Stop: {trade['stop_loss']} | Target: {trade['target']}")
                print(f"   Reason: {trade['reason']}")
        else:
            print("No quick trades identified")
        
        print("\n3. THESIS POSITIONS")
        print("-"*40)
        
        if results["thesis_positions"]:
            for thesis in results["thesis_positions"]:
                if thesis["action"] == "ESTABLISH_THESIS":
                    print(f"\n{thesis['ticker']}: ESTABLISH THESIS")
                    print(f"   Type: {thesis['type']}")
                    print(f"   Max Size: {thesis['max_size']}%")
                    print(f"   Review: {thesis['review_schedule']}")
                    print(f"   Reason: {thesis['reason']}")
        else:
            print("No thesis positions established")
        
        print("\n4. MONITOR LIST")
        print("-"*40)
        
        if results["monitor_list"]:
            for item in results["monitor_list"]:
                print(f"• {item['ticker']}: {item['reason']}")
        else:
            print("No stocks on monitor list")
        
        print("\n" + "="*80)
        print("SUMMARY")
        print("="*80)
        summary = results["summary"]
        print(f"Total Opportunities: {summary['total_opportunities']}")
        print(f"Quick Trades: {summary['quick_trades']}")
        print(f"Thesis Positions: {summary['thesis_positions']}")
        print(f"Monitor: {summary['monitor']}")
    
    def run_active_management(self):
        """Manage existing positions and theses"""
        print("\n" + "="*80)
        print("ACTIVE POSITION MANAGEMENT")
        print("="*80)
        
        # Check active theses
        active_theses = self.thesis_manager.get_active_theses()
        
        if active_theses:
            print(f"\nManaging {len(active_theses)} active theses:")
            for thesis in active_theses:
                ticker = thesis["ticker"]
                confidence = thesis["current_confidence"]
                
                # Get confidence zone
                if confidence >= 70:
                    status = "CONVICTION HOLD"
                elif confidence >= 50:
                    status = "HOLD"
                elif confidence >= 35:
                    status = "MONITOR"
                else:
                    status = "CONSIDER EXIT"
                
                print(f"\n{ticker}: {status}")
                print(f"   Confidence: {confidence}/100")
                print(f"   Type: {thesis['thesis_type']}")
                
                # Check if action needed
                if confidence < 35:
                    print("   ⚠️  Action required - confidence low")
        
        # Apply confidence decay
        print("\nApplying confidence decay...")
        self.thesis_manager.apply_confidence_decay()
        print("✓ Maintenance complete")
    
    def generate_daily_report(self) -> str:
        """Generate comprehensive daily report"""
        results = self.run_unified_analysis()
        
        report = "\n" + "="*80 + "\n"
        report += "DAILY TRADING REPORT\n"
        report += "="*80 + "\n"
        report += f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        # Quick trades section
        report += "QUICK TRADES\n"
        report += "-"*40 + "\n"
        
        if results["quick_trades"]:
            for trade in results["quick_trades"]:
                report += f"\n{trade['ticker']}: {trade['action']}\n"
                report += f"  Size: {trade['size']}, Timeframe: {trade['hold_time']}\n"
                report += f"  Reason: {trade['reason']}\n"
        else:
            report += "No quick trades today\n"
        
        # Thesis section
        report += "\nTHESIS POSITIONS\n"
        report += "-"*40 + "\n"
        
        if results["thesis_positions"]:
            for thesis in results["thesis_positions"]:
                if thesis["action"] == "ESTABLISH_THESIS":
                    report += f"\n{thesis['ticker']}: NEW THESIS\n"
                    report += f"  Type: {thesis['type']}, Max: {thesis['max_size']}%\n"
                    report += f"  Reason: {thesis['reason']}\n"
        else:
            report += "No new theses established\n"
        
        # Active theses
        active = self.thesis_manager.get_active_theses()
        if active:
            report += "\nACTIVE THESIS PORTFOLIO\n"
            report += "-"*40 + "\n"
            for thesis in active:
                report += f"{thesis['ticker']}: {thesis['thesis_type']} - {thesis['current_confidence']}/100\n"
        
        report += "\n" + "="*80 + "\n"
        report += "END REPORT\n"
        report += "="*80 + "\n"
        
        return report


def main():
    """Run the unified trading system"""
    
    # Configuration
    config = {
        "insider_monitor": {
            "enabled": True,
            "lookback_days": 7
        },
        "watchlist": ["AAPL", "MSFT", "NVDA", "TSLA", "AMD"],
        "quick_trade_threshold": 75,
        "thesis_threshold": 85,
        "enable_market_scan": False
    }
    
    # Initialize and run
    uts = UnifiedTradingSystem(config)
    
    # Run unified analysis
    results = uts.run_unified_analysis()
    
    # Active management
    uts.run_active_management()
    
    # Generate report
    report = uts.generate_daily_report()
    
    # Save report
    with open("daily_unified_report.txt", "w") as f:
        f.write(report)
    
    print("\n✅ Report saved to daily_unified_report.txt")


if __name__ == "__main__":
    main()
