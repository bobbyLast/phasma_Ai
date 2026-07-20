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
    
    def __init__(self, config=None):
        self.config = config or {}
        # Seed universe — expanded at runtime via InfiniteSymbolProvider
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
        self._expand_universe_from_provider()
        
        # Daily movers from different sectors
        self.sectors = {
            'Technology': ['AAPL', 'MSFT', 'NVDA', 'AMD', 'META', 'GOOGL', 'CRM', 'NOW', 'ORCL', 'ADBE', 'INTC', 'CSCO'],
            'Healthcare': ['JNJ', 'UNH', 'PFE', 'ABBV', 'TMO', 'MRK', 'LLY', 'ABT', 'AMGN', 'GILD', 'BMY', 'ISRG'],
            'Finance': ['JPM', 'BAC', 'WFC', 'GS', 'MS', 'C', 'AXP', 'BLK', 'SCHW', 'USB', 'PNC', 'TFC'],
            'Consumer': ['WMT', 'COST', 'HD', 'MCD', 'NKE', 'SBUX', 'KO', 'PEP', 'TGT', 'LOW', 'SBUX', 'PG'],
            'Energy': ['XOM', 'CVX', 'COP', 'SLB', 'HAL', 'BP', 'SHEL', 'ENPH', 'OXY', 'EOG', 'MPC', 'VLO'],
            'Industrial': ['CAT', 'DE', 'BA', 'GE', 'MMM', 'HON', 'UPS', 'RTX', 'LMT', 'UNP', 'FDX', 'EMR'],
            'Software': ['CRM', 'NOW', 'SNOW', 'DDOG', 'ZS', 'OKTA', 'TEAM', 'PLTR', 'PATH', 'NET', 'CRWD', 'PANW'],
            'Biotech': ['MRNA', 'BNTX', 'REGN', 'VRTX', 'BIIB', 'ILMN', 'ALNY', 'SGEN', 'EXAS', 'NBIX'],
        }

    def _expand_universe_from_provider(self) -> None:
        """Merge S&P/NASDAQ/ETF/crypto pools so we are not stuck on ~190 names."""
        try:
            from utils.infinite_symbol_provider import InfiniteSymbolProvider
            provider = InfiniteSymbolProvider()
            extra = provider.get_symbols(category="all", limit=None) or []
            merged = list(dict.fromkeys(
                [str(s).upper().replace(".", "-") for s in (self.stock_universe + list(extra)) if s]
            ))
            # Prefer equity tickers for mover scans (keep crypto/ETF separately usable)
            equities = [s for s in merged if "-" not in s and len(s) <= 5]
            self.stock_universe = equities if len(equities) >= 100 else merged
            print(f"   Dynamic scanner universe expanded to {len(self.stock_universe)} symbols")
        except Exception as exc:
            print(f"   Dynamic scanner universe expand skipped: {exc}")

    
    def get_daily_movers(self, min_volume=1000000, min_price=5.0, max_stocks=20) -> List[Dict]:
        """Find today's top movers with high volume across all sectors + universe sample."""
        movers = []
        
        # Scan ALL sectors (not a random 5) for competitive coverage
        selected_sectors = list(self.sectors.keys())
        
        for sector in selected_sectors:
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

        # Extra pass: sample broader liquid universe beyond sector seeds
        if len(movers) < max_stocks and self.stock_universe:
            seen = {m['symbol'] for m in movers}
            sample_n = min(120, len(self.stock_universe))
            for symbol in random.sample(self.stock_universe, k=sample_n):
                if symbol in seen:
                    continue
                try:
                    hist = yf.Ticker(symbol).history(period="5d")
                    if hist is None or len(hist) < 2:
                        continue
                    current_price = float(hist['Close'].iloc[-1])
                    prev_price = float(hist['Close'].iloc[-2])
                    if current_price < min_price:
                        continue
                    pct_change = ((current_price - prev_price) / prev_price) * 100
                    volume = float(hist['Volume'].iloc[-1])
                    if volume > min_volume and abs(pct_change) > 2:
                        movers.append({
                            'symbol': symbol,
                            'sector': 'Broad',
                            'price': round(current_price, 2),
                            'change_pct': round(pct_change, 2),
                            'volume': volume,
                            'momentum': 'BULLISH' if pct_change > 0 else 'BEARISH'
                        })
                        seen.add(symbol)
                    if len(movers) >= max_stocks * 2:
                        break
                except Exception:
                    continue
            movers.sort(key=lambda x: abs(x['change_pct']), reverse=True)

        return movers[:max_stocks]
    
    def get_breakout_candidates(self, min_volume=500000, max_stocks=15) -> List[Dict]:
        """Find stocks breaking out of recent ranges"""
        breakouts = []
        
        # Sample a large slice of the expanded universe each cycle
        symbols_to_check = random.sample(self.stock_universe, k=min(150, len(self.stock_universe)))
        
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
        symbols_to_check = random.sample(self.stock_universe, k=min(100, len(self.stock_universe)))
        
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
        # Scale sub-scans with requested total (competitive discovery)
        movers_n = max(10, int(total_limit * 0.45))
        break_n = max(8, int(total_limit * 0.35))
        value_n = max(7, int(total_limit * 0.25))
        
        movers = self.get_daily_movers(max_stocks=movers_n)
        all_opportunities.extend(movers)
        
        breakouts = self.get_breakout_candidates(max_stocks=break_n)
        all_opportunities.extend(breakouts)
        
        undervalued = self.get_undervalued_stocks(max_stocks=value_n)
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
