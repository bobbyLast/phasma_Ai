#!/usr/bin/env python3
"""
Phasma AI 24/7 Monitoring Startup Script
Starts continuous monitoring for trading opportunities
"""

import sys
import os
import asyncio
import logging
from datetime import datetime

def main():
    """Start 24/7 monitoring"""
    print("🚀 PHASMA AI 24/7 TRADING MONITOR")
    print("=" * 50)
    print(f"🕐 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Project root (repo root), not this file's directory
    _here = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(_here, "..", ".."))
    os.chdir(project_root)
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

    # Check if config exists
    if not os.path.exists("config.json"):
        print("❌ config.json not found!")
        print("💡 Make sure you're running from the Phasma AI directory")
        return 1

    # Import and run the monitoring system
    try:
        from main import PhasmaTradingSystem, PhasmaConfig

        print("🔧 Initializing Phasma AI Trading System...")

        # Initialize with full configuration
        config = PhasmaConfig("config.json")
        system = PhasmaTradingSystem("config.json")

        # Enable monitoring mode in config
        config.set('monitoring.enabled', True)

        # Get monitoring interval from command line or config
        interval = 5  # Default 5 minutes
        if len(sys.argv) > 1:
            try:
                interval = int(sys.argv[1])
            except ValueError:
                print(f"⚠️ Invalid interval '{sys.argv[1]}', using default 5 minutes")

        # Validate interval
        if interval < 1 or interval > 60:
            print(f"⚠️ Invalid interval {interval}, must be 1-60 minutes. Using default 5 minutes")
            interval = 5

        print(f"📊 Monitoring interval: {interval} minutes")
        print("🟢 Starting continuous monitoring...")
        print("🛑 Press Ctrl+C to stop")
        print()

        # Setup logging for monitoring
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - MONITOR - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('phasma_monitor.log'),
                logging.StreamHandler()
            ]
        )

        # Log monitoring start
        logging.info(f"Starting 24/7 monitoring with {interval} minute intervals")

        # Start 24/7 monitoring
        result = asyncio.run(system.run_24_7_monitor(interval))

        # Log monitoring end
        logging.info(f"Monitoring session ended at {datetime.now().strftime('%H:%M:%S')}")

    except KeyboardInterrupt:
        print(f"\n🛑 Monitoring stopped by user at {datetime.now().strftime('%H:%M:%S')}")
        logging.info("Monitoring stopped by user")
        return 0
    except Exception as e:
        print(f"\n❌ Error starting monitoring: {e}")
        logging.error(f"Error starting monitoring: {e}")
        import traceback
        logging.error(traceback.format_exc())
        return 1

    print(f"\n✅ Monitoring session ended at {datetime.now().strftime('%H:%M:%S')}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
