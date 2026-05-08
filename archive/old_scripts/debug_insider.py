#!/usr/bin/env python3
"""Debug insider trading system to see what's happening"""

from utils.insider_opportunity_analyzer import get_insider_analyzer, SEC_EDGAR_URL
from core.config import PhasmaConfig
import xml.etree.ElementTree as ET

def main():
    print("=== Debugging Insider System ===\n")
    
    # Load config
    config = PhasmaConfig('config.json')
    analyzer = get_insider_analyzer(config.data)
    
    # Temporarily disable filters for debugging
    analyzer.min_value = 0  # No minimum value
    analyzer.min_market_cap = 0  # No minimum market cap
    analyzer.min_avg_volume = 0  # No minimum volume
    analyzer.target_sectors = []  # No sector filter
    
    print("1. Fetching SEC feed...")
    resp = analyzer._sec_get(SEC_EDGAR_URL, timeout=30)
    if resp is None:
        print("   ✗ Failed to fetch SEC feed")
        return
    print(f"   ✓ Fetched SEC feed: {resp.status_code}")
    
    print("\n2. Parsing entries...")
    entries = analyzer._parse_sec_edgar(resp.text)
    print(f"   ✓ Found {len(entries)} entries")
    
    # Show first few entries
    print("\n   First 3 entries:")
    for i, entry in enumerate(entries[:3], 1):
        print(f"   {i}. {entry.get('title', '')[:80]}...")
        print(f"      Link: {entry.get('link', '')[:60]}...")
        print(f"      Published: {entry.get('published', 'N/A')}")
    
    print("\n3. Testing XML fetching...")
    xml_success = 0
    xml_fail = 0
    transactions_found = 0
    
    for i, entry in enumerate(entries[:10], 1):
        print(f"\n   Entry {i}: {entry.get('title', '')[:50]}...")
        
        # Try to fetch XML
        xml_content = analyzer._fetch_form4_xml(entry.get('link', ''))
        if xml_content:
            xml_success += 1
            print(f"      ✓ XML fetched ({len(xml_content)} chars)")
            
            # Parse transactions
            transactions = analyzer._parse_form4_transactions(xml_content)
            if transactions:
                transactions_found += len(transactions)
                print(f"      ✓ Found {len(transactions)} transactions:")
                for tx in transactions[:3]:
                    print(f"         - {tx['ticker']} {tx['transaction_code']} {tx['shares']} @ ${tx['price']} = ${tx['total_value']:,.0f}")
                    print(f"           Insider: {tx.get('insider_name', 'N/A')} ({tx.get('insider_role', 'N/A')})")
            else:
                print(f"      ✗ No transactions found")
        else:
            xml_fail += 1
            print(f"      ✗ Failed to fetch XML")
    
    print(f"\n=== Summary ===")
    print(f"Entries processed: {min(10, len(entries))}")
    print(f"XML fetch success: {xml_success}")
    print(f"XML fetch failed: {xml_fail}")
    print(f"Total transactions found: {transactions_found}")
    
    if xml_success == 0:
        print("\n⚠️  No XML files were successfully fetched!")
        print("   This suggests the SEC index page structure may have changed.")
        print("   The regex for finding XML links might need updating.")
    
    if transactions_found == 0 and xml_success > 0:
        print("\n⚠️  XML was fetched but no purchase transactions found!")
        print("   This is normal - most Form 4s are sales, not purchases.")
        print("   Need to process more entries to find actual buys.")

if __name__ == "__main__":
    main()
