"""
Conviction Watchlist - Millionaire Maker Stock Tracker

Tracks high-potential stocks with massive upside potential.
Generates "accumulate on dips" signals for stocks with strong fundamentals.

Key Features:
- Persistent tracking across sessions
- Dip detection and buy signal generation
- Growth potential scoring (10x-100x)
- Disruptive business model identification
- Institutional accumulation tracking
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Optional, Tuple
import json
import os


class ConvictionStock:
    """Represents a high-conviction stock with millionaire maker potential"""
    
    def __init__(self, ticker: str, name: str, thesis: str, potential: str):
        self.ticker = ticker
        self.name = name
        self.thesis = thesis  # Why this could be a 10x-100x
        self.potential = potential  # "10x", "50x", "100x"
        self.last_signal = None
        self.last_price = 0
        self.avg_cost = 0
        self.position_size = 0
        self.dip_signals = []
        self.strong_buy_signals = []
        self.last_updated = datetime.now()


class ConvictionWatchlist:
    """
    Tracks high-conviction stocks and generates buy signals on dips
    """
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.watchlist_file = 'data/conviction_watchlist.json'
        self.watchlist = self._load_watchlist()
        
        # Dip detection parameters
        self.dip_threshold = float(self.config.get('conviction', {}).get('dip_threshold', 0.15))  # 15% dip
        self.strong_buy_threshold = float(self.config.get('conviction', {}).get('strong_buy_threshold', 0.25))  # 25% dip
        self.volume_surge_multiplier = float(self.config.get('conviction', {}).get('volume_surge_multiplier', 2.0))
        
        # Conviction criteria
        self.min_growth_rate = float(self.config.get('conviction', {}).get('min_growth_rate', 0.5))  # 50% YoY growth
        self.max_market_cap = float(self.config.get('conviction', {}).get('max_market_cap', 50e9))  # Under $50B
        
        # Initialize with high-potential stocks
        self._initialize_watchlist()
    
    def _initialize_watchlist(self):
        """Initialize with pre-selected high-potential stocks"""
        if not self.watchlist:
            # SOFI - Fintech disruption
            self.add_stock(
                ticker="SOFI",
                name="SoFi Technologies",
                thesis="Fintech disruptor targeting millennial/Gen Z with full financial ecosystem. Lending, investing, banking all-in-one platform with massive TAM.",
                potential="10x-50x"
            )
            
            # PLTR - Big data analytics
            self.add_stock(
                ticker="PLTR",
                name="Palantir Technologies",
                thesis="AI-powered data analytics for government and enterprise. Moat in complex data integration, expanding into commercial markets.",
                potential="10x-30x"
            )
            
            # RIVN - EV disruption
            self.add_stock(
                ticker="RIVN",
                name="Rivian Automotive",
                thesis="EV manufacturer with Amazon backing. First-mover in electric adventure vehicles, potential to challenge Tesla in premium EV segment.",
                potential="20x-100x"
            )
            
            # LCID - Luxury EV
            self.add_stock(
                ticker="LCID",
                name="Lucid Motors",
                thesis="Luxury EV maker with superior technology. Air sedan has best-in-class range, targeting high-margin luxury segment.",
                potential="10x-50x"
            )
            
            # AI - Cloud computing
            self.add_stock(
                ticker="AI",
                name="C3.ai",
                thesis="Enterprise AI platform-as-a-service. First pure-play AI SaaS, positioned for massive enterprise AI adoption.",
                potential="20x-100x"
            )
    
    def add_stock(self, ticker: str, name: str, thesis: str, potential: str):
        """Add a stock to the conviction watchlist"""
        stock = ConvictionStock(ticker, name, thesis, potential)
        self.watchlist[ticker] = stock
        self._save_watchlist()
    
    def analyze_watchlist(self) -> List[Dict]:
        """Analyze all watchlist stocks for dip opportunities"""
        print("[CONVICTION WATCHLIST] Scanning for dip buying opportunities...")
        
        opportunities = []
        
        for ticker, stock in self.watchlist.items():
            try:
                # Get current data
                yf_ticker = yf.Ticker(ticker)
                hist = yf_ticker.history(period="3mo")
                info = yf_ticker.info
                
                if hist.empty or len(hist) < 20:
                    continue
                
                current_price = hist['Close'].iloc[-1]
                avg_volume = hist['Volume'].mean()
                recent_volume = hist['Volume'].iloc[-1]
                
                # Calculate dip percentage from 20-day high
                high_20d = hist['High'].rolling(20).max().iloc[-1]
                dip_pct = (high_20d - current_price) / high_20d
                
                # Check for growth metrics
                revenue_growth = info.get('revenueGrowth', 0)
                market_cap = info.get('marketCap', 0)
                
                # Volume surge check
                volume_surge = recent_volume / avg_volume if avg_volume > 0 else 0
                
                # Generate signals
                signal = self._generate_signal(stock, current_price, dip_pct, volume_surge, revenue_growth, market_cap)
                
                if signal:
                    opportunities.append(signal)
                    print(f"   SIGNAL: {ticker} - {signal['signal_type']} at ${current_price:.2f} ({dip_pct:.1%} dip)")
                
                # Update stock data
                stock.last_price = current_price
                stock.last_updated = datetime.now()
                
            except Exception as e:
                print(f"   Error analyzing {ticker}: {str(e)}")
                continue
        
        if opportunities:
            print(f"\n[CONVICTION WATCHLIST] Found {len(opportunities)} dip opportunities")
        
        return opportunities
    
    def _generate_signal(self, stock: ConvictionStock, price: float, dip_pct: float, 
                        volume_surge: float, revenue_growth: float, market_cap: float) -> Optional[Dict]:
        """Generate buy signal based on dip and fundamentals"""
        
        # Must meet growth criteria
        if revenue_growth < self.min_growth_rate:
            return None
        
        # Must be under market cap threshold
        if market_cap > self.max_market_cap:
            return None
        
        signal_type = None
        conviction_level = ""
        
        # Strong buy signal on deep dip
        if dip_pct >= self.strong_buy_threshold and volume_surge >= self.volume_surge_multiplier:
            signal_type = "STRONG BUY - DEEP DIP"
            conviction_level = "MAXIMUM CONVICTION"
            action = "BACK UP THE TRUCK"
            
        # Regular buy signal on moderate dip
        elif dip_pct >= self.dip_threshold:
            signal_type = "BUY - DIP ACCUMULATION"
            conviction_level = "HIGH CONVICTION"
            action = "BUY MORE"
            
        # Add to position on any weakness if fundamentals strong
        elif dip_pct >= 0.05 and revenue_growth > self.min_growth_rate * 2:
            signal_type = "ADD - WEAKNESS"
            conviction_level = "CONVICTION ADD"
            action = "ADD SHARES"
        
        if signal_type:
            return {
                'ticker': stock.ticker,
                'name': stock.name,
                'signal_type': signal_type,
                'conviction_level': conviction_level,
                'action': action,
                'price': price,
                'dip_percentage': dip_pct,
                'volume_surge': volume_surge,
                'revenue_growth': revenue_growth,
                'thesis': stock.thesis,
                'potential': stock.potential,
                'reasoning': self._generate_reasoning(stock, dip_pct, revenue_growth, volume_surge)
            }
        
        return None
    
    def _generate_reasoning(self, stock: ConvictionStock, dip_pct: float, 
                           revenue_growth: float, volume_surge: float) -> str:
        """Generate reasoning for the signal"""
        
        reasoning = f"CONVICTION ANALYSIS: {stock.ticker} ({stock.name})\n\n"
        reasoning += f"THESIS: {stock.thesis}\n"
        reasoning += f"POTENTIAL: {stock.potential} upside\n\n"
        
        reasoning += f"CURRENT OPPORTUNITY:\n"
        reasoning += f"• Trading {dip_pct:.1%} below 20-day high\n"
        reasoning += f"• Revenue growth: {revenue_growth:.1%} YoY\n"
        
        if volume_surge > 1.5:
            reasoning += f"• Volume surge: {volume_surge:.1f}x average\n"
        
        reasoning += f"\nACTION: {stock.potential} potential stock on sale - "
        reasoning += f"accumulate for long-term massive upside"
        
        return reasoning
    
    def _load_watchlist(self) -> Dict[str, ConvictionStock]:
        """Load watchlist from file"""
        if os.path.exists(self.watchlist_file):
            try:
                with open(self.watchlist_file, 'r') as f:
                    data = json.load(f)
                    watchlist = {}
                    for ticker, stock_data in data.items():
                        stock = ConvictionStock(
                            ticker=stock_data['ticker'],
                            name=stock_data['name'],
                            thesis=stock_data['thesis'],
                            potential=stock_data['potential']
                        )
                        stock.last_price = stock_data.get('last_price', 0)
                        stock.avg_cost = stock_data.get('avg_cost', 0)
                        stock.position_size = stock_data.get('position_size', 0)
                        watchlist[ticker] = stock
                    return watchlist
            except Exception as e:
                print(f"Error loading watchlist: {e}")
        
        return {}
    
    def _save_watchlist(self):
        """Save watchlist to file"""
        os.makedirs(os.path.dirname(self.watchlist_file), exist_ok=True)
        
        data = {}
        for ticker, stock in self.watchlist.items():
            data[ticker] = {
                'ticker': stock.ticker,
                'name': stock.name,
                'thesis': stock.thesis,
                'potential': stock.potential,
                'last_price': stock.last_price,
                'avg_cost': stock.avg_cost,
                'position_size': stock.position_size
            }
        
        with open(self.watchlist_file, 'w') as f:
            json.dump(data, f, indent=2)
