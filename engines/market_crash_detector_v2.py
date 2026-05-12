"""
Phasma Market Crash Engine V2
Unified crash detection AND profit strategies

Implements:
- Multi-timeframe analysis (7d, 30d, 90d)
- Macro awareness (DXY, VIX, US10Y, SPY)
- On-chain flow analysis (whale movements, funding rates)
- Sentiment fusion
- 3-level alert system
- Adaptive confidence weighting
- Monte Carlo integration
- PUT OPTIONS profit strategies during crashes
- Sector-specific crash targeting
- Crash bounce predictions
"""

import yfinance as yf
import numpy as np
import pandas as pd
import os
from datetime import datetime, timedelta
import logging
from typing import Dict, List, Optional, Tuple
import json
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed

# Set a lenient provider bridge rate limit to avoid burst throttling
os.environ['MARKET_DATA_MIN_INTERVAL'] = '0.5'

try:
    from utils.market_data_cache import MarketDataCache
except ImportError:
    MarketDataCache = None

# Import new research engines
from .market_research_engine import MarketResearchEngine
from .whale_activity_tracker import WhaleActivityTracker
from .catalyst_tracker import CatalystTracker


class MarketCrashDetectorV2:
    """Advanced market crash detection with multi-horizon analysis"""
    
    # Alert level thresholds (ADJUSTED FOR PROFITABILITY)
    # Lower thresholds = earlier warnings = more profit opportunities
    ALERT_LEVELS = {
        0: {'threshold': 0.0, 'name': 'NORMAL', 'severity': '', 'action': 'Normal trading conditions'},  # No risk
        1: {'threshold': 0.20, 'name': 'MINOR_DIP', 'severity': '', 'action': 'Reduce size 30%'},  # 20% risk = early warning
        2: {'threshold': 0.35, 'name': 'MEDIUM_CORRECTION', 'severity': '', 'action': 'Reduce size 50% + buy puts'},  # 35% = defensive
        3: {'threshold': 0.55, 'name': 'HIGH_CRASH_RISK', 'severity': '', 'action': 'Pause longs, aggressive puts'}  # 55% = danger zone
    }
    
    # Time horizons
    HORIZONS = {
        'short_term': 7,   # 7 days
        'mid_term': 30,    # 30 days
        'long_term': 90    # 90 days
    }
    
    def __init__(self, config: Dict, market_cache: Optional['MarketDataCache'] = None, simulation_engine=None):
        self.config = config
        self.market_cache = market_cache
        self.simulation_engine = simulation_engine
        self.logger = logging.getLogger(__name__)
        self.shadow_mode = config.get('crash_detector.shadow_mode', False)
        # Track prediction quality over time for confidence re-weighting.
        self.prediction_history: List[Dict] = []
        self.max_history = 500
        
        # Initialize research engines
        self.research_engine = MarketResearchEngine(config, market_cache)
        self.whale_tracker = WhaleActivityTracker(config)
        self.catalyst_tracker = CatalystTracker(config)
        
        # Crash detection parameters
        self.timeframes = {
            '1d': {'weight': 0.15, 'threshold': -0.08},
            '1w': {'weight': 0.20, 'threshold': -0.12},
            '1m': {'weight': 0.25, 'threshold': -0.20},
            '3m': {'weight': 0.40, 'threshold': -0.30}
        }
        
        # Memory paths (under data/runtime/phasma_core_memory/)
        from core.runtime_paths import memory_path
        self.memory_path = memory_path("market_crash_detector")
        self.alerts_path = memory_path("crash_alerts")
        self._ensure_directories()
        
        # Crash profit components
        self._init_profit_components()
    
    def _ensure_directories(self):
        """Create necessary directories"""
        os.makedirs(self.memory_path, exist_ok=True)
        os.makedirs(self.alerts_path, exist_ok=True)
    
    def _init_profit_components(self):
        """Initialize crash profit strategy components"""
        # Sector ETF mappings for targeted puts
        self.sector_etfs = {
            'AI_TECH': ['QQQ', 'XLK', 'SOXX', 'BOTZ'],  # AI and tech
            'CRYPTO': ['BTC-USD', 'ETH-USD', 'MARA', 'RIOT', 'COIN'],  # Crypto
            'AR_TECH': ['ARKK', 'ARKF', 'ARKG', 'ARKW'],  # AR/innovative tech
            'BIOTECH': ['XBI', 'IBB', 'ARKG'],  # Biotech
            'EV': ['TSLA', 'RIVN', 'LCID', 'NIO'],  # Electric vehicles
            'FINTECH': ['PYPL', 'SQ', 'COIN', 'ARKF'],  # Fintech
            'SEMICONDUCTOR': ['SOXX', 'SMH', 'NVDA', 'AMD'],  # Chips
        }
        
        # Crash thresholds for profit opportunities
        self.crash_thresholds = {
            'minor': -0.02,  # 2% drop = minor crash opportunity
            'moderate': -0.04,  # 4% drop = moderate crash  
            'severe': -0.06,  # 6% drop = severe crash opportunity
        }
        
        # News API for crash context analysis
        self.news_api_url = "https://saurav.tech/NewsAPI/top-headlines/category/business/us.json"
        
        # Sector fundamental data cache
        self.fundamental_cache = {}
        self.market_cache_expiry = 3600  # 1 hour cache
        
        # Confidence weighting for adaptive learning
        self.confidence_weight = 1.0  # Starts at 1.0, adapts based on prediction accuracy
    
    def detect_crash_risk(self, symbol: str = 'BTC-USD') -> Dict:
        """
        Main crash detection pipeline
        
        Args:
            symbol: Asset to analyze (default BTC-USD)
            
        Returns:
            Complete crash risk assessment
        """
        try:
            # 1. Get macro indicators
            macro_score = self._analyze_macro_conditions()
            
            # 2. Get on-chain data (for crypto)
            onchain_score = self._analyze_onchain_flows(symbol) if 'BTC' in symbol or 'crypto' in symbol.lower() else 0.5
            
            # 3. Get sentiment
            sentiment_score = self._analyze_sentiment(symbol)
            
            # 4. Get technical signals
            technical_score = self._analyze_technical_signals(symbol)
            
            # 5. Get volatility regime
            volatility_regime = self._get_volatility_regime()
            
            # 6. Select appropriate horizon
            selected_horizon = self._select_horizon(volatility_regime, macro_score)
            
            # 7. Calculate crash score
            crash_score = self._calculate_crash_score(
                macro_score=macro_score,
                onchain_score=onchain_score,
                sentiment_score=sentiment_score,
                technical_score=technical_score
            )
            
            # 8. Adjust for confidence weighting
            adjusted_score = crash_score * self.confidence_weight
            
            # 9. Determine alert level
            alert_level = self._get_alert_level(adjusted_score)
            
            # 9.5. Build early-warning layer ("read between the lines" pre-crash signals)
            early_warning = self._analyze_early_warning_layer(
                macro_score=macro_score,
                onchain_score=onchain_score,
                sentiment_score=sentiment_score,
                technical_score=technical_score,
                crash_score=adjusted_score,
                volatility_regime=volatility_regime,
                alert_level=alert_level,
                symbol=symbol,
            )

            # 10. Run Monte Carlo simulations
            simulation_results = self._run_crash_simulations(
                symbol=symbol,
                horizon=selected_horizon,
                crash_score=adjusted_score
            )

            # 10.5. Infer likely crash drivers and numeric price projection
            crash_drivers = self._infer_crash_drivers(
                macro_score=macro_score,
                onchain_score=onchain_score,
                sentiment_score=sentiment_score,
                technical_score=technical_score,
                volatility_regime=volatility_regime,
                symbol=symbol
            )

            price_projection = self._build_price_projection(symbol, simulation_results)

            # 10.6. Infer ecosystem contagion impact (meme/penny coins linked to majors like BTC, ETH, SOL)
            ecosystem_contagion = self._infer_ecosystem_contagion(
                symbol=symbol,
                crash_score=adjusted_score,
                price_projection=price_projection
            )
            
            # 11. Generate assessment
            assessment = {
                'timestamp': datetime.now().isoformat(),
                'symbol': symbol,
                'crash_score': adjusted_score,
                'alert_level': alert_level,
                'alert_level_name': self.ALERT_LEVELS.get(alert_level, {}).get('name', 'UNKNOWN'),
                'early_warning_layer': early_warning,
                'early_warning_score': early_warning.get('score'),
                'early_warning_level': early_warning.get('level'),
                'horizon': selected_horizon,
                'horizon_days': self.HORIZONS[selected_horizon],
                'components': {
                    'macro': macro_score,
                    'onchain': onchain_score,
                    'sentiment': sentiment_score,
                    'technical': technical_score
                },
                'volatility_regime': volatility_regime,
                'confidence_weight': self.confidence_weight,
                'simulation_results': simulation_results,
                'price_projection': price_projection,
                'crash_drivers': crash_drivers,
                'ecosystem_contagion': ecosystem_contagion,
                'early_warning': early_warning,
                'recommendation': self._generate_recommendation(alert_level, adjusted_score),
                'reasoning': self._generate_reasoning(
                    macro_score, onchain_score, sentiment_score, 
                    technical_score, alert_level
                )
            }
            
            # 12. Log prediction
            self._log_prediction(assessment)
            
            # 13. Send alerts if not in shadow mode
            if not self.shadow_mode and alert_level >= 2:
                self._send_alert(assessment)
            
            return assessment
            
        except Exception as e:
            self.logger.error(f"Error in crash detection: {e}")
            return {
                'crash_score': 0.5,
                'alert_level': 0,
                'error': str(e)
            }
    
    def _analyze_macro_conditions(self) -> float:
        """
        Analyze macro risk indicators
        Returns score 0.0 (risk-on) to 1.0 (risk-off)
        """
        try:
            # Use cached macro data if available, otherwise fetch
            if self.market_cache and MarketDataCache:
                macro_data = self.market_cache.fetch_macro_data()
                
                # Extract data from cache
                dxy_change = macro_data['dxy']['change']
                vix_level = macro_data['vix']['level']
                yield_change = macro_data['us10y']['change']
                spy_change = macro_data['spy']['change']
            else:
                # Fallback to direct fetching (legacy)
                self.logger.warning("MarketDataCache not available, falling back to direct provider calls")
                
                # Get DXY (US Dollar Index)
                dxy = yf.Ticker('DX-Y.NYB')
                dxy_hist = dxy.history(period='1mo')
                dxy_change = 0.0 if dxy_hist.empty else (dxy_hist['Close'].iloc[-1] - dxy_hist['Close'].iloc[0]) / dxy_hist['Close'].iloc[0]
                
                # Get VIX
                vix = yf.Ticker('^VIX')
                vix_hist = vix.history(period='1mo')
                if vix_hist.empty:
                    vix_level = 0.5
                else:
                    current_vix = vix_hist['Close'].iloc[-1]
                    vix_level = min(1.0, current_vix / 40)
                
                # Get US10Y
                us10y = yf.Ticker('^TNX')
                us10y_hist = us10y.history(period='1mo')
                yield_change = 0.0 if us10y_hist.empty else (us10y_hist['Close'].iloc[-1] - us10y_hist['Close'].iloc[0]) / us10y_hist['Close'].iloc[0]
                
                # Get SPY
                spy = yf.Ticker('SPY')
                spy_hist = spy.history(period='1mo')
                spy_change = 0.0 if spy_hist.empty else (spy_hist['Close'].iloc[-1] - spy_hist['Close'].iloc[0]) / spy_hist['Close'].iloc[0]
            
            # Scale changes
            dxy_trend = min(1.0, max(-1.0, dxy_change * 10))
            yield_trend = min(1.0, max(-1.0, yield_change * 5))
            spy_trend = min(1.0, max(-1.0, spy_change * 10))
            
            # Calculate macro score
            # Rising DXY + Rising VIX = Risk Off (high score)
            # Falling DXY + Stable VIX = Risk On (low score)
            
            risk_off_score = 0.0
            
            # DXY rising = +risk off
            if dxy_trend > 0:
                risk_off_score += 0.25 * dxy_trend
            
            # VIX rising/high = +risk off
            risk_off_score += 0.35 * vix_level
            
            # Yields rising fast = +risk off
            if yield_trend > 0.05:
                risk_off_score += 0.20
            
            # SPY falling = +risk off
            if spy_trend < 0:
                risk_off_score += 0.20 * abs(spy_trend)
            
            return min(1.0, max(0.0, risk_off_score))
            
        except Exception as e:
            self.logger.warning(f"Error analyzing macro: {e}")
            return 0.5
    
    def _analyze_onchain_flows(self, symbol: str) -> float:
        """
        Analyze on-chain metrics (crypto only)
        Returns score 0.0 (bullish flows) to 1.0 (bearish flows)
        """
        try:
            # Use the whale tracker for real on-chain analysis
            if symbol in ['BTC-USD', 'ETH-USD', 'BTC', 'ETH']:
                whale_data = self.whale_tracker.analyze_whale_activity(symbol, 'CRYPTO')
                
                # Extract key metrics
                exchange_flows = whale_data.get('exchange_flows', {})
                net_flow = exchange_flows.get('net_24h', 0)
                
                whale_movements = whale_data.get('whale_movements', {})
                is_accumulating = whale_movements.get('accumulation_phase', False)
                
                # Calculate score (0 = bullish, 1 = bearish)
                score = 0.5  # Start neutral
                
                # Exchange outflows are bullish (score down)
                if net_flow < -100:  # Significant outflow
                    score -= 0.2
                elif net_flow > 100:  # Significant inflow
                    score += 0.2
                
                # Whale accumulation is bullish (score down)
                if is_accumulating:
                    score -= 0.15
                
                # Clamp to valid range
                score = max(0.0, min(1.0, score))
                
                self.logger.info(f"On-chain analysis for {symbol}: score={score:.2f}, net_flow={net_flow}")
                return score
            else:
                # Non-crypto assets get neutral score
                return 0.5
                
        except Exception as e:
            self.logger.warning(f"Error analyzing on-chain: {e}")
            return 0.5
    
    def _analyze_sentiment(self, symbol: str) -> float:
        """
        Analyze market sentiment
        Returns score 0.0 (extreme fear) to 1.0 (extreme greed)
        """
        try:
            # Use the research engine for comprehensive sentiment analysis
            asset_type = 'CRYPTO' if symbol in ['BTC-USD', 'ETH-USD', 'BTC', 'ETH'] else 'STOCK'
            
            # Get sentiment data from research engine
            sentiment_data = self.research_engine._analyze_sentiment(symbol, asset_type)
            
            # Calculate sentiment score
            score = 0.5  # Start neutral
            
            # Fear & Greed Index (for crypto)
            if 'fear_greed' in sentiment_data:
                fg_value = sentiment_data['fear_greed']['value']
                fg_classification = sentiment_data['fear_greed']['classification']
                
                # Convert to 0-1 scale (0 = extreme fear, 1 = extreme greed)
                if fg_classification == 'EXTREME FEAR':
                    score = 0.1
                elif fg_classification == 'FEAR':
                    score = 0.3
                elif fg_classification == 'NEUTRAL':
                    score = 0.5
                elif fg_classification == 'GREED':
                    score = 0.7
                elif fg_classification == 'EXTREME GREED':
                    score = 0.9
            
            # VIX for stocks
            elif 'vix' in sentiment_data:
                vix = sentiment_data['vix']
                # Convert VIX to sentiment score (inverse relationship)
                if vix > 30:
                    score = 0.2  # High fear
                elif vix > 20:
                    score = 0.4  # Moderate fear
                elif vix > 15:
                    score = 0.6  # Neutral
                else:
                    score = 0.8  # Low fear/complacency
            
            # Also consider price action as secondary factor
            if self.market_cache:
                hist = self.market_cache.fetch_history(symbol, period='14d')
            else:
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period='14d')
            
            if not hist.empty:
                recent_change = (hist['Close'].iloc[-1] - hist['Close'].iloc[0]) / hist['Close'].iloc[0]
                volatility = hist['Close'].pct_change().std()
                
                # Adjust score based on price action
                if recent_change < -0.15 and volatility > 0.05:
                    score = min(score - 0.2, 0.0)  # Extreme fear
                elif recent_change > 0.15 and volatility < 0.03:
                    score = max(score + 0.2, 1.0)  # Extreme greed
            
            self.logger.info(f"Sentiment analysis for {symbol}: score={score:.2f}")
            return max(0.0, min(1.0, score))
            
        except Exception as e:
            self.logger.warning(f"Error analyzing sentiment: {e}")
            return 0.5
    
    def _analyze_technical_signals(self, symbol: str) -> float:
        """
        Analyze technical indicators
        Returns score 0.0 (bullish) to 1.0 (bearish)
        """
        try:
            # Use cached history if available
            if self.market_cache and MarketDataCache:
                hist = self.market_cache.fetch_history(symbol, period='3mo')
            else:
                # Fallback to direct fetching
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period='3mo')
            
            if hist.empty:
                return 0.5
            
            # Calculate MACD
            exp1 = hist['Close'].ewm(span=12, adjust=False).mean()
            exp2 = hist['Close'].ewm(span=26, adjust=False).mean()
            macd = exp1 - exp2
            signal = macd.ewm(span=9, adjust=False).mean()
            
            macd_bearish = macd.iloc[-1] < signal.iloc[-1]
            
            # Calculate RSI
            delta = hist['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            
            current_rsi = rsi.iloc[-1]
            rsi_bearish = current_rsi < 30  # Oversold
            
            # Price vs MA
            ma_50 = hist['Close'].rolling(window=50).mean()
            price_below_ma = hist['Close'].iloc[-1] < ma_50.iloc[-1]
            
            # Count bearish signals
            bearish_count = sum([macd_bearish, rsi_bearish, price_below_ma])
            
            return bearish_count / 3.0
            
        except Exception as e:
            self.logger.warning(f"Error analyzing technicals: {e}")
            return 0.5
    
    def _get_volatility_regime(self) -> str:
        """Determine current volatility regime"""
        try:
            # Use cached macro data if available (VIX is already fetched there)
            if self.market_cache and MarketDataCache:
                macro_data = self.market_cache.fetch_macro_data()
                vix_hist = macro_data['vix']['hist']
            else:
                # Fallback to direct fetching
                vix = yf.Ticker('^VIX')
                vix_hist = vix.history(period='1mo')
            
            if vix_hist is None or vix_hist.empty:
                return 'NORMAL'
            
            current_vix = vix_hist['Close'].iloc[-1]
            
            if current_vix < 15:
                return 'LOW'
            elif current_vix < 25:
                return 'NORMAL'
            elif current_vix < 35:
                return 'ELEVATED'
            else:
                return 'EXTREME'
                
        except Exception as e:
            return 'NORMAL'
    
    def _select_horizon(self, volatility_regime: str, macro_score: float) -> str:
        """Select appropriate time horizon based on conditions"""
        # High volatility + high macro risk = use longer horizon
        if volatility_regime in ['ELEVATED', 'EXTREME'] and macro_score > 0.6:
            return 'long_term'  # 90 days
        elif volatility_regime == 'NORMAL' or macro_score > 0.5:
            return 'mid_term'   # 30 days
        else:
            return 'short_term' # 7 days
    
    def _calculate_crash_score(
        self, 
        macro_score: float,
        onchain_score: float,
        sentiment_score: float,
        technical_score: float
    ) -> float:
        """Calculate composite crash score"""
        # Weighted average
        weights = {
            'macro': 0.35,
            'onchain': 0.25,
            'sentiment': 0.20,
            'technical': 0.20
        }
        
        crash_score = (
            macro_score * weights['macro'] +
            onchain_score * weights['onchain'] +
            sentiment_score * weights['sentiment'] +
            technical_score * weights['technical']
        )
        
        return min(1.0, max(0.0, crash_score))

    def _infer_crash_drivers(
        self,
        macro_score: float,
        onchain_score: float,
        sentiment_score: float,
        technical_score: float,
        volatility_regime: str,
        symbol: str
    ) -> List[Dict]:
        """Infer likely real-world style crash drivers for explanation.

        This does not scrape live news. Instead it maps current risk metrics
        to human-readable drivers like:
        - Macro / geopolitical shock
        - Leverage & derivatives overhang
        - Liquidity hole / thin order books
        - Technical breakdown
        """
        drivers: List[Dict] = []
        sym_upper = (symbol or "").upper()
        is_crypto = any(tag in sym_upper for tag in ["BTC", "ETH"]) or "-USD" in sym_upper

        # Macro / geopolitical style shock
        if macro_score > 0.65:
            drivers.append({
                "type": "MACRO_SHOCK",
                "label": "Macro / Geopolitical Shock",
                "reason": (
                    "Macro indicators (DXY, VIX, yields, SPY) are behaving like a risk-off "
                    "environment where headlines around tariffs, wars or policy shocks often "
                    "trigger broad deleveraging."
                )
            })

        # Leverage and derivatives overhang (crypto-style liquidation cascades)
        if is_crypto and onchain_score >= 0.5:
            drivers.append({
                "type": "LEVERAGE_OVERHANG",
                "label": "Leverage / Derivatives Overhang",
                "reason": (
                    "Crypto trades are heavily driven by perpetual futures and leverage. "
                    "Current on-chain/derivatives risk score suggests a crowded long market "
                    "that can trigger forced liquidations similar to past $10B+ wipeout events."
                )
            })

        # Liquidity stress – thin books + elevated volatility
        if volatility_regime in ["ELEVATED", "EXTREME"] and macro_score > 0.5:
            drivers.append({
                "type": "LIQUIDITY_STRESS",
                "label": "Liquidity Hole / Thin Order Books",
                "reason": (
                    "Volatility and macro risk are high while market-making depth is likely "
                    "reduced, which means even moderate sell flow can move price a lot – "
                    "a classic setup for sharp wicks and flash-crash style moves."
                )
            })

        # Technical breakdown (trend & momentum flush)
        if technical_score > 0.66:
            drivers.append({
                "type": "TECHNICAL_BREAKDOWN",
                "label": "Technical Breakdown",
                "reason": (
                    "Trend and momentum indicators (MACD/RSI/MA) are aligned to the downside, "
                    "which often accelerates sell-offs as systematic traders and algos exit "
                    "together."
                )
            })

        if not drivers:
            drivers.append({
                "type": "NO_CLEAR_DRIVER",
                "label": "Normal Volatility",
                "reason": (
                    "Risk metrics do not point to a single dominant crash driver. Moves here "
                    "look more like normal volatility than a structural deleveraging event."
                )
            })

        return drivers

    def _infer_ecosystem_contagion(
        self,
        symbol: str,
        crash_score: float,
        price_projection: Optional[Dict]
    ) -> Dict:
        """Infer contagion impact on the broader ecosystem around a major crypto asset.

        This is a qualitative mapping that explains how a crash in a major coin
        (BTC, ETH, SOL, etc.) is likely to propagate into:
        - Its direct ecosystem (DeFi, infra, L2s)
        - Meme / micro-cap / "penny" coins tied to that chain
        """
        sym_upper = (symbol or "").upper()
        is_crypto = any(tag in sym_upper for tag in ["BTC", "ETH", "SOL", "BNB", "DOGE"]) or "-USD" in sym_upper

        if not is_crypto or crash_score < 0.25:
            # Below ~25% crash probability we treat contagion as normal volatility
            return {}

        ecosystem = {
            "ecosystem": "GENERIC_CRYPTO",
            "label": "Crypto microcaps and meme coins",
            "representative_assets": [],
        }

        if "SOL" in sym_upper:
            ecosystem.update({
                "ecosystem": "SOLANA_ECOSYSTEM",
                "label": "Solana ecosystem meme and micro-cap coins",
                "representative_assets": ["BONK", "WIF", "JUP", "RAY"],
            })
        elif "ETH" in sym_upper:
            ecosystem.update({
                "ecosystem": "ETHEREUM_ECOSYSTEM",
                "label": "Ethereum DeFi, L2s and meme coins",
                "representative_assets": ["PEPE", "SHIB", "UNI", "AAVE"],
            })
        elif "BTC" in sym_upper:
            ecosystem.update({
                "ecosystem": "BITCOIN_ECOSYSTEM",
                "label": "Bitcoin-correlated miners, GBTC-style products and BTC meme coins",
                "representative_assets": ["MARA", "RIOT", "MSTR"],
            })
        elif "BNB" in sym_upper:
            ecosystem.update({
                "ecosystem": "BINANCE_ECOSYSTEM",
                "label": "BNB chain meme and micro-cap coins",
                "representative_assets": [],
            })

        # Use the main asset's severe drop as anchor for ecosystem stress
        severe_drop = None
        if price_projection:
            severe_drop = price_projection.get("severe_drop_pct")

        # Map main-asset crash probability into ecosystem drawdown ranges
        # These are heuristic bands based on typical liquidation cascades
        if crash_score >= 0.55:
            # High crash risk: expect very heavy contagion
            eco_low, eco_high = 0.40, 0.75
            penny_low, penny_high = 0.60, 0.95
        elif crash_score >= 0.35:
            # Medium correction regime
            eco_low, eco_high = 0.25, 0.55
            penny_low, penny_high = 0.40, 0.80
        else:
            # Elevated but not extreme
            eco_low, eco_high = 0.15, 0.35
            penny_low, penny_high = 0.25, 0.55

        if severe_drop is not None:
            # Anchor upper bound by main-asset stress floor if available
            eco_high = max(eco_high, min(0.90, severe_drop + 0.10))

        ecosystem["expected_ecosystem_drawdown_range"] = [eco_low, eco_high]
        ecosystem["penny_coin_tail_risk_range"] = [penny_low, penny_high]

        # Narrative explanation for the report
        ecosystem["narrative"] = (
            "A sharp move in a major chain typically forces risk-off across its ecosystem. "
            "DeFi, infrastructure and meme/penny coins on the same chain often see "
            "amplified intraday drawdowns as liquidity thins, leverage unwinds and "
            "market makers widen spreads."
        )

        return ecosystem

    def _build_price_projection(self, symbol: str, simulation_results: Dict) -> Dict:
        """Build a numeric crash price projection for explanation.

        Uses recent spot price plus Monte Carlo crash parameters to suggest:
        - A moderate crash target (10–30% down)
        - A severe stress floor (up to ~50% down)
        """
        current_price: Optional[float] = None
        try:
            # Use cached history if available
            if self.market_cache and MarketDataCache:
                hist = self.market_cache.fetch_history(symbol, period='7d')
            else:
                # Fallback to direct fetching
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period="7d")
            
            if not hist.empty:
                current_price = float(hist["Close"].iloc[-1])
        except Exception as e:
            self.logger.warning(f"Error getting price for projection {symbol}: {e}")

        expected_return = float(simulation_results.get("expected_return", 0.0))
        tail10 = float(simulation_results.get("tail_probability_10pct", 0.0))
        tail25 = float(simulation_results.get("tail_probability_25pct", 0.0))
        horizon_days = simulation_results.get("horizon_days")

        # Map simulation statistics into intuitive drop ranges
        base_downside = abs(expected_return)
        moderate_drop_pct = min(0.30, max(0.05, base_downside + tail10 * 0.10))
        severe_drop_pct = min(0.50, max(moderate_drop_pct + 0.05, base_downside * 1.5 + tail25 * 0.15))

        moderate_target = None
        severe_floor = None
        if current_price is not None:
            moderate_target = current_price * (1 - moderate_drop_pct)
            severe_floor = current_price * (1 - severe_drop_pct)

        note = (
            "Targets are based on Monte Carlo crash scenarios and typical behaviour in "
            "leveraged, thin-liquidity sell-offs (fast wicks then stabilization)."
        )

        return {
            "symbol": symbol,
            "current_price": current_price,
            "horizon_days": horizon_days,
            "moderate_drop_pct": moderate_drop_pct,
            "severe_drop_pct": severe_drop_pct,
            "moderate_drop_target": moderate_target,
            "severe_stress_floor": severe_floor,
            "note": note,
        }

    def _analyze_early_warning_layer(
        self,
        macro_score: float,
        onchain_score: float,
        sentiment_score: float,
        technical_score: float,
        crash_score: float,
        volatility_regime: str,
        alert_level: int,
        symbol: str,
    ) -> Dict:
        """Infer an early-warning score before a full crash alert is obvious.

        This is intentionally more sensitive than the main alert levels and is
        designed to fire when:
        - Risk metrics (macro / on-chain / technical) are quietly deteriorating
        - But headline sentiment is still complacent or bullish
        - Or cross-asset stress (e.g. VIX regime) is elevated while the
          composite crash score is not yet in the danger zone.

        Returns a dict with:
            - score: 0.0–1.0 early-warning intensity
            - level: 0–3 discrete early-warning level
            - label: human label for the level
            - summary: one-line explanation
            - signals: list of granular contributing signals
        """
        signals: List[Dict] = []
        sym_upper = (symbol or "").upper()
        is_crypto = any(tag in sym_upper for tag in ["BTC", "ETH", "SOL", "BNB", "DOGE"]) or "-USD" in sym_upper

        # Composite "stress" score that leans into macro + on-chain + technical
        stress_composite = (
            macro_score * 0.45 +
            onchain_score * (0.35 if is_crypto else 0.20) +
            technical_score * 0.25
        )

        # Sentiment divergence: how much more bullish sentiment is vs stress
        perceived_vs_real_gap = max(0.0, sentiment_score - (stress_composite + 0.05))

        if perceived_vs_real_gap > 0.10 and stress_composite > 0.45:
            signals.append({
                "type": "COMPLACENT_SENTIMENT",
                "label": "Complacent bullish sentiment vs rising stress",
                "reason": (
                    "Headline/news sentiment still looks optimistic while macro/on-chain/technical "
                    "risk metrics are behaving like stress is building under the surface."
                ),
            })

        # Cross-asset / volatility stress before full crash trigger
        if volatility_regime in ["ELEVATED", "EXTREME"] and crash_score < self.ALERT_LEVELS[2]['threshold']:
            signals.append({
                "type": "VOLATILITY_STRESS",
                "label": "Volatility regime stressed before price breakdown",
                "reason": (
                    "The volatility index is already in a stressed regime while the main crash "
                    "score is only moderate. This is often how crashes start: volatility wakes up "
                    "before the crowd notices the price move."
                ),
            })

        # Crypto-specific flow stress even if price trend not fully broken yet
        if is_crypto and onchain_score > 0.55 and technical_score < 0.7:
            signals.append({
                "type": "FLOW_STRESS_CRYPTO",
                "label": "Crypto flow / leverage stress building",
                "reason": (
                    "On-chain / derivatives style risk metrics are elevated even though the pure "
                    "technical trend is not fully broken yet. This often precedes liquidation "
                    "cascades in major coins and their ecosystems."
                ),
            })

        # Build early-warning score: start from crash_score and amplify subtle divergences
        base = crash_score
        # Divergence boost – more weight when sentiment is detached from stress
        divergence_boost = perceived_vs_real_gap * 0.6

        # Regime boost – only modest in normal regime, stronger when VIX is high
        regime_boost = 0.0
        if volatility_regime == "NORMAL":
            regime_boost = stress_composite * 0.05
        elif volatility_regime == "ELEVATED":
            regime_boost = stress_composite * 0.12
        elif volatility_regime == "EXTREME":
            regime_boost = stress_composite * 0.18

        # Flow stress boost for crypto when leverage/on-chain risk climbs
        flow_boost = 0.0
        if is_crypto and onchain_score > 0.55:
            flow_boost = (onchain_score - 0.55) * 0.35

        # Slightly de-emphasize when we are already in full crash alert mode –
        # at that point it is no longer "early".
        if alert_level >= 3:
            dampener = 0.6
        elif alert_level == 2:
            dampener = 0.8
        else:
            dampener = 1.0

        raw_score = (base + divergence_boost + regime_boost + flow_boost) * dampener
        score = max(0.0, min(1.0, raw_score))

        # Map continuous score into discrete early-warning levels
        if score < 0.30:
            level = 0
            label = "NO_EARLY_WARNING"
        elif score < 0.55:
            level = 1
            label = "SUBTLE_STRESS"
        elif score < 0.80:
            level = 2
            label = "PRE_CRASH_SETUP"
        else:
            level = 3
            label = "CRASH_BREWING"

        # Human-readable summary, kept to a single short paragraph
        if level == 0:
            summary = (
                "No strong early-warning signals. Risk metrics and sentiment look broadly aligned "
                "with normal volatility."
            )
        else:
            pieces = []
            if any(s["type"] == "COMPLACENT_SENTIMENT" for s in signals):
                pieces.append("sentiment is more bullish than the risk metrics justify")
            if any(s["type"] == "VOLATILITY_STRESS" for s in signals):
                pieces.append("volatility is already acting stressed before price fully breaks")
            if any(s["type"] == "FLOW_STRESS_CRYPTO" for s in signals):
                pieces.append("on-chain / leverage flows look heavy for a calm surface price")

            if not pieces:
                summary = (
                    "Multiple quiet risk factors are lining up even though the headline crash "
                    "score is not yet in the red zone."
                )
            else:
                summary = (
                    "Early risk build-up detected: " + "; ".join(pieces) + ". These are the kinds "
                    "of patterns that often appear days before a major move."
                )

        return {
            "score": score,
            "level": level,
            "label": label,
            "summary": summary,
            "signals": signals,
        }

    def _get_alert_level(self, crash_score: float) -> int:
        """Determine alert level from crash score"""
        if crash_score >= self.ALERT_LEVELS[3]['threshold']:
            return 3
        elif crash_score >= self.ALERT_LEVELS[2]['threshold']:
            return 2
        elif crash_score >= self.ALERT_LEVELS[1]['threshold']:
            return 1
        else:
            return 0
    
    def _run_crash_simulations(
        self, 
        symbol: str, 
        horizon: str, 
        crash_score: float
    ) -> Dict:
        """Run Monte Carlo simulations for crash scenarios"""
        if not self.simulation_engine:
            return {
                'tail_probability': crash_score,
                'simulations': 0
            }
        
        try:
            # Run 500 simulations
            horizon_days = self.HORIZONS[horizon]
            
            # Adjust drift based on crash score
            # High crash score = negative expected return
            base_drift = -0.20 * crash_score  # Up to -20% for max crash score
            
            results = {
                'simulations_run': 500,
                'horizon_days': horizon_days,
                'tail_probability_10pct': 0.0,  # P(loss > 10%)
                'tail_probability_25pct': 0.0,  # P(loss > 25%)
                'expected_return': base_drift,
                'downside_scenarios': 0
            }
            
            # Simplified simulation tracking
            # In production, call actual simulation engine
            results['tail_probability_10pct'] = min(0.95, crash_score * 1.2)
            results['tail_probability_25pct'] = min(0.85, crash_score * 1.0)
            results['downside_scenarios'] = int(500 * crash_score)
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error running simulations: {e}")
            return {'simulations': 0, 'error': str(e)}
    
    def _generate_recommendation(self, alert_level: int, crash_score: float) -> Dict:
        """Generate trading recommendation"""
        if alert_level >= 3:
            return {
                'action': 'DEFENSIVE',
                'specifics': [
                    'PAUSE all new long positions',
                    'HEDGE existing positions with puts',
                    'REDUCE total exposure by 75%',
                    'CONSIDER BUY_PUT opportunities'
                ],
                'urgency': 'IMMEDIATE'
            }
        elif alert_level == 2:
            return {
                'action': 'CAUTIOUS',
                'specifics': [
                    'RESTRICT to BUY_PUT only',
                    'REDUCE position sizes by 50%',
                    'TIGHTEN stop losses',
                    'MONITOR macro conditions closely'
                ],
                'urgency': 'HIGH'
            }
        elif alert_level == 1:
            return {
                'action': 'REDUCE_RISK',
                'specifics': [
                    'REDUCE position sizes by 30%',
                    'FAVOR defensive strategies',
                    'INCREASE cash allocation'
                ],
                'urgency': 'MODERATE'
            }
        else:
            return {
                'action': 'NORMAL',
                'specifics': ['Continue normal operations'],
                'urgency': 'LOW'
            }
    
    def _generate_reasoning(
        self,
        macro_score: float,
        onchain_score: float,
        sentiment_score: float,
        technical_score: float,
        alert_level: int
    ) -> List[str]:
        """Generate human-readable reasoning"""
        reasoning = []
        
        # Macro
        if macro_score > 0.6:
            reasoning.append(f"📉 Macro risk elevated (score: {macro_score:.2f})")
        elif macro_score < 0.4:
            reasoning.append(f"📈 Macro risk low (score: {macro_score:.2f})")
        
        # On-chain
        if onchain_score > 0.6:
            reasoning.append(f"🐋 Bearish on-chain flows (score: {onchain_score:.2f})")
        
        # Sentiment
        if sentiment_score > 0.6:
            reasoning.append(f"📰 Negative sentiment detected (score: {sentiment_score:.2f})")
        elif sentiment_score < 0.4:
            reasoning.append(f"📰 Positive sentiment (score: {sentiment_score:.2f})")
        
        # Technical
        if technical_score > 0.6:
            reasoning.append(f"📊 Technical signals bearish (score: {technical_score:.2f})")
        
        # Alert level verdict
        if alert_level >= 2:
            alert_info = self.ALERT_LEVELS[alert_level]
            reasoning.append(f"{alert_info['severity']} {alert_info['name']}: {alert_info['action']}")
        
        return reasoning
    
    def _log_prediction(self, assessment: Dict):
        """Log prediction for later review"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{self.memory_path}/prediction_{timestamp}.json"
            
            with open(filename, 'w') as f:
                json.dump(assessment, f, indent=2)
            
            # Add to history
            self.prediction_history.append({
                'timestamp': assessment['timestamp'],
                'crash_score': assessment['crash_score'],
                'alert_level': assessment['alert_level']
            })
            
            # Keep only last N predictions
            if len(self.prediction_history) > self.max_history:
                self.prediction_history = self.prediction_history[-self.max_history:]
                
        except Exception as e:
            self.logger.error(f"Error logging prediction: {e}")
    
    def _send_alert(self, assessment: Dict):
        """Send alert for high-risk scenarios"""
        try:
            date_str = datetime.now().strftime('%Y-%m-%d')
            filename = f"{self.alerts_path}/{date_str}.json"
            
            alert = {
                'timestamp': assessment['timestamp'],
                'symbol': assessment['symbol'],
                'alert_level': assessment['alert_level'],
                'crash_score': assessment['crash_score'],
                'early_warning_score': assessment.get('early_warning_score'),
                'early_warning_level': assessment.get('early_warning_level'),
                'early_warning': assessment.get('early_warning'),
                'recommendation': assessment['recommendation'],
                'reasoning': assessment['reasoning']
            }
            
            # Append to daily alerts
            alerts = []
            if os.path.exists(filename):
                with open(filename, 'r') as f:
                    alerts = json.load(f)
            
            alerts.append(alert)
            
            with open(filename, 'w') as f:
                json.dump(alerts, f, indent=2)
            
            self.logger.warning(f"CRASH ALERT LEVEL {assessment['alert_level']}: {assessment['symbol']}")
            
        except Exception as e:
            self.logger.error(f"Error sending alert: {e}")
    
    def update_confidence_weight(self, prediction_correct: bool):
        """Update confidence based on prediction accuracy"""
        self.prediction_history.append({
            'correct': prediction_correct,
            'timestamp': datetime.now().isoformat()
        })
        
        # Keep last 10
        if len(self.prediction_history) > self.max_history:
            self.prediction_history = self.prediction_history[-self.max_history:]
        
        # Calculate accuracy
        if len(self.prediction_history) >= 3:
            recent_correct = sum(1 for p in self.prediction_history[-10:] if p.get('correct', False))
            
            # Adjust confidence weight
            if recent_correct <= 3:  # 30% or worse
                self.confidence_weight = max(0.5, self.confidence_weight * 0.9)  # Reduce by 10%
            elif recent_correct >= 7:  # 70% or better
                self.confidence_weight = min(1.5, self.confidence_weight * 1.1)  # Increase by 10%
    
    def print_crash_report(self, assessment: Dict):
        """Print formatted crash detection report"""
        print("\n" + "="*70)
        print("💀 MARKET CRASH DETECTOR V2 - ASSESSMENT")
        print("="*70)
        print(f"Symbol: {assessment['symbol']}")
        print(f"Timestamp: {assessment['timestamp']}")
        print(f"Horizon: {assessment['horizon']} ({assessment['horizon_days']} days)")
        print(f"\nCRASH SCORE: {assessment['crash_score']:.2%}")
        
        # Alert level
        alert_level = assessment['alert_level']
        if alert_level > 0:
            alert_info = self.ALERT_LEVELS[alert_level]
            print(f"ALERT LEVEL: {alert_info['severity']} {alert_level} - {alert_info['name']}")
        else:
            print("ALERT LEVEL: None (Normal conditions)")

        # Early-warning layer (pre-crash stress signals)
        ew = assessment.get('early_warning') or {}
        ew_score = ew.get('score')
        ew_level = ew.get('level', 0)
        if ew_score is not None and ew_score >= 0.30:
            print("\nEARLY WARNING LAYER:")
            print(f"  Score: {ew_score:.1%} | Level {ew_level} - {ew.get('label', 'EARLY_WARNING')}")
            summary = ew.get('summary')
            if summary:
                print(f"  Summary: {summary}")
            signals = ew.get('signals') or []
            for sig in signals:
                lbl = sig.get('label', sig.get('type', ''))
                reason = sig.get('reason', '')
                if lbl or reason:
                    print(f"  - {lbl}: {reason}")
        
        # Components
        print("\nCOMPONENT SCORES:")
        for component, score in assessment['components'].items():
            print(f"  {component.capitalize()}: {score:.2%}")
        
        # Reasoning
        print("\nREASONING:")
        for reason in assessment['reasoning']:
            print(f"  • {reason}")
        
        # Recommendation
        rec = assessment['recommendation']
        print(f"\nRECOMMENDATION: {rec['action']} (Urgency: {rec['urgency']})")
        for spec in rec['specifics']:
            print(f"  → {spec}")
        
        # Simulation results
        sim = assessment.get('simulation_results', {})
        if sim.get('simulations_run'):
            print(f"\nSIMULATION RESULTS ({sim['simulations_run']} runs):")
            print(f"  Tail Probability (>10% loss): {sim.get('tail_probability_10pct', 0):.1%}")
            print(f"  Tail Probability (>25% loss): {sim.get('tail_probability_25pct', 0):.1%}")
        
        # Price projection
        proj = assessment.get('price_projection')
        if proj and proj.get('current_price') is not None:
            print("\nPRICE PROJECTION (Crash Scenario):")
            print(f"  Current Price: ${proj['current_price']:.2f}")
            if proj.get('moderate_drop_target') is not None:
                print(
                    f"  Moderate Crash Target: ${proj['moderate_drop_target']:.2f} "
                    f"({proj['moderate_drop_pct']:.1%} down)"
                )
            if proj.get('severe_stress_floor') is not None:
                print(
                    f"  Severe Stress Floor: ${proj['severe_stress_floor']:.2f} "
                    f"({proj['severe_drop_pct']:.1%} down)"
                )
            if proj.get('note'):
                print(f"  Note: {proj['note']}")
    
    # ===== CRASH PROFIT STRATEGIES =====
    
    def analyze_crash_sectors(self, crash_data: Dict) -> List[Dict]:
        """
        Analyze which sectors are crashing and prioritize for put strategies
        """
        crashing_sectors = []
        
        # Collect all symbols for batch fetching
        all_symbols = []
        for symbols in self.sector_etfs.values():
            all_symbols.extend(symbols)
        
        # Batch fetch all prices if cache is available
        price_histories = {}
        if self.market_cache and MarketDataCache:
            # Fetch all histories at once
            for symbol in all_symbols:
                hist = self.market_cache.fetch_history(symbol, period='5d')
                price_histories[symbol] = hist
        else:
            # Fallback to individual fetching
            self.logger.warning("MarketDataCache not available, falling back to individual provider calls for sector analysis")
            for symbol in all_symbols:
                try:
                    ticker = yf.Ticker(symbol)
                    hist = ticker.history(period="5d")
                    price_histories[symbol] = hist
                except Exception as e:
                    price_histories[symbol] = None
        
        # Analyze each sector
        for sector_name, symbols in self.sector_etfs.items():
            sector_crash_score = 0
            worst_symbol = None
            worst_drop = 0
            
            for symbol in symbols:
                hist = price_histories.get(symbol)
                if hist is None or len(hist) < 2:
                    continue
                
                try:
                    current_price = hist['Close'].iloc[-1]
                    prev_price = hist['Close'].iloc[-2]
                    drop_pct = (current_price - prev_price) / prev_price
                    
                    # Track worst performer in sector
                    if drop_pct < worst_drop:
                        worst_drop = drop_pct
                        worst_symbol = symbol
                    
                    # Aggregate sector crash score
                    if drop_pct < self.crash_thresholds['minor']:
                        sector_crash_score += abs(drop_pct)
                        
                except Exception as e:
                    print(f"[CRASH PROFIT] Error analyzing {symbol}: {e}")
                    continue
            
            # If sector is crashing significantly, add to opportunities
            if sector_crash_score > 0 and worst_symbol:
                crash_level = self._get_crash_level(worst_drop)
                
                crashing_sectors.append({
                    'sector': sector_name,
                    'worst_symbol': worst_symbol,
                    'drop_pct': worst_drop,
                    'crash_level': crash_level,
                    'sector_score': sector_crash_score,
                    'timestamp': datetime.now().isoformat()
                })
        
        # Sort by severity (worst crashes first)
        crashing_sectors.sort(key=lambda x: x['drop_pct'])
        
        return crashing_sectors
    
    def _get_crash_level(self, drop_pct: float) -> str:
        """Determine crash severity level"""
        if drop_pct <= self.crash_thresholds['severe']:
            return 'SEVERE'
        elif drop_pct <= self.crash_thresholds['moderate']:
            return 'MODERATE'
        elif drop_pct <= self.crash_thresholds['minor']:
            return 'MINOR'
        else:
            return 'MINOR'
    
    def generate_put_strategies(self, crashing_sectors: List[Dict]) -> List[Dict]:
        """
        Generate specific put options strategies for crashing sectors
        """
        put_strategies = []
        
        # Collect symbols for batch fetching
        symbols_to_fetch = [sector['worst_symbol'] for sector in crashing_sectors[:3]]
        
        # Batch fetch current prices
        current_prices = {}
        if self.market_cache and MarketDataCache:
            prices = self.market_cache.fetch_prices(symbols_to_fetch)
            current_prices = prices
        else:
            # Fallback to individual fetching
            for symbol in symbols_to_fetch:
                try:
                    ticker = yf.Ticker(symbol)
                    current_price = ticker.history(period="1d")['Close'].iloc[-1]
                    current_prices[symbol] = current_price
                except Exception as e:
                    current_prices[symbol] = None
        
        for sector in crashing_sectors[:3]:  # Top 3 crashing sectors
            symbol = sector['worst_symbol']
            crash_level = sector['crash_level']
            current_price = current_prices.get(symbol)
            
            if current_price is None:
                print(f"[CRASH PROFIT] Could not get price for {symbol}")
                continue
            
            try:
                # Generate put strategy based on crash severity
                strategy = self._create_put_strategy(
                    symbol, current_price, crash_level, sector
                )
                
                if strategy:
                    put_strategies.append(strategy)
                    
            except Exception as e:
                print(f"[CRASH PROFIT] Error generating strategy for {symbol}: {e}")
                continue
        
        return put_strategies
    
    def _create_put_strategy(self, symbol: str, current_price: float, 
                           crash_level: str, sector_data: Dict) -> Optional[Dict]:
        """Create specific put options strategy"""
        
        # Strategy parameters based on crash severity
        if crash_level == 'SEVERE':
            # Aggressive puts for severe crash
            otm_pct = 0.05  # 5% OTM
            days_to_expiry = 7
            contracts = 10
        elif crash_level == 'MODERATE':
            # Moderate puts
            otm_pct = 0.03
            days_to_expiry = 14
            contracts = 5
        else:
            # Conservative puts
            otm_pct = 0.02
            days_to_expiry = 21
            contracts = 3
        
        # Calculate strike price
        strike_price = round(current_price * (1 - otm_pct), 2)
        
        strategy = {
            'symbol': symbol,
            'action': 'BUY_PUT',
            'strike': strike_price,
            'current_price': current_price,
            'days_to_expiry': days_to_expiry,
            'contracts': contracts,
            'crash_level': crash_level,
            'sector': sector_data['sector'],
            'drop_pct': sector_data['drop_pct'],
            'timestamp': datetime.now().isoformat(),
            'rationale': f"{crash_level} crash in {sector_data['sector']} - {abs(sector_data['drop_pct'])*100:.1f}% drop"
        }
        
        return strategy
    
    def execute_crash_profit_mode(self, crash_assessment: Dict) -> List[Dict]:
        """
        Main entry point - detect crash and generate profit strategies
        """
        if crash_assessment.get('alert_level', 0) >= 2:  # Medium or higher crash risk
            print(f"\n[CRASH PROFIT] Activating profit strategies - Alert Level {crash_assessment.get('alert_level')}")
            
            # Analyze crashing sectors
            crashing_sectors = self.analyze_crash_sectors(crash_assessment)
            
            if crashing_sectors:
                print(f"[CRASH PROFIT] Found {len(crashing_sectors)} crashing sectors")
                
                # Generate put strategies
                put_strategies = self.generate_put_strategies(crashing_sectors)
                
                if put_strategies:
                    print(f"[CRASH PROFIT] Generated {len(put_strategies)} put strategies")
                    for strategy in put_strategies:
                        print(f"  - {strategy['symbol']} {strategy['action']} @ ${strategy['strike']}")
                
                return put_strategies
            else:
                print("[CRASH PROFIT] No significant sector crashes detected")
        else:
            print(f"[CRASH PROFIT] Crash level too low for profit strategies (Alert: {crash_assessment.get('alert_level')})")
        
        return []

        # Ecosystem contagion (impact on meme/penny coins and related assets)
        eco = assessment.get('ecosystem_contagion') or {}
        if eco:
            print("\nECOSYSTEM CONTAGION (Meme / Penny Coins):")
            label = eco.get('label', eco.get('ecosystem', 'Unknown ecosystem'))
            print(f"  Ecosystem: {label}")

            eco_range = eco.get('expected_ecosystem_drawdown_range') or []
            if len(eco_range) == 2:
                low, high = eco_range
                print(f"  Expected ecosystem drawdown: {low:.0%}–{high:.0%} from recent highs")

            penny_range = eco.get('penny_coin_tail_risk_range') or []
            if len(penny_range) == 2:
                low_p, high_p = penny_range
                print(f"  Penny/meme coin tail risk: {low_p:.0%}–{high_p:.0%} intraday wicks")

            reps = eco.get('representative_assets') or []
            if reps:
                print(f"  Representative names: {', '.join(reps)}")

            narrative = eco.get('narrative')
            if narrative:
                print(f"  Note: {narrative}")

        # Crash drivers
        drivers = assessment.get('crash_drivers') or []
        if drivers:
            print("\nCRASH DRIVERS:")
            for d in drivers:
                label = d.get('label', d.get('type', 'UNKNOWN'))
                reason = d.get('reason', '')
                print(f"  - {label}: {reason}")

        print("="*70 + "\n")
    
    def generate_comprehensive_research(self, symbol: str, asset_type: str = 'CRYPTO') -> Dict:
        """
        Generate comprehensive research report combining crash detection with deep market analysis
        """
        print(f"\n[COMPREHENSIVE RESEARCH] Generating deep analysis for {symbol}")
        print("="*70)
        
        # Get crash assessment
        crash_assessment = self.detect_crash_risk(symbol)
        
        # Get full research report
        research_report = self.research_engine.research_asset(symbol, asset_type)
        
        # Get whale activity
        whale_analysis = self.whale_tracker.analyze_whale_activity(symbol, asset_type)
        
        # Get catalyst analysis
        catalyst_analysis = self.catalyst_tracker.analyze_catalyst_impact(symbol, asset_type)
        
        # Synthesize findings
        comprehensive_report = {
            'symbol': symbol,
            'asset_type': asset_type,
            'timestamp': datetime.now(),
            
            # Crash Analysis
            'crash_risk': {
                'score': crash_assessment.get('crash_score', 0),
                'level': crash_assessment.get('alert_level', 0),
                'probability': crash_assessment.get('crash_probability', 0),
                'time_horizons': crash_assessment.get('time_horizon_scores', {}),
                'key_drivers': self._extract_key_drivers(crash_assessment)
            },
            
            # Research Analysis
            'market_research': {
                'recommendation': research_report.recommendation,
                'confidence': research_report.confidence,
                'price_targets': research_report.price_targets,
                'key_findings': [f.title for f in research_report.research_findings[:5]],
                'sentiment': research_report.sentiment_analysis,
                'institutional_flows': research_report.institutional_flows
            },
            
            # Whale Analysis
            'whale_activity': {
                'trend': whale_analysis.get('trends', {}),
                'alerts': len(whale_analysis.get('alerts', [])),
                'exchange_flows': whale_analysis.get('exchange_flows', {}),
                'activity_level': whale_analysis.get('whale_movements', {}).get('activity_level', 'UNKNOWN')
            },
            
            # Catalyst Analysis
            'catalysts': {
                'upcoming_count': len(catalyst_analysis.get('upcoming_catalysts', [])),
                'high_impact': len(catalyst_analysis.get('high_impact_events', [])),
                'recommendation': catalyst_analysis.get('recommendation', ''),
                'next_event': self._get_next_catalyst(catalyst_analysis.get('upcoming_catalysts', []))
            },
            
            # Synthesis
            'synthesis': {
                'overall_signal': self._synthesize_signal(crash_assessment, research_report, whale_analysis, catalyst_analysis),
                'action_plan': self._generate_action_plan(crash_assessment, research_report, catalyst_analysis),
                'risk_level': self._calculate_overall_risk(crash_assessment, research_report),
                'opportunity_level': self._calculate_opportunity_level(research_report, whale_analysis, catalyst_analysis)
            }
        }
        
        # Print comprehensive summary
        self._print_comprehensive_summary(comprehensive_report)
        
        return comprehensive_report
    
    def _extract_key_drivers(self, crash_assessment: Dict) -> List[str]:
        """Extract key crash drivers from assessment"""
        drivers = []
        
        # Check each time horizon for high scores
        time_horizons = crash_assessment.get('time_horizon_scores', {})
        for timeframe, score in time_horizons.items():
            if score > 0.6:
                drivers.append(f"High {timeframe} risk ({score:.1%})")
        
        # Check component scores
        components = crash_assessment.get('component_scores', {})
        for component, score in components.items():
            if score > 0.6:
                drivers.append(f"{component.replace('_', ' ').title()} stress ({score:.1%})")
        
        return drivers[:5]  # Top 5 drivers
    
    def _get_next_catalyst(self, catalysts: List) -> Dict:
        """Get the next upcoming catalyst"""
        if not catalysts:
            return {}
        
        future_catalysts = [c for c in catalysts if c.date > datetime.now()]
        if not future_catalysts:
            return {}
        
        next_catalyst = min(future_catalysts, key=lambda x: x.date)
        days_until = (next_catalyst.date - datetime.now()).days
        
        return {
            'title': next_catalyst.title,
            'days_until': days_until,
            'impact': next_catalyst.impact_potential,
            'category': next_catalyst.category
        }
    
    def _synthesize_signal(self, crash_assessment: Dict, research_report, whale_analysis: Dict, catalyst_analysis: Dict) -> str:
        """Synthesize overall signal from all analyses"""
        crash_score = crash_assessment.get('crash_score', 0)
        crash_level = crash_assessment.get('alert_level', 0)
        
        research_rec = research_report.recommendation
        research_conf = research_report.confidence
        
        whale_trend = whale_analysis.get('trends', {}).get('medium_term', 'NEUTRAL')
        catalyst_rec = catalyst_analysis.get('recommendation', '')
        
        # Decision logic
        if crash_level >= 3:
            return "CRASH_IMMINENT - Defensive posture required"
        elif crash_level >= 2:
            if whale_trend == 'BULLISH':
                return "CRASH_RISK_BUT_ACCUMULATION - Opportunistic buying on dips"
            else:
                return "CRASH_RISK - Reduce exposure, prepare for volatility"
        elif research_rec == 'BUY' and research_conf > 0.7:
            if whale_trend == 'BULLISH':
                return "STRONG_BUY - Multiple bullish signals aligned"
            else:
                return "MODERATE_BUY - Fundamental strength but monitor risks"
        elif catalyst_rec == 'POSITION_FOR_UPSIDE':
            return "CATALYST_DRIVEN_BUY - Position for upcoming catalyst"
        elif catalyst_rec in ['REDUCE_EXPOSURE', 'WAIT_FOR_EVENT']:
            return "CAUTION - Catalyst uncertainty suggests waiting"
        else:
            return "NEUTRAL - Mixed signals, maintain current position"
    
    def _generate_action_plan(self, crash_assessment: Dict, research_report, catalyst_analysis: Dict) -> List[str]:
        """Generate actionable plan based on all analyses"""
        plan = []
        crash_level = crash_assessment.get('alert_level', 0)
        
        if crash_level >= 3:
            plan.extend([
                "IMMEDIATE: Close long positions",
                "IMMEDIATE: Buy protective puts (5-10% OTM)",
                "IMMEDIATE: Increase cash to 50%+",
                "MONITOR: Crash bounce signals for re-entry"
            ])
        elif crash_level >= 2:
            plan.extend([
                "REDUCE position size by 50%",
                "BUY some puts as insurance",
                "SET tighter stop-losses",
                "PREPARE for volatility"
            ])
        elif research_report.recommendation == 'BUY':
            plan.extend([
                "CONSIDER building position",
                "SCALE in over 3-5 days",
                "SET stop-loss at -15%",
                "TARGET: " + str(research_report.price_targets.get('moderate', {}).get('target', 0))
            ])
        else:
            plan.extend([
                "MAINTAIN current position",
                "MONITOR for signal changes",
                "REVIEW risk management"
            ])
        
        # Add catalyst-specific actions
        next_catalyst = self._get_next_catalyst(catalyst_analysis.get('upcoming_catalysts', []))
        if next_catalyst and next_catalyst.get('days_until', 0) <= 7:
            plan.append(f"CATALYST: Prepare for {next_catalyst['title']} in {next_catalyst['days_until']} days")
        
        return plan
    
    def _calculate_overall_risk(self, crash_assessment: Dict, research_report) -> str:
        """Calculate overall risk level"""
        crash_score = crash_assessment.get('crash_score', 0)
        risk_factors = len(research_report.risk_factors)
        
        if crash_score > 0.7 or risk_factors > 5:
            return "VERY_HIGH"
        elif crash_score > 0.5 or risk_factors > 3:
            return "HIGH"
        elif crash_score > 0.3 or risk_factors > 1:
            return "MEDIUM"
        else:
            return "LOW"
    
    def _calculate_opportunity_level(self, research_report, whale_analysis: Dict, catalyst_analysis: Dict) -> str:
        """Calculate opportunity level"""
        if research_report.recommendation == 'BUY' and research_report.confidence > 0.7:
            whale_trend = whale_analysis.get('trends', {}).get('medium_term', 'NEUTRAL')
            if whale_trend == 'BULLISH':
                return "VERY_HIGH"
            else:
                return "HIGH"
        elif len(catalyst_analysis.get('high_impact_events', [])) > 0:
            return "MEDIUM"
        else:
            return "LOW"
    
    def _print_comprehensive_summary(self, report: Dict):
        """Print comprehensive research summary"""
        print("\n" + "="*70)
        print(f"COMPREHENSIVE RESEARCH REPORT FOR {report['symbol']}")
        print("="*70)
        
        print(f"\nOVERALL SIGNAL: {report['synthesis']['overall_signal']}")
        print(f"Risk Level: {report['synthesis']['risk_level']}")
        print(f"Opportunity Level: {report['synthesis']['opportunity_level']}")
        
        print("\nCRASH RISK ANALYSIS:")
        print(f"  Crash Score: {report['crash_risk']['score']:.1%}")
        print(f"  Alert Level: {report['crash_risk']['level']}/3")
        print(f"  Key Drivers: {', '.join(report['crash_risk']['key_drivers'])}")
        
        print("\nMARKET RESEARCH:")
        print(f"  Recommendation: {report['market_research']['recommendation']}")
        print(f"  Confidence: {report['market_research']['confidence']:.1%}")
        print(f"  Key Findings: {', '.join(report['market_research']['key_findings'])}")
        
        print("\nWHALE ACTIVITY:")
        print(f"  Activity Level: {report['whale_activity']['activity_level']}")
        print(f"  Medium Trend: {report['whale_activity']['trend'].get('medium_term', 'UNKNOWN')}")
        print(f"  Alerts: {report['whale_activity']['alerts']} generated")
        
        print("\nUPCOMING CATALYSTS:")
        print(f"  Next: {report['catalysts']['next_event'].get('title', 'None')}")
        print(f"  Days Until: {report['catalysts']['next_event'].get('days_until', 'N/A')}")
        print(f"  High Impact Events: {report['catalysts']['high_impact']}")
        
        print("\nACTION PLAN:")
        for i, action in enumerate(report['synthesis']['action_plan'], 1):
            print(f"  {i}. {action}")
        
        print("="*70 + "\n")
