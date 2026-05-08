"""Check for recent/active Kalshi markets"""

import requests
from datetime import datetime

headers = {"Authorization": "Bearer 8e9e7211-30ad-4a89-aa08-87ce81dce69e"}

# Get markets with closer close dates
response = requests.get("https://api.elections.kalshi.com/trade-api/v2/markets?status=open&limit=100", headers=headers)
data = response.json()

print("Checking for markets with non-zero prices...")
print("="*60)

active_markets = []
for market in data.get('markets', []):
    price = market.get('yes_price', 0) / 100
    volume = market.get('volume', 0)
    
    if price > 0.01:  # Non-zero price
        active_markets.append(market)
        print(f"\n✅ Found active market!")
        print(f"  Ticker: {market.get('ticker')}")
        print(f"  Title: {market.get('subtitle', 'N/A')}")
        print(f"  Yes Price: ${price:.2f}")
        print(f"  Volume: {volume:,}")
        print(f"  Close Time: {market.get('close_time', 'N/A')}")

print(f"\nTotal markets with price > $0.01: {len(active_markets)}")

# If no active markets, check for any with volume
if not active_markets:
    print("\nChecking markets with volume but zero price...")
    volume_markets = [m for m in data.get('markets', []) if m.get('volume', 0) > 0]
    print(f"Markets with volume but $0.00 price: {len(volume_markets)}")
    
    # Show top 5 by volume
    volume_markets.sort(key=lambda x: x.get('volume', 0), reverse=True)
    for i, market in enumerate(volume_markets[:5]):
        print(f"\n{i+1}. {market.get('ticker')}")
        print(f"   Volume: {market.get('volume', 0):,}")
        print(f"   Close: {market.get('close_time', 'N/A')}")

# Check if we need different endpoint
print("\n" + "="*60)
print("Checking if we need a different API endpoint...")

# Try the exchange API
try:
    exchange_response = requests.get("https://api.elections.kalshi.com/trade-api/v2/exchange/ticker", headers=headers)
    if exchange_response.status_code == 200:
        print("Exchange API accessible")
        print(f"Response: {exchange_response.text[:200]}...")
except:
    print("Exchange API not accessible")

# Check account info
try:
    account_response = requests.get("https://api.elections.kalshi.com/trade-api/v2/account", headers=headers)
    if account_response.status_code == 200:
        account = account_response.json()
        print(f"\nAccount Info:")
        print(f"  Username: {account.get('username', 'N/A')}")
        print(f"  Balance: ${account.get('balance', 0)/100:.2f}")
        print(f"  API Key works!")
except Exception as e:
    print(f"Account error: {e}")
