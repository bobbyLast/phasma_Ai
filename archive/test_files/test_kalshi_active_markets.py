"""Find actively trading Kalshi markets"""

from core.config import PhasmaConfig
from engines.kalshi_engine import KalshiPredictionEngine

def find_active_markets():
    config = PhasmaConfig()
    kalshi = KalshiPredictionEngine(config)
    
    print("🔍 Finding ACTIVELY Trading Markets")
    print("=" * 60)
    
    # Get all open markets directly
    markets_url = f"{kalshi.base_url}/markets?status=open&limit=100"
    response = kalshi.session.get(markets_url)
    all_markets = response.json().get('markets', [])
    
    print(f"Total open markets: {len(all_markets)}")
    
    # Filter for active markets
    active_markets = []
    for market in all_markets:
        price = market.get('yes_price', 0) / 100
        volume = market.get('volume', 0)
        
        # Must have non-zero price and some volume
        if price > 0.01 and volume > 0:
            active_markets.append(market)
    
    print(f"Active markets (price > $0.01 and volume > 0): {len(active_markets)}")
    
    # Show top active markets
    print("\n📊 Top 10 Most Active Markets:")
    print("-" * 60)
    
    # Sort by volume
    active_markets.sort(key=lambda x: x.get('volume', 0), reverse=True)
    
    for i, market in enumerate(active_markets[:10]):
        ticker = market.get('ticker')
        title = market.get('subtitle', market.get('title', 'N/A'))
        price = market.get('yes_price', 0) / 100
        volume = market.get('volume', 0)
        series = market.get('series_ticker', '')
        
        # Classify market type
        series_lower = series.lower()
        if any(kw in series_lower for kw in ['temp', 'weather', 'rain', 'snow']):
            market_type = "WEATHER"
        elif any(kw in series_lower for kw in ['cpi', 'econ', 'employment']):
            market_type = "ECON"
        elif any(kw in series_lower for kw in ['fed', 'rate']):
            market_type = "FED"
        else:
            market_type = "OTHER"
        
        print(f"\n{i+1}. {ticker}")
        print(f"   Type: {market_type}")
        print(f"   Title: {title[:60]}...")
        print(f"   Price: ${price:.2f} | Volume: {volume:,}")
        print(f"   Series: {series}")
        
        # Check if it would pass adjusted thresholds
        would_pass = (
            0.10 <= price <= 0.90 and
            volume >= 50
        )
        print(f"   Would Pass Adjusted: {would_pass}")

if __name__ == "__main__":
    find_active_markets()
