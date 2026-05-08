#!/usr/bin/env python3
"""Check what types of filings are in the SEC feed"""

import requests
import xml.etree.ElementTree as ET
from collections import Counter

def main():
    print("=== Analyzing SEC Feed Content ===\n")
    
    url = "https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent&CIK=&type=4&company=&dateb=&owner=include&count=100&output=atom"
    headers = {"User-Agent": "PhasmaAI/InsiderMonitor (https://sec.gov)"}
    
    resp = requests.get(url, headers=headers, timeout=30)
    if resp.status_code != 200:
        print(f"Failed to fetch: {resp.status_code}")
        return
    
    root = ET.fromstring(resp.text)
    ns = {'atom': 'http://www.w3.org/2005/Atom'}
    
    # Analyze filing types
    filing_types = Counter()
    tickers = Counter()
    
    for entry in root.findall('atom:entry', ns):
        title_el = entry.find('atom:title', ns)
        title = title_el.text if title_el is not None and title_el.text is not None else ""
        
        # Extract form type
        if ' - ' in title:
            form_type = title.split(' - ')[0]
            filing_types[form_type] += 1
        
        # Extract ticker if present
        match = re.search(r'\(([A-Z]+)\)', title)
        if match:
            tickers[match.group(1)] += 1
    
    print("Filing types found:")
    for form_type, count in filing_types.most_common():
        print(f"  {form_type}: {count}")
    
    print("\nTop tickers found:")
    for ticker, count in tickers.most_common(10):
        print(f"  {ticker}: {count}")
    
    # Show some sample Form 4 entries
    print("\nSample Form 4 entries:")
    count = 0
    for entry in root.findall('atom:entry', ns):
        title = entry.findtext('atom:title', ns) or ""
        if title.startswith('4 - '):
            print(f"\n{title[:100]}...")
            count += 1
            if count >= 5:
                break

if __name__ == "__main__":
    import re
    main()
