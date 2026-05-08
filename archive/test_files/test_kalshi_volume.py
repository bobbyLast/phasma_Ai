"""Find Kalshi markets with actual volume"""

import requests

headers = {"Authorization": "Bearer 8e9e7211-30ad-4a89-aa08-87ce81dce69e"}

# Get open markets and filter for volume
response = requests.get("https://api.elections.kalshi.com/trade-api/v2/markets?status=open&limit=100", headers=headers)
markets = response.json().get("markets", [])

print(f"Total markets: {len(markets)}")

# Find markets with volume
volume_markets = [m for m in markets if m.get("volume", 0) > 0]
print(f"Markets with volume > 0: {len(volume_markets)}")

# Sort by volume
volume_markets.sort(key=lambda x: x.get("volume", 0), reverse=True)

print("\nTop 10 markets by volume:")
print("-" * 60)

for i, m in enumerate(volume_markets[:10]):
    yes_bid = m.get("yes_bid", 0) / 100
    yes_ask = m.get("yes_ask", 0) / 100
    mid = (yes_bid + yes_ask) / 2 if yes_bid > 0 or yes_ask > 0 else 0
    
    print(f"\n{i+1}. {m['ticker']}")
    print(f"   Title: {m.get('subtitle', 'N/A')[:50]}...")
    print(f"   Price: ${mid:.2f} (Bid: ${yes_bid:.2f}, Ask: ${yes_ask:.2f})")
    print(f"   Volume: {m.get('volume', 0):,}")
    
    # Check if it meets all criteria
    price_ok = 0.10 <= mid <= 0.90
    volume_ok = m.get('volume', 0) >= 50
    active = mid > 0.01
    
    print(f"   Status: {'✅' if active and price_ok and volume_ok else '❌'}")
    if not active:
        print(f"   - No active pricing")
    if not price_ok:
        print(f"   - Price ${mid:.2f} outside $0.10-$0.90 range")
    if not volume_ok:
        print(f"   - Volume {m.get('volume', 0)} below 50")

# If no markets meet criteria, suggest lowering threshold
if not any(m for m in volume_markets[:10] if 0.10 <= (m.get('yes_bid', 0) + m.get('yes_ask', 0)) / 200 <= 0.90 and m.get('volume', 0) >= 50):
    print("\n" + "="*60)
    print("SUGGESTION: Lower volume threshold to find opportunities")
    print("Most markets have low volume - try volume >= 10 or 1")
    print("="*60)
