"""
IV Crush Predictor - Post-Earnings Volatility Collapse Detection
Implements AI Feedback Task 4: Predict and avoid IV crush scenarios
"""

import yfinance as yf
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, List
import statistics

class IVCrushPredictor:
    """Predict implied volatility crush risk (especially post-earnings)"""
    
    def __init__(self):
        """Initialize IV crush predictor"""
        self.logger = logging.getLogger(__name__)
        self.earnings_cache = {}  # Cache earnings dates
        
    def predict_iv_crush_risk(self, symbol: str, option_data: Dict) -> Dict:
        """
        Predict IV crush risk for a given symbol and option
        
        Args:
            symbol: Stock ticker
            option_data: Dictionary with option details including IV
            
        Returns:
            Dictionary with crush risk assessment
        """
        try:
            # Get earnings date
            earnings_info = self.get_earnings_date(symbol)
            
            if not earnings_info or 'days_to_earnings' not in earnings_info:
                return {
                    'crush_risk': 'UNKNOWN',
                    'recommendation': 'PROCEED_WITH_CAUTION',
                    'reason': 'Unable to determine earnings date'
                }
            
            days_to_earnings = earnings_info['days_to_earnings']
            
            # Get current IV
            current_iv = option_data.get('implied_volatility', 0)
            if current_iv == 0:
                current_iv = option_data.get('iv', 0)
            
            # Get historical IV
            historical_iv = self.get_historical_iv(symbol)
            
            # Calculate IV premium
            if historical_iv > 0:
                iv_premium_pct = ((current_iv / historical_iv) - 1) * 100
            else:
                iv_premium_pct = 0
            
            # Determine risk level
            risk_assessment = self._assess_crush_risk(
                days_to_earnings=days_to_earnings,
                iv_premium_pct=iv_premium_pct,
                current_iv=current_iv,
                historical_iv=historical_iv
            )
            
            return risk_assessment
            
        except Exception as e:
            self.logger.error(f"Error predicting IV crush for {symbol}: {e}")
            return {
                'crush_risk': 'ERROR',
                'recommendation': 'AVOID',
                'reason': f'Error in prediction: {str(e)}'
            }
    
    def get_earnings_date(self, symbol: str) -> Optional[Dict]:
        """Get next earnings date for symbol"""
        # Check cache first
        if symbol in self.earnings_cache:
            cached = self.earnings_cache[symbol]
            if datetime.now() - cached['timestamp'] < timedelta(hours=24):
                return cached['data']
        
        try:
            ticker = yf.Ticker(symbol)
            calendar = ticker.calendar
            
            if calendar is not None and hasattr(calendar, 'T'):
                # Handle DataFrame format
                if 'Earnings Date' in calendar.T.columns:
                    earnings_date = calendar.T['Earnings Date'].iloc[0]
                    
                    if isinstance(earnings_date, str):
                        earnings_date = datetime.strptime(earnings_date, '%Y-%m-%d')
                    
                    days_to_earnings = (earnings_date - datetime.now()).days
                    
                    result = {
                        'earnings_date': earnings_date,
                        'days_to_earnings': days_to_earnings,
                        'is_within_week': days_to_earnings <= 7 and days_to_earnings >= 0
                    }
                    
                    # Cache result
                    self.earnings_cache[symbol] = {
                        'data': result,
                        'timestamp': datetime.now()
                    }
                    
                    return result
            
            return None
            
        except Exception as e:
            self.logger.warning(f"Could not fetch earnings date for {symbol}: {e}")
            return None
    
    def get_historical_iv(self, symbol: str, lookback_days: int = 90) -> float:
        """
        Calculate historical average IV
        
        Args:
            symbol: Stock ticker
            lookback_days: Days to look back for average
            
        Returns:
            Average historical IV
        """
        try:
            ticker = yf.Ticker(symbol)
            
            # Try to get options chain for historical IV
            # This is simplified - in production, use historical options data
            options_dates = ticker.options
            
            if not options_dates:
                return 0.0
            
            # Use nearest-dated options as proxy
            nearest_date = options_dates[0]
            chain = ticker.option_chain(nearest_date)
            
            # Calculate average IV from ATM options
            calls = chain.calls
            atm_calls = calls[abs(calls['strike'] - calls['lastPrice'].iloc[0]) < 5]
            
            if not atm_calls.empty and 'impliedVolatility' in atm_calls.columns:
                avg_iv = atm_calls['impliedVolatility'].mean()
                # Discount by 20% as historical tends to be lower
                return avg_iv * 0.8
            
            # Fallback to historical volatility
            hist = ticker.history(period='3mo')
            if not hist.empty:
                returns = hist['Close'].pct_change().dropna()
                historical_vol = returns.std() * (252 ** 0.5)  # Annualized
                return historical_vol
            
            return 0.30  # Default 30% if unable to calculate
            
        except Exception as e:
            self.logger.warning(f"Could not calculate historical IV for {symbol}: {e}")
            return 0.30  # Default
    
    def _assess_crush_risk(
        self, 
        days_to_earnings: int,
        iv_premium_pct: float,
        current_iv: float,
        historical_iv: float
    ) -> Dict:
        """Assess IV crush risk based on parameters"""
        
        # HIGH RISK: Within 7 days of earnings + elevated IV
        if days_to_earnings <= 7 and days_to_earnings >= 0:
            if iv_premium_pct > 50:  # IV is 50%+ above historical
                return {
                    'crush_risk': 'VERY_HIGH',
                    'recommendation': 'AVOID',
                    'days_to_earnings': days_to_earnings,
                    'iv_premium': f'{iv_premium_pct:.1f}%',
                    'current_iv': f'{current_iv:.1%}',
                    'historical_iv': f'{historical_iv:.1%}',
                    'reason': 'Earnings imminent with highly elevated IV - high crush risk',
                    'suggested_action': 'Wait until after earnings or reduce position size by 75%'
                }
            elif iv_premium_pct > 25:  # IV is 25-50% above historical
                return {
                    'crush_risk': 'HIGH',
                    'recommendation': 'REDUCE_SIZE',
                    'days_to_earnings': days_to_earnings,
                    'iv_premium': f'{iv_premium_pct:.1f}%',
                    'current_iv': f'{current_iv:.1%}',
                    'historical_iv': f'{historical_iv:.1%}',
                    'reason': 'Earnings approaching with elevated IV',
                    'suggested_action': 'Reduce position size by 50% or exit before earnings'
                }
        
        # MEDIUM RISK: Within 14 days + moderately elevated IV
        if days_to_earnings <= 14 and days_to_earnings >= 0:
            if iv_premium_pct > 30:
                return {
                    'crush_risk': 'MEDIUM',
                    'recommendation': 'PROCEED_WITH_CAUTION',
                    'days_to_earnings': days_to_earnings,
                    'iv_premium': f'{iv_premium_pct:.1f}%',
                    'current_iv': f'{current_iv:.1%}',
                    'historical_iv': f'{historical_iv:.1%}',
                    'reason': 'Earnings within 2 weeks with above-average IV',
                    'suggested_action': 'Monitor closely, consider reducing size by 25%'
                }
        
        # LOW RISK: Normal conditions
        return {
            'crush_risk': 'LOW',
            'recommendation': 'PROCEED',
            'days_to_earnings': days_to_earnings if days_to_earnings >= 0 else 'N/A',
            'iv_premium': f'{iv_premium_pct:.1f}%',
            'current_iv': f'{current_iv:.1%}',
            'historical_iv': f'{historical_iv:.1%}',
            'reason': 'No immediate crush risk detected',
            'suggested_action': 'Normal position sizing'
        }
    
    def get_safe_entry_window(self, symbol: str) -> Dict:
        """
        Determine the safest window to enter a position
        
        Args:
            symbol: Stock ticker
            
        Returns:
            Dictionary with entry window recommendations
        """
        earnings_info = self.get_earnings_date(symbol)
        
        if not earnings_info:
            return {
                'window': 'UNKNOWN',
                'recommendation': 'Unable to determine - verify earnings date manually'
            }
        
        days_to_earnings = earnings_info['days_to_earnings']
        
        if days_to_earnings < 0:
            # After earnings
            days_since_earnings = abs(days_to_earnings)
            if days_since_earnings <= 3:
                return {
                    'window': 'POST_EARNINGS_OPPORTUNITY',
                    'recommendation': 'Good entry - IV likely crushed, premiums cheaper',
                    'days_since_earnings': days_since_earnings
                }
        
        if days_to_earnings > 21:
            # More than 3 weeks out
            return {
                'window': 'SAFE_ENTRY',
                'recommendation': 'Safe to enter - sufficient time before earnings',
                'days_to_earnings': days_to_earnings
            }
        elif days_to_earnings > 14:
            # 2-3 weeks out
            return {
                'window': 'MODERATE_ENTRY',
                'recommendation': 'Acceptable entry - monitor for IV expansion',
                'days_to_earnings': days_to_earnings
            }
        else:
            # Less than 2 weeks
            return {
                'window': 'RISKY_ENTRY',
                'recommendation': 'Risky - consider waiting until after earnings',
                'days_to_earnings': days_to_earnings
            }
