#!/usr/bin/env python3
"""
Check all Kalshi market types to see if any political/economic markets exist
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from engines.kalshi_engine import KalshiPredictionEngine

def check_market_types():
    """Examine all Kalshi markets to see what types are available"""
    
    print("🔍 CHECKING KALSHI MARKET TYPES")
    print("=" * 50)
    
    config = {'kalshi': {'api_key': None}}
    engine = KalshiPredictionEngine(config)
    
    try:
        # Switch back to elections domain to check available markets
        engine.base_url = "https://api.elections.kalshi.com/trade-api/v2"
        
        print("📡 Fetching all markets from elections domain...")
        response = engine._get("markets")
        
        if not response or 'markets' not in response:
            print("❌ No market data found")
            return False
        
        markets = response['markets']
        print(f"✅ Found {len(markets)} total markets")
        
        # Analyze market types
        political_count = 0
        economic_count = 0
        sports_count = 0
        other_count = 0
        
        political_examples = []
        economic_examples = []
        sports_examples = []
        other_examples = []
        
        for market in markets:
            ticker = market.get('ticker', '')
            title = market.get('title', '').lower()
            category = market.get('category', '').lower()
            
            # Classify market type
            if ticker.startswith('KXMVESPORTS') or any(sport in title for sport in ['nfl', 'nba', 'mlb', 'player', 'yards', 'points', 'rushing', 'touchdown']):
                sports_count += 1
                if len(sports_examples) < 3:
                    sports_examples.append(market.get('title', 'No title'))
            elif any(pol in title for pol in ['election', 'congress', 'senate', 'president', 'vote', 'political', 'biden', 'trump']):
                political_count += 1
                if len(political_examples) < 3:
                    political_examples.append(market.get('title', 'No title'))
            elif any(econ in title for econ in ['economy', 'gdp', 'inflation', 'fed', 'interest', 'market', 'stock', 'financial']):
                economic_count += 1
                if len(economic_examples) < 3:
                    economic_examples.append(market.get('title', 'No title'))
            else:
                other_count += 1
                if len(other_examples) < 3:
                    other_examples.append(market.get('title', 'No title'))
        
        # Report findings
        print(f"\n📊 MARKET TYPE BREAKDOWN:")
        print(f"   🏈 Sports Betting: {sports_count} markets")
        print(f"   🏛️  Political: {political_count} markets")
        print(f"   💰 Economic: {economic_count} markets")
        print(f"   ❓ Other: {other_count} markets")
        
        if political_examples:
            print(f"\n🏛️ POLITICAL MARKET EXAMPLES:")
            for example in political_examples:
                print(f"   • {example}")
        
        if economic_examples:
            print(f"\n💰 ECONOMIC MARKET EXAMPLES:")
            for example in economic_examples:
                print(f"   • {example}")
        
        if sports_examples:
            print(f"\n🏈 SPORTS MARKET EXAMPLES:")
            for example in sports_examples:
                print(f"   • {example}")
        
        if other_examples:
            print(f"\n❓ OTHER MARKET EXAMPLES:")
            for example in other_examples:
                print(f"   • {example}")
        
        # Conclusion
        if political_count > 0 or economic_count > 0:
            print(f"\n✅ FOUND {political_count + economic_count} POLITICAL/ECONOMIC MARKETS!")
            return True
        else:
            print(f"\n❌ NO POLITICAL/ECONOMIC MARKETS FOUND")
            print(f"   All {len(markets)} markets are sports betting")
            return False
            
    except Exception as e:
        print(f"❌ Error checking market types: {e}")
        return False

if __name__ == "__main__":
    has_political_economic = check_market_types()
    
    print("\n" + "=" * 50)
    if has_political_economic:
        print("🎉 POLITICAL/ECONOMIC MARKETS AVAILABLE!")
    else:
        print("❌ ONLY SPORTS MARKETS AVAILABLE - USER REJECTED SPORTS")
    print("=" * 50)
