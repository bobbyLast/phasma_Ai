import re

# Test the link generation logic with actual weather market tickers
test_tickers = [
    'HIGHNY0-25-85',      # NYC high temp
    'RAINMIA-25',         # Miami rain
    'SNOWCHIM-25-2',      # Chicago snow
    'KXTEMP-25',          # Global temp
    'HURFL-25',           # Hurricane Florida
    'KXHIGHDEN-25',       # Denver high temp
    'LOWTMIA-25',         # Miami low temp
]

def get_market_trade_link(ticker: str) -> str:
    """Get direct trading link for a Kalshi market."""
    # For weather markets, the entire ticker is usually the event ticker
    # Kalshi event URLs follow the pattern: https://kalshi.com/events/{event_ticker}
    
    # Remove any contract-specific suffixes
    # Weather markets typically don't have complex suffixes like political markets
    if '-' in ticker:
        parts = ticker.split('-')
        # For weather markets, usually format is EVENT-YEAR or EVENT-YEAR-VALUE
        # Take everything except the last part if it looks like a specific value
        if len(parts) > 2 and parts[-1].isdigit():
            event_ticker = '-'.join(parts[:-1])
        else:
            event_ticker = ticker
    else:
        event_ticker = ticker
        
    return f"https://kalshi.com/events/{event_ticker.lower()}"

print("Testing FIXED Kalshi Trade Link Generation:")
print("=" * 50)

for ticker in test_tickers:
    link = get_market_trade_link(ticker)
    print(f"{ticker:20s} -> {link}")

print("\n" + "=" * 50)
print("Expected format examples:")
print("- HIGHNY0-25-85 should link to highny0-25 event")
print("- RAINMIA-25 should link to rainmia-25 event")
print("- SNOWCHIM-25-2 should link to snowchim-25 event")
