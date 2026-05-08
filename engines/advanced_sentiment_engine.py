"""
Advanced Sentiment Engine - Reads Between the Lines in News

Analyzes news to understand what companies are REALLY saying:
- Detects implied meanings vs surface statements
- Identifies patterns of price movements after specific news types
- Correlates with insider trading data for comprehensive analysis
"""

import re
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from collections import defaultdict, Counter
import yfinance as yf
import pandas as pd

class AdvancedSentimentEngine:
    """Advanced sentiment analysis that reads between the lines"""
    
    def __init__(self, config: dict = None):
        self.config = config or {}
        
        # Pattern database for historical analysis
        self.pattern_db_file = os.path.join(
            os.path.dirname(__file__), '..', 'data', 'news_price_patterns.json'
        )
        self.patterns = self._load_patterns()
        
        # Insider trading correlation data
        self.insider_correlation_file = os.path.join(
            os.path.dirname(__file__), '..', 'data', 'insider_news_correlation.json'
        )
        self.insider_correlations = self._load_insider_correlations()
        
        # Advanced sentiment dictionaries
        self._init_sentiment_dictionaries()
        
        # Implication detection patterns
        self.implication_patterns = {
            'positive_implied': [
                r'expects (?:to|will) (?:beat|exceed|surpass)',
                r'confident in (?:growth|performance|outlook)',
                r'strong (?:demand|momentum|pipeline)',
                r'ahead of (?:schedule|guidance|expectations)',
                r'unprecedented (?:growth|demand|opportunity)',
                r'record (?:sales|revenue|earnings)',
                r'better than (?:expected|anticipated|forecast)',
                r'exceeding (?:guidance|estimates|targets)',
                r'dramatic (?:improvement|increase|growth)',
                r'transformational (?:deal|acquisition|partnership)'
            ],
            'negative_implied': [
                r'concerns about (?:growth|outlook|performance)',
                r'challenging (?:environment|conditions|market)',
                r'headwinds (?:expected|anticipated|likely)',
                r'below (?:expectations|guidance|estimates)',
                r'struggling (?:with|in|to)',
                r'declining (?:sales|demand|growth)',
                r'difficult (?:quarter|period|environment)',
                r'uncertain (?:future|outlook|prospect)',
                r'pressures (?:on|in|affecting)',
                r'weakening (?:demand|position|market)'
            ],
            'cautious_language': [
                r'may (?:impact|affect|result)',
                r'could (?:see|experience|face)',
                r'potential (?:risk|challenge|issue)',
                r'uncertainty (?:remains|persists|continues)',
                r'monitoring (?:closely|carefully)',
                r'cautiously (?:optimistic|concerned)',
                r'guidance (?:adjusted|revised|updated)',
                r'outlook (?:uncertain|mixed|cautious)'
            ]
        }
        
        # Corporate speak translations
        self.corporate_speak = {
            'restructuring': 'layoffs or cost cutting',
            'strategic alternatives': 'considering sale',
            'right-sizing': 'layoffs',
            'synergies': 'job cuts',
            'challenging environment': 'poor performance',
            'optimizing costs': 'cutting jobs',
            'portfolio rationalization': 'selling assets',
            'exploring options': 'in trouble',
            'enhancing efficiency': 'cutting costs',
            'realignment': 'layoffs',
            'streamlining operations': 'cutting jobs'
        }
    
    def _init_sentiment_dictionaries(self):
        """Initialize advanced sentiment dictionaries"""
        # Financial strength indicators
        self.financial_strength = {
            'positive': [
                'cash flow positive', 'debt reduction', 'strong balance sheet',
                'credit upgrade', 'improving margins', 'cost efficiency',
                'share buyback', 'dividend increase', 'cash reserves',
                'liquidity strong', 'debt paid down'
            ],
            'negative': [
                'cash burn', 'debt increase', 'balance sheet concerns',
                'credit downgrade', 'margin pressure', 'rising costs',
                'share dilution', 'dividend cut', 'cash shortage',
                'liquidity issues', 'debt financing'
            ]
        }
        
        # Growth indicators
        self.growth_indicators = {
            'positive': [
                'market share gain', 'expansion plans', 'new markets',
                'product pipeline', 'innovation', 'competitive advantage',
                'customer acquisition', 'recurring revenue', 'scalable model',
                'growth accelerating', 'demand surge'
            ],
            'negative': [
                'market share loss', 'contraction', 'exiting markets',
                'pipeline issues', 'innovation lag', 'competitive pressure',
                'customer churn', 'one-time revenue', 'limited scalability',
                'growth slowing', 'demand declining'
            ]
        }
        
        # Forward-looking statements
        self.forward_looking = {
            'bullish': [
                'will exceed', 'expect to beat', 'confident in',
                'poised for', 'well positioned', 'significant opportunity',
                'strong trajectory', 'accelerating growth', 'multi-year growth',
                'secular tailwind', 'market leader'
            ],
            'bearish': [
                'will miss', 'expect to fall', 'concerned about',
                'facing challenges', 'difficult environment', 'headwinds',
                'slowing growth', 'market contraction', 'competitive pressure',
                'structural decline', 'market uncertainty'
            ]
        }
    
    def _load_patterns(self) -> Dict:
        """Load historical news-to-price patterns"""
        if os.path.exists(self.pattern_db_file):
            try:
                with open(self.pattern_db_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        return {
            'patterns': {},
            'success_rate': {},
            'last_updated': None
        }
    
    def _load_insider_correlations(self) -> Dict:
        """Load insider trading and news correlation data"""
        if os.path.exists(self.insider_correlation_file):
            try:
                with open(self.insider_correlation_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        return {
            'correlations': {},
            'timing_analysis': {},
            'success_predictions': {}
        }
    
    def analyze_news_sentiment(self, news_item: Dict) -> Dict:
        """
        Analyze news sentiment with between-the-lines interpretation
        
        Args:
            news_item: Dictionary containing news data
            
        Returns:
            Dict with advanced sentiment analysis
        """
        title = news_item.get('title', '')
        content = news_item.get('content', '')
        ticker = news_item.get('ticker', '')
        
        # Combine text for analysis
        full_text = f"{title} {content}".lower()
        
        # Initialize analysis results
        analysis = {
            'ticker': ticker,
            'surface_sentiment': 0.0,
            'implied_sentiment': 0.0,
            'confidence': 0.0,
            'implications': [],
            'red_flags': [],
            'corporate_speak_detected': [],
            'forward_outlook': 'NEUTRAL',
            'financial_health': 'NEUTRAL',
            'growth_trajectory': 'NEUTRAL',
            'pattern_match': None,
            'historical_accuracy': 0.0,
            'insider_correlation': None
        }
        
        # Surface sentiment analysis
        analysis['surface_sentiment'] = self._calculate_surface_sentiment(full_text)
        
        # Implied sentiment (reading between lines)
        analysis['implied_sentiment'] = self._calculate_implied_sentiment(full_text)
        
        # Detect implications
        analysis['implications'] = self._detect_implications(full_text)
        
        # Check for red flags
        analysis['red_flags'] = self._detect_red_flags(full_text)
        
        # Translate corporate speak
        analysis['corporate_speak_detected'] = self._translate_corporate_speak(full_text)
        
        # Analyze forward outlook
        analysis['forward_outlook'] = self._analyze_forward_outlook(full_text)
        
        # Assess financial health
        analysis['financial_health'] = self._assess_financial_health(full_text)
        
        # Evaluate growth trajectory
        analysis['growth_trajectory'] = self._evaluate_growth_trajectory(full_text)
        
        # Check against historical patterns
        if ticker:
            analysis['pattern_match'] = self._match_historical_pattern(ticker, full_text)
            if analysis['pattern_match']:
                analysis['historical_accuracy'] = self.patterns['success_rate'].get(
                    analysis['pattern_match']['pattern'], 0.5
                )
        
        # Correlate with insider data
        if ticker:
            analysis['insider_correlation'] = self._correlate_with_insider_data(
                ticker, news_item.get('published_date')
            )
        
        # Calculate overall confidence
        analysis['confidence'] = self._calculate_confidence(analysis)
        
        # Save pattern for future learning
        if ticker:
            self._save_pattern_for_learning(ticker, analysis, news_item)
        
        return analysis
    
    def _calculate_surface_sentiment(self, text: str) -> float:
        """Calculate basic surface sentiment"""
        positive_words = [
            'good', 'great', 'excellent', 'strong', 'positive', 'growth',
            'profit', 'gain', 'increase', 'success', 'beat', 'exceed'
        ]
        negative_words = [
            'bad', 'poor', 'weak', 'negative', 'decline', 'loss',
            'decrease', 'failure', 'miss', 'below', 'struggle'
        ]
        
        pos_count = sum(1 for word in positive_words if word in text)
        neg_count = sum(1 for word in negative_words if word in text)
        
        total = pos_count + neg_count
        if total == 0:
            return 0.0
        
        return (pos_count - neg_count) / total
    
    def _calculate_implied_sentiment(self, text: str) -> float:
        """Calculate implied sentiment by reading between lines"""
        sentiment_score = 0.0
        
        # Check implication patterns
        for pattern_type, patterns in self.implication_patterns.items():
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    if 'positive' in pattern_type:
                        sentiment_score += 0.3
                    elif 'negative' in pattern_type:
                        sentiment_score -= 0.3
                    elif 'cautious' in pattern_type:
                        sentiment_score -= 0.1
        
        # Check for corporate speak (usually negative implications)
        for corporate_term in self.corporate_speak.keys():
            if corporate_term in text:
                sentiment_score -= 0.2
        
        # Normalize to -1 to 1 range
        return max(-1.0, min(1.0, sentiment_score))
    
    def _detect_implications(self, text: str) -> List[str]:
        """Detect what the news implies beyond surface meaning"""
        implications = []
        
        # Revenue implications
        if re.search(r'beat (?:expectations|guidance|estimates)', text):
            implications.append("Revenue likely exceeded guidance")
        
        if re.search(r'miss (?:expectations|guidance|estimates)', text):
            implications.append("Revenue likely missed guidance")
        
        # Margin implications
        if re.search(r'improving (?:margins|profitability)', text):
            implications.append("Operating margins improving")
        
        if re.search(r'margin (?:pressure|compression)', text):
            implications.append("Operating margins under pressure")
        
        # Future guidance implications
        if re.search(r'raised (?:guidance|outlook|expectations)', text):
            implications.append("Future guidance likely raised")
        
        if re.search(r'lowered (?:guidance|outlook|expectations)', text):
            implications.append("Future guidance likely lowered")
        
        # Strategic implications
        if re.search(r'exploring (?:strategic|alternatives)', text):
            implications.append("Company may be for sale")
        
        if re.search(r'restructuring|right.sizing', text):
            implications.append("Cost cutting and likely layoffs")
        
        return implications
    
    def _detect_red_flags(self, text: str) -> List[str]:
        """Detect warning signs in the news"""
        red_flags = []
        
        # Accounting issues
        if re.search(r'restating|restatement|accounting (?:irregularities|issues)', text):
            red_flags.append("Accounting concerns")
        
        # Regulatory issues
        if re.search(r'(?:investigation|probe|inquiry) by (?:SEC|DOJ|regulators)', text):
            red_flags.append("Regulatory investigation")
        
        # Leadership issues
        if re.search(r'(?:CEO|CFO|executive) (?:resigns|leaves|departs)', text):
            red_flags.append("Executive departure")
        
        # Financial distress
        if re.search(r'(?:bankruptcy|chapter 11|default|delist)', text):
            red_flags.append("Financial distress")
        
        # Lawsuits
        if re.search(r'(?:lawsuit|litigation|sued|class action)', text):
            red_flags.append("Legal action pending")
        
        return red_flags
    
    def _translate_corporate_speak(self, text: str) -> List[Dict]:
        """Translate corporate jargon to plain English"""
        translations = []
        
        for corporate_term, plain_english in self.corporate_speak.items():
            if corporate_term in text:
                translations.append({
                    'term': corporate_term,
                    'translation': plain_english,
                    'implication': 'negative' if 'layoff' in plain_english or 'cut' in plain_english else 'neutral'
                })
        
        return translations
    
    def _analyze_forward_outlook(self, text: str) -> str:
        """Analyze forward-looking statements"""
        bullish_count = 0
        bearish_count = 0
        
        for phrase in self.forward_looking['bullish']:
            if phrase in text:
                bullish_count += 1
        
        for phrase in self.forward_looking['bearish']:
            if phrase in text:
                bearish_count += 1
        
        if bullish_count > bearish_count:
            return 'BULLISH'
        elif bearish_count > bullish_count:
            return 'BEARISH'
        else:
            return 'NEUTRAL'
    
    def _assess_financial_health(self, text: str) -> str:
        """Assess financial health indicators"""
        positive_count = 0
        negative_count = 0
        
        for indicator in self.financial_strength['positive']:
            if indicator in text:
                positive_count += 1
        
        for indicator in self.financial_strength['negative']:
            if indicator in text:
                negative_count += 1
        
        if positive_count > negative_count:
            return 'STRONG'
        elif negative_count > positive_count:
            return 'WEAK'
        else:
            return 'NEUTRAL'
    
    def _evaluate_growth_trajectory(self, text: str) -> str:
        """Evaluate growth trajectory"""
        positive_count = 0
        negative_count = 0
        
        for indicator in self.growth_indicators['positive']:
            if indicator in text:
                positive_count += 1
        
        for indicator in self.growth_indicators['negative']:
            if indicator in text:
                negative_count += 1
        
        if positive_count > negative_count:
            return 'ACCELERATING'
        elif negative_count > positive_count:
            return 'DECELERATING'
        else:
            return 'STABLE'
    
    def _match_historical_pattern(self, ticker: str, text: str) -> Optional[Dict]:
        """Match news against historical patterns"""
        if ticker not in self.patterns['patterns']:
            return None
        
        # Extract key phrases from text
        words = set(re.findall(r'\b\w+\b', text.lower()))
        
        # Find best matching pattern
        best_match = None
        best_score = 0.0
        
        for pattern_name, pattern_data in self.patterns['patterns'][ticker].items():
            pattern_words = set(pattern_data.get('keywords', []))
            
            # Calculate similarity
            intersection = words.intersection(pattern_words)
            union = words.union(pattern_words)
            
            if len(union) > 0:
                similarity = len(intersection) / len(union)
                if similarity > best_score:
                    best_score = similarity
                    best_match = {
                        'pattern': pattern_name,
                        'similarity': similarity,
                        'historical_moves': pattern_data.get('price_moves', []),
                        'avg_change': pattern_data.get('avg_price_change', 0.0)
                    }
        
        return best_match if best_score > 0.3 else None
    
    def _correlate_with_insider_data(self, ticker: str, news_date: str) -> Optional[Dict]:
        """Correlate news with insider trading data"""
        if ticker not in self.insider_correlations['correlations']:
            return None
        
        # Get insider activity around news dates
        correlation_data = self.insider_correlations['correlations'][ticker]
        
        # Analyze timing patterns
        timing_analysis = {
            'insider_activity_before': 0,
            'insider_activity_after': 0,
            'pattern_confidence': 0.0,
            'implication': 'NEUTRAL'
        }
        
        # Check if insiders typically buy/sell before this type of news
        # This would integrate with actual insider data
        
        return timing_analysis
    
    def _calculate_confidence(self, analysis: Dict) -> float:
        """Calculate confidence in the sentiment analysis"""
        confidence_factors = []
        
        # Confidence from pattern matching
        if analysis['pattern_match']:
            confidence_factors.append(analysis['historical_accuracy'])
        
        # Confidence from multiple signals aligning
        signals = [
            analysis['surface_sentiment'],
            analysis['implied_sentiment']
        ]
        avg_signal = sum(signals) / len(signals)
        confidence_factors.append(abs(avg_signal))
        
        # Confidence from lack of red flags
        if not analysis['red_flags']:
            confidence_factors.append(0.2)
        
        # Confidence from clear implications
        if analysis['implications']:
            confidence_factors.append(0.1)
        
        return min(1.0, sum(confidence_factors))
    
    def _save_pattern_for_learning(self, ticker: str, analysis: Dict, news_item: Dict):
        """Save pattern for future learning"""
        # This would save the pattern and later correlate with actual price movements
        # to build the historical pattern database
        pass
    
    def predict_price_movement(self, ticker: str, analysis: Dict) -> Dict:
        """
        Predict price movement based on sentiment analysis and historical patterns
        
        Args:
            ticker: Stock symbol
            analysis: Sentiment analysis results
            
        Returns:
            Prediction with confidence
        """
        prediction = {
            'ticker': ticker,
            'direction': 'NEUTRAL',
            'confidence': 0.0,
            'expected_move': 0.0,
            'timeframe': '5 days',
            'reasoning': [],
            'risk_factors': []
        }
        
        # Base prediction on implied sentiment
        if analysis['implied_sentiment'] > 0.3:
            prediction['direction'] = 'BULLISH'
            prediction['expected_move'] = analysis['implied_sentiment'] * 0.1  # 10% max
        elif analysis['implied_sentiment'] < -0.3:
            prediction['direction'] = 'BEARISH'
            prediction['expected_move'] = abs(analysis['implied_sentiment']) * 0.1
        
        # Adjust based on historical patterns
        if analysis['pattern_match']:
            pattern = analysis['pattern_match']
            if pattern['avg_change'] > 0:
                prediction['direction'] = 'BULLISH'
            elif pattern['avg_change'] < 0:
                prediction['direction'] = 'BEARISH'
            prediction['expected_move'] = abs(pattern['avg_change'])
            prediction['reasoning'].append(
                f"Historical pattern: {pattern['pattern']} "
                f"(avg move: {pattern['avg_change']:.2%})"
            )
        
        # Adjust for red flags
        if analysis['red_flags']:
            prediction['confidence'] *= 0.7
            prediction['risk_factors'].extend(analysis['red_flags'])
        
        # Combine confidence scores
        prediction['confidence'] = min(1.0, (
            analysis['confidence'] * 0.6 +
            (1.0 if analysis['pattern_match'] else 0.0) * 0.4
        ))
        
        # Add reasoning
        if analysis['implications']:
            prediction['reasoning'].extend(analysis['implications'])
        
        if analysis['forward_outlook'] != 'NEUTRAL':
            prediction['reasoning'].append(
                f"Forward outlook: {analysis['forward_outlook']}"
            )
        
        return prediction
