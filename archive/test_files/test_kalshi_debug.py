from core.config import PhasmaConfig
from engines.kalshi_engine import KalshiPredictionEngine

config = PhasmaConfig()
engine = KalshiPredictionEngine(config)

# Test with very low thresholds to see what markets exist
opportunities = engine.scan_all_markets(
    min_volume=1,  # Very low volume
    max_markets=3  # Just test first 3 series
)

print(f"\nFinal result: Found {len(opportunities)} opportunities")
