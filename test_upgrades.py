#!/usr/bin/env python3
"""
Quick test script for the new upgrades
"""

import sys
sys.path.append('.')

from engines.enhanced_confluence_scorer import EnhancedConfluenceScorer

def test_confluence_scorer():
    """Test the enhanced confluence scorer"""
    
    print("🎯 Testing Enhanced Confluence Scorer")
    print("=" * 50)
    
    scorer = EnhancedConfluenceScorer()
    
    # Test opportunity
    opportunity = {
        'symbol': 'TEST',
        'action': 'BUY',
        'entry_price': 10.50,
        'target_price': 15.00,
        'patterns': ['breakout', 'oversold'],
        'news_items': [{'title': 'Test news'}],
        'confidence': 0.75
    }
    
    # Score it
    context = {
        'macro_regime': 'RISK_ON',
        'vix': 'LOW'
    }
    
    scored = scorer.score_opportunity(opportunity, context)
    
    print(f"Symbol: {scored['symbol']}")
    print(f"Confluence Score: {scored['confluence_score']:.0f}/100")
    print(f"Breakdown:")
    for key, value in scored['confluence_breakdown'].items():
        print(f"  {key}: {value:.0%}")
    
    # Test filtering
    opportunities = [scored]
    high_conviction = scorer.filter_high_conviction(opportunities, 70)
    
    print(f"\nHigh Conviction (70+): {len(high_conviction)}")
    
    return len(high_conviction) > 0

def test_risk_validation():
    """Test risk validation logic"""
    
    print("\n🛡️ Testing Risk-First Validation")
    print("=" * 50)
    
    # Mock signal
    signal = {
        'symbol': 'TEST',
        'position_size': 0.02,
        'sector': 'TECHNOLOGY'
    }
    
    # Simulate risk checks
    vix = 35  # High volatility
    
    if vix > 30:
        signal['position_size'] *= 0.5
        signal['risk_warning'] = "High volatility - position size reduced"
        print(f"✅ VIX at {vix} - Position size reduced to {signal['position_size']:.1%}")
    
    # Check sector correlation
    open_positions = [
        {'sector': 'TECHNOLOGY'},
        {'sector': 'TECHNOLOGY'},
        {'sector': 'TECHNOLOGY'}
    ]
    
    same_sector_count = sum(1 for p in open_positions if p.get('sector') == signal['sector'])
    if same_sector_count >= 3:
        print(f"❌ Rejected: Too many positions in {signal['sector']} sector")
        return False
    
    print("✅ Risk validation passed")
    return True

def main():
    """Run all tests"""
    
    print("🚀 Testing Upgrades - No Data Loss!\n")
    
    # Test 1: Confluence Scorer
    test1 = test_confluence_scorer()
    
    # Test 2: Risk Validation
    test2 = test_risk_validation()
    
    # Summary
    print("\n📊 Test Results:")
    print("=" * 50)
    print(f"Confluence Scorer: {'✅ PASS' if test1 else '❌ FAIL'}")
    print(f"Risk Validation: {'✅ PASS' if test2 else '❌ FAIL'}")
    
    if test1 and test2:
        print("\n✅ All upgrades working correctly!")
        print("📈 Ready to enhance trading signals")
    else:
        print("\n⚠️ Some tests failed - check implementation")

if __name__ == "__main__":
    main()
