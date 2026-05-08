"""
Commodity News Scanner
Adds support for scanning commodity-specific news including silver (SLV)
"""

import requests
import asyncio
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
import re

class CommodityNewsScanner:
    """Scans for commodity-specific news, especially precious metals"""
    
    def __init__(self, config):
        self.config = config
        
    async def scan_commodity_news(self) -> List[Dict[str, Any]]:
        """Scan for commodity news from multiple sources"""
        
        news_items = []
        
        # Source 1: Investing.com commodities news
        try:
            investing_news = await self.scan_investing_commodities()
            news_items.extend(investing_news)
            print(f"📈 Investing.com: Found {len(investing_news)} commodity news items")
        except Exception as e:
            print(f"⚠️ Investing.com error: {e}")
        
        # Source 2: Kitco (precious metals specialist)
        try:
            kitco_news = await self.scan_kitco_news()
            news_items.extend(kitco_news)
            print(f"🥈 Kitco: Found {len(kitco_news)} precious metals news")
        except Exception as e:
            print(f"⚠️ Kitco error: {e}")
        
        # Source 3: Financial Times commodities
        try:
            ft_news = await self.scan_ft_commodities()
            news_items.extend(ft_news)
            print(f"📊 FT: Found {len(ft_news)} commodities news")
        except Exception as e:
            print(f"⚠️ FT error: {e}")
        
        # Filter for silver-specific news
        silver_news = []
        for item in news_items:
            if self.is_silver_related(item):
                # Map to SLV ticker
                item['symbol'] = 'SLV'
                item['confidence'] = 80  # High confidence for direct silver news
                silver_news.append(item)
        
        print(f"🥈 Found {len(silver_news)} silver-specific news items")
        return silver_news
    
    async def scan_investing_commodities(self) -> List[Dict[str, Any]]:
        """Scan Investing.com commodities RSS feed"""
        url = "https://www.investing.com/rss/news_301.rss"
        
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            import xml.etree.ElementTree as ET
            root = ET.fromstring(response.content)
            
            news_items = []
            for item in root.findall('.//item')[:10]:  # Latest 10 items
                title = item.find('title').text or ''
                description = item.find('description').text or ''
                link = item.find('link').text or ''
                
                # Clean HTML from description
                description = re.sub(r'<[^>]+>', '', description)
                
                news_items.append({
                    'title': title,
                    'summary': description,
                    'source': 'investing_commodities',
                    'url': link,
                    'timestamp': datetime.now().isoformat(),
                    'text': f"{title} {description}"
                })
            
            return news_items
            
        except Exception as e:
            print(f"Error scanning Investing.com: {e}")
            return []
    
    async def scan_kitco_news(self) -> List[Dict[str, Any]]:
        """Scan Kitco for precious metals news"""
        url = "https://www.kitco.com/news/rss"
        
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            import xml.etree.ElementTree as ET
            root = ET.fromstring(response.content)
            
            news_items = []
            for item in root.findall('.//item')[:10]:
                title = item.find('title').text or ''
                description = item.find('description').text or ''
                link = item.find('link').text or ''
                
                # Clean HTML
                description = re.sub(r'<[^>]+>', '', description)
                
                news_items.append({
                    'title': title,
                    'summary': description,
                    'source': 'kitco',
                    'url': link,
                    'timestamp': datetime.now().isoformat(),
                    'text': f"{title} {description}"
                })
            
            return news_items
            
        except Exception as e:
            print(f"Error scanning Kitco: {e}")
            return []
    
    async def scan_ft_commodities(self) -> List[Dict[str, Any]]:
        """Scan Financial Times commodities section"""
        # Use a free news API that includes FT commodities
        url = "https://newsapi.org/v2/everything"
        params = {
            'q': 'commodities silver gold OR source:financial-times',
            'language': 'en',
            'sortBy': 'publishedAt',
            'pageSize': '10',
            'apiKey': 'demo'  # Using demo key for now
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                articles = data.get('articles', [])
                
                news_items = []
                for article in articles:
                    news_items.append({
                        'title': article.get('title', ''),
                        'summary': article.get('description', ''),
                        'source': 'ft_commodities',
                        'url': article.get('url', ''),
                        'timestamp': article.get('publishedAt', ''),
                        'text': f"{article.get('title', '')} {article.get('description', '')}"
                    })
                
                return news_items
        except:
            pass
        
        return []
    
    def is_silver_related(self, item: Dict[str, Any]) -> bool:
        """Check if news item is related to silver"""
        
        text = (item.get('title', '') + ' ' + 
                item.get('summary', '') + ' ' + 
                item.get('text', '')).lower()
        
        # Silver keywords
        silver_keywords = [
            'silver', 'slv', 'silver price', 'silver futures',
            'silver spot', 'ounce silver', 'silver etf',
            'precious metals silver', 'silver market',
            'silver rally', 'silver surge', 'silver jump',
            'silver bullion', 'silver coins', 'silver bars'
        ]
        
        # Check for silver keywords
        for keyword in silver_keywords:
            if keyword in text:
                return True
        
        # Check for silver-related companies (mining)
        silver_companies = [
            'wheaton precious metals', 'first majestic silver',
            'pan american silver', 'coeur mining',
            'hecla mining', 'silvercorp metals'
        ]
        
        for company in silver_companies:
            if company in text:
                return True
        
        return False

# Integration function to add to main news engine
def add_commodity_scanner(news_engine):
    """Add commodity scanning to existing news engine"""
    
    commodity_scanner = CommodityNewsScanner(news_engine.config)
    
    # Store reference
    news_engine.commodity_scanner = commodity_scanner
    
    # Add to scanning methods
    original_scan = news_engine.scan_real_news_sources
    
    async def enhanced_scan():
        """Enhanced scan that includes commodities"""
        # Get original news
        original_news = await original_scan()
        
        # Add commodity news
        commodity_news = await commodity_scanner.scan_commodity_news()
        
        # Combine
        all_news = original_news + commodity_news
        
        print(f"📊 Enhanced scan: {len(original_news)} regular + {len(commodity_news)} commodity = {len(all_news)} total")
        
        return all_news
    
    # Replace the method
    news_engine.scan_real_news_sources = enhanced_scan
    
    print("✅ Commodity news scanner added to news engine")
