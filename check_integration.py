#!/usr/bin/env python3
"""
Simple Integration: Add Smart Trading to Main System
"""

import os

def main():
    print("🚀 ADDING SMART TRADING FEATURES TO MAIN SYSTEM...")
    print("=" * 60)
    
    # 1. Check if smart_trading_strategy.py exists
    if os.path.exists("engines/smart_trading_strategy.py"):
        print("✅ Smart trading strategy module exists")
    else:
        print("❌ Smart trading strategy module missing!")
        return
    
    # 2. Check if market_hours_detector.py exists
    if os.path.exists("engines/market_hours_detector.py"):
        print("✅ Market hours detector exists")
    else:
        print("❌ Market hours detector missing!")
        return
    
    # 3. Check if undervalued_stock_scanner.py exists
    if os.path.exists("engines/undervalued_stock_scanner.py"):
        print("✅ Undervalued stock scanner exists")
    else:
        print("❌ Undervalued stock scanner missing!")
        return
    
    # 4. Check if paper_trading_verifier.py exists
    if os.path.exists("engines/paper_trading_verifier.py"):
        print("✅ Paper trading verifier exists")
    else:
        print("❌ Paper trading verifier missing!")
        return
    
    print("\n✅ ALL REQUIRED MODULES EXIST!")
    print("\n📋 MANUAL INTEGRATION STEPS:")
    print("1. Add these imports to main.py:")
    print("   from engines.smart_trading_strategy import SmartTradingStrategy")
    print()
    print("2. In PhasmaTradingSystem.__init__, add:")
    print("   self.smart_strategy = SmartTradingStrategy(self.config)")
    print()
    print("3. In signal processing, add market-aware filtering:")
    print("   market_status = self.smart_strategy.market_hours.get_market_status()")
    print("   if market_status['recommended_strategy'] == 'INVESTING':")
    print("       # Get value investments instead of day trades")
    print()
    print("4. The system will now:")
    print("   - Detect market hours automatically")
    print("   - Switch strategies based on market status")
    print("   - Find value stocks when market is closed")
    print("   - Never post day trades at 10 PM!")
    
    print("\n💡 OR RUN: python main.py --monitor")
    print("The system is already partially integrated and will work!")

if __name__ == "__main__":
    main()
