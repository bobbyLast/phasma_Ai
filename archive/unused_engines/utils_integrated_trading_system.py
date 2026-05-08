"""
Integrated Trading System - Combines Insider Monitor with Thesis Manager
Provides comprehensive analysis from short-term signals to long-term theses
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from insider_monitor import InsiderMonitor
from thesis_manager import ThesisManager
from datetime import datetime
from typing import Dict, List


class IntegratedTradingSystem:
    """Unified system combining insider signals with thesis-level analysis"""
    
    def __init__(self, config: Dict):
        self.insider_monitor = InsiderMonitor(config.get("insider_monitor", {}))
        self.thesis_manager = ThesisManager()
        self.config = config
    
    def run_comprehensive_analysis(self) -> Dict:
        """Run both insider monitoring and thesis evaluation"""
        print("\n" + "="*80)
        print("INTEGRATED TRADING SYSTEM - Comprehensive Analysis")
        print("="*80)
        print(f"Run Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        results = {
            "moonshot_signals": [],
            "large_cap_signals": [],
            "thesis_evaluations": [],
            "combined_recommendations": []
        }
        
        # 1. Get insider signals
        print("\n\n1. FETCHING INSIDER SIGNALS...")
        print("-"*40)
        
        insider_signals = self.insider_monitor.fetch_recent_buys()
        
        for signal in insider_signals:
            if signal.get("is_moonshot"):
                results["moonshot_signals"].append(signal)
            else:
                # These would be large-cap signals from our enhanced system
                results["large_cap_signals"].append(signal)
        
        print(f"\nFound {len(results['moonshot_signals'])} moonshot signals")
        print(f"Found {len(results['large_cap_signals'])} large-cap conviction signals")
        
        # 2. Evaluate interesting tickers with thesis manager
        print("\n\n2. THESIS EVALUATION...")
        print("-"*40)
        
        # Get unique tickers from all signals
        all_tickers = set()
        for signal in insider_signals:
            all_tickers.add(signal["ticker"])
        
        # Also include any tickers from config watchlist
        watchlist = self.config.get("watchlist", [])
        all_tickers.update(watchlist)
        
        # Run thesis evaluation on each
        for ticker in list(all_tickers)[:5]:  # Limit to first 5 for demo
            print(f"\nEvaluating {ticker} with Master Decision Loop...")
            thesis_result = self.thesis_manager.master_decision_loop(ticker)
            results["thesis_evaluations"].append({
                "ticker": ticker,
                "thesis_result": thesis_result
            })
            
            # If thesis should be established, do it
            if thesis_result.get("action") == "establish_thesis":
                self.thesis_manager.establish_thesis(ticker, thesis_result)
        
        # 3. Generate combined recommendations
        print("\n\n3. GENERATING COMBINED RECOMMENDATIONS...")
        print("-"*40)
        
        results["combined_recommendations"] = self._generate_combined_recommendations(
            results["moonshot_signals"],
            results["large_cap_signals"],
            results["thesis_evaluations"]
        )
        
        # 4. Display active theses
        print("\n\n4. ACTIVE THESIS PORTFOLIO...")
        print("-"*40)
        
        active_theses = self.thesis_manager.get_active_theses()
        for thesis in active_theses:
            print(f"\n{thesis['ticker']}:")
            print(f"   Type: {thesis['thesis_type']}")
            print(f"   Confidence: {thesis['current_confidence']}/100")
            print(f"   Max Size: {thesis['max_position_size']}%")
        
        # 5. Apply confidence decay to old theses
        print("\n\n5. MAINTENANCE - Applying Confidence Decay...")
        print("-"*40)
        
        self.thesis_manager.apply_confidence_decay()
        
        return results
    
    def _generate_combined_recommendations(
        self, 
        moonshots: List[Dict], 
        large_caps: List[Dict], 
        theses: List[Dict]
    ) -> List[Dict]:
        """Combine insider signals with thesis analysis for recommendations"""
        recommendations = []
        
        # Process moonshot signals
        for signal in moonshots:
            ticker = signal["ticker"]
            
            # Find matching thesis if exists
            matching_thesis = None
            for thesis in theses:
                if thesis["ticker"] == ticker:
                    matching_thesis = thesis["thesis_result"]
                    break
            
            rec = {
                "ticker": ticker,
                "type": "MOONSHOT ALERT",
                "insider_signal": signal,
                "thesis_analysis": matching_thesis,
                "recommendation": self._get_moonshot_recommendation(signal, matching_thesis)
            }
            
            recommendations.append(rec)
        
        # Process large-cap signals
        for signal in large_caps:
            ticker = signal["ticker"]
            
            # Find matching thesis
            matching_thesis = None
            for thesis in theses:
                if thesis["ticker"] == ticker:
                    matching_thesis = thesis["thesis_result"]
                    break
            
            rec = {
                "ticker": ticker,
                "type": "LARGE-CAP CONVICTION",
                "insider_signal": signal,
                "thesis_analysis": matching_thesis,
                "recommendation": self._get_largecap_recommendation(signal, matching_thesis)
            }
            
            recommendations.append(rec)
        
        # Process thesis-only recommendations (no insider signal)
        processed_tickers = {r["ticker"] for r in recommendations}
        for thesis in theses:
            if thesis["ticker"] not in processed_tickers:
                ticker = thesis["ticker"]
                thesis_result = thesis["thesis_result"]
                
                rec = {
                    "ticker": ticker,
                    "type": "THESIS-ONLY",
                    "insider_signal": None,
                    "thesis_analysis": thesis_result,
                    "recommendation": self._get_thesis_only_recommendation(thesis)
                }
                
                recommendations.append(rec)
        
        return recommendations
    
    def _get_moonshot_recommendation(self, signal: Dict, thesis: Dict) -> str:
        """Generate recommendation for moonshot signals"""
        base_rec = f"MOONSHOT BUY: {signal['ticker']}\n"
        base_rec += f"   Insider: {signal['insider_name']} bought ${signal['transaction_value']:,.0f}\n"
        base_rec += f"   Score: {signal['moonshot_score']}/100\n"
        base_rec += f"   Reason: {signal['reasoning']}\n"
        
        if thesis:
            if thesis.get("action") == "establish_thesis":
                base_rec += f"\n   THESIS SUPPORT: Establish long-term position\n"
                base_rec += f"   Max Size: {thesis['max_position_size']}%\n"
            elif thesis.get("action") == "monitor":
                base_rec += f"\n   THESIS CAUTION: Monitor for better entry\n"
        
        base_rec += f"\n   ACTION: Swing trade 2-6 weeks, keep small core position if thesis supports"
        
        return base_rec
    
    def _get_largecap_recommendation(self, signal: Dict, thesis: Dict) -> str:
        """Generate recommendation for large-cap conviction signals"""
        base_rec = f"LARGE-CAP BUY: {signal['ticker']}\n"
        base_rec += f"   Insider: {signal['insider_name']} bought ${signal['transaction_value']:,.0f}\n"
        base_rec += f"   Market Cap: ${signal['market_cap']/1e9:.1f}B\n"
        base_rec += f"   Sector: {signal['sector']}\n"
        
        if thesis:
            if thesis.get("action") == "establish_thesis":
                base_rec += f"\n   THESIS SUPPORT: {thesis['classification']}\n"
                base_rec += f"   Max Size: {thesis['max_position_size']}%\n"
            else:
                base_rec += f"\n   THESIS REJECT: {thesis['reasoning']}\n"
        
        base_rec += f"\n   ACTION: Trade the momentum, not a long-term hold"
        
        return base_rec
    
    def _get_thesis_only_recommendation(self, thesis: Dict) -> str:
        """Generate recommendation for thesis-only opportunities"""
        thesis_result = thesis.get("thesis_result", {})
        ticker = thesis.get("ticker", "UNKNOWN")
        
        base_rec = f"THESIS OPPORTUNITY: {ticker}\n"
        base_rec += f"   Classification: {thesis_result.get('classification', 'Unknown')}\n"
        base_rec += f"   Ecosystem Role: {thesis_result.get('ecosystem_role', 'Unknown')}\n"
        base_rec += f"   Reasoning: {thesis_result.get('reasoning', 'No reasoning available')}\n"
        
        if thesis_result.get("action") == "establish_thesis":
            base_rec += f"\n   RECOMMENDATION: Establish thesis position\n"
            base_rec += f"   Max Size: {thesis_result.get('max_position_size', 'N/A')}%\n"
            base_rec += f"   Review: Every {thesis_result.get('review_schedule', 'N/A')} months\n"
        elif thesis_result.get("action") == "monitor":
            base_rec += f"\n   RECOMMENDATION: Add to watchlist\n"
        else:
            base_rec += f"\n   RECOMMENDATION: Avoid\n"
        
        return base_rec
    
    def generate_daily_report(self) -> str:
        """Generate a comprehensive daily report"""
        results = self.run_comprehensive_analysis()
        
        report = "\n" + "="*80 + "\n"
        report += "DAILY TRADING INTELLIGENCE REPORT\n"
        report += "="*80 + "\n"
        report += f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        # Moonshot Alerts
        if results["moonshot_signals"]:
            report += "MOONSHOT ALERTS (High-Growth Potential)\n"
            report += "-"*50 + "\n"
            for rec in results["combined_recommendations"]:
                if rec["type"] == "MOONSHOT ALERT":
                    report += rec["recommendation"] + "\n\n"
        
        # Large-Cap Conviction
        if results["large_cap_signals"]:
            report += "\nLARGE-CAP CONVICTION BUYS (Institutional Grade)\n"
            report += "-"*50 + "\n"
            for rec in results["combined_recommendations"]:
                if rec["type"] == "LARGE-CAP CONVICTION":
                    report += rec["recommendation"] + "\n\n"
        
        # Thesis Opportunities
        thesis_recs = [r for r in results["combined_recommendations"] if r["type"] == "THESIS-ONLY"]
        if thesis_recs:
            report += "\nTHESIS OPPORTUNITIES (Long-Term)\n"
            report += "-"*50 + "\n"
            for rec in thesis_recs:
                report += rec["recommendation"] + "\n\n"
        
        # Active Thesis Summary
        active_theses = self.thesis_manager.get_active_theses()
        if active_theses:
            report += "\nACTIVE THESIS PORTFOLIO\n"
            report += "-"*50 + "\n"
            for thesis in active_theses:
                confidence_zone = self._get_confidence_zone(thesis["current_confidence"])
                report += f"{thesis['ticker']}: {thesis['thesis_type']} - "
                report += f"Confidence {thesis['current_confidence']}/100 ({confidence_zone})\n"
        
        report += "\n" + "="*80 + "\n"
        report += "END REPORT\n"
        report += "="*80 + "\n"
        
        return report
    
    def _get_confidence_zone(self, confidence: int) -> str:
        """Get confidence zone description"""
        if confidence >= 70:
            return "CONVICTION"
        elif confidence >= 50:
            return "HOLD"
        elif confidence >= 35:
            return "SKEPTICAL"
        else:
            return "EXIT"


def main():
    """Test the integrated trading system"""
    # Configuration
    config = {
        "insider_monitor": {
            "enabled": True,
            "lookback_days": 1,
            "min_value": 50000,
            "tickers": [],  # Monitor all
            "penny_only": False
        },
        "watchlist": ["PLUG", "NVDA", "DUK", "TSLA"]  # Example watchlist
    }
    
    # Initialize and run
    its = IntegratedTradingSystem(config)
    
    # Generate and print daily report
    report = its.generate_daily_report()
    print(report)
    
    # Save report to file
    with open("daily_trading_report.txt", "w", encoding="utf-8") as f:
        f.write(report)
    
    print("\n✅ Report saved to daily_trading_report.txt")


if __name__ == "__main__":
    main()
