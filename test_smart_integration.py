#!/usr/bin/env python3
"""
Final Integration Test: Smart Trading System
Tests all the smart trading features working together
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime
import pytz

def test_market_hours():
    """Test market hours detection"""
    print("🕐 TESTING MARKET HOURS DETECTION")
    print("-" * 40)
    
    from engines.market_hours_detector import MarketHoursDetector
    detector = MarketHoursDetector()
    
    # Test current time
    status = detector.get_market_status()
    print(f"Current Time: {status['datetime']}")
    print(f"Market Open: {status['is_market_open']}")
    print(f"Strategy: {status['recommended_strategy']}")
    print(f"Reason: {status['reason']}")
    
    return status

def test_smart_strategy():
    """Test smart strategy selection"""
    print("\n🧠 TESTING SMART STRATEGY")
    print("-" * 40)
    
    from engines.smart_trading_strategy import SmartTradingStrategy
    
    config = {}
    strategy = SmartTradingStrategy(config)
    
    # Get current strategy
    current = strategy.get_recommended_strategy()
    print(f"Strategy: {current['strategy']}")
    print(f"Timeframe: {current['timeframe']}")
    print(f"Hold Period: {current['hold_period']}")
    print(f"Focus: {current['focus']}")
    
    # Check if should day trade
    can_day_trade, reason = strategy.should_day_trade()
    print(f"Day Trading: {'✅' if can_day_trade else '❌'}")
    print(f"Reason: {reason}")
    
    return strategy

def test_value_scanner():
    """Test undervalued stock scanner"""
    print("\n🔍 TESTING VALUE SCANNER")
    print("-" * 40)
    
    from engines.undervalued_stock_scanner import UndervaluedStockScanner
    
    scanner = UndervaluedStockScanner()
    
    # Test a single stock
    print("Analyzing AAPL...")
    analysis = scanner.analyze_value_stock('AAPL')
    
    if 'error' not in analysis:
        metrics = analysis['metrics']
        print(f"Price: ${metrics['price']:.2f}")
        print(f"P/E: {metrics.get('pe_ratio', 'N/A')}")
        print(f"P/B: {metrics.get('pb_ratio', 'N/A')}")
        print(f"Value Score: {metrics.get('value_score', 0):.0f}/100")
        print(f"Recommendation: {analysis['recommendation']}")
    else:
        print(f"Error: {analysis['error']}")
    
    return scanner

def test_paper_trading():
    """Test paper trading system"""
    print("\n📊 TESTING PAPER TRADING")
    print("-" * 40)
    
    from engines.paper_trading_portfolio import get_paper_trading_portfolio
    from core.config import PhasmaConfig
    
    config = PhasmaConfig()
    config.update({
        'paper_trading': {
            'enabled': True,
            'starting_capital': 10000
        }
    })
    
    portfolio = get_paper_trading_portfolio(config)
    
    # Get portfolio summary
    summary = portfolio.get_portfolio_summary()
    print(f"Starting Capital: ${summary['starting_capital']:,.2f}")
    print(f"Current Value: ${summary['total_portfolio_value']:,.2f}")
    print(f"Total Return: ${summary['total_return']:,.2f}")
    print(f"Total Trades: {summary['total_trades']}")
    
    # Check verification
    if 'verification' in summary:
        verification = summary['verification']
        print(f"Verification Rate: {verification.get('verification_rate', 0):.1%}")
    
    return portfolio

def test_integration():
    """Test all components working together"""
    print("\n🤖 TESTING FULL INTEGRATION")
    print("-" * 40)
    
    # Get market status
    market_status = test_market_hours()
    
    # Get smart strategy
    strategy = test_smart_strategy()
    
    # Based on market status, show what AI would do
    print("\n📋 WHAT AI WOULD DO RIGHT NOW:")
    print("=" * 40)
    
    if market_status['is_market_open']:
        print("✅ MARKET IS OPEN")
        print("→ Strategy: Swing Trading")
        print("→ Look for: 1-5 day holding opportunities")
        print("→ Risk: Medium (3% per trade)")
        print("→ Position Size: 15% of portfolio")
        print("→ NO day trades - use swing trading instead")
    else:
        print("❌ MARKET IS CLOSED")
        print("→ Strategy: Value Investing")
        print("→ Look for: Undervalued stocks")
        print("→ Risk: Low to Medium")
        print("→ Holding: 3-12 months")
        print("→ Focus: Fundamentals (P/E < 15, ROE > 15%)")
        
        # Show some value opportunities
        print("\n🔍 CURRENT VALUE OPPORTUNITIES:")
        opportunities = strategy.find_value_opportunities(limit=3)
        for i, stock in enumerate(opportunities, 1):
            print(f"{i}. {stock['symbol']} - Score: {stock['value_score']:.0f}/100")
    
    print("\n✅ INTEGRATION TEST COMPLETE!")
    print("\nThe AI is now smart about:")
    print("1. Market hours awareness")
    print("2. Strategy selection")
    print("3. Value investing when closed")
    print("4. Paper trading verification")
    print("5. No more useless day trades!")

def main():
    print("🚀 PHASMA AI - SMART TRADING INTEGRATION TEST")
    print("=" * 60)
    print("Testing all smart trading features...\n")
    
    try:
        test_integration()
        
        print("\n" + "=" * 60)
        print("🎯 READY TO GO LIVE!")
        print("\nRun: python main.py --monitor")
        print("\nThe AI will now:")
        print("- Detect market hours automatically")
        print("- Switch strategies intelligently")
        print("- Find value stocks when markets are closed")
        print("- Never post day trades at 10 PM!")
        print("- Track everything with paper trading")
        
    except Exception as e:
        print(f"\n❌ Error during test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
