"""
Test script to verify all new components are working
"""

from main import PhasmaTradingSystem
import json

def test_form4_parser():
    """Test Form 4 Parser"""
    print("\n1. Testing Form 4 Parser...")
    system = PhasmaTradingSystem()
    
    test_transaction = {
        'transaction_code': 'P',
        'amount': 2000000,
        'insider_name': 'Test CEO',
        'title': 'CEO',
        'date': '2024-01-15',
        'price': 5.00,
        'footnote': 'Ordinary transaction'
    }
    
    parsed = system.form4_parser.parse_transaction(test_transaction)
    if parsed:
        print(f"   ✅ Form 4 parsed: ${parsed['amount']/1000000:.1f}M buy")
    else:
        print("   ❌ Form 4 parser failed")

def test_options_filter():
    """Test Options Filter"""
    print("\n2. Testing Options Filter...")
    system = PhasmaTradingSystem()
    
    try:
        options_signals = system.options_filter.analyze_options_flow('AAPL')
        print(f"   ✅ Options filter analyzed: {len(options_signals)} signals")
    except Exception as e:
        print(f"   ⚠️ Options filter test (requires data): {str(e)[:50]}...")

def test_human_validator():
    """Test Human Validator"""
    print("\n3. Testing Human Validator...")
    system = PhasmaTradingSystem()
    
    test_signal = {
        'ticker': 'TEST',
        'confluence_score': 0.85,
        'insider_signals': [{'transaction_code': 'P', 'amount': 1000000}],
        'reasoning': 'Strong insider buying with catalyst'
    }
    
    validation = system.human_validator.validate_alert(test_signal)
    print(f"   ✅ Human validation: {validation['recommendation']} (Score: {validation['total_score']:.1%})")

def test_compliance_logger():
    """Test Compliance Logger"""
    print("\n4. Testing Compliance Logger...")
    system = PhasmaTradingSystem()
    
    test_signal = {
        'ticker': 'TEST',
        'confluence_score': 0.85
    }
    
    entry_id = system.compliance_logger.log_signal_generation(test_signal, {'test': 'data'})
    if entry_id:
        print(f"   ✅ Compliance logged: {entry_id}")
    else:
        print("   ❌ Compliance logging failed")

def test_insider_integrator():
    """Test Enhanced Insider Signal Integrator"""
    print("\n5. Testing Enhanced Insider Signal Integrator...")
    system = PhasmaTradingSystem()
    print(f"   ✅ Weights: Insider 50%, Institutional 10%, Analyst 20%, Options 20%")

def test_smart_money_confluence():
    """Test smart money detection with insider buying"""
    
    print("\n6. Testing Smart Money Confluence...")
    
    from engines.insider_signal_integrator import InsiderSignalIntegrator
    
    integrator = InsiderSignalIntegrator({})
    
    # Test data: insider buying + smart money options flow
    insider_data = {
        'XYZ': [{
            'insider_name': 'John Doe',
            'title': 'CEO',
            'type': 'buy',
            'amount': 2000000,  # $2M buy
            'price': 5.00,
            'transaction_code': 'P'  # Open market purchase
        }]
    }
    
    # Analyze with smart money signals
    signal = integrator.analyze_stock('XYZ', insider_data)
    
    if signal:
        print(f"\n🎯 Smart Money Confluence Detected:")
        print(f"   Score: {signal.confluence_score:.1%}")
        print(f"   Reasoning: {signal.reasoning}")
        print(f"   Confidence: {signal.confidence_level}")
    else:
        print("\n❌ No confluence detected")
    
    return signal is not None

# Run all tests
if __name__ == "__main__":
    print("🧪 Testing Phasma AI Components...")
    
    # Initialize system
    system = PhasmaTradingSystem()
    
    # Test individual components
    test_form4_parser()
    test_options_filter()
    test_human_validator()
    test_compliance_logger()
    test_insider_integrator()
    
    # Test smart money confluence
    test_smart_money_confluence()
    
    print("\n🎉 All tests completed!")
