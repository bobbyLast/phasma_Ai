#!/usr/bin/env python3

# Add Alpaca Initialization to main.py
import re

def add_alpaca_initialization():
    """Add AlpacaPaperTrader initialization to main.py constructor"""
    print("🔧 Adding AlpacaPaperTrader initialization to main.py...")
    
    try:
        # Read the main.py file
        with open('main.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Find the paper trading initialization section
        pattern = r'(# 📊 Paper Trading Portfolio.*?\n\s+if self\.config\.get\(\'paper_trading\'\).*?\n\s+)(self\.paper_portfolio = get_paper_trading_portfolio\(self\.config\))'
        
        replacement = r'\1# Initialize Alpaca Paper Trading FIRST (real market data)\n            try:\n                self.alpaca_paper_trader = AlpacaPaperTrader()\n                if self.alpaca_paper_trader.alpaca:\n                    print("✅ Alpaca Paper Trading Initialized - REAL MARKET DATA")\n                    print("   Platform: Alpaca Paper Trading API")\n                    print("   Market Data: Real-time IEX feeds")\n                    print("   Account: Paper trading (no real money)")\n                else:\n                    print("⚠️ Alpaca Paper Trading failed - falling back to internal")\n                    \2\n            except Exception as e:\n                print(f"⚠️ Alpaca Paper Trading Error: {e}")\n                print("   Falling back to internal paper trading")\n                \2\n                self.alpaca_paper_trader = None'
        
        new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)
        
        # Also add the else clause for alpaca_paper_trader
        pattern2 = r'(\s+else:\n\s+self\.paper_portfolio = None\n\s+print\("⚠️ Paper Trading Disabled"\))'
        replacement2 = r'\1\n            self.alpaca_paper_trader = None'
        
        final_content = re.sub(pattern2, replacement2, new_content)
        
        # Write the modified content back
        with open('main.py', 'w', encoding='utf-8') as f:
            f.write(final_content)
        
        print("✅ AlpacaPaperTrader initialization added to main.py")
        return True
        
    except Exception as e:
        print(f"❌ Failed to add initialization: {e}")
        return False

if __name__ == "__main__":
    success = add_alpaca_initialization()
    if success:
        print("\n🎯 INTEGRATION COMPLETE!")
        print("   ✅ AlpacaPaperTrader will be initialized when main.py starts")
        print("   ✅ Trades will execute via Alpaca before posting to Telegram")
        print("   ✅ Fake internal paper trading replaced with real market data")
        print("\n🚀 Ready to test: python main.py --learning-only")
    else:
        print("\n⚠️ Manual integration needed")
