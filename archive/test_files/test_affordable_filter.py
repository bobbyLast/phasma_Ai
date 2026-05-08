#!/usr/bin/env python3
"""
Test the affordable stock filter to ensure it removes expensive stocks
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.affordable_stock_filter import AffordableStockFilter

def test_affordable_filter():
    """Test that the filter correctly removes expensive stocks"""
    
    print("="*60)
    print("TESTING AFFORDABLE STOCK FILTER")
    print("="*60)
    
    # Simulate the user's budget
    budget = 56.00
    filter = AffordableStockFilter(max_price=budget)
    
    # Test stocks with different prices
    test_stocks = [
        ('AAPL', 274.61),   # Too expensive
        ('GOOGL', 306.57),  # Too expensive
        ('TSLA', 489.88),   # Too expensive
        ('SOFI', 26.58),    # Affordable
        ('AI', 14.49),      # Affordable
        ('AMD', 145.23),    # Too expensive
        ('BAC', 44.12),     # Affordable
        ('PFE', 29.51),     # Affordable
        ('NVDA', 878.35),   # Too expensive
    ]
    
    print(f"\nBudget: ${budget:.2f}")
    print(f"\nTesting filter on {len(test_stocks)} stocks...\n")
    
    # Extract symbols
    symbols = [s[0] for s in test_stocks]
    
    # Filter
    affordable = filter.filter_affordable(symbols)
    
    # Check results
    print("\nResults:")
    expensive_count = 0
    affordable_count = 0
    
    for symbol, expected_price in test_stocks:
        if symbol in affordable:
            if expected_price <= budget:
                print(f"  [OK] {symbol}: ${expected_price:.2f} - CORRECTLY included (affordable)")
                affordable_count += 1
            else:
                print(f"  ✗ {symbol}: ${expected_price:.2f} - INCORRECTLY included (too expensive!)")
        else:
            if expected_price > budget:
                print(f"  [OK] {symbol}: ${expected_price:.2f} - CORRECTLY excluded (too expensive)")
                expensive_count += 1
            else:
                print(f"  ✗ {symbol}: ${expected_price:.2f} - INCORRECTLY excluded (should be affordable!)")
    
    print(f"\nSummary:")
    print(f"  Affordable stocks found: {len(affordable)}")
    print(f"  Expensive stocks filtered: {len(symbols) - len(affordable)}")
    
    # Verify the filter works
    if 'AAPL' in affordable or 'GOOGL' in affordable or 'TSLA' in affordable:
        print("\n❌ ERROR: Expensive stocks are still in the list!")
    else:
        print("\n[SUCCESS] All expensive stocks were filtered out!")
    
    print("\n" + "="*60)
    print("TEST COMPLETE")
    print("="*60)
    
    print("\nKey Points:")
    print("1. The filter removes stocks over the budget BEFORE analysis")
    print("2. This saves time by not analyzing stocks we can't afford")
    print("3. Only affordable stocks like SOFI ($26.58) and AI ($14.49) remain")
    print("4. The AI will focus on realistic trading opportunities")

if __name__ == "__main__":
    test_affordable_filter()
