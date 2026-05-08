import yfinance as yf

# Get SOFI data
ticker = yf.Ticker('SOFI')
hist = ticker.history(period='2d')

print("SOFI price data:")
print(hist[['Close', 'Volume']])

if len(hist) >= 2:
    prev_close = hist['Close'].iloc[-2]
    current = hist['Close'].iloc[-1]
    change = current - prev_close
    pct_change = (change / prev_close) * 100
    
    print(f"\nPrevious close: ${prev_close:.2f}")
    print(f"Current price: ${current:.2f}")
    print(f"Change: ${change:.2f} ({pct_change:.2f}%)")

# Check if the AI's price fetcher has issues
print("\nChecking price fetcher module...")
try:
    from utils.price_fetcher import get_price_fetcher
    pf = get_price_fetcher()
    price = pf.get_real_price('SOFI')
    print(f"Price fetcher returns: ${price:.2f}" if price else "Price fetcher failed")
except Exception as e:
    print(f"Price fetcher error: {e}")
