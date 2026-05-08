import requests

# Test the correct endpoint
response = requests.get("https://api.elections.kalshi.com/trade-api/v2/exchange/status")
print(f"Status Code: {response.status_code}")
print(f"Response: {response.text}")

# Test series endpoint
response2 = requests.get("https://api.elections.kalshi.com/trade-api/v2/series")
print(f"\nSeries Status: {response2.status_code}")
if response2.status_code == 200:
    data = response2.json()
    print(f"Found {len(data.get('series', []))} series")
