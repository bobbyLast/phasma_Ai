#!/usr/bin/env python3

# Simple Alpaca Integration Add
def simple_add():
    """Simply add the AlpacaPaperTrader initialization"""
    print("🔧 Adding AlpacaPaperTrader initialization...")
    
    try:
        # Read the file
        with open('main.py', 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Find the line with paper_portfolio initialization
        for i, line in enumerate(lines):
            if 'self.paper_portfolio = get_paper_trading_portfolio(self.config)' in line:
                # Insert Alpaca initialization before this line
                indent = '            '  # Match the indentation
                alpaca_lines = [
                    f'{indent}# Initialize Alpaca Paper Trading FIRST (real market data)\n',
                    f'{indent}try:\n',
                    f'{indent}    self.alpaca_paper_trader = AlpacaPaperTrader()\n',
                    f'{indent}    if self.alpaca_paper_trader.alpaca:\n',
                    f'{indent}        print("✅ Alpaca Paper Trading Initialized - REAL MARKET DATA")\n',
                    f'{indent}        print("   Platform: Alpaca Paper Trading API")\n',
                    f'{indent}        print("   Market Data: Real-time IEX feeds")\n',
                    f'{indent}        print("   Account: Paper trading (no real money)")\n',
                    f'{indent}    else:\n',
                    f'{indent}        print("⚠️ Alpaca Paper Trading failed - falling back to internal")\n',
                ]
                
                # Insert the lines before the paper_portfolio line
                lines[i:i] = alpaca_lines
                
                # Add exception handling after the paper_portfolio block
                for j in range(i+15, len(lines)):
                    if 'self.paper_portfolio = None' in lines[j]:
                        lines.insert(j+1, f'{indent}        self.alpaca_paper_trader = None\n')
                        break
                
                break
        
        # Write back
        with open('main.py', 'w', encoding='utf-8') as f:
            f.writelines(lines)
        
        print("✅ AlpacaPaperTrader initialization added")
        return True
        
    except Exception as e:
        print(f"❌ Failed: {e}")
        return False

if __name__ == "__main__":
    success = simple_add()
    if success:
        print("\n🎯 INTEGRATION COMPLETE!")
        print("   ✅ AlpacaPaperTrader initialization added")
        print("   ✅ Ready to test with: python main.py --learning-only")
    else:
        print("\n⚠️ Manual edit needed")
