import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta

# Fetch SEC Form 4 data
url = "https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent&CIK=&type=4&company=&dateb=&owner=include&count=100&output=atom"
headers = {"User-Agent": "PhasmaAI/InsiderMonitor (https://sec.gov)"}
resp = requests.get(url, headers=headers, timeout=30)

# Parse XML
root = ET.fromstring(resp.text)
entries = root.findall("{http://www.w3.org/2005/Atom}entry")

print(f"Found {len(entries)} Form 4 entries\n")

# Show first 20 entries with analysis
for i, entry in enumerate(entries[:20]):
    title = entry.find("{http://www.w3.org/2005/Atom}title").text
    updated = entry.find("{http://www.w3.org/2005/Atom}updated").text
    
    # Extract ticker
    import re
    ticker_match = re.search(r'\(([A-Z]{1,5})\)', title)
    ticker = ticker_match.group(1) if ticker_match else None
    
    # Extract price (if any)
    price_match = re.search(r'\$([0-9]+(\.[0-9]+)?)', title)
    price = float(price_match.group(1)) if price_match else None
    
    print(f"{i+1:2d}. {title}")
    print(f"     Ticker: {ticker or 'N/A'} | Price: ${price or 'N/A'} | Updated: {updated}")
    
    # Check filters
    if ticker and len(ticker) <= 5:
        print(f"     ✓ Valid ticker format")
    else:
        print(f"     ✗ Invalid/missing ticker")
    
    if price and price >= 1.00 and price <= 50.00:
        print(f"     ✓ Price in range ($1-$50)")
    elif price:
        print(f"     ✗ Price ${price:.2f} out of range")
    else:
        print(f"     ? No price info in title")
    
    print()
