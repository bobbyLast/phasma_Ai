"""
P/E Ratio Analyzer
Comprehensive P/E analysis including:
- Industry-relative comparisons
- PEG ratio calculations
- Historical P/E trends
- Fair value estimates
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
import sqlite3


class PERatioAnalyzer:
    """Advanced P/E ratio analysis for fundamental valuation"""
    
    # Industry average P/E ratios (updated quarterly)
    INDUVERAGE_PE = {
        "Technology": 28.5,
        "Healthcare": 22.3,
        "Financial Services": 13.8,
        "Energy": 15.2,
        "Utilities": 18.9,
        "Consumer Discretionary": 25.1,
        "Consumer Staples": 20.4,
        "Industrial": 19.7,
        "Materials": 16.8,
        "Real Estate": 24.3,
        "Communication Services": 23.6,
        "Biotechnology": 35.2,
        "Software": 32.8,
        "Semiconductors": 26.4,
        "Retail": 18.5,
        "Automotive": 14.2,
        "Aerospace": 21.7,
        "Chemicals": 17.9
    }
    
    def __init__(self):
        self.cache = {}
        self.cache_expiry = 3600  # 1 hour cache
        
    def analyze_pe_ratio(self, ticker: str) -> Dict:
        """Comprehensive P/E ratio analysis"""
        
        # Check cache
        if ticker in self.cache:
            cached_data, timestamp = self.cache[ticker]
            if datetime.now().timestamp() - timestamp < self.cache_expiry:
                return cached_data
        
        try:
            # Get stock data
            stock = yf.Ticker(ticker)
            info = stock.info
            
            # Basic P/E data
            trailing_pe = info.get("trailingPE", None)
            forward_pe = info.get("forwardPE", None)
            pe_growth = info.get("pegRatio", None)
            
            if not trailing_pe:
                return {
                    "ticker": ticker,
                    "error": "No P/E ratio available (company likely unprofitable)",
                    "analysis": "no_pe",
                    "score": 0
                }
            
            # Get additional metrics
            eps_growth = info.get("earningsGrowth", None)
            revenue_growth = info.get("revenueGrowth", None)
            sector = info.get("sector", "Unknown")
            market_cap = info.get("marketCap", 0)
            
            # Historical P/E data
            historical_pe = self._get_historical_pe(stock)
            
            # Industry comparison
            industry_analysis = self._compare_to_industry(trailing_pe, sector)
            
            # PEG analysis
            peg_analysis = self._analyze_peg_ratio(trailing_pe, eps_growth, pe_growth)
            
            # Trend analysis
            trend_analysis = self._analyze_pe_trend(historical_pe)
            
            # Valuation assessment
            valuation = self._assess_valuation(
                trailing_pe, forward_pe, industry_analysis, 
                peg_analysis, trend_analysis
            )
            
            # Fair value estimate
            fair_value = self._estimate_fair_value(trailing_pe, sector, eps_growth)
            
            result = {
                "ticker": ticker,
                "current_pe": trailing_pe,
                "forward_pe": forward_pe,
                "sector": sector,
                "market_cap": market_cap,
                "industry_pe": industry_analysis["industry_avg"],
                "pe_vs_industry": industry_analysis["percentile"],
                "peg_ratio": pe_growth,
                "eps_growth": eps_growth,
                "revenue_growth": revenue_growth,
                "historical_avg": historical_pe["avg"] if historical_pe else None,
                "pe_percentile": historical_pe["percentile"] if historical_pe else None,
                "trend": trend_analysis["trend"],
                "trend_strength": trend_analysis["strength"],
                "valuation_level": valuation["level"],
                "valuation_score": valuation["score"],
                "fair_value_range": fair_value,
                "analysis": "complete",
                "score": valuation["score"]
            }
            
            # Cache result
            self.cache[ticker] = (result, datetime.now().timestamp())
            
            return result
            
        except Exception as e:
            return {
                "ticker": ticker,
                "error": str(e),
                "analysis": "error",
                "score": 0
            }
    
    def _get_historical_pe(self, stock) -> Optional[Dict]:
        """Get historical P/E ratios for trend analysis"""
        try:
            # Get 5 years of historical data
            hist = stock.history(period="5y")
            
            if len(hist) < 100:  # Need at least 100 days of data
                return None
            
            # Calculate approximate P/E history using price and estimated earnings
            # Note: This is simplified - in production, you'd use actual earnings history
            prices = hist["Close"]
            
            # Simulate P/E based on price movements (this is approximate)
            # In reality, you'd fetch actual historical earnings
            current_pe = stock.info.get("trailingPE", 20)
            pe_history = prices / prices.iloc[0] * current_pe * 0.8  # Rough approximation
            
            # Calculate statistics
            avg_pe = pe_history.mean()
            min_pe = pe_history.quantile(0.1)
            max_pe = pe_history.quantile(0.9)
            current_percentile = (pe_history.iloc[-1] - min_pe) / (max_pe - min_pe)
            
            return {
                "avg": avg_pe,
                "min": min_pe,
                "max": max_pe,
                "percentile": current_percentile
            }
            
        except Exception as e:
            print(f"Error getting historical P/E: {e}")
            return None
    
    def _compare_to_industry(self, pe: float, sector: str) -> Dict:
        """Compare P/E to industry average"""
        
        # Find best matching industry
        industry_avg = self.INDUVERAGE_PE.get(sector, 20.0)  # Default to 20 if unknown
        
        # Calculate percentile vs industry
        if industry_avg > 0:
            industry_percentile = pe / industry_avg
        else:
            industry_percentile = 1.0
        
        # Determine if P/E is high/low for industry
        if industry_percentile < 0.7:
            classification = "Low"
        elif industry_percentile < 1.3:
            classification = "Normal"
        else:
            classification = "High"
        
        return {
            "industry_avg": industry_avg,
            "percentile": industry_percentile,
            "classification": classification
        }
    
    def _analyze_peg_ratio(self, pe: float, eps_growth: Optional[float], 
                          peg_ratio: Optional[float]) -> Dict:
        """Analyze PEG ratio for growth-adjusted valuation"""
        
        if peg_ratio and peg_ratio > 0:
            peg = peg_ratio
        elif eps_growth and eps_growth > 0:
            # Calculate PEG if not provided
            peg = pe / (eps_growth * 100)
        else:
            return {
                "peg": None,
                "interpretation": "No growth data available",
                "score": 5  # Neutral
            }
        
        # Interpret PEG
        if peg < 0.5:
            interpretation = "Very Undervalued"
            score = 10
        elif peg < 1.0:
            interpretation = "Undervalued"
            score = 8
        elif peg < 1.5:
            interpretation = "Fair Value"
            score = 6
        elif peg < 2.0:
            interpretation = "Overvalued"
            score = 4
        else:
            interpretation = "Very Overvalued"
            score = 2
        
        return {
            "peg": peg,
            "interpretation": interpretation,
            "score": score
        }
    
    def _analyze_pe_trend(self, historical_pe: Optional[Dict]) -> Dict:
        """Analyze P/E trend over time"""
        
        if not historical_pe:
            return {
                "trend": "Unknown",
                "strength": 0,
                "direction": "neutral"
            }
        
        current_pe = historical_pe.get("current", historical_pe.get("avg", 20))
        avg_pe = historical_pe.get("avg", 20)
        
        # Calculate trend
        if current_pe > avg_pe * 1.2:
            trend = "Expanding"
            direction = "increasing"
            strength = min((current_pe / avg_pe - 1) * 5, 5)
        elif current_pe < avg_pe * 0.8:
            trend = "Contracting"
            direction = "decreasing"
            strength = min((1 - current_pe / avg_pe) * 5, 5)
        else:
            trend = "Stable"
            direction = "neutral"
            strength = 0
        
        return {
            "trend": trend,
            "strength": strength,
            "direction": direction
        }
    
    def _assess_valuation(self, trailing_pe: float, forward_pe: Optional[float],
                        industry_analysis: Dict, peg_analysis: Dict,
                        trend_analysis: Dict) -> Dict:
        """Overall valuation assessment"""
        
        score = 5  # Base score
        factors = []
        
        # Industry comparison (40% weight)
        industry_score = 5
        if industry_analysis["classification"] == "Low":
            industry_score = 8
            factors.append("Below industry average P/E")
        elif industry_analysis["classification"] == "High":
            industry_score = 3
            factors.append("Above industry average P/E")
        else:
            factors.append("P/E near industry average")
        
        score = score * 0.4 + industry_score * 0.4
        
        # PEG analysis (30% weight)
        peg_score = peg_analysis.get("score", 5)
        score = score * 0.7 + peg_score * 0.3
        factors.append(f"PEG: {peg_analysis.get('interpretation', 'N/A')}")
        
        # Trend analysis (30% weight)
        trend_strength = trend_analysis.get("strength", 0)
        if trend_analysis["direction"] == "decreasing":
            trend_score = 8 - trend_strength  # Lower P/E trend is good
            factors.append("P/E trend is favorable")
        elif trend_analysis["direction"] == "increasing":
            trend_score = 2 + trend_strength  # Higher P/E trend is concerning
            factors.append("P/E trend is concerning")
        else:
            trend_score = 5
            factors.append("P/E trend is stable")
        
        score = score * 0.7 + trend_score * 0.3
        
        # Determine valuation level
        if score >= 8:
            level = "Very Undervalued"
        elif score >= 6.5:
            level = "Undervalued"
        elif score >= 4.5:
            level = "Fair Value"
        elif score >= 3:
            level = "Overvalued"
        else:
            level = "Very Overvalued"
        
        return {
            "level": level,
            "score": round(score, 1),
            "factors": factors
        }
    
    def _estimate_fair_value(self, current_pe: float, sector: str, 
                           eps_growth: Optional[float]) -> Dict:
        """Estimate fair value P/E range"""
        
        # Base fair P/E on industry average
        industry_pe = self.INDUVERAGE_PE.get(sector, 20.0)
        
        # Adjust for growth
        if eps_growth and eps_growth > 0:
            growth_adjustment = min(eps_growth * 100 * 0.5, 20)  # Cap at 20 points
        else:
            growth_adjustment = -5  # Penalty for no growth
        
        # Calculate fair value range
        fair_pe_base = industry_pe + growth_adjustment
        fair_pe_low = fair_pe_base * 0.8
        fair_pe_high = fair_pe_base * 1.2
        
        return {
            "low": round(fair_pe_low, 1),
            "base": round(fair_pe_base, 1),
            "high": round(fair_pe_high, 1),
            "current_vs_fair": round(current_pe / fair_pe_base, 2)
        }
    
    def get_pe_summary(self, ticker: str) -> str:
        """Get human-readable P/E analysis summary"""
        
        analysis = self.analyze_pe_ratio(ticker)
        
        if analysis.get("error"):
            return f"❌ {ticker}: {analysis['error']}"
        
        pe = analysis["current_pe"]
        industry = analysis["industry_pe"]
        fair_value = analysis["fair_value_range"]
        
        summary = f"📊 {ticker} P/E Analysis:\n"
        summary += f"   Current P/E: {pe:.1f} (Industry: {industry:.1f})\n"
        summary += f"   vs Industry: {analysis['pe_vs_industry']:.1f}x ({analysis['industry_analysis']})\n"
        
        if analysis["peg_ratio"]:
            summary += f"   PEG Ratio: {analysis['peg_ratio']:.2f} ({analysis['peg_interpretation']})\n"
        
        summary += f"   Trend: {analysis['trend']} ({analysis['trend_strength']}/5)\n"
        summary += f"   Valuation: {analysis['valuation_level']} (Score: {analysis['valuation_score']}/10)\n"
        summary += f"   Fair Value P/E: {fair_value['low']}-{fair_value['high']}\n"
        summary += f"   Current vs Fair: {fair_value['current_vs_fair']:.1f}x"
        
        return summary
    
    def screen_by_pe(self, tickers: list, max_pe: float = 20, 
                    min_peg: Optional[float] = None) -> list:
        """Screen stocks by P/E criteria"""
        
        qualified = []
        
        for ticker in tickers:
            analysis = self.analyze_pe_ratio(ticker)
            
            if analysis.get("error"):
                continue
            
            pe = analysis["current_pe"]
            
            # Check P/E threshold
            if pe > max_pe:
                continue
            
            # Check PEG if specified
            if min_peg and analysis.get("peg_ratio"):
                if analysis["peg_ratio"] > min_peg:
                    continue
            
            qualified.append({
                "ticker": ticker,
                "pe": pe,
                "score": analysis["valuation_score"],
                "analysis": analysis
            })
        
        # Sort by score (highest first)
        qualified.sort(key=lambda x: x["score"], reverse=True)
        
        return qualified


# Test the analyzer
if __name__ == "__main__":
    analyzer = PERatioAnalyzer()
    
    # Test with some example stocks
    test_tickers = ["AAPL", "MSFT", "NVDA", "JPM", "XOM"]
    
    print("="*80)
    print("P/E RATIO ANALYZER TEST")
    print("="*80)
    
    for ticker in test_tickers:
        print("\n" + analyzer.get_pe_summary(ticker))
        print("-"*60)
