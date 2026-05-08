"""Test to find closest opportunities to AI Playbook thresholds"""

from typing import Any, Dict, List, Optional
from core.config import PhasmaConfig
from engines.kalshi_ai_playbook import KalshiAIPlaybook
from datetime import datetime

def find_closest_opportunities():
    config = PhasmaConfig()
    playbook = KalshiAIPlaybook(config)
    
    print("🔍 Finding Closest Opportunities to Thresholds")
    print("=" * 60)
    
    # Get all whitelisted series
    series_list = playbook.discover_whitelisted_series()
    
    closest_opps = []
    
    for series in series_list[:50]:  # Check first 50 series to avoid timeout
        series_ticker = series.get('ticker')
        market_type = series.get('market_type', 'OTHER')
        
        if market_type not in playbook.MARKET_CONFIGS:
            continue
        
        # Get markets for this series
        markets_url = f"{playbook.base_url}/markets?series_ticker={series_ticker}&status=open"
        markets_response = playbook.session.get(markets_url)
        markets_response.raise_for_status()
        markets = markets_response.json().get('markets', [])
        
        for market in markets:
            analysis = playbook._analyze_market_debug(market, market_type)
            if analysis:
                closest_opps.append(analysis)
    
    # Sort by how close they are to passing
    closest_opps.sort(key=lambda x: x['closest_margin'], reverse=True)
    
    print(f"\n📊 Top 10 Closest Opportunities:")
    print("-" * 60)
    
    for i, opp in enumerate(closest_opps[:10]):
        print(f"\n{i+1}. {opp['ticker']} ({opp['market_type']})")
        print(f"   Title: {opp['title'][:80]}...")
        print(f"   Price: ${opp['yes_price']:.2f} | Model: {opp['model_probability']:.1%}")
        print(f"   EV: {opp['ev']:+.1%} | Required: {opp['required_edge']:.1%}")
        print(f"   Gap: {opp['ev_gap']:+.1%} | Hours: {opp['hours_to_close']:.1f}")
        print(f"   Liquidity: {opp['liquidity_score']}/3 | Volume: {opp['volume']}")
        print(f"   Failed by: {opp['failure_reasons']}")
    
    # Find patterns in failures
    print("\n" + "=" * 60)
    print("📈 Failure Analysis:")
    
    failure_counts = {}
    for opp in closest_opps:
        for reason in opp['failure_reasons']:
            failure_counts[reason] = failure_counts.get(reason, 0) + 1
    
    for reason, count in sorted(failure_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"   - {reason}: {count} markets")
    
    # Suggest threshold adjustments
    print("\n💡 Suggested Threshold Adjustments:")
    
    # Check EV gaps
    ev_gaps = [opp['ev_gap'] for opp in closest_opps if 'EV too low' in opp['failure_reasons']]
    if ev_gaps:
        avg_ev_gap = sum(ev_gaps) / len(ev_gaps)
        print(f"   - EV threshold: Lower from 10% to {max(0.05, avg_ev_gap):.1%}")
    
    # Check liquidity scores
    liq_scores = [opp['liquidity_score'] for opp in closest_opps if 'Liquidity too low' in opp['failure_reasons']]
    if liq_scores:
        max_liq = max(liq_scores)
        print(f"   - Liquidity: Accept score {max_liq} instead of 2")
    
    # Check time windows
    time_issues = [opp for opp in closest_opps if 'Outside entry window' in opp['failure_reasons']]
    if time_issues:
        print(f"   - Time window: {len(time_issues)} markets outside window")
    
    return closest_opps

# Add debug method to KalshiAIPlaybook
def _analyze_market_debug(self, market: Dict[str, Any], market_type: str) -> Optional[Dict[str, Any]]:
    """Debug version that shows why market failed"""
    config = self.MARKET_CONFIGS[market_type]
    
    ticker = market.get('ticker')
    title = market.get('title')
    
    # Calculate time to close
    close_time = market.get('close_time')
    if close_time:
        try:
            if 'Z' in close_time:
                close_dt = datetime.fromisoformat(close_time.replace('Z', '+00:00'))
            else:
                close_dt = datetime.fromisoformat(close_time)
            
            now = datetime.now()
            if close_dt.tzinfo is not None:
                now = datetime.now().astimezone()
            
            hours_to_close = (close_dt - now).total_seconds() / 3600
        except:
            hours_to_close = 999
    else:
        hours_to_close = 999
    
    # Score liquidity
    liq_score = self.score_liquidity(market)
    
    # Check price
    yes_price = market.get('yes_price', 0) / 100
    
    # Calculate model probability
    model_prob = self.model_probability(market, market_type)
    
    # Calculate EV
    ev = model_prob - yes_price
    
    # Calculate required edge
    spread_cents = (market.get('yes_ask', 0) - market.get('yes_bid', 0)) / 100
    required_edge = self.calculate_dynamic_edge(hours_to_close, spread_cents, liq_score, market_type)
    
    # Check what failed
    failure_reasons = []
    
    # Entry window check
    entry_min, entry_max = config['entry_window_hrs']
    if not (entry_max <= hours_to_close <= entry_min):
        failure_reasons.append(f"Outside entry window ({hours_to_close:.1f}h)")
    
    # Liquidity check
    if liq_score < config['min_liq_score']:
        failure_reasons.append(f"Liquidity too low ({liq_score}/{config['min_liq_score']})")
    
    # Price range check
    price_min, price_max = config['price_range']
    if not (price_min <= yes_price <= price_max):
        failure_reasons.append(f"Price out of range (${yes_price:.2f} not in ${price_min}-{price_max})")
    
    # EV check
    if ev < required_edge:
        failure_reasons.append(f"EV too low ({ev:+.1%} < {required_edge:.1%})")
    
    # Calculate how close to passing
    ev_gap = ev - required_edge
    liq_gap = liq_score - config['min_liq_score']
    time_gap = min(abs(hours_to_close - entry_min), abs(hours_to_close - entry_max))
    
    closest_margin = 0
    if ev_gap > -0.05:  # Within 5% EV
        closest_margin = max(closest_margin, ev_gap + 0.05)
    if liq_gap > -1:  # Within 1 liquidity point
        closest_margin = max(closest_margin, liq_gap + 0.1)
    if time_gap < 24:  # Within 24 hours of window
        closest_margin = max(closest_margin, (24 - time_gap) / 24)
    
    return {
        'ticker': ticker,
        'title': title,
        'market_type': market_type,
        'yes_price': yes_price,
        'model_probability': model_prob,
        'ev': ev,
        'required_edge': required_edge,
        'ev_gap': ev_gap,
        'hours_to_close': hours_to_close,
        'liquidity_score': liq_score,
        'volume': market.get('volume', 0),
        'failure_reasons': failure_reasons,
        'closest_margin': closest_margin
    }

# Monkey patch the debug method
from engines.kalshi_ai_playbook import KalshiAIPlaybook
KalshiAIPlaybook._analyze_market_debug = _analyze_market_debug

if __name__ == "__main__":
    find_closest_opportunities()
