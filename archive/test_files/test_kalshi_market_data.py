"""Check actual market data to understand why no opportunities"""

from core.config import PhasmaConfig
from engines.kalshi_engine import KalshiPredictionEngine
import json

def check_market_data():
    config = PhasmaConfig()
    kalshi = KalshiPredictionEngine(config)
    
    print("🔍 Checking Actual Market Data")
    print("=" * 60)
    
    # Get some weather series
    series_url = f"{kalshi.base_url}/series"
    response = kalshi.session.get(series_url)
    all_series = response.json().get('series', [])
    
    # Find weather series with markets
    weather_series = []
    for s in all_series:
        title = s.get('title', '').lower()
        if any(kw in title for kw in ['temperature', 'temp', 'snow', 'rain']):
            weather_series.append(s)
    
    print(f"Found {len(weather_series)} weather series")
    
    # Check first few
    for i, series in enumerate(weather_series[:5]):
        ticker = series.get('ticker')
        title = series.get('title')
        
        print(f"\n{i+1}. {ticker}")
        print(f"   Title: {title}")
        
        # Get markets
        markets_url = f"{kalshi.base_url}/markets?series_ticker={ticker}&status=open"
        markets_resp = kalshi.session.get(markets_url)
        markets = markets_resp.json().get('markets', [])
        
        print(f"   Markets: {len(markets)}")
        
        for j, market in enumerate(markets[:3]):
            print(f"\n     Market {j+1}:")
            print(f"       Ticker: {market.get('ticker')}")
            print(f"       Title: {market.get('subtitle', 'N/A')}")
            print(f"       Yes Price: ${market.get('yes_price', 0)/100:.2f}")
            print(f"       No Price: ${market.get('no_price', 0)/100:.2f}")
            print(f"       Volume: {market.get('volume', 0)}")
            print(f"       24h Volume: {market.get('volume_24h', 0)}")
            print(f"       Bid/Ask: ${market.get('yes_bid', 0)/100:.2f}/${market.get('yes_ask', 0)/100:.2f}")
            print(f"       Close Time: {market.get('close_time', 'N/A')}")
            
            # Check if it would pass
            price = market.get('yes_price', 0) / 100
            volume = market.get('volume', 0)
            
            print(f"       Would Pass: Price ${price:.2f} in $0.10-$0.90? {0.10 <= price <= 0.90}")
            print(f"       Would Pass: Volume {volume} >= 50? {volume >= 50}")

if __name__ == "__main__":
    check_market_data()
