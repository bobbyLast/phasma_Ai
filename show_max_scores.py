#!/usr/bin/env python3
"""
Show maximum confluence scores
"""

import sys
sys.path.append('.')

from engines.enhanced_confluence_scorer import EnhancedConfluenceScorer

def show_max_scores():
    """Show what gets perfect scores"""
    
    scorer = EnhancedConfluenceScorer()
    
    print("🎯 MAXIMUM CONFLUENCE SCORES")
    print("=" * 50)
    
    # Perfect opportunity
    perfect_opp = {
        'symbol': 'PERFECT',
        'action': 'BUY',
        'entry_price': 8.50,      # Under $10 (penny stock bonus)
        'target_price': 25.00,    # 194% gain potential
        'patterns': ['breakout', 'divergence'],  # Strong patterns
        'news_items': [{'title': 'Major contract signed'}],  # News catalyst
        'confidence': 0.95
    }
    
    # Score in perfect conditions
    context = {'macro_regime': 'RISK_ON', 'vix': 'LOW'}
    scored = scorer.score_opportunity(perfect_opp, context)
    
    print(f"Symbol: {scored['symbol']}")
    print(f"Confluence Score: {scored['confluence_score']:.0f}/100")
    print(f"\nBreakdown:")
    for key, value in scored['confluence_breakdown'].items():
        print(f"  {key}: {value:.0%} (weight: {scorer.weights[key]:.0%})")
    
    print(f"\nCalculation:")
    total = 0
    for key, value in scored['confluence_breakdown'].items():
        weight = scorer.weights[key]
        contribution = value * weight * 100
        total += contribution
        print(f"  {key}: {value:.0%} × {weight:.0%} = {contribution:.0f}")
    print(f"  TOTAL: {total:.0f}/100")
    
    # Show what holds back scores
    print(f"\n📊 What Reduces Scores:")
    print("=" * 50)
    print("• Wrong action (BUY in RISK_OFF): -20% macro")
    print("• Price > $50: -30% value")
    print("• No patterns: -40% technical")
    print("• No news: -40% news catalyst")
    
    print(f"\n🏆 To Score 90+:")
    print("• Perfect macro alignment (BUY in RISK_ON)")
    print("• Price under $10 with 2x+ upside")
    print("• Strong patterns (breakout + divergence)")
    print("• Recent news catalyst")

if __name__ == "__main__":
    show_max_scores()
