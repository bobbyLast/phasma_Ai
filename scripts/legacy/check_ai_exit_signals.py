#!/usr/bin/env python3

# Integrate AI Auto-Sell with Alpaca
import sys
import os
_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)
def check_ai_exit_signals():
    """Check if AI has existing exit signals and integrate with Alpaca"""
    print("🔧 Checking AI Exit Signal Integration...")
    
    # Check for exit-related files
    exit_files = [
        "utils/exit_strategy_manager.py",
        "utils/simulation_exit_manager.py",
        "engines/auto_exit_manager.py"
    ]
    
    for file in exit_files:
        if os.path.exists(file):
            print(f"✅ Found: {file}")
        else:
            print(f"❌ Missing: {file}")
    
    # Check main.py for exit logic
    print("\n🔍 Checking main.py for exit logic...")
    
    with open("main.py", "r") as f:
        content = f.read()
        
        if "review_open_positions" in content:
            print("✅ Found: review_open_positions method")
        
        if "execute_sell" in content:
            print("✅ Found: execute_sell logic")
        
        if "exit_strategy" in content:
            print("✅ Found: exit_strategy references")
        
        if "auto_exit" in content:
            print("✅ Found: auto_exit references")
    
    print("\n🎯 NEEDED INTEGRATION:")
    print("1. AI generates exit signals (already exists)")
    print("2. Connect AI exit signals to Alpaca")
    print("3. Execute Alpaca sells on AI exit signals")
    print("4. Track AI exits in Alpaca positions")

if __name__ == "__main__":
    check_ai_exit_signals()
