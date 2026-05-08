from core.config import PhasmaConfig
from engines.kalshi_engine import KalshiPredictionEngine

config = PhasmaConfig()
engine = KalshiPredictionEngine(config)

# Test with very low thresholds and check for active markets
opportunities = engine.scan_all_markets(
    min_volume=1,  # Very low volume
    max_markets=5  # Just test first 5
)

print(f"Found {len(opportunities)} opportunities")
if opportunities:
    for i, opp in enumerate(opportunities[:3]):
        print(f"\nOpportunity {i+1}:")
        print(f"  Title: {opp['market'].get('title', 'N/A')}")
        print(f"  Status: {opp['market'].get('status', 'N/A')}")
        print(f"  Probability: {opp.get('implied_probability', 'N/A'):.2%}")
        print(f"  Volume: {opp.get('volume', 0)}")
        print(f"  Confidence: {opp['analysis'].get('confidence', 0):.2f}")
else:
    # Check if there are any active markets at all
    import requests
    response = requests.get("https://api.elections.kalshi.com/trade-api/v2/markets?limit=10")
    if response.status_code == 200:
        markets = response.json().get('markets', [])
        print(f"\nChecking first 10 markets:")
        active_count = 0
        for m in markets:
            status = m.get('status', 'N/A')
            if status == 'active':
                active_count += 1
            print(f"  - {m.get('title', 'N/A')[:50]}... Status: {status}")
        print(f"\nActive markets in first 10: {active_count}")
