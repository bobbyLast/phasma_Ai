from core.config import PhasmaConfig
from engines.kalshi_engine import KalshiPredictionEngine
import traceback

config = PhasmaConfig()
engine = KalshiPredictionEngine(config)

try:
    opportunities = engine.scan_all_markets(
        min_volume=1,
        max_markets=1
    )
    print(f"Found {len(opportunities)} opportunities")
except Exception as e:
    print(f"Error: {e}")
    traceback.print_exc()
