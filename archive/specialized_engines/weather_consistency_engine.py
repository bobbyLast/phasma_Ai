"""
Phasma Weather Consistency Engine
Built for high win-rate weather prediction on Kalshi
Following the 8 principles for consistency
"""

import requests
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import json

class WeatherConsistencyEngine:
    """High-precision weather prediction engine focused on consistency"""
    
    def __init__(self):
        # Market ranking by predictability (1=highest consistency)
        self.market_ranking = {
            'temperature': 1,      # High: 24-72h temp forecasts
            'rain': 1,             # High: daily rain yes/no
            'snow': 2,             # Medium: measurement issues
            'wind': 2,             # Medium: station-specific noise
            'hurricane': 3,        # Low: path/intensity uncertainty
            'tornado': 3,          # Low: rare/unpredictable
            'global_temp': 3       # Low: long-term noise
        }
        
        # Consensus forecast sources
        self.forecast_sources = [
            'noaa',      # NOAA/NWS official
            'ecmwf',     # European model
            'gfs',       # US model
            'openmeteo'  # OpenMeteo (existing)
        ]
        
        # Edge thresholds (minimum edge required)
        self.edge_thresholds = {
            1: 0.08,  # 8% for high consistency markets
            2: 0.10,  # 10% for medium
            3: 0.12   # 12% for low consistency (avoid unless huge edge)
        }
        
        # Stability filters
        self.stability_limits = {
            'temp_max_drift': 2.0,      # °F
            'rain_prob_variance': 15,    # percentage points
            'model_disagreement': 0.1    # probability difference
        }
        
        # Liquidity requirements
        self.min_volume = 1000
        self.max_spread_pct = 5.0  # Max 5% spread
        
        # Track forecast history for stability
        self.forecast_history = {}
        
    def get_market_type(self, title: str) -> str:
        """Extract market type from title"""
        title_lower = title.lower()
        if any(word in title_lower for word in ['temperature', 'temp', 'high', 'low', '°f', '°c']):
            return 'temperature'
        elif any(word in title_lower for word in ['rain', 'rainfall', 'precipitation']):
            return 'rain'
        elif any(word in title_lower for word in ['snow', 'snowfall']):
            return 'snow'
        elif any(word in title_lower for word in ['wind', 'mph', 'km/h']):
            return 'wind'
        elif any(word in title_lower for word in ['hurricane', 'typhoon', 'cyclone']):
            return 'hurricane'
        elif any(word in title_lower for word in ['tornado']):
            return 'tornado'
        elif any(word in title_lower for word in ['global', 'worldwide', 'earth']):
            return 'global_temp'
        return 'unknown'
    
    def get_consensus_forecast(self, city: str, event_type: str, event_date: str) -> Dict:
        """
        Get ensemble forecast from multiple sources
        Returns: {
            'p_true': estimated true probability,
            'agreement': model agreement score (0-1),
            'stability': forecast stability score (0-1),
            'sources': individual forecasts
        }
        """
        forecasts = {}
        
        # TODO: Implement actual API calls
        # For now, simulate consensus logic
        
        # Simulate getting forecasts from each source
        # In real implementation, would call:
        # - NOAA API
        # - ECMWF data
        # - GFS model runs
        # - OpenMeteo
        
        # Example structure:
        forecasts['noaa'] = self._get_noaa_forecast(city, event_type, event_date)
        forecasts['ecmwf'] = self._get_ecmwf_forecast(city, event_type, event_date)
        forecasts['gfs'] = self._get_gfs_forecast(city, event_type, event_date)
        forecasts['openmeteo'] = self._get_openmeteo_forecast(city, event_type, event_date)
        
        # Calculate consensus
        values = list(forecasts.values())
        
        # Agreement = 1 - standard deviation (higher = more agreement)
        if len(values) > 1:
            agreement = 1.0 - np.std(values)
            p_true = np.mean(values)  # Ensemble mean
        else:
            agreement = 0.5
            p_true = values[0] if values else 0.5
        
        # Check stability against historical forecasts
        stability = self._check_forecast_stability(city, event_type, forecasts)
        
        return {
            'p_true': p_true,
            'agreement': max(0, min(1, agreement)),
            'stability': stability,
            'sources': forecasts
        }
    
    def _check_forecast_stability(self, city: str, event_type: str, current_forecasts: Dict) -> float:
        """Check how stable forecasts have been"""
        key = f"{city}_{event_type}"
        
        if key not in self.forecast_history:
            self.forecast_history[key] = []
        
        history = self.forecast_history[key]
        
        # Add current forecasts to history
        history.append({
            'timestamp': datetime.now(),
            'forecasts': current_forecasts
        })
        
        # Keep only last 8 runs
        if len(history) > 8:
            history = history[-8:]
            self.forecast_history[key] = history
        
        # Calculate stability
        if len(history) < 2:
            return 0.5  # No history yet
        
        # Check drift for temperature
        if event_type == 'temperature':
            temps = [np.mean(list(h['forecasts'].values())) for h in history[-4:]]
            if len(temps) > 1:
                drift = max(temps) - min(temps)
                if drift > self.stability_limits['temp_max_drift']:
                    return 0.0  # Too unstable
        
        # Check variance for rain
        elif event_type == 'rain':
            probs = [np.mean(list(h['forecasts'].values())) for h in history[-4:]]
            if len(probs) > 1:
                variance = np.std(probs) * 100
                if variance > self.stability_limits['rain_prob_variance']:
                    return 0.0  # Too unstable
        
        # Calculate stability score based on recent consistency
        recent_values = [np.mean(list(h['forecasts'].values())) for h in history[-4:]]
        if len(recent_values) > 1:
            stability = 1.0 - (np.std(recent_values) / np.mean(recent_values) if np.mean(recent_values) > 0 else 0)
            return max(0, min(1, stability))
        
        return 0.5
    
    def evaluate_trade_opportunity(self, market: Dict) -> Dict:
        """
        Main evaluation function
        Returns whether to trade and why
        """
        title = market.get('title', '')
        ticker = market.get('ticker', '')
        
        # 1. Check market type (only trade high consistency)
        market_type = self.get_market_type(title)
        consistency_rank = self.market_ranking.get(market_type, 3)
        
        if consistency_rank > 2:
            return {
                'trade': False,
                'reason': f'Market type {market_type} too unpredictable (rank {consistency_rank})',
                'confidence': 0
            }
        
        # 2. Extract city and event details
        city = self._extract_city(title)
        if not city:
            return {
                'trade': False,
                'reason': 'Could not extract city from market title',
                'confidence': 0
            }
        
        # 3. Check liquidity
        volume = market.get('volume', 0)
        if volume < self.min_volume:
            return {
                'trade': False,
                'reason': f'Insufficient volume: {volume} < {self.min_volume}',
                'confidence': 0
            }
        
        # 4. Get consensus forecast
        forecast = self.get_consensus_forecast(city, market_type, market.get('expiration_date'))
        p_true = forecast['p_true']
        
        # 5. Get market implied probability
        last_price = market.get('last_price', 0)
        p_mkt = last_price / 100.0
        
        # 6. Calculate edge
        edge = p_true - p_mkt
        required_edge = self.edge_thresholds[consistency_rank]
        
        if edge < required_edge:
            return {
                'trade': False,
                'reason': f'Edge too small: {edge:.1%} < {required_edge:.1%}',
                'confidence': 0,
                'p_true': p_true,
                'p_mkt': p_mkt,
                'edge': edge
            }
        
        # 7. Check stability
        if forecast['stability'] < 0.5:
            return {
                'trade': False,
                'reason': f'Forecast unstable: stability {forecast["stability"]:.1%} < 50%',
                'confidence': 0
            }
        
        # 8. Check agreement
        if forecast['agreement'] < 0.6:
            return {
                'trade': False,
                'reason': f'Models disagree: agreement {forecast["agreement"]:.1%} < 60%',
                'confidence': 0
            }
        
        # 9. Apply contract-specific rules
        if not self._check_contract_rules(market_type, forecast, market):
            return {
                'trade': False,
                'reason': f'Failed contract-specific rules for {market_type}',
                'confidence': 0
            }
        
        # 10. Calculate confidence
        confidence = min(0.9, edge * 2 + forecast['stability'] + forecast['agreement']) / 3
        
        return {
            'trade': True,
            'reason': f'Strong edge ({edge:.1%}) with stable forecast',
            'confidence': confidence,
            'p_true': p_true,
            'p_mkt': p_mkt,
            'edge': edge,
            'stability': forecast['stability'],
            'agreement': forecast['agreement']
        }
    
    def _check_contract_rules(self, market_type: str, forecast: Dict, market: Dict) -> bool:
        """Contract-specific trading rules"""
        
        if market_type == 'temperature':
            # Avoid extreme boundaries
            title = market.get('title', '').lower()
            if any(extreme in title for extreme in ['> 100', '< -20', 'extreme']):
                return False
            
            # Prefer major cities with good coverage
            city = self._extract_city(market.get('title', ''))
            preferred_cities = ['nyc', 'new york', 'chicago', 'boston', 'philadelphia', 'washington']
            if not any(pref in city.lower() for pref in preferred_cities):
                # Still allow but with higher agreement threshold
                if forecast['agreement'] < 0.8:
                    return False
        
        elif market_type == 'rain':
            # For YES bets: need measurable precip, not "trace"
            if forecast['p_true'] > 0.7:
                # Check if models show actual rain amounts
                # TODO: Implement precipitation amount check
                pass
            
            # For NO bets: need dry conditions + supporting humidity
            if forecast['p_true'] < 0.3:
                # TODO: Check humidity/dew point support
                pass
        
        return True
    
    def _extract_city(self, title: str) -> str:
        """Extract city name from market title"""
        # Simple extraction - would need more sophisticated parsing
        cities = ['NYC', 'New York', 'Chicago', 'Boston', 'Miami', 'Houston', 'LA', 'Los Angeles',
                  'Philadelphia', 'Phoenix', 'San Francisco', 'Seattle', 'Denver', 'Atlanta']
        
        title_upper = title.upper()
        for city in cities:
            if city.upper() in title_upper:
                return city
        
        return ''
    
    # Placeholder methods for actual API implementations
    def _get_noaa_forecast(self, city: str, event_type: str, event_date: str) -> float:
        """Get NOAA/NWS forecast"""
        # TODO: Implement NOAA API call
        return 0.6
    
    def _get_ecmwf_forecast(self, city: str, event_type: str, event_date: str) -> float:
        """Get ECMWF model forecast"""
        # TODO: Implement ECMWF data retrieval
        return 0.65
    
    def _get_gfs_forecast(self, city: str, event_type: str, event_date: str) -> float:
        """Get GFS model forecast"""
        # TODO: Implement GFS model data
        return 0.58
    
    def _get_openmeteo_forecast(self, city: str, event_type: str, event_date: str) -> float:
        """Get OpenMeteo forecast (existing)"""
        # TODO: Use existing OpenMeteo integration
        return 0.62
