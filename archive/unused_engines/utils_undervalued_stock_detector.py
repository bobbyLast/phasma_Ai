"""
Undervalued Stock Detector
Identifies deeply undervalued stocks with 10x+ potential
Analyzes business models, TAM penetration, early catalysts, and future scenarios
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import sqlite3
import re


class UndervaluedStockDetector:
    """Detects hidden gems with massive upside potential"""
    
    # Disruptive sectors with high multiplier potential
    DISRUPTIVE_SECTORS = {
        "AI/ML": ["Artificial Intelligence", "Machine Learning", "Neural Networks"],
        "Biotech": ["Biotechnology", "Pharmaceuticals", "Gene Therapy", "CRISPR"],
        "Clean Energy": ["Solar", "Wind", "Hydrogen", "Battery Technology"],
        "Fintech": ["Financial Technology", "Digital Payments", "Blockchain"],
        "EV/Autonomous": ["Electric Vehicle", "Autonomous Driving", "Battery"],
        "Cloud/Infrastructure": ["Cloud Computing", "Data Centers", "Semiconductors"],
        "Space Tech": ["Space", "Satellite", "Aerospace"],
        "Quantum": ["Quantum Computing", "Quantum Technology"]
    }
    
    # Early catalyst signals
    CATALYST_TYPES = [
        "FDA Approval", "Patent Granted", "Major Contract", "Partnership",
        "Product Launch", "Regulatory Approval", "Clinical Trial Success",
        "Government Contract", "Strategic Investment", "Market Expansion"
    ]
    
    def __init__(self):
        self.cache = {}
        self.cache_expiry = 3600  # 1 hour cache
        
    def analyze_undervaluation(self, ticker: str) -> Dict:
        """Comprehensive analysis to detect deep undervaluation"""
        
        try:
            # Get stock data
            stock = yf.Ticker(ticker)
            info = stock.info
            
            # Basic metrics
            current_price = info.get("currentPrice", 0)
            market_cap = info.get("marketCap", 0)
            revenue = info.get("totalRevenue", 0)
            book_value = info.get("bookValue", 0)
            
            # Skip if too large (already discovered)
            if market_cap > 10_000_000_000:  # $10B+
                return {
                    "ticker": ticker,
                    "error": "Market cap too large for hidden gem analysis",
                    "potential_score": 0
                }
            
            # Analyze business model and disruption potential
            business_analysis = self._analyze_business_model(info)
            
            # Calculate valuation metrics
            valuation = self._calculate_valuation_metrics(info)
            
            # Assess growth runway
            growth_analysis = self._analyze_growth_runway(info, stock)
            
            # Detect early catalysts
            catalysts = self._detect_early_catalysts(ticker, info)
            
            # Estimate future potential
            future_scenarios = self._model_future_potential(info, business_analysis)
            
            # Calculate 10x potential score
            potential_score = self._calculate_potential_score(
                business_analysis, valuation, growth_analysis, catalysts, future_scenarios
            )
            
            result = {
                "ticker": ticker,
                "current_price": current_price,
                "market_cap": market_cap / 1e9,  # In billions
                "business_model": business_analysis,
                "valuation": valuation,
                "growth": growth_analysis,
                "catalysts": catalysts,
                "future_scenarios": future_scenarios,
                "potential_score": potential_score,
                "analysis_date": datetime.now().isoformat()
            }
            
            return result
            
        except Exception as e:
            return {
                "ticker": ticker,
                "error": str(e),
                "potential_score": 0
            }
    
    def _analyze_business_model(self, info: Dict) -> Dict:
        """Analyze business model quality and disruption potential"""
        
        sector = info.get("sector", "")
        industry = info.get("industry", "")
        business_summary = info.get("longBusinessSummary", "")
        
        # Identify disruptive sector
        disruption_category = None
        disruption_score = 0
        
        for category, keywords in self.DISRUPTIVE_SECTORS.items():
            if any(keyword in business_summary for keyword in keywords):
                disruption_category = category
                disruption_score = 8
                break
        
        # Check for competitive moat indicators
        moat_keywords = ["patent", "proprietary", "network effect", "switching costs", 
                        "regulatory", "license", "franchise", "brand"]
        moat_score = sum(1 for keyword in moat_keywords if keyword in business_summary.lower())
        
        # TAM analysis clues
        tam_indicators = ["total addressable market", "TAM", "market opportunity", 
                         "billion dollar market", "$", "market size"]
        tam_score = sum(1 for indicator in tam_indicators if indicator in business_summary.lower())
        
        # Business model quality
        if "subscription" in business_summary.lower() or "recurring" in business_summary.lower():
            model_quality = 8
        elif "platform" in business_summary.lower():
            model_quality = 7
        elif "SaaS" in business_summary:
            model_quality = 9
        else:
            model_quality = 5
        
        return {
            "sector": sector,
            "industry": industry,
            "disruption_category": disruption_category,
            "disruption_score": disruption_score,
            "moat_score": min(moat_score * 2, 10),
            "tam_score": min(tam_score, 10),
            "model_quality": model_quality,
            "summary": business_summary[:500] + "..." if len(business_summary) > 500 else business_summary
        }
    
    def _calculate_valuation_metrics(self, info: Dict) -> Dict:
        """Calculate comprehensive valuation metrics"""
        
        # Basic metrics
        pe_ratio = info.get("trailingPE", None)
        pb_ratio = info.get("priceToBook", None)
        ps_ratio = info.get("priceToSales", None)
        ev_revenue = info.get("enterpriseToRevenue", None)
        
        # Cash and debt
        cash_per_share = info.get("totalCashPerShare", 0)
        debt_to_equity = info.get("debtToEquity", 0)
        
        # Growth metrics
        revenue_growth = info.get("revenueGrowth", 0)
        earnings_growth = info.get("earningsGrowth", 0)
        
        # Calculate undervaluation score
        score = 5  # Base score
        
        # P/E analysis (if profitable)
        if pe_ratio and pe_ratio > 0:
            if pe_ratio < 15:
                score += 2
            elif pe_ratio < 25:
                score += 1
            elif pe_ratio > 50:
                score -= 1
        
        # P/B analysis (asset backing)
        if pb_ratio and pb_ratio > 0:
            if pb_ratio < 1.5:
                score += 2
            elif pb_ratio < 3:
                score += 1
        
        # P/S analysis (early stage companies)
        if ps_ratio and ps_ratio > 0:
            if ps_ratio < 2:
                score += 2
            elif ps_ratio < 5:
                score += 1
        
        # Cash position
        if cash_per_share and cash_per_share > 5:
            score += 1
        
        # Low debt
        if debt_to_equity and debt_to_equity < 0.5:
            score += 1
        
        # High growth justifies higher valuation
        if revenue_growth and revenue_growth > 0.5:  # 50%+ growth
            score += 2
        elif revenue_growth and revenue_growth > 0.2:  # 20%+ growth
            score += 1
        
        return {
            "pe_ratio": pe_ratio,
            "pb_ratio": pb_ratio,
            "ps_ratio": ps_ratio,
            "ev_revenue": ev_revenue,
            "cash_per_share": cash_per_share,
            "debt_to_equity": debt_to_equity,
            "revenue_growth": revenue_growth,
            "earnings_growth": earnings_growth,
            "undervaluation_score": min(score, 10)
        }
    
    def _analyze_growth_runway(self, info: Dict, stock) -> Dict:
        """Analyze growth runway and market penetration"""
        
        market_cap = info.get("marketCap", 0)
        revenue = info.get("totalRevenue", 0)
        sector = info.get("sector", "")
        
        # Estimate TAM based on sector
        tam_estimates = {
            "Technology": 5_000_000_000_000,  # $5T
            "Biotechnology": 3_000_000_000_000,  # $3T
            "Energy": 4_000_000_000_000,  # $4T
            "Financial": 8_000_000_000_000,  # $8T
            "Healthcare": 4_000_000_000_000,  # $4T
            "Consumer": 6_000_000_000_000,  # $6T
            "Industrial": 3_000_000_000_000,  # $3T
        }
        
        tam = tam_estimates.get(sector, 1_000_000_000_000)  # Default $1T
        
        # Calculate penetration
        if revenue > 0:
            penetration = revenue / tam
        else:
            penetration = 0
        
        # Growth runway score
        if penetration < 0.001:  # < 0.1% penetration
            runway_score = 10
        elif penetration < 0.01:  # < 1% penetration
            runway_score = 8
        elif penetration < 0.05:  # < 5% penetration
            runway_score = 6
        elif penetration < 0.1:  # < 10% penetration
            runway_score = 4
        else:
            runway_score = 2
        
        # Recent growth trend
        try:
            hist = stock.history(period="1y")
            if len(hist) > 50:
                recent_revenue_growth = self._estimate_revenue_growth(hist)
            else:
                recent_revenue_growth = 0
        except:
            recent_revenue_growth = 0
        
        return {
            "estimated_tam": tam / 1e9,  # In billions
            "current_penetration": penetration * 100,  # As percentage
            "runway_score": runway_score,
            "recent_growth": recent_revenue_growth
        }
    
    def _detect_early_catalysts(self, ticker: str, info: Dict) -> Dict:
        """Detect early catalysts that could trigger price explosion"""
        
        catalysts = []
        
        # Check for recent news (simplified - in production, use news API)
        catalyst_score = 0
        
        # Insider accumulation as catalyst
        insider_signals = self._get_insider_signals(ticker)
        if insider_signals.get("accumulating", False):
            catalysts.append("Insider Accumulation")
            catalyst_score += 3
        
        # Recent partnership/investment
        if "partnership" in info.get("longBusinessSummary", "").lower():
            catalysts.append("Strategic Partnerships")
            catalyst_score += 2
        
        # Regulatory approvals (for biotech)
        if info.get("sector") == "Biotechnology":
            catalysts.append("FDA Pipeline")
            catalyst_score += 2
        
        # Product launches
        if "launch" in info.get("longBusinessSummary", "").lower():
            catalysts.append("Product Launch")
            catalyst_score += 2
        
        # Patent activity
        if "patent" in info.get("longBusinessSummary", "").lower():
            catalysts.append("Patent Portfolio")
            catalyst_score += 1
        
        return {
            "identified_catalysts": catalysts,
            "catalyst_score": min(catalyst_score, 10),
            "insider_signals": insider_signals
        }
    
    def _model_future_potential(self, info: Dict, business_analysis: Dict) -> Dict:
        """Model future price scenarios"""
        
        current_price = info.get("currentPrice", 0)
        revenue = info.get("totalRevenue", 0)
        revenue_growth = info.get("revenueGrowth", 0.2)  # Default 20%
        
        # Base case scenario (conservative)
        base_growth = min(revenue_growth, 0.3)  # Cap at 30%
        base_price = current_price * (1 + base_growth * 3)  # 3 years
        
        # Best case scenario (optimistic)
        if business_analysis.get("disruption_score", 0) > 7:
            best_growth = min(revenue_growth * 2, 0.5)  # Up to 50%
            best_price = current_price * (1 + best_growth * 5)  # 5 years
        else:
            best_growth = min(revenue_growth * 1.5, 0.4)
            best_price = current_price * (1 + best_growth * 4)
        
        # Bear case scenario
        bear_price = current_price * 0.7  # 30% decline
        
        # Probability weights
        base_probability = 0.6
        best_probability = 0.2
        bear_probability = 0.2
        
        # Expected value
        expected_price = (base_price * base_probability + 
                         best_price * best_probability + 
                         bear_price * bear_probability)
        
        # Upside potential
        upside_potential = (best_price - current_price) / current_price
        
        return {
            "current_price": current_price,
            "base_case": {
                "price": base_price,
                "return": (base_price - current_price) / current_price,
                "probability": base_probability
            },
            "best_case": {
                "price": best_price,
                "return": (best_price - current_price) / current_price,
                "probability": best_probability
            },
            "bear_case": {
                "price": bear_price,
                "return": (bear_price - current_price) / current_price,
                "probability": bear_probability
            },
            "expected_price": expected_price,
            "expected_return": (expected_price - current_price) / current_price,
            "upside_potential": upside_potential
        }
    
    def _calculate_potential_score(self, business: Dict, valuation: Dict, 
                                  growth: Dict, catalysts: Dict, scenarios: Dict) -> Dict:
        """Calculate overall 10x potential score"""
        
        # Component scores (0-10)
        business_score = business.get("disruption_score", 0)
        valuation_score = valuation.get("undervaluation_score", 0)
        growth_score = growth.get("runway_score", 0)
        catalyst_score = catalysts.get("catalyst_score", 0)
        
        # Scenario score based on upside potential
        upside = scenarios.get("upside_potential", 0)
        if upside > 10:  # 10x+ potential
            scenario_score = 10
        elif upside > 5:  # 5x+ potential
            scenario_score = 8
        elif upside > 3:  # 3x+ potential
            scenario_score = 6
        elif upside > 2:  # 2x+ potential
            scenario_score = 4
        else:
            scenario_score = 2
        
        # Weighted average
        weights = {
            "business": 0.25,
            "valuation": 0.20,
            "growth": 0.20,
            "catalysts": 0.15,
            "scenarios": 0.20
        }
        
        total_score = (
            business_score * weights["business"] +
            valuation_score * weights["valuation"] +
            growth_score * weights["growth"] +
            catalyst_score * weights["catalysts"] +
            scenario_score * weights["scenarios"]
        )
        
        # Determine potential category
        if total_score >= 8.5:
            category = "Exceptional (10x+ Potential)"
        elif total_score >= 7:
            category = "Excellent (5-10x Potential)"
        elif total_score >= 5.5:
            category = "Good (3-5x Potential)"
        elif total_score >= 4:
            category = "Moderate (2-3x Potential)"
        else:
            category = "Limited (<2x Potential)"
        
        return {
            "total_score": round(total_score, 1),
            "category": category,
            "component_scores": {
                "business": business_score,
                "valuation": valuation_score,
                "growth": growth_score,
                "catalysts": catalyst_score,
                "scenarios": scenario_score
            }
        }
    
    def _estimate_revenue_growth(self, hist_data) -> float:
        """Estimate revenue growth from price history (proxy)"""
        try:
            # Use price growth as revenue proxy (simplified)
            prices = hist_data["Close"]
            if len(prices) > 100:
                recent_growth = (prices.iloc[-1] / prices.iloc[-100] - 1) / (100/252)  # Annualized
                return max(recent_growth, 0)
        except:
            pass
        return 0
    
    def _get_insider_signals(self, ticker: str) -> Dict:
        """Get insider trading signals (simplified)"""
        # In production, this would query insider trading database
        # For now, return neutral
        return {
            "accumulating": False,
            "recent_buys": 0,
            "confidence": 5
        }
    
    def screen_hidden_gems(self, tickers: List[str], min_score: float = 7.0) -> List[Dict]:
        """Screen for hidden gems with high potential"""
        
        gems = []
        
        for ticker in tickers:
            analysis = self.analyze_undervaluation(ticker)
            
            if analysis.get("error"):
                continue
            
            score = analysis.get("potential_score", {}).get("total_score", 0)
            
            if score >= min_score:
                gems.append(analysis)
        
        # Sort by score (highest first)
        gems.sort(key=lambda x: x["potential_score"]["total_score"], reverse=True)
        
        return gems
    
    def get_analysis_summary(self, ticker: str) -> str:
        """Get human-readable analysis summary"""
        
        analysis = self.analyze_undervaluation(ticker)
        
        if analysis.get("error"):
            return f"❌ {ticker}: {analysis['error']}"
        
        price = analysis["current_price"]
        market_cap = analysis["market_cap"]
        potential = analysis["potential_score"]
        
        summary = f"💎 {ticker} - Hidden Gem Analysis:\n"
        summary += f"   Price: ${price:.2f} | Market Cap: ${market_cap:.1f}B\n"
        summary += f"   Potential Score: {potential['total_score']}/10\n"
        summary += f"   Category: {potential['category']}\n\n"
        
        # Business model
        business = analysis["business_model"]
        summary += f"🏢 Business Model:\n"
        summary += f"   Sector: {business['sector']}\n"
        if business.get("disruption_category"):
            summary += f"   Disruption: {business['disruption_category']} ({business['disruption_score']}/10)\n"
        summary += f"   Moat Score: {business['moat_score']}/10\n"
        summary += f"   Model Quality: {business['model_quality']}/10\n\n"
        
        # Valuation
        valuation = analysis["valuation"]
        summary += f"💰 Valuation:\n"
        if valuation.get("pe_ratio"):
            summary += f"   P/E: {valuation['pe_ratio']:.1f}\n"
        if valuation.get("ps_ratio"):
            summary += f"   P/S: {valuation['ps_ratio']:.1f}\n"
        summary += f"   Undervaluation Score: {valuation['undervaluation_score']}/10\n\n"
        
        # Growth
        growth = analysis["growth"]
        summary += f"📈 Growth Runway:\n"
        summary += f"   TAM Penetration: {growth['current_penetration']:.2f}%\n"
        summary += f"   Runway Score: {growth['runway_score']}/10\n\n"
        
        # Catalysts
        catalysts = analysis["catalysts"]
        if catalysts["identified_catalysts"]:
            summary += f"🚀 Catalysts: {', '.join(catalysts['identified_catalysts'])}\n"
            summary += f"   Catalyst Score: {catalysts['catalyst_score']}/10\n\n"
        
        # Future scenarios
        scenarios = analysis["future_scenarios"]
        summary += f"🔮 Future Potential:\n"
        summary += f"   Base Case: {scenarios['base_case']['return']*100:.0f}% return\n"
        summary += f"   Best Case: {scenarios['best_case']['return']*100:.0f}% return\n"
        summary += f"   Expected Return: {scenarios['expected_return']*100:.0f}%\n"
        summary += f"   Upside Potential: {scenarios['upside_potential']*100:.0f}%\n"
        
        return summary


# Test the detector
if __name__ == "__main__":
    detector = UndervaluedStockDetector()
    
    # Test with potential hidden gems
    test_tickers = ["PLUG", "NKLA", "RIVN", "LCID", "CHPT", "GOEV", "FSR"]
    
    print("="*80)
    print("UNDervalued STOCK DETECTOR TEST")
    print("="*80)
    print("\nSearching for hidden gems with 10x+ potential...\n")
    
    for ticker in test_tickers:
        print(detector.get_analysis_summary(ticker))
        print("="*60)
