#!/usr/bin/env python3
"""
Demo: Smart AI Investing in Undervalued Stocks
Shows how AI finds value opportunities when markets are closed
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from engines.smart_trading_strategy import SmartTradingStrategy
from datetime import datetime
import pytz

def demo_value_investing():
    """Demonstrate how AI finds undervalued stocks"""
    
    print("🤖 PHASMA AI - VALUE INVESTING DEMO")
    print("=" * 60)
    print("Showing how AI finds undervalued stocks when markets are closed\n")
    
    # Initialize
    config = {}
    smart_strategy = SmartTradingStrategy(config)
    
    # Get current market status
    market_status = smart_strategy.market_hours.get_market_status()
    print(f"📊 Current Market Status: {market_status['recommended_strategy']}")
    print(f"   Reason: {market_status['reason']}")
    print()
    
    # Force value scanning for demo
    print("🔍 FORCING VALUE SCAN FOR DEMO (Normally only runs when market is closed)...")
    print("-" * 60)
    
    # Get undervalued stocks directly
    undervalued = smart_strategy.value_scanner.find_undervalued_stocks(min_score=60)
    
    if not undervalued:
        print("No undervalued stocks found at this time.")
        return
    
    # Create recommendations
    recommendations = []
    for stock in undervalued[:5]:
        rec = {
            'symbol': stock['symbol'],
            'name': stock['name'],
            'action': 'BUY',
            'type': 'VALUE_INVESTMENT',
            'price': stock['price'],
            'value_score': stock['value_score'],
            'confidence': min(90, 60 + stock['value_score'] * 0.3),
            'holding_period': '3-12 months',
            'thesis': smart_strategy.value_scanner.get_investment_thesis(stock),
            'metrics': {
                'pe_ratio': stock.get('pe_ratio'),
                'pb_ratio': stock.get('pb_ratio'),
                'roe': stock.get('roe'),
                'dividend_yield': stock.get('dividend_yield'),
                'debt_to_equity': stock.get('debt_to_equity')
            },
            'risk_level': 'LOW_TO_MEDIUM',
            'reason': f"Undervalued with score {stock['value_score']:.0f}/100"
        }
        recommendations.append(rec)
    
    print(f"\n✅ Found {len(recommendations)} undervalued stocks:\n")
    
    for i, rec in enumerate(recommendations, 1):
        print(f"{i}. {rec['symbol']} - {rec['name']}")
        print(f"   Type: {rec['type']}")
        print(f"   Price: ${rec['price']:.2f}")
        print(f"   Value Score: {rec['value_score']:.0f}/100")
        print(f"   Confidence: {rec['confidence']:.0f}%")
        print(f"   Holding Period: {rec['holding_period']}")
        print(f"   Risk Level: {rec['risk_level']}")
        print(f"   Reason: {rec['reason']}")
        
        # Key metrics
        metrics = rec['metrics']
        print("   Key Metrics:")
        if metrics.get('pe_ratio'):
            print(f"     • P/E Ratio: {metrics['pe_ratio']:.1f} (Low is good)")
        if metrics.get('pb_ratio'):
            print(f"     • P/B Ratio: {metrics['pb_ratio']:.1f} (Under 1.5 is good)")
        if metrics.get('roe'):
            print(f"     • ROE: {metrics['roe']:.1f}% (Over 15% is strong)")
        if metrics.get('dividend_yield'):
            print(f"     • Dividend Yield: {metrics['dividend_yield']:.1f}%")
        if metrics.get('debt_to_equity'):
            print(f"     • Debt/Equity: {metrics['debt_to_equity']:.1f} (Low is better)")
        
        print("\n   📋 Investment Thesis:")
        thesis_lines = rec['thesis'].split('\n')
        for line in thesis_lines[:8]:  # Show first 8 lines
            print(f"     {line}")
        
        print("\n" + "-" * 60)
    
    print("\n🎯 KEY INSIGHTS:")
    print("1. Market closed? → Focus on VALUE INVESTING")
    print("2. Look for low P/E, P/B ratios")
    print("3. Strong fundamentals (ROE > 15%)")
    print("4. Low debt levels (D/E < 0.5)")
    print("5. Hold for 3-12 months")
    print("6. These are NOT day trades - they're long-term investments!")
    
    print("\n💡 This prevents the AI from posting useless day trades")
    print("   when markets are closed. Instead, it finds real value")
    print("   opportunities for long-term investing.")

if __name__ == "__main__":
    demo_value_investing()
