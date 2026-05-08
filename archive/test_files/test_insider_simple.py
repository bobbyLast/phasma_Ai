import sys
sys.path.insert(0, ".")

from utils.insider_monitor import InsiderMonitor

config = {
    "insider_monitor": {
        "enabled": True,
        "penny_only": False,
        "min_value": 20000,
        "tickers": [],
        "lookback_days": 3
    }
}

print("=== Starting Insider Monitor Test ===")
monitor = InsiderMonitor(config)
results = monitor.fetch_recent_buys()
print(f"\n=== Final Results: {len(results)} opportunities ===")
for r in results:
    print(f"- {r['ticker']}: {r['transaction_type']} at ${r['price']:.2f}")
