import json
import os
from datetime import datetime

print("📊 Documenting All AI Trades Before Reset")
print("=" * 60)

# Create a trade documentation file
doc_file = "trade_history_" + datetime.now().strftime("%Y%m%d_%H%M%S") + ".json"
trade_history = {
    "documentation_date": datetime.now().isoformat(),
    "initial_bankroll": 100,
    "bankroll_allocation": {
        "stock_trading": 50,
        "kalshi_trading": 50
    },
    "trades_found": [],
    "open_positions": [],
    "summary": {}
}

# 1. Check logs for executed trades
print("\n🔍 Scanning logs for trade executions...")
log_files = ['phasma_trading.log', 'main_output.log', 'phasma.log']

for log_file in log_files:
    if os.path.exists(log_file):
        print(f"\nChecking {log_file}...")
        with open(log_file, 'r') as f:
            lines = f.readlines()
            
        for line in lines:
            if "Trade" in line and "executed" in line:
                # Extract trade number
                try:
                    trade_num = line.split("Trade")[1].split()[0]
                    timestamp = line.split(" - ")[0]
                    trade_history["trades_found"].append({
                        "source": log_file,
                        "trade_number": trade_num,
                        "timestamp": timestamp,
                        "status": "executed",
                        "details": line.strip()
                    })
                except:
                    pass

# 2. Check state file for positions
if os.path.exists('phasma_state.json'):
    print("\n📋 Checking state file for positions...")
    with open('phasma_state.json', 'r') as f:
        state = json.load(f)
    
    portfolio = state.get('portfolio_state', {})
    
    # Document portfolio status
    trade_history["portfolio_status"] = {
        "available_capital": portfolio.get('available_capital', 0),
        "total_portfolio_value": portfolio.get('total_portfolio_value', 0),
        "total_return": portfolio.get('total_return', 0),
        "total_trades": portfolio.get('total_trades', 0)
    }
    
    # Document open positions
    if 'risk_state' in state and 'open_positions' in state['risk_state']:
        positions = state['risk_state']['open_positions']
        
        for symbol, pos_data in positions.items():
            signal = pos_data.get('signal', {})
            position = {
                "symbol": symbol,
                "trade_type": signal.get('trade_type', 'Unknown'),
                "action": signal.get('action', 'Unknown'),
                "entry_price": signal.get('entry_price', 0),
                "target_price": signal.get('target_price', 0),
                "entry_time": pos_data.get('entry_time', 'Unknown'),
                "quantity": pos_data.get('quantity', 0),
                "status": "open"
            }
            trade_history["open_positions"].append(position)

# 3. Check databases
db_files = ['unified_main.db', 'trades.db', 'profit_maximization_exits.db']
for db_file in db_files:
    if os.path.exists(db_file):
        print(f"\n📊 Checking {db_file}...")
        trade_history["databases_checked"] = trade_history.get("databases_checked", [])
        trade_history["databases_checked"].append(db_file)

# 4. Create summary
trade_history["summary"] = {
    "total_trades_executed": len(trade_history["trades_found"]),
    "total_open_positions": len(trade_history["open_positions"]),
    "bankroll_used": trade_history["portfolio_status"]["available_capital"],
    "current_portfolio_value": trade_history["portfolio_status"]["total_portfolio_value"]
}

# 5. Save documentation
with open(doc_file, 'w') as f:
    json.dump(trade_history, f, indent=2)

print(f"\n✅ Trade documentation saved to: {doc_file}")
print(f"\n📊 SUMMARY:")
print(f"   Trades Executed: {trade_history['summary']['total_trades_executed']}")
print(f"   Open Positions: {trade_history['summary']['total_open_positions']}")
print(f"   Bankroll Used: ${trade_history['summary']['bankroll_used']:.2f}")
print(f"   Portfolio Value: ${trade_history['summary']['current_portfolio_value']:.2f}")

if trade_history["trades_found"]:
    print(f"\n📈 Trades Found:")
    for trade in trade_history["trades_found"]:
        print(f"   • Trade #{trade['trade_number']} at {trade['timestamp']}")

if trade_history["open_positions"]:
    print(f"\n📋 Open Positions:")
    for pos in trade_history["open_positions"]:
        print(f"   • {pos['symbol']}: {pos['action']} @ ${pos['entry_price']:.2f}")

print(f"\n" + "=" * 60)
print("Documentation complete. Ready to reset the AI.")
