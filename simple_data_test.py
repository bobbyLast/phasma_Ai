#!/usr/bin/env python3
"""
SIMPLE WORKING DATA FETCHER
Uses Alpha Vantage and Finnhub APIs directly
"""

import os
import requests
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

class SimpleDataFetcher:
    """Simple fetcher using working APIs"""
    
    def __init__(self):
        self.alpha_key = os.getenv('ALPHA_VANTAGE_KEY')
        self.finnhub_key = os.getenv('FINNHUB_API_KEY')
        self.cache = {}
        
    def get_price(self, symbol):
        """Get real price"""
        # Try Alpha Vantage first
        if self.alpha_key:
            try:
                url = "https://www.alphavantage.co/query"
                params = {
                    'function': 'GLOBAL_QUOTE',
                    'symbol': symbol,
                    'apikey': self.alpha_key
                }
                r = requests.get(url, params=params, timeout=10)
                data = r.json()
                if 'Global Quote' in data:
                    price = float(data['Global Quote']['05. price'])
                    if price > 0:
                        return price
            except:
                pass
        
        # Try Finnhub
        if self.finnhub_key:
            try:
                url = "https://finnhub.io/api/v1/quote"
                params = {'symbol': symbol, 'token': self.finnhub_key}
                r = requests.get(url, params=params, timeout=10)
                data = r.json()
                if 'c' in data and data['c'] > 0:
                    return float(data['c'])
            except:
                pass
        
        return None

if __name__ == "__main__":
    fetcher = SimpleDataFetcher()
    
    print("Testing real data fetch...")
    for sym in ['AAPL', 'MSFT', 'TSLA']:
        price = fetcher.get_price(sym)
        if price:
            print(f"{sym}: ${price:.2f}")
        else:
            print(f"{sym}: FAILED")
