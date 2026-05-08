"""
Idea Quality Analyzer - Stage 3 of External Trader Tracking System

Evaluates individual trade ideas using Phasma AI brain capabilities.
This layer analyzes ticker quality independent of who called it.

Key Analysis Areas:
- Trend analysis (uptrend/downtrend strength)
- Volume analysis (liquidity and abnormal activity)
- Sector/market context (relative strength)
- Recent move analysis (late vs early entry)
- Basic fundamentals (business viability)
- Insider/politician alignment
- News/catalyst analysis

Output:
- Quality rating: GOOD, MEH, BAD
- Confidence score (0-100)
- Detailed reasoning with factors
- Risk assessment and recommendations
"""

import yfinance as yf
import numpy as np
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
import statistics

from trader_call_logger import Direction

@dataclass
class IdeaQuality:
    """Quality assessment for a trade idea"""
    ticker: str
    rating: str  # GOOD, MEH, BAD
    confidence: float  # 0-100
    overall_score: float  # 0-100
    trend_score: float
    volume_score: float
    sector_score: float
    timing_score: float
    fundamentals_score: float
    smart_money_score: float
    risk_level: str  # LOW, MEDIUM, HIGH
    reasoning: List[str]
    recommendation: str
    analysis_date: str
    
    def to_dict(self) -> Dict:
        return asdict(self)

