"""
Multi-Source News Aggregator
Enhances RSS feeds with multiple free news sources for comprehensive stock news coverage
"""

import requests
import json
import sqlite3
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import yfinance as yf
import time


class MultiSourceNewsAggregator:
    """Aggregates news from multiple sources for comprehensive stock coverage"""
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.db_path = "news_cache.db"
        self._init_database()
        
        # API configurations (free tiers)
        self.newsapi_key = self.config.get("newsapi_key", None)
        self.gnews_api_key = self.config.get("gnews_api_key", None)
        
        # Rate limiting
        self.last_api_calls = {}
        self.rate_limits = {
            "newsapi": 1000,  # 1000 requests per day
            "gnews": 100,     # 100 requests per day
            "twitter": 300     # 300 requests per 3 hours
        }
    
    def _init_database(self):
        """Initialize news cache database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS news_cache (
                id INTEGER PRIMARY KEY,
                ticker TEXT NOT NULL,
                source TEXT NOT NULL,
                title TEXT NOT NULL,
                url TEXT UNIQUE NOT NULL,
                summary TEXT,
                sentiment REAL,
                published TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS api_usage (
                api_name TEXT PRIMARY KEY,
                daily_count INTEGER DEFAULT 0,
                last_reset TEXT DEFAULT CURRENT_DATE
            )
        """)
        
        conn.commit()
        conn.close()
    
    def search_stock_news(self, ticker: str, hours_back: int = 24) -> List[Dict]:
        """Search for news about specific stock across all sources"""
        
        # Get company name for broader search
        try:
            stock = yf.Ticker(ticker)
            company_name = stock.info.get("shortName", ticker).split()[0]
        except:
            company_name = ticker
        
        all_news = []
        
        # Source 1: NewsAPI (if key available)
        if self.newsapi_key:
            newsapi_news = self._search_newsapi(ticker, company_name, hours_back)
            all_news.extend(newsapi_news)
        
        # Source 2: GNews API (if key available)
        if self.gnews_api_key:
            gnews_news = self._search_gnews(ticker, company_name, hours_back)
            all_news.extend(gnews_news)
        
        # Source 3: Google News scraping (always available)
        google_news = self._scrape_google_news(ticker, company_name, hours_back)
        all_news.extend(google_news)
        
        # Source 4: Yahoo Finance news (always available)
        yahoo_news = self._get_yahoo_finance_news(ticker, hours_back)
        all_news.extend(yahoo_news)
        
        # Source 5: Twitter/Reddit mentions (if available)
        social_news = self._get_social_mentions(ticker, hours_back)
        all_news.extend(social_news)
        
        # Remove duplicates and rank by relevance
        unique_news = self._deduplicate_and_rank(all_news, ticker)
        
        # Cache results
        self._cache_news(unique_news, ticker)
        
        return unique_news[:20]  # Return top 20 most relevant
    
    def _search_newsapi(self, ticker: str, company_name: str, hours_back: int) -> List[Dict]:
        """Search using NewsAPI.org"""
        
        if not self._check_rate_limit("newsapi"):
            return []
        
        try:
            # Build search query
            query = f"{ticker} OR {company_name}"
            
            # Calculate date range
            from_date = (datetime.now() - timedelta(hours=hours_back)).strftime("%Y-%m-%d")
            
            url = "https://newsapi.org/v2/everything"
            params = {
                "q": query,
                "from": from_date,
                "sortBy": "relevancy",
                "language": "en",
                "pageSize": 50,
                "apiKey": self.newsapi_key
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                articles = []
                
                for article in data.get("articles", []):
                    articles.append({
                        "source": "NewsAPI",
                        "title": article.get("title", ""),
                        "url": article.get("url", ""),
                        "summary": article.get("description", ""),
                        "published": article.get("publishedAt", ""),
                        "sentiment": self._analyze_sentiment(article.get("title", "") + " " + article.get("description", "")),
                        "relevance": self._calculate_relevance(article.get("title", "") + " " + article.get("description", ""), ticker, company_name)
                    })
                
                self._update_api_usage("newsapi")
                return articles
                
        except Exception as e:
            print(f"NewsAPI error: {e}")
        
        return []
    
    def _search_gnews(self, ticker: str, company_name: str, hours_back: int) -> List[Dict]:
        """Search using GNews API"""
        
        if not self._check_rate_limit("gnews"):
            return []
        
        try:
            query = f"{ticker} OR {company_name}"
            
            url = "https://gnews.io/api/v4/search"
            params = {
                "q": query,
                "lang": "en",
                "country": "us",
                "max": 50,
                "apikey": self.gnews_api_key
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                articles = []
                
                for article in data.get("articles", []):
                    # Filter by date
                    published = datetime.fromisoformat(article.get("publishedAt", "").replace("Z", "+00:00"))
                    if datetime.now() - published > timedelta(hours=hours_back):
                        continue
                    
                    articles.append({
                        "source": "GNews",
                        "title": article.get("title", ""),
                        "url": article.get("url", ""),
                        "summary": article.get("description", ""),
                        "published": article.get("publishedAt", ""),
                        "sentiment": self._analyze_sentiment(article.get("title", "") + " " + article.get("description", "")),
                        "relevance": self._calculate_relevance(article.get("title", "") + " " + article.get("description", ""), ticker, company_name)
                    })
                
                self._update_api_usage("gnews")
                return articles
                
        except Exception as e:
            print(f"GNews error: {e}")
        
        return []
    
    def _scrape_google_news(self, ticker: str, company_name: str, hours_back: int) -> List[Dict]:
        """Scrape Google News (no API key needed)"""
        
        try:
            query = f"{ticker} OR {company_name}"
            
            # Google News RSS feed
            url = f"https://news.google.com/rss/search?q={query}&hl=en-US&gl=US&ceid=US:en"
            
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                # Parse RSS (simplified)
                items = re.findall(r'<item>.*?</item>', response.text, re.DOTALL)
                articles = []
                
                for item in items[:20]:  # Limit to 20
                    title_match = re.search(r'<title>(.*?)</title>', item)
                    link_match = re.search(r'<link>(.*?)</link>', item)
                    desc_match = re.search(r'<description>(.*?)</description>', item)
                    date_match = re.search(r'<pubDate>(.*?)</pubDate>', item)
                    
                    if title_match and link_match:
                        title = self._clean_html(title_match.group(1))
                        url = link_match.group(1)
                        summary = self._clean_html(desc_match.group(1)) if desc_match else ""
                        published = date_match.group(1) if date_match else ""
                        
                        articles.append({
                            "source": "Google News",
                            "title": title,
                            "url": url,
                            "summary": summary,
                            "published": published,
                            "sentiment": self._analyze_sentiment(title + " " + summary),
                            "relevance": self._calculate_relevance(title + " " + summary, ticker, company_name)
                        })
                
                return articles
                
        except Exception as e:
            print(f"Google News scraping error: {e}")
        
        return []
    
    def _get_yahoo_finance_news(self, ticker: str, hours_back: int) -> List[Dict]:
        """Get news from Yahoo Finance"""
        
        try:
            stock = yf.Ticker(ticker)
            news = stock.news
            
            if news:
                articles = []
                cutoff_time = datetime.now() - timedelta(hours=hours_back)
                
                for item in news:
                    # Check if within time range
                    pub_time = datetime.fromtimestamp(item.get("providerPublishTime", 0))
                    if pub_time < cutoff_time:
                        continue
                    
                    articles.append({
                        "source": "Yahoo Finance",
                        "title": item.get("title", ""),
                        "url": item.get("link", ""),
                        "summary": item.get("summary", ""),
                        "published": pub_time.isoformat(),
                        "sentiment": self._analyze_sentiment(item.get("title", "") + " " + item.get("summary", "")),
                        "relevance": self._calculate_relevance(item.get("title", "") + " " + item.get("summary", ""), ticker, "")
                    })
                
                return articles
                
        except Exception as e:
            print(f"Yahoo Finance news error: {e}")
        
        return []
    
    def _get_social_mentions(self, ticker: str, hours_back: int) -> List[Dict]:
        """Get mentions from social sources (Reddit, etc.)"""
        
        social_news = []
        
        # Reddit mentions (if available)
        try:
            # This would use the existing Reddit client
            # For now, return empty
            pass
        except:
            pass
        
        return social_news
    
    def _analyze_sentiment(self, text: str) -> float:
        """Simple sentiment analysis (-1 to 1)"""
        
        positive_words = ["up", "rise", "gain", "beat", "strong", "growth", "bullish", "buy", "upgrade"]
        negative_words = ["down", "fall", "drop", "miss", "weak", "decline", "bearish", "sell", "downgrade"]
        
        text_lower = text.lower()
        
        pos_count = sum(1 for word in positive_words if word in text_lower)
        neg_count = sum(1 for word in negative_words if word in text_lower)
        
        if pos_count + neg_count == 0:
            return 0.0
        
        return (pos_count - neg_count) / (pos_count + neg_count)
    
    def _calculate_relevance(self, text: str, ticker: str, company_name: str) -> float:
        """Calculate relevance score for the article"""
        
        text_lower = text.lower()
        ticker_lower = ticker.lower()
        name_lower = company_name.lower()
        
        score = 0.0
        
        # Exact ticker match
        if ticker_lower in text_lower:
            score += 2.0
        
        # Company name match
        if name_lower in text_lower:
            score += 1.5
        
        # Financial keywords increase relevance
        financial_keywords = ["earnings", "revenue", "profit", "loss", "guidance", "forecast", "analyst", "rating"]
        for keyword in financial_keywords:
            if keyword in text_lower:
                score += 0.5
        
        return score
    
    def _deduplicate_and_rank(self, articles: List[Dict], ticker: str) -> List[Dict]:
        """Remove duplicates and rank by relevance"""
        
        # Remove duplicates based on URL similarity
        unique_articles = []
        seen_urls = set()
        
        for article in articles:
            url = article.get("url", "")
            
            # Simple URL deduplication
            url_base = url.split("?")[0]  # Remove query parameters
            
            if url_base not in seen_urls:
                seen_urls.add(url_base)
                unique_articles.append(article)
        
        # Sort by relevance (descending)
        unique_articles.sort(key=lambda x: x.get("relevance", 0), reverse=True)
        
        return unique_articles
    
    def _cache_news(self, articles: List[Dict], ticker: str):
        """Cache news articles in database"""
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for article in articles:
            cursor.execute("""
                INSERT OR IGNORE INTO news_cache 
                (ticker, source, title, url, summary, sentiment, published)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                ticker,
                article.get("source", ""),
                article.get("title", ""),
                article.get("url", ""),
                article.get("summary", ""),
                article.get("sentiment", 0),
                article.get("published", "")
            ))
        
        conn.commit()
        conn.close()
    
    def _check_rate_limit(self, api_name: str) -> bool:
        """Check if API rate limit allows request"""
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT daily_count, last_reset FROM api_usage WHERE api_name = ?", (api_name,))
        result = cursor.fetchone()
        
        today = datetime.now().date().isoformat()
        
        if not result:
            cursor.execute("INSERT INTO api_usage (api_name, daily_count, last_reset) VALUES (?, 1, ?)",
                         (api_name, today))
            conn.commit()
            conn.close()
            return True
        
        count, last_reset = result
        
        # Reset if it's a new day
        if last_reset != today:
            cursor.execute("UPDATE api_usage SET daily_count = 1, last_reset = ? WHERE api_name = ?",
                         (today, api_name))
            conn.commit()
            conn.close()
            return True
        
        # Check limit
        if count >= self.rate_limits.get(api_name, 100):
            conn.close()
            return False
        
        # Increment count
        cursor.execute("UPDATE api_usage SET daily_count = daily_count + 1 WHERE api_name = ?", (api_name,))
        conn.commit()
        conn.close()
        return True
    
    def _update_api_usage(self, api_name: str):
        """Update API usage counter"""
        # Already handled in _check_rate_limit
        pass
    
    def _clean_html(self, text: str) -> str:
        """Clean HTML tags from text"""
        # Simple HTML tag removal
        clean = re.sub(r'<[^>]+>', '', text)
        return clean.strip()
    
    def get_news_summary(self, ticker: str) -> str:
        """Get human-readable news summary"""
        
        news = self.search_stock_news(ticker)
        
        if not news:
            return f"No recent news found for {ticker}"
        
        summary = f"📰 {ticker} News Summary (Last 24 Hours)\n"
        summary += "="*50 + "\n\n"
        
        # Sentiment analysis
        sentiments = [n.get("sentiment", 0) for n in news]
        avg_sentiment = sum(sentiments) / len(sentiments) if sentiments else 0
        
        if avg_sentiment > 0.2:
            sentiment_desc = "🟢 Positive"
        elif avg_sentiment < -0.2:
            sentiment_desc = "🔴 Negative"
        else:
            sentiment_desc = "🟡 Neutral"
        
        summary += f"Overall Sentiment: {sentiment_desc} ({avg_sentiment:.2f})\n"
        summary += f"Articles Found: {len(news)}\n\n"
        
        # Top articles
        for i, article in enumerate(news[:5], 1):
            summary += f"{i}. {article['title']}\n"
            summary += f"   Source: {article['source']}\n"
            summary += f"   Relevance: {article['relevance']:.1f}/10\n"
            if article.get('summary'):
                summary += f"   Summary: {article['summary'][:150]}...\n"
            summary += f"   URL: {article['url']}\n\n"
        
        return summary


# Test the aggregator
if __name__ == "__main__":
    # Configuration - add your API keys here
    config = {
        # "newsapi_key": "YOUR_NEWSAPI_KEY",
        # "gnews_api_key": "YOUR_GNEWS_API_KEY"
    }
    
    aggregator = MultiSourceNewsAggregator(config)
    
    # Test with a stock
    ticker = "AAPL"
    print(f"Searching news for {ticker}...")
    
    news_summary = aggregator.get_news_summary(ticker)
    print(news_summary)
