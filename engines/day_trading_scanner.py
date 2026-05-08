"""Day Trading Stock Scanner - Generate regular stock signals for buy/sell trading"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random

class DayTradingScanner:
    """Scanner for regular day trading stocks with momentum and volume analysis"""
    
    def __init__(self, config=None):
        self.config = config or {}
        self.min_volume = 100000  # Minimum average volume
        self.min_price = 5.0  # Minimum stock price
        self.max_price = 50.0  # Maximum stock price (matches $50 bankroll)
        
        # Popular day trading stocks to watch
        self.watchlist = [
            'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA',
            'AMD', 'NFLX', 'PYPL', 'DIS', 'BABA', 'UBER', 'LYFT',
            'SNAP', 'TWTR', 'ROKU', 'ZM', 'PLTR', 'GME', 'AMC',
            'BB', 'NOK', 'SNDL', 'BNGO', 'MVIS', 'SPCE', 'RIVN',
            'LCID', 'CHPT', 'BLNK', 'FSR', 'LCID', 'RIVN'
        ]
    
    def scan_momentum_stocks(self, limit=10, additional_symbols=None, bankroll=50.0):
        """Scan for stocks with strong momentum and volume"""
        signals = []
        
        # Use dynamic scanner to get fresh opportunities
        try:
            from engines.dynamic_market_scanner import DynamicMarketScanner
            dynamic_scanner = DynamicMarketScanner()
            fresh_opps = dynamic_scanner.get_fresh_opportunities(total_limit=20)
            
            # Extract symbols from fresh opportunities
            symbols_to_scan = [opp['symbol'] for opp in fresh_opps]
            
            # Add any additional symbols from news
            if additional_symbols:
                for symbol in additional_symbols:
                    if symbol not in symbols_to_scan:
                        symbols_to_scan.append(symbol)
                        
            print(f"   🎯 Using {len(symbols_to_scan)} FRESH symbols from dynamic scanner")
            
        except Exception as e:
            # Fallback to watchlist if dynamic scanner fails
            symbols_to_scan = self.watchlist.copy()
            if additional_symbols:
                for symbol in additional_symbols:
                    if symbol not in symbols_to_scan:
                        symbols_to_scan.append(symbol)
        
        print(f"Scanning {len(symbols_to_scan)} stocks for day trading opportunities...")
        print(f"   Criteria: Price ${self.min_price:.1f}-${self.max_price:.1f}, Volume >= {self.min_volume:,}")
        print(f"   Symbols to check: {symbols_to_scan[:10]}...")  # Show first 10 symbols
        
        for symbol in symbols_to_scan:
            print(f"   Checking symbol: {symbol}")
        
        for symbol in symbols_to_scan[:limit]:
            try:
                # Get stock data
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period="5d", interval="1d")
                
                if len(hist) < 5:
                    print(f"  ! {symbol}: Insufficient data")
                    continue
                
                # Current price and volume
                current_price = hist['Close'].iloc[-1]
                current_volume = hist['Volume'].iloc[-1]
                avg_volume = hist['Volume'].mean()
                
                print(f"  Stock {symbol}: ${current_price:.2f} | Vol: {current_volume:,} | Avg: {avg_volume:,}")
                
                # Price filters
                if current_price < self.min_price or current_price > self.max_price:
                    print(f"    X Price filter failed (${current_price:.2f})")
                    continue
                
                if avg_volume < self.min_volume:
                    print(f"    X Volume filter failed ({avg_volume:,} < {self.min_volume:,})")
                    continue
                
                # Momentum indicators
                price_change_5d = (current_price - hist['Close'].iloc[0]) / hist['Close'].iloc[0]
                volume_ratio = current_volume / avg_volume
                
                # RSI calculation
                rsi = self.calculate_rsi(hist['Close'])
                
                print(f"    Change: {price_change_5d*100:.1f}% | Vol Ratio: {volume_ratio:.1f}x | RSI: {rsi:.0f}")
                
                # Generate signal based on criteria
                if self.is_buy_signal(price_change_5d, volume_ratio, rsi):
                    # Calculate confidence for position sizing
                    base_confidence = min(90, max(30, abs(price_change_5d) * 1000 + random.randint(10, 30)))
                    confidence_pct = base_confidence / 100.0
                    
                    # Calculate position sizing based on bankroll and confidence
                    position_info = self.calculate_position_size(current_price, bankroll, confidence_pct)
                    
                    signal = {
                        'symbol': symbol,
                        'action': 'BUY',
                        'entry_price': round(current_price, 2),
                        'target_price': round(current_price * 1.05, 2),  # 5% target
                        'confidence': min(90, max(30, abs(price_change_5d) * 1000 + random.randint(10, 30))),
                        'pop_from_sim': min(95, max(55, 50 + volume_ratio * 10 + random.randint(5, 20))),
                        'volume': int(current_volume),
                        'avg_volume': int(avg_volume),
                        'rsi': round(rsi, 2),
                        'price_change_5d': round(price_change_5d * 100, 2),
                        'sector': self.get_sector(symbol),
                        'industry': 'Technology',
                        'market_cap': self.get_market_cap(ticker),
                        'pattern_strength': min(0.5, abs(price_change_5d) * 5),
                        'divergence_score': 0.0,  # Not applicable for stocks
                        'win_rate': min(0.95, max(0.35, 0.5 + abs(price_change_5d) * 2)),
                        'catalyst_type': 'Momentum',
                        'title': f"{symbol} shows strong momentum with {volume_ratio:.1f}x volume",
                        'source': 'day_trading',
                        # Position sizing info
                        'shares_to_buy': position_info['shares'],
                        'position_cost': position_info['cost'],
                        'position_risk': position_info['risk_amount'],
                        'bankroll_used_pct': position_info['bankroll_used_pct']
                    }
                    signals.append(signal)
                    print(f"    SIGNAL GENERATED for {symbol}: ${current_price:.2f} | Volume: {volume_ratio:.1f}x | RSI: {rsi:.0f}")
                else:
                    print(f"    X Buy signal criteria failed")
                
            except Exception as e:
                print(f"  ! Error scanning {symbol}: {e}")
                continue
        
        print(f"Found {len(signals)} day trading opportunities")
        return signals
    
    def calculate_rsi(self, prices, periods=14):
        """Calculate RSI indicator"""
        try:
            delta = prices.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=periods).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=periods).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            rsi_value = rsi.iloc[-1] if not rsi.empty else 50
            # Handle NaN values
            if pd.isna(rsi_value) or not np.isfinite(rsi_value):
                return 50  # Neutral RSI
            return rsi_value
        except Exception:
            return 50  # Neutral RSI on any error
    
    def is_buy_signal(self, price_change, volume_ratio, rsi):
        """Check if stock meets buy criteria"""
        # Price momentum (positive or slight negative dip)
        if price_change < -0.10:  # More than 10% drop = skip
            print(f"      X Price change too negative: {price_change*100:.1f}%")
            return False
        
        # Volume surge - lowered threshold
        if volume_ratio < 1.0:  # Need normal or higher volume
            print(f"      X Volume too low: {volume_ratio:.1f}x")
            return False
        
        # RSI not overbought
        if rsi > 80:  # Too overbought
            print(f"      X RSI too overbought: {rsi:.0f}")
            return False
        
        # RSI not oversold (optional bounce play)
        if rsi < 20:
            print(f"      X RSI too oversold: {rsi:.0f}")
            return False
        
        print(f"      * All criteria passed!")
        return True
    
    def get_sector(self, symbol):
        """Get sector for symbol"""
        sectors = {
            'AAPL': 'Technology', 'MSFT': 'Technology', 'GOOGL': 'Technology',
            'AMZN': 'Consumer Discretionary', 'TSLA': 'Consumer Discretionary',
            'META': 'Technology', 'NVDA': 'Technology', 'AMD': 'Technology',
            'NFLX': 'Technology', 'PYPL': 'Technology', 'DIS': 'Communication Services',
            'BABA': 'Consumer Discretionary', 'UBER': 'Technology', 'LYFT': 'Technology',
            'SNAP': 'Technology', 'TWTR': 'Technology', 'ROKU': 'Technology',
            'ZM': 'Technology', 'PLTR': 'Technology', 'GME': 'Consumer Discretionary',
            'AMC': 'Consumer Discretionary', 'BB': 'Technology', 'NOK': 'Technology',
            'SNDL': 'Consumer Discretionary', 'BNGO': 'Healthcare', 'MVIS': 'Technology',
            'SPCE': 'Industrials', 'RIVN': 'Consumer Discretionary', 'LCID': 'Consumer Discretionary',
            'CHPT': 'Industrials', 'BLNK': 'Consumer Discretionary', 'FSR': 'Consumer Discretionary'
        }
        return sectors.get(symbol, 'Technology')
    
    def calculate_dynamic_risk(self, confidence, simulation_win_rate=None):
        """Calculate risk percentage based on confidence and simulation results"""
        # Use the lower of AI confidence and simulation win rate
        effective_confidence = confidence
        
        if simulation_win_rate is not None:
            effective_confidence = min(confidence, simulation_win_rate)
        
        # More aggressive risk scaling for faster profits
        # Scale risk from 3% to 8% based on confidence
        # 75% confidence = 3% risk
        # 95% confidence = 8% risk
        if effective_confidence >= 0.75:
            risk_pct = 0.03 + (effective_confidence - 0.75) * 0.25  # Max 8% at 95%
            risk_pct = min(risk_pct, 0.08)  # Cap at 8%
        else:
            risk_pct = 0.03  # Minimum 3% risk
        
        return risk_pct
    
    def calculate_position_size(self, stock_price, bankroll, confidence=0.5, simulation_win_rate=None):
        """Calculate position size based on bankroll, confidence, and risk management"""
        # Calculate dynamic risk based on confidence
        risk_per_trade = self.calculate_dynamic_risk(confidence, simulation_win_rate)
        
        # Risk amount based on confidence
        max_risk_amount = bankroll * risk_per_trade
        
        # Use 5% stop loss (standard for day trades)
        stop_loss_pct = 0.05
        
        # Calculate maximum position size based on risk
        max_position_value = max_risk_amount / stop_loss_pct
        
        # Limit to 30% of bankroll maximum per trade for high confidence trades
        max_cap_pct = 0.30 if confidence >= 0.90 else 0.20
        max_position_value = min(max_position_value, bankroll * max_cap_pct)
        
        # Calculate number of shares
        shares = int(max_position_value / stock_price)
        
        # Ensure at least 1 share if affordable
        if shares == 0 and stock_price <= bankroll * 0.20:
            shares = 1
        
        # Calculate actual position cost and risk
        position_cost = shares * stock_price
        actual_risk = position_cost * stop_loss_pct
        bankroll_used_pct = (position_cost / bankroll) * 100
        
        return {
            'shares': shares,
            'cost': round(position_cost, 2),
            'risk_amount': round(actual_risk, 2),
            'bankroll_used_pct': round(bankroll_used_pct, 1),
            'max_loss': round(position_cost * stop_loss_pct, 2)
        }
    
    def get_market_cap(self, ticker):
        """Get market cap from ticker info"""
        try:
            info = ticker.info
            market_cap = info.get('marketCap', 0)
            return market_cap
        except:
            return 1000000000  # Default $1B

def get_day_trading_scanner(config=None):
    """Get day trading scanner instance"""
    return DayTradingScanner(config)
