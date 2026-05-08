"""
News-Insider Correlation Analyzer

Correlates news sentiment and patterns with insider trading activity:
- Identifies when insiders trade before major news
- Detects patterns of insider behavior around news events
- Provides comprehensive stock analysis combining news and insider data
"""

import json
import os
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from collections import defaultdict, Counter
import re

from .advanced_sentiment_engine import AdvancedSentimentEngine
from .news_pattern_recognition import NewsPatternRecognizer
from .insider_signal_integrator import SignalSource, ConfluenceSignal

class NewsInsiderCorrelator:
    """Correlates news sentiment with insider trading patterns"""
    
    def __init__(self, config: dict = None):
        self.config = config or {}
        
        # Initialize component engines
        self.sentiment_engine = AdvancedSentimentEngine(config)
        self.pattern_recognizer = NewsPatternRecognizer(config)
        
        # Data files
        self.correlation_file = os.path.join(
            os.path.dirname(__file__), '..', 'data', 'news_insider_correlations.json'
        )
        self.correlations = self._load_correlations()
        
        # Time windows for analysis
        self.time_windows = {
            'pre_news': {
                '1_week': 7,
                '2_weeks': 14,
                '1_month': 30
            },
            'post_news': {
                '1_day': 1,
                '3_days': 3,
                '5_days': 5,
                '10_days': 10
            }
        }
        
        # Insider trading data cache
        self.insider_data = {}
        
    def _load_correlations(self) -> Dict:
        """Load existing correlation data"""
        if os.path.exists(self.correlation_file):
            try:
                with open(self.correlation_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        return {
            'correlations': {},
            'patterns': {},
            'predictions': [],
            'accuracy': {}
        }
    
    def analyze_stock_correlation(self, ticker: str, news_items: List[Dict], 
                                insider_trades: List[Dict]) -> Dict:
        """
        Analyze correlation between news sentiment and insider trading for a stock
        
        Args:
            ticker: Stock symbol
            news_items: List of news articles
            insider_trades: List of insider trading data
            
        Returns:
            Comprehensive correlation analysis
        """
        analysis = {
            'ticker': ticker,
            'analysis_date': datetime.now().isoformat(),
            'overall_score': 0.0,
            'sentiment_analysis': {},
            'insider_activity': {},
            'correlations': [],
            'key_insights': [],
            'warnings': [],
            'opportunities': [],
            'historical_patterns': {},
            'prediction': {}
        }
        
        # Analyze news sentiment
        if news_items:
            analysis['sentiment_analysis'] = self._analyze_news_sentiment_batch(
                ticker, news_items
            )
        
        # Analyze insider activity
        if insider_trades:
            analysis['insider_activity'] = self._analyze_insider_activity(
                ticker, insider_trades
            )
        
        # Find correlations
        if news_items and insider_trades:
            analysis['correlations'] = self._find_correlations(
                news_items, insider_trades
            )
            
            # Generate insights
            analysis['key_insights'] = self._generate_insights(
                analysis['correlations']
            )
            
            # Identify warnings
            analysis['warnings'] = self._identify_warnings(
                analysis['correlations']
            )
            
            # Find opportunities
            analysis['opportunities'] = self._find_opportunities(
                analysis['correlations']
            )
        
        # Get historical patterns
        analysis['historical_patterns'] = self._get_historical_patterns(ticker)
        
        # Generate prediction
        analysis['prediction'] = self._generate_prediction(analysis)
        
        # Calculate overall score
        analysis['overall_score'] = self._calculate_overall_score(analysis)
        
        # Save for future learning
        self._save_correlation_data(ticker, analysis)
        
        return analysis
    
    def _analyze_news_sentiment_batch(self, ticker: str, news_items: List[Dict]) -> Dict:
        """Analyze sentiment for multiple news items"""
        sentiments = []
        patterns = []
        
        for news in news_items:
            sentiment = self.sentiment_engine.analyze_news_sentiment(news)
            sentiments.append(sentiment)
            
            pattern = self.pattern_recognizer.analyze_news_pattern(ticker, news)
            patterns.append(pattern)
        
        # Aggregate results
        return {
            'total_articles': len(news_items),
            'avg_surface_sentiment': np.mean([s['surface_sentiment'] for s in sentiments]),
            'avg_implied_sentiment': np.mean([s['implied_sentiment'] for s in sentiments]),
            'confidence': np.mean([s['confidence'] for s in sentiments]),
            'key_patterns': Counter([p['pattern_type'] for p in patterns if p['pattern_type']]),
            'red_flags': list(set([flag for s in sentiments for flag in s['red_flags']])),
            'implications': list(set([imp for s in sentiments for imp in s['implications']]))
        }
    
    def _analyze_insider_activity(self, ticker: str, insider_trades: List[Dict]) -> Dict:
        """Analyze insider trading activity"""
        if not insider_trades:
            return {}
        
        # Classify trades
        buys = [t for t in insider_trades if t.get('action') == 'BUY']
        sells = [t for t in insider_trades if t.get('action') == 'SELL']
        
        # Calculate totals
        total_buy_value = sum(t.get('value', 0) for t in buys)
        total_sell_value = sum(t.get('value', 0) for t in sells)
        
        # Recent activity (last 30 days)
        cutoff_date = datetime.now() - timedelta(days=30)
        recent_trades = [
            t for t in insider_trades 
            if datetime.fromisoformat(t.get('date', '')) >= cutoff_date
        ]
        
        return {
            'total_trades': len(insider_trades),
            'buy_trades': len(buys),
            'sell_trades': len(sells),
            'buy_value': total_buy_value,
            'sell_value': total_sell_value,
            'net_activity': total_buy_value - total_sell_value,
            'recent_trades': len(recent_trades),
            'top_buyers': self._get_top_insiders(buys),
            'top_sellers': self._get_top_insiders(sells),
            'buy_sell_ratio': len(buys) / len(sells) if sells else float('inf')
        }
    
    def _get_top_insiders(self, trades: List[Dict], limit: int = 5) -> List[Dict]:
        """Get top insiders by trade value"""
        insider_totals = defaultdict(float)
        for trade in trades:
            insider = trade.get('insider_name', 'Unknown')
            insider_totals[insider] += trade.get('value', 0)
        
        return sorted(
            [{'insider': k, 'total_value': v} for k, v in insider_totals.items()],
            key=lambda x: x['total_value'],
            reverse=True
        )[:limit]
    
    def _find_correlations(self, news_items: List[Dict], 
                          insider_trades: List[Dict]) -> List[Dict]:
        """Find correlations between news and insider trades"""
        correlations = []
        
        for news in news_items:
            news_date = datetime.fromisoformat(news.get('published_date', ''))
            
            # Find insider trades before and after news
            pre_news_trades = self._get_trades_in_window(
                insider_trades, news_date, before=True
            )
            post_news_trades = self._get_trades_in_window(
                insider_trades, news_date, before=False
            )
            
            # Analyze correlation
            if pre_news_trades or post_news_trades:
                correlation = {
                    'news_title': news.get('title', ''),
                    'news_date': news_date.isoformat(),
                    'news_sentiment': self.sentiment_engine.analyze_news_sentiment(news),
                    'pre_news_activity': pre_news_trades,
                    'post_news_activity': post_news_trades,
                    'correlation_score': 0.0,
                    'pattern_detected': None
                }
                
                # Detect patterns
                correlation['pattern_detected'] = self._detect_insider_pattern(
                    pre_news_trades, post_news_trades, correlation['news_sentiment']
                )
                
                # Calculate correlation score
                correlation['correlation_score'] = self._calculate_correlation_score(
                    correlation
                )
                
                correlations.append(correlation)
        
        # Sort by correlation score
        correlations.sort(key=lambda x: x['correlation_score'], reverse=True)
        
        return correlations
    
    def _get_trades_in_window(self, trades: List[Dict], date: datetime, 
                             before: bool = True, days: int = 14) -> List[Dict]:
        """Get trades within a time window"""
        window_start = date - timedelta(days=days) if before else date
        window_end = date if before else date + timedelta(days=days)
        
        return [
            trade for trade in trades
            if window_start <= datetime.fromisoformat(trade.get('date', '')) <= window_end
        ]
    
    def _detect_insider_pattern(self, pre_trades: List[Dict], 
                               post_trades: List[Dict], 
                               sentiment: Dict) -> Optional[str]:
        """Detect insider trading patterns around news"""
        pre_buy_value = sum(t.get('value', 0) for t in pre_trades if t.get('action') == 'BUY')
        pre_sell_value = sum(t.get('value', 0) for t in pre_trades if t.get('action') == 'SELL')
        
        # Pattern 1: Insiders buy before good news
        if pre_buy_value > pre_sell_value and sentiment['implied_sentiment'] > 0.3:
            return "BULLISH_INSIDER_KNOWLEDGE"
        
        # Pattern 2: Insiders sell before bad news
        if pre_sell_value > pre_buy_value and sentiment['implied_sentiment'] < -0.3:
            return "BEARISH_INSIDER_KNOWLEDGE"
        
        # Pattern 3: Insiders buy after bad news (contrarian)
        if sentiment['implied_sentiment'] < -0.3:
            post_buy_value = sum(t.get('value', 0) for t in post_trades if t.get('action') == 'BUY')
            if post_buy_value > 0:
                return "CONTRARIAN_BUY_DIP"
        
        # Pattern 4: Heavy selling after good news (profit taking)
        if sentiment['implied_sentiment'] > 0.3:
            post_sell_value = sum(t.get('value', 0) for t in post_trades if t.get('action') == 'SELL')
            if post_sell_value > 100000:  # Significant selling
                return "INSIDER_PROFIT_TAKING"
        
        return None
    
    def _calculate_correlation_score(self, correlation: Dict) -> float:
        """Calculate correlation strength score"""
        score = 0.0
        
        # Base score from pattern detection
        if correlation['pattern_detected']:
            score += 0.5
        
        # Sentiment strength
        sentiment = correlation['news_sentiment']
        score += abs(sentiment['implied_sentiment']) * 0.3
        
        # Trade volume significance
        pre_total = sum(t.get('value', 0) for t in correlation['pre_news_activity'])
        if pre_total > 500000:  # $500k+ in trades
            score += 0.2
        
        return min(1.0, score)
    
    def _generate_insights(self, correlations: List[Dict]) -> List[str]:
        """Generate key insights from correlations"""
        insights = []
        
        if not correlations:
            return insights
        
        # Top correlation
        top_corr = correlations[0]
        if top_corr['correlation_score'] > 0.7:
            insights.append(
                f"Strong correlation detected: {top_corr['pattern_detected']}"
            )
        
        # Pattern frequency
        patterns = [c['pattern_detected'] for c in correlations if c['pattern_detected']]
        if patterns:
            most_common = Counter(patterns).most_common(1)[0]
            insights.append(
                f"Most common pattern: {most_common[0]} ({most_common[1]} occurrences)"
            )
        
        # Sentiment alignment
        positive_sentiments = [c for c in correlations 
                            if c['news_sentiment']['implied_sentiment'] > 0.3]
        if len(positive_sentiments) > len(correlations) * 0.6:
            insights.append("Predominantly positive news sentiment detected")
        
        return insights
    
    def _identify_warnings(self, correlations: List[Dict]) -> List[str]:
        """Identify warning signs"""
        warnings = []
        
        for corr in correlations:
            # Heavy selling before bad news
            if (corr['pattern_detected'] == "BEARISH_INSIDER_KNOWLEDGE" 
                and corr['correlation_score'] > 0.8):
                warnings.append(
                    f"⚠️ Insiders sold heavily before negative news: {corr['news_title'][:50]}..."
                )
            
            # Red flags in news
            if corr['news_sentiment']['red_flags']:
                warnings.append(
                    f"⚠️ News contains red flags: {', '.join(corr['news_sentiment']['red_flags'])}"
                )
        
        return warnings
    
    def _find_opportunities(self, correlations: List[Dict]) -> List[Dict]:
        """Find trading opportunities"""
        opportunities = []
        
        for corr in correlations:
            # Bullish insider knowledge with high confidence
            if (corr['pattern_detected'] == "BULLISH_INSIDER_KNOWLEDGE"
                and corr['correlation_score'] > 0.7):
                
                opportunities.append({
                    'type': 'BULLISH_OPPORTUNITY',
                    'confidence': corr['correlation_score'],
                    'reason': f"Insiders bought before positive news: {corr['news_title'][:50]}...",
                    'sentiment': corr['news_sentiment']['implied_sentiment'],
                    'insider_activity': sum(t.get('value', 0) 
                                          for t in corr['pre_news_activity'] 
                                          if t.get('action') == 'BUY')
                })
            
            # Contrarian buy dip
            elif corr['pattern_detected'] == "CONTRARIAN_BUY_DIP":
                opportunities.append({
                    'type': 'CONTRARIAN_OPPORTUNITY',
                    'confidence': corr['correlation_score'] * 0.8,
                    'reason': f"Insiders buying after negative news: {corr['news_title'][:50]}...",
                    'sentiment': corr['news_sentiment']['implied_sentiment']
                })
        
        return opportunities
    
    def _get_historical_patterns(self, ticker: str) -> Dict:
        """Get historical patterns for the ticker"""
        return self.pattern_recognizer.get_top_patterns(ticker)
    
    def _generate_prediction(self, analysis: Dict) -> Dict:
        """Generate overall prediction based on all analysis"""
        prediction = {
            'direction': 'NEUTRAL',
            'confidence': 0.0,
            'expected_move': 0.0,
            'timeframe': '5-10 days',
            'key_factors': [],
            'risk_level': 'MEDIUM'
        }
        
        # Factor in opportunities
        if analysis['opportunities']:
            opp = analysis['opportunities'][0]
            if opp['type'] == 'BULLISH_OPPORTUNITY':
                prediction['direction'] = 'BULLISH'
                prediction['confidence'] = opp['confidence']
                prediction['key_factors'].append('Bullish insider activity')
            elif opp['type'] == 'CONTRARIAN_OPPORTUNITY':
                prediction['direction'] = 'BULLISH'
                prediction['confidence'] = opp['confidence'] * 0.7
                prediction['key_factors'].append('Contrarian insider buying')
        
        # Factor in warnings
        if analysis['warnings']:
            prediction['confidence'] *= 0.7
            prediction['risk_level'] = 'HIGH'
            prediction['key_factors'].append('Warning signs detected')
        
        # Factor in sentiment
        if analysis['sentiment_analysis']:
            avg_sentiment = analysis['sentiment_analysis']['avg_implied_sentiment']
            if abs(avg_sentiment) > 0.3:
                if avg_sentiment > 0 and prediction['direction'] != 'BEARISH':
                    prediction['direction'] = 'BULLISH'
                elif avg_sentiment < 0 and prediction['direction'] != 'BULLISH':
                    prediction['direction'] = 'BEARISH'
                prediction['key_factors'].append(f'Sentiment: {avg_sentiment:.2f}')
        
        # Calculate expected move based on confidence
        prediction['expected_move'] = prediction['confidence'] * 0.08  # Max 8%
        
        return prediction
    
    def _calculate_overall_score(self, analysis: Dict) -> float:
        """Calculate overall correlation score"""
        score = 0.0
        
        # Correlation strength
        if analysis['correlations']:
            avg_corr = np.mean([c['correlation_score'] for c in analysis['correlations']])
            score += avg_corr * 0.4
        
        # Opportunity quality
        if analysis['opportunities']:
            opp_confidence = np.mean([o['confidence'] for o in analysis['opportunities']])
            score += opp_confidence * 0.3
        
        # Sentiment clarity
        if analysis['sentiment_analysis']:
            sentiment_conf = analysis['sentiment_analysis']['confidence']
            score += sentiment_conf * 0.2
        
        # Data completeness
        if analysis['sentiment_analysis'] and analysis['insider_activity']:
            score += 0.1
        
        return min(1.0, score)
    
    def _save_correlation_data(self, ticker: str, analysis: Dict):
        """Save correlation data for future learning"""
        if ticker not in self.correlations['correlations']:
            self.correlations['correlations'][ticker] = []
        
        self.correlations['correlations'][ticker].append({
            'date': analysis['analysis_date'],
            'score': analysis['overall_score'],
            'prediction': analysis['prediction'],
            'patterns': [c['pattern_detected'] for c in analysis['correlations']]
        })
        
        # Save to file
        try:
            with open(self.correlation_file, 'w') as f:
                json.dump(self.correlations, f, indent=2)
        except Exception as e:
            print(f"Error saving correlations: {e}")
    
    def get_comprehensive_report(self, ticker: str) -> str:
        """Generate a human-readable comprehensive report"""
        # This would fetch and analyze current data
        # For now, return a template
        return f"""
=== COMPREHENSIVE STOCK ANALYSIS: {ticker} ===

[This report would include:]
- Recent news sentiment analysis
- Insider trading activity summary
- Key correlations detected
- Historical patterns
- Current opportunities
- Risk assessment
- Price prediction

[Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}]
"""
