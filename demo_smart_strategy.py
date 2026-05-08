#!/usr/bin/env python3
"""
Demo: Smart Trading Strategy Based on Market Hours
Shows how AI adapts its strategy based on market conditions
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from engines.smart_trading_strategy import SmartTradingStrategy
from engines.market_hours_detector import MarketHoursDetector
from datetime import datetime, timedelta
import pytz

def demo_smart_strategy():
    """Demonstrate how the AI adapts to market hours"""
    
    print("🤖 PHASMA AI - SMART TRADING STRATEGY DEMO")
    print("=" * 60)
    
    # Initialize
    config = {}  # Your config
    smart_strategy = SmartTradingStrategy(config)
    market_hours = MarketHoursDetector()
    
    # Test different times
    test_times = [
        ("Market Open (9:30 AM ET)", datetime.now(pytz.timezone('America/New_York')).replace(hour=9, minute=30, second=0, microsecond=0)),
        ("Mid-day (12:00 PM ET)", datetime.now(pytz.timezone('America/New_York')).replace(hour=12, minute=0, second=0, microsecond=0)),
        ("Market Close (4:00 PM ET)", datetime.now(pytz.timezone('America/New_York')).replace(hour=16, minute=0, second=0, microsecond=0)),
        ("After Hours (6:00 PM ET)", datetime.now(pytz.timezone('America/New_York')).replace(hour=18, minute=0, second=0, microsecond=0)),
        ("Pre-market (7:00 AM ET)", datetime.now(pytz.timezone('America/New_York')).replace(hour=7, minute=0, second=0, microsecond=0)),
        ("Weekend (Saturday)", datetime.now(pytz.timezone('America/New_York')) + timedelta(days=(5 - datetime.now().weekday()) % 7 + 1)),
    ]
    
    for name, test_time in test_times:
        print(f"\n📊 {name}")
        print("-" * 40)
        
        # Get market status
        status = market_hours.get_market_status(test_time)
        print(f"Market Status: {status['is_market_open']}")
        print(f"Recommended: {status['recommended_strategy']}")
        print(f"Reason: {status['reason']}")
        
        # Get trading strategy
        strategy = smart_strategy.get_recommended_strategy(test_time)
        print(f"\nStrategy Details:")
        print(f"  Type: {strategy['strategy']}")
        print(f"  Timeframe: {strategy['timeframe']}")
        print(f"  Hold Period: {strategy['hold_period']}")
        print(f"  Focus: {strategy['focus']}")
        print(f"  Risk Level: {strategy['risk_level']}")
        
        # Check if day trading is appropriate
        can_day_trade, reason = smart_strategy.should_day_trade(test_time)
        print(f"\nDay Trading: {'✅ Yes' if can_day_trade else '❌ No'}")
        print(f"  Reason: {reason}")
        
        # Get position sizing rules
        sizing = smart_strategy.get_position_sizing_rules()
        print(f"\nPosition Sizing:")
        print(f"  Max Positions: {sizing['max_positions']}")
        print(f"  Size per Position: {sizing['position_size_percent']*100:.0f}%")
        print(f"  Risk per Trade: {sizing['risk_per_trade']*100:.0f}%")
        print(f"  Expected Hold: {sizing['holding_period']}")
    
    print("\n" + "=" * 60)
    print("🎯 KEY INSIGHTS:")
    print("1. Market is closed? → Focus on INVESTING (long-term)")
    print("2. Market is open? → Use SWING TRADING (medium-term)")
    print("3. Never day trade when market is closed!")
    print("4. Risk adjusts based on market conditions")
    print("5. Position sizing adapts to strategy")
    
    print("\n💡 This prevents the AI from posting day trades")
    print("   when markets are closed or when it's not")
    print("   fast enough to execute them properly.")

if __name__ == "__main__":
    demo_smart_strategy()
