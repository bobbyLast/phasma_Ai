"""Test different Kalshi API endpoints to find active markets"""

import requests

headers = {"Authorization": "Bearer 8e9e7211-30ad-4a89-aa08-87ce81dce69e"}

base_urls = [
    "https://api.elections.kalshi.com/trade-api/v2",
    "https://api.kalshi.com/trade-api/v2",
    "https://demo-api.kalshi.com/trade-api/v2"
]

endpoints = [
    "/markets",
    "/markets?status=open",
    "/series",
    "/exchange/ticker",
    "/portfolio/positions",
    "/account/balance"
]

for base_url in base_urls:
    print(f"\n{'='*60}")
    print(f"Testing: {base_url}")
    print('='*60)
    
    for endpoint in endpoints:
        try:
            url = base_url + endpoint
            response = requests.get(url, headers=headers, timeout=5)
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    if 'markets' in data:
                        markets = data.get('markets', [])
                        non_zero = [m for m in markets if m.get('yes_price', 0) > 0]
                        print(f"✅ {endpoint}: {len(markets)} markets, {len(non_zero)} with price > 0")
                        
                        # Show sample if non-zero found
                        if non_zero:
                            m = non_zero[0]
                            print(f"   Sample: {m.get('ticker')} - ${m.get('yes_price', 0)/100:.2f}")
                    elif 'series' in data:
                        print(f"✅ {endpoint}: {len(data.get('series', []))} series")
                    else:
                        print(f"✅ {endpoint}: OK - {str(data)[:50]}...")
                except:
                    print(f"✅ {endpoint}: OK (non-JSON)")
            else:
                print(f"❌ {endpoint}: {response.status_code}")
                
        except requests.exceptions.Timeout:
            print(f"⏰ {endpoint}: Timeout")
        except requests.exceptions.ConnectionError:
            print(f"🔌 {endpoint}: Connection failed")
        except Exception as e:
            print(f"❌ {endpoint}: {str(e)[:50]}")

# Check documentation for correct URL
print("\n" + "="*60)
print("Checking Kalshi documentation...")
print("="*60)

# Try to get docs
try:
    docs_response = requests.get("https://docs.kalshi.com/")
    print(f"✅ Documentation accessible")
except:
    print("❌ Documentation not accessible")

# Try public API without auth
print("\nTesting public API (no auth)...")
try:
    public_response = requests.get("https://api.elections.kalshi.com/trade-api/v2/series")
    if public_response.status_code == 200:
        data = public_response.json()
        print(f"✅ Public API works: {len(data.get('series', []))} series")
except Exception as e:
    print(f"❌ Public API failed: {e}")
