import json
import os
import sqlite3
from datetime import datetime

print("🔄 RESETTING PHASMA AI WITH PROPER BANKROLL ALLOCATION")
print("=" * 60)

# 1. Backup current state
backup_file = f"phasma_state_backup_before_reset_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
if os.path.exists('phasma_state.json'):
    os.rename('phasma_state.json', backup_file)
    print(f"✅ Backed up current state to: {backup_file}")

# 2. Create new state with proper bankroll allocation
new_state = {
    "version": "2.0",
    "reset_date": datetime.now().isoformat(),
    "bankroll_allocation": {
        "total_bankroll": 100,
        "stock_trading": {
            "allocated": 50,
            "available": 50,
            "used": 0
        },
        "kalshi_trading": {
            "allocated": 50,
            "available": 50,
            "used": 0
        }
    },
    "portfolio_state": {
        "available_capital": 100.0,
        "total_portfolio_value": 100.0,
        "total_return": 0.0,
        "total_trades": 0,
        "win_rate": 0.0,
        "open_positions_count": 0,
        "open_positions": []
    },
    "risk_state": {
        "open_positions": {},
        "risk_metrics": {
            "max_position_size": 10.0,
            "max_risk_per_trade": 0.02,
            "current_risk": 0.0
        }
    },
    "trading_state": {
        "last_trade_id": 0,
        "daily_trades": 0,
        "last_reset": datetime.now().isoformat()
    }
}

# Save new state
with open('phasma_state.json', 'w') as f:
    json.dump(new_state, f, indent=2)
print("✅ Created new state with proper bankroll allocation")

# 3. Update config.json to reflect proper allocation
config = {
    "bankroll": 100,
    "trading_mode": "stocks_and_kalshi",
    "kalshi_enabled": True,
    "bankroll_allocation": {
        "stock_trading": 50,
        "kalshi_trading": 50
    },
    "trading": {
        "bankroll": 100,
        "risk_per_trade": 0.02,
        "min_contracts": 2,
        "max_contracts": 20,
        "max_concurrent_trades": 8,
        "stock_trading": {
            "enabled": True,
            "bankroll": 50,
            "max_positions": 5,
            "position_size": 10
        },
        "kalshi_trading": {
            "enabled": True,
            "bankroll": 50,
            "max_positions": 10,
            "min_edge_threshold": 0.08,
            "max_bet_size": 5
        }
    },
    "global_macro": {"japan_yield_threshold": 1.5},
    "insider_integrator": {"min_insider_amount": 1000000},
    "pump_dump": {"volume_surge_threshold": 3.0}
}

with open('config.json', 'w') as f:
    json.dump(config, f, indent=2)
print("✅ Updated config.json with proper bankroll allocation")

# 4. Clear and reset databases
databases_to_reset = [
    'unified_main.db',
    'trades.db',
    'profit_maximization_exits.db',
    'insider_accumulation.db'
]

for db_file in databases_to_reset:
    if os.path.exists(db_file):
        os.remove(db_file)
        print(f"✅ Removed old database: {db_file}")

# Create fresh unified_main.db with proper structure
conn = sqlite3.connect('unified_main.db')
cursor = conn.cursor()

# Create trades table with platform tracking
cursor.execute("""
    CREATE TABLE trades (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        platform TEXT NOT NULL,  -- 'stock' or 'kalshi'
        symbol TEXT NOT NULL,
        action TEXT NOT NULL,
        entry_price REAL,
        quantity INTEGER,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        profit_loss REAL DEFAULT 0,
        status TEXT DEFAULT 'open',
        bankroll_used REAL
    )
""")

# Create positions table
cursor.execute("""
    CREATE TABLE positions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        platform TEXT NOT NULL,
        symbol TEXT NOT NULL,
        quantity INTEGER,
        entry_price REAL,
        current_price REAL,
        status TEXT DEFAULT 'open',
        entry_date DATETIME DEFAULT CURRENT_TIMESTAMP
    )
""")

# Create bankroll tracking table
cursor.execute("""
    CREATE TABLE bankroll_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        platform TEXT NOT NULL,
        allocated REAL,
        used REAL,
        available REAL,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        notes TEXT
    )
""")

# Insert initial bankroll allocation
cursor.execute("""
    INSERT INTO bankroll_log (platform, allocated, used, available, notes)
    VALUES ('stock', 50, 0, 50, 'Initial allocation'),
           ('kalshi', 50, 0, 50, 'Initial allocation')
""")

conn.commit()
conn.close()
print("✅ Created fresh database with proper tracking")

# 5. Create a bankroll monitor to track allocation
bankroll_monitor = {
    "created": datetime.now().isoformat(),
    "total_bankroll": 100,
    "allocations": {
        "stock_trading": {
            "allocated": 50,
            "available": 50,
            "used": 0,
            "trades_count": 0
        },
        "kalshi_trading": {
            "allocated": 50,
            "available": 50,
            "used": 0,
            "trades_count": 0
        }
    },
    "rules": {
        "max_stock_position": 10,  # Max $10 per stock trade
        "max_kalshi_bet": 5,      # Max $5 per Kalshi bet
        "stock_max_positions": 5,
        "kalshi_max_positions": 10
    }
}

with open('bankroll_monitor.json', 'w') as f:
    json.dump(bankroll_monitor, f, indent=2)
print("✅ Created bankroll monitor for tracking allocations")

print("\n" + "=" * 60)
print("✅ AI RESET COMPLETE!")
print("\n📊 BANKROLL ALLOCATION:")
print("   Total Bankroll: $100")
print("   Stock Trading: $50 (5 positions max @ $10 each)")
print("   Kalshi Trading: $50 (10 positions max @ $5 each)")
print("\n📋 NEXT STEPS:")
print("   1. Run 'python main.py' to start fresh trading")
print("   2. AI will use dynamic scanner for fresh stocks")
print("   3. Weather markets will use consistency engine")
print("   4. Bankroll monitor will track allocations")
print("\n⚠️  IMPORTANT:")
print("   - Each platform has its own $50 allocation")
print("   - AI cannot exceed allocation limits")
print("   - All trades are now properly tracked")
