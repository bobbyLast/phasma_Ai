"""
Test AI bubble awareness and macro context in insider signals
"""

from engines.insider_signal_integrator import InsiderSignalIntegrator

def test_ai_bubble_awareness():
    """Test how system handles AI bubble and macro context"""
    
    print("\n🤖 Testing AI Bubble Awareness & Macro Context...")
    
    # Create integrator with low threshold for testing
    config = {
        'insider_integrator': {
            'confluence_threshold': 0.3,
            'max_price': 1000.0
        }
    }
    integrator = InsiderSignalIntegrator(config)
    
    # Mock options filter
    class MockOptionsFilter:
        def analyze_options_flow(self, symbol):
            return [{
                'type': 'sweep_trade',
                'option_type': 'calls',
                'strike': 500.0,
                'volume': 10000,
                'open_interest': 2000,
                'confidence': 0.90,
                'reasoning': 'Massive sweep: 10K contracts (10x avg)',
                'final_score': 0.90,
                'multiple': 10.0
            }]
        
        def calculate_bullish_bearish_ratio(self, signals):
            return {'bullish': 0.9, 'bearish': 0.1}
    
    integrator.options_filter = MockOptionsFilter()
    
    # Test cases
    test_cases = [
        {
            'ticker': 'NVDA',
            'name': 'NVIDIA - AI Infrastructure',
            'insider': {
                'insider_name': 'Jensen Huang',
                'title': 'CEO',
                'type': 'buy',
                'amount': 5000000,  # $5M buy
                'price': 500.00,
                'transaction_code': 'P'
            }
        },
        {
            'ticker': 'CEG',
            'name': 'Constellation Energy - Nuclear for AI',
            'insider': {
                'insider_name': 'Joe Dominguez',
                'title': 'CEO',
                'type': 'buy',
                'amount': 2000000,  # $2M buy
                'price': 150.00,
                'transaction_code': 'P'
            }
        },
        {
            'ticker': 'SMCI',
            'name': 'Super Micro - AI Servers',
            'insider': {
                'insider_name': 'Charles Liang',
                'title': 'CEO',
                'type': 'buy',
                'amount': 3000000,  # $3M buy
                'price': 300.00,
                'transaction_code': 'P'
            }
        }
    ]
    
    for test in test_cases:
        print(f"\n--- Testing {test['name']} ({test['ticker']}) ---")
        
        insider_data = {test['ticker']: [test['insider']]}
        signal = integrator.analyze_stock(test['ticker'], insider_data)
        
        if signal:
            print(f"\n✅ SIGNAL DETECTED:")
            print(f"   Score: {signal.confluence_score:.1%}")
            print(f"   Confidence: {signal.confidence_level}")
            print(f"   Reasoning: {signal.reasoning}")
            
            # Check for macro context
            if "🌍" in signal.reasoning:
                print(f"\n✅ Macro context included!")
            
            # Check for AI bubble warning
            if "Bubble Alert" in signal.reasoning:
                print(f"\n⚠️ AI BUBBLE WARNING ACTIVATED!")
            
            # Check for smart money
            if "🎯 SMART MONEY" in signal.reasoning:
                print(f"\n🎯 Smart money confluence detected!")
        else:
            print(f"\n❌ No signal detected")
    
    print("\n" + "="*60)
    print("📊 MACRO INTELLIGENCE SUMMARY:")
    print("• AI Infrastructure stocks get 15% boost for massive capex")
    print("• Energy stocks get 8% boost for AI power demand")
    print("• P/E ratios monitored for bubble warnings")
    print("• Sector capital flows integrated into signal scoring")
    print("="*60)

if __name__ == "__main__":
    test_ai_bubble_awareness()
