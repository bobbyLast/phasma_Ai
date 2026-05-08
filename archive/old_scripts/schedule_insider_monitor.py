"""
Schedule insider trading monitor to run multiple times per day.
Run this script to set up automated monitoring throughout trading hours.
"""

import schedule
import time
import subprocess
import sys
from datetime import datetime

def run_insider_monitor():
    """Execute the insider trading monitor."""
    print(f"\n{'='*60}")
    print(f"🔍 INSIDER TRADING MONITOR - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}")
    
    try:
        # Run the main system
        result = subprocess.run([sys.executable, 'main.py'], 
                              capture_output=True, 
                              text=True, 
                              cwd='c:\\Users\\kyran\\CascadeProjects\\phasma_Ai')
        
        # Print output
        if result.stdout:
            print(result.stdout)
        
        # Check for errors
        if result.returncode != 0:
            print(f"❌ Error running insider monitor: {result.stderr}")
    
    except Exception as e:
        print(f"❌ Failed to run insider monitor: {e}")

def main():
    """Set up and run the scheduler."""
    print("🚀 Starting Insider Trading Monitor Scheduler")
    print("📅 Schedule:")
    print("   - Pre-market: 8:00 AM ET")
    print("   - Midday: 12:00 PM ET") 
    print("   - Post-close: 4:30 PM ET")
    print("   - Overnight: 10:00 PM ET")
    print("\nPress Ctrl+C to stop\n")
    
    # Schedule runs
    schedule.every().day.at("08:00").do(run_insider_monitor)  # Pre-market
    schedule.every().day.at("12:00").do(run_insider_monitor)  # Midday
    schedule.every().day.at("16:30").do(run_insider_monitor)  # Post-close
    schedule.every().day.at("22:00").do(run_insider_monitor)  # Overnight
    
    # Run immediately on start
    print("🏃 Running initial check...")
    run_insider_monitor()
    
    # Keep scheduler running
    while True:
        schedule.run_pending()
        time.sleep(60)  # Check every minute

if __name__ == "__main__":
    main()
