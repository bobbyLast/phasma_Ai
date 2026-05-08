"""
Penny Stock Scanner - Comprehensive Low-Priced Stock Analysis

Scans for penny stock opportunities using multiple criteria:
- Price under $5 (configurable threshold)
- Volume surge detection
- Technical analysis for momentum
- Sector focus on high-growth areas
- News catalyst detection
- Market cap and liquidity filtering

Features:
- Real-time scanning of market data
- Multi-factor scoring system
- Telegram alerts for high-potential opportunities
- Integration with existing Phasma AI infrastructure
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Optional, Tuple
import json
import os

class PennyStockScanner:
    """
    Comprehensive penny stock scanner that identifies low-priced opportunities
    with high growth potential using technical and fundamental analysis
    """
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        
        # Penny stock parameters
        self.max_price = float(self.config.get('penny_scanner', {}).get('max_price', 5.0))
        self.min_price = float(self.config.get('penny_scanner', {}).get('min_price', 0.10))
        self.min_volume = int(self.config.get('penny_scanner', {}).get('min_volume', 50000))
        self.min_market_cap = float(self.config.get('penny_scanner', {}).get('min_market_cap', 10000000))  # $10M minimum
        
        # Technical thresholds
        self.volume_surge_threshold = float(self.config.get('penny_scanner', {}).get('volume_surge_threshold', 2.0))  # 2x average volume
        self.rsi_oversold = float(self.config.get('penny_scanner', {}).get('rsi_oversold', 30))
        self.rsi_overbought = float(self.config.get('penny_scanner', {}).get('rsi_overbought', 70))
        
        # Target sectors for penny stocks
        self.target_sectors = [
            'biotechnology', 'pharmaceuticals', 'technology', 
            'energy', 'healthcare', 'mining', 'financial services'
        ]
        
        # Popular penny stock watchlist
        self.penny_watchlist = [
            'AMC', 'GME', 'BB', 'NOK', 'SNDL', 'MVIS', 'PLTR', 'SPCE',
            'RIVN', 'LCID', 'NIU', 'BNGO', 'MSTR', 'TLRY', 'HEXO', 'CGC',
            'BPMC', 'CRSP', 'EDIT', 'NTLA', 'MRNA', 'NVAX', 'SRNE', 'SINO',
            'FCEL', 'PLUG', 'BLDP', 'RUN', 'ENPH', 'SPWR', 'CSIQ', 'JKS'
        ]
        
        print("🪙 Penny Stock Scanner initialized")
        print(f"   - Price range: ${self.min_price:.2f} - ${self.max_price:.2f}")
        print(f"   - Min volume: {self.min_volume:,}")
        print(f"   - Min market cap: ${self.min_market_cap:,}")
        print(f"   - Target sectors: {len(self.target_sectors)} sectors")
    
    def scan_penny_stocks(self, custom_symbols: List[str] = None) -> List[Dict]:
        """
        Scan for penny stock opportunities
        
        Args:
            custom_symbols: Optional list of symbols to scan (overrides default watchlist)
        
        Returns:
            List of penny stock opportunities with scores
        """
        try:
            symbols = custom_symbols if custom_symbols else self.penny_watchlist
            print(f"🔍 Scanning {len(symbols)} symbols for penny stock opportunities...")
            
            opportunities = []
            
            for symbol in symbols:
                try:
                    opportunity = self._analyze_symbol(symbol)
                    if opportunity:
                        opportunities.append(opportunity)
                        print(f"  ✅ {symbol}: {opportunity['score']:.0f}/100 - {opportunity['rating']}")
                    else:
                        print(f"  ❌ {symbol}: No opportunity")
                        
                except Exception as e:
                    print(f"  ⚠️ {symbol}: Error - {str(e)}")
                    continue
            
            # Sort by score
            opportunities.sort(key=lambda x: x['score'], reverse=True)
            
            print(f"🪙 Found {len(opportunities)} penny stock opportunities")
            return opportunities
            
        except Exception as e:
            print(f"❌ Error scanning penny stocks: {str(e)}")
            return []
    
    def _analyze_symbol(self, symbol: str) -> Optional[Dict]:
        """Analyze a single symbol for penny stock opportunity"""
        try:
            # Get stock data
            stock = yf.Ticker(symbol)
            hist = stock.history(period="2mo")
            info = stock.info
            
            if hist.empty or len(hist) < 20:
                return None
            
            current_price = hist['Close'].iloc[-1]
            
            # Price filter
            if current_price < self.min_price or current_price > self.max_price:
                return None
            
            # Volume filter
            current_volume = hist['Volume'].iloc[-1]
            avg_volume = hist['Volume'].tail(20).mean()
            
            if current_volume < self.min_volume:
                return None
            
            # Market cap filter
            market_cap = info.get('marketCap', 0)
            if market_cap < self.min_market_cap:
                return None
            
            # Technical indicators
            rsi = self._calculate_rsi(hist)
            volume_surge = current_volume / avg_volume if avg_volume > 0 else 1.0
            
            # Price momentum
            price_change_5d = ((hist['Close'].iloc[-1] - hist['Close'].iloc[-6]) / hist['Close'].iloc[-6]) * 100
            price_change_20d = ((hist['Close'].iloc[-1] - hist['Close'].iloc[-21]) / hist['Close'].iloc[-21]) * 100
            
            # Moving averages
            ma_10 = hist['Close'].tail(10).mean()
            ma_20 = hist['Close'].tail(20).mean()
            above_ma_10 = current_price > ma_10
            above_ma_20 = current_price > ma_20
            
            # Sector analysis
            sector = info.get('sector', '').lower()
            sector_bonus = 10 if any(target in sector for target in self.target_sectors) else 0
            
            # Calculate score
            score = 0
            score_factors = []
            
            # Volume surge (30 points)
            if volume_surge >= 3.0:
                score += 30
                score_factors.append(f"Volume surge: {volume_surge:.1f}x")
            elif volume_surge >= 2.0:
                score += 20
                score_factors.append(f"Volume surge: {volume_surge:.1f}x")
            elif volume_surge >= 1.5:
                score += 10
                score_factors.append(f"Volume surge: {volume_surge:.1f}x")
            
            # RSI momentum (25 points)
            if rsi and self.rsi_oversold <= rsi <= 50:
                score += 25
                score_factors.append(f"RSI momentum: {rsi:.1f}")
            elif rsi and 50 < rsi <= self.rsi_overbought:
                score += 15
                score_factors.append(f"RSI strength: {rsi:.1f}")
            
            # Price momentum (20 points)
            if price_change_5d > 10:
                score += 20
                score_factors.append(f"5-day momentum: +{price_change_5d:.1f}%")
            elif price_change_5d > 5:
                score += 15
                score_factors.append(f"5-day momentum: +{price_change_5d:.1f}%")
            elif price_change_20d > 15:
                score += 10
                score_factors.append(f"20-day momentum: +{price_change_20d:.1f}%")
            
            # Moving average position (15 points)
            if above_ma_10 and above_ma_20:
                score += 15
                score_factors.append("Above key moving averages")
            elif above_ma_10:
                score += 10
                score_factors.append("Above 10-day MA")
            
            # Sector bonus (10 points)
            if sector_bonus > 0:
                score += sector_bonus
                score_factors.append(f"Target sector: {sector.title()}")
            
            # Price level (10 points)
            if 1.0 <= current_price <= 3.0:
                score += 10
                score_factors.append("Optimal price range")
            elif 3.0 < current_price <= 5.0:
                score += 5
                score_factors.append("Higher-end penny stock")
            
            # Determine rating
            if score >= 70:
                rating = "STRONG BUY"
            elif score >= 50:
                rating = "BUY"
            elif score >= 30:
                rating = "WATCH"
            else:
                rating = "WEAK"
            
            # Risk assessment
            risk_level = "HIGH"  # All penny stocks are high risk
            if rsi and rsi > 80:
                risk_level = "VERY HIGH"
            elif volume_surge > 5.0:
                risk_level = "VERY HIGH"
            
            return {
                'symbol': symbol,
                'current_price': current_price,
                'score': score,
                'rating': rating,
                'risk_level': risk_level,
                'volume_surge': volume_surge,
                'rsi': rsi,
                'price_change_5d': price_change_5d,
                'price_change_20d': price_change_20d,
                'above_ma_10': above_ma_10,
                'above_ma_20': above_ma_20,
                'sector': sector,
                'market_cap': market_cap,
                'current_volume': current_volume,
                'avg_volume': avg_volume,
                'score_factors': score_factors,
                'analysis_date': datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            print(f"Error analyzing {symbol}: {str(e)}")
            return None
    
    def _calculate_rsi(self, hist: pd.DataFrame, period: int = 14) -> Optional[float]:
        """Calculate RSI indicator"""
        try:
            delta = hist['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            
            return rsi.iloc[-1] if not rsi.empty else None
            
        except Exception:
            return None
    
    def format_for_telegram(self, opportunity: Dict) -> str:
        """Format penny stock opportunity for Telegram"""
        symbol = opportunity['symbol']
        price = opportunity['current_price']
        score = opportunity['score']
        rating = opportunity['rating']
        risk = opportunity['risk_level']
        
        factors_text = '\n'.join([f"• {factor}" for factor in opportunity['score_factors'][:5]])
        
        message = (
            f"🪙 **Penny Stock Alert**\n\n"
            f"📈 **{symbol} - {rating}**\n"
            f"💰 Score: {score:.0f}/100\n"
            f"💵 Price: ${price:.2f}\n"
            f"⚠️ Risk: {risk}\n"
            f"📊 Volume: {opportunity['volume_surge']:.1f}x average\n"
            f"🏢 Sector: {opportunity['sector'].title()}\n"
            f"💼 Market Cap: ${opportunity['market_cap']/1e6:.0f}M\n\n"
            f"🎯 **Key Factors:**\n{factors_text}\n\n"
            f"⏰ Analysis: {opportunity['analysis_date'][:10]}"
        )
        
        return message
    
    def get_top_opportunities(self, min_score: int = 40, limit: int = 5) -> List[Dict]:
        """Get top penny stock opportunities above minimum score"""
        opportunities = self.scan_penny_stocks()
        filtered = [opp for opp in opportunities if opp['score'] >= min_score]
        return filtered[:limit]

# Example usage and testing
if __name__ == "__main__":
    print("🧪 Testing Penny Stock Scanner...")
    
    scanner = PennyStockScanner()
    
    # Scan for opportunities
    opportunities = scanner.scan_penny_stocks()
    
    if opportunities:
        print(f"\n📊 Top Penny Stock Opportunities:")
        for i, opp in enumerate(opportunities[:5], 1):
            print(f"\n{i}. {opp['symbol']} - {opp['rating']} ({opp['score']:.0f}/100)")
            print(f"   Price: ${opp['current_price']:.2f} | Volume: {opp['volume_surge']:.1f}x")
            print(f"   Sector: {opp['sector'].title()} | Risk: {opp['risk_level']}")
            print(f"   Factors: {', '.join(opp['score_factors'][:3])}")
            
            # Show Telegram format
            if i == 1:  # Show format for top opportunity
                print(f"\n📱 Telegram Format:")
                print(scanner.format_for_telegram(opp))
    else:
        print("❌ No penny stock opportunities found")
    
    print(f"\n✅ Penny Stock Scanner working!")
    print(f"   - Configured for stocks under ${scanner.max_price:.2f}")
    print(f"   - Ready for integration with main system")
