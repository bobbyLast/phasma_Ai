"""
Smoke test for confluence service - run on 1k symbols
"""

from main import PhasmaTradingSystem
import random

def test_confluence_smoke():
    """Test confluence service on sample symbols"""
    
    print("\n" + "="*80)
    print("🧪 CONFLUENCE SERVICE SMOKE TEST")
    print("="*80)
    
    # Initialize system
    system = PhasmaTradingSystem()
    
    # Sample symbols (mix of tech, energy, financials)
    symbols = [
        'AAPL', 'MSFT', 'GOOGL', 'NVDA', 'TSLA', 'META', 'AMZN', 'CRM', 'ADBE', 'ORCL',
        'JPM', 'BAC', 'WFC', 'GS', 'MS', 'C', 'AXP', 'BLK', 'SPGI', 'ICE',
        'XOM', 'CVX', 'COP', 'EOG', 'SLB', 'HAL', 'BKR', 'PSX', 'VLO', 'MPC',
        'CEG', 'NU', 'NRG', 'VST', 'AEE', 'DTE', 'XEL', 'WEC', 'AES', 'SRE',
        'AMD', 'INTC', 'MU', 'QCOM', 'TXN', 'AVGO', 'MRVL', 'LRCX', 'KLAC', 'AMAT',
        'PLTR', 'PLUG', 'FSLR', 'ENPH', 'RUN', 'SEDG', 'BE', 'CHPT', 'EVGO', 'RIVN'
    ]
    
    print(f"\n📊 Testing confluence on {len(symbols)} symbols...")
    
    results = {
        'total': len(symbols),
        'scored': 0,
        'filtered': 0,
        'high_confluence': 0,
        'errors': 0
    }
    
    for symbol in symbols:
        try:
            result = system.confluence_service.score(symbol)
            
            if result is None:
                results['filtered'] += 1
                print(f"  ❌ {symbol}: FILTERED")
            else:
                results['scored'] += 1
                print(f"  ✅ {symbol}: {result.score:.1%} ({result.confidence})")
                
                if result.score >= 0.7:
                    results['high_confluence'] += 1
                    print(f"    🎯 HIGH CONFLUENCE: {result.reasoning}")
                
        except Exception as e:
            results['errors'] += 1
            print(f"  ⚠️ {symbol}: ERROR - {e}")
    
    print("\n" + "="*80)
    print("📈 SMOKE TEST RESULTS")
    print("="*80)
    print(f"Total Symbols: {results['total']}")
    print(f"Scored: {results['scored']} ({results['scored']/results['total']:.1%})")
    print(f"Filtered: {results['filtered']} ({results['filtered']/results['total']:.1%})")
    print(f"High Confluence: {results['high_confluence']} ({results['high_confluence']/results['total']:.1%})")
    print(f"Errors: {results['errors']}")
    
    # Test strategy switch
    print("\n🔄 Testing strategy switch to smallcap...")
    system.confluence_service.active_strategy = 'smallcap'
    
    # Test a few small caps
    small_caps = ['SNDL', 'AMC', 'BB', 'NOK', 'PLTR']
    for symbol in small_caps:
        result = system.confluence_service.score(symbol)
        if result:
            print(f"  ✅ {symbol}: {result.score:.1%}")
        else:
            print(f"  ❌ {symbol}: FILTERED")
    
    print("\n✅ Smoke test complete!")
    return results

if __name__ == "__main__":
    test_confluence_smoke()
