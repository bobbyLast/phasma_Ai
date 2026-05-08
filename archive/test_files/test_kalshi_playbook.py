"""Test Kalshi AI Playbook Implementation"""

from core.config import PhasmaConfig
from engines.kalshi_ai_playbook import KalshiAIPlaybook

def test_playbook():
    config = PhasmaConfig()
    playbook = KalshiAIPlaybook(config)
    
    print("🤖 Testing Kalshi AI Playbook")
    print("=" * 60)
    
    # Test 1: Discover whitelisted series
    print("\n1️⃣ Testing Market Discovery...")
    series = playbook.discover_whitelisted_series()
    
    if series:
        print(f"✅ Found {len(series)} whitelisted series")
        
        # Count by type
        type_counts = {}
        for s in series:
            mtype = s.get('market_type', 'UNKNOWN')
            type_counts[mtype] = type_counts.get(mtype, 0) + 1
        
        print("   By type:")
        for mtype, count in type_counts.items():
            print(f"     - {mtype}: {count}")
    else:
        print("❌ No series found")
    
    # Test 2: Find opportunities
    print("\n2️⃣ Testing Opportunity Detection...")
    opportunities = playbook.find_opportunities()
    
    if opportunities:
        print(f"✅ Found {len(opportunities)} opportunities")
        
        print("\n📊 Top 3 Opportunities:")
        for i, opp in enumerate(opportunities[:3]):
            print(f"\n{i+1}. {opp['ticker']} ({opp['market_type']})")
            print(f"   Title: {opp['title'][:100]}...")
            print(f"   Signal: {opp['trade_signal']} @ ${opp['yes_price']:.2f}")
            print(f"   Model Prob: {opp['model_probability']:.1%}")
            print(f"   EV: {opp['ev']:+.1%} (Required: {opp['required_edge']:.1%})")
            print(f"   Hours to Close: {opp['hours_to_close']:.1f}")
            print(f"   Liquidity Score: {opp['liquidity_score']}/3")
            print(f"   Volume: {opp['volume']:,}")
            print(f"   Confidence: {opp['confidence']:.1f}x")
            print(f"   Rationale: {opp['rationale']}")
    else:
        print("💤 No opportunities found")
    
    # Test 3: Liquidity scoring
    print("\n3️⃣ Testing Liquidity Scoring...")
    if opportunities:
        first_opp = opportunities[0]
        print(f"Sample liquidity score: {first_opp['liquidity_score']}/3")
        print(f"   Volume: {first_opp['volume']:,}")
        print(f"   Spread: {first_opp['spread_cents']:.1f} cents")
    
    # Test 4: Dynamic edge calculation
    print("\n4️⃣ Testing Dynamic Edge Calculation...")
    test_cases = [
        (72, 2, 2, "WEATHER"),
        (24, 5, 3, "ECON"),
        (96, 1, 1, "FED")
    ]
    
    for hours, spread, liq, mtype in test_cases:
        edge = playbook.calculate_dynamic_edge(hours, spread, liq, mtype)
        print(f"   {mtype}: {hours}h, {spread}¢ spread, liq={liq} → Required edge: {edge:.1%}")
    
    print("\n" + "=" * 60)
    print("✅ AI Playbook test complete!")

if __name__ == "__main__":
    test_playbook()
