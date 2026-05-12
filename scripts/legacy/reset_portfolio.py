#!/usr/bin/env python3
"""
Portfolio Reset Script - Remove recent bankroll bug trades while keeping legitimate month-old trades
"""

import json
from datetime import datetime, timedelta
import os

def reset_portfolio():
    """Reset portfolio by removing trades newer than 30 days while keeping older legitimate trades"""
    
    # Load current state
    state_file = "phasma_state.json"
    backup_file = "phasma_state.json.backup"
    
    print("🔄 Loading portfolio state...")
    
    if not os.path.exists(state_file):
        print(f"❌ Error: {state_file} not found")
        return
    
    if not os.path.exists(backup_file):
        print(f"❌ Error: {backup_file} not found - create backup first!")
        return
    
    with open(state_file, 'r') as f:
        state = json.load(f)
    
    # Calculate cutoff date (30 days ago from now)
    cutoff_date = datetime.now() - timedelta(days=30)
    print(f"📅 Cutoff date: {cutoff_date.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Check if open_positions exists (nested under risk_state)
    if "risk_state" not in state or "open_positions" not in state["risk_state"]:
        print("❌ No open_positions found in state file")
        print("📋 Available top-level keys:", list(state.keys()))
        if "risk_state" in state:
            print("📋 Available risk_state keys:", list(state["risk_state"].keys()))
        return
    
    positions = state["risk_state"]["open_positions"]
    original_count = len(positions)
    print(f"📊 Original positions: {original_count}")
    
    # Filter positions by entry_time
    kept_positions = {}
    removed_positions = {}
    
    for symbol, position_data in positions.items():
        entry_time_str = position_data.get("entry_time", "")
        
        if not entry_time_str:
            print(f"⚠️  No entry_time for {symbol}, keeping by default")
            kept_positions[symbol] = position_data
            continue
        
        try:
            # Parse entry_time (ISO format: "2025-12-06T02:48:32.856214")
            entry_time = datetime.fromisoformat(entry_time_str.replace('Z', '+00:00'))
            
            if entry_time < cutoff_date:
                # Keep older trades (legitimate month-old trades)
                kept_positions[symbol] = position_data
                days_old = (datetime.now() - entry_time).days
                print(f"✅ KEEP {symbol}: {days_old} days old")
            else:
                # Remove recent trades (bankroll bug trades)
                removed_positions[symbol] = position_data
                days_old = (datetime.now() - entry_time).days
                print(f"❌ REMOVE {symbol}: {days_old} days old (too recent)")
                
        except Exception as e:
            print(f"⚠️  Error parsing entry_time for {symbol}: {e}, keeping by default")
            kept_positions[symbol] = position_data
    
    # Update state with filtered positions (nested under risk_state)
    state["risk_state"]["open_positions"] = kept_positions
    
    # Save updated state
    with open(state_file, 'w') as f:
        json.dump(state, f, indent=2)
    
    # Summary
    kept_count = len(kept_positions)
    removed_count = len(removed_positions)
    
    print(f"\n📋 SUMMARY:")
    print(f"   Original positions: {original_count}")
    print(f"   Kept (>30 days): {kept_count}")
    print(f"   Removed (<30 days): {removed_count}")
    print(f"   Portfolio cleaned: {state_file}")
    print(f"   Backup available: {backup_file}")
    
    if removed_count > 0:
        print(f"\n🧹 Removed recent trades (bankroll bug):")
        for symbol in removed_positions.keys():
            print(f"   - {symbol}")
    
    print(f"\n✅ Portfolio reset complete!")

if __name__ == "__main__":
    reset_portfolio()
