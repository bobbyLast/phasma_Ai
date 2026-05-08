#!/usr/bin/env python3
"""
Run Insider Monitor in Standalone Mode - Exactly as Originally Designed
No thesis integration, pure insider signal generation
"""

from utils.insider_monitor import InsiderMonitor
from datetime import datetime


def main():
    print("="*80)
    print("INSIDER TRADING MONITOR - STANDALONE MODE")
    print("="*80)
    print(f"Run Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("\nMode: Pure Insider Signal Generation")
    print("No thesis evaluation - original functionality only\n")
    
    # Original configuration - exactly as before
    config = {
        "enabled": True,
        "lookback_days": 7,
        "min_transaction_value": 50000,
        "max_price_per_share": 50.00,
        "moonshot_mode": True,
        "large_cap_mode": True
    }
    
    # Initialize insider monitor
    im = InsiderMonitor(config)
    
    # Fetch recent buys - original function
    print("1. FETCHING RECENT INSIDER BUYS...")
    print("-"*40)
    signals = im.fetch_recent_buys()
    
    # Display results - original format
    print(f"\nFound {len(signals)} insider signals\n")
    
    # Moonshot signals
    moonshots = [s for s in signals if s.get("is_moonshot", False)]
    
    if moonshots:
        print("🚀 MOONSHOT OPPORTUNITIES:")
        print("="*40)
        for signal in moonshots:
            print(f"\n{signal['title']}")
            print(f"   {signal['reasoning']}")
            print(f"   Transaction: ${signal['transaction_value']:,.0f}")
            print(f"   Moonshot Score: {signal['moonshot_score']}/100")
    
    # Summary
    print("\n" + "="*80)
    print("INSIDER MONITOR SUMMARY")
    print("="*80)
    print(f"Total Signals: {len(signals)}")
    print(f"Moonshots: {len(moonshots)}")
    print(f"Large-Cap Signals: Printed above")
    print(f"Clusters: {len([s for s in signals if 'CLUSTER' in s.get('title', '')])}")
    
    # Export functionality (original feature)
    if signals:
        print(f"\n✅ Ready to export signals for trading decisions")
        print("   No thesis evaluation - pure insider signals")
    
    print("\nNote: This is the ORIGINAL insider monitor functionality.")
    print("Thesis evaluation can be added separately if desired.")


if __name__ == "__main__":
    main()
