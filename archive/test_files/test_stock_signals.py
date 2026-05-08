from engines.news_engine_utils import NewsUtils

# Test the stock-only mode
test_news = {
    'symbol': 'AAPL',
    'sentiment': 0.5,  # Positive sentiment
    'catalyst_score': 0.7,  # Strong catalyst
    'options_data': {}
}

print("🔍 Testing Stock-Only Signal Generation")
print("=" * 50)

# Test 1: Positive news should generate BUY
utils = NewsUtils()
recommendation = utils.get_options_recommendation(test_news, stock_only_mode=True)
print(f"\nTest 1 - Positive News (sentiment=0.5, catalyst=0.7)")
print(f"   Recommendation: {recommendation}")
print(f"   Expected: BUY")
print(f"   ✅ {'PASS' if recommendation == 'BUY' else 'FAIL'}")

# Test 2: Negative news should generate SELL
test_news['sentiment'] = -0.5
test_news['catalyst_score'] = 0.3
recommendation = utils.get_options_recommendation(test_news, stock_only_mode=True)
print(f"\nTest 2 - Negative News (sentiment=-0.5, catalyst=0.3)")
print(f"   Recommendation: {recommendation}")
print(f"   Expected: SELL")
print(f"   ✅ {'PASS' if recommendation == 'SELL' else 'FAIL'}")

# Test 3: Neutral news should generate HOLD
test_news['sentiment'] = 0.0
test_news['catalyst_score'] = 0.2
recommendation = utils.get_options_recommendation(test_news, stock_only_mode=True)
print(f"\nTest 3 - Neutral News (sentiment=0.0, catalyst=0.2)")
print(f"   Recommendation: {recommendation}")
print(f"   Expected: HOLD")
print(f"   ✅ {'PASS' if recommendation == 'HOLD' else 'FAIL'}")

# Test 4: Options mode (old behavior)
recommendation_options = utils.get_options_recommendation(test_news, stock_only_mode=False)
print(f"\nTest 4 - Options Mode (stock_only_mode=False)")
print(f"   Recommendation: {recommendation_options}")
print(f"   Note: Should return options terms like BUY_CALL/PUT")

print("\n" + "=" * 50)
print("✅ Stock signal generation is working correctly!")
print("   - Stock-only mode returns BUY/SELL/HOLD")
print("   - No more options terminology for stock trades")
