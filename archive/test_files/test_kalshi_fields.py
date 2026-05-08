import requests

# Get a sample market to see its structure
response = requests.get("https://api.elections.kalshi.com/trade-api/v2/markets?limit=2")
if response.status_code == 200:
    markets = response.json().get('markets', [])
    for m in markets:
        print(f"\nMarket: {m.get('ticker')}")
        print(f"Title: {m.get('title')}")
        print(f"Status: {m.get('status')}")
        print(f"Available fields: {list(m.keys())}")
        
        # Check price-related fields
        if 'last_price' in m:
            print(f"Last price: {m['last_price']} cents = {m['last_price']/100:.1%}")
        if 'yes_bid' in m:
            print(f"Yes bid: {m['yes_bid']} cents = {m['yes_bid']/100:.1%}")
        if 'yes_ask' in m:
            print(f"Yes ask: {m['yes_ask']} cents = {m['yes_ask']/100:.1%}")
        if 'implied_probability' in m:
            print(f"Implied probability: {m['implied_probability']:.1%}")
        else:
            print("No implied_probability field!")
