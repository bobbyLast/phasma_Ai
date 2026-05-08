"""Test Kalshi AI Playbook with adjusted thresholds"""

from core.config import PhasmaConfig
from engines.kalshi_ai_playbook import KalshiAIPlaybook
from engines.kalshi_ai_playbook import KalshiAIPlaybook

class AdjustedKalshiPlaybook(KalshiAIPlaybook):
    """AI Playbook with adjusted thresholds for testing"""
    
    def __init__(self, config):
        super().__init__(config)
        
        # Adjusted thresholds based on analysis
        self.MARKET_CONFIGS = {
            "WEATHER": {
                "min_liq_score": 1,  # Lowered from 2
                "min_volume": 50,    # Lowered from 500
                "price_range": (0.10, 0.90),  # Expanded from 0.35-0.60
                "entry_window_hrs": (168, 12),  # Expanded: 7 days to 12 hours
                "base_edge": 0.05    # Lowered from 0.10
            },
            "ECON": {
                "min_liq_score": 1,  # Lowered from 2
                "min_volume": 100,   # Lowered from 1000
                "price_range": (0.10, 0.90),  # Expanded
                "entry_window_hrs": (168, 12),  # Expanded
                "base_edge": 0.05    # Lowered from 0.12
            },
            "FED": {
                "min_liq_score": 1,  # Lowered from 3
                "min_volume": 100,   # Lowered from 2000
                "price_range": (0.10, 0.90),  # Expanded
                "entry_window_hrs": (168, 12),  # Expanded
                "base_edge": 0.05    # Lowered from 0.10
            }
        }
    
    def score_liquidity(self, market, orderbook=None):
        """More lenient liquidity scoring"""
        score = 0
        
        # Check 24h volume - lower threshold
        volume_24h = market.get('volume_24h', 0)
        if volume_24h >= 50:  # Lowered from 500
            score += 1
        
        # Check spread - more lenient
        yes_bid = market.get('yes_bid', 0) / 100
        yes_ask = market.get('yes_ask', 0) / 100
        spread_cents = (yes_ask - yes_bid) * 100
        
        if spread_cents <= 0.10:  # Increased from 3 cents
            score += 1
        
        # Check total volume - lower threshold
        total_volume = market.get('volume', 0)
        if total_volume >= 50:  # Lowered from 1000
            score += 1
        
        return score

def test_adjusted_playbook():
    config = PhasmaConfig()
    playbook = AdjustedKalshiPlaybook(config)
    
    print("🔧 Testing ADJUSTED Kalshi AI Playbook")
    print("=" * 60)
    print("Adjusted Thresholds:")
    print("- Liquidity: 1/3 (was 2-3)")
    print("- Volume: 50-100 (was 500-2000)")
    print("- Price: $0.10-$0.90 (was $0.35-$0.60)")
    print("- Time: 7d-12h (was 48-24h)")
    print("- EV: 5% (was 10-18%)")
    print("=" * 60)
    
    # Find opportunities
    opportunities = playbook.find_opportunities()
    
    if opportunities:
        print(f"\n🎯 Found {len(opportunities)} opportunities with adjusted thresholds!")
        
        print(f"\n📊 Top Opportunities:")
        for i, opp in enumerate(opportunities[:5]):
            print(f"\n{i+1}. {opp['ticker']} ({opp['market_type']})")
            print(f"   Title: {opp['title'][:80]}...")
            print(f"   Signal: {opp['trade_signal']} @ ${opp['yes_price']:.2f}")
            print(f"   Model: {opp['model_probability']:.1%} | EV: {opp['ev']:+.1%}")
            print(f"   Required: {opp['required_edge']:.1%} | Confidence: {opp['confidence']:.1f}x")
            print(f"   Hours: {opp['hours_to_close']:.1f} | Liquidity: {opp['liquidity_score']}/3")
            print(f"   Volume: {opp['volume']:,} | Spread: {opp['spread_cents']:.1f}¢")
            print(f"   Rationale: {opp['rationale']}")
    else:
        print("\n💤 Still no opportunities - let's check why")
        
        # Debug first few markets
        print("\n🔍 Debugging first 5 markets:")
        series_list = playbook.discover_whitelisted_series()
        
        count = 0
        for series in series_list:
            if count >= 5:
                break
                
            markets_url = f"{playbook.base_url}/markets?series_ticker={series['ticker']}&status=open"
            markets_response = playbook.session.get(markets_url)
            markets = markets_response.json().get('markets', [])
            
            for market in markets[:1]:  # Just first market
                opp = playbook._analyze_market_debug(market, series['market_type'])
                if opp:
                    print(f"\n{count+1}. {opp['ticker']}")
                    print(f"   Price: ${opp['yes_price']:.2f} | EV: {opp['ev']:+.1%}")
                    print(f"   Failed: {opp['failure_reasons']}")
                    count += 1
                    break

if __name__ == "__main__":
    test_adjusted_playbook()
