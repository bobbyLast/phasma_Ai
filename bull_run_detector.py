"""
Bull Run Detector - Multi-Source Confirmation System
Finds REAL bull runs confirmed by multiple sources and sends to Kalshi
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, timedelta
import re
from typing import List, Dict, Tuple

class BullRunDetector:
    """Detects real bull runs confirmed by multiple sources"""
    
    def __init__(self, config):
        self.config = config
        self.price_threshold = 50.0
        
        # Import necessary modules
        from utils.price_fetcher import get_price_fetcher
        self.price_fetcher = get_price_fetcher()
        
        from engines.news_engine_integrated import IntegratedNewsSources
        self.news_sources = IntegratedNewsSources(config)
        
        # Real bull run indicators (not just hype)
        self.bull_run_indicators = {
            'volume_surge': [
                'unusual volume', 'volume spike', 'heavy volume', 
                'above average volume', 'volume explosion'
            ],
            'institutional_buying': [
                'institutional buying', 'insider buying', 'whale accumulation',
                'smart money buying', 'fund accumulation', 'ETF buying'
            ],
            'breakout_patterns': [
                'breakout', 'resistance broken', 'new high', '52-week high',
                'bullish breakout', 'ascending triangle', 'flag breakout'
            ],
            'catalyst_events': [
                'FDA approval', 'patent approved', 'contract won', 'partnership',
                'acquisition', 'buyout', 'merger', 'earnings beat', 'guidance raise'
            ],
            'sector_momentum': [
                'sector rally', 'industry surge', 'ETF inflow', 'sector rotation',
                'hot sector', 'trending sector'
            ],
            'technical_momentum': [
                'RSI strong', 'MACD bullish', 'golden cross', 'moving average',
                'momentum shift', 'trend reversal', 'bullish divergence'
            ]
        }
        
        # High-confidence sources
        self.high_confidence_sources = {
            'sec_filings': 3.0,  # SEC Form 4 insider buys
            'press_releases': 2.5,  # Company press releases
            'major_news': 2.0,  # Reuters, Bloomberg, WSJ
            'analyst_reports': 2.0,  # Analyst upgrades
            'institutional_reports': 2.5,  # Hedge fund reports
            'social_sentiment': 1.5,  # Twitter, Reddit sentiment
            'options_flow': 2.0,  # Unusual options activity
            'dark_pool': 1.5  # Dark pool activity
        }
        
        # Kalshi event mappings
        self.kalshi_mappings = {
            'stock_momentum': 'Will {symbol} be above ${strike} in {days} days?',
            'sector_momentum': 'Will {sector} ETF outperform?',
            'market_events': 'Market will be up on {date}?'
        }
    
    async def detect_bull_runs(self) -> List[Dict]:
        """Find real bull runs with multi-source confirmation"""
        
        print("=" * 80)
        print("🚀 BULL RUN DETECTOR - MULTI-SOURCE CONFIRMATION")
        print("=" * 80)
        print("Finding REAL bull runs confirmed by multiple sources...")
        print("=" * 80)
        
        # 1. Get all news from multiple sources
        print("\n📰 Fetching news from 20+ sources...")
        all_news = await self.news_sources.fetch_all_integrated_sources()
        print(f"   Total news items: {len(all_news)}")
        
        # 2. Analyze each stock for bull run signals
        print("\n🔍 Analyzing for bull run indicators...")
        stock_signals = {}
        
        for item in all_news:
            text = f"{item.get('title', '')} {item.get('summary', '')}".upper()
            symbol = self._extract_symbol(text)
            
            if not symbol:
                continue
            
            # Check for bull run indicators
            signals = self._analyze_bull_run_indicators(text)
            
            if not signals:
                continue
            
            # Get source confidence
            source_confidence = self._get_source_confidence(item.get('source', ''))
            
            if symbol not in stock_signals:
                stock_signals[symbol] = {
                    'total_score': 0,
                    'indicators': set(),
                    'sources': [],
                    'evidence': [],
                    'confirmation_count': 0
                }
            
            # Add signals
            for indicator_type, strength in signals.items():
                stock_signals[symbol]['indicators'].add(indicator_type)
                stock_signals[symbol]['total_score'] += strength * source_confidence
                stock_signals[symbol]['evidence'].append({
                    'type': indicator_type,
                    'strength': strength,
                    'source': item.get('source', ''),
                    'text': item.get('title', '')[:100] + '...',
                    'confidence': source_confidence
                })
            
            stock_signals[symbol]['sources'].append(item.get('source', ''))
            stock_signals[symbol]['confirmation_count'] = len(set(stock_signals[symbol]['sources']))
        
        print(f"   Found {len(stock_signals)} stocks with bull run signals")
        
        # 3. Filter by price and multi-source confirmation
        print("\n💰 Filtering for affordable stocks with multi-source confirmation...")
        confirmed_bull_runs = []
        
        for symbol, data in stock_signals.items():
            # Need at least 2 sources for confirmation
            if data['confirmation_count'] < 2:
                continue
            
            # Get current price
            price = self.price_fetcher.get_real_price(symbol)
            
            if not price:
                continue
            
            try:
                price = float(price)
            except:
                continue
            
            # Must be under $50
            if price > self.price_threshold:
                continue
            
            # Calculate final score
            final_score = data['total_score'] / data['confirmation_count']
            
            # Need minimum score
            if final_score < 5.0:
                continue
            
            confirmed_bull_runs.append({
                'symbol': symbol,
                'price': price,
                'score': final_score,
                'indicators': list(data['indicators']),
                'confirmation_count': data['confirmation_count'],
                'sources': list(set(data['sources'])),
                'evidence': data['evidence'][:5],  # Top 5 evidence
                'trade_type': self._determine_trade_type(data['indicators'])
            })
        
        # Sort by score
        confirmed_bull_runs.sort(key=lambda x: x['score'], reverse=True)
        
        print(f"   Found {len(confirmed_bull_runs)} confirmed bull runs under ${self.price_threshold}")
        
        # 4. Display results
        print("\n" + "=" * 80)
        print("🚀 CONFIRMED BULL RUNS - MULTI-SOURCE VERIFIED")
        print("=" * 80)
        
        if not confirmed_bull_runs:
            print("❌ No confirmed bull runs found")
            return []
        
        for i, bull_run in enumerate(confirmed_bull_runs[:10], 1):
            print(f"\n{i}. 🚀 {bull_run['symbol']} - ${bull_run['price']:.2f}")
            print(f"   Score: {bull_run['score']:.1f} | Confirmations: {bull_run['confirmation_count']}")
            print(f"   Indicators: {', '.join(bull_run['indicators'])}")
            print(f"   Sources: {', '.join(bull_run['sources'][:3])}")
            print(f"   Trade Type: {bull_run['trade_type']}")
            
            # Show top evidence
            if bull_run['evidence']:
                print(f"   Top Signal: {bull_run['evidence'][0]['text']}")
        
        return confirmed_bull_runs
    
    def _analyze_bull_run_indicators(self, text: str) -> Dict[str, float]:
        """Analyze text for bull run indicators"""
        found_indicators = {}
        
        for indicator_type, keywords in self.bull_run_indicators.items():
            score = 0
            for keyword in keywords:
                score += text.count(keyword.upper())
            
            if score > 0:
                found_indicators[indicator_type] = score
        
        return found_indicators
    
    def _get_source_confidence(self, source: str) -> float:
        """Get confidence score for news source"""
        source_lower = source.lower()
        
        if 'sec' in source_lower:
            return self.high_confidence_sources['sec_filings']
        elif 'press' in source_lower or 'pr' in source_lower:
            return self.high_confidence_sources['press_releases']
        elif any(x in source_lower for x in ['reuters', 'bloomberg', 'wsj', 'wall street']):
            return self.high_confidence_sources['major_news']
        elif 'analyst' in source_lower or 'upgrade' in source_lower:
            return self.high_confidence_sources['analyst_reports']
        elif 'institutional' in source_lower or 'fund' in source_lower:
            return self.high_confidence_sources['institutional_reports']
        elif any(x in source_lower for x in ['twitter', 'reddit', 'social']):
            return self.high_confidence_sources['social_sentiment']
        elif 'options' in source_lower or 'flow' in source_lower:
            return self.high_confidence_sources['options_flow']
        else:
            return 1.0  # Default confidence
    
    def _extract_symbol(self, text: str) -> str:
        """Extract stock symbols from text"""
        symbols = []
        
        # $SYMBOL pattern
        symbols.extend(re.findall(r'\$([A-Z]{1,5})\b', text))
        
        # Common stock names
        stock_names = {
            'TESLA': 'TSLA', 'APPLE': 'AAPL', 'AMAZON': 'AMZN', 'MICROSOFT': 'MSFT',
            'GOOGLE': 'GOOGL', 'META': 'META', 'NETFLIX': 'NFLX', 'NVIDIA': 'NVDA',
            'AMD': 'AMD', 'INTEL': 'INTC', 'DISNEY': 'DIS', 'NIKE': 'NKE',
            'COINBASE': 'COIN', 'ROBINHOOD': 'HOOD', 'PALANTIR': 'PLTR',
            'GAMESTOP': 'GME', 'AMC': 'AMC', 'BLACKBERRY': 'BB', 'NOKIA': 'NOK',
            'SILVER': 'SLV', 'GOLD': 'GOLD', 'BITCOIN': 'BTC', 'ETHEREUM': 'ETH'
        }
        
        for name, symbol in stock_names.items():
            if name in text:
                symbols.append(symbol)
        
        # Standalone caps (1-5 letters)
        candidates = re.findall(r'\b([A-Z]{1,5})\b', text)
        for candidate in candidates:
            if candidate not in ['A', 'I', 'OK', 'US', 'UK', 'CEO', 'CFO', 'COO', 'NYC', 'LA', 'TV', 'AI', 'IT', 'HR', 'PR']:
                symbols.append(candidate)
        
        # Return first valid symbol
        for symbol in symbols[:5]:
            if len(symbol) <= 5 and symbol.isalpha():
                return symbol
        
        return ''
    
    def _determine_trade_type(self, indicators: List[str]) -> str:
        """Determine best trade type based on indicators"""
        if 'breakout_patterns' in indicators:
            return 'MOMENTUM_CALL'
        elif 'catalyst_events' in indicators:
            return 'EVENT_DRIVEN_CALL'
        elif 'volume_surge' in indicators:
            return 'VOLUME_BREAKOUT_CALL'
        elif 'sector_momentum' in indicators:
            return 'SECTOR_ETF_CALL'
        else:
            return 'BULLISH_SWING_CALL'
    
    async def create_kalshi_events(self, bull_runs: List[Dict]) -> List[Dict]:
        """Create Kalshi trading events from bull runs"""
        print("\n🎯 CREATING KALSHI TRADING EVENTS")
        print("=" * 60)
        
        kalshi_events = []
        
        for bull_run in bull_runs:
            # Create Kalshi event based on trade type
            if bull_run['trade_type'] == 'MOMENTUM_CALL':
                event = {
                    'type': 'STOCK_PRICE',
                    'title': f"Will {bull_run['symbol']} be above ${bull_run['price'] * 1.2:.0f} in 7 days?",
                    'symbol': bull_run['symbol'],
                    'strike': round(bull_run['price'] * 1.2, 2),
                    'days': 7,
                    'confidence': min(bull_run['score'] / 10, 0.9),
                    'reasoning': f"Multi-source confirmed bull run with {bull_run['confirmation_count']} sources",
                    'indicators': bull_run['indicators']
                }
            elif bull_run['trade_type'] == 'EVENT_DRIVEN_CALL':
                event = {
                    'type': 'STOCK_PRICE',
                    'title': f"Will {bull_run['symbol']} be above ${bull_run['price'] * 1.3:.0f} in 14 days?",
                    'symbol': bull_run['symbol'],
                    'strike': round(bull_run['price'] * 1.3, 2),
                    'days': 14,
                    'confidence': min(bull_run['score'] / 10, 0.9),
                    'reasoning': f"Catalyst-driven bull run confirmed by {bull_run['confirmation_count']} sources",
                    'indicators': bull_run['indicators']
                }
            else:
                event = {
                    'type': 'STOCK_PRICE',
                    'title': f"Will {bull_run['symbol']} be above ${bull_run['price'] * 1.15:.0f} in 10 days?",
                    'symbol': bull_run['symbol'],
                    'strike': round(bull_run['price'] * 1.15, 2),
                    'days': 10,
                    'confidence': min(bull_run['score'] / 10, 0.9),
                    'reasoning': f"Bullish momentum confirmed by {bull_run['confirmation_count']} sources",
                    'indicators': bull_run['indicators']
                }
            
            kalshi_events.append(event)
            
            print(f"\n✅ Kalshi Event Created:")
            print(f"   {event['title']}")
            print(f"   Confidence: {event['confidence']:.1%}")
            print(f"   Reasoning: {event['reasoning']}")
        
        print(f"\n✅ Created {len(kalshi_events)} Kalshi trading events")
        return kalshi_events

async def main():
    """Main function to detect bull runs and create Kalshi events"""
    
    # Load config
    from config.secure_config import config
    
    # Initialize detector
    detector = BullRunDetector(config)
    
    # Find bull runs
    bull_runs = await detector.detect_bull_runs()
    
    if bull_runs:
        # Create Kalshi events
        kalshi_events = await detector.create_kalshi_events(bull_runs)
        
        # Save results
        import json
        results = {
            'timestamp': datetime.now().isoformat(),
            'bull_runs': bull_runs,
            'kalshi_events': kalshi_events
        }
        
        with open('bull_run_signals.json', 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\n💾 Results saved to bull_run_signals.json")
        print(f"📊 Ready to trade {len(kalshi_events)} events on Kalshi!")
        
        return kalshi_events
    else:
        print("\n⚠️ No bull runs detected - check again later")
        return []

if __name__ == "__main__":
    events = asyncio.run(main())
    
    if events:
        print(f"\n🎯 SUCCESS: Found {len(events)} tradeable bull run signals!")
    else:
        print("\n⏰ No signals at this time")
