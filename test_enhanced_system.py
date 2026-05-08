"""
============================================================
PHASMA AI - ENHANCED UNDERGROUND DISCOVERY WITH DATA INTEGRATION
============================================================
Integrating new data sources into the existing system
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime, timedelta
from engines.underground_stock_discovery import UndergroundStockDiscovery, UndergroundSignal
from engines.data_integration import NewsDataIntegrator, SignalDetector
import logging

logger = logging.getLogger(__name__)

class EnhancedUndergroundDiscovery(UndergroundStockDiscovery):
    """Enhanced discovery with integrated news data"""
    
    def __init__(self, config):
        super().__init__(config)
        self.news_integrator = NewsDataIntegrator()
        self.signal_detector = SignalDetector()
        self.enable_news_signals = config.get('enable_news_signals', True)
        self.news_signal_weight = config.get('news_signal_weight', 0.3)
    
    def scan_for_opportunities(self) -> list:
        """Enhanced scan with news signals"""
        logger.info("[ENHANCED] Starting enhanced opportunity scan...")
        
        # Get original signals
        original_signals = super().scan_for_opportunities()
        logger.info(f"[ENHANCED] Found {len(original_signals)} original signals")
        
        # Get news signals if enabled
        if self.enable_news_signals:
            news_signals = self._get_news_signals()
            logger.info(f"[ENHANCED] Found {len(news_signals)} news signals")
            
            # Combine signals
            all_signals = original_signals + news_signals
            
            # Deduplicate by ticker
            unique_signals = self._deduplicate_signals(all_signals)
            logger.info(f"[ENHANCED] Total unique signals: {len(unique_signals)}")
        else:
            unique_signals = original_signals
        
        # Apply enhanced filtering
        filtered_signals = self._enhanced_filter(unique_signals)
        logger.info(f"[ENHANCED] Signals after filtering: {len(filtered_signals)}")
        
        return filtered_signals
    
    def _get_news_signals(self) -> list:
        """Get signals from news data"""
        try:
            # Fetch all news data
            news_data = self.news_integrator.get_all_news(hours_back=24)
            
            # Detect signals
            news_signals_raw = self.signal_detector.find_signals(news_data)
            
            # Convert to UndergroundSignal format
            news_signals = []
            
            for signal_data in news_signals_raw:
                article = signal_data['article']
                
                # Extract ticker
                tickers = article.get('tickers', [])
                if not tickers:
                    continue  # Skip if no ticker found
                
                ticker = tickers[0]
                
                # Calculate strength
                base_strength = signal_data['confidence']
                sentiment_adjustment = signal_data['sentiment'] * 0.5
                final_strength = min(1.0, max(0.0, base_strength + sentiment_adjustment))
                
                # Only include if strength meets minimum
                if final_strength < 0.3:
                    continue
                
                # Create signal
                signal = UndergroundSignal(
                    ticker=ticker,
                    signal_type='news_sentiment',
                    strength=final_strength,
                    evidence=f"News: {article.get('title', '')[:100]}",
                    timestamp=datetime.now(),
                    sources=[article.get('source', 'news')],
                    liquidity_score=0.7,  # Default for news signals
                    dilution_risk='LOW'
                )
                
                news_signals.append(signal)
            
            return news_signals
            
        except Exception as e:
            logger.error(f"[ENHANCED] Error getting news signals: {e}")
            return []
    
    def _deduplicate_signals(self, signals: list) -> list:
        """Remove duplicate signals by ticker"""
        ticker_signals = {}
        
        for signal in signals:
            if signal.ticker not in ticker_signals:
                ticker_signals[signal.ticker] = []
            ticker_signals[signal.ticker].append(signal)
        
        # Keep the strongest signal for each ticker
        unique_signals = []
        for ticker, sig_list in ticker_signals.items():
            strongest = max(sig_list, key=lambda s: s.strength)
            unique_signals.append(strongest)
        
        return unique_signals
    
    def _enhanced_filter(self, signals: list) -> list:
        """Apply enhanced filtering logic"""
        filtered = []
        
        for signal in signals:
            # Market cap filter (if available)
            if hasattr(signal, 'market_cap'):
                if not (self.min_market_cap <= signal.market_cap <= self.max_market_cap):
                    continue
            
            # Strength filter
            if signal.strength < 0.3:
                continue
            
            # Additional news-specific filters
            if signal.signal_type == 'news_sentiment':
                # Only keep news signals with positive sentiment for buys
                if 'sell' in signal.evidence.lower():
                    continue
            
            filtered.append(signal)
        
        # Sort by strength
        filtered.sort(key=lambda s: s.strength, reverse=True)
        
        return filtered
    
    def get_enhanced_diagnostics(self) -> dict:
        """Get enhanced diagnostics including news data"""
        base_diagnostics = self.get_diagnostics()
        
        # Add news diagnostics
        news_diagnostics = {
            'news_integration': {
                'enabled': self.enable_news_signals,
                'weight': self.news_signal_weight,
                'last_fetch': datetime.now().isoformat()
            }
        }
        
        # Test news APIs
        api_status = {}
        try:
            world_news = self.news_integrator.fetch_world_news()
            api_status['world_news'] = 'active'
        except:
            api_status['world_news'] = 'error'
        
        try:
            gnews = self.news_integrator.fetch_gnews()
            api_status['gnews'] = 'active'
        except:
            api_status['gnews'] = 'error'
        
        news_diagnostics['api_status'] = api_status
        
        # Merge with base diagnostics
        base_diagnostics.update(news_diagnostics)
        
        return base_diagnostics

def test_enhanced_system():
    """Test the enhanced system"""
    print("=" * 80)
    print("🚀 PHASMA AI - ENHANCED SYSTEM TEST")
    print("=" * 80)
    
    # Configuration
    config = {
        'underground_discovery': {
            'strategy': 'penny_moonshot',
            'min_market_cap': 10_000_000,
            'max_market_cap': 500_000_000,
            'min_adv': 50_000
        },
        'enable_news_signals': True,
        'news_signal_weight': 0.3
    }
    
    # Initialize enhanced discovery
    discovery = EnhancedUndergroundDiscovery(config)
    
    print("\n1️⃣ GETTING ENHANCED DIAGNOSTICS...")
    print("-" * 40)
    
    diagnostics = discovery.get_enhanced_diagnostics()
    
    print("   System Status:")
    print(f"      • News Integration: {'✅ Enabled' if diagnostics['news_integration']['enabled'] else '❌ Disabled'}")
    print(f"      • News Weight: {diagnostics['news_integration']['weight']}")
    print(f"      • Last Fetch: {diagnostics['news_integration']['last_fetch']}")
    
    print("\n   API Status:")
    for api, status in diagnostics['api_status'].items():
        icon = "✅" if status == 'active' else "❌"
        print(f"      • {api}: {icon} {status}")
    
    print("\n2️⃣ RUNNING ENHANCED SCAN...")
    print("-" * 40)
    
    signals = discovery.scan_for_opportunities()
    
    print(f"\n📊 Results:")
    print(f"   • Total Signals: {len(signals)}")
    
    if signals:
        print("\n   Top 5 Signals:")
        for i, signal in enumerate(signals[:5], 1):
            print(f"\n   {i}. {signal.ticker}")
            print(f"      Type: {signal.signal_type}")
            print(f"      Strength: {signal.strength:.2f}")
            print(f"      Evidence: {signal.evidence[:80]}...")
            print(f"      Sources: {', '.join(signal.sources)}")
    
    print("\n3️⃣ PERFORMANCE COMPARISON...")
    print("-" * 40)
    
    # Run without news for comparison
    discovery.enable_news_signals = False
    signals_no_news = discovery.scan_for_opportunities()
    
    print(f"   Without News: {len(signals_no_news)} signals")
    print(f"   With News: {len(signals)} signals")
    print(f"   Improvement: {len(signals) - len(signals_no_news)} additional signals")
    
    # Calculate improvement percentage
    if len(signals_no_news) > 0:
        improvement_pct = ((len(signals) - len(signals_no_news)) / len(signals_no_news)) * 100
        print(f"   Improvement: {improvement_pct:.1f}% increase")
    
    print("\n4️⃣ FINAL SCORE...")
    print("-" * 40)
    
    # Calculate score
    score = min(100, len(signals) * 10)
    
    if score >= 80:
        print(f"   🏆 EXCELLENT: {score:.1f}/100")
    elif score >= 60:
        print(f"   ✅ GOOD: {score:.1f}/100")
    elif score >= 40:
        print(f"   ⚠️  ACCEPTABLE: {score:.1f}/100")
    else:
        print(f"   ❌ NEEDS WORK: {score:.1f}/100")
    
    return {
        'signals': signals,
        'diagnostics': diagnostics,
        'score': score
    }

if __name__ == "__main__":
    # Run test
    result = test_enhanced_system()
    
    # Save results
    import json
    with open('enhanced_system_results.json', 'w') as f:
        json.dump(result, f, indent=2, default=str)
    
    print(f"\n📄 Results saved to: enhanced_system_results.json")
