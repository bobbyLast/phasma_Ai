#!/usr/bin/env python3
"""
Market Hours Detector
Helps AI determine if markets are open and choose appropriate strategies
"""

import pytz
from datetime import datetime, time, timedelta

# Simple holiday check - can be expanded later
def is_us_holiday(date):
    """Simple check for major US holidays"""
    # List of major US holidays (can be expanded)
    major_holidays = [
        '01-01',  # New Year's Day
        '07-04',  # Independence Day
        '12-25',  # Christmas Day
    ]
    return date.strftime('%m-%d') in major_holidays

class MarketHoursDetector:
    """Detects market hours and suggests appropriate strategies"""
    
    def __init__(self):
        self.nyse = pytz.timezone('America/New_York')
        
    def is_market_open(self, dt: datetime = None) -> bool:
        """Check if US market is currently open"""
        if dt is None:
            dt = datetime.now(self.nyse)
        
        # Check if it's a weekday
        if dt.weekday() >= 5:  # Saturday or Sunday
            return False
        
        # Check if it's a holiday
        if is_us_holiday(dt.date()):
            return False
        
        # Check if it's within market hours (9:30 AM - 4:00 PM ET)
        market_open = time(9, 30)
        market_close = time(16, 0)
        current_time = dt.time()
        
        return market_open <= current_time <= market_close
    
    def is_pre_market(self, dt: datetime = None) -> bool:
        """Check if it's pre-market (4:00 AM - 9:30 AM ET)"""
        if dt is None:
            dt = datetime.now(self.nyse)
        
        if dt.weekday() >= 5 or is_us_holiday(dt.date()):
            return False
        
        pre_market_start = time(4, 0)
        pre_market_end = time(9, 30)
        current_time = dt.time()
        
        return pre_market_start <= current_time < pre_market_end
    
    def is_after_hours(self, dt: datetime = None) -> bool:
        """Check if it's after hours (4:00 PM - 8:00 PM ET)"""
        if dt is None:
            dt = datetime.now(self.nyse)
        
        if dt.weekday() >= 5 or is_us_holiday(dt.date()):
            return False
        
        after_hours_start = time(16, 0)
        after_hours_end = time(20, 0)
        current_time = dt.time()
        
        return after_hours_start <= current_time <= after_hours_end
    
    def get_market_status(self, dt: datetime = None) -> dict:
        """Get comprehensive market status"""
        if dt is None:
            dt = datetime.now(self.nyse)
        
        status = {
            'datetime': dt.isoformat(),
            'is_weekday': dt.weekday() < 5,
            'is_holiday': is_us_holiday(dt.date()),
            'is_market_open': self.is_market_open(dt),
            'is_pre_market': self.is_pre_market(dt),
            'is_after_hours': self.is_after_hours(dt),
            'time_until_open': None,
            'time_until_close': None,
            'recommended_strategy': 'INVESTING'
        }
        
        # Calculate time until market opens/closes
        if not status['is_market_open']:
            # Time until next market open
            if dt.time() > time(16, 0) or dt.weekday() >= 5:
                # After market hours or weekend
                days_ahead = 0
                while days_ahead < 7:
                    check_date = (dt + timedelta(days=days_ahead)).date()
                    if not is_us_holiday(check_date) and (dt + timedelta(days=days_ahead)).weekday() < 5:
                        break
                    days_ahead += 1
                
                next_open = dt.replace(hour=9, minute=30, second=0, microsecond=0) + timedelta(days=days_ahead)
            else:
                # Before market open on weekday
                next_open = dt.replace(hour=9, minute=30, second=0, microsecond=0)
            
            status['time_until_open'] = next_open - dt
        
        if status['is_market_open']:
            # Time until market close
            market_close = dt.replace(hour=16, minute=0, second=0, microsecond=0)
            status['time_until_close'] = market_close - dt
        
        # Recommend strategy based on market status
        if status['is_market_open']:
            status['recommended_strategy'] = 'SWING_TRADING'
            status['reason'] = 'Market is open - suitable for swing trades'
        elif status['is_pre_market']:
            status['recommended_strategy'] = 'PRE_MARKET_SETUP'
            status['reason'] = 'Pre-market - prepare for opening bell trades'
        elif status['is_after_hours']:
            status['recommended_strategy'] = 'AFTER_HOURS_ANALYSIS'
            status['reason'] = 'After hours - analyze for tomorrow'
        else:
            status['recommended_strategy'] = 'INVESTING'
            status['reason'] = 'Market closed - focus on long-term investments'
        
        return status
    
    def should_day_trade(self, dt: datetime = None) -> bool:
        """Determine if day trading is appropriate"""
        status = self.get_market_status(dt)
        
        # Only day trade during market hours with high volatility
        if not status['is_market_open']:
            return False
        
        # Additional checks could be added here:
        # - Volume indicators
        # - Volatility metrics
        # - News catalysts
        
        return True

if __name__ == "__main__":
    detector = MarketHoursDetector()
    status = detector.get_market_status()
    
    print("🕐 MARKET STATUS:")
    print(f"   Time: {status['datetime']}")
    print(f"   Market Open: {status['is_market_open']}")
    print(f"   Pre-Market: {status['is_pre_market']}")
    print(f"   After Hours: {status['is_after_hours']}")
    print(f"   Recommended Strategy: {status['recommended_strategy']}")
    print(f"   Reason: {status['reason']}")
    
    if status['time_until_open']:
        print(f"   Time Until Open: {status['time_until_open']}")
    if status['time_until_close']:
        print(f"   Time Until Close: {status['time_until_close']}")
