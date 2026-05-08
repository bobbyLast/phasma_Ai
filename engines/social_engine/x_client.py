"""
X.com (Twitter) Social Media Engine for Phasma AI
Real-time stock sentiment and trending symbol detection from Twitter/X
"""

import tweepy
import re
import os
from typing import Dict, List, Set
from datetime import datetime, timedelta
import asyncio
import logging

logger = logging.getLogger(__name__)

class XTrendingTracker:
    """
    Tracks trending stock symbols from X.com/Twitter for sentiment analysis
    """
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.api = None
        self.symbols: Dict[str, int] = {}
        self.last_update = datetime.now()
        
        # Twitter/X API credentials from environment
        self.api_key = os.getenv('TWITTER_API_KEY')
        self.api_secret = os.getenv('TWITTER_API_SECRET')
        self.access_token = os.getenv('TWITTER_ACCESS_TOKEN')
        self.access_secret = os.getenv('TWITTER_ACCESS_SECRET')
        
        # Stock-related Twitter accounts to monitor
        self.watchlist = [
            'charliebilello',  # Market analysis
            'WSJmarkets',      # Wall Street Journal
            'CNBC',            # CNBC
            'Benzinga',        # Breaking news
            'StockTwits',      # Stock community
            'bespokeinvest',   # Market research
            'yahoofinance',    # Yahoo Finance
            'business',        # Business news
            'Reuters',         # Reuters Business
            'FT',              # Financial Times
            'marketwatch',     # MarketWatch
            'TheStreet',       # The Street
            'IBDinvestors',    # Investor's Business Daily
            'RealVision',      # Financial analysis
            'mikebellafiore',  # Options trader
            'traderstewie',    # Trader
            'OptionsHawk',     # Options flow
            'unusual_whales',  # Unusual options activity
            'zerohedge',       # Market commentary
        ]
        
        # Stock-related hashtags to track
        self.hashtags = [
            '#stocks', '#investing', '#trading', '#stockmarket', '#wallstreet',
            '#options', '#investments', '#finance', '#money', '#daytrading',
            '#swingtrading', '#stockstowatch', '#buystocks', '#stockmarketnews'
        ]
        
        # Common words to exclude from symbol extraction
        self.exclude_words = {
            'THE', 'AND', 'FOR', 'ARE', 'YOU', 'HAS', 'WAS', 'WERE', 'THIS', 'THAT',
            'WILL', 'HAVE', 'THEY', 'THEIR', 'WHAT', 'WHEN', 'WHERE', 'YOUR', 'FROM',
            'WITH', 'JUST', 'NOT', 'CAN', 'GET', 'OUT', 'SEE', 'WAY', 'NOW', 'NEW',
            'ALL', 'ONE', 'OUR', 'DAY', 'BUT', 'HER', 'SHE', 'HIM', 'HIS', 'HOW',
            'WHO', 'WHY', 'DID', 'SAID', 'MAKE', 'LIKE', 'TIME', 'VERY', 'COME',
            'THEM', 'THESE', 'THOSE', 'GOOD', 'BAD', 'BIG', 'SMALL', 'LONG', 'SHORT',
            'HIGH', 'LOW', 'UP', 'DOWN', 'BUY', 'SELL', 'CALL', 'PUT', 'STOCK',
            'TRADE', 'MARKET', 'PRICE', 'MONEY', 'CASH', 'USD', 'HTTP', 'HTTPS',
            'WWW', 'COM', 'HTML', 'DATA', 'INFO', 'NEWS', 'POST', 'USER', 'VIA',
            'A', 'I', 'DD', 'WSB', 'YOLO', 'FOMO', 'HODL', 'IT', 'GO', 'ON', 'AT',
            'TO', 'SO', 'NO', 'DO', 'OF', 'IS', 'IN', 'BE', 'AS', 'OR', 'IF', 'BY'
        }
        
        # Known valid stock tickers for validation
        self.known_tickers = {
            'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA', 'NFLX', 'DIS', 'BABA',
            'GME', 'AMC', 'BB', 'NOK', 'PLTR', 'SNDL', 'BNGO', 'MVIS', 'SPCE', 'RBLX',
            'COIN', 'ROKU', 'ZM', 'PTON', 'SQ', 'PYPL', 'SHOP', 'SNAP', 'TWTR', 'UBER',
            'LYFT', 'DOCU', 'ZS', 'CRWD', 'OKTA', 'SNOW', 'PLBY', 'GPRO', 'FIT', 'NIO',
            'XPEV', 'LI', 'LCID', 'RIVN', 'FSR', 'CHPT', 'BLNK', 'SPWR', 'ENPH', 'SEDG',
            'SOFI', 'HOOD', 'DKNG', 'MARA', 'RIOT', 'BTFD', 'TSLAQ', 'SPY', 'QQQ', 'IWM',
            'GLD', 'SLV', 'TLT', 'VIX', 'UVXY', 'SVXY', 'DIA', 'VTI', 'VOO', 'IVV'
        }
    
    async def _initialize_client(self) -> bool:
        """
        Initialize Twitter API client with authentication
        """
        try:
            if not all([self.api_key, self.api_secret, self.access_token, self.access_secret]):
                logger.error("❌ X CLIENT: Missing Twitter API credentials in .env file")
                return False
            
            # Initialize Tweepy client
            auth = tweepy.OAuthHandler(self.api_key, self.api_secret)
            auth.set_access_token(self.access_token, self.access_secret)
            self.api = tweepy.API(auth, wait_on_rate_limit=True)
            
            # Test authentication
            me = self.api.verify_credentials()
            logger.info(f"✅ X CLIENT: Successfully authenticated as @{me.screen_name}")
            return True
            
        except Exception as e:
            logger.error(f"❌ X CLIENT: Failed to initialize - {str(e)}")
            return False
    
    def extract_symbols(self, text: str) -> List[str]:
        """
        Extract potential stock symbols from tweet text
        """
        if not text:
            return []
        
        # Pattern to match stock symbols
        patterns = [
            r'\$([A-Za-z]{1,5})(?![a-z])',  # $GME style
            r'\b([A-Z]{2,5})\b',            # GME, AMC style (all caps)
            r'\b([A-Z]{1,4}\d{1,2})\b',     # GME1, AAPL2 style
            r'\b(\d{1,2}[A-Z]{1,4})\b',     # 1GME, 2AAPL style
        ]
        
        all_symbols = []
        for pattern in patterns:
            matches = re.findall(pattern, text.upper())
            all_symbols.extend(matches)
        
        # Filter symbols to find likely stock tickers
        filtered = []
        for symbol in all_symbols:
            if len(symbol) < 2 or len(symbol) > 5:
                continue
            if symbol in self.exclude_words:
                continue
            
            # Strict filtering for quality symbols
            if symbol.isalpha() and symbol.isupper():
                # Keep if it's a known ticker or looks like one
                if symbol in self.known_tickers:
                    filtered.append(symbol)
                elif len(symbol) >= 3 and len(symbol) <= 4:
                    # Check vowel count (most tickers have ≤2 vowels)
                    vowel_count = sum(1 for char in symbol if char in 'AEIOU')
                    if vowel_count <= 2:
                        filtered.append(symbol)
            elif any(c.isdigit() for c in symbol):
                # Keep numbered symbols if they have enough letters
                letter_count = sum(1 for c in symbol if c.isalpha())
                if letter_count >= 2:
                    filtered.append(symbol)
        
        return list(set(filtered))  # Remove duplicates
    
    async def _search_tweets(self, query: str, count: int = 20) -> List[Dict]:
        """
        Search for tweets containing stock-related content
        """
        try:
            if not self.api:
                if not await self._initialize_client():
                    return []
            
            # Search tweets
            tweets = self.api.search_tweets(
                q=query,
                lang='en',
                result_type='recent',
                count=count,
                tweet_mode='extended'
            )
            
            results = []
            for tweet in tweets:
                # Extract symbols from tweet text
                symbols = self.extract_symbols(tweet.full_text)
                
                if symbols:
                    results.append({
                        'text': tweet.full_text,
                        'symbols': symbols,
                        'user': tweet.user.screen_name,
                        'created_at': tweet.created_at,
                        'retweets': tweet.retweet_count,
                        'likes': tweet.favorite_count
                    })
            
            return results
            
        except Exception as e:
            logger.error(f"❌ X CLIENT: Error searching tweets - {str(e)}")
            return []
    
    async def get_trending_symbols(self, limit: int = 20) -> Dict[str, int]:
        """
        Get trending stock symbols from X.com/Twitter
        Returns: Dictionary of {symbol: mention_count}
        """
        print(f"🔍 X CLIENT: Getting trending symbols from X.com")
        
        if not self.api:
            if not await self._initialize_client():
                return {}
        
        # Clear previous symbols
        self.symbols.clear()
        
        # Search queries for stock-related content
        search_queries = [
            '$AAPL OR $TSLA OR $NVDA OR $META OR $GME OR $AMC',
            '#stocks OR #investing OR #trading',
            'stock market OR wallstreet OR investing',
            'options trading OR stock picks',
            'breaking stocks OR market news'
        ]
        
        all_results = []
        for query in search_queries:
            print(f"🔍 X CLIENT: Searching for: {query}")
            results = await self._search_tweets(query, count=20)
            all_results.extend(results)
            
            # Small delay to respect rate limits
            await asyncio.sleep(1)
        
        # Count symbol mentions
        symbol_counts = {}
        for result in all_results:
            for symbol in result['symbols']:
                symbol_counts[symbol] = symbol_counts.get(symbol, 0) + 1
        
        # Sort by mention count and limit results
        sorted_symbols = sorted(symbol_counts.items(), key=lambda x: x[1], reverse=True)
        self.symbols = dict(sorted_symbols[:limit])
        
        print(f"🔍 X CLIENT: Found {len(self.symbols)} trending symbols: {list(self.symbols.keys())[:10]}")
        return self.symbols
    
    async def get_symbol_sentiment(self, symbol: str) -> Dict:
        """
        Get sentiment analysis for a specific stock symbol
        """
        try:
            if not self.api:
                if not await self._initialize_client():
                    return {}
            
            # Search recent tweets about the symbol
            query = f"${symbol} OR #{symbol}"
            results = await self._search_tweets(query, count=50)
            
            if not results:
                return {}
            
            # Simple sentiment analysis based on keywords
            positive_keywords = ['bullish', 'buy', 'moon', 'rocket', 'gain', 'profit', 'strong', 'good', 'great']
            negative_keywords = ['bearish', 'sell', 'crash', 'drop', 'loss', 'weak', 'bad', 'terrible']
            
            positive_count = 0
            negative_count = 0
            total_tweets = len(results)
            
            for result in results:
                text_lower = result['text'].lower()
                if any(keyword in text_lower for keyword in positive_keywords):
                    positive_count += 1
                if any(keyword in text_lower for keyword in negative_keywords):
                    negative_count += 1
            
            # Calculate sentiment score
            if total_tweets > 0:
                sentiment_score = (positive_count - negative_count) / total_tweets
            else:
                sentiment_score = 0
            
            return {
                'symbol': symbol,
                'sentiment_score': sentiment_score,
                'positive_count': positive_count,
                'negative_count': negative_count,
                'total_tweets': total_tweets,
                'engagement': sum(r['likes'] + r['retweets'] for r in results)
            }
            
        except Exception as e:
            logger.error(f"❌ X CLIENT: Error getting sentiment for {symbol} - {str(e)}")
            return {}
