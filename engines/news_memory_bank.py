"""
Smart Memory Bank for News Storage and Retrieval
Prevents costly repeated lookups and remembers past news for pattern learning
"""

import json
import os
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging

class NewsMemoryBank:
    """
    Smart memory system for storing and retrieving news articles
    Features:
    - Deduplication by content hash
    - Fast lookup cache
    - Historical pattern learning
    - Automatic cleanup of old news
    - Symbol-based indexing
    """
    
    def __init__(self, memory_path: str = 'phasma_core_memory/news_bank'):
        """Initialize memory bank"""
        self.memory_path = memory_path
        self.logger = logging.getLogger(__name__)
        
        # Create memory directories
        os.makedirs(memory_path, exist_ok=True)
        os.makedirs(f"{memory_path}/daily", exist_ok=True)
        os.makedirs(f"{memory_path}/symbols", exist_ok=True)
        os.makedirs(f"{memory_path}/cache", exist_ok=True)
        
        # In-memory cache for fast lookups
        self.cache = {
            'articles': {},      # article_hash -> article_data
            'symbols': {},       # symbol -> list of article_hashes
            'sources': {},       # source -> list of article_hashes
            'duplicates': set()  # hashes of duplicate articles
        }
        
        # Load existing memory
        self._load_memory()
        
        # Statistics
        self.stats = {
            'total_articles': 0,
            'duplicates_prevented': 0,
            'cache_hits': 0,
            'cache_misses': 0
        }
    
    def store_article(self, article: Dict) -> Dict:
        """
        Store article in memory bank with deduplication
        
        Returns:
        {
            'stored': bool,
            'hash': str,
            'is_duplicate': bool,
            'original_date': str (if duplicate)
        }
        """
        try:
            # Generate unique hash for article
            article_hash = self._generate_article_hash(article)
            
            # Check if already stored
            if article_hash in self.cache['articles']:
                self.stats['duplicates_prevented'] += 1
                original = self.cache['articles'][article_hash]
                
                return {
                    'stored': False,
                    'hash': article_hash,
                    'is_duplicate': True,
                    'original_date': original.get('stored_at'),
                    'reason': 'Duplicate article already in memory'
                }
            
            # Add metadata
            article['hash'] = article_hash
            article['stored_at'] = datetime.now().isoformat()
            
            # Store in cache
            self.cache['articles'][article_hash] = article
            
            # Index by symbol
            symbols = article.get('symbols', [])
            if isinstance(symbols, str):
                symbols = [symbols]
            
            for symbol in symbols:
                if symbol:
                    if symbol not in self.cache['symbols']:
                        self.cache['symbols'][symbol] = []
                    self.cache['symbols'][symbol].append(article_hash)
            
            # Index by source
            source = article.get('source', 'unknown')
            if source not in self.cache['sources']:
                self.cache['sources'][source] = []
            self.cache['sources'][source].append(article_hash)
            
            # Persist to disk
            self._persist_article(article)
            
            self.stats['total_articles'] += 1
            
            return {
                'stored': True,
                'hash': article_hash,
                'is_duplicate': False
            }
            
        except Exception as e:
            self.logger.error(f"Error storing article: {e}")
            return {
                'stored': False,
                'error': str(e)
            }
    
    def get_article_by_hash(self, article_hash: str) -> Optional[Dict]:
        """Retrieve article by hash"""
        if article_hash in self.cache['articles']:
            self.stats['cache_hits'] += 1
            return self.cache['articles'][article_hash]
        
        self.stats['cache_misses'] += 1
        return None
    
    def get_articles_by_symbol(
        self, 
        symbol: str, 
        hours_back: int = 24,
        limit: int = 50
    ) -> List[Dict]:
        """Get all articles for a specific symbol"""
        if symbol not in self.cache['symbols']:
            return []
        
        article_hashes = self.cache['symbols'][symbol]
        articles = []
        
        cutoff_time = datetime.now() - timedelta(hours=hours_back)
        
        for article_hash in article_hashes[:limit]:
            article = self.cache['articles'].get(article_hash)
            
            if article:
                stored_at = datetime.fromisoformat(article['stored_at'])
                if stored_at > cutoff_time:
                    articles.append(article)
        
        return articles
    
    def search_articles(
        self,
        keywords: List[str] = None,
        symbols: List[str] = None,
        sources: List[str] = None,
        hours_back: int = 24,
        limit: int = 100
    ) -> List[Dict]:
        """
        Search articles by keywords, symbols, or sources
        Smart search with ranking
        """
        results = []
        cutoff_time = datetime.now() - timedelta(hours=hours_back)
        
        # Get candidate articles
        candidate_hashes = set()
        
        if symbols:
            for symbol in symbols:
                if symbol in self.cache['symbols']:
                    candidate_hashes.update(self.cache['symbols'][symbol])
        
        if sources:
            for source in sources:
                if source in self.cache['sources']:
                    candidate_hashes.update(self.cache['sources'][source])
        
        if not symbols and not sources:
            # Search all articles
            candidate_hashes = set(self.cache['articles'].keys())
        
        # Filter and rank
        for article_hash in candidate_hashes:
            article = self.cache['articles'].get(article_hash)
            
            if not article:
                continue
            
            # Time filter
            stored_at = datetime.fromisoformat(article['stored_at'])
            if stored_at <= cutoff_time:
                continue
            
            # Keyword filter
            if keywords:
                title = article.get('title', '').lower()
                content = article.get('content', '').lower()
                full_text = f"{title} {content}"
                
                keyword_matches = sum(1 for kw in keywords if kw.lower() in full_text)
                if keyword_matches == 0:
                    continue
                
                article['relevance_score'] = keyword_matches / len(keywords)
            
            results.append(article)
            
            if len(results) >= limit:
                break
        
        # Sort by relevance or time
        if keywords:
            results.sort(key=lambda x: x.get('relevance_score', 0), reverse=True)
        else:
            results.sort(key=lambda x: x.get('stored_at', ''), reverse=True)
        
        return results[:limit]
    
    def check_if_seen(self, article: Dict) -> bool:
        """Quick check if article has been seen before"""
        article_hash = self._generate_article_hash(article)
        return article_hash in self.cache['articles']
    
    def get_symbol_history(
        self, 
        symbol: str, 
        days_back: int = 30
    ) -> Dict:
        """
        Get historical analysis for a symbol
        Returns patterns, frequency, sentiment trends
        """
        articles = self.get_articles_by_symbol(symbol, hours_back=days_back*24, limit=1000)
        
        if not articles:
            return {
                'symbol': symbol,
                'article_count': 0,
                'message': 'No historical data'
            }
        
        # Analyze patterns
        sentiments = [a.get('sentiment', 0) for a in articles if 'sentiment' in a]
        catalyst_scores = [a.get('catalyst_score', 0) for a in articles if 'catalyst_score' in a]
        
        sources = {}
        for article in articles:
            source = article.get('source', 'unknown')
            sources[source] = sources.get(source, 0) + 1
        
        # Calculate trends
        avg_sentiment = sum(sentiments) / len(sentiments) if sentiments else 0
        avg_catalyst = sum(catalyst_scores) / len(catalyst_scores) if catalyst_scores else 0
        
        return {
            'symbol': symbol,
            'article_count': len(articles),
            'avg_sentiment': avg_sentiment,
            'avg_catalyst_score': avg_catalyst,
            'sources': sources,
            'most_active_source': max(sources.items(), key=lambda x: x[1])[0] if sources else None,
            'time_range_days': days_back
        }
    
    def cleanup_old_articles(self, days_to_keep: int = 30):
        """Remove articles older than specified days"""
        cutoff_time = datetime.now() - timedelta(days=days_to_keep)
        
        articles_to_remove = []
        
        for article_hash, article in self.cache['articles'].items():
            stored_at = datetime.fromisoformat(article['stored_at'])
            
            if stored_at < cutoff_time:
                articles_to_remove.append(article_hash)
        
        # Remove from cache
        for article_hash in articles_to_remove:
            article = self.cache['articles'].pop(article_hash, None)
            
            if article:
                # Remove from indexes
                symbols = article.get('symbols', [])
                if isinstance(symbols, str):
                    symbols = [symbols]
                
                for symbol in symbols:
                    if symbol in self.cache['symbols']:
                        try:
                            self.cache['symbols'][symbol].remove(article_hash)
                        except ValueError:
                            pass
                
                source = article.get('source', 'unknown')
                if source in self.cache['sources']:
                    try:
                        self.cache['sources'][source].remove(article_hash)
                    except ValueError:
                        pass
        
        self.logger.info(f"Cleaned up {len(articles_to_remove)} old articles")
        
        # Persist cleanup
        self._save_memory()
        
        return len(articles_to_remove)
    
    def get_statistics(self) -> Dict:
        """Get memory bank statistics"""
        cache_efficiency = 0
        total_lookups = self.stats['cache_hits'] + self.stats['cache_misses']
        if total_lookups > 0:
            cache_efficiency = (self.stats['cache_hits'] / total_lookups) * 100
        
        return {
            'total_articles': len(self.cache['articles']),
            'unique_symbols': len(self.cache['symbols']),
            'unique_sources': len(self.cache['sources']),
            'duplicates_prevented': self.stats['duplicates_prevented'],
            'cache_hits': self.stats['cache_hits'],
            'cache_misses': self.stats['cache_misses'],
            'cache_efficiency_pct': cache_efficiency
        }
    
    def _generate_article_hash(self, article: Dict) -> str:
        """Generate unique hash for article based on title and content"""
        # Use title + first 200 chars of content
        title = article.get('title', '')
        content = article.get('content', article.get('summary', ''))[:200]
        
        # Normalize
        text = f"{title}|{content}".lower().strip()
        
        # Generate hash
        return hashlib.md5(text.encode()).hexdigest()
    
    def _persist_article(self, article: Dict):
        """Persist article to disk"""
        try:
            # Daily file organization
            today = datetime.now().strftime('%Y%m%d')
            daily_file = f"{self.memory_path}/daily/{today}.json"
            
            # Append to daily file
            daily_articles = []
            if os.path.exists(daily_file):
                with open(daily_file, 'r') as f:
                    daily_articles = json.load(f)
            
            daily_articles.append(article)
            
            with open(daily_file, 'w') as f:
                json.dump(daily_articles, f, indent=2)
            
            # Symbol-specific storage
            symbols = article.get('symbols', [])
            if isinstance(symbols, str):
                symbols = [symbols]
            
            for symbol in symbols:
                if symbol:
                    symbol_file = f"{self.memory_path}/symbols/{symbol}.json"
                    
                    symbol_articles = []
                    if os.path.exists(symbol_file):
                        with open(symbol_file, 'r') as f:
                            symbol_articles = json.load(f)
                    
                    symbol_articles.append(article)
                    
                    # Keep only last 100 articles per symbol
                    symbol_articles = symbol_articles[-100:]
                    
                    with open(symbol_file, 'w') as f:
                        json.dump(symbol_articles, f, indent=2)
            
        except Exception as e:
            self.logger.error(f"Error persisting article: {e}")
    
    def _load_memory(self):
        """Load memory from disk"""
        try:
            # Load today's articles
            today = datetime.now().strftime('%Y%m%d')
            daily_file = f"{self.memory_path}/daily/{today}.json"
            
            if os.path.exists(daily_file):
                with open(daily_file, 'r') as f:
                    articles = json.load(f)
                
                for article in articles:
                    article_hash = article.get('hash')
                    if article_hash:
                        self.cache['articles'][article_hash] = article
                        
                        # Rebuild indexes
                        symbols = article.get('symbols', [])
                        if isinstance(symbols, str):
                            symbols = [symbols]
                        
                        for symbol in symbols:
                            if symbol:
                                if symbol not in self.cache['symbols']:
                                    self.cache['symbols'][symbol] = []
                                self.cache['symbols'][symbol].append(article_hash)
                        
                        source = article.get('source', 'unknown')
                        if source not in self.cache['sources']:
                            self.cache['sources'][source] = []
                        self.cache['sources'][source].append(article_hash)
                
                self.logger.info(f"Loaded {len(articles)} articles from memory")
            
        except Exception as e:
            self.logger.error(f"Error loading memory: {e}")
    
    def _save_memory(self):
        """Save current memory state"""
        try:
            cache_file = f"{self.memory_path}/cache/memory_state.json"
            
            with open(cache_file, 'w') as f:
                json.dump({
                    'stats': self.stats,
                    'last_saved': datetime.now().isoformat()
                }, f, indent=2)
            
        except Exception as e:
            self.logger.error(f"Error saving memory: {e}")
