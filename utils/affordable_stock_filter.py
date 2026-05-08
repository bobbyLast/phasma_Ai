"""
Affordable Stock Filter - Pre-filters watchlists to remove stocks over available capital
"""

import yfinance as yf
from typing import List
import time

class AffordableStockFilter:
    """Filters stock lists to only include affordable stocks"""
    
    def __init__(self, max_price: float):
        self.max_price = max_price
        self.cache = {}  # Cache prices to avoid repeated API calls
        
    def get_price(self, symbol: str) -> float:
        """Get current price with simple caching"""
        if symbol in self.cache:
            return self.cache[symbol]
        
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period='1d')
            if len(hist) > 0:
                price = float(hist['Close'].iloc[-1])
                self.cache[symbol] = price
                return price
        except:
            pass
        
        return None
    
    def filter_affordable(self, symbols: List[str]) -> List[str]:
        """Filter list to only include stocks under max_price"""
        affordable = []
        
        print(f"\nFiltering {len(symbols)} stocks by max price: ${self.max_price:.2f}")
        
        for symbol in symbols:
            price = self.get_price(symbol)
            
            if price is None:
                print(f"  [ERROR] {symbol}: No price data")
                continue
                
            if price <= self.max_price:
                affordable.append(symbol)
                print(f"  [OK] {symbol}: ${price:.2f} (affordable)")
            else:
                print(f"  [EXPENSIVE] {symbol}: ${price:.2f} > ${self.max_price:.2f} (too expensive)")
            
            # Rate limiting
            time.sleep(0.1)
        
        print(f"\n[OK] {len(affordable)}/{len(symbols)} stocks are affordable\n")
        return affordable
