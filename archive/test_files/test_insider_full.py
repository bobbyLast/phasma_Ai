import sys
import time
from utils.insider_monitor import InsiderMonitor

# Configure insider monitor
config = {
    "insider_monitor": {
        "enabled": True,
        "penny_only": False,
        "min_value": 20000,
        "tickers": [],
        "lookback_days": 3
    }
}

# Create monitor
monitor = InsiderMonitor(config)

# Redirect all output to file
with open('insider_full_output.txt', 'w') as f:
    # Save original stdout
    import os
    if hasattr(os, 'dup'):
        original_stdout = os.dup(1)
    
    try:
        import subprocess
        result = subprocess.run([sys.executable, '-c', '''
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

monitor = InsiderMonitor(config)
print("=== Starting Insider Monitor Test ===")
results = monitor.fetch_recent_buys()
print(f"\n=== Final Results: {len(results)} opportunities ===")
for r in results:
    print(f"- {r['ticker']}: {r['transaction_type']} at ${r['price']:.2f}")
'''], capture_output=True, text=True, cwd='c:\\Users\\kyran\\CascadeProjects\\phasma_Ai')
        
        f.write(result.stdout)
        f.write("\n\n=== STDERR ===\n")
        f.write(result.stderr)
        
    except Exception as e:
        f.write(f"Error: {e}")

print("Test complete. Check insider_full_output.txt for full logs.")
