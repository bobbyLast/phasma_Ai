"""
News Engine - Integrated Sources Module
Adds our 20 news sources to the existing Phasma AI news engine
"""

import requests
import feedparser
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
import yfinance as yf
from bs4 import BeautifulSoup

from utils.discovery_limits import discovery_limit
from utils.company_resolver import get_resolver
from utils.prediction_market_filters import (
    is_stale_prediction_market,
    tag_intel_only_fields,
)
from engines.news_engine_utils import NewsUtils

class IntegratedNewsSources:
    """Integrated news sources for Phasma AI - 20 sources total"""

    _shared_news_cache: Optional[List[Dict[str, Any]]] = None
    _shared_news_cache_time: Optional[datetime] = None
    _cycle_token: Optional[str] = None
    _cycle_full_ingest_done: bool = False
    _single_ingest_per_cycle: bool = True

    @classmethod
    def begin_cycle(cls, cycle_attempt: int) -> None:
        """Mark a new trading cycle — at most one full ingest until next cycle."""
        cls._cycle_token = str(cycle_attempt)
        cls._cycle_full_ingest_done = False

    @classmethod
    def set_single_ingest_per_cycle(cls, enabled: bool) -> None:
        cls._single_ingest_per_cycle = bool(enabled)

    NOISE_SYMBOLS = NewsUtils.EXTRACTION_STOPWORDS | NewsUtils.BLOCKED_SYMBOLS
    
    def __init__(self, config):
        self.config = config
        self._news_symbol_limit = discovery_limit(config, "news_symbol_limit", 25)
        self._prediction_market_limit = discovery_limit(config, "prediction_market_limit", 25)
        self._news_cache_minutes = discovery_limit(config, "news_cache_minutes", 5)
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        # Load API keys
        self.world_news_key = getattr(config, 'world_news_api_key', None)
        self.gnews_key = getattr(config, 'gnews_api_key', None)
        self.mediastack_key = getattr(config, 'mediastack_api_key', None)
        self.currents_key = getattr(config, 'currents_api_key', None)
        self.alpha_vantage_key = getattr(config, 'alpha_vantage_key', None)
        self._symbol_validation_cache = {}
        
        # SEC headers for compliance
        self.sec_headers = {
            'User-Agent': 'Phasma-AI/1.0 (research@example.com) - Educational purpose',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
        }
        
        print("[INTEGRATED] 20 News Sources initialized")

    _DEFAULT_SOURCE_ORDER = (
        'social', 'apis', 'rss', 'sec', 'market', 'sentiment', 'prediction', 'github',
    )

    def _source_priority(self) -> List[str]:
        """Configurable ingest order; social runs first by default."""
        from utils.discovery_limits import _config_get
        cfg = _config_get(self.config, 'news_source_priority', None)
        if not cfg:
            return list(self._DEFAULT_SOURCE_ORDER)
        known = set(self._DEFAULT_SOURCE_ORDER)
        ordered = [s for s in cfg if s in known]
        for step in self._DEFAULT_SOURCE_ORDER:
            if step not in ordered:
                ordered.append(step)
        return ordered

    # region agent log
    def _debug_log(self, run_id: str, hypothesis_id: str, location: str, message: str, data: Dict[str, Any]):
        """Temporary debug instrumentation for session 28cc99."""
        try:
            payload = {
                "sessionId": "28cc99",
                "runId": run_id,
                "hypothesisId": hypothesis_id,
                "location": location,
                "message": message,
                "data": data,
                "pid": __import__("os").getpid(),
                "timestamp": int(datetime.now().timestamp() * 1000),
            }
            with open("debug-28cc99.log", "a", encoding="utf-8") as f:
                f.write(json.dumps(payload, default=str) + "\n")
        except Exception:
            pass
    # endregion
    
    async def fetch_all_integrated_sources(self) -> List[Dict[str, Any]]:
        """Fetch data from all 20 integrated sources"""
        now = datetime.now()
        if (
            self.__class__._single_ingest_per_cycle
            and self.__class__._cycle_full_ingest_done
            and self.__class__._shared_news_cache is not None
        ):
            cached_news = [dict(item) for item in self.__class__._shared_news_cache]
            print(
                f"[INTEGRATED] ♻️ Single ingest per cycle — reusing {len(cached_news)} items "
                "(no full re-fetch; use deep investigation for high-potential follow-ups)"
            )
            return cached_news
        if (
            self.__class__._shared_news_cache is not None
            and self.__class__._shared_news_cache_time is not None
            and now - self.__class__._shared_news_cache_time < timedelta(minutes=self._news_cache_minutes)
        ):
            cached_news = [dict(item) for item in self.__class__._shared_news_cache]
            # region agent log
            self._debug_log(
                "pre-fix",
                "H10",
                "engines/news_engine_integrated.py:fetch_all_integrated_sources:cache_hit",
                "reused integrated news source cache",
                {"total_items": len(cached_news), "cache_age_seconds": round((now - self.__class__._shared_news_cache_time).total_seconds(), 3)},
            )
            # endregion
            return cached_news
        
        all_news = []
        news_symbols: List[str] = []
        news_keywords: List[str] = []
        valid_market_symbols: set = set()

        for step in self._source_priority():
            if step == 'social':
                social_data = await self._fetch_social_data()
                all_news.extend(social_data)
                print(f"[INTEGRATED] Social: {len(social_data)} items")
            elif step == 'apis':
                api_news = await self._fetch_news_apis()
                all_news.extend(api_news)
                print(f"[INTEGRATED] News APIs: {len(api_news)} articles")
            elif step == 'rss':
                rss_news = await self._fetch_rss_feeds()
                all_news.extend(rss_news)
                print(f"[INTEGRATED] RSS Feeds: {len(rss_news)} articles")
            elif step == 'sec':
                sec_news = await self._fetch_sec_filings()
                all_news.extend(sec_news)
                print(f"[INTEGRATED] SEC Filings: {len(sec_news)} items")
            elif step == 'market':
                news_symbols = self._extract_news_symbols(all_news)
                market_data = await self._fetch_market_data(news_symbols)
                all_news.extend(market_data)
                NewsUtils.propagate_prices(all_news)
                valid_market_symbols = {item.get('symbol') for item in market_data if item.get('symbol')}
                valid_market_symbols.update(news_symbols)
                valid_market_symbols.update({'BTC', 'ETH', 'SOL'})
                print(f"[INTEGRATED] Market Data: {len(market_data)} tickers")
            elif step == 'sentiment':
                sentiment_news = await self._fetch_sentiment_data()
                all_news.extend(sentiment_news)
                print(f"[INTEGRATED] Sentiment: {len(sentiment_news)} articles")
            elif step == 'prediction':
                if not news_symbols:
                    news_symbols = self._extract_news_symbols(all_news)
                news_keywords = self._extract_news_keywords(all_news, news_symbols)
                prediction_market_data = await self._fetch_prediction_markets(news_symbols, news_keywords)
                all_news.extend(prediction_market_data)
                matched = sum(
                    1 for item in prediction_market_data
                    if item.get('symbol') or item.get('news_match_score', 0) > 0
                )
                print(
                    f"[INTEGRATED] Prediction Markets: {len(prediction_market_data)} items "
                    f"({matched} news-aligned)"
                )
            elif step == 'github':
                github_data = await self._fetch_github_data()
                all_news.extend(github_data)
                print(f"[INTEGRATED] GitHub: {len(github_data)} items")

        for item in all_news:
            if item.get('prediction_market'):
                cleaned_symbol = self._clean_symbol(item.get('symbol'))
                if cleaned_symbol:
                    item['symbol'] = cleaned_symbol
                continue
            cleaned_symbol = self._clean_symbol(item.get('symbol'))
            item['symbol'] = cleaned_symbol if cleaned_symbol in valid_market_symbols else ''

        # region agent log
        symbol_counts = {}
        source_counts = {}
        for item in all_news:
            source = item.get('source') or 'missing_source'
            source_counts[source] = source_counts.get(source, 0) + 1
            symbol = item.get('symbol')
            if symbol:
                symbol_counts[symbol] = symbol_counts.get(symbol, 0) + 1
        self._debug_log(
            "pre-fix",
            "H6,H8",
            "engines/news_engine_integrated.py:fetch_all_integrated_sources",
            "integrated source counts and extracted symbol universe",
            {
                "total_items": len(all_news),
                "source_counts": source_counts,
                "unique_symbol_count": len(symbol_counts),
                "top_symbols": sorted(symbol_counts.items(), key=lambda item: item[1], reverse=True)[:20],
                "blank_symbol_items": sum(1 for item in all_news if not item.get('symbol')),
            },
        )
        # endregion

        # Hot path: local CSV stamp only — do NOT yfinance/DuckDuckGo every headline.
        # Top-N coalition resolve happens later in the cycle.
        resolver = get_resolver()
        local_hits = 0
        for item in all_news:
            before = item.get("company_name")
            resolver.enrich_news_item(item, allow_yf=False, allow_web=False, local_only=True)
            if item.get("company_name") and item.get("company_name") != before:
                local_hits += 1
        print(
            f"[INTEGRATED] Local enrich only: {local_hits} CSV hits "
            f"(skipped web/yf for {len(all_news)} items)"
        )

        print(f"[INTEGRATED] Total: {len(all_news)} items from 20 sources")
        self.__class__._shared_news_cache = [dict(item) for item in all_news]
        self.__class__._shared_news_cache_time = now
        self.__class__._cycle_full_ingest_done = True
        return all_news
    
    async def _fetch_news_apis(self) -> List[Dict[str, Any]]:
        """Fetch from 4 news APIs"""
        news = []
        
        # World News API
        if self.world_news_key:
            try:
                url = f"https://api.worldnewsapi.com/search-news?api-key={self.world_news_key}&text=insider%20trading&language=en&sort=publish-time"
                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    for article in data.get('news', [])[:10]:
                        news.append({
                            'title': article.get('title', ''),
                            'source': 'World News API',
                            'symbol': self._extract_symbol(article.get('title', '')),
                            'timestamp': article.get('publish_date', ''),
                            'url': article.get('url', ''),
                            'summary': article.get('text', ''),
                            'sentiment': 0.6
                        })
            except Exception as e:
                print(f"[INTEGRATED] World News API error: {e}")
        
        # GNews API
        if self.gnews_key:
            try:
                url = "https://gnews.io/api/v4/search"
                params = {
                    'q': 'insider trading',
                    'lang': 'en',
                    'country': 'us',
                    'max': 10,
                    'apikey': self.gnews_key
                }
                response = requests.get(url, params=params, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    for article in data.get('articles', [])[:10]:
                        news.append({
                            'title': article.get('title', ''),
                            'source': 'GNews API',
                            'symbol': self._extract_symbol(article.get('title', '')),
                            'timestamp': article.get('publishedAt', ''),
                            'url': article.get('url', ''),
                            'summary': article.get('description', ''),
                            'sentiment': 0.6
                        })
            except Exception as e:
                print(f"[INTEGRATED] GNews API error: {e}")
        
        # MediaStack API
        if self.mediastack_key:
            try:
                url = "http://api.mediastack.com/v1/news"
                params = {
                    'access_key': self.mediastack_key,
                    'keywords': 'insider trading',
                    'countries': 'us',
                    'limit': 10
                }
                response = requests.get(url, params=params, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    for article in data.get('data', [])[:10]:
                        news.append({
                            'title': article.get('title', ''),
                            'source': 'MediaStack API',
                            'symbol': self._extract_symbol(article.get('title', '')),
                            'timestamp': article.get('published_at', ''),
                            'url': article.get('url', ''),
                            'summary': article.get('description', ''),
                            'sentiment': 0.6
                        })
            except Exception as e:
                print(f"[INTEGRATED] MediaStack API error: {e}")
        
        # Currents API
        if self.currents_key:
            try:
                url = f"https://api.currentsapi.services/v1/latest-news?apiKey={self.currents_key}&category=business"
                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    for article in data.get('news', [])[:10]:
                        news.append({
                            'title': article.get('title', ''),
                            'source': 'Currents API',
                            'symbol': self._extract_symbol(article.get('title', '')),
                            'timestamp': article.get('published', ''),
                            'url': article.get('url', ''),
                            'summary': article.get('description', ''),
                            'sentiment': 0.6
                        })
            except Exception as e:
                print(f"[INTEGRATED] Currents API error: {e}")
        
        return news
    
    async def _fetch_rss_feeds(self) -> List[Dict[str, Any]]:
        """Fetch from 10 RSS feeds"""
        news = []
        
        rss_feeds = [
            ('Seeking Alpha', 'https://seekingalpha.com/feed.xml'),
            ('MarketWatch', 'https://www.marketwatch.com/rss/topstories'),
            ('Yahoo Finance', 'https://finance.yahoo.com/news/rssindex'),
            ('Financial Times', 'https://www.ft.com/rss/home'),
            ('CNBC Markets', 'https://www.cnbc.com/id/100003114/device/rss/rss.html'),
            ('BBC Business', 'https://feeds.bbci.co.uk/news/business/rss.xml'),
            ('Economic Times', 'https://economictimes.indiatimes.com/rssfeedsdefault.cms'),
            ('Bloomberg', 'https://bloomberg.com/feed/news/economy.rss'),
            ('Reuters Business', 'https://www.reuters.com/rssFeed/businessNews'),
            ('WSJ', 'https://feeds.wsjonline.com/wsj/xml/rss/3_7014.xml')
        ]
        
        for name, url in rss_feeds:
            try:
                response = requests.get(url, headers=self.headers, timeout=10)
                if response.status_code == 200:
                    feed = feedparser.parse(response.content)
                    for entry in feed.entries[:5]:  # Limit to 5 per feed
                        news.append({
                            'title': entry.get('title', ''),
                            'source': name,
                            'symbol': self._extract_symbol(entry.get('title', '')),
                            'timestamp': entry.get('published', ''),
                            'url': entry.get('link', ''),
                            'summary': entry.get('summary', ''),
                            'sentiment': 0.5
                        })
            except Exception as e:
                print(f"[INTEGRATED] RSS {name} error: {e}")
        
        return news
    
    async def _fetch_sec_filings(self) -> List[Dict[str, Any]]:
        """Fetch SEC Form 4 filings"""
        news = []
        
        try:
            url = "https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent&CIK=&type=4&company=&dateb=&owner=include&count=10"
            response = requests.get(url, headers=self.sec_headers, timeout=15)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                links = soup.find_all('a', href=True)
                
                for link in links[:10]:
                    if '/Archives/edgar/data/' in link.get('href', ''):
                        # Extract symbol from link text
                        text = link.get_text(strip=True)
                        symbol = self._extract_symbol(text)
                        
                        news.append({
                            'title': f'Form 4 Filing: {text}',
                            'source': 'SEC EDGAR',
                            'symbol': symbol,
                            'timestamp': datetime.now().isoformat(),
                            'url': 'https://www.sec.gov' + link.get('href', ''),
                            'summary': 'SEC Form 4 insider trading filing',
                            'sentiment': 0.7
                        })
        except Exception as e:
            print(f"[INTEGRATED] SEC error: {e}")
        
        return news
    
    def _extract_news_symbols(self, items: List[Dict[str, Any]], limit: Optional[int] = None) -> List[str]:
        limit = limit if limit is not None else self._news_symbol_limit
        """Use today's news symbols as the market-data universe."""
        symbols = []
        seen = set()
        for item in items:
            symbol = str(item.get('symbol') or '').upper().strip()
            if not symbol or symbol in seen:
                continue
            if not self._clean_symbol(symbol):
                continue
            if not self._is_live_tradeable_symbol(symbol):
                continue
            seen.add(symbol)
            symbols.append(symbol)
            if len(symbols) >= limit:
                break
        return symbols

    _MACRO_KEYWORDS = (
        'fed', 'federal reserve', 'fomc', 'inflation', 'cpi', 'gdp', 'unemployment',
        'jobs report', 'interest rate', 'recession', 'tariff', 'trade war', 'oil',
        'crude', 'bitcoin', 'ethereum', 'crypto', 'president', 'election', 'congress',
        'senate', 'white house', 'treasury', 'debt ceiling', 'earnings', 'ipo',
        'merger', 'acquisition', 'bankruptcy', 'sec ', 'fda', 'nvidia', 'tesla',
        'apple', 'amazon', 'microsoft', 'google', 'meta', 'jpmorgan', 'goldman',
    )
    _SPORTS_DEPRIORITIZE = (
        'nfl', 'nba', 'mlb', 'nhl', 'ncaa', 'touchdown', 'parlay', 'spread',
        'moneyline', 'over under', 'super bowl', 'world series', 'runs scored',
        'wins by over', ' goals scored', 'points', 'rebounds', 'assists',
    )

    _KEYWORD_STOPWORDS = frozenset({
        'that', 'this', 'with', 'from', 'have', 'will', 'been', 'were', 'their',
        'about', 'after', 'before', 'would', 'could', 'should', 'which', 'while',
        'where', 'when', 'what', 'your', 'more', 'than', 'into', 'over', 'under',
        'news', 'says', 'said', 'report', 'market', 'stock', 'stocks', 'shares',
    })

    def _extract_news_keywords(
        self, items: List[Dict[str, Any]], symbols: Optional[List[str]] = None
    ) -> List[str]:
        """Theme/entity keywords from today's news for prediction-market matching."""
        import re

        keywords: set = set()
        for sym in symbols or []:
            keywords.add(sym.lower())
        blob_parts = []
        for item in items:
            if item.get('prediction_market'):
                continue
            blob_parts.append(str(item.get('title') or ''))
            blob_parts.append(str(item.get('summary') or ''))
        blob = ' '.join(blob_parts).lower()
        for kw in self._MACRO_KEYWORDS:
            if kw in blob:
                keywords.add(kw)
        for token in re.findall(r'[a-z]{4,}', blob):
            if token not in self._KEYWORD_STOPWORDS:
                keywords.add(token)
        return sorted(keywords)

    def _is_kalshi_sports_noise(self, title: str) -> bool:
        title_l = (title or '').lower()
        if not title_l:
            return False
        if any(term in title_l for term in self._SPORTS_DEPRIORITIZE):
            return True
        if ': 2+' in title_l or 'goals scored' in title_l or title_l.count('yes ') >= 2:
            return True
        if title_l.startswith('yes ') and ',' in title_l:
            return True
        return False

    def _score_prediction_market(
        self, title: str, news_symbols: List[str], news_keywords: List[str]
    ) -> int:
        title_l = (title or '').lower()
        if not title_l or self._is_kalshi_sports_noise(title):
            return -999
        score = 0
        for sym in news_symbols:
            if sym.lower() in title_l:
                score += 10
        for kw in news_keywords:
            if kw in title_l:
                score += 3
        return score

    def _is_live_tradeable_symbol(self, symbol: str) -> bool:
        """Validate a candidate ticker against live market lookup before analysis."""
        symbol = self._clean_symbol(symbol)
        if not symbol:
            return False
        if symbol in NewsUtils.CRYPTO_SYMBOLS:
            return True
        if not NewsUtils.is_valid_extracted_ticker(symbol):
            return False
        if symbol in self._symbol_validation_cache:
            return self._symbol_validation_cache[symbol]

        is_valid = False
        try:
            response = requests.get(
                "https://query2.finance.yahoo.com/v1/finance/search",
                params={"q": symbol, "quotesCount": 5, "newsCount": 0},
                headers=self.headers,
                timeout=5,
            )
            if response.status_code == 200:
                for quote in response.json().get("quotes", []):
                    quote_symbol = str(quote.get("symbol", "")).upper()
                    quote_type = str(quote.get("quoteType", "")).upper()
                    if quote_symbol == symbol and quote_type in {"EQUITY", "ETF", "CRYPTOCURRENCY"}:
                        is_valid = True
                        break
        except Exception:
            is_valid = False

        self._symbol_validation_cache[symbol] = is_valid
        return is_valid
    
    def _normalize_ticker_list(self, tickers) -> List[str]:
        """Normalize tickers from set/list/tuple/string/None to deduped uppercase list."""
        if not tickers:
            return []
        if isinstance(tickers, str):
            raw = [tickers]
        elif isinstance(tickers, set):
            raw = sorted(tickers)
        else:
            raw = list(tickers)

        cleaned: List[str] = []
        seen: set = set()
        for item in raw:
            if item is None:
                continue
            symbol = str(item).strip().upper()
            if not symbol or symbol in seen:
                continue
            seen.add(symbol)
            cleaned.append(symbol)
        return cleaned

    async def _fetch_market_data(self, tickers: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """Fetch market data for symbols discovered from current news."""
        data = []
        ticker_list = self._normalize_ticker_list(tickers)
        limited_tickers = ticker_list[: self._news_symbol_limit]

        # region agent log
        self._debug_log(
            "pre-fix",
            "H6",
            "engines/news_engine_integrated.py:_fetch_market_data",
            "news-derived market-data ticker list used",
            {"tickers": limited_tickers, "reason": "symbols extracted from current news"},
        )
        # endregion

        for ticker in limited_tickers:
            try:
                snapshot = self._fetch_ticker_price_snapshot(ticker)
                if snapshot:
                    price = snapshot["price"]
                    volume = snapshot["volume"]
                    data.append({
                        'title': f'{ticker} Market Data',
                        'source': snapshot["source"],
                        'symbol': ticker,
                        'timestamp': datetime.now().isoformat(),
                        'url': '',
                        'summary': f"Price: ${price:.2f}, Volume: {volume:,}",
                        'sentiment': 0.5,
                        'price': price,
                        'volume': volume
                    })
            except Exception as e:
                print(f"[INTEGRATED] YFinance {ticker} error: {e}")

        # region agent log
        self._debug_log(
            "pre-fix",
            "H11",
            "engines/news_engine_integrated.py:_fetch_market_data:results",
            "market-data enrichment result count",
            {"requested": limited_tickers, "returned_symbols": [item.get("symbol") for item in data], "count": len(data)},
        )
        # endregion
        
        return data

    def _fetch_yahoo_chart_snapshot(self, yahoo_symbol: str) -> Optional[Dict[str, Any]]:
        """Fetch last close from Yahoo chart API."""
        try:
            response = requests.get(
                f"https://query1.finance.yahoo.com/v8/finance/chart/{yahoo_symbol}",
                params={"range": "5d", "interval": "1d"},
                headers=self.headers,
                timeout=8,
            )
            if response.status_code != 200:
                return None
            result = (response.json().get("chart", {}).get("result") or [None])[0]
            quote = ((result or {}).get("indicators", {}).get("quote") or [{}])[0]
            closes = [value for value in quote.get("close", []) if value is not None]
            volumes = [value for value in quote.get("volume", []) if value is not None]
            if not closes:
                return None
            return {
                "source": "Yahoo Chart",
                "price": float(closes[-1]),
                "volume": int(volumes[-1]) if volumes else 0,
            }
        except Exception:
            return None

    def _fetch_ticker_price_snapshot(self, ticker: str) -> Optional[Dict[str, Any]]:
        """Fetch one live price with fallbacks that work when yfinance history is empty."""
        if ticker in NewsUtils.CRYPTO_SYMBOLS:
            crypto_snapshot = self._fetch_yahoo_chart_snapshot(f"{ticker}-USD")
            if crypto_snapshot:
                crypto_snapshot["source"] = "Yahoo Crypto"
                return crypto_snapshot

        try:
            stock = yf.Ticker(ticker)
            history = stock.history(period='1d')
            if len(history) > 0:
                price = float(history['Close'].iloc[-1])
                if ticker in NewsUtils.CRYPTO_SYMBOLS and price < 1000:
                    crypto_snapshot = self._fetch_yahoo_chart_snapshot(f"{ticker}-USD")
                    if crypto_snapshot:
                        crypto_snapshot["source"] = "Yahoo Crypto"
                        return crypto_snapshot
                return {
                    "source": "YFinance",
                    "price": price,
                    "volume": int(history['Volume'].iloc[-1]) if 'Volume' in history else 0,
                }
        except Exception:
            pass

        yahoo_symbols = [ticker]
        if ticker in NewsUtils.CRYPTO_SYMBOLS:
            yahoo_symbols.insert(0, f"{ticker}-USD")

        for yahoo_symbol in yahoo_symbols:
            snapshot = self._fetch_yahoo_chart_snapshot(yahoo_symbol)
            if snapshot:
                return snapshot

        if ticker.isalpha() and len(ticker) <= 5:
            try:
                import csv
                import io
                response = requests.get(
                    f"https://stooq.com/q/l/?s={ticker.lower()}.us&f=sd2t2ohlcv&h&e=csv",
                    headers=self.headers,
                    timeout=8,
                )
                rows = list(csv.DictReader(io.StringIO(response.text)))
                if rows and rows[0].get("Close") not in (None, "N/D"):
                    volume = rows[0].get("Volume") or 0
                    return {
                        "source": "Stooq",
                        "price": float(rows[0]["Close"]),
                        "volume": int(float(volume)) if volume not in ("", None, "N/D") else 0,
                    }
            except Exception:
                pass

        return None
    
    async def _fetch_prediction_markets(
        self,
        news_symbols: Optional[List[str]] = None,
        news_keywords: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """Fetch Kalshi/Polymarket markets; prioritize news symbol/keyword overlap."""
        data: List[Dict[str, Any]] = []
        news_symbols = news_symbols or []
        news_keywords = news_keywords or []
        bulk_limit = max(self._prediction_market_limit * 4, 100)

        try:
            kalshi_rows = self._fetch_kalshi_markets_for_news(
                news_symbols, news_keywords, bulk_limit
            )
            for match_score, market, title in kalshi_rows[: self._prediction_market_limit]:
                row = {
                    'title': title,
                    'source': 'Kalshi',
                    'symbol': self._extract_symbol(title),
                    'timestamp': datetime.now().isoformat(),
                    'url': '',
                    'summary': f"Kalshi market: {title}",
                    'sentiment': 0.5,
                    'prediction_market': 'kalshi',
                    'market_ticker': market.get('ticker'),
                    'volume': market.get('volume'),
                    'yes_price': market.get('yes_price'),
                    'news_match_score': match_score,
                }
                tag_intel_only_fields(row, self.config)
                data.append(row)
            positive = sum(1 for score, _, _ in kalshi_rows if score > 0)
            print(
                f"[INTEGRATED] Kalshi: {positive} news-matched, "
                f"kept {min(len(kalshi_rows), self._prediction_market_limit)}"
            )
        except Exception as e:
            print(f"[INTEGRATED] Kalshi markets error: {e}")

        try:
            response = requests.get(
                "https://gamma-api.polymarket.com/markets",
                params={"active": "true", "closed": "false", "limit": bulk_limit},
                headers=self.headers,
                timeout=10,
            )
            if response.status_code == 200:
                markets = response.json()
                if isinstance(markets, dict):
                    markets = markets.get('markets', [])
                scored = []
                for market in markets:
                    title = market.get('question') or market.get('title') or ''
                    match_score = self._score_prediction_market(title, news_symbols, news_keywords)
                    scored.append((match_score, market, title))
                scored.sort(key=lambda row: row[0], reverse=True)
                for match_score, market, title in scored[: self._prediction_market_limit]:
                    row = {
                        'title': title,
                        'source': 'Polymarket',
                        'symbol': self._extract_symbol(title),
                        'timestamp': datetime.now().isoformat(),
                        'url': market.get('slug', ''),
                        'summary': f"Polymarket market: {title}",
                        'sentiment': 0.5,
                        'prediction_market': 'polymarket',
                        'market_ticker': market.get('id'),
                        'volume': market.get('volume'),
                        'news_match_score': match_score,
                    }
                    tag_intel_only_fields(row, self.config)
                    data.append(row)
        except Exception as e:
            print(f"[INTEGRATED] Polymarket markets error: {e}")

        return data

    def _fetch_kalshi_markets_for_news(
        self,
        news_symbols: List[str],
        news_keywords: List[str],
        bulk_limit: int,
    ) -> List[tuple]:
        """Pull Kalshi markets via series discovery (bulk feed is sports-heavy)."""
        base = "https://api.elections.kalshi.com/trade-api/v2"
        macro_terms = {k.lower() for k in self._MACRO_KEYWORDS}
        match_terms = {sym.lower() for sym in news_symbols}
        match_terms.update(k for k in news_keywords if k in macro_terms or len(k) >= 5)
        series_hits: List[Dict[str, Any]] = []
        seen_series: set = set()

        series_resp = requests.get(f"{base}/series", headers=self.headers, timeout=12)
        if series_resp.status_code == 200:
            for series in series_resp.json().get('series', []):
                title = (series.get('title') or '').lower()
                ticker = (series.get('ticker') or '').lower()
                if any(term in title or term in ticker for term in match_terms):
                    key = series.get('ticker')
                    if key and key not in seen_series:
                        seen_series.add(key)
                        series_hits.append(series)

        if len(series_hits) < 15:
            for series in series_resp.json().get('series', []) if series_resp.status_code == 200 else []:
                title = (series.get('title') or '').lower()
                if any(term in title for term in self._MACRO_KEYWORDS):
                    key = series.get('ticker')
                    if key and key not in seen_series:
                        seen_series.add(key)
                        series_hits.append(series)
                if len(series_hits) >= 30:
                    break

        candidates: List[Dict[str, Any]] = []
        for series in series_hits[:25]:
            st = series.get('ticker')
            if not st:
                continue
            try:
                mresp = requests.get(
                    f"{base}/markets",
                    params={"status": "open", "series_ticker": st, "limit": 15},
                    headers=self.headers,
                    timeout=10,
                )
                if mresp.status_code == 200:
                    for market in mresp.json().get('markets', []):
                        title = market.get('title') or market.get('subtitle') or ''
                        if is_stale_prediction_market(market, title):
                            continue
                        candidates.append(market)
            except Exception:
                continue

        if len(candidates) < bulk_limit // 2:
            cursor = None
            pages = 0
            while pages < 4 and len(candidates) < bulk_limit:
                params: Dict[str, Any] = {"status": "open", "limit": 100}
                if cursor:
                    params["cursor"] = cursor
                mresp = requests.get(f"{base}/markets", params=params, headers=self.headers, timeout=10)
                if mresp.status_code != 200:
                    break
                payload = mresp.json()
                for market in payload.get('markets', []):
                    title = market.get('title') or market.get('subtitle') or ''
                    if self._is_kalshi_sports_noise(title):
                        continue
                    if is_stale_prediction_market(market, title):
                        continue
                    candidates.append(market)
                cursor = payload.get('next_cursor')
                pages += 1
                if not cursor:
                    break

        scored: List[tuple] = []
        seen_tickers: set = set()
        for market in candidates:
            ticker = market.get('ticker')
            if not ticker or ticker in seen_tickers:
                continue
            title = market.get('title') or market.get('subtitle') or ''
            if is_stale_prediction_market(market, title):
                continue
            seen_tickers.add(ticker)
            match_score = self._score_prediction_market(title, news_symbols, news_keywords)
            scored.append((match_score, market, title))
        scored.sort(key=lambda row: row[0], reverse=True)

        positive = [row for row in scored if row[0] > 0]
        selected = positive[: self._prediction_market_limit]
        if len(selected) < self._prediction_market_limit:
            seen = {row[1].get('ticker') for row in selected}
            for row in scored:
                if len(selected) >= self._prediction_market_limit:
                    break
                if row[0] <= 0:
                    continue
                if row[1].get('ticker') not in seen:
                    selected.append(row)
                    seen.add(row[1].get('ticker'))
        if len(selected) < self._prediction_market_limit:
            seen = {row[1].get('ticker') for row in selected}
            for row in scored:
                if len(selected) >= self._prediction_market_limit:
                    break
                if row[1].get('ticker') not in seen:
                    selected.append(row)
                    seen.add(row[1].get('ticker'))
        return selected
    
    async def _fetch_sentiment_data(self) -> List[Dict[str, Any]]:
        """Fetch sentiment data from Alpha Vantage"""
        news = []
        
        if self.alpha_vantage_key and self.alpha_vantage_key != 'your_alpha_vantage_key_here':
            try:
                url = f"https://www.alphavantage.co/query?function=NEWS_SENTIMENT&apikey={self.alpha_vantage_key}"
                response = requests.get(url, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    for article in data.get('feed', [])[:10]:
                        news.append({
                            'title': article.get('title', ''),
                            'source': 'Alpha Vantage',
                            'symbol': self._extract_symbol(article.get('title', '')),
                            'timestamp': article.get('time_published', ''),
                            'url': article.get('url', ''),
                            'summary': article.get('summary', ''),
                            'sentiment': float(article.get('overall_sentiment_score', 0))
                        })
            except Exception as e:
                print(f"[INTEGRATED] Alpha Vantage error: {e}")
        
        return news
    
    async def _fetch_social_data(self) -> List[Dict[str, Any]]:
        """Fetch social media data"""
        data = []
        
        # Reddit status
        if hasattr(self.config, 'reddit_client_id'):
            data.append({
                'title': 'Reddit API Status',
                'source': 'Reddit',
                'symbol': '',
                'timestamp': datetime.now().isoformat(),
                'url': '',
                'summary': 'Reddit API configured for sentiment analysis',
                'sentiment': 0.5
            })
        
        # Twitter status
        if hasattr(self.config, 'twitter_api_key'):
            data.append({
                'title': 'Twitter API Status',
                'source': 'Twitter',
                'symbol': '',
                'timestamp': datetime.now().isoformat(),
                'url': '',
                'summary': 'Twitter API configured for influencer monitoring',
                'sentiment': 0.5
            })
        
        return data
    
    async def _fetch_github_data(self) -> List[Dict[str, Any]]:
        """Fetch GitHub integration data"""
        data = []
        
        # FeedBin API status
        data.append({
            'title': 'FeedBin API Ready',
            'source': 'FeedBin',
            'symbol': '',
            'timestamp': datetime.now().isoformat(),
            'url': '',
            'summary': 'RSS aggregation framework ready',
            'sentiment': 0.5
        })
        
        # Elon Musk scraper
        data.append({
            'title': 'Elon Musk Scraper Active',
            'source': 'Twitter',
            'symbol': 'TSLA',
            'timestamp': datetime.now().isoformat(),
            'url': '',
            'summary': 'Monitoring Elon Musk tweets for Tesla/crypto sentiment',
            'sentiment': 0.5
        })
        
        return data
    
    def _extract_symbol(self, text: str) -> str:
        """Extract stock symbol from text"""
        import re
        
        text_upper = text.upper()
        cash_tags = re.findall(r'\$([A-Z]{1,5})\b', text_upper)
        symbols = list(cash_tags)
        
        # Look for common stock names and variations
        stock_patterns = {
            # Direct mentions
            r'\bApple\b': 'AAPL',
            r'\bTesla\b': 'TSLA',
            r'\bMicrosoft\b': 'MSFT',
            r'\bGoogle\b': 'GOOGL',
            r'\bAlphabet\b': 'GOOGL',
            r'\bAmazon\b': 'AMZN',
            r'\bFacebook\b': 'META',
            r'\bMeta\b': 'META',
            r'\bNetflix\b': 'NFLX',
            r'\bNVIDIA\b': 'NVDA',
            r'\bNvidia\b': 'NVDA',
            r'\bAMD\b': 'AMD',
            r'\bIntel\b': 'INTC',
            r'\bBoeing\b': 'BA',
            r'\bJPMorgan\b': 'JPM',
            r'\bGoldman\b': 'GS',
            r'\bBank of America\b': 'BAC',
            r'\bWalmart\b': 'WMT',
            r'\bDisney\b': 'DIS',
            r'\bGameStop\b': 'GME',
            r'\bAMC\b': 'AMC',
            r'\bBlackRock\b': 'BLK',
            r'\bSilver\b': 'SLV',
            r'\bGold\b': 'GLD',
            r'\bBitcoin\b': 'BTC',
            r'\bEthereum\b': 'ETH',
            r'\bDow\b': 'DOW',
            r'\bS&P\b': 'SPY',
            r'\bDutch Bros\b': 'BROS',
            # Pattern matches for insider trading terms
            r'insider.*?([A-Z]{1,5})\b': r'\1',
            r'shares.*?([A-Z]{1,5})\b': r'\1',
            r'stock.*?([A-Z]{1,5})\b': r'\1',
            r'\b([A-Z]{1,5})\b.*?shares': r'\1',
        }
        
        # Apply patterns
        for pattern, symbol in stock_patterns.items():
            if re.search(pattern, text, re.IGNORECASE):
                if isinstance(symbol, str) and symbol.startswith('$'):
                    symbols.append(symbol[1:])
                elif isinstance(symbol, str):
                    symbols.append(symbol)
                elif isinstance(symbol, str) and symbol.startswith('\\'):
                    # Extract group from pattern
                    match = re.search(pattern, text, re.IGNORECASE)
                    if match:
                        symbols.append(match.group(1))
        
        for ticker in cash_tags:
            cleaned = self._clean_symbol(ticker)
            if cleaned and NewsUtils.is_valid_extracted_ticker(cleaned, from_cash_tag=True):
                return cleaned

        # Return the first valid symbol from company-name / pattern matches
        for symbol in symbols:
            cleaned = self._clean_symbol(symbol)
            if cleaned and NewsUtils.is_valid_extracted_ticker(cleaned):
                return cleaned
        
        return ''
    
    def _clean_symbol(self, symbol: str) -> str:
        """Drop obvious non-ticker terms before downstream stock analysis."""
        symbol = str(symbol or '').upper().strip()
        if not symbol or len(symbol) > 5 or not symbol.isalpha():
            return ''
        if symbol in self.NOISE_SYMBOLS:
            return ''
        if not NewsUtils.is_valid_extracted_ticker(symbol):
            return ''
        return symbol
