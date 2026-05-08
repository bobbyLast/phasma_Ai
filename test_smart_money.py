"""
Test smart money confluence with simulated data
"""

from engines.insider_signal_integrator import InsiderSignalIntegrator
from engines.options_flow_filter import OptionsFlowFilter

def test_smart_money_simulation():
    """Test smart money detection with simulated insider + options data"""
    
    print("\n🎯 Testing Smart Money Confluence (Simulated)...")
    
    # Create integrator with lower threshold for testing
    config = {
        'insider_integrator': {
            'confluence_threshold': 0.3,  # Lower to 30%
            'max_price': 500.0  # Increase max price to $500
        }
    }
    integrator = InsiderSignalIntegrator(config)
    
    # Create mock options filter with simulated smart money signals
    class MockOptionsFilter:
        def analyze_options_flow(self, symbol):
            print(f"   [MOCK OPTIONS] Simulating smart money sweep for {symbol}")
            # Simulate a smart money sweep detection
            return [{
                'type': 'sweep_trade',
                'option_type': 'calls',
                'strike': 7.50,
                'volume': 2500,  # Large sweep
                'open_interest': 500,
                'confidence': 0.85,
                'reasoning': 'Sweep: 2500 contracts (5.0x avg volume)',
                'final_score': 0.85,
                'multiple': 5.0
            }]
        
        def calculate_bullish_bearish_ratio(self, signals):
            return {'bullish': 0.8, 'bearish': 0.2}
    
    # Replace the options filter with our mock
    integrator.options_filter = MockOptionsFilter()
    
    # Test data: insider buying + smart money options flow
    insider_data = {
        'AAPL': [{
            'insider_name': 'Tim Cook',
            'title': 'CEO',
            'type': 'buy',
            'amount': 2000000,  # $2M buy
            'price': 150.00,
            'transaction_code': 'P'  # Open market purchase
        }]
    }
    
    print(f"\n   [TEST] Analyzing AAPL with insider data...")
    print(f"   [TEST] Insider amount: ${insider_data['AAPL'][0]['amount']/1000000:.1f}M")
    
    # Analyze with smart money signals
    signal = integrator.analyze_stock('AAPL', insider_data)
    
    print(f"\n   [RESULT] Signal returned: {signal is not None}")
    
    if signal:
        print(f"\n🎯 SMART MONEY CONFLUENCE DETECTED:")
        print(f"   Score: {signal.confluence_score:.1%}")
        print(f"   Reasoning: {signal.reasoning}")
        print(f"   Confidence: {signal.confidence_level}")
        
        # Check if smart money was detected
        if "🎯 SMART MONEY" in signal.reasoning:
            print(f"\n✅ Smart money properly identified in reasoning!")
        
        if signal.confluence_score > 0.5:
            print(f"\n✅ Strong confluence score (>50%) achieved!")
            
    else:
        print("\n❌ No confluence detected")
    
    return signal

if __name__ == "__main__":
    # Run the smart money test
    signal = test_smart_money_simulation()
    
    if signal:
        print("\n✅ Smart money integration working correctly!")
    else:
        print("\n❌ Smart money integration needs adjustment")
