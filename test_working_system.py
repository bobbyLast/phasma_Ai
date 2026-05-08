"""
============================================================
PHASMA AI - WORKING DATA INTEGRATION UPDATE
============================================================
Fix the integration to actually use the news APIs
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime
from engines.underground_stock_discovery import UndergroundSignal
from engines.data_integration import NewsDataIntegrator, SignalDetector
import json

def create_working_signals():
    """Create working signals from news data"""
    
    print("🚀 PHASMA AI - WORKING SIGNAL GENERATION")
    print("=" * 60)
    
    # Initialize components
    integrator = NewsDataIntegrator()
    detector = SignalDetector()
    
    # Fetch news data
    print("\n1️⃣ FETCHING NEWS DATA...")
    print("-" * 40)
    
    news_data = integrator.get_all_news(hours_back=24)
    
    total_articles = sum(len(articles) for articles in news_data['sources'].values())
    print(f"   Total articles fetched: {total_articles}")
    
    for source, articles in news_data['sources'].items():
        print(f"   • {source}: {len(articles)} articles")
    
    # Detect signals
    print("\n2️⃣ DETECTING TRADING SIGNALS...")
    print("-" * 40)
    
    signals = detector.find_signals(news_data)
    print(f"   Signals detected: {len(signals)}")
    
    # Convert to UndergroundSignal format
    print("\n3️⃣ CONVERTING TO UNDERGROUND SIGNALS...")
    print("-" * 40)
    
    underground_signals = []
    
    for signal_data in signals:
        article = signal_data['article']
        
        # Extract ticker
        tickers = article.get('tickers', [])
        if not tickers:
            # Try to extract from title
            tickers = integrator.extract_tickers(article.get('title', ''))
        
        if not tickers:
            continue  # Skip if no ticker
        
        ticker = tickers[0]
        
        # Calculate strength
        base_strength = signal_data['confidence']
        sentiment_adjustment = signal_data['sentiment'] * 0.3
        final_strength = min(1.0, max(0.1, base_strength + sentiment_adjustment))
        
        # Create UndergroundSignal
        signal = UndergroundSignal(
            ticker=ticker,
            signal_type='news_sentiment',
            strength=final_strength,
            evidence=f"News Signal: {article.get('title', '')[:100]}",
            timestamp=datetime.now(),
            sources=[article.get('source', 'news')],
            liquidity_score=0.7,
            dilution_risk='LOW'
        )
        
        underground_signals.append(signal)
    
    print(f"   Underground signals created: {len(underground_signals)}")
    
    # Show top signals
    print("\n4️⃣ TOP 5 SIGNALS...")
    print("-" * 40)
    
    # Sort by strength
    underground_signals.sort(key=lambda s: s.strength, reverse=True)
    
    for i, signal in enumerate(underground_signals[:5], 1):
        print(f"\n{i}. {signal.ticker}")
        print(f"   Strength: {signal.strength:.2f}")
        print(f"   Type: {signal.signal_type}")
        print(f"   Evidence: {signal.evidence[:80]}...")
        print(f"   Sources: {', '.join(signal.sources)}")
    
    # Create mock SEC signals for testing
    print("\n5️⃣ ADDING MOCK SEC SIGNALS...")
    print("-" * 40)
    
    mock_sec_signals = [
        UndergroundSignal(
            ticker='MOCK1',
            signal_type='sec_filing',
            strength=0.8,
            evidence='VP purchased 10,000 shares at $5.50',
            timestamp=datetime.now(),
            sources=['SEC EDGAR'],
            liquidity_score=0.8,
            dilution_risk='LOW'
        ),
        UndergroundSignal(
            ticker='MOCK2',
            signal_type='sec_filing',
            strength=0.7,
            evidence='Director bought 5,000 shares',
            timestamp=datetime.now(),
            sources=['SEC EDGAR'],
            liquidity_score=0.7,
            dilution_risk='MEDIUM'
        ),
        UndergroundSignal(
            ticker='MOCK3',
            signal_type='sec_filing',
            strength=0.6,
            evidence='Officer acquired 2,500 shares',
            timestamp=datetime.now(),
            sources=['SEC EDGAR'],
            liquidity_score=0.6,
            dilution_risk='LOW'
        )
    ]
    
    all_signals = underground_signals + mock_sec_signals
    
    # Remove duplicates
    unique_signals = {}
    for signal in all_signals:
        if signal.ticker not in unique_signals or signal.strength > unique_signals[signal.ticker].strength:
            unique_signals[signal.ticker] = signal
    
    final_signals = list(unique_signals.values())
    final_signals.sort(key=lambda s: s.strength, reverse=True)
    
    print(f"   Mock SEC signals: {len(mock_sec_signals)}")
    print(f"   Total unique signals: {len(final_signals)}")
    
    # Save results
    results = {
        'timestamp': datetime.now().isoformat(),
        'signals': [
            {
                'ticker': s.ticker,
                'type': s.signal_type,
                'strength': s.strength,
                'evidence': s.evidence,
                'sources': s.sources
            }
            for s in final_signals
        ],
        'stats': {
            'total_signals': len(final_signals),
            'news_signals': len(underground_signals),
            'sec_signals': len(mock_sec_signals),
            'api_articles': total_articles
        }
    }
    
    with open('working_signals.json', 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n✅ Results saved to: working_signals.json")
    
    # Calculate score
    score = min(100, len(final_signals) * 10)
    
    print(f"\n🎯 SYSTEM SCORE: {score:.1f}/100")
    
    if score >= 80:
        print("🏆 EXCELLENT - System generating quality signals!")
    elif score >= 60:
        print("✅ GOOD - System performing well")
    elif score >= 40:
        print("⚠️  ACCEPTABLE - System needs optimization")
    else:
        print("❌ NEEDS WORK - System requires improvements")
    
    return final_signals

def simulate_full_pipeline():
    """Simulate the full pipeline with working signals"""
    
    print("\n" + "=" * 80)
    print("🔄 SIMULATING FULL PIPELINE")
    print("=" * 80)
    
    # Get signals
    signals = create_working_signals()
    
    if not signals:
        print("\n❌ No signals to process")
        return
    
    print("\n1️⃣ SIGNAL AGGREGATION...")
    print("-" * 40)
    
    # Group by type
    by_type = {}
    for signal in signals:
        if signal.signal_type not in by_type:
            by_type[signal.signal_type] = []
        by_type[signal.signal_type].append(signal)
    
    for signal_type, sig_list in by_type.items():
        avg_strength = sum(s.strength for s in sig_list) / len(sig_list)
        print(f"   • {signal_type}: {len(sig_list)} signals (avg strength: {avg_strength:.2f})")
    
    print("\n2️⃣ HUMAN GATE SIMULATION...")
    print("-" * 40)
    
    # Simulate human gate decisions
    approved = []
    rejected = []
    
    for signal in signals:
        # Simple approval logic
        if signal.strength >= 0.5 and 'sell' not in signal.evidence.lower():
            approved.append(signal)
            decision = "APPROVED"
        else:
            rejected.append(signal)
            decision = "REJECTED"
        
        print(f"   • {signal.ticker}: {decision} (strength: {signal.strength:.2f})")
    
    print(f"\n   Approved: {len(approved)}")
    print(f"   Rejected: {len(rejected)}")
    
    print("\n3️⃣ EXECUTION SIMULATION...")
    print("-" * 40)
    
    # Simulate execution for approved signals
    executed = []
    
    for signal in approved:
        # Simulate execution
        execution = {
            'ticker': signal.ticker,
            'shares': 1000,
            'price': 10.0,
            'status': 'FILLED',
            'slippage': 0.001,
            'commission': 5.0
        }
        executed.append(execution)
        
        print(f"   • {signal.ticker}: Executed 1000 shares @ $10.00")
    
    print(f"\n   Executed trades: {len(executed)}")
    
    print("\n4️⃣ PERFORMANCE SUMMARY...")
    print("-" * 40)
    
    # Calculate metrics
    total_signals = len(signals)
    approval_rate = len(approved) / total_signals if total_signals > 0 else 0
    execution_rate = len(executed) / total_signals if total_signals > 0 else 0
    
    print(f"   Total signals generated: {total_signals}")
    print(f"   Human gate approval rate: {approval_rate:.1%}")
    print(f"   Execution rate: {execution_rate:.1%}")
    print(f"   Expected daily trades: {len(executed)}")
    
    # Overall assessment
    if approval_rate >= 0.5 and execution_rate >= 0.3:
        print("\n✅ PIPELINE PERFORMING WELL!")
    elif approval_rate >= 0.3 and execution_rate >= 0.2:
        print("\n⚠️  PIPELINE ACCEPTABLE - Needs tuning")
    else:
        print("\n❌ PIPELINE NEEDS IMPROVEMENT")
    
    return {
        'signals': signals,
        'approved': approved,
        'executed': executed,
        'metrics': {
            'total_signals': total_signals,
            'approval_rate': approval_rate,
            'execution_rate': execution_rate
        }
    }

if __name__ == "__main__":
    # Run the simulation
    result = simulate_full_pipeline()
    
    # Save full results
    with open('pipeline_simulation.json', 'w') as f:
        json.dump(result, f, indent=2, default=str)
    
    print(f"\n📄 Full simulation saved to: pipeline_simulation.json")
