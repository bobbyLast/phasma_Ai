from core.config import PhasmaConfig
from engines.kalshi_engine import KalshiPredictionEngine

config = PhasmaConfig()
print(f"kalshi_enabled: {config.get('kalshi_enabled')}")

engine = KalshiPredictionEngine(config)
print("Engine initialized")

# Test the API directly
import requests
response = requests.get("https://api.kalshi.com/trade-api/v2/series")
print(f"API Response Status: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    print(f"Series found: {len(data.get('series', []))}")
else:
    print(f"Error: {response.text}")
