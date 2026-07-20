"""
Universal Trading Intelligence System
Applies deep understanding and multi-source confirmation to ALL trading strategies
"""

import asyncio
import sys
import os

_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _root not in sys.path:
    sys.path.insert(0, _root)

from datetime import datetime, timedelta
import json
import re
from typing import List, Dict, Tuple, Optional, TYPE_CHECKING
from enum import Enum

from utils.discovery_limits import is_max_discovery

if TYPE_CHECKING:
    from utils.cycle_data_context import CycleDataContext

class TradeType(Enum):
    """All trade types with deep understanding requirements"""
    BULL_RUN = "bull_run"
    BEAR_DROP = "bear_drop"
    EARNINGS_PLAY = "earnings_play"
    MERGER_ARBITRAGE = "merger_arbitrage"
    SECTOR_ROTATION = "sector_rotation"
    MOMENTUM_SWING = "momentum_swing"
    MEAN_REVERSION = "mean_reversion"
    OPTIONS_FLOW = "options_flow"
    INSIDER_TRADING = "insider_trading"
    CATALYST_EVENT = "catalyst_event"
    TECHNICAL_BREAKOUT = "technical_breakout"
    SENTIMENT_SHIFT = "sentiment_shift"
    MACRO_EVENT = "macro_event"
    CRYPTO_MOMENTUM = "crypto_momentum"
    COMMODITY_TREND = "commodity_trend"

