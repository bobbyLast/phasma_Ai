"""
============================================================
PHASMA AI - SYSTEM PERFORMANCE TEST
============================================================
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime
from engines.underground_stock_discovery import UndergroundStockDiscovery
import json

def test_system_performance():
    """Test the current system performance"""
    
    print("=" * 80)
    print("🚀 PHASMA AI - SYSTEM PERFORMANCE TEST")
    print("=" * 80)
    print(f"Test started: {datetime.now()}")
    print()
    
    # 1. Initialize discovery engine
    print("1️⃣ INITIALIZING DISCOVERY ENGINE...")
    print("-" * 40)
    
    config = {
        'underground_discovery': {
            'strategy': 'penny_moonshot',
            'min_market_cap': 10_000_000,
            'max_market_cap': 500_000_000,
            'min_adv': 50_000
        }
    }
    
    discovery = UndergroundStockDiscovery(config['underground_discovery'])
    print("✅ Discovery engine initialized")
    print(f"   Strategy: {discovery.strategy}")
    print(f"   Market cap range: ${discovery.min_market_cap:,} - ${discovery.max_market_cap:,}")
    print(f"   Min ADV: ${discovery.min_adv:,}")
    print()
    
    # 2. Run signal detection
    print("2️⃣ RUNNING SIGNAL DETECTION...")
    print("-" * 40)
    
    signals = discovery.scan_for_opportunities()
    
    print(f"📊 Signals detected: {len(signals)}")
    
    if signals:
        for i, signal in enumerate(signals[:5], 1):
            print(f"   {i}. {signal.ticker}: {signal.signal_type}")
            print(f"      Strength: {signal.strength:.2f}")
            print(f"      Liquidity: {signal.liquidity_score:.2f}")
            print(f"      Evidence: {signal.evidence[:100]}...")
            print()
    else:
        print("   ⚠️  No signals detected in current scan")
        print("   (This is normal if no recent Form 4 filings meet criteria)")
        print()
    
    # 3. Get diagnostics
    print("3️⃣ SYSTEM DIAGNOSTICS...")
    print("-" * 40)
    
    diagnostics = discovery.get_diagnostics()
    
    print("📊 Current Diagnostics:")
    print(f"   Timestamp: {diagnostics['timestamp']}")
    print(f"   Strategy: {diagnostics['strategy']}")
    print()
    
    print("   Thresholds:")
    for key, value in diagnostics['thresholds'].items():
        print(f"      • {key}: {value}")
    print()
    
    print("   Filings:")
    for key, value in diagnostics['filings'].items():
        print(f"      • {key}: {value}")
    print()
    
    print("   Exclusions:")
    for key, value in diagnostics['exclusions'].items():
        print(f"      • {key}: {value}")
    print()
    
    print("   Signals:")
    for key, value in diagnostics['signals'].items():
        print(f"      • {key}: {value}")
    print()
    
    print("   Activity:")
    for key, value in diagnostics['activity'].items():
        if key != 'top_tickers':
            print(f"      • {key}: {value}")
    print()
    
    print("   Health:")
    for key, value in diagnostics['health'].items():
        print(f"      • {key}: {value}")
    print()
    
    # 4. Test aggregation audit
    print("4️⃣ AGGREGATION AUDIT...")
    print("-" * 40)
    
    if discovery.recent_transactions:
        # Test audit for first ticker
        sample_ticker = list(discovery.recent_transactions.keys())[0]
        audit = discovery.get_aggregation_audit(sample_ticker)
        
        print(f"📋 Audit for {sample_ticker}:")
        print(f"   Total transactions: {audit['total_transactions']}")
        print(f"   Weighted total: ${audit['weighted_total']:,.2f}")
        print(f"   Unique insiders: {audit['unique_insiders']}")
        print()
        
        print("   Transaction breakdown:")
        for trans_type in audit['transaction_breakdown']:
            details = audit['transaction_breakdown'][trans_type]
            print(f"      • {trans_type}: {details['count']} trades, ${details['total']:,.2f}")
        print()
        
        print("   Insider details:")
        for insider in audit['insider_details'][:3]:  # Show top 3
            print(f"      • {insider['name']}: {insider['transaction_count']} trades, ${insider['total']:,.2f}")
    else:
        print("   No recent transactions to audit")
    print()
    
    # 5. Test fallback sensitivity
    print("5️⃣ FALLBACK SENSITIVITY CHECK...")
    print("-" * 40)
    
    borderline = discovery.check_fallback_sensitivity()
    
    if borderline:
        print(f"⚠️  Fallback mode activated: {len(borderline)} candidates")
        for candidate in borderline[:3]:
            print(f"   • {candidate['ticker']}: {candidate['reason']}")
    else:
        print("✅ Normal mode active - no fallback needed")
    print()
    
    # 6. Performance summary
    print("6️⃣ PERFORMANCE SUMMARY...")
    print("-" * 40)
    
    # Calculate metrics
    total_filings = diagnostics['filings']['total']
    buy_ratio = float(diagnostics['filings']['buy_ratio'].rstrip('%')) / 100
    parser_errors = diagnostics['health']['parser_errors']
    error_rate = float(diagnostics['health']['error_rate'].rstrip('%')) / 100
    
    print("📈 Key Metrics:")
    print(f"   • Total filings processed: {total_filings}")
    print(f"   • Buy ratio: {buy_ratio:.1%}")
    print(f"   • Parser error rate: {error_rate:.2%}")
    print(f"   • Signals generated: {diagnostics['signals']['generated']}")
    print()
    
    # Score the system
    scores = {
        'data_quality': max(0, 100 - parser_errors * 100),  # Lower errors is better
        'signal_detection': min(100, len(signals) * 20),  # More signals is better
        'buy_ratio_quality': min(100, buy_ratio * 200),  # Higher buy ratio is better
        'system_stability': 100 if error_rate < 0.01 else 50  # Stable if <1% errors
    }
    
    overall_score = sum(scores.values()) / len(scores)
    
    print("📊 Component Scores:")
    for component, score in scores.items():
        status = "✅" if score >= 80 else "⚠️" if score >= 60 else "❌"
        print(f"   {status} {component.replace('_', ' ').title()}: {score:.1f}/100")
    
    print(f"\n🎯 OVERALL SYSTEM SCORE: {overall_score:.1f}/100")
    
    if overall_score >= 90:
        print("🏆 EXCELLENT - System performing at optimal level!")
    elif overall_score >= 80:
        print("✅ GOOD - System performing well")
    elif overall_score >= 70:
        print("⚠️  ACCEPTABLE - System needs some optimization")
    else:
        print("❌ NEEDS ATTENTION - System requires improvements")
    
    print()
    
    # 7. Recommendations
    print("7️⃣ RECOMMENDATIONS...")
    print("-" * 40)
    
    recommendations = []
    
    if buy_ratio < 0.1:
        recommendations.append("• Consider lowering signal thresholds to increase buy ratio")
    
    if len(signals) == 0:
        recommendations.append("• No signals detected - check market conditions or broaden criteria")
    
    if parser_errors > 0:
        recommendations.append("• Investigate parser errors - some filings may be malformed")
    
    if error_rate > 0.01:
        recommendations.append("• High error rate detected - review system health")
    
    if not recommendations:
        recommendations.append("• System is performing optimally - continue monitoring")
    
    for rec in recommendations:
        print(f"   {rec}")
    
    print()
    print("=" * 80)
    print(f"Test completed: {datetime.now()}")
    print("=" * 80)
    
    return {
        'overall_score': overall_score,
        'diagnostics': diagnostics,
        'scores': scores,
        'recommendations': recommendations
    }

if __name__ == "__main__":
    result = test_system_performance()
    
    # Save results
    with open('system_test_results.json', 'w') as f:
        json.dump(result, f, indent=2, default=str)
    
    print("\n📄 Results saved to: system_test_results.json")
