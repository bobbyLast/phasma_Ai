"""
Value Selector - Mind 2 of the Three-Mind Trading Framework

Decides what's worth owning or shorting based on fundamental value.
Implements Graham-style margin of safety with modern adaptations.
"""

import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import yfinance as yf


@dataclass
class ValueScore:
    """Fundamental value assessment for a ticker"""
    symbol: str
    intrinsic_value: float
    current_price: float
    margin_of_safety: float  # Percentage below intrinsic value
    quality_score: float  # 0-1, based on fundamentals
    value_grade: str  # DEEP_VALUE, VALUE, FAIR, OVERVALUED, JUNK
    conviction: float  # 0-1, combines value and quality
    thesis: str  # Brief explanation of value case


class ValueSelector:
    """Mind 2: Graham-style value investing with modern adaptations"""
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        
        # Graham formula parameters (modernized)
        self.base_pe = 15.0  # Historical average PE
        self.default_growth = 5.0  # Default growth assumption
        
        # Quality metrics weights
        self.quality_weights = {
            'roe': 0.25,  # Return on Equity
            'debt_to_equity': 0.20,  # Leverage
            'current_ratio': 0.15,  # Liquidity
            'gross_margin': 0.20,  # Profitability
            'earnings_stability': 0.20  # Consistency
        }
        
        # Adjustments for macro environment
        self.risk_free_rate = 0.04  # Current 10-year Treasury
        self.market_pe_adjustment = 1.0  # Adjust for market multiples
        
    def analyze_value(self, symbol: str, macro_context: Dict = None) -> Optional[ValueScore]:
        """Complete value analysis for a single stock"""
        
        try:
            # Get fundamental data
            ticker = yf.Ticker(symbol)
            info = ticker.info
            financials = ticker.financials
            balance_sheet = ticker.balance_sheet
            
            # Skip if insufficient data
            if not info or 'regularMarketPrice' not in info:
                return None
                
            price = info['regularMarketPrice']
            
            # Calculate intrinsic value using Graham formula
            intrinsic_value = self._calculate_graham_value(info, financials)
            
            if not intrinsic_value or intrinsic_value <= 0:
                return None
            
            # Calculate margin of safety
            margin_of_safety = (intrinsic_value - price) / intrinsic_value
            
            # Assess quality
            quality_score = self._assess_quality(info, financials, balance_sheet)
            
            # Determine value grade
            value_grade = self._grade_value(margin_of_safety, quality_score)
            
            # Calculate conviction (combines value and quality)
            conviction = self._calculate_conviction(margin_of_safety, quality_score)
            
            # Generate thesis
            thesis = self._generate_thesis(symbol, info, margin_of_safety, quality_grade)
            
            return ValueScore(
                symbol=symbol,
                intrinsic_value=intrinsic_value,
                current_price=price,
                margin_of_safety=margin_of_safety,
                quality_score=quality_score,
                value_grade=value_grade,
                conviction=conviction,
                thesis=thesis
            )
            
        except Exception as e:
            print(f"Error analyzing {symbol}: {e}")
            return None
    
    def _calculate_graham_value(self, info: Dict, financials: Dict) -> Optional[float]:
        """Calculate intrinsic value using Graham formula with modern adjustments"""
        
        try:
            # Get EPS (use trailing if available, otherwise forward)
            eps = info.get('trailingEps', info.get('forwardEps', 0))
            if eps <= 0:
                return None
            
            # Get expected growth (use analyst estimates if available)
            growth = info.get('earningsGrowth', self.default_growth)
            if growth > 50:  # Sanity check for unrealistic growth
                growth = 30
            
            # Adjust PE for current interest rates (Graham's adjustment)
            rate_adjustment = (4.4 / self.risk_free_rate) if self.risk_free_rate > 0 else 1.0
            
            # Graham formula: V = EPS × (8.5 + 2g) × rate_adjustment
            base_pe = 8.5 + (2 * growth)
            adjusted_pe = base_pe * rate_adjustment * self.market_pe_adjustment
            
            # Apply sanity bounds (PE between 5 and 40)
            adjusted_pe = np.clip(adjusted_pe, 5, 40)
            
            intrinsic_value = eps * adjusted_pe
            
            # Additional check: Book value floor
            book_value = info.get('bookValue', 0)
            if book_value > 0:
                book_floor = book_value * 1.5  # Graham's book value rule
                intrinsic_value = max(intrinsic_value, book_floor)
            
            return intrinsic_value
            
        except Exception as e:
            print(f"Error in Graham valuation: {e}")
            return None
    
    def _assess_quality(self, info: Dict, financials: Dict, balance_sheet: Dict) -> float:
        """Assess company quality (0-1 scale)"""
        
        quality_score = 0.0
        
        try:
            # ROE (Return on Equity)
            roe = info.get('returnOnEquity', 0)
            if roe and roe > 0:
                # Score: ROE > 20% = 1.0, 10% = 0.5, < 5% = 0
                roe_score = min(max((roe - 0.05) / 0.15, 0), 1)
                quality_score += roe_score * self.quality_weights['roe']
            
            # Debt to Equity
            debt_to_equity = info.get('debtToEquity', 0)
            if debt_to_equity >= 0:
                # Score: D/E < 0.3 = 1.0, 1.0 = 0.5, > 2.0 = 0
                debt_score = max(1 - (debt_to_equity / 2.0), 0)
                quality_score += debt_score * self.quality_weights['debt_to_equity']
            
            # Current Ratio (Liquidity)
            current_ratio = info.get('currentRatio', 1.0)
            if current_ratio > 0:
                # Score: > 2.0 = 1.0, 1.5 = 0.5, < 1.0 = 0
                liquidity_score = min(max((current_ratio - 1.0), 0) / 1.0, 1)
                quality_score += liquidity_score * self.quality_weights['current_ratio']
            
            # Gross Margin
            gross_margin = info.get('grossMargins', 0)
            if gross_margin > 0:
                # Score: > 50% = 1.0, 30% = 0.5, < 20% = 0
                margin_score = min(max((gross_margin - 0.20) / 0.30, 0), 1)
                quality_score += margin_score * self.quality_weights['gross_margin']
            
            # Earnings Stability (simplified - check if consistently profitable)
            if financials is not None and len(financials) > 0:
                net_income = financials.loc['Net Income'].iloc[0] if 'Net Income' in financials.index else 0
                if net_income > 0:
                    quality_score += self.quality_weights['earnings_stability']
            
            return min(quality_score, 1.0)
            
        except Exception as e:
            print(f"Error assessing quality: {e}")
            return 0.3  # Default to low quality on error
    
    def _grade_value(self, margin: float, quality: float) -> str:
        """Grade the value opportunity"""
        
        if margin > 0.5 and quality > 0.7:
            return "DEEP_VALUE"
        elif margin > 0.3 and quality > 0.5:
            return "VALUE"
        elif margin > 0.1:
            return "FAIR"
        elif margin < -0.2:
            return "OVERVALUED"
        else:
            return "JUNK"
    
    def _calculate_conviction(self, margin: float, quality: float) -> float:
        """Calculate conviction score (0-1)"""
        
        # Combine margin of safety and quality
        # Margin is more important than quality for value investors
        margin_score = min(max(margin * 2, 0), 1)  # 50% margin = 1.0
        quality_weighted = quality * 0.5
        
        conviction = (margin_score * 0.7) + quality_weighted
        return min(conviction, 1.0)
    
    def _generate_thesis(self, symbol: str, info: Dict, margin: float, grade: str) -> str:
        """Generate brief value thesis"""
        
        company_name = info.get('shortName', symbol)
        sector = info.get('sector', 'Unknown')
        
        if grade == "DEEP_VALUE":
            thesis = f"{company_name} trading at {abs(margin):.0%} below intrinsic value with strong fundamentals"
        elif grade == "VALUE":
            thesis = f"{company_name} offers {abs(margin):.0%} margin of safety in {sector} sector"
        elif grade == "FAIR":
            thesis = f"{company_name} fairly valued, suitable for quality-focused portfolios"
        elif grade == "OVERVALUED":
            thesis = f"{company_name} overvalued by {abs(margin):.0%}, consider avoiding or shorting"
        else:
            thesis = f"{company_name} appears risky based on fundamental analysis"
        
        return thesis
    
    def screen_universe(self, symbols: List[str], macro_context: Dict = None) -> List[ValueScore]:
        """Screen universe of stocks for value opportunities"""
        
        opportunities = []
        
        for symbol in symbols:
            value = self.analyze_value(symbol, macro_context)
            if value and value.value_grade in ["DEEP_VALUE", "VALUE"]:
                opportunities.append(value)
        
        # Sort by conviction
        opportunities.sort(key=lambda x: x.conviction, reverse=True)
        
        return opportunities
    
    def get_long_universe(self, symbols: List[str]) -> List[str]:
        """Get universe of stocks suitable for long positions"""
        
        long_universe = []
        
        for symbol in symbols:
            value = self.analyze_value(symbol)
            if value and value.value_grade in ["VALUE", "DEEP_VALUE"] and value.quality_score > 0.4:
                long_universe.append(symbol)
        
        return long_universe
    
    def get_short_universe(self, symbols: List[str]) -> List[str]:
        """Get universe of stocks suitable for short positions"""
        
        short_universe = []
        
        for symbol in symbols:
            value = self.analyze_value(symbol)
            if value and value.value_grade == "OVERVALUED" and value.quality_score < 0.5:
                short_universe.append(symbol)
        
        return short_universe
