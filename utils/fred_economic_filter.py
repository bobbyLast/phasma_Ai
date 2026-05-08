#!/usr/bin/env python3
"""
PHASMA AI - FRED Economic Filter
Uses Federal Reserve Economic Data for market regime filtering
"""

import asyncio
import os
import aiohttp
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class MacroIndicators:
    """Key macro economic indicators"""
    gdp_growth: float
    unemployment_rate: float
    cpi_inflation: float
    interest_rate: float
    consumer_confidence: float
    manufacturing_pmi: float
    timestamp: str

class FRDEconomicFilter:
    """FRED API integration for macroeconomic filtering"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.stlouisfed.org/fred"
        self.session = None
        
        # FRED series IDs
        self.series_ids = {
            'GDP': 'GDP',  # GDP Growth Rate
            'UNRATE': 'UNRATE',  # Unemployment Rate
            'CPIAUCSL': 'T5YIE',  # 5-Year Breakeven Inflation Rate (% - not raw index)
            'FEDFUNDS': 'FEDFUNDS',  # Federal Funds Rate
            'UMCSENT': 'UMCSENT',  # Consumer Sentiment
        }
        
        # Regime thresholds
        self.thresholds = {
            'recession_gdp': -0.5,  # GDP growth below this = recession risk
            'high_unemployment': 6.0,  # Above this = bearish
            'high_inflation': 4.0,  # Above this = bearish
            'high_interest_rates': 5.0,  # Above this = bearish
            'low_confidence': 70.0,  # Below this = bearish
            'contraction_pmi': 48.0  # Below this = contraction
        }
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def get_series_data(self, series_id: str, limit: int = 1) -> Optional[float]:
        """Get latest data for a FRED series"""
        try:
            url = f"{self.base_url}/series/observations"
            params = {
                'series_id': series_id,
                'api_key': self.api_key,
                'file_type': 'json',
                'sort_order': 'desc',
                'limit': limit
            }
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    observations = data.get('observations', [])
                    if observations:
                        return float(observations[0].get('value', 0))
                else:
                    logger.error(f"FRED API error for {series_id}: {response.status}")
                    
        except Exception as e:
            logger.error(f"Error fetching {series_id}: {e}")
        
        return None
    
    async def get_macro_indicators(self) -> Optional[MacroIndicators]:
        """Get all macro indicators"""
        try:
            def _safe_num(value: Optional[float], default: float = 0.0) -> float:
                """Normalize FRED values so regime comparisons never see None/NaN."""
                try:
                    if value is None:
                        return default
                    return float(value)
                except (TypeError, ValueError):
                    return default

            # Fetch all series concurrently
            tasks = []
            for name, series_id in self.series_ids.items():
                task = self.get_series_data(series_id)
                tasks.append((name, task))
            
            results = {}
            for name, task in tasks:
                value = await task
                results[name] = value
            
            # Calculate GDP growth rate (quarter over quarter)
            gdp_value = results.get('GDP', 0)
            gdp_growth = 0.0  # Would need previous quarter for real calculation
            
            # Create indicators object
            indicators = MacroIndicators(
                gdp_growth=gdp_growth,
                unemployment_rate=_safe_num(results.get('UNRATE'), 0.0),
                cpi_inflation=_safe_num(results.get('CPIAUCSL'), 0.0),
                interest_rate=_safe_num(results.get('FEDFUNDS'), 0.0),
                consumer_confidence=_safe_num(results.get('UMCSENT'), 0.0),
                manufacturing_pmi=50.0,  # Default neutral; FRED ISM series unavailable
                timestamp=datetime.now().isoformat()
            )
            
            logger.info("Macro indicators fetched successfully")
            return indicators
            
        except Exception as e:
            logger.error(f"Error fetching macro indicators: {e}")
            return None
    
    def determine_market_regime(self, indicators: MacroIndicators) -> str:
        """Determine market regime based on macro indicators"""
        score = 0
        reasons = []
        
        # GDP growth
        if indicators.gdp_growth < self.thresholds['recession_gdp']:
            score -= 2
            reasons.append(f"Negative GDP growth: {indicators.gdp_growth:.1f}%")
        elif indicators.gdp_growth > 2.0:
            score += 1
            reasons.append(f"Strong GDP growth: {indicators.gdp_growth:.1f}%")
        
        # Unemployment
        if indicators.unemployment_rate > self.thresholds['high_unemployment']:
            score -= 1
            reasons.append(f"High unemployment: {indicators.unemployment_rate:.1f}%")
        elif indicators.unemployment_rate < 4.0:
            score += 1
            reasons.append(f"Low unemployment: {indicators.unemployment_rate:.1f}%")
        
        # Inflation
        if indicators.cpi_inflation > self.thresholds['high_inflation']:
            score -= 1
            reasons.append(f"High inflation: {indicators.cpi_inflation:.1f}%")
        elif 2.0 < indicators.cpi_inflation < 3.0:
            score += 1
            reasons.append(f"Moderate inflation: {indicators.cpi_inflation:.1f}%")
        
        # Interest rates
        if indicators.interest_rate > self.thresholds['high_interest_rates']:
            score -= 1
            reasons.append(f"High interest rates: {indicators.interest_rate:.1f}%")
        elif indicators.interest_rate < 2.0:
            score += 1
            reasons.append(f"Low interest rates: {indicators.interest_rate:.1f}%")
        
        # Consumer confidence
        if indicators.consumer_confidence < self.thresholds['low_confidence']:
            score -= 1
            reasons.append(f"Low consumer confidence: {indicators.consumer_confidence:.1f}")
        elif indicators.consumer_confidence > 100:
            score += 1
            reasons.append(f"High consumer confidence: {indicators.consumer_confidence:.1f}")
        
        # Manufacturing PMI
        if indicators.manufacturing_pmi < self.thresholds['contraction_pmi']:
            score -= 2
            reasons.append(f"Manufacturing contraction: PMI {indicators.manufacturing_pmi:.1f}")
        elif indicators.manufacturing_pmi > 55:
            score += 1
            reasons.append(f"Manufacturing expansion: PMI {indicators.manufacturing_pmi:.1f}")
        
        # Determine regime
        if score <= -3:
            regime = "BEARISH"
            logger.warning(f"Bearish regime detected (score: {score}). Reasons: {'; '.join(reasons)}")
        elif score >= 2:
            regime = "BULLISH"
            logger.info(f"Bullish regime detected (score: {score}). Reasons: {'; '.join(reasons)}")
        else:
            regime = "NEUTRAL"
            logger.info(f"Neutral regime (score: {score}). Reasons: {'; '.join(reasons)}")
        
        return regime
    
    def get_filter_adjustments(self, regime: str) -> Dict[str, Any]:
        """Get filter adjustments based on regime"""
        adjustments = {
            'BEARISH': {
                'min_confidence': 0.8,  # Higher confidence required
                'min_volume': 2000000,  # Higher volume required
                'max_positions': 5,  # Fewer positions
                'position_size_multiplier': 0.5,  # Smaller positions
                'skip_momentum': True,  # Skip momentum plays
                'focus_defensive': True  # Focus on defensive sectors
            },
            'BULLISH': {
                'min_confidence': 0.6,  # Normal confidence
                'min_volume': 1000000,  # Normal volume
                'max_positions': 15,  # More positions
                'position_size_multiplier': 1.2,  # Larger positions
                'skip_momentum': False,  # Allow momentum
                'focus_defensive': False
            },
            'NEUTRAL': {
                'min_confidence': 0.7,  # Slightly higher confidence
                'min_volume': 1500000,  # Moderate volume
                'max_positions': 10,  # Moderate positions
                'position_size_multiplier': 1.0,  # Normal positions
                'skip_momentum': False,
                'focus_defensive': False
            }
        }
        
        return adjustments.get(regime, adjustments['NEUTRAL'])

# Example usage
async def main():
    """Example of FRED economic filter"""
    api_key = os.getenv('FRED_API_KEY')
    if not api_key:
        print("Missing FRED_API_KEY")
        return
    
    async with FRDEconomicFilter(api_key) as fred:
        # Get macro indicators
        indicators = await fred.get_macro_indicators()
        
        if indicators:
            print("\nMacro Indicators:")
            print(f"  GDP Growth: {indicators.gdp_growth:.2f}%")
            print(f"  Unemployment: {indicators.unemployment_rate:.1f}%")
            print(f"  Inflation (CPI): {indicators.cpi_inflation:.1f}")
            print(f"  Interest Rate: {indicators.interest_rate:.1f}%")
            print(f"  Consumer Confidence: {indicators.consumer_confidence:.1f}")
            print(f"  Manufacturing PMI: {indicators.manufacturing_pmi:.1f}" if indicators.manufacturing_pmi is not None else "  Manufacturing PMI: N/A")
            
            # Determine regime
            regime = fred.determine_market_regime(indicators)
            print(f"\nMarket Regime: {regime}")
            
            # Get filter adjustments
            adjustments = fred.get_filter_adjustments(regime)
            print(f"\nFilter Adjustments for {regime}:")
            for key, value in adjustments.items():
                print(f"  {key}: {value}")

if __name__ == "__main__":
    import os
    from dotenv import load_dotenv
    load_dotenv()
    asyncio.run(main())
