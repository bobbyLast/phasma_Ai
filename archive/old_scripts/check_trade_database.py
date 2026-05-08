import sqlite3
import os
from datetime import datetime

# Check the trade database for actual executed trades
db_files = ['trades.db', 'phasma_trades.db']

for db_file in db_files:
    if os.path.exists(db_file):
        print(f"\n📊 Checking {db_file}")
        print("=" * 50)
        
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        
        # Check tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print(f"Tables: {[t[0] for t in tables]}")
        
        # Check recent trades
        if any('trades' in t[0] for t in tables):
            cursor.execute("SELECT * FROM trades ORDER BY timestamp DESC LIMIT 10")
            trades = cursor.fetchall()
            
            if trades:
                print(f"\nRecent Trades (last 10):")
                for trade in trades:
                    print(f"  {trade}")
            else:
                print("\nNo trades found")
        
        # Check positions table if exists
        if any('position' in t[0].lower() for t in tables):
            cursor.execute("SELECT * FROM positions WHERE status='active'")
            positions = cursor.fetchall()
            
            if positions:
                print(f"\nActive Positions:")
                for pos in positions:
                    print(f"  {pos}")
            else:
                print("\nNo active positions in database")
        
        conn.close()

# Also check if there's a unified system tracking
print("\n🔍 Unified System Check")
print("=" * 50)

# Check for unified trading system
if os.path.exists('unified_system_state.json'):
    with open('unified_system_state.json', 'r') as f:
        state = json.load(f)
    
    if 'active_positions' in state:
        positions = state['active_positions']
        if positions:
            print(f"Found {len(positions)} positions in unified system:")
            for symbol, pos in positions.items():
                print(f"  {symbol}: {pos}")
        else:
            print("No active positions in unified system")
