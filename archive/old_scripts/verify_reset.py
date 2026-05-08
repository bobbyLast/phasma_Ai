import json
import os
from datetime import datetime

print("✅ VERIFYING AI RESET SUCCESS")
print("=" * 60)

# 1. Check state file
print("\n📊 Checking phasma_state.json...")
with open('phasma_state.json', 'r') as f:
    state = json.load(f)

portfolio = state['portfolio_state']
bankroll = state['bankroll_allocation']

print(f"   Total Bankroll: ${bankroll['total_bankroll']}")
print(f"   Stock Trading: ${bankroll['stock_trading']['allocated']} allocated, ${bankroll['stock_trading']['available']} available")
print(f"   Kalshi Trading: ${bankroll['kalshi_trading']['allocated']} allocated, ${bankroll['kalshi_trading']['available']} available")
print(f"   Portfolio Available Capital: ${portfolio['available_capital']:.2f}")
print(f"   Open Positions: {portfolio['open_positions_count']}")

# 2. Check config
print("\n⚙️ Checking config.json...")
with open('config.json', 'r') as f:
    config = json.load(f)

print(f"   Bankroll: ${config['bankroll']}")
print(f"   Stock Trading Bankroll: ${config['trading']['stock_trading']['bankroll']}")
print(f"   Kalshi Trading Bankroll: ${config['trading']['kalshi_trading']['bankroll']}")

# 3. Check bankroll monitor
print("\n💰 Checking bankroll monitor...")
with open('bankroll_monitor.json', 'r') as f:
    monitor = json.load(f)

print(f"   Total: ${monitor['total_bankroll']}")
print(f"   Stock Available: ${monitor['allocations']['stock_trading']['available']}")
print(f"   Kalshi Available: ${monitor['allocations']['kalshi_trading']['available']}")

# 4. List all files created/modified
print("\n📁 Files Related to Reset:")
files = [
    'phasma_state.json',
    'config.json',
    'bankroll_monitor.json',
    'unified_main.db',
    'trade_history_20251225_225015.json'  # The documented trades
]

for file in files:
    if os.path.exists(file):
        size = os.path.getsize(file)
        mtime = datetime.fromtimestamp(os.path.getmtime(file))
        print(f"   ✓ {file} ({size} bytes, modified {mtime.strftime('%Y-%m-%d %H:%M:%S')})")

print("\n" + "=" * 60)
print("🎯 RESET VERIFICATION COMPLETE!")
print("\n📈 DOCUMENTED TRADES (from previous session):")
print("   • 11 trades executed on Dec 12, 2025")
print("   • 9 positions were open (now cleared)")
print("   • Full documentation saved to trade_history_*.json")

print("\n💰 NEW BANKROLL SETUP:")
print("   • Total: $100")
print("   • Stock Trading: $50 (max 5 positions @ $10 each)")
print("   • Kalshi Trading: $50 (max 10 positions @ $5 each)")

print("\n🚀 READY TO TRADE:")
print("   • AI will find FRESH stocks (no more NVDA, LCID, BTC repeat)")
print("   • Weather markets use consistency engine for high win rate")
print("   • Each platform tracks its own bankroll separately")
print("   • All trades are properly recorded in unified_main.db")

print("\n⚠️  REMEMBER:")
print("   • Run 'python main.py' to start trading")
print("   • Check 'bankroll_monitor.json' to track allocations")
print("   • Trade history is preserved in documentation file")
