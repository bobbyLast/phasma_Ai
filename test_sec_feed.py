"""
Test SEC feed directly to debug
"""

import requests
import xml.etree.ElementTree as ET
from dateutil.parser import parse

def test_sec_feed():
    """Test SEC RSS feed directly"""
    
    print("🔍 Testing SEC RSS Feed Directly")
    print("="*50)
    
    # Test Form 4 feed
    form4_url = "https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent&CIK=&type=4&company=&dateb=&owner=only&count=10&output=atom"
    
    session = requests.Session()
    session.headers.update({
        "User-Agent": "PhasmaAI Test (https://sec.gov)"
    })
    
    print("\n📄 Fetching Form 4 feed...")
    response = session.get(form4_url, timeout=30)
    print(f"Status: {response.status_code}")
    print(f"Content length: {len(response.content)}")
    
    if response.status_code == 200:
        print("\n📋 Parsing XML...")
        root = ET.fromstring(response.content)
        ns = {'atom': 'http://www.w3.org/2005/Atom'}
        
        entries = root.findall('atom:entry', ns)
        print(f"Found {len(entries)} entries")
        
        for i, entry in enumerate(entries[:3]):  # Show first 3
            title = entry.find('atom:title', ns).text
            print(f"\n{i+1}. Title: {title[:100]}...")
            
            # Try to extract ticker - different format
            import re
            # Look for ticker in parentheses after company name
            ticker_match = re.search(r'\(([A-Z]{1,5})\)', title)
            if not ticker_match:
                # Try alternative format
                ticker_match = re.search(r'FORM 4\s+([A-Z]{1,5})', title.upper())
            
            if ticker_match:
                print(f"   Ticker: {ticker_match.group(1)}")
            
            # Check for updated date instead of published
            updated = entry.find('atom:updated', ns)
            if updated is not None:
                pub_date = updated.text
                print(f"   Date: {pub_date}")
            
            summary = entry.find('atom:summary', ns).text or ""
            if 'purchase' in summary.lower():
                print(f"   ✓ Contains 'purchase'")
            else:
                print(f"   ✗ No purchase found")
            
            # Show part of summary to understand format
            if summary:
                print(f"   Summary: {summary[:100]}...")
    
    print("\n" + "="*50)

if __name__ == "__main__":
    test_sec_feed()
