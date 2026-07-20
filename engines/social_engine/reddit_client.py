import os
import re
import json
import asyncio
import logging
import asyncpraw
from collections import Counter
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from .trader_reputation import TraderReputation

logger = logging.getLogger(__name__)


def _social_debug_enabled(config: dict) -> bool:
    if not config:
        return False
    return bool(config.get("debug_mode") or config.get("debug"))


def _social_debug(config: dict, msg: str) -> None:
    if _social_debug_enabled(config):
        logger.debug(msg)

class RedditTrendingTracker:
    """
    Tracks trending tickers and coins from Reddit discussions.
    Integrates with Phasma AI's main system.
    """
    
    def __init__(self, config: dict = None):
        """Initialize with optional config"""
        self.config = config or {}
        self.reddit = None
        self.symbols = Counter()
        self.last_update = None
        # Reddit client will be initialized lazily when needed
        
        # Initialize trader reputation system
        self.trader_reputation = TraderReputation()
        
        # Load dynamic whitelist from validated symbols
        self.dynamic_whitelist = self._load_dynamic_whitelist()
        
        # Subreddits to monitor
        self.subreddits = [
            'pennystocks', 'wallstreetbets', 'CryptoCurrency', 'stocks',
            'StockMarket', 'investing', 'RobinHoodPennyStocks', 'shortsqueeze',
            'Daytrading', 'SmallCapStocks', 'Stock_Picks', 'trakstocks'
        ]
        
        # Common words to ignore
        self.ignore_words = {
            'A', 'I', 'DD', 'WSB', 'YOLO', 'FOMO', 'HODL', 'THE', 'AND', 'FOR',
            'ARE', 'YOU', 'HAS', 'WAS', 'WERE', 'THIS', 'THAT', 'WILL', 'HAVE',
            'THEY', 'THEIR', 'WHAT', 'WHEN', 'WHERE', 'YOUR', 'FROM', 'WITH', 'JUST'
        }
        self.reddit = None
    
    def _load_dynamic_whitelist(self) -> set:
        """Load validated symbols from company validation cache"""
        dynamic_symbols = set()
        cache_file = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'company_validation_cache.json')
        
        try:
            if os.path.exists(cache_file):
                with open(cache_file, 'r') as f:
                    cache = json.load(f)
                    # Add all validated symbols
                    for symbol, data in cache.items():
                        if data.get('is_valid', False):
                            dynamic_symbols.add(symbol)
                    _social_debug(self.config, f"Loaded {len(dynamic_symbols)} symbols from validation cache")
        except Exception as e:
            print(f"Error loading dynamic whitelist: {e}")
        
        return dynamic_symbols
    
    async def _initialize_client(self):
        """Initialize Reddit client with environment variables"""
        try:
            _social_debug(self.config, "Initializing Reddit client with credentials")
            self.reddit = asyncpraw.Reddit(
                client_id=os.getenv('REDDIT_CLIENT_ID'),
                client_secret=os.getenv('REDDIT_SECRET'),
                user_agent=os.getenv('REDDIT_USER_AGENT', 'PhasmaAITrading/1.0')
            )
            # Test connection
            await self.reddit.user.me()
            _social_debug(self.config, "Reddit client initialized and connected successfully")
        except Exception as e:
            print(f"[ERROR] Failed to initialize Reddit client: {e}")
            self.reddit = None
    
    def _validate_symbol(self, symbol: str) -> bool:
        """Validate if symbol is a real stock ticker"""
        try:
            # Check against company validation cache if available
            cache_file = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'company_validation_cache.json')
            if os.path.exists(cache_file):
                with open(cache_file, 'r') as f:
                    cache = json.load(f)
                    if symbol in cache:
                        return cache[symbol].get('is_valid', False)
            
            # Basic criteria validation (more lenient)
            # Accept 2-5 letter uppercase symbols
            if len(symbol) < 2 or len(symbol) > 5:
                return False
            if not symbol.isalpha() or not symbol.isupper():
                return False
            
            # Additional checks to avoid common words
            if symbol in ['THE', 'AND', 'FOR', 'ARE', 'YOU', 'HAS', 'WAS', 'WERE', 'THIS', 'THAT']:
                return False
            
            return True
        except Exception as e:
            print(f"Validation error for {symbol}: {e}")
            # Fall back to basic criteria if validation fails
            return (len(symbol) >= 2 and len(symbol) <= 5 and 
                   symbol.isalpha() and symbol.isupper())
    
    def extract_symbols(self, text: str) -> List[str]:
        """Extract stock/crypto symbols from text"""
        if not text:
            return []
            
        # Expanded symbol detection patterns
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
        
        # Filter to actual stock tickers only using strict criteria
        filtered = []
        
        # Common Reddit words and non-ticker terms to exclude
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
            'TO', 'SO', 'NO', 'DO', 'OF', 'IS', 'IN', 'BE', 'AS', 'OR', 'IF', 'BY',
            'KNOW', 'MOST', 'FAIL', 'TEST', 'TRY', 'KNOW', 'MOST', 'FAIL', 'TEST', 'TRY',
            'KNOW', 'MOST', 'FAIL', 'TEST', 'TRY', 'KNOW', 'MOST', 'FAIL', 'TEST', 'TRY'
        }    # Additional common words that were causing yfinance errors
        exclude_words = {
            'OF', 'IS', 'IN', 'BE', 'AS', 'OR', 'IF', 'BY', 'MY', 'WE', 'HE', 'SHE',
            'HIM', 'HER', 'ITS', 'WHO', 'WHOM', 'WHOSE', 'WHICH', 'THAT', 'THIS',
            'THESE', 'THOSE', 'AM', 'IS', 'ARE', 'WAS', 'WERE', 'BEEN', 'BEING'
        }
        
        # Whitelist of real stock tickers - only accept these
        common_tickers = {
            # Tech Giants
            'AAPL', 'MSFT', 'GOOGL', 'GOOG', 'AMZN', 'TSLA', 'META', 'NVDA', 'NFLX', 'DIS',
            'CRM', 'ADBE', 'INTC', 'CSCO', 'PYPL', 'NFLX', 'CMCSA', 'PEP', 'COST', 'AVGO',
            
            # Popular Meme/Reddit Stocks
            'GME', 'AMC', 'BB', 'NOK', 'PLTR', 'SNDL', 'BNGO', 'MVIS', 'SPCE', 'RBLX',
            'KOSS', 'EXPR', 'FIZZ', 'BBBY', 'CLOV', 'WISH', 'MUDS', 'SPRT', 'SOS', 'RIOT',
            
            # EV & Auto
            'NIO', 'XPEV', 'LI', 'LCID', 'RIVN', 'FSR', 'CHPT', 'BLNK', 'NKLA', 'HYLN',
            'GM', 'F', 'TM', 'HMC', 'VWAGY', 'BMWYY', 'NSANY', 'DDAIF', 'TSLA', 'RIVN',
            
            # Crypto & Blockchain
            'COIN', 'MARA', 'RIOT', 'SQ', 'PYPL', 'MSTR', 'HOOD', 'IBIT', 'FBTC', 'BITO',
            'BTC', 'ETH', 'SOL', 'ADA', 'DOT', 'MATIC', 'LINK', 'AVAX', 'UNI', 'ATOM',
            
            # Growth Tech
            'ROKU', 'ZM', 'PTON', 'DOCU', 'ZS', 'CRWD', 'OKTA', 'SNOW', 'PLBY', 'GPRO',
            'FIT', 'TWLO', 'SNAP', 'TWTR', 'UBER', 'LYFT', 'DASH', 'MELI', 'SE', 'SPOT',
            
            # Biotech & Pharma
            'MRNA', 'BNTX', 'JNJ', 'PFE', 'ABBV', 'BMY', 'AMGN', 'GILD', 'REGN', 'VRTX',
            'MDT', 'ISRG', 'SYK', 'BSX', 'ABT', 'TMO', 'DHR', 'IDXX', 'BHC', 'PEN',
            
            # Energy & Industrial
            'XOM', 'CVX', 'COP', 'SLB', 'HAL', 'BKR', 'OXY', 'BP', 'SHEL', 'TOT',
            'CAT', 'DE', 'GE', 'MMM', 'HON', 'UPS', 'RTX', 'BA', 'LMT', 'NOC',
            
            # Financials
            'JPM', 'BAC', 'WFC', 'GS', 'MS', 'C', 'AXP', 'BLK', 'SPGI', 'V',
            'MA', 'PYPL', 'SQ', 'COIN', 'BRK.A', 'BRK.B', 'AIG', 'MET', 'PRU', 'TRV',
            
            # Consumer Staples
            'WMT', 'PG', 'KO', 'PEP', 'COST', 'CL', 'KMB', 'GIS', 'K', 'KR',
            'HD', 'LOW', 'TGT', 'MCD', 'SBUX', 'NKE', 'UA', 'LULU', 'CROX', 'DECK',
            
            # Healthcare
            'JNJ', 'PFE', 'UNH', 'ABBV', 'T', 'DHR', 'ABT', 'MDT', 'ISRG', 'SYK',
            'BSX', 'BMY', 'AMGN', 'GILD', 'REGN', 'VRTX', 'ILMN', 'IDXX', 'BDX', 'BIO',
            
            # Real Estate & REITs
            'AMT', 'PLD', 'CCI', 'EQIX', 'PSA', 'O', 'SPG', 'DLR', 'EXR', 'PRO',
            'VTR', 'WELL', 'HST', 'ESS', 'AVB', 'EQR', 'MAA', 'UDR', 'FRT', 'KIM',
            
            # Utilities
            'NEE', 'DUK', 'SO', 'AEP', 'EXC', 'SRE', 'XEL', 'WEC', 'ED', 'DTE',
            'PEG', 'EIX', 'AEE', 'CMS', 'AWK', 'ETR', 'FE', 'NI', 'PNW', 'WR',
            
            # Materials & Mining
            'LIN', 'APD', 'ECL', 'DD', 'DOW', 'CC', 'NUE', 'STLD', 'NEM', 'FCX',
            'RIO', 'BHP', 'VALE', 'GOLD', 'BARR', 'FNV', 'WPM', 'KL', 'AGI', 'SAND',
            
            # Communication Services
            'GOOGL', 'GOOG', 'META', 'T', 'VZ', 'CMCSA', 'CHTR', 'DIS', 'NFLX', 'EA',
            'ATVI', 'TTWO', 'ZNGA', 'EA', 'TTWO', 'DIS', 'NFLX', 'ROKU', 'SNAP', 'TWTR',
            
            # Small Cap & Growth
            'UPST', 'AFRM', 'SQ', 'HOOD', 'COIN', 'RBLX', 'PLTR', 'NKLA', 'LCID', 'RIVN',
            'CHPT', 'BLNK', 'FSR', 'SPCE', 'MVIS', 'BNGO', 'SNDL', 'AMC', 'GME', 'BB',
            
            # ETFs
            'SPY', 'QQQ', 'IWM', 'DIA', 'VTI', 'VOO', 'GLD', 'SLV', 'TLT', 'HYG',
            'LQD', 'XLF', 'XLE', 'XLK', 'XLI', 'XLU', 'XLV', 'XLY', 'XLP', 'XLB'
        }
        
        for symbol in all_symbols:
            if len(symbol) < 2 or len(symbol) > 5:
                continue
            if symbol in exclude_words or symbol in self.exclude_words:
                continue
            
            # Skip symbols with bad trader reputation
            if self.trader_reputation.should_avoid_symbol(symbol):
                continue
            
            # Validate symbol is a real stock ticker
            if not self._validate_symbol(symbol):
                continue
            
            # Whitelist filtering: accept symbols from static list OR dynamic cache
            if symbol.isalpha() and symbol.isupper():
                # Keep if it's in our static ticker list OR dynamic whitelist
                if symbol in common_tickers or symbol in self.dynamic_whitelist:
                    filtered.append(symbol)
            elif any(c.isdigit() for c in symbol):
                # Keep symbols with numbers but only if they have at least 2 letters
                letter_count = sum(1 for c in symbol if c.isalpha())
                if letter_count >= 2 and len(symbol) <= 5:
                    # Check if the letters part looks like a real ticker
                    letters = ''.join([c for c in symbol if c.isalpha()])
                    if letters in common_tickers or len(letters) >= 2:
                        filtered.append(symbol)
        
        return filtered
    
    def _detect_sentiment(self, text: str) -> str:
        """Detect if sentiment is bullish, bearish, or neutral"""
        text = text.upper()
        
        bullish_words = ['BUY', 'MOON', 'ROCKET', 'BULL', 'CALL', 'LONG', 'PUMP', 'RIP', 'TO_THE_MOON', 'DIAMOND_HANDS']
        bearish_words = ['SELL', 'CRASH', 'BEAR', 'PUT', 'SHORT', 'DUMP', 'PAPER_HANDS', 'FALL', 'DROP']
        
        bullish_count = sum(1 for word in bullish_words if word in text)
        bearish_count = sum(1 for word in bearish_words if word in text)
        
        if bullish_count > bearish_count:
            return 'BULLISH'
        elif bearish_count > bullish_count:
            return 'BEARISH'
        else:
            return 'NEUTRAL'
    
    async def get_trending_symbols(self, limit: int = 20) -> Dict[str, int]:
        """
        Get trending symbols from monitored subreddits
        Returns: Dictionary of {symbol: mention_count}
        """
        if not self.reddit:
            await self._initialize_client()
            if not self.reddit:
                _social_debug(self.config, "Failed to initialize Reddit client")
                return {}
        
        self.symbols.clear()
        subreddits_scanned = 0
        
        for subreddit_name in self.subreddits:
            try:
                subreddits_scanned += 1
                # Add timeout for each subreddit scan (asyncio.timeout not available in some envs)
                async def _scan_subreddit():
                    subreddit = await self.reddit.subreddit(subreddit_name)
                    post_count = 0
                    symbols_found = 0
                    
                    # Scan more posts from hot and new
                    async for submission in subreddit.hot(limit=10):
                        content = f"{submission.title} {getattr(submission, 'selftext', '')}"
                        extracted = self.extract_symbols(content)
                        if extracted:
                            self.symbols.update(extracted)
                            symbols_found += len(extracted)
                            
                            # Track user predictions for reputation system
                            if hasattr(submission, 'author') and submission.author:
                                username = str(submission.author)
                                # Detect sentiment from title
                                sentiment = self._detect_sentiment(submission.title)
                                for symbol in extracted:
                                    self.trader_reputation.record_prediction(
                                        username=username,
                                        symbol=symbol,
                                        prediction='SOCIAL_MENTION',
                                        sentiment=sentiment
                                    )
                        
                        post_count += 1
                        if post_count >= 10:
                            break
                        await asyncio.sleep(0.1)
                    
                    # Also scan some new posts for fresh trends
                    post_count = 0
                    async for submission in subreddit.new(limit=5):
                        content = f"{submission.title} {getattr(submission, 'selftext', '')}"
                        extracted = self.extract_symbols(content)
                        if extracted:
                            self.symbols.update(extracted)
                            symbols_found += len(extracted)
                        post_count += 1
                        if post_count >= 5:
                            break
                        await asyncio.sleep(0.1)
                    
                await asyncio.wait_for(_scan_subreddit(), timeout=15)

            except asyncio.TimeoutError:
                print(f"[WARNING] Timeout processing r/{subreddit_name}")
                continue
            except Exception as e:
                print(f"[WARNING] Error processing r/{subreddit_name}: {e}")
                continue
        
        self.last_update = datetime.now()
        result = dict(self.symbols.most_common(limit))
        _social_debug(
            self.config,
            f"Reddit scan done: {len(result)} trending symbols from "
            f"{subreddits_scanned} subreddits ({sum(self.symbols.values())} mentions)",
        )
        return result
    
    def get_status(self) -> dict:
        """Get current status of the tracker"""
        return {
            'last_update': self.last_update.isoformat() if self.last_update else None,
            'subreddits_monitored': len(self.subreddits),
            'symbols_tracked': len(self.symbols),
            'top_symbols': dict(self.symbols.most_common(10))
        }
    
    async def close(self):
        """Clean up resources"""
        if self.reddit:
            await self.reddit.close()

# Example usage
async def example():
    tracker = RedditTrendingTracker()
    try:
        trending = await tracker.get_trending_symbols()
        print("Trending symbols:")
        for symbol, count in trending.items():
            print(f"${symbol}: {count} mentions")
    finally:
        await tracker.close()

if __name__ == "__main__":
    asyncio.run(example())
