from core.config import PhasmaConfig
from engines.kalshi_ai_playbook import KalshiAIPlaybook
import requests

config = PhasmaConfig()
playbook = KalshiAIPlaybook(config)

# Get a few temperature markets
headers = {"Authorization": "Bearer 8e9e7211-30ad-4a89-aa08-87ce81dce69e"}

# Get temperature series
response = requests.get("https://api.elections.kalshi.com/trade-api/v2/series", headers=headers)
series = [s for s in response.json().get("series", []) if "temperature" in s.get("title", "").lower()]

if series:
    print(f"Found temperature series: {series[0]['ticker']}")
    
    # Get markets for first series
    markets_url = f"https://api.elections.kalshi.com/trade-api/v2/markets?series_ticker={series[0]['ticker']}&status=open&limit=3"
    markets_resp = requests.get(markets_url, headers=headers)
    markets = markets_resp.json().get("markets", [])
    
    print(f"Found {len(markets)} markets")
    
    for m in markets:
        yes_bid = m.get("yes_bid", 0) / 100
        yes_ask = m.get("yes_ask", 0) / 100
        mid = (yes_bid + yes_ask) / 2 if yes_bid > 0 or yes_ask > 0 else 0
        
        print(f"\nMarket: {m['ticker']}")
        print(f"  Title: {m.get('subtitle', 'N/A')}")
        print(f"  Bid: ${yes_bid:.2f}")
        print(f"  Ask: ${yes_ask:.2f}")
        print(f"  Mid: ${mid:.2f}")
        print(f"  Volume: {m.get('volume', 0)}")
        
        if mid > 0.01:
            print(f"  ✅ ACTIVE - Can trade!")
            
            # Check if it meets adjusted thresholds
            if 0.10 <= mid <= 0.90 and m.get('volume', 0) >= 50:
                print(f"  ✅ Meets adjusted thresholds!")
            else:
                print(f"  ❌ Doesn't meet thresholds")
        else:
            print(f"  ❌ Inactive")
else:
    print("No temperature series found")
