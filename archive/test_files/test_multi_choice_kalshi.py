from engines.kalshi_engine import KalshiPredictionEngine
from core.config import PhasmaConfig

# Initialize the Kalshi engine
config = PhasmaConfig()
engine = KalshiPredictionEngine(config)

print("🗳️ Testing Kalshi Multi-Choice Market Support")
print("=" * 60)

# Test multi-choice markets
test_markets = [
    {
        'ticker': 'KXPERSONPRESFUENTES-45',
        'title': 'Fuentes to win 2024 Presidential Election',
        'last_price': 35,
        'volume': 5000,
        'expiration_date': '2024-11-05'
    },
    {
        'ticker': 'KXPERSONPRESMAM-45',
        'title': 'Mam to win 2024 Presidential Election',
        'last_price': 30,
        'volume': 4000,
        'expiration_date': '2024-11-05'
    },
    {
        'ticker': 'KXTEAMAVSTEAM-25',
        'title': 'Team A vs Team B - Winner',
        'last_price': 60,
        'volume': 3000,
        'expiration_date': '2024-12-26'
    },
    {
        'ticker': 'HIGHNY0-25-85',
        'title': 'NYC - High temperature > 85°F on Dec 26',
        'last_price': 65,
        'volume': 2000,
        'expiration_date': '2024-12-26'
    }
]

for market in test_markets:
    print(f"\nAnalyzing: {market['ticker']}")
    print(f"Title: {market['title']}")
    
    # Check if it's multi-choice
    is_multi = engine._is_multi_choice_market(market['ticker'])
    print(f"Multi-Choice: {'Yes' if is_multi else 'No'}")
    
    if is_multi:
        # Get multi-choice info
        choices = engine._get_multi_choice_info(market['ticker'])
        print(f"Available Choices: {len(choices)}")
        for choice in choices:
            print(f"  • {choice['title']}: {choice['implied_probability']:.1%}")
    
    # Analyze the market
    analysis = engine.analyze_market_opportunity(market)
    
    print(f"Signal: {analysis.get('signal', 'None')}")
    print(f"Confidence: {analysis.get('confidence', 0):.1%}")
    print(f"Rationale: {analysis.get('rationale', 'No rationale')}")
    
    if analysis.get('is_multi_choice'):
        print(f"Selected: {analysis.get('selected_choice', 'Unknown')}")
        print(f"Total Choices: {analysis.get('choices_count', 0)}")

print("\n" + "=" * 60)
print("✅ Multi-Choice Market Test Complete!")
print("\n📋 Key Features:")
print("1. Detects multi-choice markets (elections, vs matches)")
print("2. Fetches all available choices")
print("3. Selects the best value (highest probability)")
print("4. Returns BUY_YES for the selected choice only")
print("\n🎯 For regular markets (like temperature):")
print("- Uses normal Yes/No analysis")
print("- No multi-choice logic applied")
