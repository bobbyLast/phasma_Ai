"""
News Engine APIs Module
Individual news API implementations
"""

import requests
import asyncio
import xml.etree.ElementTree as ET
import time
import logging
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
from engines.finnhub_news import get_finnhub

class NewsAPIs:
    """Individual news API implementations"""

    def __init__(self, config):
        self.config = config
        self.company_db = None  # Will be set by core module
        self.utils = None  # Will be set by core module
        self.validator = None  # Will be set by core module
        self.finnhub = get_finnhub()  # Add Finnhub real-time news

    def _retry_request(self, func, *args, max_retries=3, base_delay=1, **kwargs):
        """
        Retry HTTP requests with exponential backoff
        
        Args:
            func: Function to call (e.g., requests.get)
            max_retries: Maximum number of retry attempts
            base_delay: Initial delay in seconds
            *args, **kwargs: Arguments to pass to the function
            
        Returns:
            Response object or None if all retries fail
        """
        for attempt in range(max_retries + 1):
            try:
                response = func(*args, timeout=10, **kwargs)
                response.raise_for_status()
                return response
            except (requests.exceptions.RequestException, requests.exceptions.Timeout) as e:
                if attempt == max_retries:
                    return None
                
                delay = base_delay * (2 ** attempt)  # Exponential backoff
                time.sleep(delay)
        
        return None

    async def scan_saurav_newsapi(self) -> List[Dict[str, Any]]:
        """Scan Saurav NewsAPI for business news - WITH DATE AND RELEVANCE FILTERING"""
        url = "https://saurav.tech/NewsAPI/top-headlines/category/business/us.json"
        
        print(f"🔍 NEWS DEBUG: Fetching from {url}")

        response = self._retry_request(requests.get, url)
        if response is None:
            print("❌ Saurav NewsAPI: All retry attempts failed")
            return []

        try:
            data = response.json()
            articles = data.get('articles', [])
            print(f"🔍 NEWS DEBUG: Retrieved {len(articles)} articles from Saurav NewsAPI")

            news_items = []
            from datetime import datetime, timedelta
            
            # Only accept news from last 7 days
            cutoff_date = datetime.now() - timedelta(days=7)
            
            filtered_reasons = {'old_news': 0, 'no_symbol': 0, 'gossip': 0, 'passed': 0}
            
            for i, article in enumerate(articles[:10]):  # Check more articles but filter strictly
                title = article.get('title', 'NO TITLE')
                
                # Check date first
                published_at = article.get('publishedAt', '')
                try:
                    if published_at:
                        article_date = datetime.fromisoformat(published_at.replace('Z', '+00:00'))
                        if article_date < cutoff_date:
                            filtered_reasons['old_news'] += 1
                            print(f"[DEBUG] Article {i+1}: ❌ OLD ({article_date.strftime('%Y-%m-%d')}) - {title[:60]}...")
                            continue  # Skip old news
                except:
                    pass  # If date parsing fails, continue but flag as suspicious
                
                # Extract symbol from title or description
                text = self.utils.clean_news_text(
                    article.get('title', '') + ' ' + article.get('description', '')
                )
                symbol = self.utils.extract_symbol_from_text(text, self.company_db)

                # Only add if we found a valid symbol AND it's relevant
                if symbol:
                    # Check relevance: symbol must be in title (not just mentioned)
                    title_lower = article.get('title', '').lower()
                    
                    # Skip if it's just gossip/opinion without trading catalyst
                    gossip_keywords = ['questions', 'opinion', 'thinks', 'believes', 'says', 'claims']
                    if any(word in title_lower for word in gossip_keywords):
                        # Only allow if there's a real catalyst keyword
                        catalyst_keywords = ['earnings', 'revenue', 'profit', 'deal', 'merger', 'acquisition', 
                                            'partnership', 'contract', 'fda', 'approval', 'launch', 'breakthrough']
                        if not any(word in title_lower for word in catalyst_keywords):
                            filtered_reasons['gossip'] += 1
                            print(f"[DEBUG] Article {i+1}: ❌ GOSSIP - {title[:60]}...")
                            continue  # Skip gossip without catalyst
                    
                    filtered_reasons['passed'] += 1
                    print(f"[DEBUG] Article {i+1}: ✅ PASSED ({symbol}) - {title[:60]}...")
                    
                    news_item = {
                        'title': self.utils.clean_news_text(article.get('title', '')),
                        'source': 'saurav_newsapi',
                        'symbol': symbol,
                        'sector': self.utils.get_sector_from_symbol(symbol, self.company_db),
                        'timestamp': self.utils.format_timestamp(article.get('publishedAt')),
                        'url': article.get('url', ''),
                        'current_price': 0.0,  # Real price would come from market data API
                        'strike': 0.0,        # Real strike would come from options API
                        'sentiment': self.utils.calculate_sentiment(text),
                        'catalyst_score': self.utils.calculate_catalyst_score(article.get('title', ''), self.config.data)
                    }
                    news_items.append(news_item)
                else:
                    filtered_reasons['no_symbol'] += 1
                    print(f"[DEBUG] Article {i+1}: ❌ NO SYMBOL - {title[:60]}...")

            # Print summary
            print(f"\n[DEBUG] Filtering Summary:")
            print(f"  ❌ Old news (>7 days): {filtered_reasons['old_news']}")
            print(f"  ❌ No symbol found: {filtered_reasons['no_symbol']}")
            print(f"  ❌ Gossip without catalyst: {filtered_reasons['gossip']}")
            print(f"  ✅ Passed filters: {filtered_reasons['passed']}")
            print(f"  📰 Total news items: {len(news_items)}\n")
            
            if not news_items:
                print("[INFO] Saurav NewsAPI: No recent relevant news found (filtered out old/gossip articles)")
            
            return news_items

        except Exception as e:
            print(f"❌ Saurav NewsAPI error: {e}")
            # DO NOT generate fake news - return empty list for safety
            return []

    async def scan_marketaux(self, symbols: List[str] = None) -> List[Dict[str, Any]]:
        """Scan Marketaux API for symbol-specific news"""
        if not symbols:
            return []

        all_news = []
        for symbol in symbols[:3]:  # Limit symbols for API rate limits
            url = f"https://api.marketaux.com/v1/news/all?symbols={symbol}&filter_entities=true&limit=5"

            response = self._retry_request(requests.get, url)
            if response is None:
                print(f"❌ Marketaux API: All retry attempts failed for {symbol}")
                continue

            try:
                data = response.json()
                articles = data.get('data', [])

                for article in articles:
                    text = self.utils.clean_news_text(
                        article.get('title', '') + ' ' + article.get('description', '')
                    )

                    news_item = {
                        'title': self.utils.clean_news_text(article.get('title', '')),
                        'source': 'marketaux',
                        'symbol': symbol,
                        'sector': self.utils.get_sector_from_symbol(symbol, self.company_db),
                        'timestamp': self.utils.format_timestamp(article.get('published_at')),
                        'url': article.get('url', ''),
                        'current_price': 0.0,  # Real price would come from market data API
                        'strike': 0.0,        # Real strike would come from options API
                        'sentiment': self.utils.calculate_sentiment(text),
                        'catalyst_score': self.utils.calculate_catalyst_score(article.get('title', ''), self.config.data)
                    }
                    all_news.append(news_item)

            except Exception as e:
                print(f"❌ Marketaux API error for {symbol}: {e}")
                # DO NOT generate fake news - return empty for safety

        # Return only real news, no fallback
        return all_news

    async def scan_yahoo_rss(self, symbols: List[str] = None) -> List[Dict[str, Any]]:
        """Scan Yahoo Finance RSS feeds"""
        if not symbols:
            return []

        all_news = []
        for symbol in symbols[:3]:
            url = f"https://feeds.finance.yahoo.com/rss/2.0/headline?s={symbol}"

            response = self._retry_request(requests.get, url)
            if response is None:
                print(f"❌ Yahoo RSS: All retry attempts failed for {symbol}")
                continue

            try:
                # Parse RSS XML
                root = ET.fromstring(response.content)
                items = root.findall('.//item')

                for item in items[:3]:  # Top 3 articles per symbol
                    title_elem = item.find('title')
                    desc_elem = item.find('description')

                    title = title_elem.text if title_elem is not None else ''
                    description = desc_elem.text if desc_elem is not None else ''

                    text = self.utils.clean_news_text(title + ' ' + description)

                    news_item = {
                        'title': self.utils.clean_news_text(title),
                        'source': 'yahoo_rss',
                        'symbol': symbol,
                        'sector': self.utils.get_sector_from_symbol(symbol, self.company_db),
                        'timestamp': self.utils.format_timestamp(None),  # RSS doesn't always have pubDate
                        'url': item.find('link').text if item.find('link') is not None else '',
                        'current_price': 0.0,  # Real price would come from market data API
                        'strike': 0.0,        # Real strike would come from options API
                        'sentiment': self.utils.calculate_sentiment(text),
                        'catalyst_score': self.utils.calculate_catalyst_score(title, self.config.data)
                    }
                    all_news.append(news_item)

            except Exception as e:
                print(f"❌ Yahoo RSS error for {symbol}: {e}")

        # Return only real news, no fallback
        return all_news

    async def scan_reuters_rss(self) -> List[Dict[str, Any]]:
        """Scan Reuters RSS feed"""
        # Reuters Business News RSS (working alternative)
        url = "https://news.google.com/rss/search?q=site:reuters.com+business&hl=en-US&gl=US&ceid=US:en"

        response = self._retry_request(requests.get, url)
        if response is None:
            print("❌ Reuters RSS: All retry attempts failed")
            return []

        try:
            # Parse RSS XML
            root = ET.fromstring(response.content)
            items = root.findall('.//item')

            news_items = []
            for item in items[:5]:  # Top 5 articles
                title_elem = item.find('title')
                desc_elem = item.find('description')

                title = title_elem.text if title_elem is not None else ''
                description = desc_elem.text if desc_elem is not None else ''

                text = self.utils.clean_news_text(title + ' ' + description)
                symbol = self.utils.extract_symbol_from_text(text, self.company_db)

                if symbol:
                    news_item = {
                        'title': self.utils.clean_news_text(title),
                        'source': 'reuters_rss',
                        'symbol': symbol,
                        'sector': self.utils.get_sector_from_symbol(symbol, self.company_db),
                        'timestamp': self.utils.format_timestamp(None),
                        'url': item.find('link').text if item.find('link') is not None else '',
                        'current_price': 0.0,  # Real price would come from market data API
                        'strike': 0.0,        # Real strike would come from options API
                        'sentiment': self.utils.calculate_sentiment(text),
                        'catalyst_score': self.utils.calculate_catalyst_score(title, self.config.data)
                    }
                    news_items.append(news_item)

            return news_items

        except Exception as e:
            print(f"❌ Reuters RSS error: {e}")
            # DO NOT generate fake news - return empty list for safety
            return []

    async def scan_bbc_rss(self) -> List[Dict[str, Any]]:
        """Scan BBC Business RSS feed"""
        url = "http://feeds.bbci.co.uk/news/business/rss.xml"

        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()

            # Parse RSS XML
            root = ET.fromstring(response.content)
            items = root.findall('.//item')

            news_items = []
            for item in items[:5]:
                title_elem = item.find('title')
                desc_elem = item.find('description')

                title = title_elem.text if title_elem is not None else ''
                description = desc_elem.text if desc_elem is not None else ''

                text = self.utils.clean_news_text(title + ' ' + description)
                symbol = self.utils.extract_symbol_from_text(text, self.company_db)

                if symbol:
                    news_item = {
                        'title': self.utils.clean_news_text(title),
                        'source': 'bbc_rss',
                        'symbol': symbol,
                        'sector': self.utils.get_sector_from_symbol(symbol, self.company_db),
                        'timestamp': self.utils.format_timestamp(None),
                        'url': item.find('link').text if item.find('link') is not None else '',
                        'current_price': 0.0,  # Real price would come from market data API
                        'strike': 0.0,        # Real strike would come from options API
                        'sentiment': self.utils.calculate_sentiment(text),
                        'catalyst_score': self.utils.calculate_catalyst_score(title, self.config.data)
                    }
                    news_items.append(news_item)

            return news_items

        except Exception as e:
            print(f"❌ BBC RSS error: {e}")
            # DO NOT generate fake news - return empty list for safety
            return []

    async def scan_cnbc_rss(self) -> List[Dict[str, Any]]:
        """Scan CNBC RSS feed"""
        url = "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=100003114"

        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()

            # Parse RSS XML
            root = ET.fromstring(response.content)
            items = root.findall('.//item')

            news_items = []
            for item in items[:5]:
                title_elem = item.find('title')
                desc_elem = item.find('description')

                title = title_elem.text if title_elem is not None else ''
                description = desc_elem.text if desc_elem is not None else ''

                text = self.utils.clean_news_text(title + ' ' + description)
                symbol = self.utils.extract_symbol_from_text(text, self.company_db)

                if symbol:
                    news_item = {
                        'title': self.utils.clean_news_text(title),
                        'source': 'cnbc_rss',
                        'symbol': symbol,
                        'sector': self.utils.get_sector_from_symbol(symbol, self.company_db),
                        'timestamp': self.utils.format_timestamp(None),
                        'url': item.find('link').text if item.find('link') is not None else '',
                        'current_price': 0.0,  # Real price would come from market data API
                        'strike': 0.0,        # Real strike would come from options API
                        'sentiment': self.utils.calculate_sentiment(text),
                        'catalyst_score': self.utils.calculate_catalyst_score(title, self.config.data)
                    }
                    news_items.append(news_item)

            return news_items

        except Exception as e:
            print(f"❌ CNBC RSS error: {e}")
            # DO NOT generate fake news - return empty list for safety
            return []

    async def scan_industry_news(self, industry: str) -> List[Dict[str, Any]]:
        """Scan news specifically for a target industry using industry-specific keywords"""
        if not self.company_db or not self.utils:
            return []

        # Industry-specific keywords for better targeting
        industry_keywords = {
            'Tech/AI': ['AI', 'artificial intelligence', 'chip', 'semiconductor', 'tech', 'earnings', 'quarterly', 'revenue', 'guidance', 'deal', 'partnership', 'acquisition'],
            'Energy': ['oil', 'energy', 'gas', 'sanctions', 'permian', 'pipeline', 'drilling', 'refinery', 'crude', 'barrel', 'opec', 'renewable'],
            'Consumer/Food': ['retail', 'consumer', 'sales', 'earnings', 'quarterly', 'revenue', 'growth', 'market share', 'brand', 'product launch'],
            'EV/Auto': ['electric vehicle', 'EV', 'tesla', 'delivery', 'battery', 'charging', 'autonomous', 'auto sales', 'car', 'vehicle'],
            'Biotech/Health': ['clinical trial', 'FDA', 'drug', 'treatment', 'breakthrough', 'health', 'medical', 'biotech', 'pharma'],
            'Politics/Finance': ['interest rate', 'fed', 'banking', 'financial', 'policy', 'regulation', 'tariff', 'trade', 'election'],
            'Mining/Metals': ['mining', 'metal', 'commodity', 'rare earth', 'copper', 'gold', 'mineral', 'extraction'],
            'Crypto/Blockchain': ['bitcoin', 'ethereum', 'crypto', 'cryptocurrency', 'blockchain', 'BTC', 'ETH', 'mining', 'coinbase', 'digital currency', 'web3', 'defi', 'NFT', 'token', 'wallet', 'exchange']
        }

        keywords = industry_keywords.get(industry, [])
        if not keywords:
            return []

        # Get symbols for this industry
        # Use the validator from core module - fallback to general symbols if not available
        try:
            industry_symbols = self.validator.get_industry_symbols(industry) if self.validator else []
        except:
            # Fallback: use general high-volume symbols if validator not available
            industry_symbols = ['AAPL', 'MSFT', 'GOOGL', 'NVDA', 'AMD', 'TSLA', 'AMZN', 'META', 'NFLX', 'CRM']

        # USE FINNHUB FOR REAL-TIME NEWS (not Saurav's 3.5yr old cache!)
        # Get real-time news from Finnhub instead
        try:
            finnhub_articles = self.finnhub.get_market_news(category='general', limit=50)
            
            # Filter by industry keywords
            articles = []
            for article in finnhub_articles:
                title_lower = article.get('title', '').lower()
                summary_lower = article.get('summary', '').lower()
                full_text = f"{title_lower} {summary_lower}"
                
                # Check if any industry keyword matches
                if any(keyword.lower() in full_text for keyword in keywords):
                    articles.append({
                        'title': article.get('title', ''),
                        'publishedAt': article.get('timestamp', ''),
                        'description': article.get('summary', ''),
                        'source': {'name': 'Finnhub'},
                        'url': article.get('url', ''),
                        'related': article.get('related', '')
                    })

            news_items = []
            from datetime import datetime, timedelta
            
            # Only accept news from last 7 days
            cutoff_date = datetime.now() - timedelta(days=7)
            
            for article in articles[:10]:  # More articles for industry targeting
                # Check date first
                published_at = article.get('publishedAt', '')
                try:
                    if published_at:
                        article_date = datetime.fromisoformat(published_at.replace('Z', '+00:00'))
                        if article_date < cutoff_date:
                            continue  # Skip old news
                except:
                    pass
                
                title = article.get('title', '')
                description = article.get('description', '')
                full_text = self.utils.clean_news_text(title + ' ' + description)

                # Skip gossip/opinion without catalyst
                title_lower = title.lower()
                gossip_keywords = ['questions', 'opinion', 'thinks', 'believes', 'says', 'claims']
                if any(word in title_lower for word in gossip_keywords):
                    catalyst_keywords = ['earnings', 'revenue', 'profit', 'deal', 'merger', 'acquisition', 
                                        'partnership', 'contract', 'fda', 'approval', 'launch', 'breakthrough']
                    if not any(word in title_lower for word in catalyst_keywords):
                        continue  # Skip gossip

                # Extract symbols from text
                symbol = self.utils.extract_symbol_from_text(full_text, self.company_db)

                # Also check if any industry symbols appear in text
                if not symbol:
                    for industry_symbol in industry_symbols:
                        if industry_symbol in full_text.upper():
                            symbol = industry_symbol
                            break

                if symbol:
                    # Check if article matches industry keywords
                    matches_industry = any(keyword.lower() in full_text.lower() for keyword in keywords)

                    if matches_industry:
                        news_item = {
                            'title': self.utils.clean_news_text(title),
                            'source': f'industry_{industry.lower()}',
                            'symbol': symbol,
                            'sector': self.utils.get_sector_from_symbol(symbol, self.company_db),
                            'industry': industry,
                            'timestamp': self.utils.format_timestamp(article.get('publishedAt')),
                            'url': article.get('url', ''),
                            'current_price': 0.0,  # Real price would come from market data API
                            'strike': 0.0,        # Real strike would come from options API
                            'sentiment': self.utils.calculate_sentiment(full_text),
                            'catalyst_score': self.utils.calculate_catalyst_score(title, self.config.data),
                            'industry_targeted': True
                        }
                        news_items.append(news_item)

            print(f"📊 Industry scan ({industry}): Found {len(news_items)} relevant items")
            return news_items

        except Exception as e:
            print(f"❌ Industry scan error for {industry}: {e}")
            # DO NOT generate fake news - return empty list for safety
            return []

    async def scan_reddit_wallstreetbets_rss(self) -> List[Dict[str, Any]]:
        """
        Scan Reddit WallStreetBets RSS for meme stock sentiment and viral hype
        Perfect for quick trades on AI/food sectors, filters for high-vol tickers
        """
        url = "https://www.reddit.com/r/wallstreetbets/.rss"
        
        try:
            # Reddit RSS requires a user agent
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            # Parse RSS XML
            root = ET.fromstring(response.content)
            
            # Reddit RSS uses Atom format
            namespace = {'atom': 'http://www.w3.org/2005/Atom'}
            entries = root.findall('.//atom:entry', namespace)
            
            news_items = []
            for entry in entries[:10]:  # Top 10 posts
                title_elem = entry.find('atom:title', namespace)
                content_elem = entry.find('atom:content', namespace)
                link_elem = entry.find('atom:link', namespace)
                
                title = title_elem.text if title_elem is not None else ''
                content = content_elem.text if content_elem is not None else ''
                
                # Clean HTML from content
                import re
                content_clean = re.sub('<[^<]+?>', '', content) if content else ''
                
                text = self.utils.clean_news_text(title + ' ' + content_clean)
                symbol = self.utils.extract_symbol_from_text(text, self.company_db)
                
                # WSB often mentions tickers directly - try to extract
                if not symbol:
                    # Look for common ticker patterns: $TSLA, TSLA, etc.
                    ticker_match = re.search(r'\$?([A-Z]{2,5})\b', title)
                    if ticker_match:
                        potential_symbol = ticker_match.group(1)
                        # Validate it's a real ticker
                        if self.company_db and potential_symbol in self.company_db:
                            symbol = potential_symbol
                
                if symbol:
                    # Calculate sentiment - WSB posts are often extreme
                    sentiment = self.utils.calculate_sentiment(text)
                    
                    # Detect meme stock indicators
                    meme_keywords = ['moon', 'squeeze', 'yolo', 'diamond hands', 'apes', 'rocket', '🚀', 'to the moon']
                    is_meme = any(keyword.lower() in text.lower() for keyword in meme_keywords)
                    
                    news_item = {
                        'title': self.utils.clean_news_text(title),
                        'source': 'reddit_wsb',
                        'symbol': symbol,
                        'sector': self.utils.get_sector_from_symbol(symbol, self.company_db),
                        'timestamp': self.utils.format_timestamp(None),
                        'url': link_elem.get('href') if link_elem is not None else '',
                        'current_price': 0.0,  # Real price would come from market data API
                        'strike': 0.0,        # Real strike would come from options API
                        'sentiment': sentiment,
                        'catalyst_score': self.utils.calculate_catalyst_score(title, self.config.data),
                        'is_meme_stock': is_meme,
                        'social_buzz': True  # Flag for high social media attention
                    }
                    news_items.append(news_item)
            
            if news_items:
                print(f"📱 Reddit WSB: Found {len(news_items)} posts with tickers")
            
            return news_items
            
        except Exception as e:
            print(f"❌ Reddit WSB RSS error: {e}")
            # DO NOT generate fake news - return empty list for safety
            return []
    
    async def scan_finnhub_news(self) -> List[Dict[str, Any]]:
        """Scan Finnhub for REAL-TIME market news"""
        try:
            # Get latest market news from Finnhub
            finnhub_articles = self.finnhub.get_market_news(category='general', limit=50)
            
            if not finnhub_articles:
                print("[INFO] Finnhub: No recent news found")
                return []
            
            news_items = []
            print(f"[DEBUG] Finnhub: Processing {len(finnhub_articles)} articles")
            
            for article in finnhub_articles:
                # Extract symbols from related field
                related_symbols = article.get('related', '').split(',')
                
                for symbol in related_symbols:
                    symbol = symbol.strip().upper()
                    
                    if not symbol or len(symbol) > 5:
                        continue
                    
                    # Check if symbol is in our company database
                    if self.company_db and symbol not in self.company_db:
                        continue
                    
                    # Create news item
                    news_item = {
                        'title': article.get('title', ''),
                        'source': 'finnhub_realtime',
                        'symbol': symbol,
                        'sector': self.utils.get_sector_from_symbol(symbol, self.company_db) if self.utils else 'Unknown',
                        'timestamp': article.get('timestamp', datetime.now().isoformat()),
                        'url': article.get('url', ''),
                        'summary': article.get('summary', ''),
                        'current_price': 0.0,  # Will be fetched by price_fetcher
                        'strike': 0.0,
                        'sentiment': 0.6,  # Default positive for news mentions
                        'catalyst_score': 0.5,
                        'is_realtime': True  # Flag as real-time news
                    }
                    news_items.append(news_item)
                    
                    # Limit to avoid duplicates
                    if len(news_items) >= 20:
                        break
                
                if len(news_items) >= 20:
                    break
            
            print(f"✅ Finnhub: Found {len(news_items)} relevant news items with tickers")
            return news_items
            
        except Exception as e:
            print(f"❌ Finnhub scanning error: {e}")
            return []
    
    def _generate_industry_fallback_news(self, industry: str) -> List[Dict[str, Any]]:
        """REMOVED: This function was dangerous for real trading - generates fake news"""
        print(f"⚠️ WARNING: Fallback news generation disabled for safety")
        return []
