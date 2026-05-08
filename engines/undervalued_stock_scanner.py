#!/usr/bin/env python3
"""
Undervalued Stock Scanner
Finds stocks trading below their intrinsic value for long-term investing
"""

import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Optional

class UndervaluedStockScanner:
    """Scans for undervalued stocks using fundamental metrics"""
    
    def __init__(self):
        self.value_metrics = {
            'pe_ratio': {'max': 15, 'weight': 0.25},      # P/E ratio under 15
            'pb_ratio': {'max': 1.5, 'weight': 0.20},     # P/B ratio under 1.5
            'peg_ratio': {'max': 1.0, 'weight': 0.20},    # PEG under 1.0
            'debt_to_equity': {'max': 0.5, 'weight': 0.15}, # D/E under 0.5
            'roe': {'min': 15, 'weight': 0.20}            # ROE over 15%
        }
        
        # Value stock candidates (well-known companies that might be undervalued)
        self.value_candidates = [
            # Tech Giants
            'AAPL', 'MSFT', 'GOOGL', 'META', 'CSCO', 'INTC', 'IBM',
            
            # Financial Services
            'JPM', 'BAC', 'WFC', 'GS', 'MS', 'AXP', 'BLK',
            
            # Healthcare
            'JNJ', 'PFE', 'UNH', 'ABT', 'T', 'VZ', 'CI',
            
            # Consumer Staples
            'PG', 'KO', 'PEP', 'WMT', 'COST', 'HD', 'MCD',
            
            # Industrial
            'GE', 'MMM', 'CAT', 'DE', 'BA', 'HON', 'UPS',
            
            # Energy
            'XOM', 'CVX', 'COP', 'SLB', 'HAL', 'BP',
            
            # Materials/Commodities
            'DOW', 'DD', 'FCX', 'NUE', 'STLD',
            
            # Real Estate
            'SPG', 'AMT', 'PLD', 'CCI', 'EQIX',
            
            # Utilities
            'NEE', 'DUK', 'SO', 'AEP', 'XEL',
            
            # Retail/Consumer Discretionary
            'AMZN', 'TSLA', 'NKE', 'DIS', 'LOW', 'TGT', 'BBY',
            
            # Transportation
            'UNP', 'NSC', 'CSX', 'FDX', 'UPS',
            
            # Other Value Plays
            'BRK-B', 'IBM', 'F', 'GM', 'FORD', 'TME'
        ]
    
    def get_financial_metrics(self, symbol: str) -> Optional[Dict]:
        """Get financial metrics for a stock"""
        try:
            stock = yf.Ticker(symbol)
            info = stock.info
            
            # Get current price
            hist = stock.history(period='5d')
            if hist.empty:
                return None
            current_price = hist['Close'].iloc[-1]
            
            # Extract metrics
            metrics = {
                'symbol': symbol,
                'price': current_price,
                'pe_ratio': info.get('forwardPE', info.get('trailingPE', None)),
                'pb_ratio': info.get('priceToBook', None),
                'peg_ratio': info.get('pegRatio', None),
                'debt_to_equity': info.get('debtToEquity', None),
                'roe': info.get('returnOnEquity', None),
                'market_cap': info.get('marketCap', 0),
                'dividend_yield': info.get('dividendYield', 0) * 100 if info.get('dividendYield') else 0,
                'revenue_growth': info.get('revenueGrowth', 0) * 100 if info.get('revenueGrowth') else 0,
                'earnings_growth': info.get('earningsGrowth', 0) * 100 if info.get('earningsGrowth') else 0,
                'name': info.get('shortName', symbol),
                'sector': info.get('sector', 'Unknown'),
                'beta': info.get('beta', None)
            }
            
            return metrics
            
        except Exception as e:
            print(f"Error getting data for {symbol}: {e}")
            return None
    
    def calculate_value_score(self, metrics: Dict) -> float:
        """Calculate a value score (0-100) based on metrics"""
        score = 0
        total_weight = 0
        
        for metric, config in self.value_metrics.items():
            value = metrics.get(metric)
            
            if value is None:
                continue
            
            weight = config['weight']
            
            if metric == 'pe_ratio':
                # Lower P/E is better
                if value <= config['max']:
                    score += (1 - value / config['max']) * weight * 100
                total_weight += weight
                
            elif metric == 'pb_ratio':
                # Lower P/B is better
                if value <= config['max']:
                    score += (1 - value / config['max']) * weight * 100
                total_weight += weight
                
            elif metric == 'peg_ratio':
                # Lower PEG is better
                if value <= config['max']:
                    score += (1 - value / config['max']) * weight * 100
                total_weight += weight
                
            elif metric == 'debt_to_equity':
                # Lower D/E is better
                if value <= config['max']:
                    score += (1 - value / config['max']) * weight * 100
                total_weight += weight
                
            elif metric == 'roe':
                # Higher ROE is better
                if value >= config['min']:
                    score += min(value / config['min'], 2) * weight * 100  # Cap at 2x
                total_weight += weight
        
        # Normalize score
        if total_weight > 0:
            return score / total_weight
        return 0
    
    def find_undervalued_stocks(self, min_score: float = 60) -> List[Dict]:
        """Find undervalued stocks based on fundamental analysis"""
        print("🔍 SCANNING FOR UNDERVALUED STOCKS...")
        print(f"   Analyzing {len(self.value_candidates)} stocks...")
        
        undervalued = []
        
        for symbol in self.value_candidates:
            metrics = self.get_financial_metrics(symbol)
            
            if not metrics:
                continue
            
            # Calculate value score
            score = self.calculate_value_score(metrics)
            metrics['value_score'] = score
            
            # Check if meets criteria
            if score >= min_score:
                # Additional checks
                if metrics.get('market_cap', 0) > 1000000000:  # Market cap > $1B
                    undervalued.append(metrics)
        
        # Sort by value score
        undervalued.sort(key=lambda x: x['value_score'], reverse=True)
        
        return undervalued
    
    def analyze_value_stock(self, symbol: str) -> Dict:
        """Detailed analysis of a single value stock"""
        metrics = self.get_financial_metrics(symbol)
        
        if not metrics:
            return {'error': f'Could not fetch data for {symbol}'}
        
        score = self.calculate_value_score(metrics)
        metrics['value_score'] = score
        
        # Add analysis
        analysis = {
            'metrics': metrics,
            'strengths': [],
            'weaknesses': [],
            'recommendation': ''
        }
        
        # Analyze strengths
        if metrics.get('pe_ratio', 0) < 15:
            analysis['strengths'].append(f"Low P/E ratio ({metrics['pe_ratio']:.1f})")
        if metrics.get('pb_ratio', 0) < 1.5:
            analysis['strengths'].append(f"Low P/B ratio ({metrics['pb_ratio']:.1f})")
        if metrics.get('roe', 0) > 15:
            analysis['strengths'].append(f"Strong ROE ({metrics['roe']:.1f}%)")
        if metrics.get('dividend_yield', 0) > 2:
            analysis['strengths'].append(f"Good dividend yield ({metrics['dividend_yield']:.1f}%)")
        if metrics.get('debt_to_equity', 10) < 0.5:
            analysis['strengths'].append(f"Low debt ({metrics['debt_to_equity']:.1f})")
        
        # Analyze weaknesses
        if metrics.get('pe_ratio', 0) > 20:
            analysis['weaknesses'].append(f"High P/E ratio ({metrics['pe_ratio']:.1f})")
        if metrics.get('debt_to_equity', 0) > 1:
            analysis['weaknesses'].append(f"High debt ({metrics['debt_to_equity']:.1f})")
        if metrics.get('roe', 0) < 10:
            analysis['weaknesses'].append(f"Low ROE ({metrics['roe']:.1f}%)")
        if metrics.get('revenue_growth', 0) < 0:
            analysis['weaknesses'].append(f"Negative revenue growth ({metrics['revenue_growth']:.1f}%)")
        
        # Recommendation
        if score > 80:
            analysis['recommendation'] = "STRONG BUY - Excellent value"
        elif score > 70:
            analysis['recommendation'] = "BUY - Good value"
        elif score > 60:
            analysis['recommendation'] = "HOLD - Fair value"
        else:
            analysis['recommendation'] = "AVOID - Overvalued"
        
        return analysis
    
    def get_investment_thesis(self, metrics: Dict) -> str:
        """Generate investment thesis for a value stock"""
        thesis = f"INVESTMENT THESIS: {metrics['name']} ({metrics['symbol']})\n"
        thesis += f"Current Price: ${metrics['price']:.2f}\n"
        thesis += f"Value Score: {metrics['value_score']:.0f}/100\n\n"
        
        thesis += "KEY METRICS:\n"
        if metrics.get('pe_ratio'):
            thesis += f"  • P/E Ratio: {metrics['pe_ratio']:.1f} (Industry avg ~20)\n"
        if metrics.get('pb_ratio'):
            thesis += f"  • P/B Ratio: {metrics['pb_ratio']:.1f} (Under 1.5 is good)\n"
        if metrics.get('roe'):
            thesis += f"  • ROE: {metrics['roe']:.1f}% (Over 15% is strong)\n"
        if metrics.get('debt_to_equity'):
            thesis += f"  • Debt/Equity: {metrics['debt_to_equity']:.1f} (Lower is better)\n"
        if metrics.get('dividend_yield'):
            thesis += f"  • Dividend Yield: {metrics['dividend_yield']:.1f}%\n"
        
        thesis += f"\nSECTOR: {metrics['sector']}\n"
        thesis += f"MARKET CAP: ${metrics['market_cap']/1000000000:.0f}B\n"
        
        if metrics.get('beta'):
            thesis += f"BETA: {metrics['beta']:.1f} (S&P 500 = 1.0)\n"
        
        return thesis

if __name__ == "__main__":
    scanner = UndervaluedStockScanner()
    
    # Find undervalued stocks
    undervalued = scanner.find_undervalued_stocks(min_score=60)
    
    print("\n📊 TOP UNDERVALUED STOCKS:")
    print("=" * 60)
    
    for i, stock in enumerate(undervalued[:10], 1):
        print(f"\n{i}. {stock['symbol']} - {stock['name']}")
        print(f"   Price: ${stock['price']:.2f}")
        print(f"   Value Score: {stock['value_score']:.0f}/100")
        print(f"   P/E: {stock.get('pe_ratio', 'N/A')} | P/B: {stock.get('pb_ratio', 'N/A')} | ROE: {stock.get('roe', 'N/A')}%")
        print(f"   Sector: {stock['sector']}")
    
    # Analyze a specific stock
    if undervalued:
        print("\n" + "=" * 60)
        analysis = scanner.analyze_value_stock(undervalued[0]['symbol'])
        thesis = scanner.get_investment_thesis(undervalued[0])
        print(thesis)
