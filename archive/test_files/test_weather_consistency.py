from engines.weather_consistency_engine import WeatherConsistencyEngine

# Initialize the consistency engine
engine = WeatherConsistencyEngine()

# Example weather contracts from Kalshi
test_contracts = [
    {
        'title': 'NYC - High temperature > 85°F on Dec 26',
        'ticker': 'HIGHNY0-25-85',
        'last_price': 65,  # 65% implied probability
        'volume': 5000,
        'expiration_date': '2024-12-26'
    },
    {
        'title': 'Chicago - Snowfall > 2 inches on Dec 27',
        'ticker': 'SNOWCHIM-25-2',
        'last_price': 30,  # 30% implied probability
        'volume': 2000,
        'expiration_date': '2024-12-27'
    },
    {
        'title': 'Miami - Measurable rain on Dec 26',
        'ticker': 'RAINMIA-25',
        'last_price': 20,  # 20% implied probability
        'volume': 8000,
        'expiration_date': '2024-12-26'
    },
    {
        'title': 'Hurricane hits Florida in 2025',
        'ticker': 'HURFL-25',
        'last_price': 45,  # 45% implied probability
        'volume': 1000,
        'expiration_date': '2025-12-31'
    }
]

print("🌤️ Phasma Weather Consistency Engine Test")
print("=" * 50)

for contract in test_contracts:
    print(f"\nAnalyzing: {contract['title']}")
    print(f"Market Price: {contract['last_price']}% | Volume: {contract['volume']:,}")
    
    result = engine.evaluate_trade_opportunity(contract)
    
    if result['trade']:
        print(f"✅ TRADE: {result['reason']}")
        print(f"   Edge: {result['edge']:.1%}")
        print(f"   Confidence: {result['confidence']:.1%}")
        print(f"   Stability: {result.get('stability', 0):.1%}")
        print(f"   Model Agreement: {result.get('agreement', 0):.1%}")
    else:
        print(f"❌ SKIP: {result['reason']}")
        if 'edge' in result:
            print(f"   Edge was only {result['edge']:.1%}")

print("\n" + "=" * 50)
print("Key Principles Demonstrated:")
print("1. Only high-consistency markets (temp/rain) get traded")
print("2. Requires minimum 8% edge for temp/rain markets")
print("3. Checks forecast stability before trading")
print("4. Low-consistency markets (hurricanes) are avoided")
