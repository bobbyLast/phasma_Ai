"""
Silver Price Monitor
Monitors silver price movements and generates signals
"""

import yfinance as yf
import asyncio
from typing import Dict, List, Any
from datetime import datetime, timedelta

class SilverPriceMonitor:
    """Monitors SLV (Silver ETF) price movements"""
    
    def __init__(self):
        self.symbol = 'SLV'
        self.last_price = None
        self.price_history = []
        
    async def get_current_silver_price(self) -> float:
        """Get current SLV price"""
        try:
            ticker = yf.Ticker(self.symbol)
            hist = ticker.history(period='2d')
            
            if len(hist) > 1:
                current = float(hist['Close'].iloc[-1])
                previous = float(hist['Close'].iloc[-2])
                
                change = current - previous
                change_pct = (change / previous) * 100
                
                return current, change, change_pct
        except Exception as e:
            print(f"Error getting SLV price: {e}")
            
        return None, 0, 0
    
    async def check_silver_opportunity(self) -> Dict[str, Any]:
        """Check if there's a silver trading opportunity"""
        
        current, change, change_pct = await self.get_current_silver_price()
        
        if current is None:
            return None
        
        # Generate signal if silver is moving significantly
        signal = None
        
        if abs(change_pct) > 2.0:  # 2% movement threshold
            direction = "RALLY" if change_pct > 0 else "DROP"
            confidence = min(90, 60 + abs(change_pct) * 5)
            
            signal = {
                'symbol': 'SLV',
                'source': 'price_monitor',
                'title': f'Silver {direction}: {change_pct:.2f}%',
                'summary': f'Silver ETF (SLV) is {direction.lower()} {abs(change_pct):.2f}% to ${current:.2f}',
                'confidence': confidence,
                'timestamp': datetime.now().isoformat(),
                'signal_type': f'SILVER_{direction}',
                'reason': f'Silver price {"surging" if change_pct > 0 else "dropping"} {abs(change_pct):.2f}%',
                'current_price': current,
                'price_change': change,
                'price_change_pct': change_pct,
                'url': f'https://finance.yahoo.com/quote/{self.symbol}'
            }
            
            print(f"🥈 SILVER SIGNAL: {direction} {abs(change_pct):.2f}% at ${current:.2f}")
        
        return signal

# Add to main system
def add_silver_monitor_to_system(trading_system):
    """Add silver monitoring to the trading system"""
    
    monitor = SilverPriceMonitor()
    trading_system.silver_monitor = monitor
    
    # Override the news scanning to include silver check
    original_scan = trading_system.scan_news_sources
    
    async def enhanced_scan():
        """Enhanced scan that includes silver monitoring"""
        
        # Get original news
        news_signals = await original_scan()
        
        # Check silver price
        silver_signal = await monitor.check_silver_opportunity()
        
        if silver_signal:
            print(f"\n🥈 SILVER PRICE ALERT: {silver_signal['title']}")
            news_signals.append(silver_signal)
        else:
            # Check current price anyway
            current, _, _ = await monitor.get_current_silver_price()
            if current:
                print(f"\n🥈 Silver Price: ${current:.2f} (no significant movement)")
        
        return news_signals
    
    trading_system.scan_news_sources = enhanced_scan
    print("✅ Silver price monitor added to trading system")
