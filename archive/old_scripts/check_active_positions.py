import json
import os
from datetime import datetime

# Check for active positions in the state file
state_file = 'phasma_state.json'

if os.path.exists(state_file):
    with open(state_file, 'r') as f:
        state = json.load(f)
    
    print("🔍 Checking Active Positions")
    print("=" * 50)
    
    # Check risk state for open positions
    if 'risk_state' in state and 'open_positions' in state['risk_state']:
        open_positions = state['risk_state']['open_positions']
        
        if open_positions:
            print(f"\nFound {len(open_positions)} open positions:")
            
            for symbol, pos_data in open_positions.items():
                signal = pos_data.get('signal', {})
                entry_time = pos_data.get('entry_time', 'Unknown')
                trade_type = signal.get('trade_type', 'Unknown')
                action = signal.get('action', 'Unknown')
                entry_price = signal.get('entry_price', 0)
                target_price = signal.get('target_price', 0)
                
                print(f"\n📊 {symbol}")
                print(f"   Type: {trade_type}")
                print(f"   Action: {action}")
                print(f"   Entry: ${entry_price:.2f}")
                print(f"   Target: ${target_price:.2f}")
                print(f"   Entry Time: {entry_time}")
                
                # Check if it has simulation results
                if 'simulation_results' in signal:
                    sim = signal['simulation_results']
                    print(f"   Win Rate: {sim.get('win_rate', 0):.1%}")
                    print(f"   Expected Return: {sim.get('expected_return', 0):.1%}")
        else:
            print("\n❌ No open positions found")
    else:
        print("\n❌ No risk_state or open_positions in state file")
    
    # Check portfolio state
    if 'portfolio_state' in state:
        portfolio = state['portfolio_state']
        print(f"\n💰 Portfolio Status:")
        print(f"   Available Capital: ${portfolio.get('available_capital', 0):.2f}")
        print(f"   Total Value: ${portfolio.get('total_portfolio_value', 0):.2f}")
        print(f"   Open Positions Count: {portfolio.get('open_positions_count', 0)}")
        
        if portfolio.get('open_positions'):
            print(f"\n   Open Positions in Portfolio:")
            for pos in portfolio['open_positions'][:5]:  # Show first 5
                print(f"   • {pos['symbol']}: {pos['quantity']} shares @ ${pos['avg_cost']:.2f}")
else:
    print(f"❌ State file not found: {state_file}")
