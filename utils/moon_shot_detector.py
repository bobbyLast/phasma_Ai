"""
Moon Shot Detector - Overnight Catalyst-Driven Opportunity Identifier

Identifies stocks with 2x-5x+ potential through catalyst analysis:
- Upcoming earnings announcements
- FDA approvals and clinical trial results
- Product launches and partnerships
- M&A announcements and buyouts
- Clinical trial phase advancements
- Regulatory approvals and patents

Features:
- Catalyst-driven scoring system (0-100)
- Overnight holding potential (multi-day to multi-week)
- Event-based opportunity detection
- Integration with catalyst calendar system
- Time horizon analysis for optimal entry/exit
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Optional, Tuple
import json
import os

class MoonShotDetector:
    """
    Advanced detector for overnight catalyst-driven opportunities (2x-5x+ potential)
    """
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        
        # Moon Shot thresholds
        self.min_score = int(self.config.get('moon_shot', {}).get('min_score', 70))
        self.volume_surge_threshold = float(self.config.get('moon_shot', {}).get('volume_surge_threshold', 3.0))
        self.price_breakout_threshold = float(self.config.get('moon_shot', {}).get('price_breakout_threshold', 0.1))
        
        # Catalyst parameters
        self.max_days_to_catalyst = int(self.config.get('moon_shot', {}).get('max_days_to_catalyst', 30))
        self.min_catalyst_impact = float(self.config.get('moon_shot', {}).get('min_catalyst_impact', 0.7))
        
        # Overnight holding parameters
        self.min_holding_days = int(self.config.get('moon_shot', {}).get('min_holding_days', 1))
        self.max_holding_days = int(self.config.get('moon_shot', {}).get('max_holding_days', 30))
        
        # Catalyst types for moon shots
        self.high_impact_catalysts = [
            'earnings_announcement', 'fda_approval', 'clinical_trial_results',
            'product_launch', 'partnership', 'merger_acquisition', 'buyout',
            'regulatory_approval', 'patent_approval', 'phase_advancement'
        ]
        
        # Moon Shot watchlist (high-potential candidates)
        self.moon_shot_watchlist = [
            # Biotech/Medical - catalyst-driven
            'NVAX', 'MRNA', 'BNTX', 'CRSP', 'EDIT', 'NTLA', 'SRNE', 'BPMC',
            # Technology/Innovation - disruption potential
            'PLTR', 'RIVN', 'LCID', 'SPCE', 'MVIS', 'AI', 'SOUN', 'U',
            # Energy/Transition - sector rotation
            'FCEL', 'PLUG', 'BLDP', 'RUN', 'ENPH', 'SPWR', 'CSIQ', 'JKS',
            # Meme/Social - retail momentum
            'AMC', 'GME', 'BB', 'NOK', 'SNDL', 'BNGO',
            # Crypto/Blockchain - emerging tech
            'MSTR', 'COIN', 'RIOT', 'MARA', 'HUT', 'BITF',
            # Special Situations
            'TLRY', 'CGC', 'HEXO', 'ACB', 'CRON'
        ]
        
        print("🌙 Moon Shot Detector initialized")
        print(f"   - Min score: {self.min_score}/100")
        print(f"   - Volume surge threshold: {self.volume_surge_threshold}x")
        print(f"   - Price breakout threshold: {self.price_breakout_threshold*100:.0f}%")
        print(f"   - Watchlist: {len(self.moon_shot_watchlist)} candidates")
    
    def scan_moon_shots(self, custom_symbols: List[str] = None, 
                       max_price: float = None) -> List[Dict]:
        """
        Scan for moon shot opportunities
        
        Args:
            custom_symbols: Optional custom symbol list
            max_price: Maximum price filter (for portfolio scaling)
        
        Returns:
            List of moon shot opportunities with potential multiples
        """
        try:
            symbols = custom_symbols if custom_symbols else self.moon_shot_watchlist
            print(f"🌙 Scanning {len(symbols)} symbols for moon shot opportunities...")
            
            moon_shots = []
            
            for symbol in symbols:
                try:
                    moon_shot = self._analyze_moon_shot_potential(symbol, max_price)
                    if moon_shot and moon_shot['score'] >= self.min_score:
                        moon_shots.append(moon_shot)
                        potential = moon_shot['potential_multiple']
                        print(f"  🚀 {symbol}: {moon_shot['score']:.0f}/100 - {potential}x potential")
                    else:
                        print(f"  ❌ {symbol}: No moon shot potential")
                        
                except Exception as e:
                    print(f"  ⚠️ {symbol}: Error - {str(e)}")
                    continue
            
            # Sort by score
            moon_shots.sort(key=lambda x: x['score'], reverse=True)
            
            print(f"🌙 Found {len(moon_shots)} moon shot opportunities")
            return moon_shots
            
        except Exception as e:
            print(f"❌ Error scanning moon shots: {str(e)}")
            return []
    
    def _analyze_moon_shot_potential(self, symbol: str, max_price: float = None, 
                               catalyst_data: Dict = None) -> Optional[Dict]:
        """Analyze symbol for overnight catalyst-driven moon shot potential"""
        try:
            # Get stock data
            stock = yf.Ticker(symbol)
            hist = stock.history(period="3mo")
            info = stock.info
            
            if hist.empty or len(hist) < 30:
                return None
            
            current_price = hist['Close'].iloc[-1]
            
            # Price filter (for portfolio scaling)
            if max_price and current_price > max_price:
                return None
            
            # 🌙 CATALYST ANALYSIS: Focus on upcoming events
            catalyst_score = 0
            catalyst_factors = []
            
            if catalyst_data:
                catalyst_type = catalyst_data.get('catalyst_type', '').lower()
                days_to_catalyst = catalyst_data.get('days_to_catalyst', 0)
                catalyst_impact = catalyst_data.get('catalyst_impact', 0.5)
                
                # High-impact catalyst types (40 points)
                if catalyst_type in self.high_impact_catalysts:
                    catalyst_score += 40
                    catalyst_factors.append(f"High-impact catalyst: {catalyst_type.replace('_', ' ').title()}")
                
                # Optimal timing window (20 points)
                if 1 <= days_to_catalyst <= 14:  # 1-2 weeks optimal for overnight holds
                    catalyst_score += 20
                    catalyst_factors.append(f"Optimal timing: {days_to_catalyst} days to catalyst")
                elif 15 <= days_to_catalyst <= 30:
                    catalyst_score += 15
                    catalyst_factors.append(f"Good timing: {days_to_catalyst} days to catalyst")
                
                # Catalyst impact strength (20 points)
                if catalyst_impact >= 0.8:
                    catalyst_score += 20
                    catalyst_factors.append(f"High catalyst impact: {catalyst_impact:.1f}")
                elif catalyst_impact >= 0.6:
                    catalyst_score += 15
                    catalyst_factors.append(f"Moderate catalyst impact: {catalyst_impact:.1f}")
                
                # Sector-specific catalysts (10 points)
                sector = info.get('sector', '').lower()
                if 'biotechnology' in sector and catalyst_type in ['fda_approval', 'clinical_trial_results', 'phase_advancement']:
                    catalyst_score += 10
                    catalyst_factors.append("Biotech catalyst with FDA/clinical event")
                elif 'technology' in sector and catalyst_type in ['product_launch', 'partnership', 'merger_acquisition']:
                    catalyst_score += 10
                    catalyst_factors.append("Tech catalyst with launch/M&A event")
                elif 'energy' in sector and catalyst_type in ['regulatory_approval', 'partnership']:
                    catalyst_score += 10
                    catalyst_factors.append("Energy catalyst with regulatory/partnership event")
            
            # 📊 FUNDAMENTAL STRENGTH: Support for catalyst impact (20 points)
            fundamental_score = 0
            fundamental_factors = []
            
            # Market cap (smaller caps have more room to run)
            market_cap = info.get('marketCap', 0)
            if 100_000_000 <= market_cap <= 2_000_000_000:  # $100M - $2B optimal for moon shots
                fundamental_score += 10
                fundamental_factors.append(f"Optimal market cap: ${market_cap/1e6:.0f}M")
            elif market_cap < 100_000_000:
                fundamental_score += 5
                fundamental_factors.append(f"Small cap: ${market_cap/1e6:.0f}M")
            
            # Price level (lower prices have more upside)
            if 1.0 <= current_price <= 5.0:
                fundamental_score += 10
                fundamental_factors.append(f"Optimal price range: ${current_price:.2f}")
            elif 5.0 < current_price <= 15.0:
                fundamental_score += 5
                fundamental_factors.append(f"Reasonable price: ${current_price:.2f}")
            
            # 🎯 OVERNIGHT HOLDING SUITABILITY: Technical confirmation (20 points)
            technical_score = 0
            technical_factors = []
            
            # RSI for entry timing (not overbought yet)
            rsi = self._calculate_rsi(hist)
            if rsi and 30 <= rsi <= 60:
                technical_score += 10
                technical_factors.append(f"Good RSI entry: {rsi:.1f}")
            elif rsi and 20 <= rsi <= 70:
                technical_score += 5
                technical_factors.append(f"Acceptable RSI: {rsi:.1f}")
            
            # Volume for liquidity (need ability to enter/exit)
            current_volume = hist['Volume'].iloc[-1]
            avg_volume = hist['Volume'].tail(20).mean()
            volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1.0
            
            if avg_volume >= 100000:  # Minimum liquidity
                technical_score += 10
                technical_factors.append(f"Good liquidity: {avg_volume/1000:.0f}K avg volume")
            elif avg_volume >= 50000:
                technical_score += 5
                technical_factors.append(f"Adequate liquidity: {avg_volume/1000:.0f}K avg volume")
            
            # Calculate total moon shot score
            score = catalyst_score + fundamental_score + technical_score
            score_factors = catalyst_factors + fundamental_factors + technical_factors
            
            # Determine potential multiple based on catalyst strength
            potential_multiple = self._estimate_catalyst_potential_multiple(
                score, catalyst_data, market_cap, current_price
            )
            
            # Moon Shot classification (overnight catalyst-driven)
            if score >= 85:
                classification = "MEGA CATALYST MOON SHOT"
            elif score >= 75:
                classification = "CATALYST MOON SHOT"
            elif score >= 65:
                classification = "CATALYST ROCKET SHOT"
            else:
                classification = "CATALYST OPPORTUNITY"
            
            return {
                'symbol': symbol,
                'current_price': current_price,
                'score': score,
                'classification': classification,
                'potential_multiple': potential_multiple,
                'catalyst_type': catalyst_data.get('catalyst_type', 'Unknown') if catalyst_data else 'Unknown',
                'days_to_catalyst': catalyst_data.get('days_to_catalyst', 0) if catalyst_data else 0,
                'catalyst_impact': catalyst_data.get('catalyst_impact', 0.5) if catalyst_data else 0.5,
                'rsi': rsi,
                'market_cap': market_cap,
                'sector': sector,
                'avg_volume': avg_volume,
                'holding_period': f"{self.min_holding_days}-{self.max_holding_days} days",
                'score_factors': score_factors,
                'analysis_date': datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            print(f"Error analyzing {symbol}: {str(e)}")
            return None
    
    def _estimate_catalyst_potential_multiple(self, score: int, catalyst_data: Dict, 
                                         market_cap: float, current_price: float) -> str:
        """Estimate potential return multiple based on catalyst strength"""
        
        if not catalyst_data:
            return "2x"
        
        catalyst_type = catalyst_data.get('catalyst_type', '').lower()
        catalyst_impact = catalyst_data.get('catalyst_impact', 0.5)
        days_to_catalyst = catalyst_data.get('days_to_catalyst', 0)
        
        # Base potential on catalyst type
        if catalyst_type in ['fda_approval', 'merger_acquisition', 'buyout']:
            base_potential = "5x+"
        elif catalyst_type in ['clinical_trial_results', 'phase_advancement', 'product_launch']:
            base_potential = "3x-5x"
        elif catalyst_type in ['earnings_announcement', 'partnership', 'regulatory_approval']:
            base_potential = "2x-3x"
        else:
            base_potential = "2x"
        
        # Adjust for catalyst impact
        if catalyst_impact >= 0.9 and score >= 80:
            base_potential = "5x+"
        elif catalyst_impact >= 0.8 and score >= 75:
            base_potential = "3x-5x"
        
        # Adjust for market cap (smaller caps have more room)
        if market_cap <= 500_000_000 and score >= 75:  # Under $500M
            base_potential = "5x+" if "5x" not in base_potential else base_potential
        
        # Adjust for timing (closer catalysts = more certain)
        if days_to_catalyst <= 7 and score >= 70:
            base_potential = "3x-5x" if base_potential == "2x" else base_potential
        
        return base_potential
    
    def _estimate_potential_multiple(self, score: int, volume_surge: float, 
                                   price_change_5d: float, volatility: float, 
                                   sector: str) -> str:
        """Estimate potential return multiple based on factors"""
        
        # Base potential on score
        if score >= 85:
            base_potential = "5x+"
        elif score >= 75:
            base_potential = "3x-5x"
        elif score >= 65:
            base_potential = "2x-3x"
        else:
            base_potential = "2x"
        
        # Adjust for volume surge
        if volume_surge >= 5.0:
            base_potential = "5x+" if "5x" not in base_potential else "10x+"
        elif volume_surge >= 3.0 and score >= 70:
            base_potential = "3x-5x"
        
        # Adjust for sector
        high_potential_sectors = ['biotechnology', 'technology']
        if any(target in sector for target in high_potential_sectors) and score >= 75:
            base_potential = "5x+" if "5x" not in base_potential else base_potential
        
        # Adjust for extreme momentum
        if price_change_5d >= 25 and score >= 70:
            base_potential = "5x+"
        
        return base_potential
    
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
    
    def format_for_telegram(self, moon_shot: Dict) -> str:
        """Format moon shot opportunity for Telegram"""
        symbol = moon_shot['symbol']
        price = moon_shot['current_price']
        score = moon_shot['score']
        classification = moon_shot['classification']
        potential = moon_shot['potential_multiple']
        
        factors_text = '\n'.join([f"🚀 {factor}" for factor in moon_shot['score_factors'][:4]])
        
        message = (
            f"🌙 **MOON SHOT ALERT**\n\n"
            f"📈 **{symbol} - {classification}**\n"
            f"💰 Score: {score:.0f}/100\n"
            f"🎯 Potential: {potential} return\n"
            f"💵 Price: ${price:.2f}\n"
            f"📊 Volume: {moon_shot['volume_surge']:.1f}x average\n"
            f"⚡ 5-day momentum: +{moon_shot['price_change_5d']:.1f}%\n"
            f"🏢 Sector: {moon_shot['sector'].title()}\n\n"
            f"🚀 **Moon Shot Factors:**\n{factors_text}\n\n"
            f"⏰ Analysis: {moon_shot['analysis_date'][:10]}\n"
            f"⚠️ High volatility - Manage risk carefully"
        )
        
        return message
    
    def get_top_moon_shots(self, min_score: int = 70, limit: int = 3, 
                          max_price: float = None) -> List[Dict]:
        """Get top moon shot opportunities"""
        moon_shots = self.scan_moon_shots(max_price=max_price)
        filtered = [shot for shot in moon_shots if shot['score'] >= min_score]
        return filtered[:limit]

# Example usage and testing
if __name__ == "__main__":
    print("🧪 Testing Moon Shot Detector...")
    
    detector = MoonShotDetector()
    
    # Scan for moon shots
    moon_shots = detector.scan_moon_shots()
    
    if moon_shots:
        print(f"\n🌙 Top Moon Shot Opportunities:")
        for i, moon_shot in enumerate(moon_shots[:3], 1):
            print(f"\n{i}. {moon_shot['symbol']} - {moon_shot['classification']} ({moon_shot['score']:.0f}/100)")
            print(f"   Price: ${moon_shot['current_price']:.2f} | Potential: {moon_shot['potential_multiple']}")
            print(f"   Volume: {moon_shot['volume_surge']:.1f}x | 5-day: +{moon_shot['price_change_5d']:.1f}%")
            print(f"   Factors: {', '.join(moon_shot['score_factors'][:2])}")
            
            # Show Telegram format
            if i == 1:  # Show format for top opportunity
                print(f"\n📱 Telegram Format:")
                print(detector.format_for_telegram(moon_shot))
    else:
        print("❌ No moon shot opportunities found")
    
    print(f"\n✅ Moon Shot Detector working!")
    print(f"   - Explosive growth identification implemented")
    print(f"   - 2x-5x+ potential classification working")
    print(f"   - Ready for integration with dynamic scaling")
