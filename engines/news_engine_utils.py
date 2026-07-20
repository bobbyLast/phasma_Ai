"""
News Engine Utilities Module
Utility functions for news processing, validation, and analysis
"""

import re
from typing import List, Dict, Optional, Any
from datetime import datetime

# Import moonshot keywords
try:
    from .moonshot_keywords import MoonshotKeywords
    MOONSHOT_DETECTION_ENABLED = True
except ImportError:
    MOONSHOT_DETECTION_ENABLED = False
    print("[WARN] Moonshot keywords not available")

class NewsUtils:
    """Utility functions for news processing"""

    # NON-TRADEABLE SYMBOLS - Never extract these from news
    BLOCKED_SYMBOLS = {
        # Currency pairs (not stocks)
        'EURUSD', 'GBPUSD', 'USDJPY', 'AUDUSD', 'USDCAD', 'USDCHF', 'NZDUSD',
        'EURJPY', 'GBPJPY', 'AUDJPY', 'CADJPY', 'CHFJPY', 'EURGBP', 'EURCAD',
        'GBPCAD', 'AUDCAD', 'NZDCAD', 'EURCHF', 'GBPCHF', 'AUDCHF', 'NZDCHF',
        # Commodities (not stocks)
        'GOLD', 'SILVER', 'COPPER', 'CRUDE', 'NATURALGAS', 'CORN', 'WHEAT',
        'SOYBEANS', 'COTTON', 'SUGAR', 'COFFEE', 'COCOA', 'PLATINUM', 'PALLADIUM'
    }

    # Words that look like tickers in headlines but are not tradeable symbols
    EXTRACTION_STOPWORDS = {
        'THE', 'AND', 'FOR', 'YOU', 'ARE', 'ALL', 'HAS', 'WAS', 'BUT', 'NOT', 'CAN',
        'THIS', 'THAT', 'WITH', 'FROM', 'HAVE', 'BEEN', 'WILL', 'MORE', 'WHEN', 'MAKE',
        'THAN', 'LIKE', 'TIME', 'JUST', 'KNOW', 'YEAR', 'COULD', 'THEM', 'SEE', 'OTHER',
        'THEN', 'NOW', 'LOOK', 'ONLY', 'COME', 'ITS', 'OVER', 'ALSO', 'BACK', 'AFTER',
        'USE', 'TWO', 'HOW', 'OUR', 'WORK', 'FIRST', 'WELL', 'WAY', 'EVEN', 'NEW', 'WANT',
        'BECAUSE', 'ANY', 'THESE', 'GIVE', 'DAY', 'MOST', 'USA', 'CEO', 'CFO', 'COO',
        'IPO', 'SEC', 'FDA', 'NYSE', 'NASDAQ', 'ETF', 'API', 'NEWS', 'BREAKING', 'UPDATE',
        'LOW', 'HIGH', 'TOP', 'BIG', 'RED', 'MAY', 'RUN', 'SET', 'GET', 'PUT', 'CALL',
        'BUY', 'SELL', 'HIT', 'CUT', 'ADD', 'END', 'AGO', 'PER', 'VIA', 'OUT', 'OFF',
        'UAE', 'GDP', 'CPI', 'FED', 'ECB', 'BOJ', 'IMF', 'WHO', 'UN', 'EU', 'UK', 'US',
        'AI', 'IT', 'HR', 'PR', 'TV', 'LA', 'NYC', 'OK', 'VS', 'PM', 'AM', 'EST', 'PST',
        'NBA', 'NHL', 'MLB', 'NFL', 'UFC', 'GTA', 'CFTC', 'MAGA', 'RSS', 'URL', 'PDF',
        'Q&A', 'B2B', 'B2C', 'R&D', 'ATH', 'ATL', 'YTD', 'QOQ', 'YOY', 'EPS', 'PE',
        'CEO', 'CFO', 'COO', 'CTO', 'CMO', 'VP', 'LLC', 'INC', 'LTD', 'PLC',
        'ON', 'ONE', 'AN', 'AT', 'BE', 'BY', 'DO', 'GO', 'IF', 'IN', 'IS', 'ME', 'MY',
        'NO', 'OF', 'OR', 'SO', 'TO', 'UP', 'WE', 'CAT', 'REAL', 'NEXT', 'OPEN', 'FREE',
        'GOOD', 'BEST', 'FAST', 'SAFE', 'TRUE', 'PLAY', 'MOVE', 'LIVE', 'HOME', 'CARE',
    }

    # Ambiguous tickers that need cashtag or company-context agreement
    AMBIGUOUS_TICKERS = frozenset({
        'AI', 'IT', 'ON', 'ALL', 'CAT', 'A', 'NOW', 'LOW', 'RUN', 'REAL', 'OPEN', 'FREE',
    })

    CRYPTO_SYMBOLS = {'BTC', 'ETH', 'SOL', 'XRP', 'DOGE', 'LINK'}

    # INDICES - Can be extracted and considered for trading
    TRADEABLE_INDICES = {
        'VIX', 'SPY', 'SPX', 'QQQ', 'IWM', 'VTI', 'VOO', 'IVV', 'SCHB',
        'DIA', 'ONEQ', 'VTWO', 'SCHX', 'SCHA', 'SCHM', 'SCHV', 'SCHG',
        'IJR', 'IJH', 'IJJ', 'IJK', 'IJT', 'IJS', 'IWN', 'IWO', 'IWP', 'IWS',
        'SPYG', 'SPYV', 'SPYD', 'SPYL', 'SPTM', 'SPTS', 'SPTL', 'SPTB',
        'QQQE', 'QQQM', 'PSQ', 'QID', 'QLD', 'TQQQ', 'SQQQ', 'UPRO', 'SPXL', 'SPXS',
        # Additional indices
        'RUT', 'NDX', 'COMPX', 'DJIA', 'NYA', 'XAX', 'BATX', 'HGX',
        'SOX', 'BKX', 'XBD', 'XED', 'XEO', 'XSP', 'ES', 'NQ', 'RTY', 'YM'
    }

    @staticmethod
    def is_valid_extracted_ticker(symbol: str, from_cash_tag: bool = False) -> bool:
        """Reject headline words and ambiguous 1-letter tokens masquerading as tickers."""
        symbol = str(symbol or '').upper().strip()
        if not symbol or not symbol.isalpha() or len(symbol) > 5:
            return False
        if symbol in NewsUtils.BLOCKED_SYMBOLS or symbol in NewsUtils.EXTRACTION_STOPWORDS:
            return False
        if len(symbol) == 1 and not from_cash_tag:
            return False
        if symbol in getattr(NewsUtils, "AMBIGUOUS_TICKERS", ()) and not from_cash_tag:
            return False
        return True

    @staticmethod
    def propagate_prices(items: List[Dict]) -> None:
        """Copy known prices from market-data rows onto symbol-tagged news rows."""
        prices: Dict[str, float] = {}
        for item in items:
            symbol = str(item.get('symbol') or '').upper().strip()
            price = item.get('price') if item.get('price') is not None else item.get('current_price')
            if not symbol or price is None:
                continue
            try:
                prices[symbol] = float(price)
            except (TypeError, ValueError):
                continue
        for item in items:
            symbol = str(item.get('symbol') or '').upper().strip()
            if symbol and item.get('price') is None and symbol in prices:
                item['price'] = prices[symbol]

    @staticmethod
    def extract_symbol_from_text(text: str, company_db: Dict) -> Optional[str]:
        """Extract stock symbol from text by checking both tickers and company names"""
        text_upper = text.upper()

        # First, try to find direct ticker matches (most reliable)
        for symbol in company_db.keys():
            if symbol in text_upper and symbol not in NewsUtils.BLOCKED_SYMBOLS:
                return symbol

        # Then, try to match company names and aliases
        for symbol, info in company_db.items():
            if symbol in NewsUtils.BLOCKED_SYMBOLS:
                continue
            aliases = info.get('aliases', [])
            for alias in aliases:
                if alias.upper() in text_upper:
                    return symbol

        return None

    @staticmethod
    def filter_by_options_criteria(news_items: List[Dict], min_iv: float = 20.0, min_volume: int = 100) -> List[Dict]:
        """Filter news items by options criteria (IV, volume) - LOWERED for more opportunities"""
        filtered_items = []

        for item in news_items:
            # Simulate realistic options data based on company and news
            symbol = item.get('symbol', '')
            catalyst_score = item.get('catalyst_score', 0.0)
            sentiment = item.get('sentiment', 0.0)

            # Estimate IV based on company type and news sentiment/catalyst
            company_info = item.get('fact_check', {}).get('company_info', {})
            avg_volume = company_info.get('avg_volume', 'Medium')

            # Base IV calculation - more realistic per sector
            sector_vol_map = {
                'Technology': 0.45, 'AI': 0.55, 'Energy': 0.40, 'Healthcare': 0.50,
                'Finance': 0.35, 'Consumer': 0.30, 'Automotive': 0.45, 'Mining': 0.50,
                'E-commerce': 0.40, 'Entertainment': 0.35
            }

            # Get sector from company info
            company_info = item.get('fact_check', {}).get('company_info', {})
            sector = company_info.get('sector', 'Technology')

            # Base IV from sector
            base_iv = sector_vol_map.get(sector, 0.35) * 100  # Convert to percentage

            # Adjust for company volume (high volume = higher IV)
            if avg_volume == 'High':
                base_iv += 15.0
            elif avg_volume == 'Medium':
                base_iv += 5.0

            # Adjust for news catalyst and sentiment
            catalyst_multiplier = 1.0 + (catalyst_score * 0.5)  # Strong catalysts increase IV
            sentiment_multiplier = 1.0 + (abs(sentiment) * 0.3)  # Strong sentiment increases IV

            estimated_iv = base_iv * catalyst_multiplier * sentiment_multiplier
            estimated_iv = min(estimated_iv, 150.0)  # Cap at 150%

            # Estimate options volume based on company and news - more realistic per sector
            sector_volume_map = {
                'Technology': 25000, 'AI': 35000, 'Energy': 20000, 'Healthcare': 15000,
                'Finance': 30000, 'Consumer': 12000, 'Automotive': 18000, 'Mining': 8000,
                'E-commerce': 20000, 'Entertainment': 15000
            }

            # Base volume from sector
            base_options_volume = sector_volume_map.get(sector, 15000)

            # Adjust for company volume (high volume companies have more options trading)
            if avg_volume == 'High':
                base_options_volume *= 2.5
            elif avg_volume == 'Medium':
                base_options_volume *= 1.5

            # News impact on volume (stronger news = more options activity)
            news_volume_multiplier = 1.0 + (catalyst_score * 2.0) + (abs(sentiment) * 1.5)
            estimated_options_volume = int(base_options_volume * news_volume_multiplier)

            # Add options data to the item
            item['options_data'] = {
                'estimated_iv': round(estimated_iv, 1),
                'estimated_options_volume': estimated_options_volume,
                'meets_criteria': estimated_iv >= min_iv and estimated_options_volume >= min_volume
            }

            # Filter items that meet options criteria
            if item['options_data']['meets_criteria']:
                filtered_items.append(item)

        print(f"📊 Options filtering: {len(filtered_items)}/{len(news_items)} items meet IV>{min_iv}% & Volume>{min_volume} criteria")
        return filtered_items

    @staticmethod
    def get_options_recommendation(news_item: Dict, stock_only_mode: bool = False) -> str:
        """Get options trading recommendation based on news and company data
        
        Args:
            news_item: News item dictionary
            stock_only_mode: If True, returns simple BUY/SELL recommendations
        """
        symbol = news_item.get('symbol', '')
        sentiment = news_item.get('sentiment', 0.0)
        catalyst_score = news_item.get('catalyst_score', 0.0)
        options_data = news_item.get('options_data', {})

        # If in stock-only mode, return simple BUY/SELL
        if stock_only_mode:
            if sentiment > 0.1 or catalyst_score > 0.5:
                return 'BUY'  # Positive sentiment = BUY stock
            elif sentiment < -0.1:
                return 'SELL'  # Negative sentiment = SELL stock
            else:
                return 'HOLD'  # Neutral = hold

        iv = options_data.get('estimated_iv', 0.0)
        volume = options_data.get('estimated_options_volume', 0)

        # Determine recommendation based on sentiment and catalyst
    @staticmethod
    def calculate_optimal_expiry(news_item: Dict) -> int:
        """Calculate optimal options expiry based on catalyst timing"""
        catalyst_score = news_item.get('catalyst_score', 0.0)
        source = news_item.get('source', '')

        # Base expiry calculation
        if 'earnings' in source.lower() or catalyst_score > 0.8:
            return 7  # 1 week for earnings/high catalyst
        elif catalyst_score > 0.5:
            return 14  # 2 weeks for medium catalyst
        else:
            return 30  # 1 month for low catalyst

    @staticmethod
    def get_sector_from_symbol(symbol: str, company_db: Dict) -> str:
        """Get sector from symbol"""
        company_info = company_db.get(symbol.upper())
        return company_info.get('sector', 'Technology') if company_info else 'Technology'

    @staticmethod
    def calculate_sentiment(text: str) -> float:
        """Calculate sentiment score from text"""
        text_lower = text.lower()

        # Positive words
        positive_words = ['surge', 'soar', 'rise', 'gain', 'profit', 'growth', 'beat', 'exceed', 'strong', 'bullish', 'up', 'high', 'record']
        positive_score = sum(1 for word in positive_words if word in text_lower)

        # Negative words
        negative_words = ['fall', 'drop', 'decline', 'loss', 'miss', 'weak', 'bearish', 'plunge', 'crash', 'down', 'low', 'cut']
        negative_score = sum(1 for word in negative_words if word in text_lower)

        # Neutralize with context
        total_words = len(text.split())
        if total_words == 0:
            return 0.0

        # Add context-based adjustments
        context_multipliers = {
            'earnings': 1.2,
            'revenue': 1.1,
            'profit': 1.3,
            'loss': -1.2,
            'miss': -1.1,
            'beat': 1.2,
            'guidance': 0.8
        }

        context_multiplier = 1.0
        for context, multiplier in context_multipliers.items():
            if context in text_lower:
                context_multiplier *= multiplier

        sentiment = ((positive_score - negative_score) / max(total_words / 10, 1)) * context_multiplier
        return max(-1.0, min(1.0, sentiment))

    @staticmethod
    def calculate_catalyst_score(title: str, config: Dict) -> float:
        """Calculate catalyst score from title"""
        title_lower = title.lower()

        # Catalyst keywords from config
        catalyst_keywords = config.get('news', {}).get('catalyst_keywords', [
            'surge', 'deal', 'partnership', 'breakout', 'earnings',
            'soar', 'plunge', 'moon', 'rocket', 'pump', 'buzz',
            'merger', 'acquisition', 'ipo', 'split', 'dividend',
            'upgrade', 'downgrade', 'analyst', 'target'
        ])

        matches = sum(1 for keyword in catalyst_keywords if keyword in title_lower)
        total_keywords = len(catalyst_keywords)

        # Boost score for multiple matches
        if matches > 1:
            matches *= 1.5
        if matches > 3:
            matches *= 1.3

        return min(1.0, matches / max(total_keywords / 4, 1))

    @staticmethod
    def format_timestamp(timestamp_str: str) -> str:
        """Format timestamp consistently"""
        try:
            # Try to parse and format timestamp
            if timestamp_str:
                # If it's already in ISO format, keep it
                if 'T' in timestamp_str:
                    return timestamp_str
                else:
                    # Convert to ISO format
                    return datetime.utcnow().isoformat()
            else:
                return datetime.utcnow().isoformat()
        except:
            return datetime.utcnow().isoformat()

    @staticmethod
    def clean_news_text(text: str) -> str:
        """Clean and normalize news text"""
        if not text:
            return ""

        # Remove extra whitespace
        text = ' '.join(text.split())

        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', text)

        # Remove URLs
        text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)

        return text.strip()
    
    @staticmethod
    def detect_moonshot_catalyst(text: str) -> Dict[str, Any]:
        """
        Detect hidden moonshot catalysts in news text
        
        Returns:
            {
                'is_moonshot': bool,
                'score': 0-100,
                'keywords_found': [],
                'potential_move': '+50-200%',
                'risk_level': 'EXTREME/HIGH/MEDIUM/LOW',
                'priority': 'VERY_HIGH/HIGH/MEDIUM/LOW'
            }
        """
        if not MOONSHOT_DETECTION_ENABLED:
            return {
                'is_moonshot': False,
                'score': 0,
                'keywords_found': [],
                'potential_move': 'Not estimated',
                'risk_level': 'LOW',
                'priority': 'LOW'
            }
        
        # Use MoonshotKeywords to analyze text
        result = MoonshotKeywords.calculate_moonshot_score(text)
        
        # Add additional context
        result['catalyst_type'] = 'MOONSHOT' if result['is_moonshot'] else 'NORMAL'
        
        return result
    
    @staticmethod
    def get_moonshot_keywords_list() -> List[str]:
        """Get list of all moonshot keywords for reference"""
        if not MOONSHOT_DETECTION_ENABLED:
            return []
        return MoonshotKeywords.get_all_keywords()
    
    @staticmethod
    def get_high_priority_moonshots() -> List[str]:
        """Get only VERY_HIGH priority moonshot keywords"""
        if not MOONSHOT_DETECTION_ENABLED:
            return []
        return MoonshotKeywords.get_high_priority_keywords()
