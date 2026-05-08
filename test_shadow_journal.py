#!/usr/bin/env python3
"""
Test the shadow journal functionality
"""

from utils.shadow_journal import ShadowJournal
from datetime import datetime
import json

def test_shadow_journal():
    """Test the shadow journal"""
    print("📊 Testing Shadow Journal")
    print("=" * 50)
    
    # Create a test journal
    journal = ShadowJournal("logs/test_shadow_journal.json")
    
    # Simulate some trade signals and outcomes
    test_signals = [
        {
            'symbol': 'AAPL',
            'action': 'BUY',
            'confidence': 0.75,
            'source': 'insider',
            'position_size': 1000,
            'entry_price': 175.50
        },
        {
            'symbol': 'MSFT',
            'action': 'BUY',
            'confidence': 0.85,
            'source': 'news',
            'position_size': 1500,
            'entry_price': 380.25
        },
        {
            'symbol': 'GOOGL',
            'action': 'BUY',
            'confidence': 0.65,
            'source': 'social',
            'position_size': 800,
            'entry_price': 140.80
        },
        {
            'symbol': 'NVDA',
            'action': 'BUY',
            'confidence': 0.90,
            'source': 'convergence',
            'position_size': 2000,
            'entry_price': 785.40
        },
        {
            'symbol': 'TSLA',
            'action': 'BUY',
            'confidence': 0.55,
            'source': 'technical',
            'position_size': 500,
            'entry_price': 192.30
        }
    ]
    
    # Record signals
    print("\n1. Recording trade signals...")
    for signal in test_signals:
        journal.record_trade_signal(signal)
        print(f"   Recorded: {signal['symbol']} @ {signal['confidence']:.1%} confidence")
    
    # Simulate outcomes
    outcomes = [
        {'status': 'CLOSED', 'outcome': 'WIN', 'pnl': 150.00, 'pnl_percent': 0.085, 'hold_days': 3, 'exit_reason': 'TAKE_PROFIT'},
        {'status': 'CLOSED', 'outcome': 'WIN', 'pnl': 225.00, 'pnl_percent': 0.039, 'hold_days': 2, 'exit_reason': 'TAKE_PROFIT'},
        {'status': 'CLOSED', 'outcome': 'LOSS', 'pnl': -40.00, 'pnl_percent': -0.035, 'hold_days': 1, 'exit_reason': 'STOP_LOSS'},
        {'status': 'CLOSED', 'outcome': 'WIN', 'pnl': 400.00, 'pnl_percent': 0.025, 'hold_days': 5, 'exit_reason': 'TAKE_PROFIT'},
        {'status': 'CLOSED', 'outcome': 'LOSS', 'pnl': -25.00, 'pnl_percent': -0.05, 'hold_days': 1, 'exit_reason': 'STOP_LOSS'}
    ]
    
    # Record outcomes
    print("\n2. Recording trade outcomes...")
    for i, (signal, outcome) in enumerate(zip(test_signals, outcomes)):
        trade_id = f"{signal['symbol']}_{datetime.now().timestamp() - (5-i)}"
        journal.record_trade_outcome(trade_id, outcome)
        print(f"   Recorded: {signal['symbol']} {outcome['outcome']} ({outcome['pnl_percent']:+.1%})")
    
    # Analyze confidence performance
    print("\n3. Confidence Analysis:")
    print("-" * 50)
    analysis = journal.get_confidence_analysis(min_trades=1)
    
    for conf_range, stats in sorted(analysis.items()):
        print(f"{conf_range}%: {stats['win_rate']:.1%} win rate "
              f"({stats['wins']}/{stats['total_trades']}) "
              f"Avg P&L: {stats['avg_pnl_percent']:+.1%}")
    
    # Get optimal threshold
    optimal = journal.get_optimal_confidence_threshold()
    print(f"\n🎯 Optimal Confidence Threshold: {optimal:.1%}")
    
    # Source performance
    print("\n4. Source Performance:")
    print("-" * 50)
    source_perf = journal.get_source_performance()
    for source, stats in sorted(source_perf.items(), key=lambda x: x[1]['win_rate'], reverse=True):
        print(f"{source}: {stats['win_rate']:.1%} win rate "
              f"({stats['total_trades']} trades) "
              f"Avg conf: {stats['avg_confidence']:.1%}")
    
    # Test threshold adjustment
    print("\n5. Threshold Adjustment Test:")
    print("-" * 50)
    current_threshold = 0.70
    should_adjust, new_threshold, reason = journal.should_adjust_threshold(current_threshold)
    
    if should_adjust:
        print(f"⚠️  Should adjust from {current_threshold:.1%} to {new_threshold:.1%}")
        print(f"   Reason: {reason}")
    else:
        print(f"✅ Keep current threshold at {current_threshold:.1%}")
    
    # Learning insights
    print("\n6. Learning Insights:")
    print("-" * 50)
    insights = journal.get_learning_insights()
    for insight in insights:
        print(f"   • {insight}")
    
    # Generate report
    print("\n7. Full Report:")
    print("=" * 50)
    report = journal.generate_report()
    print(report)

if __name__ == "__main__":
    test_shadow_journal()
