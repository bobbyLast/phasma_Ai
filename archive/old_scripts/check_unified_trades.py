import sqlite3
import json
import os
from datetime import datetime

print("🔍 Checking Unified Trading System Records")
print("=" * 60)

# Check unified_main.db
if os.path.exists('unified_main.db'):
    print("\n📊 Checking unified_main.db...")
    conn = sqlite3.connect('unified_main.db')
    cursor = conn.cursor()
    
    # Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [t[0] for t in cursor.fetchall()]
    print(f"Tables: {tables}")
    
    # Check trades table
    if 'trades' in tables:
        cursor.execute("SELECT COUNT(*) FROM trades")
        count = cursor.fetchone()[0]
        print(f"\nTotal trades in unified_main.db: {count}")
        
        if count > 0:
            # Get all trades with details
            cursor.execute("""
                SELECT symbol, strategy, action, entry_price, quantity, 
                       timestamp, profit_loss, status
                FROM trades 
                ORDER BY timestamp DESC
            """)
            trades = cursor.fetchall()
            
            print(f"\n📈 All Trades:")
            total_invested = 0
            total_pnl = 0
            
            for i, trade in enumerate(trades, 1):
                symbol, strategy, action, entry_price, quantity, timestamp, pnl, status = trade
                invested = entry_price * quantity
                total_invested += invested
                total_pnl += pnl
                
                print(f"\n{i}. {symbol}")
                print(f"   Strategy: {strategy}")
                print(f"   Action: {action}")
                print(f"   Entry: ${entry_price:.2f} x {quantity} shares = ${invested:.2f}")
                print(f"   P&L: ${pnl:.2f}")
                print(f"   Status: {status}")
                print(f"   Time: {timestamp}")
            
            print(f"\n💰 Summary:")
            print(f"   Total Invested: ${total_invested:.2f}")
            print(f"   Total P&L: ${total_pnl:.2f}")
            print(f"   Current Value: ${total_invested + total_pnl:.2f}")
    
    conn.close()

# Check backup state file
if os.path.exists('phasma_state_backup.json'):
    print(f"\n📋 Checking backup state file...")
    with open('phasma_state_backup.json', 'r') as f:
        backup = json.load(f)
    
    portfolio = backup.get('portfolio_state', {})
    print(f"Backup Portfolio:")
    print(f"   Available Capital: ${portfolio.get('available_capital', 0):.2f}")
    print(f"   Total Value: ${portfolio.get('total_portfolio_value', 0):.2f}")
    print(f"   Total Return: ${portfolio.get('total_return', 0):.2f}")
    print(f"   Total Trades: {portfolio.get('total_trades', 0)}")
    
    # Check if backup has different positions
    if 'risk_state' in backup and 'open_positions' in backup['risk_state']:
        positions = backup['risk_state']['open_positions']
        if positions:
            print(f"\n   Backup has {len(positions)} positions:")
            for symbol, pos in positions.items():
                signal = pos.get('signal', {})
                entry_price = signal.get('entry_price', 0)
                if entry_price > 0:
                    print(f"   • {symbol}: Entry ${entry_price:.2f}")

# Check trade_memory.json
if os.path.exists('trade_memory.json'):
    print(f"\n🧠 Checking trade memory...")
    with open('trade_memory.json', 'r') as f:
        trade_memory = json.load(f)
    
    if isinstance(trade_memory, dict) and 'trades' in trade_memory:
        trades = trade_memory['trades']
        print(f"Trade memory has {len(trades)} records")
        
        for trade in trades[-5:]:  # Show last 5
            print(f"   {trade}")

# Check recent logs for trade executions
print(f"\n📝 Checking recent logs...")
log_files = ['phasma_trading.log', 'main_output.log']
for log_file in log_files:
    if os.path.exists(log_file):
        print(f"\n{log_file} (last 20 lines):")
        with open(log_file, 'r') as f:
            lines = f.readlines()[-20:]
            for line in lines:
                if any(keyword in line for keyword in ['EXECUTED', 'BOUGHT', 'SOLD', 'POSITION OPENED', 'TRADE']):
                    print(f"   {line.strip()}")
