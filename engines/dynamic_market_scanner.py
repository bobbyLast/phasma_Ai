"""
Dynamic Market Scanner - Finds fresh trading opportunities daily
Instead of using the same stocks repeatedly, scans for new movers
"""

import yfinance as yf
import pandas as pd
from typing import List, Dict, Any
import random
from datetime import datetime, timedelta

class DynamicMarketScanner:
    """Scans market for fresh opportunities based on real-time data"""
    
    def __init__(self):
        # Broad universe of liquid US stocks
        self.stock_universe = [
            # Tech Giants
            'AAPL', 'MSFT', 'GOOGL', 'GOOG', 'META', 'NVDA', 'AMD', 'INTC', 'CSCO', 'ORCL',
            # Cloud & Software
            'CRM', 'NOW', 'TEAM', 'ADBE', 'INTU', 'SNOW', 'PLTR', 'DDOG', 'ZS', 'OKTA',
            # Semiconductors
            'TSM', 'ASML', 'QCOM', 'TXN', 'MU', 'LRCX', 'KLAC', 'AMAT', 'MRVL', 'ON',
            # AI & Data
            'AI', 'SOUN', 'UPST', 'PATH', 'RGTI', 'BBAI', 'C3AI', 'DUOL', 'CHEK', 'VERI',
            # E-commerce & Internet
            'AMZN', 'EBAY', 'ETSY', 'SHOP', 'BABA', 'JD', 'PDD', 'MELI', 'SE', 'RBLX',
            # Gaming & Streaming
            'TCEHY', 'NTDOY', 'EA', 'TTWO', 'ATVI', 'NFLX', 'DIS', 'ROKU', 'PARA', 'WBD',
            # EV & Auto
            'TSLA', 'RIVN', 'LCID', 'NIO', 'XPEV', 'LI', 'GM', 'F', 'TM', 'HMC',
            # Energy & Clean Tech
            'XOM', 'CVX', 'COP', 'SLB', 'HAL', 'BP', 'SHEL', 'ENPH', 'SEDG', 'FSLR',
            # Financials
            'JPM', 'BAC', 'WFC', 'GS', 'MS', 'C', 'AXP', 'BLK', 'SPGI', 'V',
            # Healthcare
            'JNJ', 'UNH', 'PFE', 'ABBV', 'TMO', 'ABT', 'DHR', 'BMY', 'AMGN', 'GILD',
            # Consumer
            'WMT', 'COST', 'HD', 'MCD', 'NKE', 'SBUX', 'KO', 'PEP', 'PG', 'CL',
            # Industrial
            'CAT', 'DE', 'BA', 'GE', 'MMM', 'HON', 'UPS', 'RTX', 'LMT', 'NOV',
            # Retail
            'TGT', 'LOW', 'BBY', 'TJX', 'ROST', 'M', 'KSS', 'JCP', 'DLTR', 'BIG',
            # Biotech
            'GILD', 'BIIB', 'MRK', 'LLY', 'AZN', 'NVS', 'SNY', 'BNTX', 'REGN', 'VRTX',
            # Telecom
            'VZ', 'T', 'TMUS', 'S', 'CMCSA', 'CHTR', 'DISH', 'LUMN', 'WIN', 'ATUS',
            # Meme & High Volatility (reduced)
            'GME', 'AMC', 'BB', 'NOK', 'SNDL', 'BNGO', 'MVIS', 'SPCE', 'WKHS', 'PLTR',
            # REITs
            'AMT', 'PLD', 'CCI', 'EQIX', 'PSA', 'O', 'DLR', 'EXR', 'PRO', 'VICI',
            # Materials
            'BHP', 'RIO', 'VALE', 'FCX', 'NUE', 'X', 'AA', 'DD', 'DOW', 'EMN',
            # Utilities
            'NEE', 'DUK', 'SO', 'AEP', 'EXC', 'SRE', 'XEL', 'ED', 'PEG', 'WEC'
        ]
        
        # Daily movers from different sectors
        self.sectors = {
            'Technology': ['AAPL', 'MSFT', 'NVDA', 'AMD', 'META', 'GOOGL', 'CRM', 'NOW'],
            'Healthcare': ['JNJ', 'UNH', 'PFE', 'ABBV', 'TMO', 'MRK', 'LLY', 'ABT'],
            'Finance': ['JPM', 'BAC', 'WFC', 'GS', 'MS', 'C', 'AXP', 'BLK'],
            'Consumer': ['WMT', 'COST', 'HD', 'MCD', 'NKE', 'SBUX', 'KO', 'PEP'],
            'Energy': ['XOM', 'CVX', 'COP', 'SLB', 'HAL', 'BP', 'SHEL', 'ENPH'],
            'Industrial': ['CAT', 'DE', 'BA', 'GE', 'MMM', 'HON', 'UPS', 'RTX']
        }
    
    def get_daily_movers(self, min_volume=1000000, min_price=5.0, max_stocks=20) -> List[Dict]:
        """Find today's top movers with high volume"""
        movers = []
        
        # Randomly select different sectors each day to ensure variety
        selected_sectors = random.sample(list(self.sectors.keys()), k=min(5, len(self.sectors)))
        
        for sector in selected_sectors:
            # Get symbols from this sector
            sector_symbols = self.sectors[sector]
            
            for symbol in sector_symbols:
                try:
                    # Get stock data
                    ticker = yf.Ticker(symbol)
                    hist = ticker.history(period="5d")
                    
                    if hist.empty:
                        continue
                    
                    # Get current price and change
                    current_price = hist['Close'].iloc[-1]
                    prev_price = hist['Close'].iloc[-2]
                    
                    # Skip if price too low
                    if current_price < min_price:
                        continue
                    
                    # Calculate percent change
                    pct_change = ((current_price - prev_price) / prev_price) * 100
                    
                    # Get volume
                    volume = hist['Volume'].iloc[-1]
                    
                    # Only include stocks with decent volume and movement
                    if volume > min_volume and abs(pct_change) > 2:
                        movers.append({
                            'symbol': symbol,
                            'sector': sector,
                            'price': round(current_price, 2),
                            'change_pct': round(pct_change, 2),
                            'volume': volume,
                            'momentum': 'BULLISH' if pct_change > 0 else 'BEARISH'
                        })
                        
                except Exception as e:
                    continue
        
        # Sort by absolute change and return top movers
        movers.sort(key=lambda x: abs(x['change_pct']), reverse=True)
        return movers[:max_stocks]
    
    def get_breakout_candidates(self, min_volume=500000, max_stocks=15) -> List[Dict]:
        """Find stocks breaking out of recent ranges"""
        breakouts = []
        
        # Sample different stocks each day
        symbols_to_check = random.sample(self.stock_universe, k=min(50, len(self.stock_universe)))
        
        for symbol in symbols_to_check:
            try:
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period="30d")
                
                if len(hist) < 20:
                    continue
                
                # Calculate 20-day high and low
                high_20 = hist['High'].iloc[-20:-1].max()
                low_20 = hist['Low'].iloc[-20:-1].max()
                current_price = hist['Close'].iloc[-1]
                volume = hist['Volume'].iloc[-1]
                
                # Check for breakout above 20-day high
                if current_price > high_20 * 1.02 and volume > min_volume:
                    breakouts.append({
                        'symbol': symbol,
                        'price': round(current_price, 2),
                        'breakout_level': round(high_20, 2),
                        'volume': volume,
                        'type': 'BULLISH_BREAKOUT'
                    })
                    
                # Check for breakdown below 20-day low
                elif current_price < low_20 * 0.98 and volume > min_volume:
                    breakouts.append({
                        'symbol': symbol,
                        'price': round(current_price, 2),
                        'breakdown_level': round(low_20, 2),
                        'volume': volume,
                        'type': 'BEARISH_BREAKDOWN'
                    })
                    
            except Exception as e:
                continue
        
        return breakouts[:max_stocks]
    
    def get_undervalued_stocks(self, max_stocks=10) -> List[Dict]:
        """Find potentially undervalued stocks based on recent drops"""
        undervalued = []
        
        # Look for stocks that dropped significantly but might be oversold
        symbols_to_check = random.sample(self.stock_universe, k=min(30, len(self.stock_universe)))
        
        for symbol in symbols_to_check:
            try:
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period="30d")
                
                if len(hist) < 20:
                    continue
                
                # Calculate recent drop
                recent_high = hist['High'].iloc[-10:-1].max()
                current_price = hist['Close'].iloc[-1]
                
                # Check if dropped at least 15% from recent high
                if current_price < recent_high * 0.85:
                    # Check if stabilizing (not dropping more in last 3 days)
                    last_3_days_low = hist['Low'].iloc[-3:].min()
                    if current_price > last_3_days_low * 0.95:
                        undervalued.append({
                            'symbol': symbol,
                            'price': round(current_price, 2),
                            'recent_high': round(recent_high, 2),
                            'drop_pct': round(((recent_high - current_price) / recent_high) * 100, 1),
                            'type': 'POTENTIAL_BOUNCE'
                        })
                        
            except Exception as e:
                continue
        
        return undervalued[:max_stocks]
    
    def get_fresh_opportunities(self, total_limit=25) -> List[Dict]:
        """Get a mix of fresh opportunities from different strategies"""
        all_opportunities = []
        
        # Get daily movers
        movers = self.get_daily_movers(max_stocks=10)
        all_opportunities.extend(movers)
        
        # Get breakouts
        breakouts = self.get_breakout_candidates(max_stocks=8)
        all_opportunities.extend(breakouts)
        
        # Get undervalued
        undervalued = self.get_undervalued_stocks(max_stocks=7)
        all_opportunities.extend(undervalued)
        
        # Remove duplicates and return
        seen = set()
        unique_opps = []
        for opp in all_opportunities:
            symbol = opp.get('symbol')
            if symbol and symbol not in seen:
                seen.add(symbol)
                unique_opps.append(opp)
        
        return unique_opps[:total_limit]
