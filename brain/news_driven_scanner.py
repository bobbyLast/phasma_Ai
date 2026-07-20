"""
News-Driven Stock Scanner
Finds hyped stocks from news sources
"""

import asyncio
import sys
import os

_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _root not in sys.path:
    sys.path.insert(0, _root)

from datetime import datetime
import re
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from utils.cycle_data_context import CycleDataContext

class NewsDrivenScanner:
    """Scans news to find hot stocks from headlines"""
    
    def __init__(self, config, news_sources=None):
        self.config = config
        from utils.price_filter_config import apply_price_threshold
        apply_price_threshold(config, self)
        
        # Import price fetcher
        from utils.price_fetcher import get_price_fetcher
        self.price_fetcher = get_price_fetcher()
        
        if news_sources is None:
            from engines.news_engine_integrated import IntegratedNewsSources
            self.news_sources = IntegratedNewsSources(config)
        else:
            self.news_sources = news_sources
        
        # Keywords that indicate hype/good news
        self.hype_keywords = [
            'surge', 'soar', 'rocket', 'moon', 'explode', 'rally', 'jump',
            'breakout', 'spike', 'bullish', 'buy', 'upgrade', 'target',
            'partnership', 'deal', 'acquisition', 'buyout', 'merger',
            'earnings beat', 'profit', 'growth', 'boom', 'rally',
            'momentum', 'hot', 'trending', 'viral', 'buzz', 'hype'
        ]
        
        # Bearish keywords (for short opportunities)
        self.bearish_keywords = [
            'plunge', 'crash', 'drop', 'fall', 'slump', 'sell',
            'downgrade', 'cut', 'loss', 'miss', 'weak', 'bearish'
        ]
    
    async def scan_news_for_hot_stocks(self, cycle_context: Optional["CycleDataContext"] = None):
        """Scan all news to find hot stocks"""
        
        print("=" * 80)
        print("🔥 NEWS-DRIVEN STOCK SCANNER")
        print("=" * 80)
        print("Finding hyped stocks from news...")
        print("=" * 80)
        
        if cycle_context is not None:
            print("\n📰 Using cycle ingest snapshot (no re-fetch)...")
            all_news = cycle_context.ingested_news
        else:
            print("\n📰 Fetching news from 20 sources...")
            all_news = await self.news_sources.fetch_all_integrated_sources()
        print(f"   Total news items: {len(all_news)}")
        
        # 2. Extract symbols and analyze sentiment
        print("\n🔍 Analyzing news for stock mentions...")
        stock_mentions = {}
        prediction_mentions = {}
        
        for item in all_news:
            title = item.get('title', '').upper()
            summary = item.get('summary', '').upper()
            text = f"{title} {summary}"

            if item.get('prediction_market') and item.get('market_ticker'):
                ticker = str(item.get('market_ticker'))
                hype_score = self._calculate_hype_score(text)
                if ticker not in prediction_mentions:
                    prediction_mentions[ticker] = {
                        'market_ticker': ticker,
                        'prediction_market': item.get('prediction_market'),
                        'title': item.get('title', ''),
                        'mentions': 0,
                        'hype_score': 0,
                        'news_match_score': item.get('news_match_score', 0),
                        'symbol': item.get('symbol') or '',
                    }
                prediction_mentions[ticker]['mentions'] += 1
                prediction_mentions[ticker]['hype_score'] += hype_score['bullish']
                if item.get('news_match_score', 0) > prediction_mentions[ticker]['news_match_score']:
                    prediction_mentions[ticker]['news_match_score'] = item['news_match_score']
                if item.get('symbol'):
                    prediction_mentions[ticker]['symbol'] = item['symbol']
                continue
            
            # Extract symbols
            symbol = item.get('symbol') or self._extract_symbol(text)
            
            if not symbol:
                continue
            
            # Check if symbol is mentioned with hype keywords
            hype_score = self._calculate_hype_score(text)
            
            if symbol not in stock_mentions:
                stock_mentions[symbol] = {
                    'mentions': 0,
                    'hype_score': 0,
                    'bearish_score': 0,
                    'news_items': [],
                    'sentiment': 'neutral',
                    'price': None
                }

            if item.get('price') or item.get('current_price'):
                stock_mentions[symbol]['price'] = item.get('price') or item.get('current_price')
            
            stock_mentions[symbol]['mentions'] += 1
            stock_mentions[symbol]['hype_score'] += hype_score['bullish']
            stock_mentions[symbol]['bearish_score'] += hype_score['bearish']
            stock_mentions[symbol]['news_items'].append({
                'title': item.get('title', ''),
                'source': item.get('source', ''),
                'summary': item.get('summary', '')[:200] + '...'
            })
        
        print(f"   Found {len(stock_mentions)} stocks mentioned in news")
        news_aligned_preds = sum(
            1 for p in prediction_mentions.values()
            if p.get('symbol') or p.get('news_match_score', 0) > 0
        )
        print(
            f"   Found {len(prediction_mentions)} prediction markets "
            f"({news_aligned_preds} news-aligned)"
        )

        # Wire news-matched prediction intel into stock discovery universe
        for pdata in prediction_mentions.values():
            if float(pdata.get("news_match_score") or 0) <= 0:
                continue
            sym = str(pdata.get("symbol") or "").upper().strip()
            if not sym or len(sym) > 5 or not sym.isalpha():
                continue
            if sym not in stock_mentions:
                stock_mentions[sym] = {
                    "mentions": 0,
                    "hype_score": 0,
                    "bearish_score": 0,
                    "news_items": [],
                    "sentiment": "neutral",
                    "price": None,
                    "kalshi_intel": True,
                }
            stock_mentions[sym]["mentions"] += 1
            stock_mentions[sym]["hype_score"] += float(pdata.get("hype_score") or 0)
            stock_mentions[sym]["news_items"].append({
                "title": f"[Kalshi intel] {pdata.get('title', '')[:120]}",
                "source": pdata.get("prediction_market", "kalshi"),
                "summary": "Prediction-market flow mapped to equity research (not a trade signal).",
            })
        
        # 3. Filter by price and sort by hype
        cap_msg = f"(max ${self.price_threshold})" if self.price_filter_enabled else "(no price cap)"
        print(f"\n💰 Checking stock prices {cap_msg}...")
        affordable_stocks = []
        
        for symbol, data in stock_mentions.items():
            # Use prices already verified during news ingestion; avoid blocking live lookups here.
            price = data.get('price')
            
            if not price:
                continue
            
            try:
                price = float(price)
            except:
                continue
            
            if (
                self.price_filter_enabled
                and self.price_threshold is not None
                and price > self.price_threshold
            ):
                continue
            
            # Calculate sentiment
            if data['hype_score'] > data['bearish_score']:
                sentiment = 'bullish'
            elif data['bearish_score'] > data['hype_score']:
                sentiment = 'bearish'
            else:
                sentiment = 'neutral'
            
            stock_data = {
                'symbol': symbol,
                'price': price,
                'mentions': data['mentions'],
                'hype_score': data['hype_score'],
                'bearish_score': data['bearish_score'],
                'sentiment': sentiment,
                'news_items': data['news_items'][:3],  # Top 3 news items
                'total_score': data['hype_score'] - data['bearish_score']
            }
            
            affordable_stocks.append(stock_data)
        
        # Sort by hype score
        affordable_stocks.sort(key=lambda x: x['total_score'], reverse=True)
        
        cap = f"under ${self.price_threshold}" if self.price_filter_enabled else "found"
        print(f"   Found {len(affordable_stocks)} stocks {cap}")
        
        # 4. Display results
        print("\n" + "=" * 80)
        print("🚀 HOT STOCKS FROM NEWS")
        print("=" * 80)
        
        if not affordable_stocks:
            print("❌ No hot stocks found from news scan")
            return []
        
        # Show top 20
        top_stocks = affordable_stocks[:20]
        
        for i, stock in enumerate(top_stocks, 1):
            sentiment_icon = {
                'bullish': '🚀',
                'bearish': '📉',
                'neutral': '📊'
            }.get(stock['sentiment'], '📊')
            
            print(f"\n{i}. {sentiment_icon} {stock['symbol']} - ${stock['price']:.2f}")
            print(f"   Mentions: {stock['mentions']} | Hype Score: {stock['hype_score']} | Sentiment: {stock['sentiment'].upper()}")
            
            # Show top news
            if stock['news_items']:
                print(f"   Latest: {stock['news_items'][0]['title'][:80]}...")
        
        print(f"\n✅ Found {len(top_stocks)} hot stocks ready for analysis!")
        
        return top_stocks
    
    def _extract_symbol(self, text):
        """Extract stock symbols from text"""
        symbols = []
        
        # $SYMBOL pattern
        symbols.extend(re.findall(r'\$([A-Z]{1,5})\b', text))
        
        # Common stock names
        stock_names = {
            'TESLA': 'TSLA',
            'APPLE': 'AAPL',
            'AMAZON': 'AMZN',
            'MICROSOFT': 'MSFT',
            'GOOGLE': 'GOOGL',
            'META': 'META',
            'NETFLIX': 'NFLX',
            'NVIDIA': 'NVDA',
            'AMD': 'AMD',
            'INTEL': 'INTC',
            'DISNEY': 'DIS',
            'NIKE': 'NKE',
            'COINBASE': 'COIN',
            'ROBINHOOD': 'HOOD',
            'PALANTIR': 'PLTR',
            'GAMESTOP': 'GME',
            'AMC': 'AMC',
            'BLACKBERRY': 'BB',
            'NOKIA': 'NOK',
            'SILVER': 'SLV',
            'GOLD': 'GOLD',
            'BITCOIN': 'BTC',
            'ETHEREUM': 'ETH'
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
        for symbol in symbols[:5]:  # Check first 5
            if len(symbol) <= 5 and symbol.isalpha():
                return symbol
        
        return ''
    
    def _calculate_hype_score(self, text):
        """Calculate hype/bearish score from text"""
        bullish_score = 0
        bearish_score = 0
        
        # Count bullish keywords
        for keyword in self.hype_keywords:
            bullish_score += text.count(keyword.upper())
        
        # Count bearish keywords
        for keyword in self.bearish_keywords:
            bearish_score += text.count(keyword.upper())
        
        return {
            'bullish': bullish_score,
            'bearish': bearish_score
        }

async def main():
    """Main function to run the scanner"""
    
    # Load config
    from config.secure_config import config
    
    # Initialize scanner
    scanner = NewsDrivenScanner(config)
    
    # Scan for hot stocks
    hot_stocks = await scanner.scan_news_for_hot_stocks()
    
    # Return symbols for main system to analyze
    if hot_stocks:
        symbols = [stock['symbol'] for stock in hot_stocks]
        print(f"\n🎯 SYMBOLS FOR ANALYSIS: {', '.join(symbols)}")
        return symbols
    else:
        print("\n❌ No symbols found for analysis")
        return []

if __name__ == "__main__":
    symbols = asyncio.run(main())
    
    if symbols:
        print(f"\n✅ Ready to analyze: {len(symbols)} symbols")
    else:
        print("\n⚠️ Run again later for more news")
