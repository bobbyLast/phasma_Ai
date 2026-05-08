"""Check closed markets to see actual prices"""

import requests
from datetime import datetime

headers = {"Authorization": "Bearer 8e9e7211-30ad-4a89-aa08-87ce81dce69e"}

# Check settled markets to see if they have prices
print("Checking settled/closed markets...")
print("="*60)

# Get closed markets
closed_response = requests.get("https://api.elections.kalshi.com/trade-api/v2/markets?status=closed&limit=20", headers=headers)
closed_data = closed_response.json()

closed_markets = closed_data.get('markets', [])
print(f"Closed markets: {len(closed_markets)}")

# Show settled markets with prices
settled = [m for m in closed_markets if m.get('yes_price', 0) > 0]
print(f"Settled markets with price > 0: {len(settled)}")

for i, market in enumerate(settled[:5]):
    print(f"\n{i+1}. {market.get('ticker')}")
    print(f"   Yes Price: ${market.get('yes_price', 0)/100:.2f}")
    print(f"   No Price: ${market.get('no_price', 0)/100:.2f}")
    print(f"   Result: {market.get('result', 'N/A')}")
    print(f"   Volume: {market.get('volume', 0):,}")
    print(f"   Close Time: {market.get('close_time', 'N/A')}")

# Check specific event types
print("\n" + "="*60)
print("Checking specific market categories...")

# Get all series and look for recent ones
series_response = requests.get("https://api.elections.kalshi.com/trade-api/v2/series", headers=headers)
all_series = series_response.json().get('series', [])

# Look for recent series
recent_series = []
for s in all_series:
    # Check if it's a recent event
    title = s.get('title', '').lower()
    if any(keyword in title for keyword in ['2024', '2025', 'biden', 'trump', 'election']):
        recent_series.append(s)

print(f"Recent/political series: {len(recent_series)}")

# Check first few recent series
for i, series in enumerate(recent_series[:3]):
    print(f"\n{i+1}. {series.get('ticker')}")
    print(f"   Title: {series.get('title')}")
    
    # Get markets
    markets_url = f"https://api.elections.kalshi.com/trade-api/v2/markets?series_ticker={series.get('ticker')}"
    markets_resp = requests.get(markets_url, headers=headers)
    markets = markets_resp.json().get('markets', [])
    
    print(f"   Total markets: {len(markets)}")
    
    # Check for any with prices
    priced = [m for m in markets if m.get('yes_price', 0) > 0]
    print(f"   With prices: {len(priced)}")
    
    if priced:
        p = priced[0]
        print(f"   Sample price: ${p.get('yes_price', 0)/100:.2f}")

# Try without auth to see if it's different
print("\n" + "="*60)
print("Testing without authentication...")

try:
    no_auth_response = requests.get("https://api.elections.kalshi.com/trade-api/v2/markets?limit=10")
    no_auth_data = no_auth_response.json()
    
    print(f"Markets without auth: {len(no_auth_data.get('markets', []))}")
    
    # Check prices
    no_auth_priced = [m for m in no_auth_data.get('markets', []) if m.get('yes_price', 0) > 0]
    print(f"With prices > 0: {len(no_auth_priced)}")
    
except Exception as e:
    print(f"Error: {e}")
