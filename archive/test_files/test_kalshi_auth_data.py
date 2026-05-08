"""Check authenticated Kalshi API data"""

import requests
import json

# Use the API key
headers = {"Authorization": "Bearer 8e9e7211-30ad-4a89-aa08-87ce81dce69e"}

# Get markets
response = requests.get("https://api.elections.kalshi.com/trade-api/v2/markets?status=open&limit=10", headers=headers)
data = response.json()

print(f"Total markets returned: {len(data.get('markets', []))}")

# Check first few markets
for i, market in enumerate(data.get('markets', [])[:5]):
    print(f"\nMarket {i+1}:")
    print(f"  Ticker: {market.get('ticker')}")
    print(f"  Title: {market.get('subtitle', 'N/A')}")
    print(f"  Yes Price: ${market.get('yes_price', 0)/100:.2f}")
    print(f"  No Price: ${market.get('no_price', 0)/100:.2f}")
    print(f"  Volume: {market.get('volume', 0)}")
    print(f"  Category: {market.get('category', 'N/A')}")
    print(f"  Close Time: {market.get('close_time', 'N/A')}")

# Also check series
print("\n" + "="*60)
print("Checking series...")

series_response = requests.get("https://api.elections.kalshi.com/trade-api/v2/series", headers=headers)
series_data = series_response.json()

print(f"Total series: {len(series_data.get('series', []))}")

# Look for weather/econ series
weather_series = []
econ_series = []
fed_series = []

for s in series_data.get('series', []):
    title = s.get('title', '').lower()
    if any(kw in title for kw in ['temperature', 'temp', 'rain', 'snow', 'weather']):
        weather_series.append(s)
    elif any(kw in title for kw in ['cpi', 'inflation', 'employment', 'gdp']):
        econ_series.append(s)
    elif 'fed' in title:
        fed_series.append(s)

print(f"Weather series: {len(weather_series)}")
print(f"Econ series: {len(econ_series)}")
print(f"Fed series: {len(fed_series)}")

# Check first weather series
if weather_series:
    ws = weather_series[0]
    print(f"\nFirst weather series: {ws.get('ticker')}")
    print(f"  Title: {ws.get('title')}")
    
    # Get markets for this series
    markets_url = f"https://api.elections.kalshi.com/trade-api/v2/markets?series_ticker={ws.get('ticker')}&status=open"
    markets_resp = requests.get(markets_url, headers=headers)
    markets = markets_resp.json().get('markets', [])
    print(f"  Open markets: {len(markets)}")
    
    if markets:
        m = markets[0]
        print(f"  First market:")
        print(f"    Price: ${m.get('yes_price', 0)/100:.2f}")
        print(f"    Volume: {m.get('volume', 0)}")
