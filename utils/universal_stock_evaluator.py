"""
Universal Stock Evaluator - Applies thesis reasoning to ANY stock
Not limited to insider signals - can evaluate any ticker at any time
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from thesis_manager import ThesisManager
from typing import Dict, List
import yfinance as yf


class UniversalStockEvaluator:
    """Universal evaluator that applies the Master Decision Loop to any stock"""
    
    def __init__(self):
        self.tm = ThesisManager()
    
    def evaluate_any_stock(self, ticker: str) -> Dict:
        """
        Evaluate any stock using the Master Decision Loop
        This is the universal entry point for all stock analysis
        """
        print(f"\n{'='*80}")
        print(f"UNIVERSAL STOCK EVALUATION: {ticker}")
        print(f"{'='*80}")
        
        # Run the complete Master Decision Loop
        decision = self.tm.master_decision_loop(ticker)
        
        # Add universal metadata
        decision.update({
            "evaluated_at": self.tm._get_current_time(),
            "evaluation_source": "universal_request",
            "requires_thesis": decision.get("action") == "establish_thesis",
            "trade_only": decision.get("action") == "trade_only",
            "reject": decision.get("action") == "reject"
        })
        
        # Generate spoken reasoning (as per document)
        reasoning = self._generate_spoken_reasoning(ticker, decision)
        decision["spoken_reasoning"] = reasoning
        
        # If thesis worthy, offer to establish it
        if decision.get("action") == "establish_thesis":
            print(f"\n✅ {ticker} QUALIFIES FOR THESIS ESTABLISHMENT")
            print(f"   Type: {decision['classification']}")
            print(f"   Max Size: {decision['max_position_size']}%")
            print(f"   Review Cycle: {decision['review_schedule']} months")
        
        return decision
    
    def _generate_spoken_reasoning(self, ticker: str, decision: Dict) -> str:
        """Generate the spoken reasoning chain as specified in the document"""
        reasoning = f""""I am not predicting price.
I am evaluating whether {ticker} can survive long enough to benefit from a structural shift in the world."

Macro Reality Check:
"Is the world forced to move in this direction over the next decade?"
→ {decision.get('reasoning', 'Unable to determine')}

Constraint Identification:
"What problem does this solve that cannot be ignored?"
→ {self._identify_constraint(ticker)}

Company Role Classification:
"Is this company a direct beneficiary or an option on the future?"
→ {decision.get('ecosystem_role', 'Unknown')} - {decision.get('classification', 'Unknown')}

Survival Test:
"Can this company stay alive without destroying shareholders?"
→ Survival Score: {decision.get('survival_score', 'N/A')}/10

Price vs Risk Buffer:
"Am I paying a low enough price to justify uncertainty?"
→ {self._assess_price_buffer(ticker)}

Optionality Justification:
"If this works, does upside meaningfully exceed downside?"
→ {self._evaluate_optionality(ticker)}

Regret-Based Position Sizing:
"Will I regret missing this more than I regret losing this?"
→ Max Position: {decision.get('max_position_size', 'N/A')}% of portfolio

