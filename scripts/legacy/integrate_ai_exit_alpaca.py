#!/usr/bin/env python3

# Connect AI Auto-Exit Manager to Alpaca
import sys
import os
_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)
def integrate_ai_exit_with_alpaca():
    """Connect the AI's exit signals to Alpaca"""
    print("🔧 Connecting AI Auto-Exit to Alpaca...")
    
    # Read the main.py to see where AutoExitManager is initialized
    print("\n📋 STEPS TO INTEGRATE:")
    print("1. ✅ AI already has AutoExitManager with exit signals")
    print("2. ✅ AutoExitManager calls self.broker_api to execute exits")
    print("3. 🔧 Need to pass Alpaca trader as broker_api")
    print("4. 🔧 Need to start monitoring positions")
    
    print("\n🎯 INTEGRATION PLAN:")
    print("1. Pass EnhancedAlpacaPaperTrader as broker_api to AutoExitManager")
    print("2. Start AutoExitManager.monitor_positions() in main loop")
    print("3. AI generates exit signals → AutoExitManager → Alpaca sells")
    
    return True

if __name__ == "__main__":
    integrate_ai_exit_with_alpaca()
