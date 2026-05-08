import sys
sys.path.insert(0, '.')
from dotenv import load_dotenv
load_dotenv()

import json
from engines.kalshi_engine import KalshiPredictionEngine

# Load config
with open('config.json', 'r') as f:
    config = json.load(f)

# Initialize Kalshi engine
kalshi = KalshiPredictionEngine(config)

print('🔑 Testing Kalshi API with provided key...')
print('🔗 Testing market data retrieval...')

# Test with empty string to get all markets
markets = kalshi.get_market_implied_view('')
if markets:
    print(f'✅ Found {len(markets)} total markets')
    print('📊 Available series tickers:')
    series_seen = set()
    for market in markets[:10]:  # Check first 10
        series = market.get('series_ticker', 'Unknown')
        if series not in series_seen:
            series_seen.add(series)
            print(f'   - {series}')
    
    print('\\n🎯 Testing first market:')
    market = markets[0]
    ticker = market.get('ticker', 'Unknown')
    title = market.get('title', 'Unknown Title')
    implied_prob = market.get('implied_probability', 0.5)
    volume = market.get('volume', 0)
    
    print(f'{ticker}: {title[:60]}...')
    print(f'   Prob: {implied_prob:.1%} | Vol: ${volume:,.0f}')
    
    # Test analysis
    analysis = kalshi.analyze_market_opportunity(market)
    if analysis.get('signal'):
        confidence = analysis.get('confidence', 0)
        signal = analysis.get('signal')
        print(f'   Signal: {signal} (Conf: {confidence:.1%})')
    else:
        print('   No signal')
else:
    print('❌ No markets found')
