"""
Early Investment System
Separate from main trading - identifies 5-10 year investment opportunities
Focus on secular trends and market transformation, not trading
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import sqlite3


class EarlyInvestmentSystem:
    """Identifies early-stage companies for 5-10 year investment horizon"""
    
    # Secular trends for long-term investment
    SECULAR_TRENDS = {
        "AI Revolution": {
            "keywords": ["artificial intelligence", "machine learning", "neural networks", "deep learning"],
            "market_size": 15_000_000_000_000,  # $15T by 2030
            "penetration_threshold": 0.02  # 2% = early stage
        },
        "Energy Transition": {
            "keywords": ["renewable energy", "solar", "wind", "hydrogen", "battery", "EV"],
            "market_size": 8_000_000_000_000,  # $8T by 2030
            "penetration_threshold": 0.05  # 5% = early stage
        },
        "Digital Healthcare": {
            "keywords": ["telemedicine", "digital health", "biotechnology", "genomics", "personalized medicine"],
            "market_size": 5_000_000_000_000,  # $5T by 2030
            "penetration_threshold": 0.03  # 3% = early stage
        },
        "Fintech Evolution": {
            "keywords": ["digital banking", "blockchain", "cryptocurrency", "digital payments", "defi"],
            "market_size": 7_000_000_000_000,  # $7T by 2030
            "penetration_threshold": 0.04  # 4% = early stage
        },
        "Autonomous Everything": {
            "keywords": ["autonomous vehicle", "self-driving", "robotics", "automation", "drone"],
            "market_size": 4_000_000_000_000,  # $4T by 2030
            "penetration_threshold": 0.01  # 1% = very early stage
        }
    }
    
    def __init__(self):
        self.db_path = "early_investments.db"
        self._init_database()
    
    def _init_database(self):
        """Initialize database for tracking early investments"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS early_opportunities (
                id INTEGER PRIMARY KEY,
                ticker TEXT UNIQUE NOT NULL,
                secular_trend TEXT NOT NULL,
                current_penetration REAL,
                projected_penetration_10y REAL,
            market_cap_current REAL,
            market_cap_potential_10y REAL,
            investment_thesis TEXT,
            key_metrics TEXT,
            risk_factors TEXT,
            last_updated TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS investment_progress (
                id INTEGER PRIMARY KEY,
                ticker TEXT,
                year INTEGER,
                actual_penetration REAL,
                market_cap REAL,
                milestones TEXT,
                FOREIGN KEY (ticker) REFERENCES early_opportunities(ticker)
            )
        """)
        
        conn.commit()
        conn.close()
    
    def analyze_early_investment(self, ticker: str) -> Dict:
        """Analyze a stock for 5-10 year investment potential"""
        
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            
            # Basic metrics
            current_price = info.get("currentPrice", 0)
            market_cap = info.get("marketCap", 0)
            revenue = info.get("totalRevenue", 0)
            
            # Skip if too large (not early stage)
            if market_cap > 5_000_000_000:  # $5B threshold
                return {
                    "ticker": ticker,
                    "error": "Market cap too large for early investment analysis",
                    "investment_score": 0
                }
            
            # Identify secular trend
            trend_analysis = self._identify_secular_trend(info)
            
            if not trend_analysis["trend"]:
                return {
                    "ticker": ticker,
                    "error": "Not aligned with major secular trends",
                    "investment_score": 0
                }
            
            # Calculate market penetration
            penetration = self._calculate_market_penetration(revenue, trend_analysis)
            
            # Assess long-term potential
            potential = self._assess_10y_potential(info, trend_analysis, penetration)
            
            # Build investment thesis
            thesis = self._build_investment_thesis(ticker, info, trend_analysis, potential)
            
            # Calculate investment score (0-100)
            score = self._calculate_investment_score(trend_analysis, penetration, potential)
            
            result = {
                "ticker": ticker,
                "current_price": current_price,
                "market_cap_b": market_cap / 1e9,
                "secular_trend": trend_analysis["trend"],
                "trend_score": trend_analysis["score"],
                "current_penetration_pct": penetration["current"] * 100,
                "projected_penetration_10y_pct": penetration["projected_10y"] * 100,
                "potential_10x": potential["potential_10x"],
                "investment_score": score,
                "thesis": thesis,
                "time_horizon": "5-10 years",
                "risk_level": self._assess_risk_level(info, penetration)
            }
            
            # Save to database
            self._save_opportunity(result)
            
            return result
            
        except Exception as e:
            return {
                "ticker": ticker,
                "error": str(e),
                "investment_score": 0
            }
    
    def _identify_secular_trend(self, info: Dict) -> Dict:
        """Identify which secular trend the company belongs to"""
        
        business_summary = info.get("longBusinessSummary", "").lower()
        sector = info.get("sector", "")
        industry = info.get("industry", "")
        
        best_trend = None
        best_score = 0
        
        for trend_name, trend_data in self.SECULAR_TRENDS.items():
            score = 0
            
            # Check keywords in business summary
            for keyword in trend_data["keywords"]:
                if keyword in business_summary:
                    score += 3
            
            # Check sector/industry alignment
            if any(kw in sector.lower() for kw in trend_data["keywords"][:2]):
                score += 2
            if any(kw in industry.lower() for kw in trend_data["keywords"][:2]):
                score += 2
            
            if score > best_score:
                best_score = score
                best_trend = trend_name
        
        if best_trend and best_score >= 3:
            return {
                "trend": best_trend,
                "score": min(best_score, 10),
                "market_size": self.SECULAR_TRENDS[best_trend]["market_size"],
                "threshold": self.SECULAR_TRENDS[best_trend]["penetration_threshold"]
            }
        
        return {"trend": None, "score": 0}
    
    def _calculate_market_penetration(self, revenue: float, trend_analysis: Dict) -> Dict:
        """Calculate current and projected market penetration"""
        
        market_size = trend_analysis["market_size"]
        current_penetration = revenue / market_size if revenue > 0 else 0
        
        # Project 10-year penetration based on growth stage
        if current_penetration < 0.001:  # < 0.1%
            projected_10y = 0.05  # Could reach 5%
        elif current_penetration < 0.01:  # < 1%
            projected_10y = 0.10  # Could reach 10%
        elif current_penetration < 0.05:  # < 5%
            projected_10y = 0.20  # Could reach 20%
        else:
            projected_10y = min(current_penetration * 3, 0.50)  # Max 50%
        
        return {
            "current": current_penetration,
            "projected_10y": projected_10y,
            "growth_potential": projected_10y / current_penetration if current_penetration > 0 else 100
        }
    
    def _assess_10y_potential(self, info: Dict, trend_analysis: Dict, penetration: Dict) -> Dict:
        """Assess 10-year potential based on market penetration growth"""
        
        current_market_cap = info.get("marketCap", 0)
        market_size = trend_analysis["market_size"]
        projected_penetration = penetration["projected_10y"]
        
        # Potential market cap at 10% market share of trend
        potential_market_cap = market_size * projected_penetration * 0.10  # Assuming 10% market share
        
        # Calculate potential multiple
        potential_10x = potential_market_cap / current_market_cap if current_market_cap > 0 else 0
        
        # Realistic adjustment (not everyone gets 10% market share)
        realistic_multiple = potential_10x * 0.3  # 30% chance of achieving
        
        return {
            "potential_market_cap_b": potential_market_cap / 1e9,
            "potential_10x": potential_10x,
            "realistic_multiple": realistic_multiple,
            "is_10x_candidate": realistic_multiple >= 10
        }
    
    def _build_investment_thesis(self, ticker: str, info: Dict, trend_analysis: Dict, potential: Dict) -> Dict:
        """Build comprehensive investment thesis"""
        
        secular_trend = trend_analysis["trend"]
        current_penetration = penetration["current"] * 100
        
        thesis = {
            "title": f"{ticker}: Early Investment in {secular_trend}",
            "summary": f"{ticker} is positioned at the forefront of the {secular_trend}, "
                     f"currently capturing less than {current_penetration:.1f}% of a "
                     f"${trend_analysis['market_size']/1e12:.1f} trillion market.",
            
            "opportunity": {
                "market_size": f"${trend_analysis['market_size']/1e12:.1f}T by 2030",
                "current_penetration": f"{current_penetration:.2f}%",
                "growth_stage": self._determine_growth_stage(current_penetration),
                "competitive_advantage": self._identify_moat(info)
            },
            
            "catalysts": self._identify_10y_catalysts(info, secular_trend),
            
            "risks": self._identify_long_term_risks(info),
            
            "potential_outcomes": {
                "bear_case": f"2-3x return (10% market penetration)",
                "base_case": f"5-7x return (20% market penetration)",
                "best_case": f"10-15x return (30%+ market penetration)"
            }
        }
        
        return thesis
    
    def _calculate_investment_score(self, trend_analysis: Dict, penetration: Dict, potential: Dict) -> int:
        """Calculate investment score from 0-100"""
        
        score = 0
        
        # Trend alignment (30 points)
        score += trend_analysis["score"] * 3
        
        # Early stage bonus (30 points)
        if penetration["current"] < 0.001:  # < 0.1%
            score += 30
        elif penetration["current"] < 0.01:  # < 1%
            score += 25
        elif penetration["current"] < 0.05:  # < 5%
            score += 20
        else:
            score += 10
        
        # 10x potential (40 points)
        if potential["potential_10x"] >= 100:
            score += 40
        elif potential["potential_10x"] >= 50:
            score += 30
        elif potential["potential_10x"] >= 20:
            score += 20
        elif potential["potential_10x"] >= 10:
            score += 10
        
        return min(score, 100)
    
    def _determine_growth_stage(self, penetration_pct: float) -> str:
        """Determine growth stage based on penetration"""
        if penetration_pct < 0.1:
            return "Pre-Inflection"
        elif penetration_pct < 1:
            return "Early Adoption"
        elif penetration_pct < 5:
            return "Early Growth"
        else:
            return "Growth Stage"
    
    def _identify_moat(self, info: Dict) -> str:
        """Identify competitive moat"""
        summary = info.get("longBusinessSummary", "").lower()
        
        if "patent" in summary:
            return "Patent protection"
        elif "network effect" in summary or "platform" in summary:
            return "Network effects"
        elif "proprietary" in summary:
            return "Proprietary technology"
        elif "regulatory" in summary:
            return "Regulatory advantages"
        else:
            return "First-mover advantage"
    
    def _identify_10y_catalysts(self, info: Dict, trend: str) -> List[str]:
        """Identify 10-year catalysts"""
        catalysts = []
        
        # Trend-specific catalysts
        if "AI" in trend:
            catalysts.extend([
                "AI adoption across enterprises",
                "Regulatory framework establishment",
                "Hardware cost reduction"
            ])
        elif "Energy" in trend:
            catalysts.extend([
                "Government climate initiatives",
                "Battery technology breakthroughs",
                "Grid modernization"
            ])
        elif "Healthcare" in trend:
            catalysts.extend([
                "FDA digital health approval",
                "Aging population demand",
                "Healthcare cost pressures"
            ])
        
        # Universal catalysts
        catalysts.extend([
            "Market education and awareness",
            "Infrastructure development",
            "Economies of scale achievement"
        ])
        
        return catalysts[:5]  # Top 5 catalysts
    
    def _identify_long_term_risks(self, info: Dict) -> List[str]:
        """Identify long-term risks"""
        risks = []
        
        # Common risks
        risks.extend([
            "Execution risk over decade",
            "Technological disruption",
            "Regulatory changes",
            "Capital intensity requirements",
            "Competitive landscape evolution"
        ])
        
        return risks
    
    def _assess_risk_level(self, info: Dict, penetration: Dict) -> str:
        """Assess risk level"""
        market_cap = info.get("marketCap", 0)
        
        if market_cap < 500_000_000 and penetration["current"] < 0.001:
            return "Very High"
        elif market_cap < 1_000_000_000:
            return "High"
        elif market_cap < 2_000_000_000:
            return "Medium"
        else:
            return "Moderate"
    
    def _save_opportunity(self, result: Dict):
        """Save opportunity to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO early_opportunities 
            (ticker, secular_trend, current_penetration, projected_penetration_10y,
             market_cap_current, market_cap_potential_10y, investment_thesis, 
             key_metrics, risk_factors)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            result["ticker"],
            result["secular_trend"],
            result["current_penetration_pct"] / 100,
            result["projected_penetration_10y_pct"] / 100,
            result["market_cap_b"],
            result["potential_10x"],
            str(result["thesis"]),
            f"Score: {result['investment_score']}/100",
            result["risk_level"]
        ))
        
        conn.commit()
        conn.close()
    
    def get_investment_summary(self, ticker: str) -> str:
        """Get human-readable investment summary"""
        
        analysis = self.analyze_early_investment(ticker)
        
        if analysis.get("error"):
            return f"❌ {ticker}: {analysis['error']}"
        
        return f"""
🚀 {ticker} - Early Investment Opportunity (5-10 Year Horizon)

📊 Current Status:
   Price: ${analysis['current_price']:.2f}
   Market Cap: ${analysis['market_cap_b']:.1f}B
   Investment Score: {analysis['investment_score']}/100

🌍 Secular Trend: {analysis['secular_trend']}
   Current Market Penetration: {analysis['current_penetration_pct']:.2f}%
   Projected 10Y Penetration: {analysis['projected_penetration_10y_pct']:.1f}%
   10X Potential: {analysis['potential_10x']:.1f}x

📈 Investment Thesis:
   {analysis['thesis']['summary']}

⚠️ Risk Level: {analysis['risk_level']}
   Time Horizon: 5-10 years
   This is NOT a trading recommendation - it's a long-term investment analysis
        """


# Test the system
if __name__ == "__main__":
    system = EarlyInvestmentSystem()
    
    # Test with potential early stage companies
    test_stocks = ["PLUG", "CHPT", "NKLA", "RIVN", "LCID"]
    
    print("="*80)
    print("EARLY INVESTMENT SYSTEM")
    print("="*80)
    print("\nAnalyzing 5-10 year investment opportunities...\n")
    
    for ticker in test_stocks:
        print(system.get_investment_summary(ticker))
        print("="*60)
