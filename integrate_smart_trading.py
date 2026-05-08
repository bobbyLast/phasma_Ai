#!/usr/bin/env python3
"""
Integration Script: Smart Trading Logic
Adds all the smart trading features to the main system
"""

import os
import sys
import json

# Add to main.py imports
def add_imports_to_main():
    """Add necessary imports to main.py"""
    main_file = "main.py"
    
    # Read main.py with UTF-8 encoding
    with open(main_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check if imports already exist
    if "from engines.smart_trading_strategy import SmartTradingStrategy" in content:
        print("✅ Smart trading imports already exist")
        return
    
    # Find the import section
    import_section = """from engines.real_portfolio_manager import RealPortfolioManager
from engines.market_hours_detector import MarketHoursDetector
from engines.paper_trading_portfolio import PaperTradingPortfolio, get_paper_trading_portfolio
from engines.smart_trading_strategy import SmartTradingStrategy"""
    
    # Replace existing imports
    old_import = "from engines.real_portfolio_manager import RealPortfolioManager\nfrom engines.market_hours_detector import MarketHoursDetector\nfrom engines.paper_trading_portfolio import PaperTradingPortfolio, get_paper_trading_portfolio"
    
    content = content.replace(old_import, import_section)
    
    # Write back
    with open(main_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ Added smart trading imports to main.py")

def add_smart_strategy_init():
    """Initialize smart strategy in PhasmaTradingSystem"""
    main_file = "main.py"
    
    with open(main_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find initialization section
    init_code = """        # 🕐 Market Hours Detector - Smart strategy selection
        self.market_hours = MarketHoursDetector()
        market_status = self.market_hours.get_market_status()
        print(f"🕐 Market Status: {market_status['recommended_strategy']}")
        print(f"   Reason: {market_status['reason']}")
        
        # Set trading strategy based on market hours
        if market_status['is_market_open']:
            self.trading_strategy = 'SWING_TRADING'
        else:
            self.trading_strategy = 'INVESTING'
            print("   📈 Market closed - Switching to investing strategy")
        
        # 🧠 Smart Trading Strategy - Intelligent strategy selection
        self.smart_strategy = SmartTradingStrategy(self.config)
        print("✅ Smart Trading Strategy Initialized")
        print(f"   Current Strategy: {self.trading_strategy}")"""
    
    # Find where to insert (after paper trading init)
    insert_point = "        else:\n            self.paper_portfolio = None\n            print(\"⚠️ Paper Trading Disabled\")"
    
    if init_code not in content:
        content = content.replace(insert_point, insert_point + "\n\n" + init_code)
        
        with open(main_file, 'w') as f:
            f.write(content)
        
        print("✅ Added smart strategy initialization to main.py")
    else:
        print("✅ Smart strategy initialization already exists")

def add_market_aware_signal_processing():
    """Add market-aware signal processing"""
    main_file = "main.py"
    
    with open(main_file, 'r') as f:
        content = f.read()
    
    # Find signal processing section
    signal_processing_code = """        # 🧠 Apply market-aware strategy filtering
        if hasattr(self, 'smart_strategy'):
            # Adjust signals based on market hours
            market_status = self.smart_strategy.market_hours.get_market_status()
            
            if market_status['recommended_strategy'] == 'INVESTING':
                # Market closed - filter for investment opportunities
                print("📈 Market closed - Filtering for investment opportunities...")
                
                # Get value investment recommendations
                investment_recs = self.smart_strategy.get_investment_recommendations()
                
                if investment_recs:
                    print(f"   Found {len(investment_recs)} value investment opportunities")
                    # Convert investment recs to signals
                    for rec in investment_recs:
                        signal = Signal(
                            symbol=rec['symbol'],
                            action='BUY',
                            confidence=rec['confidence'] / 100,
                            rationale=rec['reason'],
                            source='Value Investing',
                            metadata={
                                'type': 'VALUE_INVESTMENT',
                                'holding_period': rec['holding_period'],
                                'value_score': rec['value_score'],
                                'thesis': rec['thesis']
                            }
                        )
                        signals.append(signal)
                else:
                    print("   No value opportunities found")
            
            elif market_status['recommended_strategy'] == 'SWING_TRADING':
                # Market open - focus on swing trades
                print("📊 Market open - Focusing on swing trading opportunities...")
                # Filter out very short-term signals
                filtered_signals = []
                for s in signals:
                    if hasattr(s, 'metadata') and s.metadata.get('timeframe') in ['1m', '5m']:
                        print(f"   Filtering out short-term signal: {s.symbol}")
                        continue
                    filtered_signals.append(s)
                signals = filtered_signals"""
    
    # Find where to insert (before signal processing)
    insert_point = "        # Process signals through Meta-Brain"
    
    if signal_processing_code not in content:
        content = content.replace(insert_point, signal_processing_code + "\n\n        " + insert_point)
        
        with open(main_file, 'w') as f:
            f.write(content)
        
        print("✅ Added market-aware signal processing to main.py")
    else:
        print("✅ Market-aware signal processing already exists")

def add_paper_trading_integration():
    """Ensure paper trading is properly integrated"""
    main_file = "main.py"
    
    with open(main_file, 'r') as f:
        content = f.read()
    
    # Check if paper trading is enabled in config
    config_file = "config.json"
    
    if os.path.exists(config_file):
        with open(config_file, 'r') as f:
            config = json.load(f)
        
        if 'paper_trading' not in config:
            config['paper_trading'] = {
                'enabled': True,
                'starting_capital': 10000,
                'track_ai_performance': True,
                'auto_trade_signals': True,
                'min_confidence_threshold': 70,
                'max_position_size': 1000,
                'max_positions': 10
            }
            
            with open(config_file, 'w') as f:
                json.dump(config, f, indent=2)
            
            print("✅ Added paper trading configuration to config.json")
        else:
            print("✅ Paper trading configuration already exists")

def create_integration_summary():
    """Create a summary of all integrations"""
    summary = """
🤖 PHASMA AI - SMART TRADING INTEGRATION COMPLETE
==================================================

✅ INTEGRATED FEATURES:

1. Market Hours Detection
   - Automatically detects if market is open/closed
   - Switches strategies based on market status
   - Prevents day trading when market is closed

2. Smart Strategy Selection
   - Market Open: Swing Trading (1-5 day holds)
   - Market Closed: Value Investing (3-12 month holds)
   - Proper position sizing based on strategy

3. Value Stock Scanner
   - Finds undervalued stocks using fundamental metrics
   - P/E < 15, P/B < 1.5, ROE > 15%
   - Only runs when market is closed

4. Paper Trading Verification
   - Verifies all trades with real market data
   - Creates immutable trade records
   - Tracks AI confidence vs actual returns

5. Signal Filtering
   - Filters out inappropriate signals
   - No day trades when market is closed
   - Focus on actionable opportunities

🚀 READY TO GO:

Run: python main.py --monitor

The AI will now:
- Detect market hours automatically
- Switch between swing trading and investing
- Find value stocks when markets are closed
- Never post useless day trades at 10 PM
- Track performance with paper trading

💡 NEXT STEPS:

1. Test with: python main.py --monitor --interval 5 --max-runtime 1
2. Check paper trading: python paper_trading_dashboard.py
3. Verify market awareness: python demo_smart_strategy.py
"""
    
    with open("INTEGRATION_SUMMARY.md", 'w') as f:
        f.write(summary)
    
    print("✅ Created INTEGRATION_SUMMARY.md")

def main():
    """Run all integrations"""
    print("🚀 INTEGRATING SMART TRADING LOGIC INTO MAIN SYSTEM...")
    print("=" * 60)
    
    add_imports_to_main()
    add_smart_strategy_init()
    add_market_aware_signal_processing()
    add_paper_trading_integration()
    create_integration_summary()
    
    print("\n" + "=" * 60)
    print("✅ ALL INTEGRATIONS COMPLETE!")
    print("\nThe AI is now smart about market hours and will:")
    print("- Only day trade when markets are open")
    print("- Find value stocks when markets are closed")
    print("- Use proper strategies for each situation")
    print("- Track everything with paper trading")
    print("\nRun 'python main.py --monitor' to go live!")

if __name__ == "__main__":
    main()
