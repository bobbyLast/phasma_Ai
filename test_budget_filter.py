"""
Test budget filter in confluence service
"""

from main import PhasmaTradingSystem

def test_budget_filter():
    """Test that expensive stocks are skipped"""
    
    print("\n" + "="*80)
    print("💰 TESTING BUDGET FILTER")
    print("="*80)
    
    # Initialize system
    system = PhasmaTradingSystem()
    
    # Test symbols - mix of affordable and expensive
    test_symbols = {
        'AAPL': 195,  # Too expensive
        'GOOGL': 140,  # Too expensive  
        'NVDA': 480,   # Too expensive
        'MSFT': 380,   # Too expensive
        'AMZN': 155,   # Too expensive
        'SNDL': 1.5,   # Affordable
        'BBAI': 2.8,   # Affordable
        'NOK': 3.5,    # Affordable
        'BB': 3.0,     # Affordable
        'PLTR': 18,    # Affordable
    }
    
    print(f"\nBudget: ${system.config.get('trading_budget', {}).get('max_price_per_share', 50)} max per share")
    print("\nTesting symbols:")
    
    results = {
        'total': len(test_symbols),
        'skipped': 0,
        'analyzed': 0
    }
    
    for symbol, expected_price in test_symbols.items():
        result = system.confluence_service.score(symbol)
        
        if result is None:
            results['skipped'] += 1
            print(f"  ❌ {symbol}: SKIPPED (price ~${expected_price})")
        else:
            results['analyzed'] += 1
            print(f"  ✅ {symbol}: ANALYZED - Score {result.score:.1%}")
    
    print("\n" + "="*80)
    print("📊 BUDGET FILTER RESULTS")
    print("="*80)
    print(f"Total symbols: {results['total']}")
    print(f"Skipped (too expensive): {results['skipped']}")
    print(f"Analyzed (affordable): {results['analyzed']}")
    print(f"\n✅ Budget filter saves time by skipping {results['skipped']} expensive stocks!")
    
    # Time savings estimate
    time_per_analysis = 2  # seconds
    time_saved = results['skipped'] * time_per_analysis
    print(f"⏱️ Time saved: ~{time_saved} seconds per run")
    
    return results

if __name__ == "__main__":
    test_budget_filter()
