from engines.kalshi_engine import KalshiPredictionEngine
from core.config import PhasmaConfig

# Initialize the Kalshi engine
config = PhasmaConfig()
engine = KalshiPredictionEngine(config)

print("🌤️ Testing Kalshi Weather-Only Restriction")
print("=" * 60)

# Test various market types
test_markets = [
    # Weather markets (should be allowed)
    {
        'ticker': 'HIGHNY0-25-85',
        'title': 'NYC - High temperature > 85°F on Dec 26',
        'last_price': 65,
        'volume': 2000,
        'expiration_date': '2024-12-26',
        'expected': 'ALLOWED'
    },
    {
        'ticker': 'RAINMIA-25',
        'title': 'Miami rain on Dec 25',
        'last_price': 40,
        'volume': 1500,
        'expiration_date': '2024-12-25',
        'expected': 'ALLOWED'
    },
    {
        'ticker': 'SNOWCHIM-25-2',
        'title': 'Chicago snow > 2 inches',
        'last_price': 30,
        'volume': 1000,
        'expiration_date': '2024-12-25',
        'expected': 'ALLOWED'
    },
    # Non-weather markets (should be blocked)
    {
        'ticker': 'KXPERSONPRESFUENTES-45',
        'title': 'Fuentes to win 2024 Presidential Election',
        'last_price': 35,
        'volume': 5000,
        'expiration_date': '2024-11-05',
        'expected': 'BLOCKED'
    },
    {
        'ticker': 'KXTEAMAVSTEAM-25',
        'title': 'Team A vs Team B - Winner',
        'last_price': 60,
        'volume': 3000,
        'expiration_date': '2024-12-26',
        'expected': 'BLOCKED'
    },
    {
        'ticker': 'KXFEDRATEUP-25',
        'title': 'Fed will raise rates',
        'last_price': 25,
        'volume': 4000,
        'expiration_date': '2024-12-31',
        'expected': 'BLOCKED'
    }
]

print("\n📊 Testing Market Filter:")
print("-" * 60)

allowed_count = 0
blocked_count = 0

for market in test_markets:
    ticker = market['ticker']
    title = market['title']
    expected = market['expected']
    
    # Check if it's detected as weather
    is_weather = engine._is_weather_market(ticker)
    
    # Analyze the market
    analysis = engine.analyze_market_opportunity(market)
    
    # Determine result
    if analysis.get('signal') is None and analysis.get('market_type') == 'non_weather':
        result = 'BLOCKED'
    elif analysis.get('signal') is None and 'non-weather' in analysis.get('rationale', '').lower():
        result = 'BLOCKED'
    else:
        result = 'ALLOWED'
    
    # Count
    if result == 'ALLOWED':
        allowed_count += 1
    else:
        blocked_count += 1
    
    # Check if match expected
    status = "✅" if result == expected else "❌"
    
    print(f"\n{status} {ticker}")
    print(f"   Title: {title}")
    print(f"   Weather Market: {is_weather}")
    print(f"   Expected: {expected} | Result: {result}")
    print(f"   Rationale: {analysis.get('rationale', 'No rationale')}")

print("\n" + "=" * 60)
print(f"📊 SUMMARY: {allowed_count} Allowed | {blocked_count} Blocked")

if allowed_count == 3 and blocked_count == 3:
    print("✅ SUCCESS: Kalshi is correctly restricted to weather markets only!")
else:
    print("❌ ERROR: Some markets are not being filtered correctly")

print("\n🌤️ Weather-Only Benefits:")
print("   • AI focuses on consistent weather patterns")
print("   • No election/sports/politics distractions")
print("   • Better specialization in weather prediction")
print("   • Cleaner, more reliable signals")