Final Decision: {decision.get('action', 'Unknown').upper()}
"""
        return reasoning
    
    def _identify_constraint(self, ticker: str) -> str:
        """Identify what problem the company solves"""
        try:
            info = yf.Ticker(ticker).info
            sector = info.get("sector", "")
            industry = info.get("industry", "")
            summary = info.get("longBusinessSummary", "")
            
            constraints = {
                "Technology": ["Compute scarcity", "Data infrastructure", "Digital transformation"],
                "Healthcare": ["Aging population", "Disease treatment", "Healthcare costs"],
                "Energy": ["Energy transition", "Power demand", "Climate change"],
                "Financial": ["Payment efficiency", "Capital allocation", "Risk management"],
                "Industrial": ["Supply chain", "Infrastructure", "Automation"],
                "Consumer": ["Convenience", "Cost savings", "Experience"]
            }
            
            for sec, problems in constraints.items():
                if sec in sector:
                    return problems[0] if problems else "Unknown constraint"
            
            return "General market inefficiency"
        except:
            return "Unable to identify constraint"
    
    def _assess_price_buffer(self, ticker: str) -> str:
        """Assess if price provides room for error"""
        try:
            info = yf.Ticker(ticker).info
            current = info.get("currentPrice", 0)
            high_52 = info.get("fiftyTwoWeekHigh", 0)
            
            if not all([current, high_52]):
                return "Unable to assess price buffer"
            
            position = current / high_52
            
            if position < 0.3:
                return "Excellent buffer - near lows"
            elif position < 0.5:
                return "Good buffer - below midpoint"
            elif position < 0.7:
                return "Limited buffer - above midpoint"
            else:
                return "No buffer - near highs"
        except:
            return "Unable to assess price buffer"
    
    def _evaluate_optionality(self, ticker: str) -> str:
        """Evaluate if upside exceeds downside"""
        try:
            info = yf.Ticker(ticker).info
            market_cap = info.get("marketCap", 0)
            
            if market_cap < 1_000_000_000:
                return "High optionality - micro-cap with room to grow 10x+"
            elif market_cap < 10_000_000_000:
                return "Moderate optionality - small-cap with 3-5x potential"
            else:
                return "Limited optionality - large cap, focus on execution"
        except:
            return "Unable to evaluate optionality"
    
    def batch_evaluate(self, tickers: List[str]) -> Dict:
        """Evaluate multiple stocks in batch"""
        results = {}
        
        print(f"\n{'='*80}")
        print(f"BATCH EVALUATION - {len(tickers)} stocks")
        print(f"{'='*80}")
        
        for ticker in tickers:
            try:
                results[ticker] = self.evaluate_any_stock(ticker)
            except Exception as e:
                print(f"Error evaluating {ticker}: {e}")
                results[ticker] = {"error": str(e)}
        
        # Generate summary
        thesis_candidates = [t for t, r in results.items() 
                           if r.get("action") == "establish_thesis"]
        trade_only = [t for t, r in results.items() 
                    if r.get("action") == "trade_only"]
        rejects = [t for t, r in results.items() 
                 if r.get("action") == "reject"]
        
        print(f"\n{'='*80}")
        print("BATCH EVALUATION SUMMARY")
        print(f"{'='*80}")
        print(f"Total Evaluated: {len(tickers)}")
        print(f"Thesis Candidates: {len(thesis_candidates)}")
        print(f"Trade Only: {len(trade_only)}")
        print(f"Rejects: {len(rejects)}")
        
        if thesis_candidates:
            print(f"\n✅ THESIS CANDIDATES:")
            for ticker in thesis_candidates:
                print(f"   {ticker}: {results[ticker]['classification']}")
        
        return results
    
    def scan_market(self, 
                    sectors: List[str] = None,
                    market_cap_min: int = None,
                    market_cap_max: int = None,
                    limit: int = 20) -> List[str]:
        """
        Scan market for stocks meeting criteria
        Returns tickers for evaluation
        """
        print(f"\n{'='*80}")
        print("MARKET SCANNER")
        print(f"{'='*80}")
        
        # This would integrate with a stock screener API
        # For now, return example tickers based on sectors
        example_tickers = {
            "Technology": ["NVDA", "AMD", "INTC", "MU", "SMCI"],
            "Healthcare": ["JNJ", "PFE", "MRK", "ABT", "UNH"],
            "Energy": ["XOM", "CVX", "COP", "EOG", "SLB"],
            "Financial": ["JPM", "BAC", "WFC", "GS", "MS"],
            "Consumer": ["AMZN", "TSLA", "HD", "MCD", "NKE"]
        }
        
        tickers = []
        if sectors:
            for sector in sectors:
                tickers.extend(example_tickers.get(sector, []))
        else:
            for sector_tickers in example_tickers.values():
                tickers.extend(sector_tickers)
        
        # Limit results
        tickers = tickers[:limit] if limit else tickers
        
        print(f"Found {len(tickers)} tickers to evaluate")
        return tickers
    
    def evaluate_from_news(self, news_tickers: List[str]) -> Dict:
        """Evaluate stocks mentioned in news"""
        print(f"\n{'='*80}")
        print(f"NEWS-DRIVEN EVALUATION - {len(news_tickers)} tickers")
        print(f"{'='*80}")
        
        results = {}
        for ticker in news_tickers:
            print(f"\nEvaluating {ticker} from news...")
            results[ticker] = self.evaluate_any_stock(ticker)
        
        return results


def main():
    """Demonstrate universal evaluation"""
    evaluator = UniversalStockEvaluator()
    
    # Example 1: Evaluate any stock on demand
    print("\n\n1. SINGLE STOCK EVALUATION")
    print("="*40)
    result = evaluator.evaluate_any_stock("AAPL")
    
    # Example 2: Batch evaluation
    print("\n\n2. BATCH EVALUATION")
    print("="*40)
    batch = ["MSFT", "GOOGL", "META", "TSLA"]
    batch_results = evaluator.batch_evaluate(batch)
    
    # Example 3: Market scan
    print("\n\n3. MARKET SCAN")
    print("="*40)
    scanned = evaluator.scan_market(sectors=["Technology"], limit=5)
    if scanned:
        evaluator.batch_evaluate(scanned[:3])


if __name__ == "__main__":
    main()
