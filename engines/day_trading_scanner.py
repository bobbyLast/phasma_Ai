"""Day Trading Stock Scanner - Generate regular stock signals for buy/sell trading"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Any

class DayTradingScanner:
    """Scanner for regular day trading stocks with momentum and volume analysis"""

    # New circulation / heavy-mover thresholds
    HEAVY_MIN_VOLUME_RATIO = 1.8
    HEAVY_MIN_DAY_CHANGE_PCT = 2.5
    HEAVY_NEWS_SCORE_BOOST = 1.25
    
    def __init__(self, config=None):
        self.config = config or {}
        from utils.price_filter_config import resolve_price_filter
        self.price_filter_enabled, cap = resolve_price_filter(self.config)
        self.min_volume = 100000  # Minimum average volume
        self.min_price = 5.0  # Minimum stock price
        self.max_price = cap if self.price_filter_enabled else 10000.0
        
        # Popular day trading stocks to watch
        self.watchlist = [
            'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA',
            'AMD', 'NFLX', 'PYPL', 'DIS', 'BABA', 'UBER', 'LYFT',
            'SNAP', 'TWTR', 'ROKU', 'ZM', 'PLTR', 'GME', 'AMC',
            'BB', 'NOK', 'SNDL', 'BNGO', 'MVIS', 'SPCE', 'RIVN',
            'LCID', 'CHPT', 'BLNK', 'FSR', 'LCID', 'RIVN'
        ]

    def _normalize_symbol(self, symbol: str) -> str:
        return str(symbol or "").strip().upper()

    def _resolve_symbols_to_scan(
        self,
        additional_symbols: Optional[List[str]] = None,
        dynamic_limit: int = 20,
    ) -> List[str]:
        """News-linked symbols first, then dynamic fresh names, then watchlist."""
        symbols_to_scan: List[str] = []
        seen: Set[str] = set()

        def _add(sym: str) -> None:
            normalized = self._normalize_symbol(sym)
            if not normalized or normalized.startswith("KX") or normalized in seen:
                return
            seen.add(normalized)
            symbols_to_scan.append(normalized)

        for symbol in additional_symbols or []:
            _add(symbol)

        try:
            from engines.dynamic_market_scanner import DynamicMarketScanner
            fresh_opps = DynamicMarketScanner().get_fresh_opportunities(total_limit=dynamic_limit)
            for opp in fresh_opps:
                _add(opp.get("symbol", ""))
            print(f"   Using {len(symbols_to_scan)} symbols (news-first + dynamic scanner)")
        except Exception:
            for symbol in self.watchlist:
                _add(symbol)
            print(f"   Dynamic scanner unavailable — using news + watchlist ({len(symbols_to_scan)} symbols)")

        return symbols_to_scan

    def _hist_from_batch_or_yf(
        self,
        symbol: str,
        history_batch: Optional[Dict[str, Any]] = None,
        *,
        min_rows: int = 2,
    ):
        """Prefer shared coalition history batch; fall back to yfinance once."""
        hist = None
        if history_batch:
            hist = history_batch.get(symbol)
        if hist is not None and hasattr(hist, "__len__") and len(hist) >= min_rows:
            return hist
        try:
            hist = yf.Ticker(symbol).history(period="5d", interval="1d")
            if hist is not None and len(hist) >= min_rows:
                return hist
        except Exception:
            return None
        return None

    def scan_heavy_movers(
        self,
        limit: int = 10,
        additional_symbols: Optional[List[str]] = None,
        min_volume_ratio: float = None,
        min_day_change_pct: float = None,
        history_batch: Optional[Dict[str, Any]] = None,
        coalition_boost: Optional[Dict[str, float]] = None,
    ) -> List[Dict]:
        """
        Rank stocks with new circulation (elevated relative volume + meaningful day move).
        Prefer news-linked symbols. Watch-oriented — not trade execution signals.
        """
        min_volume_ratio = (
            self.HEAVY_MIN_VOLUME_RATIO if min_volume_ratio is None else min_volume_ratio
        )
        min_day_change_pct = (
            self.HEAVY_MIN_DAY_CHANGE_PCT if min_day_change_pct is None else min_day_change_pct
        )
        news_set = {
            self._normalize_symbol(s)
            for s in (additional_symbols or [])
            if self._normalize_symbol(s)
        }

        symbols_to_scan = self._resolve_symbols_to_scan(additional_symbols, dynamic_limit=20)
        # Scan a wider pool than the return limit so ranking has room
        scan_cap = min(len(symbols_to_scan), max(limit * 4, 40))

        print(f"Scanning {scan_cap} stocks for heavy movers / new circulation...")
        print(
            f"   Criteria: day move >= {min_day_change_pct:.1f}%, "
            f"rel volume >= {min_volume_ratio:.1f}x, "
            f"price ${self.min_price:.1f}-${self.max_price:.1f}"
        )
        if history_batch:
            print(f"   Using shared market batch ({len(history_batch)} histories)")

        movers: List[Dict] = []
        for symbol in symbols_to_scan[:scan_cap]:
            try:
                hist = self._hist_from_batch_or_yf(symbol, history_batch, min_rows=2)
                if hist is None or len(hist) < 2:
                    continue

                current_price = float(hist["Close"].iloc[-1])
                prev_close = float(hist["Close"].iloc[-2])
                current_volume = float(hist["Volume"].iloc[-1])
                avg_volume = float(hist["Volume"].mean())

                if current_price < self.min_price:
                    continue
                if self.price_filter_enabled and current_price > self.max_price:
                    continue
                if avg_volume < self.min_volume or avg_volume <= 0 or prev_close <= 0:
                    continue

                day_change_pct = ((current_price - prev_close) / prev_close) * 100.0
                volume_ratio = current_volume / avg_volume
                if abs(day_change_pct) < min_day_change_pct:
                    continue
                if volume_ratio < min_volume_ratio:
                    continue

                rsi = self.calculate_rsi(hist["Close"])
                from_news = symbol in news_set
                direction = "up" if day_change_pct >= 0 else "down"
                reason = (
                    f"New circulation: {volume_ratio:.1f}x avg volume, "
                    f"{day_change_pct:+.1f}% day move ({direction})"
                )
                if from_news:
                    reason += " — in today's news"

                rank_score = abs(day_change_pct) * volume_ratio
                if from_news:
                    rank_score *= self.HEAVY_NEWS_SCORE_BOOST
                if coalition_boost and symbol in coalition_boost:
                    rank_score *= float(coalition_boost[symbol])

                movers.append({
                    "symbol": symbol,
                    "price": round(current_price, 2),
                    "change_pct": round(day_change_pct, 2),
                    "volume_ratio": round(volume_ratio, 2),
                    "volume": int(current_volume),
                    "avg_volume": int(avg_volume),
                    "rsi": round(float(rsi), 2),
                    "reason": reason,
                    "rank_score": round(rank_score, 2),
                    "from_news": from_news,
                    "sector": self.get_sector(symbol),
                    "source": "heavy_mover_watch",
                })
                print(
                    f"   MOVER {symbol}: {day_change_pct:+.1f}% | "
                    f"vol {volume_ratio:.1f}x | score {rank_score:.1f}"
                )
            except Exception as exc:
                print(f"  ! Error scanning heavy mover {symbol}: {exc}")
                continue

        movers.sort(key=lambda m: m["rank_score"], reverse=True)
        ranked = movers[:limit]
        print(f"Found {len(ranked)} heavy mover watch candidates (of {len(movers)} qualified)")
        return ranked
    
    def scan_momentum_stocks(
        self,
        limit=10,
        additional_symbols=None,
        bankroll=50.0,
        history_batch: Optional[Dict[str, Any]] = None,
    ):
        """Scan for stocks with strong momentum and volume"""
        signals = []
        symbols_to_scan = self._resolve_symbols_to_scan(additional_symbols, dynamic_limit=20)
        
        print(f"Scanning {len(symbols_to_scan)} stocks for day trading opportunities...")
        print(f"   Criteria: Price ${self.min_price:.1f}-${self.max_price:.1f}, Volume >= {self.min_volume:,}")
        print(f"   Symbols to check: {symbols_to_scan[:10]}...")  # Show first 10 symbols
        if history_batch:
            print(f"   Using shared market batch ({len(history_batch)} histories)")
        
        for symbol in symbols_to_scan:
            print(f"   Checking symbol: {symbol}")
        
        for symbol in symbols_to_scan[:limit]:
            try:
                hist = self._hist_from_batch_or_yf(symbol, history_batch, min_rows=5)
                if hist is None or len(hist) < 5:
                    print(f"  ! {symbol}: Insufficient data")
                    continue
                
                # Current price and volume
                current_price = hist['Close'].iloc[-1]
                current_volume = hist['Volume'].iloc[-1]
                avg_volume = hist['Volume'].mean()
                
                print(f"  Stock {symbol}: ${current_price:.2f} | Vol: {current_volume:,} | Avg: {avg_volume:,}")
                
                if current_price < self.min_price:
                    print(f"    X Price filter failed (${current_price:.2f})")
                    continue
                if self.price_filter_enabled and current_price > self.max_price:
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
                    momentum_score = min(60.0, abs(price_change_5d) * 1000)
                    volume_score = min(25.0, volume_ratio * 5)
                    rsi_score = 10.0 if 30 <= rsi <= 70 else 5.0
                    base_confidence = min(90, max(30, momentum_score + volume_score + rsi_score))
                    confidence_pct = base_confidence / 100.0
                    
                    # Calculate position sizing based on bankroll and confidence
                    position_info = self.calculate_position_size(current_price, bankroll, confidence_pct)
                    
                    sim_pop = min(95, max(55, 50 + volume_ratio * 10 + momentum_score * 0.3))
                    signal = {
                        'symbol': symbol,
                        'action': 'BUY',
                        'entry_price': round(current_price, 2),
                        'target_price': round(current_price * 1.05, 2),  # 5% target
                        'confidence': base_confidence,
                        'simulation_pop': sim_pop,
                        'monte_carlo_sim_score': sim_pop,
                        'pop_from_sim': sim_pop,
                        'assumption_based_simulation': True,
                        'confidence_type': 'heuristic',
                        'news_recency_score': 0.0,
                        'source_quality_score': 0.7,
                        'price_confirmation_score': min(1.0, abs(price_change_5d) * 10),
                        'volume_confirmation_score': min(1.0, volume_ratio / 3),
                        'volume': int(current_volume),
                        'avg_volume': int(avg_volume),
                        'rsi': round(rsi, 2),
                        'price_change_5d': round(price_change_5d * 100, 2),
                        'sector': self.get_sector(symbol),
                        'industry': 'Technology',
                        'market_cap': 0,
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
        """Get market cap from ticker info (slow; avoid on hot path)."""
        try:
            if isinstance(ticker, str):
                return 0
            info = ticker.info
            market_cap = info.get('marketCap', 0)
            return market_cap
        except Exception:
            return 1000000000  # Default $1B

def get_day_trading_scanner(config=None):
    """Get day trading scanner instance"""
    return DayTradingScanner(config)
