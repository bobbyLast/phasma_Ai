#!/usr/bin/env python3
"""
Check what price data the AI is actually using
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.price_fetcher import get_price_fetcher

def check_ai_price_data():
    """Check what prices the AI is actually using"""
    
    print("="*60)
    print("CHECKING AI PRICE DATA")
    print("="*60)
    
    # Initialize the same price fetcher the AI uses
    price_fetcher = get_price_fetcher()
    
    # Check SOFI price
    print("\nChecking SOFI price...")
    sofia_price = price_fetcher.get_real_price('SOFI')
    
    if sofia_price:
        print(f"  AI sees SOFI at: ${sofia_price:.2f}")
    else:
        print("  [ERROR] AI could not fetch SOFI price")
    
    # Check other stocks for comparison
    test_symbols = ['AI', 'GOOGL', 'TSLA', 'AAPL']
    
    print("\nChecking other stock prices...")
    for symbol in test_symbols:
        price = price_fetcher.get_real_price(symbol)
        if price:
            print(f"  {symbol}: ${price:.2f}")
        else:
            print(f"  {symbol}: [ERROR] Could not fetch")
    
    # Compare with yfinance directly
    print("\nComparing with yfinance directly...")
    import yfinance as yf
    
    for symbol in ['SOFI', 'AI', 'GOOGL']:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period='1d')
        if len(hist) > 0:
            yf_price = hist['Close'].iloc[-1]
            ai_price = price_fetcher.get_real_price(symbol)
            
            if ai_price:
                diff = abs(yf_price - ai_price)
                pct_diff = (diff / yf_price) * 100
                print(f"  {symbol}: yfinance=${yf_price:.2f}, AI=${ai_price:.2f}, diff={pct_diff:.1f}%")
                
                if pct_diff > 1:
                    print(f"    [WARNING] Price mismatch > 1%")
                else:
                    print(f"    [OK] Prices match")
            else:
                print(f"  {symbol}: yfinance=${yf_price:.2f}, AI=[ERROR]")
    
    print("\n" + "="*60)
    print("CONCLUSION:")
    print("If AI prices match yfinance, the AI is using correct data.")
    print("If there are large differences, there's a data source issue.")

if __name__ == "__main__":
    check_ai_price_data()