class UniversalTradingIntelligence:
    """AI with deep understanding of all trading strategies"""

    NOISE_SYMBOLS = None  # set in __init__ from NewsUtils
    
    def __init__(self, config, news_sources=None):
        self.config = config
        from utils.price_filter_config import apply_price_threshold
        apply_price_threshold(config, self)
        from engines.news_engine_utils import NewsUtils
        self._news_utils = NewsUtils
        self.NOISE_SYMBOLS = NewsUtils.EXTRACTION_STOPWORDS | NewsUtils.BLOCKED_SYMBOLS
        
        # Import modules
        from utils.price_fetcher import get_price_fetcher
        self.price_fetcher = get_price_fetcher()
        
        if news_sources is None:
            from engines.news_engine_integrated import IntegratedNewsSources
            self.news_sources = IntegratedNewsSources(config)
        else:
            self.news_sources = news_sources
        
        # Deep understanding for each trade type
        self.trade_intelligence = {
            TradeType.BULL_RUN: {
                'what_to_look_for': [
                    'volume_surge', 'institutional_buying', 'breakout_patterns',
                    'catalyst_events', 'sector_momentum', 'technical_momentum'
                ],
                'confirmation_sources': 2,
                'min_score': 5.0,
                'timeframe': '7-14 days',
                'success_rate': 0.75
            },
            TradeType.BEAR_DROP: {
                'what_to_look_for': [
                    'volume_surge_sell', 'institutional_selling', 'breakdown_patterns',
                    'negative_catalyst', 'sector_weakness', 'bearish_technical'
                ],
                'confirmation_sources': 2,
                'min_score': 5.0,
                'timeframe': '7-14 days',
                'success_rate': 0.70
            },
            TradeType.EARNINGS_PLAY: {
                'what_to_look_for': [
                    'pre_earnings_leak', 'whisper_numbers', 'options_activity',
                    'historical_beat_rate', 'sector_earnings_trend', 'guidance_hint'
                ],
                'confirmation_sources': 3,
                'min_score': 6.0,
                'timeframe': '1-3 days',
                'success_rate': 0.65
            },
            TradeType.MERGER_ARBITRAGE: {
                'what_to_look_for': [
                    'merger_rumor', 'arbitrage_opportunity', 'regulatory_approval',
                    'shareholder_approval', 'competing_bids', 'deal_certainty'
                ],
                'confirmation_sources': 3,
                'min_score': 7.0,
                'timeframe': '30-90 days',
                'success_rate': 0.85
            },
            TradeType.SECTOR_ROTATION: {
                'what_to_look_for': [
                    'sector_inflow', 'etf_accumulation', 'economic_shift',
                    'industry_trend', 'fund_reallocation', 'relative_strength'
                ],
                'confirmation_sources': 2,
                'min_score': 4.0,
                'timeframe': '14-30 days',
                'success_rate': 0.60
            },
            TradeType.MOMENTUM_SWING: {
                'what_to_look_for': [
                    'price_momentum', 'volume_confirmation', 'pattern_breakout',
                    'trend_continuation', 'volatility_expansion', 'sector_sync'
                ],
                'confirmation_sources': 2,
                'min_score': 4.0,
                'timeframe': '3-7 days',
                'success_rate': 0.55
            },
            TradeType.MEAN_REVERSION: {
                'what_to_look_for': [
                    'extreme_deviation', 'oversold_rsi', 'support_test',
                    'reversal_pattern', 'volume_dry_up', 'contrarian_sentiment'
                ],
                'confirmation_sources': 2,
                'min_score': 4.0,
                'timeframe': '5-10 days',
                'success_rate': 0.60
            },
            TradeType.OPTIONS_FLOW: {
                'what_to_look_for': [
                    'unusual_options_activity', 'block_trades', 'call_put_ratio',
                    'strike_accumulation', 'date_concentration', 'smart_money_flow'
                ],
                'confirmation_sources': 2,
                'min_score': 5.0,
                'timeframe': '1-5 days',
                'success_rate': 0.65
            },
            TradeType.INSIDER_TRADING: {
                'what_to_look_for': [
                    'form4_buying', 'offmarket_purchases', 'cluster_buying',
                    'director_confidence', 'executive_options', 'shareholder_patterns'
                ],
                'confirmation_sources': 1,  # SEC filing is enough
                'min_score': 3.0,
                'timeframe': '30-60 days',
                'success_rate': 0.70
            },
            TradeType.CATALYST_EVENT: {
                'what_to_look_for': [
                    'fda_approval', 'patent_grant', 'contract_award',
                    'partnership_announcement', 'analyst_upgrade', 'rating_change'
                ],
                'confirmation_sources': 2,
                'min_score': 5.0,
                'timeframe': '1-7 days',
                'success_rate': 0.75
            },
            TradeType.TECHNICAL_BREAKOUT: {
                'what_to_look_for': [
                    'resistance_break', 'volume_spike', 'pattern_completion',
                    'moving_average_cross', 'momentum_shift', 'breakout_retest'
                ],
                'confirmation_sources': 2,
                'min_score': 4.0,
                'timeframe': '3-10 days',
                'success_rate': 0.55
            },
            TradeType.SENTIMENT_SHIFT: {
                'what_to_look_for': [
                    'sentiment_reversal', 'social_volume_surge', 'media_attention',
                    'analyst_consensus_shift', 'retail_interest', 'whisper_trend'
                ],
                'confirmation_sources': 2,
                'min_score': 4.0,
                'timeframe': '5-15 days',
                'success_rate': 0.50
            },
            TradeType.MACRO_EVENT: {
                'what_to_look_for': [
                    'fed_announcement', 'inflation_data', 'gdp_release',
                    'employment_data', 'geopolitical_event', 'market_impact'
                ],
                'confirmation_sources': 2,
                'min_score': 6.0,
                'timeframe': '1-7 days',
                'success_rate': 0.60
            },
            TradeType.CRYPTO_MOMENTUM: {
                'what_to_look_for': [
                    'crypto_volume_surge', 'whale_movement', 'exchange_inflow',
                    'defi_activity', 'social_sentiment', 'btc_correlation'
                ],
                'confirmation_sources': 2,
                'min_score': 4.0,
                'timeframe': '1-7 days',
                'success_rate': 0.45
            },
            TradeType.COMMODITY_TREND: {
                'what_to_look_for': [
                    'supply_demand_shift', 'inventory_data', 'geopolitical_impact',
                    'currency_correlation', 'seasonal_pattern', 'futures_activity'
                ],
                'confirmation_sources': 2,
                'min_score': 5.0,
                'timeframe': '14-30 days',
                'success_rate': 0.55
            }
        }

        self._relaxed_discovery = is_max_discovery(config)
        if self._relaxed_discovery:
            self._relax_trade_thresholds()

        # Source reliability scores
        self.source_reliability = {
            'sec_filings': 3.0,
            'company_press_release': 2.5,
            'regulatory_filing': 2.5,
            'major_news': 2.0,
            'analyst_report': 2.0,
            'institutional_report': 2.0,
            'exchange_filing': 2.0,
            'options_data': 2.0,
            'insider_tracking': 2.0,
            'kalshi': 2.0,
            'polymarket': 2.0,
            'technical_analysis': 1.5,
            'social_sentiment': 1.5,
            'news_aggregator': 1.0,
            'forum_discussion': 0.5
        }
        
        # Kalshi event templates for all trade types
        self.kalshi_templates = {
            TradeType.BULL_RUN: "Will {symbol} be above ${strike} in {days} days?",
            TradeType.BEAR_DROP: "Will {symbol} be below ${strike} in {days} days?",
            TradeType.EARNINGS_PLAY: "Will {symbol} beat earnings expectations?",
            TradeType.MERGER_ARBITRAGE: "Will the {symbol} merger be completed?",
            TradeType.SECTOR_ROTATION: "Will {sector} ETF outperform the market?",
            TradeType.MOMENTUM_SWING: "Will {symbol} be above ${strike} in {days} days?",
            TradeType.MEAN_REVERSION: "Will {symbol} revert to ${strike}?",
            TradeType.OPTIONS_FLOW: "Will {symbol} see unusual options activity?",
            TradeType.INSIDER_TRADING: "Will {symbol} rise after insider buying?",
            TradeType.CATALYST_EVENT: "Will {symbol} benefit from the catalyst?",
            TradeType.TECHNICAL_BREAKOUT: "Will {symbol} break resistance at ${strike}?",
            TradeType.SENTIMENT_SHIFT: "Will {symbol} sentiment improve?",
            TradeType.MACRO_EVENT: "Will the market react positively to {event}?",
            TradeType.CRYPTO_MOMENTUM: "Will {crypto} be above ${strike} in {days} days?",
            TradeType.COMMODITY_TREND: "Will {commodity} trend {direction}?"
        }

    _HYPE_BULL_WORDS = (
        'surge', 'soar', 'rocket', 'rally', 'jump', 'breakout', 'spike', 'bullish',
        'upgrade', 'beat', 'growth', 'record', 'partnership', 'deal', 'acquisition',
        'approval', 'launch', 'momentum', 'outperform', 'buy', 'raises', 'raised',
    )
    _HYPE_BEAR_WORDS = (
        'plunge', 'crash', 'drop', 'fall', 'slump', 'selloff', 'bearish', 'downgrade',
        'miss', 'cut', 'loss', 'weak', 'layoff', 'lawsuit', 'investigation', 'recall',
    )

    def _relax_trade_thresholds(self) -> None:
        """Loosen gates in max-discovery mode so real news can surface candidates."""
        for cfg in self.trade_intelligence.values():
            cfg['min_score'] = max(2.0, float(cfg['min_score']) * 0.6)
            cfg['confirmation_sources'] = max(1, int(cfg['confirmation_sources']) - 1)

    # region agent log
    def _debug_log(self, run_id: str, hypothesis_id: str, location: str, message: str, data: Dict):
        """Temporary debug instrumentation for session 28cc99."""
        try:
            payload = {
                "sessionId": "28cc99",
                "runId": run_id,
                "hypothesisId": hypothesis_id,
                "location": location,
                "message": message,
                "data": data,
                "pid": os.getpid(),
                "timestamp": int(datetime.now().timestamp() * 1000),
            }
            with open("debug-28cc99.log", "a", encoding="utf-8") as f:
                f.write(json.dumps(payload, default=str) + "\n")
        except Exception:
            pass
    # endregion
    
    async def analyze_all_opportunities(self, cycle_context: Optional["CycleDataContext"] = None) -> List[Dict]:
        """Analyze ALL trade types with deep understanding"""
        
        print("=" * 80)
        print("🧠 UNIVERSAL TRADING INTELLIGENCE - DEEP ANALYSIS")
        print("=" * 80)
        print("Analyzing ALL trading strategies with multi-source confirmation...")
        print("=" * 80)
        
        if cycle_context is not None:
            print("\n📊 Using cycle ingest snapshot (no re-fetch)...")
            all_data = self._intelligence_from_news(cycle_context.ingested_news)
        else:
            print("\n📊 Gathering intelligence from 20+ sources...")
            all_data = await self._gather_all_intelligence()
        print(f"   Collected {len(all_data)} data points")

        # region agent log
        source_counts = {}
        symbol_counts = {}
        for item in all_data:
            source = item.get('source') or 'missing_source'
            source_counts[source] = source_counts.get(source, 0) + 1
            symbol = item.get('symbol')
            if symbol:
                symbol_counts[symbol] = symbol_counts.get(symbol, 0) + 1
        self._debug_log(
            "pre-fix",
            "H6,H7,H8",
            "brain/universal_trading_intelligence.py:analyze_all_opportunities",
            "news-derived intelligence universe before trade scoring",
            {
                "data_points": len(all_data),
                "source_counts": source_counts,
                "unique_symbol_count": len(symbol_counts),
                "top_symbols": sorted(symbol_counts.items(), key=lambda item: item[1], reverse=True)[:20],
                "kalshi_live_input_present": any('kalshi' in str(item.get('source', '')).lower() for item in all_data),
                "polymarket_live_input_present": any('poly' in str(item.get('source', '')).lower() for item in all_data),
            },
        )
        # endregion
        
        # Analyze each trade type
        all_opportunities = []
        
        for trade_type in TradeType:
            print(f"\n🔍 Analyzing {trade_type.value.replace('_', ' ').title()} opportunities...")
            
            opportunities = await self._analyze_trade_type(trade_type, all_data)
            
            if opportunities:
                print(f"   ✅ Found {len(opportunities)} {trade_type.value} opportunities")
                all_opportunities.extend(opportunities)
            else:
                print(f"   ⚠️ No confirmed {trade_type.value} opportunities")
        
        # Sort by confidence score
        all_opportunities.sort(key=lambda x: x['confidence'], reverse=True)
        
        # Display top opportunities
        print("\n" + "=" * 80)
        print("🎯 TOP TRADING OPPORTUNITIES - ALL STRATEGIES")
        print("=" * 80)
        
        for i, opp in enumerate(all_opportunities[:10], 1):
            print(f"\n{i}. {opp['symbol']} - {opp['trade_type'].title()}")
            print(f"   Confidence: {opp['confidence']:.1%} | Success Rate: {opp['expected_success']:.1%}")
            print(f"   Timeframe: {opp['timeframe']} | Sources: {opp['confirmations']}")
            print(f"   Rationale: {opp['rationale']}")
            
            if opp.get('kalshi_event'):
                print(f"   Kalshi: {opp['kalshi_event']['title']}")
        
        return all_opportunities
    
    def _intelligence_from_news(self, news_items: List[Dict]) -> List[Dict]:
        """Build intelligence rows from pre-ingested news (no fetch)."""
        intelligence = []
        items = [dict(item) for item in news_items]
        self._news_utils.propagate_prices(items)
        for item in items:
            title = str(item.get('title') or '')
            summary = str(item.get('summary') or item.get('description') or '')
            text = f"{title} {summary}".strip()
            symbol = self._clean_symbol(item.get('symbol') or '')
            if not symbol:
                symbol = self._clean_symbol(self._extract_symbol(text))
            if not symbol and item.get('prediction_market'):
                symbol = self._clean_symbol(item.get('symbol') or self._extract_symbol(title))
            text_lower = text.lower()
            bullish_hits = sum(1 for w in self._HYPE_BULL_WORDS if w in text_lower)
            bearish_hits = sum(1 for w in self._HYPE_BEAR_WORDS if w in text_lower)
            sentiment = item.get('sentiment')
            if sentiment is None:
                if bullish_hits > bearish_hits:
                    sentiment = min(0.5 + bullish_hits * 0.1, 0.95)
                elif bearish_hits > bullish_hits:
                    sentiment = max(0.5 - bearish_hits * 0.1, 0.05)
                else:
                    sentiment = 0.5
            intelligence.append({
                'type': 'news',
                'source': item.get('source', '') or item.get('prediction_market', '') or 'news',
                'content': text,
                'title': title,
                'symbol': symbol,
                'timestamp': item.get('timestamp', '') or item.get('published', ''),
                'reliability': self._get_source_reliability(item.get('source', '')),
                'price': item.get('price') or item.get('current_price'),
                'news_match_score': float(item.get('news_match_score') or 0),
                'prediction_market': item.get('prediction_market'),
                'sentiment': float(sentiment) if sentiment is not None else 0.5,
                'bullish_hits': bullish_hits,
                'bearish_hits': bearish_hits,
            })
        self._news_utils.propagate_prices(intelligence)
        with_symbol = sum(1 for row in intelligence if row.get('symbol'))
        print(f"   Mapped {with_symbol}/{len(intelligence)} news rows to tickers")
        return intelligence

    async def _gather_all_intelligence(self) -> List[Dict]:
        """Gather all types of intelligence"""
        intelligence = []
        
        # News sources
        news_items = await self.news_sources.fetch_all_integrated_sources()
        self._news_utils.propagate_prices(news_items)
        for item in news_items:
            symbol = self._clean_symbol(item.get('symbol') or self._extract_symbol(item.get('title', '')))
            intelligence.append({
                'type': 'news',
                'source': item.get('source', ''),
                'content': f"{item.get('title', '')} {item.get('summary', '')}",
                'symbol': symbol,
                'timestamp': item.get('timestamp', ''),
                'reliability': self._get_source_reliability(item.get('source', '')),
                'price': item.get('price') or item.get('current_price'),
                'news_match_score': float(item.get('news_match_score') or 0),
                'prediction_market': item.get('prediction_market'),
            })
        
        # Add more data sources here (options flow, technical analysis, etc.)
        self._news_utils.propagate_prices(intelligence)
        
        return intelligence
    
    def _effective_confirmations(self, items: List[Dict]) -> int:
        """Count evidence breadth — multiple headlines or venues count, not only unique source strings."""
        sources = {
            str(i.get('source') or '').strip().lower()
            for i in items
            if str(i.get('source') or '').strip()
        }
        evidence = len(sources) if sources else 0
        if len(items) >= 2:
            evidence = max(evidence, 2)
        if any(float(i.get('news_match_score') or 0) >= 40 for i in items):
            evidence = max(evidence, 2)
        if any(i.get('prediction_market') for i in items):
            evidence = max(evidence, 2)
        if any(int(i.get('bullish_hits') or 0) >= 2 or int(i.get('bearish_hits') or 0) >= 2 for i in items):
            evidence = max(evidence, 2)
        return max(evidence, 1)

    async def _analyze_trade_type(self, trade_type: TradeType, data: List[Dict]) -> List[Dict]:
        """Analyze specific trade type with deep understanding"""
        
        intelligence = self.trade_intelligence[trade_type]
        opportunities = []
        
        # Group data by symbol
        symbol_data = {}
        for item in data:
            symbol = item.get('symbol')
            if symbol:
                if symbol not in symbol_data:
                    symbol_data[symbol] = []
                symbol_data[symbol].append(item)
        
        # Analyze each symbol
        for symbol, items in symbol_data.items():
            # Check if symbol meets trade type criteria
            score = self._calculate_trade_score(trade_type, items)
            confirmations = self._effective_confirmations(items)
            
            # Check minimum requirements
            if confirmations < intelligence['confirmation_sources']:
                continue
            
            if score < intelligence['min_score']:
                continue
            
            price = next((item.get('price') for item in items if item.get('price')), None)
            if not price:
                try:
                    price = self.price_fetcher.get_real_price(symbol)
                except Exception:
                    price = None
            high_conviction = score >= intelligence['min_score'] * 1.25 or any(
                float(i.get('news_match_score') or 0) >= 55 for i in items
            )
            if not price and not high_conviction:
                continue
            
            try:
                price = float(price) if price is not None else 0.0
            except (TypeError, ValueError):
                if not high_conviction:
                    continue
                price = 0.0
            
            if (
                price > 0
                and self.price_filter_enabled
                and self.price_threshold is not None
                and price > self.price_threshold
                and trade_type not in [TradeType.MACRO_EVENT, TradeType.COMMODITY_TREND]
            ):
                continue
            
            # Create opportunity
            opportunity = {
                'symbol': symbol,
                'trade_type': trade_type.value,
                'confidence': min(score / 10, 0.95),
                'expected_success': intelligence['success_rate'],
                'timeframe': intelligence['timeframe'],
                'confirmations': confirmations,
                'sources': list(set(item['source'] for item in items)),
                'score': score,
                'current_price': price,
                'rationale': self._generate_rationale(trade_type, items),
                'evidence': items[:3]  # Top 3 evidence
            }
            
            # Add Kalshi event
            opportunity['kalshi_event'] = self._create_kalshi_event(trade_type, symbol, price, opportunity)
            
            opportunities.append(opportunity)
        
        return opportunities
    
    def _calculate_trade_score(self, trade_type: TradeType, items: List[Dict]) -> float:
        """Calculate score based on trade type intelligence"""
        intelligence = self.trade_intelligence[trade_type]
        score = 0.0
        
        for item in items:
            content = item['content'].upper()
            reliability = item['reliability']
            
            # Check for relevant indicators
            for indicator in intelligence['what_to_look_for']:
                if self._has_indicator(content, indicator):
                    score += reliability

            # News-aligned prediction markets: sector/ticker hint without full keyword match
            match_score = float(item.get('news_match_score') or 0)
            if match_score > 0 and (item.get('symbol') or item.get('prediction_market')):
                score += min(match_score / 25.0, 4.0) * reliability

            # Headline hype / sentiment alignment
            bullish = int(item.get('bullish_hits') or 0)
            bearish = int(item.get('bearish_hits') or 0)
            if trade_type in (TradeType.BULL_RUN, TradeType.MOMENTUM_SWING, TradeType.CATALYST_EVENT):
                score += min(bullish, 4) * 0.75
            if trade_type in (TradeType.BEAR_DROP, TradeType.MEAN_REVERSION):
                score += min(bearish, 4) * 0.75
            if trade_type == TradeType.SENTIMENT_SHIFT and (bullish >= 2 or bearish >= 2):
                score += 2.0
            if trade_type == TradeType.EARNINGS_PLAY and any(
                w in content.lower() for w in ('earnings', 'revenue', 'eps', 'guidance', 'quarter')
            ):
                score += 2.5
            if trade_type == TradeType.MERGER_ARBITRAGE and any(
                w in content.lower() for w in ('merger', 'acquisition', 'buyout', 'takeover', 'deal')
            ):
                score += 2.5
            if trade_type == TradeType.CRYPTO_MOMENTUM:
                sym = str(item.get('symbol') or '').upper()
                if sym in ('BTC', 'ETH', 'SOL', 'COIN', 'MSTR', 'MARA', 'RIOT') or 'BITCOIN' in content or 'CRYPTO' in content:
                    score += 2.0

            try:
                sent = float(item.get('sentiment', 0.5))
                if trade_type in (TradeType.BULL_RUN, TradeType.MOMENTUM_SWING) and sent > 0.55:
                    score += (sent - 0.5) * 4
                if trade_type in (TradeType.BEAR_DROP,) and sent < 0.45:
                    score += (0.5 - sent) * 4
            except (TypeError, ValueError):
                pass

        # Multiple headlines on same ticker = stronger signal
        if len(items) >= 2:
            score += min(len(items), 4) * 0.5
        
        return score
    
    def _has_indicator(self, content: str, indicator: str) -> bool:
        """Check if content has specific indicator keywords or token hints."""
        text = content.lower()
        keywords = {
            'volume_surge': ['volume', 'spike', 'unusual', 'heavy', 'surge'],
            'volume_surge_sell': ['volume', 'spike', 'sell', 'selloff', 'heavy', 'plunge'],
            'institutional_buying': ['institutional', 'fund', 'whale', 'accumulation', 'inflow'],
            'institutional_selling': ['institutional', 'selling', 'outflow', 'distribution'],
            'breakout_patterns': ['breakout', 'resistance', 'new high', 'soar', 'rally'],
            'breakdown_patterns': ['breakdown', 'support', 'new low', 'selloff', 'plunge', 'crash'],
            'catalyst_events': ['approval', 'patent', 'contract', 'partnership', 'deal', 'launch'],
            'negative_catalyst': ['downgrade', 'recall', 'lawsuit', 'investigation', 'miss', 'layoff'],
            'earnings_beat': ['beat', 'exceed', 'top', 'better than', 'surprise'],
            'pre_earnings_leak': ['earnings', 'whisper', 'preview', 'guidance', 'quarter', 'eps'],
            'whisper_numbers': ['whisper', 'consensus', 'estimate', 'preview'],
            'merger_rumor': ['merger', 'acquisition', 'buyout', 'takeover', 'deal'],
            'arbitrage_opportunity': ['arbitrage', 'spread', 'merger', 'acquisition'],
            'options_activity': ['options', 'calls', 'puts', 'unusual'],
            'unusual_options_activity': ['options', 'calls', 'puts', 'unusual', 'flow'],
            'form4_buying': ['insider', 'form 4', 'form4', 'director', 'executive', 'sec filing'],
            'insider_buying': ['insider', 'form 4', 'form4', 'director', 'executive'],
            'technical_breakout': ['golden cross', 'rsi', 'macd', 'moving average', 'breakout'],
            'sentiment_reversal': ['sentiment', 'bullish', 'bearish', 'shift', 'turnaround'],
            'sector_momentum': ['sector', 'rally', 'rotation', 'outperform', 'leadership'],
            'sector_inflow': ['sector', 'inflow', 'etf', 'rotation'],
            'sector_weakness': ['sector', 'weak', 'underperform', 'lag'],
            'macro_event': ['fed', 'inflation', 'gdp', 'employment', 'rate', 'tariff'],
            'fed_announcement': ['fed', 'fomc', 'rate', 'powell'],
            'fda_approval': ['fda', 'approval', 'clinical', 'trial', 'drug'],
            'patent_grant': ['patent', 'grant', 'intellectual'],
            'contract_award': ['contract', 'award', 'agreement', 'wins'],
            'partnership_announcement': ['partnership', 'collaboration', 'joint', 'deal'],
            'analyst_upgrade': ['upgrade', 'outperform', 'buy rating', 'raises target'],
            'rating_change': ['upgrade', 'downgrade', 'rating', 'target'],
            'price_momentum': ['momentum', 'rally', 'surge', 'soar', 'jump', 'gain'],
            'volume_confirmation': ['volume', 'momentum', 'breakout'],
            'pattern_breakout': ['breakout', 'pattern', 'resistance', 'flag'],
            'trend_continuation': ['trend', 'continuation', 'momentum', 'higher'],
            'volatility_expansion': ['volatility', 'volatile', 'swing', 'range'],
            'extreme_deviation': ['oversold', 'overbought', 'deviation', 'stretched'],
            'oversold_rsi': ['oversold', 'rsi', 'bounce'],
            'support_test': ['support', 'hold', 'bounce', 'floor'],
            'reversal_pattern': ['reversal', 'turnaround', 'bottom', 'recover'],
            'crypto_volume_surge': ['bitcoin', 'crypto', 'btc', 'ethereum', 'volume'],
            'whale_movement': ['whale', 'bitcoin', 'crypto', 'large transfer'],
            'supply_demand_shift': ['supply', 'demand', 'inventory', 'shortage', 'glut'],
            'geopolitical_impact': ['sanctions', 'war', 'geopolitical', 'tariff', 'conflict'],
        }

        if indicator in keywords:
            for keyword in keywords[indicator]:
                if keyword in text:
                    return True

        # Fallback: match underscore tokens (most declared indicators had no keyword map)
        for part in indicator.split('_'):
            if len(part) >= 4 and part in text:
                return True

        return False
    
    def _get_source_reliability(self, source: str) -> float:
        """Get reliability score for source"""
        source_lower = source.lower()
        
        if 'sec' in source_lower:
            return self.source_reliability['sec_filings']
        elif 'press' in source_lower:
            return self.source_reliability['company_press_release']
        elif any(x in source_lower for x in ['reuters', 'bloomberg', 'wsj']):
            return self.source_reliability['major_news']
        elif 'options' in source_lower:
            return self.source_reliability['options_data']
        elif 'kalshi' in source_lower or 'polymarket' in source_lower:
            return self.source_reliability['kalshi']
        elif any(x in source_lower for x in ('rss', 'yahoo', 'cnbc', 'reuters', 'finnhub')):
            return self.source_reliability['major_news']
        else:
            return self.source_reliability['news_aggregator']

    def _clean_symbol(self, symbol: str) -> str:
        """Drop obvious non-ticker terms before stock analysis."""
        symbol = str(symbol or '').upper().strip()
        if not symbol or len(symbol) > 5 or not symbol.isalpha():
            return ''
        if symbol in self.NOISE_SYMBOLS:
            return ''
        if not self._news_utils.is_valid_extracted_ticker(symbol):
            return ''
        return symbol
    
    def _extract_symbol(self, text: str) -> str:
        """Extract stock symbol from text using integrated engine rules."""
        return self.news_sources._extract_symbol(text)
    
    def _generate_rationale(self, trade_type: TradeType, items: List[Dict]) -> str:
        """Generate rationale for trade"""
        sources = list(set(item['source'] for item in items))
        return f"{trade_type.value.title()} confirmed by {len(sources)} sources: {', '.join(sources[:2])}"
    
    def _create_kalshi_event(self, trade_type: TradeType, symbol: str, price: float, opportunity: Dict) -> Optional[Dict]:
        """Create Kalshi event for trade"""
        template = self.kalshi_templates.get(trade_type)
        if not template:
            return None
        
        # Calculate strike based on trade type
        if trade_type in [TradeType.BULL_RUN, TradeType.MOMENTUM_SWING]:
            strike = round(price * 1.2, 2)
            days = 7
        elif trade_type == TradeType.BEAR_DROP:
            strike = round(price * 0.8, 2)
            days = 7
        else:
            strike = round(price * 1.1, 2)
            days = 10
        
        event = {
            'title': template.format(symbol=symbol, strike=strike, days=days),
            'symbol': symbol,
            'strike': strike,
            'days': days,
            'confidence': opportunity['confidence'],
            'trade_type': trade_type.value
        }
        
        return event

async def main():
    """Main function to run universal trading intelligence"""
    
    # Load config
    from config.secure_config import config
    
    # Initialize system
    uti = UniversalTradingIntelligence(config)
    
    # Analyze all opportunities
    opportunities = await uti.analyze_all_opportunities()
    
    if opportunities:
        # Save results
        import json
        results = {
            'timestamp': datetime.now().isoformat(),
            'total_opportunities': len(opportunities),
            'opportunities': opportunities[:20]  # Top 20
        }
        
        with open('universal_trading_signals.json', 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\n💾 Results saved to universal_trading_signals.json")
        print(f"🎯 Ready to trade {len(opportunities)} opportunities across all strategies!")
        
        return opportunities
    else:
        print("\n⚠️ No opportunities found at this time")
        return []

if __name__ == "__main__":
    opportunities = asyncio.run(main())
    
    if opportunities:
        print(f"\n✅ SUCCESS: Found {len(opportunities)} trading opportunities!")
    else:
        print("\n⏰ Check again later for new opportunities")
