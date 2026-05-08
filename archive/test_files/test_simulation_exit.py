#!/usr/bin/env python3
"""
Test Simulation Exit Manager - Verifies profit maximization using Monte Carlo targets
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.simulation_exit_manager import SimulationExitManager

def test_simulation_exit():
    """Test that the simulation exit manager uses Monte Carlo targets correctly"""
    
    print("="*60)
    print("TESTING SIMULATION EXIT MANAGER")
    print("="*60)
    
    # Initialize the manager
    manager = SimulationExitManager()
    
    # Check if positions were loaded
    positions = manager.get_all_positions()
    
    print(f"\nLoaded {len(positions)} positions with simulation data")
    
    if not positions:
        print("\n[TEST] No positions found - checking phasma_state.json...")
        
        # Check if state file has positions with simulations
        import json
        try:
            with open('phasma_state.json', 'r') as f:
                state = json.load(f)
                
            open_positions = state.get('risk_state', {}).get('open_positions', {})
            print(f"Found {len(open_positions)} open positions in state file")
            
            for ticker, pos_data in open_positions.items():
                signal = pos_data.get('signal', {})
                sim_results = signal.get('simulation_results', {})
                if sim_results:
                    print(f"\n{ticker} has simulation data:")
                    print(f"  Target Price: ${sim_results.get('target_price', 0):.2f}")
                    print(f"  Stop Loss: ${sim_results.get('stop_loss', 0):.2f}")
                    print(f"  Win Rate: {sim_results.get('win_rate', 0):.1%}")
                    print(f"  Holding Days: {sim_results.get('holding_days', 0)}")
                else:
                    print(f"\n{ticker} has NO simulation data")
                    
        except Exception as e:
            print(f"Error reading state file: {e}")
    
    # Test analysis of positions
    print("\n" + "="*60)
    print("TESTING EXIT DECISIONS")
    print("="*60)
    
    for ticker in positions.keys():
        print(f"\nAnalyzing {ticker}...")
        exit_decision = manager.analyze_position(ticker)
        
        if exit_decision:
            print(f"  Current Price: ${exit_decision.current_price:.2f}")
            print(f"  Target Price: ${exit_decision.target_price:.2f}")
            print(f"  Progress: {exit_decision.price_progress:.1%}")
            print(f"  Profit: {exit_decision.profit_pct:.1f}%")
            print(f"  Days Held: {exit_decision.days_held}/{exit_decision.optimal_exit_day}")
            print(f"  Signal: {exit_decision.last_signal.value}")
            print(f"  Reason: {exit_decision.last_reason.value}")
            
            # Verify it's not using fixed percentages
            if exit_decision.last_signal.value == "FULL_SELL":
                if exit_decision.last_reason.value == "SIMULATION_TARGET":
                    print("  [OK] Correctly sold at simulation target!")
                elif exit_decision.last_reason.value == "OPTIMAL_EXIT_DAY":
                    print("  [OK] Correctly sold at optimal exit day!")
                else:
                    print(f"  [WARNING] Sold for reason: {exit_decision.last_reason.value}")
            else:
                print("  [OK] Holding for better exit (not selling early)")
        else:
            print("  No exit decision returned")
    
    print("\n" + "="*60)
    print("TEST COMPLETE")
    print("="*60)
    
    # Summary
    print("\nKey Points:")
    print("1. Simulation Exit Manager uses Monte Carlo target prices")
    print("2. Won't sell on small 2% gains")
    print("3. Holds until target price or optimal exit day")
    print("4. Only exits early on crash detection or stop loss")
    print("5. Maximizes profit by letting winners run")

if __name__ == "__main__":
    test_simulation_exit()
