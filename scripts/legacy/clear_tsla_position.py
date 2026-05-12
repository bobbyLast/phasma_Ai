#!/usr/bin/env python3
"""Clear TSLA position from portfolio state to stop exit alerts"""

import json
import os

def clear_tsla_position():
    state_file = 'phasma_state.json'
    
    if not os.path.exists(state_file):
        print(f"State file {state_file} not found")
        return
    
    # Load the state
    with open(state_file, 'r') as f:
        state = json.load(f)
    
    # Clear any TSLA positions
    if 'portfolio' in state:
        if 'stock_positions' in state['portfolio']:
            if 'TSLA' in state['portfolio']['stock_positions']:
                del state['portfolio']['stock_positions']['TSLA']
                print("Cleared TSLA from stock_positions")
        
        if 'kalshi_positions' in state['portfolio']:
            if 'TSLA' in state['portfolio']['kalshi_positions']:
                del state['portfolio']['kalshi_positions']['TSLA']
                print("Cleared TSLA from kalshi_positions")
    
    # Clear any signals with TSLA
    if 'signals' in state:
        if 'TSLA' in state['signals']:
            del state['signals']['TSLA']
            print("Cleared TSLA from signals")
    
    # Save the updated state
    with open(state_file, 'w') as f:
        json.dump(state, f, indent=2)
    
    print("TSLA position cleared successfully")

if __name__ == "__main__":
    clear_tsla_position()
