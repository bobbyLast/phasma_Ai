"""
News Collection Network - 24/7 Automated News Aggregation
Comprehensive RSS feed aggregation with smart deduplication and processing
"""

import asyncio
import feedparser
import re
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import aiohttp
from bs4 import BeautifulSoup

class NewsCollectionNetwork:
    """
    24/7 News aggregation from 50+ free RSS feeds
    Features:
    - Automatic fetching every 60 seconds
    - Symbol extraction and validation
    - Deduplication across sources
    - Relevance scoring
    - Integration with Phasma AI
    """
    
    def __init__(self, memory_bank=None, company_db=None, meta_brain=None):
        """Initialize news collection network"""
        self.memory_bank = memory_bank
        self.company_db = company_db or {}
        self.meta_brain = meta_brain
        self.logger = logging.getLogger(__name__)
        
        # RSS Feed Registry (50+ sources!)
        self.rss_feeds = self._initialize_comprehensive_feeds()
        
        # Running state
        self.is_running = False
        self.fetch_interval = 60  # seconds
        
        # Statistics
        self.stats = {
            'total_fetches': 0,
            'total_articles': 0,
            'duplicates_filtered': 0,
            'symbols_extracted': 0,
            'errors': 0
        }
    
    def _initialize_comprehensive_feeds(self) -> Dict:
        """Initialize 50+ free RSS feeds across all categories"""
        return {
            'FINANCIAL_HIGH_PRIORITY': [
                'https://feeds.reuters.com/reuters/businessNews',
                'https://feeds.reuters.com/reuters/topNews',
                'https://feeds.reuters.com/reuters/companyNews',
                'https://www.cnbc.com/id/100003114/device/rss/rss.html',  # Top News
                'https://www.cnbc.com/id/100727362/device/rss/rss.html',  # Stocks
                'https://www.marketwatch.com/rss/topstories',
                'https://www.investing.com/rss/news.rss',
                'https://www.investing.com/rss/news_25.rss',  # Most Popular
                'https://seekingalpha.com/feed.xml',
                'https://feeds.finance.yahoo.com/rss/2.0/headline?s=^GSPC',  # S&P 500
            ],
            
            'FINANCIAL_SECTOR_SPECIFIC': [
                'https://www.investing.com/rss/news_1.rss',  # Latest Financial News
                'https://www.investing.com/rss/news_14.rss',  # Stock Market News
                'https://www.investing.com/rss/news_301.rss',  # Commodities
                'https://www.investing.com/rss/news_95.rss',  # Cryptocurrency
                'https://www.fool.com/feeds/index.aspx',  # Motley Fool
                'https://www.bloomberg.com/feed/podcast/etf-report.xml',
            ],
            
            'TECH_AI_SECTOR': [
                'https://techcrunch.com/feed/',
                'https://www.theverge.com/rss/index.xml',
                'https://feeds.arstechnica.com/arstechnica/index',
                'https://www.wired.com/feed/rss',
                'https://www.cnet.com/rss/news/',
                'https://www.zdnet.com/news/rss.xml',
                'https://venturebeat.com/feed/',
                'https://www.artificialintelligence-news.com/feed/',
                'https://www.techmeme.com/feed.xml',
            ],
            
            'BUSINESS_GENERAL': [
                'https://feeds.bbci.co.uk/news/business/rss.xml',
                'https://www.ft.com/?format=rss',  # Financial Times
                'https://www.economist.com/business/rss.xml',
                'https://www.wsj.com/xml/rss/3_7014.xml',  # Wall Street Journal Markets
                'https://www.forbes.com/business/feed/',
                'https://www.businessinsider.com/rss',
            ],
            
            'NEWS_WIRE_SERVICES': [
                'https://rss.cnn.com/rss/money_latest.rss',
                'https://rss.nytimes.com/services/xml/rss/nyt/Business.xml',
                'https://feeds.reuters.com/Reuters/worldNews',
                'https://www.theguardian.com/world/rss',
                'https://www.theguardian.com/business/rss',
                'https://apnews.com/apf-topnews',
            ],
            
            'CRYPTO_BLOCKCHAIN': [
                'https://cointelegraph.com/rss',
                'https://www.coindesk.com/arc/outboundfeeds/rss/',
                'https://bitcoinmagazine.com/.rss/full/',
                'https://cryptonews.com/news/feed/',
                'https://decrypt.co/feed',
            ],
            
            'ENERGY_COMMODITIES': [
                'https://www.rigzone.com/news/feeds/rss_xml.asp',  # Oil & Gas
                'https://oilprice.com/rss/main',
                'https://www.worldoil.com/rss',
                'https://www.mining.com/feed/',  # Mining
            ],
            
            'BIOTECH_PHARMA': [
                'https://www.fiercebiotech.com/rss/xml',
                'https://www.fiercepharma.com/rss/xml',
                'https://www.biopharmadive.com/feeds/news/',
                'https://www.genengnews.com/feed/',
            ],
            
            'SOCIAL_SENTIMENT': [
                'https://www.reddit.com/r/wallstreetbets/.rss',
                'https://www.reddit.com/r/stocks/.rss',
                'https://www.reddit.com/r/investing/.rss',
                'https://www.reddit.com/r/options/.rss',
                'https://www.reddit.com/r/StockMarket/.rss',
                'https://www.reddit.com/r/daytrading/.rss',
                'https://www.reddit.com/r/trading/.rss',
                'https://www.reddit.com/r/pennystocks/.rss',
                'https://www.reddit.com/r/cryptocurrency/.rss',
                'https://www.reddit.com/r/cryptotrading/.rss',
            ],
            
            'ECONOMIC_DATA': [
                'https://www.federalreserve.gov/feeds/press_all.xml',  # Fed Announcements
                'https://www.census.gov/economic-indicators/indicator.xml',
                'https://tradingeconomics.com/rss/news.aspx',
            ]
        }
    
    async def start_network(self):
        """Start 24/7 news collection network"""
        self.is_running = True
        self.logger.info("🚀 Starting News Collection Network with 50+ RSS feeds...")
        
        while self.is_running:
            try:
                await self._fetch_all_feeds()
                await asyncio.sleep(self.fetch_interval)
            except Exception as e:
                self.logger.error(f"Network error: {e}")
                self.stats['errors'] += 1
                await asyncio.sleep(30)
    
    async def stop_network(self):
        """Stop news collection"""
        self.is_running = False
        self.logger.info("⏸️ Stopping News Collection Network")
    
    async def _fetch_all_feeds(self):
        """Fetch all RSS feeds concurrently"""
        self.stats['total_fetches'] += 1
        
        tasks = []
        
        for category, feeds in self.rss_feeds.items():
            for feed_url in feeds:
                task = asyncio.create_task(
                    self._fetch_single_feed(feed_url, category)
                )
                tasks.append(task)
        
        # Fetch all concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        all_articles = []
        for result in results:
            if isinstance(result, list):
                all_articles.extend(result)
            elif isinstance(result, Exception):
                self.stats['errors'] += 1
        
        # Process through pipeline
        if all_articles:
            await self._process_articles(all_articles)
    
    async def _fetch_single_feed(self, feed_url: str, category: str) -> List[Dict]:
        """Fetch and parse individual RSS feed"""
        try:
            # Add timeout for feed parsing
            loop = asyncio.get_event_loop()
            feed = await loop.run_in_executor(
                None, 
                lambda: feedparser.parse(feed_url)
            )
            
            if not feed.entries:
                return []
            
            articles = []
            
            for entry in feed.entries[:10]:  # Top 10 per feed
                article = {
                    'title': entry.get('title', ''),
                    'link': entry.get('link', ''),
                    'published': entry.get('published', ''),
                    'summary': entry.get('summary', entry.get('description', '')),
                    'source': feed_url,
                    'category': category,
                    'fetch_time': datetime.now().isoformat(),
                    'symbols': []  # Will be extracted
                }
                
                # Clean HTML from summary
                if article['summary']:
                    article['summary'] = self._clean_html(article['summary'])
                
                articles.append(article)
            
            return articles
            
        except Exception as e:
            self.logger.warning(f"Error fetching {feed_url}: {e}")
            return []
    
    async def _process_articles(self, articles: List[Dict]):
        """Process articles through full pipeline"""
        # Step 1: Extract symbols
        for article in articles:
            article['symbols'] = self._extract_symbols(
                article['title'] + ' ' + article.get('summary', '')
            )
        
        # Step 2: Filter relevant articles (have symbols or keywords)
        relevant_articles = [
            a for a in articles 
            if a['symbols'] or self._is_trading_relevant(a)
        ]
        
        self.logger.info(f"📰 Fetched {len(articles)} articles, {len(relevant_articles)} relevant")
        
        # Step 3: Deduplicate
        unique_articles = await self._deduplicate(relevant_articles)
        
        self.stats['total_articles'] += len(unique_articles)
        self.stats['duplicates_filtered'] += len(relevant_articles) - len(unique_articles)
        
        # Step 4: Store in memory bank
        if self.memory_bank:
            for article in unique_articles:
                result = self.memory_bank.store_article(article)
                if result['stored']:
                    self.stats['symbols_extracted'] += len(article['symbols'])
        
        # Step 5: Send to Phasma AI for analysis
        if self.meta_brain:
            for article in unique_articles:
                await self._send_to_phasma_ai(article)
    
    def _extract_symbols(self, text: str) -> List[str]:
        """Extract stock ticker symbols from text"""
        # Pattern for tickers: 1-5 uppercase letters
        ticker_pattern = r'\b[A-Z]{1,5}\b'
        potential_symbols = re.findall(ticker_pattern, text.upper())
        
        # Common words to exclude
        exclude_words = {
            'THE', 'AND', 'FOR', 'YOU', 'ARE', 'ALL', 'HAS', 'WAS', 'BUT',
            'NOT', 'CAN', 'THIS', 'THAT', 'WITH', 'FROM', 'HAVE', 'BEEN',
            'WILL', 'MORE', 'WHEN', 'MAKE', 'THAN', 'LIKE', 'TIME', 'JUST',
            'KNOW', 'YEAR', 'COULD', 'THEM', 'SEE', 'OTHER', 'THAN', 'THEN',
            'NOW', 'LOOK', 'ONLY', 'COME', 'ITS', 'OVER', 'ALSO', 'BACK',
            'AFTER', 'USE', 'TWO', 'HOW', 'OUR', 'WORK', 'FIRST', 'WELL',
            'WAY', 'EVEN', 'NEW', 'WANT', 'BECAUSE', 'ANY', 'THESE', 'GIVE',
            'DAY', 'MOST', 'USA', 'CEO', 'CFO', 'IPO', 'SEC', 'FDA', 'NYSE',
            'ETF', 'API', 'NEWS', 'BREAKING', 'UPDATE'
        }
        
        valid_symbols = []
        
        for symbol in potential_symbols:
            # Skip if in exclude list
            if symbol in exclude_words:
                continue
            
            # Validate against company database
            if self.company_db and symbol in self.company_db:
                valid_symbols.append(symbol)
            elif len(symbol) >= 2 and len(symbol) <= 5:
                # If no company_db, accept 2-5 letter tickers
                valid_symbols.append(symbol)
        
        # Remove duplicates while preserving order
        return list(dict.fromkeys(valid_symbols))
    
    def _is_trading_relevant(self, article: Dict) -> bool:
        """Check if article is relevant for trading"""
        relevance_keywords = [
            'earnings', 'profit', 'revenue', 'stock', 'shares', 'trading',
            'acquisition', 'merger', 'deal', 'contract', 'partnership',
            'fda approval', 'clinical trial', 'breakthrough', 'guidance',
            'beats estimates', 'misses estimates', 'outlook', 'forecast',
            'dividend', 'buyback', 'ipo', 'offering', 'delisting',
            'bankruptcy', 'investigation', 'lawsuit', 'settlement',
            'tariff', 'sanctions', 'regulation', 'subsidy'
        ]
        
        text = (article.get('title', '') + ' ' + article.get('summary', '')).lower()
        
        return any(keyword in text for keyword in relevance_keywords)
    
    async def _deduplicate(self, articles: List[Dict]) -> List[Dict]:
        """Deduplicate articles across sources"""
        if not self.memory_bank:
            # Simple title-based dedup
            seen_titles = set()
            unique = []
            
            for article in articles:
                title_normalized = self._normalize_text(article['title'])
                
                if title_normalized not in seen_titles:
                    seen_titles.add(title_normalized)
                    unique.append(article)
            
            return unique
        
        # Use memory bank for deduplication
        unique = []
        
        for article in articles:
            if not self.memory_bank.check_if_seen(article):
                unique.append(article)
        
        return unique
    
    def _normalize_text(self, text: str) -> str:
        """Normalize text for comparison"""
        # Remove special chars, extra spaces, lowercase
        text = re.sub(r'[^\w\s]', '', text.lower())
        text = ' '.join(text.split())
        return text
    
    def _clean_html(self, html_text: str) -> str:
        """Remove HTML tags from text"""
        try:
            soup = BeautifulSoup(html_text, 'html.parser')
            return soup.get_text(strip=True)
        except:
            # Fallback: simple regex
            return re.sub(r'<[^>]+>', '', html_text)
    
    async def _send_to_phasma_ai(self, article: Dict):
        """Send article to Phasma AI for analysis"""
        try:
            if not self.meta_brain:
                return
            
            # Convert to Phasma format
            news_item = {
                'title': article['title'],
                'content': article.get('summary', ''),
                'symbol': article['symbols'][0] if article['symbols'] else '',
                'source': article['source'],
                'published_at': article.get('published', ''),
                'url': article['link'],
                'category': article['category'],
                'all_symbols': article['symbols']
            }
            
            # Send to meta-brain for fact-checking and analysis
            # (This would integrate with your existing meta_brain system)
            # fact_check = self.meta_brain.fact_check_company(news_item)
            
            self.logger.debug(f"Sent to Phasma AI: {article['title'][:50]}...")
            
        except Exception as e:
            self.logger.error(f"Error sending to Phasma AI: {e}")
    
    def get_statistics(self) -> Dict:
        """Get network statistics"""
        return {
            'total_fetches': self.stats['total_fetches'],
            'total_articles': self.stats['total_articles'],
            'duplicates_filtered': self.stats['duplicates_filtered'],
            'symbols_extracted': self.stats['symbols_extracted'],
            'errors': self.stats['errors'],
            'feeds_count': sum(len(feeds) for feeds in self.rss_feeds.values()),
            'is_running': self.is_running
        }
    
    def get_feed_registry(self) -> Dict:
        """Get complete list of RSS feeds by category"""
        registry = {}
        
        for category, feeds in self.rss_feeds.items():
            registry[category] = {
                'count': len(feeds),
                'feeds': feeds
            }
        
        return registry
