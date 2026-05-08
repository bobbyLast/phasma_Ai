import json
import os
import sqlite3
from datetime import datetime

print("🔍 Searching for Real AI Trades")
print("=" * 60)

# 1. Check all possible database files
db_files = ['trades.db', 'phasma_trades.db', 'portfolio.db', 'unified_trades.db']
found_dbs = []

for db_file in db_files:
    if os.path.exists(db_file):
        found_dbs.append(db_file)
        print(f"\n📊 Found database: {db_file}")
        
        try:
            conn = sqlite3.connect(db_file)
            cursor = conn.cursor()
            
            # Get all tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = [t[0] for t in cursor.fetchall()]
            print(f"   Tables: {tables}")
            
            # Check for trades
            if 'trades' in tables:
                cursor.execute("SELECT COUNT(*) FROM trades")
                count = cursor.fetchone()[0]
                print(f"   Total trades: {count}")
                
                if count > 0:
                    # Get recent trades with actual values
                    cursor.execute("""
                        SELECT symbol, strategy, action, entry_price, quantity, timestamp, profit_loss
                        FROM trades 
                        ORDER BY timestamp DESC 
                        LIMIT 10
                    """)
                    trades = cursor.fetchall()
                    
                    print(f"\n   Recent Trades:")
                    for t in trades:
                        symbol, strategy, action, entry_price, quantity, timestamp, pnl = t
                        print(f"   • {symbol}: {action} {quantity} @ ${entry_price:.2f} | P&L: ${pnl:.2f}")
            
            # Check for positions
            if 'positions' in tables or 'portfolio' in tables:
                table_name = 'positions' if 'positions' in tables else 'portfolio'
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                count = cursor.fetchone()[0]
                print(f"   Positions in {table_name}: {count}")
            
            conn.close()
            
        except Exception as e:
            print(f"   Error reading {db_file}: {e}")

# 2. Check portfolio state for actual position values
if os.path.exists('phasma_state.json'):
    with open('phasma_state.json', 'r') as f:
        state = json.load(f)
    
    print(f"\n💰 Portfolio State:")
    portfolio = state.get('portfolio_state', {})
    print(f"   Available Capital: ${portfolio.get('available_capital', 0):.2f}")
    print(f"   Total Portfolio Value: ${portfolio.get('total_portfolio_value', 0):.2f}")
    print(f"   Total Return: ${portfolio.get('total_return', 0):.2f}")
    print(f"   Total Trades: {portfolio.get('total_trades', 0)}")
    
    # Check invested capital
    invested = portfolio.get('total_portfolio_value', 0) - portfolio.get('available_capital', 0)
    print(f"   Currently Invested: ${invested:.2f}")
    
    # Show actual open positions with real values
    open_positions = portfolio.get('open_positions', [])
    if open_positions:
        print(f"\n   Open Positions ({len(open_positions)}):")
        for pos in open_positions:
            symbol = pos.get('symbol', 'Unknown')
            quantity = pos.get('quantity', 0)
            avg_cost = pos.get('avg_cost', 0)
            current_price = pos.get('current_price', 0)
            pnl = pos.get('unrealized_pnl', 0)
            
            if quantity > 0 and avg_cost > 0:
                value = quantity * avg_cost
                print(f"   • {symbol}: {quantity} shares @ ${avg_cost:.2f} = ${value:.2f} | P&L: ${pnl:.2f}")

# 3. Check trade logs
log_files = ['trade_log.txt', 'trades.log', 'execution_log.txt']
for log_file in log_files:
    if os.path.exists(log_file):
        print(f"\n📝 Found log file: {log_file}")
        with open(log_file, 'r') as f:
            lines = f.readlines()[-10:]  # Last 10 lines
            for line in lines:
                if 'BUY' in line or 'SELL' in line or 'EXECUTED' in line:
                    print(f"   {line.strip()}")

# 4. Summary
print(f"\n" + "=" * 60)
print("SUMMARY:")
if found_dbs:
    print(f"✅ Found {len(found_dbs)} database(s) with trade records")
else:
    print("❌ No trade databases found")

if portfolio.get('total_trades', 0) > 0:
    print(f"✅ Portfolio shows {portfolio.get('total_trades')} total trades")
    print(f"💰 Total invested: ${invested:.2f}")
else:
    print("❌ No trades recorded in portfolio")
