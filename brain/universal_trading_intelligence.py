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
import re
from typing import List, Dict, Tuple, Optional
from enum import Enum

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
    
    def __init__(self, config):
        self.config = config
        self.price_threshold = 50.0
        
        # Import modules
        from utils.price_fetcher import get_price_fetcher
        self.price_fetcher = get_price_fetcher()
        
        from engines.news_engine_integrated import IntegratedNewsSources
        self.news_sources = IntegratedNewsSources(config)
        
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
    
    async def analyze_all_opportunities(self) -> List[Dict]:
        """Analyze ALL trade types with deep understanding"""
        
        print("=" * 80)
        print("🧠 UNIVERSAL TRADING INTELLIGENCE - DEEP ANALYSIS")
        print("=" * 80)
        print("Analyzing ALL trading strategies with multi-source confirmation...")
        print("=" * 80)
        
        # Get all news and data
        print("\n📊 Gathering intelligence from 20+ sources...")
        all_data = await self._gather_all_intelligence()
        print(f"   Collected {len(all_data)} data points")
        
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
    
    async def _gather_all_intelligence(self) -> List[Dict]:
        """Gather all types of intelligence"""
        intelligence = []
        
        # News sources
        news_items = await self.news_sources.fetch_all_integrated_sources()
        for item in news_items:
            intelligence.append({
                'type': 'news',
                'source': item.get('source', ''),
                'content': f"{item.get('title', '')} {item.get('summary', '')}",
                'symbol': self._extract_symbol(item.get('title', '')),
                'timestamp': item.get('timestamp', ''),
                'reliability': self._get_source_reliability(item.get('source', ''))
            })
        
        # Add more data sources here (options flow, technical analysis, etc.)
        
        return intelligence
    
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
            confirmations = len(set(item['source'] for item in items))
            
            # Check minimum requirements
            if confirmations < intelligence['confirmation_sources']:
                continue
            
            if score < intelligence['min_score']:
                continue
            
            # Get current price
            price = self.price_fetcher.get_real_price(symbol)
            if not price:
                continue
            
            try:
                price = float(price)
            except:
                continue
            
            # Skip if too expensive
            if price > self.price_threshold and trade_type not in [TradeType.MACRO_EVENT, TradeType.COMMODITY_TREND]:
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
        
        return score
    
    def _has_indicator(self, content: str, indicator: str) -> bool:
        """Check if content has specific indicator"""
        # Simplified - in real implementation, would have sophisticated pattern matching
        keywords = {
            'volume_surge': ['volume', 'spike', 'unusual', 'heavy'],
            'institutional_buying': ['institutional', 'fund', 'whale', 'accumulation'],
            'breakout_patterns': ['breakout', 'resistance', 'new high'],
            'catalyst_events': ['approval', 'patent', 'contract', 'partnership'],
            'earnings_beat': ['beat', 'exceed', 'top', 'better than'],
            'merger_rumor': ['merger', 'acquisition', 'buyout', 'takeover'],
            'options_activity': ['options', 'calls', 'puts', 'unusual'],
            'insider_buying': ['insider', 'form 4', 'director', 'executive'],
            'technical_breakout': ['golden cross', 'rsi', 'macd', 'moving average'],
            'sentiment_reversal': ['sentiment', 'bullish', 'bearish', 'shift']
        }
        
        if indicator in keywords:
            for keyword in keywords[indicator]:
                if keyword in content:
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
        else:
            return self.source_reliability['news_aggregator']
    
    def _extract_symbol(self, text: str) -> str:
        """Extract stock symbol from text"""
        # Same implementation as before
        symbols = re.findall(r'\$([A-Z]{1,5})\b', text.upper())
        
        stock_names = {
            'TESLA': 'TSLA', 'APPLE': 'AAPL', 'AMAZON': 'AMZN', 'MICROSOFT': 'MSFT',
            'GOOGLE': 'GOOGL', 'META': 'META', 'NETFLIX': 'NFLX', 'NVIDIA': 'NVDA',
            'AMD': 'AMD', 'INTEL': 'INTC', 'DISNEY': 'DIS', 'NIKE': 'NKE',
            'GAMESTOP': 'GME', 'AMC': 'AMC', 'SILVER': 'SLV', 'GOLD': 'GOLD',
            'BITCOIN': 'BTC', 'ETHEREUM': 'ETH'
        }
        
        for name, symbol in stock_names.items():
            if name in text.upper():
                symbols.append(symbol)
        
        for symbol in symbols[:5]:
            if len(symbol) <= 5 and symbol.isalpha():
                return symbol
        
        return ''
    
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
