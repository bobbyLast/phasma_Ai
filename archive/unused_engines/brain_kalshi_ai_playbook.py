"""Kalshi AI Playbook - Professional Trading System

Implements the Kalshi AI Playbook strategies for Weather, Economic Data, and Fed Policy markets.
Focuses on buying mispriced probability before consensus forms.

Core Principles:
1. Price = Odds (buy at $0.40-$0.60, not $0.90)
2. Volume = Execution Safety (minimum thresholds per market type)
3. EV is non-negotiable (never trade negative EV)
4. Timing matters more than prediction (trade 48-24h window)
"""

import os
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import statistics
import math

from engines.kalshi_engine import KalshiPredictionEngine
from engines.enhanced_weather_research import EnhancedWeatherResearch


class KalshiAIPlaybook:
    """Professional Kalshi trading system implementing the AI Playbook"""
    
    def __init__(self, config):
        self.config = config
        self.base_engine = KalshiPredictionEngine(config)
        self.weather_research = EnhancedWeatherResearch()
        
        # API endpoints
        self.base_url = "https://api.elections.kalshi.com/trade-api/v2"
        self.session = self.base_engine.session
        
        # Check if using adjusted thresholds
        adjusted_config = self.config.get('kalshi_ai_playbook', {}).get('adjusted_mode', {})
        use_adjusted = adjusted_config.get('use_adjusted_thresholds', False)
        
        if use_adjusted:
            print("🔧 Using ADJUSTED thresholds (testing mode)")
            self.MARKET_CONFIGS = {
                "WEATHER": {
                    "min_liq_score": adjusted_config.get('min_liquidity_score', 1),
                    "min_volume": adjusted_config.get('min_volume', 50),
                    "price_range": tuple(adjusted_config.get('price_range', [0.10, 0.90])),
                    "entry_window_hrs": tuple(adjusted_config.get('entry_window_hours', [168, 12])),
                    "base_edge": self.config.get('kalshi_ai_playbook', {}).get('min_ev_threshold', 0.05)
                },
                "ECON": {
                    "min_liq_score": adjusted_config.get('min_liquidity_score', 1),
                    "min_volume": adjusted_config.get('min_volume', 100),
                    "price_range": tuple(adjusted_config.get('price_range', [0.10, 0.90])),
                    "entry_window_hrs": tuple(adjusted_config.get('entry_window_hours', [168, 12])),
                    "base_edge": self.config.get('kalshi_ai_playbook', {}).get('min_ev_threshold', 0.05)
                },
                "FED": {
                    "min_liq_score": adjusted_config.get('min_liquidity_score', 1),
                    "min_volume": adjusted_config.get('min_volume', 100),
                    "price_range": tuple(adjusted_config.get('price_range', [0.10, 0.90])),
                    "entry_window_hrs": tuple(adjusted_config.get('entry_window_hours', [168, 12])),
                    "base_edge": self.config.get('kalshi_ai_playbook', {}).get('min_ev_threshold', 0.05)
                }
            }
        else:
            # Professional thresholds (default)
            self.MARKET_CONFIGS = {
                "WEATHER": {
                    "min_liq_score": 2,
                    "min_volume": 500,
                    "price_range": (0.35, 0.60),
                    "entry_window_hrs": (48, 24),
                    "base_edge": 0.10
                },
                "ECON": {
                    "min_liq_score": 2,
                    "min_volume": 1000,
                    "price_range": (0.35, 0.60),
                    "entry_window_hrs": (72, 24),
                    "base_edge": 0.12
                },
                "FED": {
                    "min_liq_score": 3,
                    "min_volume": 2000,
                    "price_range": (0.40, 0.65),
                    "entry_window_hrs": (168, 48),  # 7 days to 2 days
                    "base_edge": 0.10
                }
            }
        
        # Risk management
        self.RISK = {
            "max_per_trade_bankroll_frac": 0.05,
            "max_total_open_bankroll_frac": 0.25,
            "max_same_event_exposure_frac": 0.08
        }
    
    def discover_whitelisted_series(self) -> List[Dict[str, Any]]:
        """Discover whitelisted series using keyword matching
        
        Returns:
            List of series dictionaries for Weather, Econ, and Fed markets
        """
        whitelisted_series = []
        
        try:
            # Get all series
            series_response = self.session.get(f"{self.base_url}/series")
            series_response.raise_for_status()
            all_series = series_response.json().get('series', [])
            
            print(f"   Found {len(all_series)} total series")
            
            # Define keywords for each market type
            weather_keywords = ['temperature', 'temp', 'rain', 'snow', 'weather', 'precipitation', '°f', '°c', 'high', 'low']
            econ_keywords = ['cpi', 'inflation', 'employment', 'nfp', 'gdp', 'economic', 'data', 'initial', 'claims']
            fed_keywords = ['fed', 'fomc', 'interest rate', 'rate decision', 'monetary policy']
            
            # Classify and filter series
            for series in all_series:
                title = series.get('title', '').lower()
                ticker = series.get('ticker', '').lower()
                
                # Check weather
                if any(kw in title or kw in ticker for kw in weather_keywords):
                    series['market_type'] = 'WEATHER'
                    whitelisted_series.append(series)
                
                # Check econ
                elif any(kw in title or kw in ticker for kw in econ_keywords):
                    series['market_type'] = 'ECON'
                    whitelisted_series.append(series)
                
                # Check fed
                elif any(kw in title or kw in ticker for kw in fed_keywords):
                    series['market_type'] = 'FED'
                    whitelisted_series.append(series)
            
            print(f"✅ Discovered {len(whitelisted_series)} whitelisted series")
            return whitelisted_series
            
        except Exception as e:
            print(f"⚠️ Error discovering series: {e}")
            return []
    
    def _classify_market_type(self, title: str, tags: List[str]) -> str:
        """Classify market type based on title and tags"""
        title_lower = title.lower()
        tags_lower = [t.lower() for t in tags]
        
        weather_keywords = ['temperature', 'temp', 'rain', 'snow', 'weather', 'precipitation', '°f', '°c']
        econ_keywords = ['cpi', 'inflation', 'employment', 'nfp', 'gdp', 'economic', 'data']
        fed_keywords = ['fed', 'fomc', 'interest rate', 'rate decision', 'monetary policy']
        
        if any(kw in title_lower or kw in tags_lower for kw in weather_keywords):
            return "WEATHER"
        elif any(kw in title_lower or kw in tags_lower for kw in fed_keywords):
            return "FED"
        elif any(kw in title_lower or kw in tags_lower for kw in econ_keywords):
            return "ECON"
        else:
            return "OTHER"
    
        
    def score_liquidity(self, market: Dict[str, Any], orderbook: Optional[Dict] = None) -> int:
        """Score market liquidity from 0-3
        
        Args:
            market: Market data from Kalshi API
            orderbook: Optional orderbook data for deeper analysis
            
        Returns:
            Liquidity score (0-3)
        """
        score = 0
        
        # Check 24h volume
        volume_24h = market.get('volume_24h', 0)
        if volume_24h >= 500:
            score += 1
        
        # Check spread - use bid/ask
        yes_bid = market.get('yes_bid', 0) / 100
        yes_ask = market.get('yes_ask', 0) / 100
        spread_cents = (yes_ask - yes_bid) * 100
        
        if spread_cents <= 3:  # Tight spread <= 3 cents
            score += 1
        
        # Check total volume
        total_volume = market.get('volume', 0)
        if total_volume >= 1000:
            score += 1
        
        return score
    
    def calculate_dynamic_edge(self, hours_to_close: float, spread_cents: float, 
                             liq_score: int, market_type: str) -> float:
        """Calculate required EV edge based on market conditions
        
        Args:
            hours_to_close: Hours until market closes
            spread_cents: Bid-ask spread in cents
            liq_score: Liquidity score (0-3)
            market_type: WEATHER, ECON, or FED
            
        Returns:
            Required edge as decimal (e.g., 0.12 for 12%)
        """
        config = self.MARKET_CONFIGS.get(market_type, self.MARKET_CONFIGS["WEATHER"])
        edge = config["base_edge"]
        
        # Time-based adjustments
        if hours_to_close > 72:
            edge = 0.18  # Too early = noisy
        elif hours_to_close <= 24:
            edge = 0.15  # Late = less upside
        
        # Spread penalty
        if spread_cents > 4:
            edge += 0.05
        
        # Liquidity bonus
        if liq_score == 3:
            edge -= 0.02
        
        return max(edge, 0.08)  # Minimum 8% edge
    
    def model_probability(self, market: Dict[str, Any], market_type: str) -> float:
        """Calculate model probability for a market
        
        Args:
            market: Market data
            market_type: Type of market (WEATHER, ECON, FED)
            
        Returns:
            Model probability (0-1)
        """
        if market_type == "WEATHER":
            return self._weather_model_probability(market)
        elif market_type == "ECON":
            return self._econ_model_probability(market)
        elif market_type == "FED":
            return self._fed_model_probability(market)
        else:
            return 0.5  # Default
    
    def _weather_model_probability(self, market: Dict[str, Any]) -> float:
        """Weather probability model using enhanced research"""
        ticker = market.get('ticker', '')
        title = market.get('title', '')
        
        # Use enhanced weather research
        research = self.weather_research.analyze_weather_market(ticker, market)
        
        if research.get('valid_market'):
            # Extract probability from research
            confidence = research.get('confidence', 0.5)
            forecast_prob = research.get('detailed_analysis', {}).get('forecast', {}).get('consensus_probability', 0.5)
            
            # Weight the research confidence
            model_prob = forecast_prob * 0.7 + confidence * 0.3
            return max(0.1, min(0.9, model_prob))
        
        return 0.5
    
    def _econ_model_probability(self, market: Dict[str, Any]) -> float:
        """Economic data probability model"""
        # Placeholder for econ model
        # Would integrate with economic forecast APIs
        return 0.5
    
    def _fed_model_probability(self, market: Dict[str, Any]) -> float:
        """Fed policy probability model"""
        # Placeholder for Fed model
        # Would integrate with Fed funds futures and CME FedWatch
        return 0.5
    
    def find_opportunities(self) -> List[Dict[str, Any]]:
        """Find trading opportunities using AI Playbook strategy
        
        Returns:
            List of opportunity dictionaries with full analysis
        """
        opportunities = []
        
        # Discover whitelisted series
        series_list = self.discover_whitelisted_series()
        
        for series in series_list:
            series_ticker = series.get('ticker')
            market_type = series.get('market_type', 'OTHER')
            
            if market_type not in self.MARKET_CONFIGS:
                continue
            
            # Get markets for this series
            markets_url = f"{self.base_url}/markets?series_ticker={series_ticker}&status=open"
            markets_response = self.session.get(markets_url)
            markets_response.raise_for_status()
            markets = markets_response.json().get('markets', [])
            
            for market in markets:
                opp = self._analyze_market(market, market_type)
                if opp and opp['trade_signal']:
                    opportunities.append(opp)
        
        # Sort by EV
        opportunities.sort(key=lambda x: x['ev'], reverse=True)
        
        print(f"🎯 Found {len(opportunities)} AI Playbook opportunities")
        return opportunities
    
    def _analyze_market(self, market: Dict[str, Any], market_type: str) -> Optional[Dict[str, Any]]:
        """Analyze a single market for trading opportunity"""
        config = self.MARKET_CONFIGS[market_type]
        
        # Use market data directly (no need to fetch individual series)
        ticker = market.get('ticker')
        title = market.get('title')
        
        # Calculate time to close
        close_time = market.get('close_time')
        if close_time:
            # Handle different datetime formats
            try:
                if 'Z' in close_time:
                    close_dt = datetime.fromisoformat(close_time.replace('Z', '+00:00'))
                else:
                    close_dt = datetime.fromisoformat(close_time)
                
                # Ensure both datetimes have timezone info
                now = datetime.now()
                if close_dt.tzinfo is not None:
                    now = datetime.now().astimezone()
                
                hours_to_close = (close_dt - now).total_seconds() / 3600
            except Exception as e:
                print(f"   ⚠️ Error parsing close_time for {ticker}: {e}")
                hours_to_close = 999
        else:
            hours_to_close = 999
        
        # Check entry window
        entry_min, entry_max = config['entry_window_hrs']
        if not (entry_max <= hours_to_close <= entry_min):
            return None
        
        # Score liquidity
        liq_score = self.score_liquidity(market)
        if liq_score < config['min_liq_score']:
            return None
        
        # Check price range - use bid/ask midpoint since yes_price doesn't exist
        yes_bid = market.get('yes_bid', 0) / 100  # Convert from cents
        yes_ask = market.get('yes_ask', 0) / 100
        yes_price = (yes_bid + yes_ask) / 2 if yes_bid > 0 or yes_ask > 0 else 0
        price_min, price_max = config['price_range']
        if not (price_min <= yes_price <= price_max):
            return None
        
        # Calculate model probability
        model_prob = self.model_probability(market, market_type)
        
        # Calculate EV
        ev = model_prob - yes_price
        
        # Calculate required edge
        spread_cents = (yes_ask - yes_bid) * 100  # Already in dollars, convert to cents
        required_edge = self.calculate_dynamic_edge(hours_to_close, spread_cents, liq_score, market_type)
        
        # Check if EV meets requirement
        if ev < required_edge:
            return None
        
        # Build opportunity
        opportunity = {
            'ticker': ticker,
            'title': title,
            'market_type': market_type,
            'yes_price': yes_price,
            'model_probability': model_prob,
            'ev': ev,
            'required_edge': required_edge,
            'hours_to_close': hours_to_close,
            'liquidity_score': liq_score,
            'volume': market.get('volume', 0),
            'spread_cents': spread_cents,
            'trade_signal': 'BUY_YES' if model_prob > 0.5 else 'BUY_NO',
            'confidence': abs(ev) / required_edge,  # Confidence as multiple of required edge
            'rationale': self._build_rationale(market, model_prob, yes_price, ev, market_type)
        }
        
        return opportunity
    
    def _build_rationale(self, market: Dict[str, Any], model_prob: float, 
                        market_price: float, ev: float, market_type: str) -> str:
        """Build trading rationale"""
        direction = "YES" if model_prob > 0.5 else "NO"
        
        rationale = f"{market_type} EDGE: Model {model_prob:.1%} vs Market {market_price:.2f} = {ev:+.1%} EV"
        
        if market_type == "WEATHER":
            rationale += " | Weather research consensus"
        elif market_type == "ECON":
            rationale += " | Economic forecast advantage"
        elif market_type == "FED":
            rationale += " | Fed policy expectation"
        
        return rationale
    
    def run_backtest(self, days_back: int = 30) -> Dict[str, Any]:
        """Run backtest on historical data
        
        Args:
            days_back: Number of days to backtest
            
        Returns:
            Backtest results dictionary
        """
        # Placeholder for backtest implementation
        # Would use candlestick data to simulate trading
        return {
            'period': f'{days_back} days',
            'total_opportunities': 0,
            'avg_ev': 0,
            'win_rate': 0,
            'total_return': 0
        }


# Example usage
if __name__ == "__main__":
    from core.config import PhasmaConfig
    
    config = PhasmaConfig()
    playbook = KalshiAIPlaybook(config)
    
    print("🤖 Kalshi AI Playbook System")
    print("=" * 60)
    
    # Find opportunities
    opportunities = playbook.find_opportunities()
    
    if opportunities:
        print(f"\n📊 Top {min(5, len(opportunities))} Opportunities:")
        for i, opp in enumerate(opportunities[:5]):
            print(f"\n{i+1}. {opp['ticker']} ({opp['market_type']})")
            print(f"   Title: {opp['title']}")
            print(f"   Signal: {opp['trade_signal']} @ ${opp['yes_price']:.2f}")
            print(f"   EV: {opp['ev']:+.1%} (Required: {opp['required_edge']:.1%})")
            print(f"   Confidence: {opp['confidence']:.1f}x")
            print(f"   Rationale: {opp['rationale']}")
    else:
        print("\n💤 No opportunities found at this time")