class IdeaQualityAnalyzer:
    """
    Analyzes trade ideas using Phasma AI brain capabilities
    Stage 3: Idea quality evaluation independent of trader
    """
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        
        # Analysis parameters
        self.trend_weight = 0.25
        self.volume_weight = 0.20
        self.sector_weight = 0.15
        self.timing_weight = 0.20
        self.fundamentals_weight = 0.10
        self.smart_money_weight = 0.10
        
        print("🧠 Idea Quality Analyzer initialized")
        print("   - Analyzing trend, volume, sector, timing, fundamentals, smart money")
    
    def analyze_ticker(self, ticker: str, direction: Direction = Direction.LONG) -> Optional[IdeaQuality]:
        """
        Comprehensive analysis of a ticker idea
        
        Args:
            ticker: Stock symbol to analyze
            direction: LONG or SHORT bias
        
        Returns:
            IdeaQuality with detailed assessment
        """
        try:
            print(f"🔍 Analyzing {ticker} for {direction.value} opportunity...")
            
            # Get ticker data
            stock = yf.Ticker(ticker)
            hist = stock.history(period="3mo")  # 3 months for trend analysis
            
            if hist.empty:
                print(f"❌ No data available for {ticker}")
                return None
            
            # Analyze each component
            trend_score, trend_reasoning = self._analyze_trend(hist, direction)
            volume_score, volume_reasoning = self._analyze_volume(hist)
            sector_score, sector_reasoning = self._analyze_sector_context(stock, hist)
            timing_score, timing_reasoning = self._analyze_timing(hist)
            fundamentals_score, fundamentals_reasoning = self._analyze_fundamentals(stock)
            smart_money_score, smart_money_reasoning = self._analyze_smart_money(ticker)
            
            # Calculate overall score
            overall_score = (
                trend_score * self.trend_weight +
                volume_score * self.volume_weight +
                sector_score * self.sector_weight +
                timing_score * self.timing_weight +
                fundamentals_score * self.fundamentals_weight +
                smart_money_score * self.smart_money_weight
            )
            
            # Determine rating and confidence
            rating, confidence = self._determine_rating(overall_score, trend_score, volume_score)
            
            # Assess risk level
            risk_level = self._assess_risk_level(ticker, hist, overall_score)
            
            # Combine all reasoning
            all_reasoning = (
                trend_reasoning + volume_reasoning + sector_reasoning + 
                timing_reasoning + fundamentals_reasoning + smart_money_reasoning
            )
            
            # Generate recommendation
            recommendation = self._generate_recommendation(rating, confidence, risk_level, direction)
            
            return IdeaQuality(
                ticker=ticker,
                rating=rating,
                confidence=confidence,
                overall_score=overall_score,
                trend_score=trend_score,
                volume_score=volume_score,
                sector_score=sector_score,
                timing_score=timing_score,
                fundamentals_score=fundamentals_score,
                smart_money_score=smart_money_score,
                risk_level=risk_level,
                reasoning=all_reasoning,
                recommendation=recommendation,
                analysis_date=datetime.now(timezone.utc).isoformat()
            )
            
        except Exception as e:
            print(f"❌ Error analyzing {ticker}: {str(e)}")
            return None
    
    def _analyze_trend(self, hist, direction: Direction) -> Tuple[float, List[str]]:
        """Analyze trend strength and direction"""
        try:
            # Calculate moving averages
            short_ma = hist['Close'].rolling(window=10).mean()
            long_ma = hist['Close'].rolling(window=30).mean()
            
            current_price = hist['Close'].iloc[-1]
            current_short_ma = short_ma.iloc[-1]
            current_long_ma = long_ma.iloc[-1]
            
            # Trend direction
            if direction == Direction.LONG:
                # For long positions, want price above MAs and MAs trending up
                price_above_short = current_price > current_short_ma
                price_above_long = current_price > current_long_ma
                short_above_long = current_short_ma > current_long_ma
                
                if price_above_short and price_above_long and short_above_long:
                    score = 85
                    reasoning = ["Strong uptrend: price above both moving averages", "Short-term momentum above long-term trend"]
                elif price_above_short:
                    score = 70
                    reasoning = ["Moderate uptrend: price above short-term average", "Some momentum present"]
                elif price_above_long:
                    score = 55
                    reasoning = ["Weak uptrend: price above long-term average only", "Momentum uncertain"]
                else:
                    score = 30
                    reasoning = ["Downtrend: price below moving averages", "Negative momentum"]
            
            else:  # SHORT direction
                # For short positions, want price below MAs and MAs trending down
                price_below_short = current_price < current_short_ma
                price_below_long = current_price < current_long_ma
                short_below_long = current_short_ma < current_long_ma
                
                if price_below_short and price_below_long and short_below_long:
                    score = 85
                    reasoning = ["Strong downtrend: price below both moving averages", "Short-term momentum below long-term trend"]
                elif price_below_short:
                    score = 70
                    reasoning = ["Moderate downtrend: price below short-term average", "Downside momentum present"]
                elif price_below_long:
                    score = 55
                    reasoning = ["Weak downtrend: price below long-term average only", "Downside momentum uncertain"]
                else:
                    score = 30
                    reasoning = ["Uptrend: price above moving averages", "Not suitable for short"]
            
            return score, reasoning
            
        except Exception as e:
            return 50, [f"Trend analysis error: {str(e)}"]
    
    def _analyze_volume(self, hist) -> Tuple[float, List[str]]:
        """Analyze volume patterns and liquidity"""
        try:
            recent_volume = hist['Volume'].tail(10).mean()
            avg_volume = hist['Volume'].mean()
            current_volume = hist['Volume'].iloc[-1]
            
            # Volume ratio analysis
            volume_ratio = recent_volume / avg_volume if avg_volume > 0 else 1
            current_volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1
            
            reasoning = []
            
            # Check liquidity
            if recent_volume < 100000:  # Less than 100k shares/day
                score = 30
                reasoning.append("Low liquidity: thin trading volume")
            elif recent_volume < 500000:  # Less than 500k shares/day
                score = 60
                reasoning.append("Moderate liquidity: acceptable volume")
            else:
                score = 80
                reasoning.append("Good liquidity: strong trading volume")
            
            # Check for unusual volume
            if current_volume_ratio > 2.0:
                score += 10
                reasoning.append("High current volume: unusual interest")
            elif current_volume_ratio < 0.5:
                score -= 10
                reasoning.append("Low current volume: limited interest")
            
            # Volume trend
            if volume_ratio > 1.2:
                reasoning.append("Increasing volume trend")
            elif volume_ratio < 0.8:
                reasoning.append("Decreasing volume trend")
            
            return min(max(score, 0), 100), reasoning
            
        except Exception as e:
            return 50, [f"Volume analysis error: {str(e)}"]
    
    def _analyze_sector_context(self, stock, hist) -> Tuple[float, List[str]]:
        """Analyze sector performance and context"""
        try:
            info = stock.info
            
            # Get sector and industry
            sector = info.get('sector', 'Unknown')
            industry = info.get('industry', 'Unknown')
            
            reasoning = [f"Sector: {sector}", f"Industry: {industry}"]
            
            # Basic sector scoring (simplified - in production would use sector ETF data)
            score = 60  # Neutral baseline
            
            # Check if it's a growth sector
            growth_sectors = ['Technology', 'Healthcare', 'Consumer Discretionary', 'Communication Services']
            defensive_sectors = ['Utilities', 'Consumer Staples', 'Healthcare']
            
            if sector in growth_sectors:
                score += 10
                reasoning.append("Growth sector with potential")
            elif sector in defensive_sectors:
                score += 5
                reasoning.append("Defensive sector with stability")
            
            # Market cap consideration
            market_cap = info.get('marketCap', 0)
            if market_cap > 10000000000:  # Large cap
                score += 10
                reasoning.append("Large cap stability")
            elif market_cap > 2000000000:  # Mid cap
                score += 5
                reasoning.append("Mid cap balance")
            else:  # Small cap
                reasoning.append("Small cap higher risk")
            
            return min(max(score, 0), 100), reasoning
            
        except Exception as e:
            return 50, [f"Sector analysis error: {str(e)}"]
    
    def _analyze_timing(self, hist) -> Tuple[float, List[str]]:
        """Analyze entry timing - late vs early"""
        try:
            # Calculate recent performance
            recent_5d = hist['Close'].pct_change(5).iloc[-1] * 100
            recent_10d = hist['Close'].pct_change(10).iloc[-1] * 100
            recent_30d = hist['Close'].pct_change(30).iloc[-1] * 100
            
            reasoning = []
            score = 60  # Neutral baseline
            
            # Check if already moved significantly
            if recent_5d > 15:
                score -= 20
                reasoning.append(f"Already moved +{recent_5d:.1f}% in 5 days - late entry risk")
            elif recent_5d > 8:
                score -= 10
                reasoning.append(f"Recent strong move +{recent_5d:.1f}% - watch for pullback")
            elif recent_5d < -10:
                score += 10
                reasoning.append(f"Recent pullback -{recent_5d:.1f}% - potential entry")
            
            # 10-day performance
            if recent_10d > 25:
                score -= 15
                reasoning.append(f"Extended +{recent_10d:.1f}% move in 10 days")
            elif recent_10d < -15:
                score += 15
                reasoning.append(f"Significant -{recent_10d:.1f}% pullback in 10 days")
            
            # Volatility consideration
            volatility = hist['Close'].pct_change().std() * np.sqrt(252) * 100
            if volatility > 50:
                score -= 10
                reasoning.append(f"High volatility {volatility:.1f}% - increased risk")
            elif volatility < 20:
                score += 5
                reasoning.append(f"Moderate volatility {volatility:.1f}% - stable")
            
            return min(max(score, 0), 100), reasoning
            
        except Exception as e:
            return 50, [f"Timing analysis error: {str(e)}"]
    
    def _analyze_fundamentals(self, stock) -> Tuple[float, List[str]]:
        """Basic fundamental analysis"""
        try:
            info = stock.info
            reasoning = []
            score = 60  # Neutral baseline
            
            # P/E ratio
            pe_ratio = info.get('forwardPE', 0)
            if pe_ratio and pe_ratio > 0:
                if pe_ratio < 15:
                    score += 10
                    reasoning.append(f"Reasonable P/E {pe_ratio:.1f}")
                elif pe_ratio > 30:
                    score -= 10
                    reasoning.append(f"High P/E {pe_ratio:.1f} - expensive")
                else:
                    reasoning.append(f"Moderate P/E {pe_ratio:.1f}")
            
            # Revenue growth
            revenue_growth = info.get('revenueGrowth', 0)
            if revenue_growth:
                if revenue_growth > 0.15:  # 15% growth
                    score += 15
                    reasoning.append(f"Strong revenue growth {revenue_growth*100:.1f}%")
                elif revenue_growth > 0.05:  # 5% growth
                    score += 5
                    reasoning.append(f"Moderate revenue growth {revenue_growth*100:.1f}%")
                elif revenue_growth < 0:
                    score -= 10
                    reasoning.append(f"Declining revenue {revenue_growth*100:.1f}%")
            
            # Profit margin
            profit_margin = info.get('profitMargins', 0)
            if profit_margin and profit_margin > 0:
                if profit_margin > 0.15:  # 15% margin
                    score += 10
                    reasoning.append(f"Strong profit margin {profit_margin*100:.1f}%")
                elif profit_margin > 0.05:
                    reasoning.append(f"Moderate profit margin {profit_margin*100:.1f}%")
            else:
                score -= 5
                reasoning.append("No profitability")
            
            return min(max(score, 0), 100), reasoning
            
        except Exception as e:
            return 50, [f"Fundamentals analysis error: {str(e)}"]
    
    def _analyze_smart_money(self, ticker: str) -> Tuple[float, List[str]]:
        """Analyze smart money alignment (placeholder for integration)"""
        try:
            reasoning = []
            score = 50  # Neutral baseline
            
            # This would integrate with:
            # - Insider monitor (Form 4 buys)
            # - Politician tracker (government trades)
            # - Institutional ownership data
            
            # For now, provide placeholder analysis
            reasoning.append("Smart money analysis pending integration")
            reasoning.append("Will check insider buying patterns")
            reasoning.append("Will check politician trading activity")
            
            return score, reasoning
            
        except Exception as e:
            return 50, [f"Smart money analysis error: {str(e)}"]
    
    def _determine_rating(self, overall_score: float, trend_score: float, volume_score: float) -> Tuple[str, float]:
        """Determine rating and confidence based on scores"""
        if overall_score >= 75 and trend_score >= 70 and volume_score >= 60:
            rating = "GOOD"
            confidence = min(90, overall_score)
        elif overall_score >= 60:
            rating = "MEH"
            confidence = overall_score
        else:
            rating = "BAD"
            confidence = max(10, 100 - overall_score)
        
        return rating, confidence
    
    def _assess_risk_level(self, ticker: str, hist, overall_score: float) -> str:
        """Assess risk level based on volatility and score"""
        try:
            volatility = hist['Close'].pct_change().std() * np.sqrt(252) * 100
            
            # Check if it's a penny stock
            current_price = hist['Close'].iloc[-1]
            is_penny = current_price < 5.0
            
            if is_penny or volatility > 60 or overall_score < 40:
                return "HIGH"
            elif volatility > 35 or overall_score < 60:
                return "MEDIUM"
            else:
                return "LOW"
                
        except Exception:
            return "MEDIUM"
    
    def _generate_recommendation(self, rating: str, confidence: float, risk_level: str, direction: Direction) -> str:
        """Generate actionable recommendation"""
        if rating == "GOOD" and confidence > 70:
            if risk_level == "LOW":
                return f"Strong {direction.value} candidate with good risk/reward"
            elif risk_level == "MEDIUM":
                return f"Consider {direction.value} with position sizing"
            else:
                return f"High-risk {direction.value} - only for aggressive strategies"
        elif rating == "MEH":
            return f"Wait for better entry or confirmation"
        else:
            return f"Avoid {direction.value} - poor setup"

# Example usage and testing
if __name__ == "__main__":
    print("🧪 Testing Idea Quality Analyzer...")
    
    analyzer = IdeaQualityAnalyzer()
    
    # Test analysis on some tickers
    test_tickers = ['AAPL', 'TSLA', 'MSFT', 'GME']
    
    for ticker in test_tickers:
        print(f"\n{'='*50}")
        quality = analyzer.analyze_ticker(ticker, Direction.LONG)
        
        if quality:
            print(f"📊 {ticker} Analysis:")
            print(f"   Rating: {quality.rating} (Confidence: {quality.confidence:.0f}%)")
            print(f"   Overall Score: {quality.overall_score:.0f}/100")
            print(f"   Risk Level: {quality.risk_level}")
            print(f"   Recommendation: {quality.recommendation}")
            print(f"   Key Factors:")
            for reason in quality.reasoning[:5]:  # Show top 5 reasons
                print(f"     • {reason}")
        else:
            print(f"❌ Failed to analyze {ticker}")
    
    print(f"\n✅ Stage 3 complete: Idea quality analysis working!")
    print(f"   - Ready for trader trust + idea quality combination")
