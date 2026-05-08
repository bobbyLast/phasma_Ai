from engines.dynamic_market_scanner import DynamicMarketScanner

scanner = DynamicMarketScanner()
opportunities = scanner.get_fresh_opportunities(total_limit=15)

print(f"Found {len(opportunities)} fresh opportunities:")
for i, opp in enumerate(opportunities, 1):
    symbol = opp['symbol']
    change = opp.get('change_pct', 0)
    volume = opp.get('volume', 0)
    opp_type = opp.get('type', opp.get('momentum', 'UNKNOWN'))
    print(f"{i:2d}. {symbol:6s} - {opp_type:20s} ({change:+6.1f}%) Vol: {volume:10,}")
