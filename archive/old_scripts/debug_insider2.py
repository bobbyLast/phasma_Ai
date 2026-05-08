#!/usr/bin/env python3
"""Debug insider trading system to see where filtering happens"""

from utils.insider_opportunity_analyzer import get_insider_analyzer, SEC_EDGAR_URL
from core.config import PhasmaConfig
from datetime import datetime, timedelta, timezone
from dateutil import parser as date_parser

def main():
    print("=== Debugging Insider Filtering ===\n")
    
    # Load config
    config = PhasmaConfig('config.json')
    analyzer = get_insider_analyzer(config.data)
    
    # Disable all filters for debugging
    analyzer.min_value = 0
    analyzer.min_market_cap = 0
    analyzer.min_avg_volume = 0
    analyzer.target_sectors = []
    
    print("1. Fetching and processing with detailed logging...")
    
    resp = analyzer._sec_get(SEC_EDGAR_URL, timeout=30)
    entries = analyzer._parse_sec_edgar(resp.text)
    print(f"   Found {len(entries)} entries")
    
    opportunities = []
    cutoff = datetime.now(timezone.utc) - timedelta(days=analyzer.lookback_days)
    
    for i, entry in enumerate(entries[:20], 1):
        print(f"\n--- Entry {i} ---")
        print(f"Title: {entry.get('title', '')[:80]}")
        
        link = entry.get('link', '')
        if not link:
            print("✗ No link")
            continue
            
        pub_raw = entry.get('published')
        if not pub_raw:
            print("✗ No publish date")
            continue
            
        try:
            pub_dt = date_parser.parse(pub_raw)
        except Exception as e:
            print(f"✗ Date parse error: {e}")
            continue
            
        if pub_dt < cutoff:
            print(f"✗ Too old: {pub_dt}")
            continue
            
        print(f"✓ Date OK: {pub_dt}")
        
        # Fetch XML
        xml_content = analyzer._fetch_form4_xml(link)
        if not xml_content:
            print("✗ No XML fetched")
            continue
            
        transactions = analyzer._parse_form4_transactions(xml_content)
        if not transactions:
            print("✗ No transactions")
            continue
            
        print(f"✓ Found {len(transactions)} transactions")
        
        for tx in transactions:
            ticker = tx['ticker']
            print(f"\n  Transaction: {ticker} {tx['transaction_code']} {tx['shares']} @ ${tx['price']} = ${tx['total_value']:,.0f}")
            
            # Check filters
            print(f"  Value filter: ${tx['total_value']:,.0f} >= ${analyzer.min_value}")
            if tx['total_value'] < analyzer.min_value:
                print("  ✗ Failed value filter")
                continue
                
            print("  ✓ Value filter passed")
            
            # Get market data
            market_data = analyzer._market_data_cache.get(ticker)
            if market_data is None:
                print(f"  Fetching market data for {ticker}...")
                market_data = analyzer._get_market_data(ticker)
                analyzer._market_data_cache[ticker] = market_data
                
            if not market_data:
                print("  ✗ No market data")
                continue
                
            print("  ✓ Market data found")
            print(f"    Market cap: ${market_data.get('market_cap', 0):,.0f}")
            print(f"    Sector: {market_data.get('sector', 'N/A')}")
            
            # Calculate score
            days_since = (datetime.now(timezone.utc) - pub_dt).days
            insider_data = {
                'ticker': ticker,
                'title': entry.get('title', ''),
                'link': link,
                'published': pub_raw,
                'purchase_price': tx['price'],
                'transaction_value': tx['total_value'],
                'days_since_purchase': days_since,
                'insider_name': tx.get('insider_name'),
                'insider_role': tx.get('insider_role'),
            }
            
            score, reasoning = analyzer._calculate_opportunity_score(insider_data, market_data)
            print(f"  Score: {score:.0f} - {reasoning}")
            
            if score >= 50:
                print("  ✓ Score >= 50, adding to opportunities")
                opportunities.append({
                    **insider_data,
                    **market_data,
                    'opportunity_score': score,
                    'reasoning': reasoning,
                })
            else:
                print("  ✗ Score < 50")
    
    print(f"\n=== Final Results ===")
    print(f"Total opportunities found: {len(opportunities)}")
    
    for opp in opportunities:
        print(f"\n{opp['ticker']}: Score {opp['opportunity_score']:.0f}")
        print(f"  {opp['reasoning']}")

if __name__ == "__main__":
    import sys
    from datetime import timedelta
    from dateutil import parser as date_parser
    main()
