"""
Integration of Three-Mind Framework into Phasma AI Trading System

This module connects the three-mind framework with the existing system
to generate high-conviction trading signals.
"""

import asyncio
from typing import Dict, List
from datetime import datetime

from brains.three_mind_framework import ThreeMindFramework, ThreeMindSignal
from core.config import PhasmaConfig


class ThreeMindIntegration:
    """Integrates three-mind framework with Phasma AI"""
    
    def __init__(self, config: PhasmaConfig):
        self.config = config
        self.framework = ThreeMindFramework(config.config)
        self.enabled = config.get('trading.three_mind_enabled', False)
        
    async def run_three_mind_analysis(self, market_data: Dict, 
                                     news_items: List[Dict]) -> List[ThreeMindSignal]:
        """Run complete three-mind analysis"""
        
        if not self.enabled:
            print("[THREE MIND] Framework disabled in config")
            return []
        
        print("\n🧠 THREE-MIND FRAMEWORK: Running Confluence Analysis")
        print("=" * 60)
        
        # Get symbols to analyze (from news, watchlist, etc.)
        symbols = self._get_symbols_to_analyze(news_items)
        
        # Get price data for all symbols
        price_data = await self._fetch_price_data(symbols)
        
        # Run three-mind analysis
        signals = await self.framework.scan_universe(symbols, price_data, market_data)
        
        # Log and display results
        for signal in signals:
            self.framework.log_signal(signal)
            self._display_signal(signal)
        
        print(f"\n✅ Generated {len(signals)} high-conviction signals")
        
        return signals
    
    def _get_symbols_to_analyze(self, news_items: List[Dict]) -> List[str]:
        """Extract symbols to analyze from various sources"""
        
        symbols = set()
        
        # From news
        for item in news_items:
            symbol = item.get('symbol', '')
            if symbol and symbol != 'UNKNOWN':
                symbols.add(symbol)
        
        # Add thematic stocks
        from brain.thematic_analysis_engine import ThematicAnalyzer
        analyzer = ThematicAnalyzer(self.config.config)
        themes = analyzer.analyze_news_themes(news_items)
        thematic_stocks = analyzer.map_themes_to_stocks(themes)
        
        for stock in thematic_stocks:
            symbols.add(stock['ticker'])
        
        # Add sector intelligence stocks
        # TODO: Integrate with sector intelligence
        
        # Add some liquid ETFs for diversification
        symbols.update(['SPY', 'QQQ', 'IWM', 'DIA'])
        
        return list(symbols)[:50]  # Limit to 50 symbols
    
    async def _fetch_price_data(self, symbols: List[str]) -> Dict:
        """Fetch price data for analysis"""
        
        price_data = {}
        
        # Use existing price fetcher
        from engines.price_fetcher import PriceFetcher
        fetcher = PriceFetcher(self.config)
        
        for symbol in symbols:
            try:
                # Get historical data for technical analysis
                hist = await fetcher.get_historical_data(symbol, period='2mo')
                
                if hist and len(hist) > 50:
                    price_data[symbol] = {
                        'closes': [bar['close'] for bar in hist],
                        'highs': [bar['high'] for bar in hist],
                        'lows': [bar['low'] for bar in hist],
                        'volumes': [bar['volume'] for bar in hist]
                    }
                    
            except Exception as e:
                print(f"[THREE MIND] Error fetching data for {symbol}: {e}")
        
        return price_data
    
    def _display_signal(self, signal: ThreeMindSignal):
        """Display three-mind signal"""
        
        print(f"\n🎯 THREE-MIND SIGNAL: {signal.symbol}")
        print(f"   Action: {signal.action}")
        print(f"   Confluence Score: {signal.confluence_score:.0f}/100")
        print(f"   Entry: ${signal.trade_plan.entry_price:.2f}")
        print(f"   Stop: ${signal.trade_plan.stop_loss:.2f}")
        print(f"   Target: ${signal.trade_plan.target_price:.2f}")
        print(f"   Position Size: {signal.trade_plan.position_size:.1%}")
        print(f"\n   Reasoning:")
        for line in signal.reasoning.split('\n'):
            if line.strip():
                print(f"   {line}")
    
    async def integrate_with_unified_brain(self, unified_results: Dict) -> Dict:
        """Integrate three-mind signals with unified brain results"""
        
        if not self.enabled:
            return unified_results
        
        # Get market data from unified results
        market_data = {
            'vix': unified_results.get('vix', 20),
            'spy_price': unified_results.get('spy_price', 400),
            'dxy': unified_results.get('dxy', 100),
            'rate_expectations': 0.5,  # TODO: Get from real data
            'growth_momentum': 0.5,   # TODO: Get from real data
        }
        
        # Get news items
        news_items = unified_results.get('news_items', [])
        
        # Run three-mind analysis
        three_mind_signals = await self.run_three_mind_analysis(market_data, news_items)
        
        # Add to unified results
        unified_results['three_mind_signals'] = [s.to_dict() for s in three_mind_signals]
        unified_results['three_mind_count'] = len(three_mind_signals)
        
        # If we have high-conviction signals, promote them
        if three_mind_signals:
            best_signal = max(three_mind_signals, key=lambda x: x.confluence_score)
            if best_signal.confluence_score > 80:
                print(f"\n🚀 HIGH-CONVICTION ALERT: {best_signal.symbol} at {best_signal.confluence_score:.0f}/100")
                # Add to top opportunities
                if 'opportunities' not in unified_results:
                    unified_results['opportunities'] = []
                
                unified_results['opportunities'].insert(0, {
                    'symbol': best_signal.symbol,
                    'confidence': best_signal.confluence_score / 100,
                    'action': best_signal.action,
                    'source': 'THREE_MIND_CONFLUENCE',
                    'entry_price': best_signal.trade_plan.entry_price,
                    'target_price': best_signal.trade_plan.target_price,
                    'stop_loss': best_signal.trade_plan.stop_loss,
                    'reasoning': best_signal.reasoning
                })
        
        return unified_results
