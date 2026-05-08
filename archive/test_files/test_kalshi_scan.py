from core.config import PhasmaConfig
from engines.kalshi_engine import KalshiPredictionEngine

config = PhasmaConfig()
engine = KalshiPredictionEngine(config)

# Test with very low thresholds
opportunities = engine.scan_all_markets(
    min_volume=1,  # Very low volume
    max_markets=10  # Just test first 10
)

print(f"Found {len(opportunities)} opportunities")
if opportunities:
    for i, opp in enumerate(opportunities[:3]):
        print(f"\nOpportunity {i+1}:")
        print(f"  Title: {opp['market'].get('title', 'N/A')}")
        print(f"  Probability: {opp.get('implied_probability', 'N/A'):.2%}")
        print(f"  Volume: {opp.get('volume', 0)}")
