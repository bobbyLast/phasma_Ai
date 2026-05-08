#!/usr/bin/env python3
"""
PHASMA AI - Robust Market Data Fetcher
Uses web scraping as fallback when APIs fail
"""

import requests
import json
from datetime import datetime

class WebScrapeFetcher:
    """Fetch market data via web scraping"""
    
    def get_stock_price(self, symbol):
        """Get stock price from Yahoo Finance via scraping"""
        try:
            # Yahoo Finance quote page
            url = f"https://finance.yahoo.com/quote/{symbol}"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            
            # Extract price from HTML
            import re
            # Look for price pattern in the HTML
            price_match = re.search(r'regularMarketPrice.*?value":"([\d\.]+)"', response.text)
            change_match = re.search(r'regularMarketChange.*?value":"([\d\.-]+)"', response.text)
            change_pct_match = re.search(r'regularMarketChangePercent.*?value":"([\d\.-]+)"', response.text)
            
            if price_match:
                price = float(price_match.group(1))
                change = float(change_match.group(1)) if change_match else 0
                change_pct = float(change_pct_match.group(1)) if change_pct_match else 0
                
                return {
                    'symbol': symbol,
                    'price': price,
                    'change': change,
                    'change_pct': change_pct,
                    'source': 'yahoo_scrape',
                    'timestamp': datetime.now().isoformat()
                }
        except Exception as e:
            print(f"   Error fetching {symbol}: {e}")
        
        return None

def test_fetcher():
    """Test the fetcher"""
    print("🚀 PHASMA AI - WEB SCRAPE DATA FETCHER")
    print("=" * 60)
    
    fetcher = WebScrapeFetcher()
    
    # Test symbols
    symbols = ['AAPL', 'MSFT', 'GOOGL', 'TSLA', 'NVDA']
    
    print(f"\n📊 Fetching {len(symbols)} symbols...\n")
    
    results = []
    for symbol in symbols:
        print(f"Fetching {symbol}...")
        data = fetcher.get_stock_price(symbol)
        if data:
            results.append(data)
            print(f"  ✅ {symbol}: ${data['price']:.2f} ({data['change']:+.2f})")
        else:
            print(f"  ❌ {symbol}: Failed")
    
    print(f"\n📈 RESULTS")
    print("=" * 60)
    print(f"Success: {len(results)}/{len(symbols)}")
    
    if results:
        print("\nLive Market Data:")
        for r in results:
            emoji = "📈" if r['change'] > 0 else "📉"
            print(f"{emoji} {r['symbol']:8s} ${r['price']:>10.2f} ({r['change']:+.2f}, {r['change_pct']:+.2f}%)")

if __name__ == "__main__":
    test_fetcher()
