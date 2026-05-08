"""
News Engine Core Module
Main NewsAPIIntegration class that orchestrates all components
"""

import asyncio
from typing import List, Dict, Optional, Any
from datetime import datetime

# Import component modules
from .news_engine_validation import CompanyValidator
from .news_engine_utils import NewsUtils
from .news_engine_apis import NewsAPIs
from .news_engine_analysis import NewsAnalyzer
from .news_engine_integrated import IntegratedNewsSources

# Import Smart Memory Bank and News Collection Network
from .news_memory_bank import NewsMemoryBank
from .news_collection_network import NewsCollectionNetwork
from .silver_detector import add_silver_detection_to_news_engine

class NewsAPIIntegration:
    """Main news API integration class - orchestrates all components"""

    def __init__(self, config):
        self.config = config

        # Initialize component modules first
        self.validator = CompanyValidator(config)  # Pass config to CompanyValidator
        self.utils = NewsUtils()
        self.apis = NewsAPIs(self.config)
        self.analyzer = NewsAnalyzer(self.config)
        
        # Initialize our 20 integrated news sources
        self.integrated_sources = IntegratedNewsSources(self.config)

        # Build company database from validator
        self.company_db = self.validator.company_db
        print(f"🔍 NEWS DEBUG: company_db size = {len(self.company_db)}")
        print(f"🔍 NEWS DEBUG: sample symbols = {list(self.company_db.keys())[:10]}")

        # Set utils and company_db reference in APIs module
        self.apis.utils = self.utils
        self.apis.company_db = self.company_db
        self.apis.validator = self.validator

        # Initialize Smart Memory Bank
        try:
            self.memory_bank = NewsMemoryBank()
            print("[OK] Smart Memory Bank initialized")
        except Exception as e:
            print(f"[WARN] Could not initialize Smart Memory Bank: {e}")
            self.memory_bank = None

        # Initialize News Collection Network (24/7 RSS aggregation)
        try:
            self.news_network = NewsCollectionNetwork(
                memory_bank=self.memory_bank,
                company_db=self.company_db,
                meta_brain=None  # Will be set later if needed
            )
            print("[OK] News Collection Network initialized (58 RSS feeds)")
        except Exception as e:
            print(f"[WARN] Could not initialize News Collection Network: {e}")
            self.news_network = None

        # Add Silver Opportunity Detector
        try:
            add_silver_detection_to_news_engine(self)
            print("[OK] Silver Opportunity Detector added")
        except Exception as e:
            print(f"[WARN] Could not add Silver Detector: {e}")

        print("[OK] News Engine initialized with modular components + Smart Memory + RSS Network + Silver Detector + 20 Integrated Sources")

    def _fact_check_company(self, news_item: Dict, all_sectors_mode: bool = False) -> Dict:
        """Fact check a company from news item"""
        return self.validator.fact_check_company(news_item, all_sectors_mode)

    async def scan_all_sources(self, symbols: List[str] = None) -> List[Dict[str, Any]]:
        """Scan all real news sources for opportunities using hybrid industry approach"""
        print("[INFO] Scanning real news sources with hybrid industry approach...")

        # Get configuration for all_sectors_mode
        all_sectors_mode = getattr(self.config, 'all_sectors_mode', False) or (self.config.get('trading.all_sectors_mode') or False)
        if all_sectors_mode:
            print("[MODE] ALL SECTORS: Scanning all industries equally")
        else:
            print("[MODE] TARGETED: Scanning high-volume sectors only")

        # Get all available industries for targeted scanning
        available_industries = self.validator.get_all_industries()

        print(f"[INFO] Scanning {len(available_industries)} high-volume industries: {available_industries}")

        # Priority 1: Scan high-volume industries first (40% focus)
        industry_news = []
        for industry in available_industries[:5]:  # Top 5 industries
            print(f"[INFO] Scanning {industry} industry...")
            industry_items = await self.apis.scan_industry_news(industry)
            industry_news.extend(industry_items)

        # Priority 2: Scan our 20 INTEGRATED SOURCES (60% focus)
        print(f"[INFO] Scanning 20 Integrated News Sources...")
        integrated_news = []
        
        # Fetch all our integrated sources
        integrated_items = await self.integrated_sources.fetch_all_integrated_sources()
        integrated_news.extend(integrated_items)
        print(f"   📰 Integrated Sources: {len(integrated_items)} items")
        
        # Also scan existing RSS feeds for additional coverage
        reuters_items = await self.apis.scan_reuters_rss()
        integrated_news.extend(reuters_items)
        print(f"   📰 Reuters: {len(reuters_items)} items")
        
        cnbc_items = await self.apis.scan_cnbc_rss()
        integrated_news.extend(cnbc_items)
        print(f"   📰 CNBC: {len(cnbc_items)} items")
        
        finnhub_items = await self.apis.scan_finnhub_news()
        integrated_news.extend(finnhub_items)
        print(f"   📰 Finnhub: {len(finnhub_items)} items")

        # Combine all sources
        all_news_items = industry_news + integrated_news
        seen_symbols = set()
        unique_news_items = []

        for item in all_news_items:
            symbol = item.get('symbol')
            if symbol and symbol not in seen_symbols:
                seen_symbols.add(symbol)
                unique_news_items.append(item)

        print(f"[INFO] Combined scan: {len(industry_news)} industry + {len(integrated_news)} integrated = {len(unique_news_items)} unique symbols")

        # Apply fact checking to each news item
        for item in unique_news_items:
            fact_check = self._fact_check_company(item, all_sectors_mode)
            if not isinstance(fact_check, dict):
                fact_check = {'is_valid': False, 'validation_score': 0.0, 'company_info': {}}
            if 'is_valid' not in fact_check:
                fact_check['is_valid'] = False
            item['fact_check'] = fact_check

        # Filter to only real companies
        real_news_items = [
            item for item in unique_news_items
            if item.get('fact_check', {}).get('is_valid', False)
            and item.get('fact_check', {}).get('company_info', {}).get('real_ticker', False)
        ]

        # Apply fundamental qualitative filters BEFORE options loading (performance optimization)
        print(f"[DEBUG] Applying fundamental filters to {len(real_news_items)} real companies:")
        filtered_items = []
        for item in real_news_items:
            company_info = item.get('fact_check', {}).get('company_info', {})
            market_cap = company_info.get('market_cap', 0)
            avg_volume = company_info.get('avg_volume', 0)
            sector = company_info.get('sector', '')
            industry = company_info.get('industry', '')
            symbol = item.get('symbol', 'UNKNOWN')
            
            # Fundamental gates: require sector/industry, sufficient volume, market cap
            if not sector and not industry:
                print(f"  ❌ {symbol}: No sector/industry")
                continue
            if avg_volume and avg_volume < 500_000:
                print(f"  ❌ {symbol}: Volume too low ({avg_volume:,})")
                continue
            if market_cap and market_cap < 500_000_000:
                print(f"  ❌ {symbol}: Market cap too low (${market_cap/1e6:.1f}M)")
                continue
            
            print(f"  ✅ {symbol}: Passed fundamental filters")
            filtered_items.append(item)
        
        print(f"[INFO] Kept {len(filtered_items)} items after fundamental filters\n")

        # Filter by options criteria - use config values
        min_iv = self.config.get('trading.min_implied_volatility') or 20.0
        min_volume = self.config.get('trading.min_options_volume') or 100
        options_filtered_items = self.utils.filter_by_options_criteria(
            filtered_items, 
            min_iv=min_iv, 
            min_volume=min_volume
        )

        # If no items meet options criteria, don't trade on fake data
        if not options_filtered_items:
            print("[INFO] No real trading opportunities found - system will not generate fake data")
            print("[HINT] This is the correct behavior for real money trading")

        # Add options recommendations, expiry timing, and moonshot detection
        moonshot_count = 0
        for item in options_filtered_items:
            item['options_recommendation'] = self.utils.get_options_recommendation(item, stock_only_mode=True)
            item['optimal_expiry_days'] = self.utils.calculate_optimal_expiry(item)
            
            # Detect moonshot catalysts
            full_text = f"{item.get('title', '')} {item.get('description', '')}"
            moonshot_analysis = self.utils.detect_moonshot_catalyst(full_text)
            item['moonshot_analysis'] = moonshot_analysis
            
            if moonshot_analysis.get('is_moonshot'):
                moonshot_count += 1
                print(f"🚀 MOONSHOT DETECTED: {item.get('symbol')} - {moonshot_analysis.get('potential_move')} potential")
                print(f"   Keywords: {[kw['keyword'] for kw in moonshot_analysis.get('keywords_found', [])]}")

        print(f"[OK] Found {len(options_filtered_items)} tradable opportunities ({moonshot_count} moonshots) from {len(available_industries)} industries")
        return options_filtered_items

    async def _scan_single_source(self, source: str, symbols: List[str] = None) -> List[Dict[str, Any]]:
        """Scan a single news source"""
        try:
            if source == 'finnhub':
                return await self.apis.scan_finnhub_news()  # REAL-TIME NEWS!
            elif source == 'saurav_newsapi':
                return await self.apis.scan_saurav_newsapi()
            elif source == 'marketaux':
                return await self.apis.scan_marketaux(symbols)
            elif source == 'yahoo_rss':
                return await self.apis.scan_yahoo_rss(symbols)
            elif source == 'reuters_rss':
                return await self.apis.scan_reuters_rss()
            elif source == 'bbc_rss':
                return await self.apis.scan_bbc_rss()
            elif source == 'cnbc_rss':
                return await self.apis.scan_cnbc_rss()
            elif source == 'reddit_wsb':
                return await self.apis.scan_reddit_wallstreetbets_rss()
            elif source == 'thenews_api':
                return await self.apis.scan_thenews_api()
            else:
                return []
        except Exception as e:
            print(f"[ERROR] Error scanning {source}: {e}")
            return []

    def _calculate_layered_divergence(self, news_item: Dict) -> Dict:
        """Calculate layered divergence analysis"""
        return self.analyzer.calculate_layered_divergence(news_item)

    def detect_technical_patterns(self, news_items: List[Dict]) -> List[Dict]:
        """Detect technical patterns in news items"""
        return self.analyzer.detect_technical_patterns(news_items)

    def _calculate_pattern_position_size(self, confidence: float, fact_check: Dict, is_moonshot: bool) -> float:
        """Calculate position size based on pattern analysis"""
        return self.analyzer.calculate_position_size(confidence, fact_check, is_moonshot)

    def get_sector_trends(self, news_items: List[Dict]) -> Dict[str, Any]:
        """Get sector trend analysis"""
        return self.analyzer.analyze_sector_trends(news_items)

    def find_moonshot_opportunities(self, news_items: List[Dict]) -> List[Dict[str, Any]]:
        """Find potential moonshot opportunities"""
        return self.analyzer.identify_moonshot_opportunities(news_items)

    def get_real_companies(self) -> List[str]:
        """Get list of real companies we track"""
        return [symbol for symbol, info in self.company_db.items() if info.get('real', False)]

    def get_company_info(self, symbol: str) -> Optional[Dict]:
        """Get detailed company information"""
        return self.company_db.get(symbol.upper())
    
    # ========== SMART MEMORY BANK METHODS ==========
    
    async def start_news_collection_network(self):
        """Start 24/7 news collection from 58 RSS feeds"""
        if not self.news_network:
            print("[WARN] News Collection Network not initialized")
            return False
        
        try:
            print("[INFO] Starting 24/7 News Collection Network...")
            # Start network in background
            asyncio.create_task(self.news_network.start_network())
            print("[OK] News Collection Network started (58 RSS feeds, 60s interval)")
            return True
        except Exception as e:
            print(f"[ERROR] Failed to start News Collection Network: {e}")
            return False
    
    async def stop_news_collection_network(self):
        """Stop news collection network"""
        if not self.news_network:
            return
        
        try:
            await self.news_network.stop_network()
            print("[OK] News Collection Network stopped")
        except Exception as e:
            print(f"[ERROR] Failed to stop News Collection Network: {e}")
    
    def get_news_from_memory(self, symbol: str = None, hours_back: int = 24) -> List[Dict]:
        """
        Get news from Smart Memory Bank
        
        Args:
            symbol: Stock ticker (optional)
            hours_back: How many hours to look back
            
        Returns:
            List of news articles
        """
        if not self.memory_bank:
            print("[WARN] Smart Memory Bank not initialized")
            return []
        
        try:
            if symbol:
                return self.memory_bank.get_articles_by_symbol(symbol, hours_back=hours_back)
            else:
                # Get all recent articles
                return self.memory_bank.search_articles(hours_back=hours_back, limit=100)
        except Exception as e:
            print(f"[ERROR] Failed to retrieve news from memory: {e}")
            return []
    
    def search_news_memory(
        self, 
        keywords: List[str] = None,
        symbols: List[str] = None,
        hours_back: int = 24
    ) -> List[Dict]:
        """
        Search news in memory bank by keywords or symbols
        
        Args:
            keywords: List of keywords to search for
            symbols: List of stock tickers
            hours_back: How many hours to look back
            
        Returns:
            List of matching news articles
        """
        if not self.memory_bank:
            print("[WARN] Smart Memory Bank not initialized")
            return []
        
        try:
            return self.memory_bank.search_articles(
                keywords=keywords,
                symbols=symbols,
                hours_back=hours_back
            )
        except Exception as e:
            print(f"[ERROR] Failed to search news memory: {e}")
            return []
    
    def get_symbol_history(self, symbol: str, days_back: int = 30) -> Dict:
        """
        Get historical news analysis for a symbol
        
        Args:
            symbol: Stock ticker
            days_back: How many days to analyze
            
        Returns:
            Historical analysis dict with sentiment trends, source breakdown, etc.
        """
        if not self.memory_bank:
            print("[WARN] Smart Memory Bank not initialized")
            return {}
        
        try:
            return self.memory_bank.get_symbol_history(symbol, days_back=days_back)
        except Exception as e:
            print(f"[ERROR] Failed to get symbol history: {e}")
            return {}

    def build_latent_news_context(self, symbol: str, hours_back: int = 168) -> Dict[str, Any]:
        if not self.memory_bank or not symbol:
            return {}
        try:
            articles = self.memory_bank.get_articles_by_symbol(symbol, hours_back=hours_back, limit=50)
        except Exception:
            return {}
        if not articles:
            return {}
        symbol_upper = str(symbol).upper()
        risk_keywords = [
            "whale",
            "whales",
            "liquidation",
            "liquidations",
            "outflow",
            "outflows",
            "inflow",
            "inflows",
            "sell-off",
            "dump",
            "crackdown",
            "ban",
            "probe",
            "investigation",
            "lawsuit",
            "sanction",
            "sanctions",
        ]
        wsb_loss_keywords = [
            "loss update",
            "down $",
            "down -",
            "margin call",
            "blown up",
            "blew up",
            "portfolio destroyed",
            "account blown",
            "rip account",
            "bagholder",
            "bagholding",
        ]
        risk_events = []
        wsb_loss_events = []
        for a in articles:
            title = a.get("title", "")
            summary = a.get("summary", a.get("content", ""))
            text = f"{title} {summary}"
            text_lower = text.lower()
            try:
                sent = self.utils.calculate_sentiment(text)
            except Exception:
                sent = 0.0

            source_str = str(a.get("source", "")).lower()
            reddit_trading_subs = [
                "wallstreetbets",
                "daytrading",
                "trading",
                "options",
                "pennystocks",
                "cryptocurrency",
                "cryptotrading",
            ]
            is_reddit_trading_source = "reddit.com/r/" in source_str and any(
                sub in source_str for sub in reddit_trading_subs
            )
            is_wsb_loss = is_reddit_trading_source and any(
                kw in text_lower for kw in wsb_loss_keywords
            )

            is_risk = sent < 0 or any(k in text_lower for k in risk_keywords) or is_wsb_loss
            if not is_risk:
                continue

            ts_str = a.get("stored_at") or a.get("published") or a.get("fetch_time")
            event = {
                "title": title,
                "timestamp": ts_str,
                "sentiment": sent,
            }

            if is_wsb_loss:
                wsb_loss_events.append(event)
            risk_events.append(event)

        if not risk_events:
            return {}

        risk_count = len(risk_events)
        wsb_loss_count = len(wsb_loss_events)
        latest_ts = None
        for e in risk_events:
            ts_str = e.get("timestamp")
            if not ts_str:
                continue
            ts = None
            try:
                ts = datetime.fromisoformat(str(ts_str).replace("Z", "+00:00"))
            except Exception:
                ts = None
            if ts is None:
                continue
            if latest_ts is None or ts > latest_ts:
                latest_ts = ts
        age_hours = None
        if latest_ts is not None:
            try:
                age_hours = max(0.0, (datetime.now(latest_ts.tzinfo) - latest_ts).total_seconds() / 3600.0)
            except Exception:
                age_hours = max(0.0, (datetime.now() - latest_ts).total_seconds() / 3600.0)
        base_score = min(1.0, 0.2 * risk_count)
        if wsb_loss_count > 0:
            score = min(1.0, base_score + 0.3)
        else:
            score = base_score

        summary_parts = []
        if risk_count > 0:
            first = risk_events[0]
            if risk_count == 1:
                summary_parts.append(
                    f"Recent risk headline stored for {symbol_upper}: \"{first.get('title', '')[:120]}\""
                )
            else:
                summary_parts.append(
                    f"{risk_count} stored risk headlines for {symbol_upper} in the last {hours_back // 24} days. Latest: \"{first.get('title', '')[:120]}\""
                )

        if wsb_loss_count > 0:
            loss_example = wsb_loss_events[0]
            summary_parts.append(
                f"WSB loss memory: {wsb_loss_count} loss posts mentioning {symbol_upper}, e.g. \"{loss_example.get('title', '')[:120]}\""
            )

        summary = " ".join(summary_parts) if summary_parts else None

        return {
            "symbol": symbol_upper,
            "risk_article_count": risk_count,
            "latent_risk_score": score,
            "last_risk_age_hours": age_hours,
            "sample_events": risk_events[:3],
            "wsb_loss_event_count": wsb_loss_count,
            "wsb_loss_sample_events": wsb_loss_events[:3],
            "has_wsb_loss_events": wsb_loss_count > 0,
            "summary": summary,
        }
    
    def get_memory_stats(self) -> Dict:
        """Get Smart Memory Bank statistics"""
        if not self.memory_bank:
            return {'status': 'disabled'}
        
        try:
            return self.memory_bank.get_statistics()
        except Exception as e:
            print(f"[ERROR] Failed to get memory stats: {e}")
            return {'status': 'error', 'error': str(e)}
    
    def get_network_stats(self) -> Dict:
        """Get News Collection Network statistics"""
        if not self.news_network:
            return {'status': 'disabled'}
        
        try:
            return self.news_network.get_statistics()
        except Exception as e:
            print(f"[ERROR] Failed to get network stats: {e}")
            return {'status': 'error', 'error': str(e)}
    
    def cleanup_old_news(self, days_to_keep: int = 30) -> int:
        """
        Clean up old news from memory bank
        
        Args:
            days_to_keep: How many days of news to keep
            
        Returns:
            Number of articles removed
        """
        if not self.memory_bank:
            return 0
        
        try:
            return self.memory_bank.cleanup_old_articles(days_to_keep=days_to_keep)
        except Exception as e:
            print(f"[ERROR] Failed to cleanup old news: {e}")
            return 0
