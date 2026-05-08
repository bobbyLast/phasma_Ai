"""
Trader Reputation System for Reddit
Tracks user predictions and their outcomes to identify consistently bad traders
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from collections import defaultdict

class TraderReputation:
    """
    Tracks Reddit users' trading predictions and their outcomes
    Learns from bad traders to avoid similar patterns
    """
    
    def __init__(self, data_dir: str = None):
        if data_dir is None:
            data_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'data')
        
        self.data_file = os.path.join(data_dir, 'trader_reputation.json')
        self.reputation_data = self._load_data()
        
        # Reputation thresholds
        self.BAD_TRADER_THRESHOLD = -0.3  # 30% below average is considered bad
        self.MIN_PREDICTIONS = 5  # Minimum predictions before judging
        
    def _load_data(self) -> Dict:
        """Load trader reputation data from file"""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading trader reputation: {e}")
        
        return {
            'users': {},  # username -> {predictions: [], accuracy: float, reputation: str}
            'symbol_patterns': {},  # symbol -> {bad_patterns: [], avoid_count: int}
            'last_updated': None
        }
    
    def _save_data(self):
        """Save trader reputation data to file"""
        try:
            self.reputation_data['last_updated'] = datetime.now().isoformat()
            with open(self.data_file, 'w') as f:
                json.dump(self.reputation_data, f, indent=2)
        except Exception as e:
            print(f"Error saving trader reputation: {e}")
    
    def record_prediction(self, username: str, symbol: str, prediction: str, 
                         sentiment: str, timestamp: datetime = None):
        """
        Record a user's prediction for a symbol
        
        Args:
            username: Reddit username
            symbol: Stock/crypto symbol
            prediction: Type of prediction (e.g., 'BUY', 'SELL', 'MOONSHOT')
            sentiment: Bullish/Bearish/Neutral
            timestamp: When the prediction was made
        """
        if timestamp is None:
            timestamp = datetime.now()
            
        if username not in self.reputation_data['users']:
            self.reputation_data['users'][username] = {
                'predictions': [],
                'accuracy': 0.0,
                'reputation': 'UNKNOWN',
                'total_predictions': 0,
                'correct_predictions': 0
            }
        
        # Record the prediction
        prediction_data = {
            'symbol': symbol,
            'prediction': prediction,
            'sentiment': sentiment,
            'timestamp': timestamp.isoformat(),
            'outcome': None,  # Will be updated later
            'days_to_outcome': None
        }
        
        self.reputation_data['users'][username]['predictions'].append(prediction_data)
        self.reputation_data['users'][username]['total_predictions'] += 1
        
        self._save_data()
    
    def record_outcome(self, symbol: str, outcome: str, price_change: float):
        """
        Record the outcome for a symbol and update user reputations
        
        Args:
            symbol: Stock/crypto symbol
            outcome: 'WIN' or 'LOSS'
            price_change: Percentage price change
        """
        # Update all users who predicted this symbol
        for username, user_data in self.reputation_data['users'].items():
            for pred in user_data['predictions']:
                if pred['symbol'] == symbol and pred['outcome'] is None:
                    pred['outcome'] = outcome
                    pred['price_change'] = price_change
                    
                    # Check if prediction was correct
                    was_correct = self._was_prediction_correct(pred, outcome, price_change)
                    if was_correct:
                        user_data['correct_predictions'] += 1
                    
                    # Update accuracy
                    if user_data['total_predictions'] >= self.MIN_PREDICTIONS:
                        user_data['accuracy'] = user_data['correct_predictions'] / user_data['total_predictions']
                        
                        # Update reputation
                        if user_data['accuracy'] < 0.4:  # Less than 40% accuracy
                            user_data['reputation'] = 'BAD_TRADER'
                        elif user_data['accuracy'] > 0.6:  # More than 60% accuracy
                            user_data['reputation'] = 'GOOD_TRADER'
                        else:
                            user_data['reputation'] = 'AVERAGE'
                    
                    # Track bad patterns
                    if not was_correct and user_data['reputation'] == 'BAD_TRADER':
                        self._track_bad_pattern(symbol, pred)
        
        self._save_data()
    
    def _was_prediction_correct(self, prediction: Dict, outcome: str, price_change: float) -> bool:
        """Determine if a prediction was correct"""
        pred_type = prediction['prediction'].upper()
        sentiment = prediction['sentiment'].upper()
        
        # Simple correctness check
        if sentiment == 'BULLISH':
            return price_change > 0
        elif sentiment == 'BEARISH':
            return price_change < 0
        else:
            return outcome == 'WIN'
    
    def _track_bad_pattern(self, symbol: str, prediction: Dict):
        """Track patterns from bad traders to avoid"""
        if symbol not in self.reputation_data['symbol_patterns']:
            self.reputation_data['symbol_patterns'][symbol] = {
                'bad_patterns': [],
                'avoid_count': 0
            }
        
        pattern = {
            'prediction_type': prediction['prediction'],
            'sentiment': prediction['sentiment'],
            'timestamp': prediction['timestamp']
        }
        
        self.reputation_data['symbol_patterns'][symbol]['bad_patterns'].append(pattern)
        self.reputation_data['symbol_patterns'][symbol]['avoid_count'] += 1
    
    def get_user_reputation(self, username: str) -> str:
        """Get the reputation of a user"""
        if username in self.reputation_data['users']:
            return self.reputation_data['users'][username]['reputation']
        return 'UNKNOWN'
    
    def should_avoid_symbol(self, symbol: str) -> bool:
        """Check if a symbol has too many bad trader predictions"""
        if symbol in self.reputation_data['symbol_patterns']:
            avoid_count = self.reputation_data['symbol_patterns'][symbol]['avoid_count']
            # Avoid if more than 3 bad predictions
            return avoid_count > 3
        return False
    
    def get_bad_traders(self) -> List[str]:
        """Get list of users with bad trader reputation"""
        bad_traders = []
        for username, user_data in self.reputation_data['users'].items():
            if user_data['reputation'] == 'BAD_TRADER':
                bad_traders.append(username)
        return bad_traders
    
    def get_reputation_summary(self) -> Dict:
        """Get summary of trader reputations"""
        summary = {
            'total_users': len(self.reputation_data['users']),
            'bad_traders': 0,
            'good_traders': 0,
            'average_traders': 0,
            'symbols_to_avoid': 0
        }
        
        for user_data in self.reputation_data['users'].values():
            if user_data['reputation'] == 'BAD_TRADER':
                summary['bad_traders'] += 1
            elif user_data['reputation'] == 'GOOD_TRADER':
                summary['good_traders'] += 1
            else:
                summary['average_traders'] += 1
        
        for symbol_data in self.reputation_data['symbol_patterns'].values():
            if symbol_data['avoid_count'] > 3:
                summary['symbols_to_avoid'] += 1
        
        return summary
