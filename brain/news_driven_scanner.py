"""
News-Driven Stock Scanner
Finds hyped stocks under $50 from news sources
"""

import asyncio
import sys
import os

_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _root not in sys.path:
    sys.path.insert(0, _root)

from datetime import datetime
import re

class NewsDrivenScanner:
    """Scans news to find hot stocks under $50"""
    
    def __init__(self, config):
        self.config = config
        self.price_threshold = 50.0
        
        # Import price fetcher
        from utils.price_fetcher import get_price_fetcher
        self.price_fetcher = get_price_fetcher()
        
        # Import integrated news sources
        from engines.news_engine_integrated import IntegratedNewsSources
        self.news_sources = IntegratedNewsSources(config)
        
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
    
    async def scan_news_for_hot_stocks(self):
        """Scan all news to find hot stocks under $50"""
        
        print("=" * 80)
        print("🔥 NEWS-DRIVEN STOCK SCANNER")
        print("=" * 80)
        print("Finding hyped stocks under $50...")
        print("=" * 80)
        
        # 1. Get all news from our 20 sources
        print("\n📰 Fetching news from 20 sources...")
        all_news = await self.news_sources.fetch_all_integrated_sources()
        print(f"   Total news items: {len(all_news)}")
        
        # 2. Extract symbols and analyze sentiment
        print("\n🔍 Analyzing news for stock mentions...")
        stock_mentions = {}
        
        for item in all_news:
            title = item.get('title', '').upper()
            summary = item.get('summary', '').upper()
            text = f"{title} {summary}"
            
            # Extract symbols
            symbol = self._extract_symbol(text)
            
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
                    'sentiment': 'neutral'
                }
            
            stock_mentions[symbol]['mentions'] += 1
            stock_mentions[symbol]['hype_score'] += hype_score['bullish']
            stock_mentions[symbol]['bearish_score'] += hype_score['bearish']
            stock_mentions[symbol]['news_items'].append({
                'title': item.get('title', ''),
                'source': item.get('source', ''),
                'summary': item.get('summary', '')[:200] + '...'
            })
        
        print(f"   Found {len(stock_mentions)} stocks mentioned in news")
        
        # 3. Filter by price and sort by hype
        print("\n💰 Checking stock prices (under $50 only)...")
        affordable_stocks = []
        
        for symbol, data in stock_mentions.items():
            # Get current price
            price = self.price_fetcher.get_real_price(symbol)
            
            if not price:
                continue
            
            try:
                price = float(price)
            except:
                continue
            
            # Only include stocks under $50
            if price > self.price_threshold:
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
        
        print(f"   Found {len(affordable_stocks)} stocks under ${self.price_threshold}")
        
        # 4. Display results
        print("\n" + "=" * 80)
        print("🚀 HOT STOCKS UNDER $50")
        print("=" * 80)
        
        if not affordable_stocks:
            print("❌ No hot stocks found under $50")
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
        
        print(f"\n✅ Found {len(top_stocks)} hot stocks under $50 ready for analysis!")
        
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
