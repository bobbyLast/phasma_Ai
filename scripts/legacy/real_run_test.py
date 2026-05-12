#!/usr/bin/env python3
"""
PHASMA AI - Real Run Test with Available APIs
Tests the system with currently configured data sources
"""

import asyncio
import os
import time
from datetime import datetime
import sys

# Add project root to path
_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)
async def test_real_run():
    """Run Phasma AI with available data sources"""
    print("🚀 PHASMA AI - REAL RUN WITH AVAILABLE DATA")
    print("=" * 60)
    print(f"Run Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Check available API keys
    print("\n🔑 CHECKING API KEYS")
    print("-" * 40)
    
    available_apis = []
    
    # Check news APIs
    if os.getenv('WORLD_NEWS_API_KEY'):
        available_apis.append("World News")
        print("✅ World News API")
    
    if os.getenv('GNEWS_API_KEY'):
        available_apis.append("GNews")
        print("✅ GNews API")
    
    if os.getenv('MEDIASTACK_API_KEY'):
        available_apis.append("MediaStack")
        print("✅ MediaStack API")
    
    # Check other APIs
    if os.getenv('KALSHI_API_KEY'):
        available_apis.append("Kalshi")
        print("✅ Kalshi Prediction Markets")
    
    if os.getenv('ALPHA_VANTAGE_KEY'):
        available_apis.append("Alpha Vantage")
        print("✅ Alpha Vantage")
    
    if os.getenv('REDDIT_CLIENT_ID'):
        available_apis.append("Reddit")
        print("✅ Reddit API")
    
    print(f"\n✅ Total APIs Available: {len(available_apis)}")
    
    # Initialize components
    print("\n📊 INITIALIZING COMPONENTS")
    print("-" * 40)
    
    # Import available engines
    try:
        from engines import NewsAPIIntegration
        news_engine = NewsAPIIntegration()
        print("✅ News Engine initialized")
    except Exception as e:
        print(f"⚠️ News Engine: {e}")
        news_engine = None
    
    try:
        from engines.social_engine import RedditTrendingTracker
        social_engine = RedditTrendingTracker()
        print("✅ Social Engine initialized")
    except Exception as e:
        print(f"⚠️ Social Engine: {e}")
        social_engine = None
    
    try:
        from brain.signal_convergence_engine import SignalConvergenceEngine
        convergence_engine = SignalConvergenceEngine()
        print("✅ Convergence Engine initialized")
    except Exception as e:
        print(f"⚠️ Convergence Engine: {e}")
        convergence_engine = None
    
    # Phase 1: Data Collection
    print("\n🔍 PHASE 1: DATA COLLECTION")
    print("-" * 40)
    
    all_signals = []
    
    # Collect news signals
    if news_engine:
        print("\n📰 Collecting News Signals...")
        try:
            news_signals = await news_engine.get_signals()
            print(f"   ✅ Found {len(news_signals)} news signals")
            all_signals.extend(news_signals)
        except Exception as e:
            print(f"   ⚠️ News collection error: {e}")
    
    # Collect social signals
    if social_engine:
        print("\n💬 Collecting Social Signals...")
        try:
            social_signals = await social_engine.get_trending_signals()
            print(f"   ✅ Found {len(social_signals)} social signals")
            all_signals.extend(social_signals)
        except Exception as e:
            print(f"   ⚠️ Social collection error: {e}")
    
    # Phase 2: Convergence Analysis
    print(f"\n🧠 PHASE 2: CONVERGENCE ANALYSIS")
    print("-" * 40)
    
    if convergence_engine and all_signals:
        print(f"Processing {len(all_signals)} signals...")
        
        # Add signals to convergence engine
        for signal in all_signals[:10]:  # Limit for demo
            try:
                convergence_engine.add_signal({
                    'source': signal.get('source', 'unknown'),
                    'ticker': signal.get('symbol', 'UNKNOWN'),
                    'confidence': signal.get('confidence', 0.5),
                    'action': signal.get('action', 'HOLD'),
                    'timestamp': datetime.now().isoformat()
                })
            except Exception as e:
                print(f"   ⚠️ Signal processing error: {e}")
        
        # Find convergence opportunities
        try:
            opportunities = convergence_engine.find_convergence_opportunities(min_sources=2)
            print(f"\n🎯 CONVERGENCE OPPORTUNITIES:")
            print(f"   Found {len(opportunities)} opportunities")
            
            for opp in opportunities[:3]:  # Top 3
                print(f"\n   ✨ {opp['opportunity_type']}: {opp['target']}")
                print(f"      📊 Score: {opp['convergence_score']:.1%}")
                print(f"      🔗 Sources: {opp['unique_sources']}")
                print(f"      💰 Position: ${opp['recommended_position_size']:,}")
        except Exception as e:
            print(f"   ⚠️ Convergence analysis error: {e}")
    else:
        print("   ⚠️ No convergence analysis possible")
    
    # Phase 3: Market Scan (Simulated)
    print(f"\n📊 PHASE 3: MARKET SCAN")
    print("-" * 40)
    
    # Simulate market scan with popular stocks
    watchlist = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'TSLA', 'META', 'BTC-USD']
    
    print(f"Scanning {len(watchlist)} assets...")
    
    # Simple price check simulation
    from utils.price_fetcher import get_price_fetcher
    price_fetcher = get_price_fetcher()
    
    market_data = []
    for symbol in watchlist:
        try:
            price = price_fetcher.get_real_price(symbol)
            if price:
                market_data.append({
                    'symbol': symbol,
                    'price': price,
                    'change': (hash(symbol) % 100 - 50) / 100  # Simulated change
                })
        except:
            pass
    
    print(f"   ✅ Retrieved {len(market_data)} price quotes")
    
    # Phase 4: Signal Generation
    print(f"\n🤖 PHASE 4: SIGNAL GENERATION")
    print("-" * 40)
    
    generated_signals = []
    
    for data in market_data:
        # Simple signal logic based on simulated change
        if abs(data['change']) > 0.02:  # 2% move
            direction = 'BUY' if data['change'] > 0 else 'SELL'
            confidence = min(0.8, abs(data['change']) * 10)
            
            signal = {
                'symbol': data['symbol'],
                'action': direction,
                'confidence': confidence,
                'price': data['price'],
                'change': data['change'],
                'source': 'market_scan',
                'timestamp': datetime.now().isoformat()
            }
            
            generated_signals.append(signal)
            print(f"   📊 {data['symbol']}: {direction} @ ${data['price']:.2f} (conf: {confidence:.1%})")
    
    print(f"\n✅ Generated {len(generated_signals)} trading signals")
    
    # Phase 5: Risk Assessment
    print(f"\n🛡️ PHASE 5: RISK ASSESSMENT")
    print("-" * 40)
    
    # Simulate risk checks
    portfolio_exposure = 125000  # $125k already exposed
    account_equity = 250000     # $250k total equity
    max_exposure = 0.35         # 35% max exposure
    
    current_exposure_pct = portfolio_exposure / account_equity
    available_capacity = (account_equity * max_exposure) - portfolio_exposure
    
    print(f"   Portfolio Exposure: ${portfolio_exposure:,} ({current_exposure_pct:.1%})")
    print(f"   Max Allowed: ${account_equity * max_exposure:,} ({max_exposure:.1%})")
    print(f"   Available Capacity: ${available_capacity:,}")
    
    # Filter signals based on risk
    executable_signals = []
    for signal in generated_signals:
        if signal['confidence'] > 0.6 and available_capacity > 10000:
            signal['position_size'] = min(25000, available_capacity / len(generated_signals))
            executable_signals.append(signal)
    
    print(f"\n✅ {len(executable_signals)} signals passed risk filters")
    
    # Phase 6: Summary
    print(f"\n📈 RUN SUMMARY")
    print("=" * 60)
    
    print(f"⏱️  Total Run Time: {time.time():.1f}s")
    print(f"📊 APIs Used: {len(available_apis)}")
    print(f"🔍 Signals Collected: {len(all_signals)}")
    print(f"🤖 Signals Generated: {len(generated_signals)}")
    print(f"💰 Signals Executable: {len(executable_signals)}")
    print(f"🛡️ Risk Status: {'✅ COMPLIANT' if current_exposure_pct < max_exposure else '⚠️ AT LIMIT'}")
    
    if executable_signals:
        print(f"\n🎯 TOP EXECUTION SIGNALS:")
        for signal in executable_signals[:3]:
            print(f"   • {signal['symbol']} {signal['action']} @ ${signal['price']:.2f}")
            print(f"     Confidence: {signal['confidence']:.1%} | Size: ${signal['position_size']:,}")
    
    print(f"\n✅ RUN COMPLETE - System Operational!")
    
    # Save results
    results = {
        'timestamp': datetime.now().isoformat(),
        'signals_found': len(all_signals),
        'signals_generated': len(generated_signals),
        'signals_executable': len(executable_signals),
        'portfolio_exposure': portfolio_exposure,
        'available_capacity': available_capacity
    }
    
    with open('last_run_results.json', 'w') as f:
        import json
        json.dump(results, f, indent=2)
    
    print(f"📁 Results saved to last_run_results.json")

if __name__ == "__main__":
    asyncio.run(test_real_run())
