#!/usr/bin/env python3
"""
Test OpenInsider scraper functionality
"""

import asyncio
from utils.openinsider_scraper import OpenInsiderScraper

async def test_openinsider():
    """Test OpenInsider scraper"""
    print("🕵️ Testing OpenInsider Scraper")
    print("=" * 50)
    
    # Test parsing functionality without actual scraping
    scraper = OpenInsiderScraper()
    
    # Test confidence calculation
    print("\n1. Testing confidence calculation:")
    print("-" * 50)
    
    test_cases = [
        {'is_buy': True, 'title': 'CEO', 'value': 500000, 'expected': 'High'},
        {'is_buy': True, 'title': 'Director', 'value': 100000, 'expected': 'Medium'},
        {'is_buy': True, 'title': 'Manager', 'value': 50000, 'expected': 'Low'},
        {'is_buy': False, 'title': 'CEO', 'value': 500000, 'expected': 'Medium'},  # Sells have lower base
    ]
    
    for case in test_cases:
        confidence = scraper._calculate_confidence(
            case['is_buy'], 
            case['title'], 
            case['value']
        )
        print(f"   {case['title']} {'Buy' if case['is_buy'] else 'Sell'} ${case['value']:,.0f}: {confidence:.1%} confidence ({case['expected']})")
    
    # Test data parsing
    print("\n2. Testing data parsing:")
    print("-" * 50)
    
    # Test price parsing
    price_tests = ['$175.50', '$1,234.56', '', '$']
    for price_str in price_tests:
        result = scraper._parse_price(price_str)
        print(f"   Price '{price_str}' -> {result}")
    
    # Test quantity parsing
    qty_tests = ['1000', '50,000', '', '0']
    for qty_str in qty_tests:
        result = scraper._parse_quantity(qty_str)
        print(f"   Quantity '{qty_str}' -> {result}")
    
    # Test date parsing
    date_tests = ['2024-02-10', '02/10/2024', 'Feb 10 2024', '']
    for date_str in date_tests:
        result = scraper._parse_date(date_str)
        print(f"   Date '{date_str}' -> {result}")
    
    # Test symbol filtering
    print("\n3. Testing mock trade data generation:")
    print("-" * 50)
    
    # Create mock trade data
    mock_trades = [
        {
            'symbol': 'AAPL',
            'company_name': 'Apple Inc.',
            'insider_name': 'John Doe',
            'insider_title': 'CEO',
            'trade_type': 'Buy',
            'action': 'BUY',
            'price': 175.50,
            'quantity': 1000,
            'value': 175500,
            'confidence': 0.85,
            'source': 'openinsider'
        },
        {
            'symbol': 'MSFT',
            'company_name': 'Microsoft Corp.',
            'insider_name': 'Jane Smith',
            'insider_title': 'CFO',
            'trade_type': 'Buy',
            'action': 'BUY',
            'price': 380.25,
            'quantity': 500,
            'value': 190125,
            'confidence': 0.80,
            'source': 'openinsider'
        }
    ]
    
    # Convert to signals
    signals = []
    for trade in mock_trades:
        signal = {
            'symbol': trade['symbol'],
            'action': trade['action'],
            'confidence': trade['confidence'],
            'position_size': min(trade['value'] / 1000, 1000),
            'rationale': f"Insider {trade['insider_name']} ({trade['insider_title']}) bought ${trade['value']:,.0f} worth",
            'source': trade['source'],
            'current_price': trade['price'],
            'trade_type': 'STOCK',
            'insider_data': trade,
            'timestamp': '2026-02-10T18:45:00'
        }
        signals.append(signal)
    
    print(f"Generated {len(signals)} trading signals:")
    for signal in signals:
        print(f"\n   Signal: {signal['symbol']}")
        print(f"   Action: {signal['action']}")
        print(f"   Confidence: {signal['confidence']:.1%}")
        print(f"   Position Size: ${signal['position_size']:,.0f}")
        print(f"   Rationale: {signal['rationale']}")
    
    print("\n✅ OpenInsider scraper tests completed!")
    print("\nNote: Actual scraping disabled to avoid rate limits.")
    print("To enable real scraping, call scraper.scrape_latest_insider_trades()")

if __name__ == "__main__":
    asyncio.run(test_openinsider())
