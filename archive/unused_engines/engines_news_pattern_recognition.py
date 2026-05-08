"""
News Pattern Recognition System

Tracks historical patterns of how stocks move after specific types of news:
- Identifies recurring patterns in news-to-price movements
- Measures accuracy of predictions over time
- Learns from historical data to improve predictions
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

class NewsPatternRecognizer:
    """Recognizes and learns from news-to-price movement patterns"""
    
    def __init__(self, config: dict = None):
        self.config = config or {}
        
        # Pattern database files
        self.pattern_file = os.path.join(
            os.path.dirname(__file__), '..', 'data', 'news_price_patterns.json'
        )
        self.performance_file = os.path.join(
            os.path.dirname(__file__), '..', 'data', 'pattern_performance.json'
        )
        
        # Load existing patterns
        self.patterns = self._load_patterns()
        self.performance = self._load_performance()
        
        # Pattern categories
        self.pattern_categories = {
            'earnings': [
                'beat earnings', 'missed earnings', 'earnings beat',
                'eps beat', 'revenue beat', 'earnings miss',
                'eps miss', 'revenue miss', 'earnings guidance'
            ],
            'partnerships': [
                'partnership', 'collaboration', 'joint venture',
                'strategic alliance', 'teams up', 'agreement',
                'contract', 'deal', 'acquisition', 'merger'
            ],
            'regulatory': [
                'fda approval', 'regulatory approval', 'sec filing',
                'compliance', 'violation', 'fine', 'penalty',
                'lawsuit', 'litigation', 'investigation'
            ],
            'financial': [
                'debt financing', 'offering', 'share buyback',
                'dividend', 'credit rating', 'bankruptcy',
                'restructuring', 'cost cutting', 'layoffs'
            ],
            'product': [
                'product launch', 'fda approval', 'patent',
                'innovation', 'breakthrough', 'recall',
                'discontinued', 'new product', 'upgrade'
            ],
            'management': [
                'ceo', 'cfo', 'executive', 'board', 'leadership',
                'resignation', 'appointment', 'fired', 'hired',
                'management change'
            ]
        }
        
        # Price movement thresholds
        self.movement_thresholds = {
            'small': 0.02,    # 2%
            'medium': 0.05,   # 5%
            'large': 0.10,    # 10%
            'very_large': 0.20  # 20%
        }
    
    def _load_patterns(self) -> Dict:
        """Load existing pattern data"""
        if os.path.exists(self.pattern_file):
            try:
                with open(self.pattern_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        return {
            'patterns': {},
            'keywords': {},
            'last_updated': None
        }
    
    def _load_performance(self) -> Dict:
        """Load pattern performance data"""
        if os.path.exists(self.performance_file):
            try:
                with open(self.performance_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        return {
            'accuracy': {},
            'predictions': [],
            'success_rate': 0.0
        }
    
    def analyze_news_pattern(self, ticker: str, news_item: Dict) -> Dict:
        """
        Analyze news item and identify pattern type
        
        Args:
            ticker: Stock symbol
            news_item: News data
            
        Returns:
            Pattern analysis with historical data
        """
        title = news_item.get('title', '').lower()
        content = news_item.get('content', '').lower()
        full_text = f"{title} {content}"
        
        # Initialize analysis
        analysis = {
            'ticker': ticker,
            'pattern_type': None,
            'pattern_keywords': [],
            'historical_occurrences': 0,
            'avg_price_change': 0.0,
            'success_rate': 0.0,
            'confidence': 0.0,
            'price_movements': [],
            'timeframes': {
                '1_day': {'avg_change': 0.0, 'success_rate': 0.0},
                '3_days': {'avg_change': 0.0, 'success_rate': 0.0},
                '5_days': {'avg_change': 0.0, 'success_rate': 0.0},
                '10_days': {'avg_change': 0.0, 'success_rate': 0.0}
            }
        }
        
        # Identify pattern type
        pattern_type, keywords = self._identify_pattern_type(full_text)
        analysis['pattern_type'] = pattern_type
        analysis['pattern_keywords'] = keywords
        
        # Get historical data for this pattern
        if pattern_type and ticker:
            historical_data = self._get_historical_pattern_data(
                ticker, pattern_type, keywords
            )
            analysis.update(historical_data)
        
        return analysis
    
    def _identify_pattern_type(self, text: str) -> Tuple[Optional[str], List[str]]:
        """Identify the type of news pattern"""
        found_keywords = []
        pattern_scores = {}
        
        # Score each pattern category
        for pattern_type, keywords in self.pattern_categories.items():
            score = 0
            matched_keywords = []
            
            for keyword in keywords:
                if keyword in text:
                    score += 1
                    matched_keywords.append(keyword)
            
            if score > 0:
                pattern_scores[pattern_type] = {
                    'score': score,
                    'keywords': matched_keywords
                }
        
        # Return best match
        if pattern_scores:
            best_pattern = max(pattern_scores.items(), key=lambda x: x[1]['score'])
            return best_pattern[0], best_pattern[1]['keywords']
        
        return None, []
    
    def _get_historical_pattern_data(self, ticker: str, pattern_type: str, keywords: List[str]) -> Dict:
        """Get historical data for a specific pattern"""
        # Check if we have data for this ticker and pattern
        if ticker not in self.patterns['patterns']:
            return self._empty_historical_data()
        
        ticker_patterns = self.patterns['patterns'][ticker]
        
        # Find matching patterns
        matching_patterns = []
        for pattern_name, pattern_data in ticker_patterns.items():
            if pattern_type.lower() in pattern_name.lower():
                matching_patterns.append(pattern_data)
        
        if not matching_patterns:
            return self._empty_historical_data()
        
        # Aggregate historical data
        all_movements = []
        timeframe_data = {
            '1_day': [],
            '3_days': [],
            '5_days': [],
            '10_days': []
        }
        
        for pattern in matching_patterns:
            movements = pattern.get('price_movements', [])
            all_movements.extend(movements)
            
            # Aggregate by timeframe
            for movement in movements:
                for tf in timeframe_data.keys():
                    if tf in movement:
                        timeframe_data[tf].append(movement[tf])
        
        # Calculate statistics
        result = {
            'historical_occurrences': len(matching_patterns),
            'avg_price_change': np.mean(all_movements) if all_movements else 0.0,
            'price_movements': all_movements
        }
        
        # Calculate timeframe statistics
        for tf, movements in timeframe_data.items():
            if movements:
                result['timeframes'][tf] = {
                    'avg_change': np.mean(movements),
                    'success_rate': len([m for m in movements if m > 0]) / len(movements)
                }
        
        # Get success rate from performance data
        pattern_key = f"{ticker}_{pattern_type}"
        result['success_rate'] = self.performance['accuracy'].get(pattern_key, 0.5)
        
        # Calculate confidence based on data points
        result['confidence'] = min(1.0, len(all_movements) / 20.0)
        
        return result
    
    def _empty_historical_data(self) -> Dict:
        """Return empty historical data structure"""
        return {
            'historical_occurrences': 0,
            'avg_price_change': 0.0,
            'success_rate': 0.5,
            'confidence': 0.0,
            'price_movements': [],
            'timeframes': {
                '1_day': {'avg_change': 0.0, 'success_rate': 0.5},
                '3_days': {'avg_change': 0.0, 'success_rate': 0.5},
                '5_days': {'avg_change': 0.0, 'success_rate': 0.5},
                '10_days': {'avg_change': 0.0, 'success_rate': 0.5}
            }
        }
    
    def record_pattern_outcome(self, ticker: str, pattern_type: str, 
                             news_date: datetime, actual_movements: Dict):
        """
        Record the actual price movement after a pattern occurred
        Used for learning and improving predictions
        
        Args:
            ticker: Stock symbol
            pattern_type: Type of news pattern
            news_date: Date news was published
            actual_movements: Dictionary of actual price movements by timeframe
        """
        # Initialize ticker patterns if needed
        if ticker not in self.patterns['patterns']:
            self.patterns['patterns'][ticker] = {}
        
        # Create pattern key
        pattern_key = f"{pattern_type}_{news_date.strftime('%Y%m')}"
        
        # Initialize pattern if needed
        if pattern_key not in self.patterns['patterns'][ticker]:
            self.patterns['patterns'][ticker][pattern_key] = {
                'pattern_type': pattern_type,
                'occurrences': 0,
                'price_movements': [],
                'keywords': []
            }
        
        # Record this occurrence
        pattern = self.patterns['patterns'][ticker][pattern_key]
        pattern['occurrences'] += 1
        
        # Store price movements
        for timeframe, movement in actual_movements.items():
            if timeframe not in pattern:
                pattern[timeframe] = []
            pattern[timeframe].append(movement)
        
        # Also store in flat list for easy access
        pattern['price_movements'].append(actual_movements.get('5_days', 0.0))
        
        # Update performance tracking
        self._update_performance(ticker, pattern_type, actual_movements)
        
        # Save data
        self._save_patterns()
        self._save_performance()
    
    def _update_performance(self, ticker: str, pattern_type: str, movements: Dict):
        """Update performance tracking for pattern predictions"""
        pattern_key = f"{ticker}_{pattern_type}"
        
        if pattern_key not in self.performance['accuracy']:
            self.performance['accuracy'][pattern_key] = {
                'predictions': 0,
                'correct': 0,
                'total_change': 0.0,
                'avg_change': 0.0
            }
        
        perf = self.performance['accuracy'][pattern_key]
        perf['predictions'] += 1
        
        # Check if prediction was correct (positive movement for bullish patterns)
        movement_5d = movements.get('5_days', 0.0)
        if movement_5d > 0:
            perf['correct'] += 1
        
        perf['total_change'] += movement_5d
        perf['avg_change'] = perf['total_change'] / perf['predictions']
        
        # Update overall success rate
        total_predictions = sum(p['predictions'] for p in self.performance['accuracy'].values())
        total_correct = sum(p['correct'] for p in self.performance['accuracy'].values())
        self.performance['success_rate'] = total_correct / total_predictions if total_predictions > 0 else 0.0
    
    def predict_movement(self, ticker: str, pattern_type: str, 
                        timeframe: str = '5_days') -> Dict:
        """
        Predict price movement based on historical patterns
        
        Args:
            ticker: Stock symbol
            pattern_type: Type of news pattern
            timeframe: Prediction timeframe
            
        Returns:
            Prediction with confidence
        """
        prediction = {
            'ticker': ticker,
            'pattern_type': pattern_type,
            'timeframe': timeframe,
            'direction': 'NEUTRAL',
            'expected_change': 0.0,
            'confidence': 0.0,
            'historical_accuracy': 0.0,
            'sample_size': 0,
            'reasoning': []
        }
        
        # Get historical data
        pattern_key = f"{ticker}_{pattern_type}"
        
        if ticker in self.patterns['patterns']:
            # Find all patterns of this type
            matching_patterns = []
            for pattern_name, pattern_data in self.patterns['patterns'][ticker].items():
                if pattern_type.lower() in pattern_name.lower():
                    matching_patterns.append(pattern_data)
            
            if matching_patterns:
                # Aggregate predictions
                all_movements = []
                for pattern in matching_patterns:
                    if timeframe in pattern:
                        all_movements.extend(pattern[timeframe])
                
                if all_movements:
                    prediction['expected_change'] = np.mean(all_movements)
                    prediction['sample_size'] = len(all_movements)
                    
                    # Determine direction
                    if prediction['expected_change'] > 0.02:  # 2% threshold
                        prediction['direction'] = 'BULLISH'
                    elif prediction['expected_change'] < -0.02:
                        prediction['direction'] = 'BEARISH'
                    
                    # Calculate confidence
                    prediction['confidence'] = min(1.0, len(all_movements) / 10.0)
                    
                    # Get historical accuracy
                    if pattern_key in self.performance['accuracy']:
                        perf = self.performance['accuracy'][pattern_key]
                        prediction['historical_accuracy'] = perf['correct'] / perf['predictions']
                        prediction['reasoning'].append(
                            f"Historical accuracy: {prediction['historical_accuracy']:.1%}"
                        )
                    
                    prediction['reasoning'].append(
                        f"Based on {len(all_movements)} historical occurrences"
                    )
        
        return prediction
    
    def get_top_patterns(self, ticker: str, min_occurrences: int = 5) -> List[Dict]:
        """
        Get top performing patterns for a ticker
        
        Args:
            ticker: Stock symbol
            min_occurrences: Minimum number of occurrences to consider
            
        Returns:
            List of top patterns with their stats
        """
        if ticker not in self.patterns['patterns']:
            return []
        
        top_patterns = []
        
        for pattern_name, pattern_data in self.patterns['patterns'][ticker].items():
            if pattern_data['occurrences'] >= min_occurrences:
                movements = pattern_data.get('price_movements', [])
                if movements:
                    avg_change = np.mean(movements)
                    pattern_key = f"{ticker}_{pattern_data.get('pattern_type', 'unknown')}"
                    
                    top_patterns.append({
                        'pattern_type': pattern_data.get('pattern_type', 'unknown'),
                        'occurrences': pattern_data['occurrences'],
                        'avg_change': avg_change,
                        'success_rate': len([m for m in movements if m > 0]) / len(movements),
                        'last_seen': pattern_name
                    })
        
        # Sort by average change
        top_patterns.sort(key=lambda x: x['avg_change'], reverse=True)
        
        return top_patterns[:10]
    
    def _save_patterns(self):
        """Save pattern data to file"""
        try:
            self.patterns['last_updated'] = datetime.now().isoformat()
            with open(self.pattern_file, 'w') as f:
                json.dump(self.patterns, f, indent=2)
        except Exception as e:
            print(f"Error saving patterns: {e}")
    
    def _save_performance(self):
        """Save performance data to file"""
        try:
            self.performance['last_updated'] = datetime.now().isoformat()
            with open(self.performance_file, 'w') as f:
                json.dump(self.performance, f, indent=2)
        except Exception as e:
            print(f"Error saving performance: {e}")
