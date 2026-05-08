"""Check weather market data structure"""

import requests

headers = {"Authorization": "Bearer 8e9e7211-30ad-4a89-aa08-87ce81dce69e"}

# Get weather series
series_response = requests.get("https://api.elections.kalshi.com/trade-api/v2/series", headers=headers)
all_series = series_response.json().get('series', [])

# Find temperature series
temp_series = []
for s in all_series:
    title = s.get('title', '').lower()
    if 'temperature' in title or 'temp' in title:
        temp_series.append(s)

print(f"Found {len(temp_series)} temperature series")

# Check first temperature series
if temp_series:
    series = temp_series[0]
    print(f"\nChecking series: {series.get('ticker')}")
    print(f"Title: {series.get('title')}")
    
    # Get markets for this series
    markets_url = f"https://api.elections.kalshi.com/trade-api/v2/markets?series_ticker={series.get('ticker')}&status=open"
    markets_response = requests.get(markets_url, headers=headers)
    markets = markets_response.json().get('markets', [])
    
    print(f"\nMarkets: {len(markets)}")
    
    # Show first market with all fields
    if markets:
        market = markets[0]
        print(f"\nFirst market: {market.get('ticker')}")
        print(f"Title: {market.get('subtitle')}")
        
        # Check all price-related fields
        print("\nPrice fields:")
        for key, value in market.items():
            if 'price' in key.lower() or 'bid' in key.lower() or 'ask' in key.lower():
                print(f"  {key}: {value}")
        
        # Check if we need to calculate price differently
        print(f"\nOther key fields:")
        print(f"  yes_bid: {market.get('yes_bid')}")
        print(f"  yes_ask: {market.get('yes_ask')}")
        print(f"  no_bid: {market.get('no_bid')}")
        print(f"  no_ask: {market.get('no_ask')}")
        print(f"  volume: {market.get('volume')}")
        print(f"  status: {market.get('status')}")
        
        # Calculate implied probability from bid/ask
        yes_bid = market.get('yes_bid', 0)
        yes_ask = market.get('yes_ask', 0)
        
        if yes_bid > 0 or yes_ask > 0:
            mid_price = (yes_bid + yes_ask) / 2 / 100
            print(f"\nImplied probability from mid-price: {mid_price:.1%}")
        else:
            print("\nNo active pricing - market not yet trading")