"""
Finnhub Real-Time News Integration
Uses your API key: d2r5jkhr01qlk22rpl70d2r5jkhr01qlk22rpl7g
"""
import requests
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from dotenv import load_dotenv

load_dotenv()

class FinnhubNews:
    """Real-time news from Finnhub API"""
    
    def __init__(self):
        self.api_key = os.getenv('FINNHUB_API_KEY', '')
        self.base_url = "https://finnhub.io/api/v1"
        
        if not self.api_key:
            print("⚠️ Finnhub API key not found in .env")
    
    def get_market_news(self, category='general', limit=50) -> List[Dict]:
        """
        Get latest market news from Finnhub
        Categories: general, forex, crypto, merger
        """
        if not self.api_key:
            return []
        
        url = f"{self.base_url}/news"
        params = {
            'category': category,
            'token': self.api_key
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            news_data = response.json()
            
            # Filter for recent news only (last 24 hours)
            cutoff = datetime.now() - timedelta(hours=24)
            
            formatted_news = []
            for article in news_data[:limit]:
                # Finnhub timestamps are in Unix seconds
                article_date = datetime.fromtimestamp(article.get('datetime', 0))
                
                if article_date < cutoff:
                    continue
                
                formatted_news.append({
                    'title': article.get('headline', ''),
                    'summary': article.get('summary', ''),
                    'source': f"finnhub_{article.get('source', 'unknown')}",
                    'url': article.get('url', ''),
                    'timestamp': article_date.isoformat(),
                    'related': article.get('related', ''),  # Stock symbols
                    'image': article.get('image', ''),
                    'category': article.get('category', 'general')
                })
            
            print(f"✅ Finnhub: Found {len(formatted_news)} recent news articles")
            return formatted_news
            
        except Exception as e:
            print(f"❌ Finnhub news error: {e}")
            return []
    
    def get_company_news(self, symbol: str, days_back=7) -> List[Dict]:
        """Get news for a specific company"""
        if not self.api_key:
            return []
        
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        
        url = f"{self.base_url}/company-news"
        params = {
            'symbol': symbol,
            'from': start_date.strftime('%Y-%m-%d'),
            'to': end_date.strftime('%Y-%m-%d'),
            'token': self.api_key
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            news_data = response.json()
            
            formatted_news = []
            for article in news_data[:20]:  # Limit to 20 most recent
                article_date = datetime.fromtimestamp(article.get('datetime', 0))
                
                formatted_news.append({
                    'symbol': symbol,
                    'title': article.get('headline', ''),
                    'summary': article.get('summary', ''),
                    'source': f"finnhub_{article.get('source', 'unknown')}",
                    'url': article.get('url', ''),
                    'timestamp': article_date.isoformat(),
                    'image': article.get('image', ''),
                    'category': article.get('category', 'company')
                })
            
            return formatted_news
            
        except Exception as e:
            print(f"❌ Finnhub company news error for {symbol}: {e}")
            return []
    
    def get_trending_symbols_from_news(self) -> Dict[str, int]:
        """Extract trending symbols from news mentions"""
        news = self.get_market_news(limit=100)
        
        symbol_counts = {}
        for article in news:
            # Extract symbols from 'related' field (comma-separated)
            related_symbols = article.get('related', '').split(',')
            for symbol in related_symbols:
                symbol = symbol.strip().upper()
                if symbol and len(symbol) <= 5:  # Valid stock symbols
                    symbol_counts[symbol] = symbol_counts.get(symbol, 0) + 1
        
        # Sort by mention count
        sorted_symbols = dict(sorted(symbol_counts.items(), key=lambda x: x[1], reverse=True))
        
        return sorted_symbols

# Global instance
_finnhub = None

def get_finnhub():
    """Get or create global Finnhub instance"""
    global _finnhub
    if _finnhub is None:
        _finnhub = FinnhubNews()
    return _finnhub
