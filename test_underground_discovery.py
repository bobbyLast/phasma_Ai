"""
Test Underground Stock Discovery System
"""

from main import PhasmaTradingSystem

def test_underground_discovery():
    """Test the underground stock discovery engine"""
    
    print("\n" + "="*80)
    print("🔍 TESTING UNDERGROUND STOCK DISCOVERY")
    print("="*80)
    
    # Initialize system
    system = PhasmaTradingSystem()
    
    if not system.underground_discovery:
        print("❌ Underground discovery not enabled in config")
        return
    
    print("\n🚀 Running underground discovery scan...")
    
    # Run the scan
    opportunities = system.underground_discovery.scan_for_opportunities()
    
    print("\n" + "="*80)
    print("📊 UNDERGROUND DISCOVERY RESULTS")
    print("="*80)
    
    if not opportunities:
        print("No underground opportunities found")
        return
    
    print(f"Found {len(opportunities)} opportunities:\n")
    
    for i, opp in enumerate(opportunities, 1):
        print(f"{i}. {opp.ticker}")
        print(f"   Type: {opp.signal_type.upper()}")
        print(f"   Strength: {opp.strength:.1%}")
        print(f"   Evidence: {opp.evidence}")
        print(f"   Liquidity: {opp.liquidity_score:.1%}")
        print(f"   Dilution Risk: {opp.dilution_risk}")
        print(f"   Sources: {', '.join(opp.sources)}")
        print()
    
    # Analyze patterns
    signal_types = {}
    for opp in opportunities:
        signal_types[opp.signal_type] = signal_types.get(opp.signal_type, 0) + 1
    
    print("📈 Signal Breakdown:")
    for signal_type, count in signal_types.items():
        print(f"   {signal_type}: {count}")
    
    # Top opportunities
    high_strength = [opp for opp in opportunities if opp.strength >= 0.7]
    if high_strength:
        print(f"\n🎯 High Strength Opportunities ({len(high_strength)}):")
        for opp in high_strength:
            print(f"   {opp.ticker}: {opp.strength:.1%} - {opp.evidence[:60]}...")
    
    print("\n✅ Underground discovery test complete!")
    
    # Integration test with main system
    print("\n" + "="*80)
    print("🔄 INTEGRATION TEST WITH MAIN SYSTEM")
    print("="*80)
    
    # Convert to signals
    underground_signals = []
    for opp in opportunities[:3]:  # Test top 3
        signal = type('Signal', (), {
            'symbol': opp.ticker,
            'action': 'BUY',
            'trade_type': 'STOCK',
            'confidence': int(opp.strength * 100),
            'source': 'Underground Discovery',
            'evidence': opp.evidence,
            'metadata': {
                'signal_type': opp.signal_type,
                'liquidity_score': opp.liquidity_score
            }
        })()
        underground_signals.append(signal)
    
    print(f"Created {len(underground_signals)} signal objects for main system")
    
    # Test confluence scoring
    for signal in underground_signals:
        print(f"\n🧠 Scoring {signal.symbol} with confluence service...")
        result = system.confluence_service.score(signal.symbol)
        if result:
            print(f"   Score: {result.score:.1%} ({result.confidence})")
            print(f"   Reasoning: {result.reasoning}")
        else:
            print(f"   No confluence data available")
    
    return opportunities

if __name__ == "__main__":
    test_underground_discovery()
