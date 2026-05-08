#!/usr/bin/env python3
"""
Test the robust price fetcher with multiple data sources
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.robust_price_fetcher import get_robust_price_fetcher

def test_robust_price_fetcher():
    """Test the robust price fetcher with various stocks"""
    
    print("="*60)
    print("TESTING ROBUST PRICE FETCHER")
    print("="*60)
    
    # Initialize the fetcher
    fetcher = get_robust_price_fetcher()
    
    # Test stocks with different characteristics
    test_symbols = [
        'AAPL',  # High volume, reliable
        'GOOGL', # High volume, reliable
        'TSLA',  # High volume, volatile
        'SOFI',  # Recent drop we discussed
        'AI',    # Mid-cap
        'INVALID',  # Should fail gracefully
    ]
    
    print("\nTesting price fetching for multiple symbols...\n")
    
    for symbol in test_symbols:
        print(f"Testing {symbol}:")
        result = fetcher.get_price_with_validation(symbol)
        
        if result['valid']:
            print(f"  [OK] Price: ${result['price']:.2f}")
        else:
            print(f"  [FAILED] Failed: {result['reason']}")
        print()
    
    # Test caching
    print("Testing caching (should be instant)...")
    import time
    start = time.time()
    price = fetcher.get_real_price('AAPL')
    end = time.time()
    print(f"  Cached fetch took: {(end - start)*1000:.1f}ms")
    
    # Test statistics
    print("\nPrice fetcher statistics:")
    fetcher.print_statistics()
    
    # Test failover (simulate yfinance failure)
    print("\nTesting failover behavior...")
    print("(This would test backup sources if yfinance fails)")
    
    print("\n" + "="*60)
    print("TEST COMPLETE")
    print("="*60)
    
    print("\nKey Points:")
    print("1. Primary source: yfinance")
    print("2. Backup sources: Alpha Vantage, Finnhub, Yahoo Direct")
    print("3. 5-minute cache to reduce API calls")
    print("4. Rate limiting for each source")
    print("5. Automatic failover with statistics tracking")

if __name__ == "__main__":
    test_robust_price_fetcher()
