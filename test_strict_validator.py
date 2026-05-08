#!/usr/bin/env python3
"""
Test the strict data validator
"""

from utils.strict_data_validator import StrictDataValidator, validate_data_or_skip, is_mock_data

def test_strict_validator():
    """Test the strict data validator"""
    print("🔒 Testing Strict Data Validator")
    print("=" * 50)
    
    validator = StrictDataValidator()
    
    # Test cases
    test_cases = [
        {
            'name': 'Valid real data',
            'data': {
                'symbol': 'AAPL',
                'price': 175.50,
                'volume': 1000000,
                'source': 'yahoo',
                'timestamp': '2026-02-10T18:40:00'
            },
            'should_pass': True
        },
        {
            'name': 'Mock data source',
            'data': {
                'symbol': 'AAPL',
                'price': 175.50,
                'source': 'mock'
            },
            'should_pass': False
        },
        {
            'name': 'Simulated data source',
            'data': {
                'symbol': 'AAPL',
                'price': 175.50,
                'source': 'simulated'
            },
            'should_pass': False
        },
        {
            'name': 'Fake symbol',
            'data': {
                'symbol': 'TEST_FAKE',
                'price': 175.50,
                'source': 'yahoo'
            },
            'should_pass': False
        },
        {
            'name': 'Price too high',
            'data': {
                'symbol': 'AAPL',
                'price': 200000,  # Over $100k threshold
                'source': 'yahoo'
            },
            'should_pass': False
        },
        {
            'name': 'Negative volume',
            'data': {
                'symbol': 'AAPL',
                'price': 175.50,
                'volume': -100,
                'source': 'yahoo'
            },
            'should_pass': False
        },
        {
            'name': 'Valid signal',
            'data': {
                'symbol': 'MSFT',
                'action': 'BUY',
                'confidence': 0.75,
                'source': 'finnhub',
                'price': 380.25
            },
            'should_pass': True
        },
        {
            'name': 'Invalid confidence',
            'data': {
                'symbol': 'MSFT',
                'action': 'BUY',
                'confidence': 1.5,  # Over 100%
                'source': 'finnhub'
            },
            'should_pass': False
        }
    ]
    
    print("\nTest Results:")
    print("-" * 50)
    
    passed = 0
    failed = 0
    
    for test in test_cases:
        if 'action' in test['data']:
            # It's a signal
            result = validator.validate_signal(test['data'])
            test_type = 'Signal'
        else:
            # It's price data
            result = validator.validate_price_data(test['data'])
            test_type = 'Price'
        
        status = "✅ PASS" if result == test['should_pass'] else "❌ FAIL"
        if result == test['should_pass']:
            passed += 1
        else:
            failed += 1
        
        print(f"{status} | {test['name']} ({test_type})")
        if result != test['should_pass']:
            print(f"       Expected: {test['should_pass']}, Got: {result}")
    
    print("-" * 50)
    print(f"\nSummary: {passed} passed, {failed} failed")
    
    # Test convenience functions
    print("\nConvenience Function Tests:")
    print("-" * 50)
    
    # Test validate_data_or_skip
    real_data = {'symbol': 'AAPL', 'price': 175.50, 'source': 'yahoo'}
    fake_data = {'symbol': 'AAPL', 'price': 175.50, 'source': 'mock'}
    
    print(f"Real data validation: {validate_data_or_skip(real_data, 'price')}")
    print(f"Fake data validation: {validate_data_or_skip(fake_data, 'price')}")
    
    # Test is_mock_data
    print(f"is_mock_data on fake source: {is_mock_data(fake_data)}")
    print(f"is_mock_data on real source: {is_mock_data(real_data)}")
    
    # Show validation summary
    print("\nValidation Rules Summary:")
    print("-" * 50)
    summary = validator.get_validation_summary()
    print(f"Fake sources blocked: {summary['fake_sources']}")
    print(f"Price thresholds: {summary['price_thresholds']}")
    print(f"Symbol patterns: {list(summary['symbol_patterns'].keys())}")

if __name__ == "__main__":
    test_strict_validator()
