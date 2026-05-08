"""Weather Validation Engine for Kalshi Temperature Markets

Validates temperature prediction markets using historical weather data and forecasts
from OpenMeteo API (FREE, no API key required) to assess prediction accuracy and confidence.
"""

import os
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
import json


class WeatherValidationEngine:
    """Weather validation engine for Kalshi temperature prediction markets."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        # OpenMeteo - FREE, no API key required, unlimited calls
        self.base_url = "https://api.open-meteo.com/v1"
        self.archive_url = "https://archive-api.open-meteo.com/v1"
        self.enabled = True  # Always enabled - no API key needed
        
        # City coordinates for major markets
        self.city_coords = {
            'NYC': {'lat': 40.7128, 'lon': -74.0060, 'name': 'New York City'},
            'CHI': {'lat': 41.8781, 'lon': -87.6298, 'name': 'Chicago'},
            'LA': {'lat': 34.0522, 'lon': -118.2437, 'name': 'Los Angeles'},
            'BOS': {'lat': 42.3601, 'lon': -71.0589, 'name': 'Boston'},
            'MIA': {'lat': 25.7617, 'lon': -80.1918, 'name': 'Miami'},
            'SEA': {'lat': 47.6062, 'lon': -122.3321, 'name': 'Seattle'},
            'DFW': {'lat': 32.7767, 'lon': -96.7970, 'name': 'Dallas'},
            'PHX': {'lat': 33.4484, 'lon': -112.0740, 'name': 'Phoenix'},
            'PHL': {'lat': 39.9526, 'lon': -75.1652, 'name': 'Philadelphia'},
            'ATL': {'lat': 33.7490, 'lon': -84.3880, 'name': 'Atlanta'}
        }
        
        print(" Weather validation engine initialized with OpenMeteo API (FREE, no key required)")
    
    def parse_kalshi_temp_market(self, market_title: str, ticker: str) -> Optional[Dict[str, Any]]:
        """Parse Kalshi temperature market to extract location, date, and temperature range.
        
        Args:
            market_title: Market title (e.g., "Will the high temp in NYC be 42-43° on Dec 11, 2025?")
            ticker: Market ticker (e.g., "KXHIGHNY-25DEC11-B42.5")
            
        Returns:
            Dict with parsed location, date, temp_range or None if parsing fails
        """
        try:
            title_lower = market_title.lower()
            
            # Extract city code
            city_code = None
            for code in self.city_coords:
                if code.lower() in title_lower:
                    city_code = code
                    break
            
            if not city_code:
                # Try ticker parsing (e.g., KXHIGHNY -> NYC)
                if 'NYC' in ticker:
                    city_code = 'NYC'
                elif 'CHI' in ticker:
                    city_code = 'CHI'
                elif 'LA' in ticker:
                    city_code = 'LA'
            
            if not city_code:
                return None
            
            # Extract temperature range from title
            temp_range = None
            if '>45' in title_lower:
                temp_range = {'min': 45.1, 'max': 100, 'type': 'above'}
            elif '<38' in title_lower:
                temp_range = {'min': -100, 'max': 37.9, 'type': 'below'}
            elif '42-43' in title_lower:
                temp_range = {'min': 42, 'max': 43, 'type': 'range'}
            elif '40-41' in title_lower:
                temp_range = {'min': 40, 'max': 41, 'type': 'range'}
            elif '44-45' in title_lower:
                temp_range = {'min': 44, 'max': 45, 'type': 'range'}
            else:
                # Try to extract generic range pattern "X-Y°"
                import re
                range_match = re.search(r'(\d+)-(\d+)[°\s]', market_title)
                if range_match:
                    temp_range = {
                        'min': float(range_match.group(1)),
                        'max': float(range_match.group(2)),
                        'type': 'range'
                    }
            
            if not temp_range:
                return None
            
            # Extract date from ticker (e.g., 25DEC11 -> Dec 11, 2025)
            date_match = None
            import re
            date_pattern = r'(\d{2})([A-Z]{3})(\d{2})'
            date_match = re.search(date_pattern, ticker)
            
            if date_match:
                year = 2000 + int(date_match.group(1))
                month_str = date_match.group(2)
                day = int(date_match.group(3))
                
                month_map = {
                    'JAN': 1, 'FEB': 2, 'MAR': 3, 'APR': 4, 'MAY': 5, 'JUN': 6,
                    'JUL': 7, 'AUG': 8, 'SEP': 9, 'OCT': 10, 'NOV': 11, 'DEC': 12
                }
                
                month = month_map.get(month_str)
                if month:
                    target_date = datetime(year, month, day)
                else:
                    return None
            else:
                return None
            
            return {
                'city_code': city_code,
                'city_name': self.city_coords[city_code]['name'],
                'coords': self.city_coords[city_code],
                'target_date': target_date,
                'temp_range': temp_range,
                'days_until': (target_date - datetime.now()).days
            }
            
        except Exception as e:
            print(f" Error parsing temperature market: {e}")
            return None
    
    def get_historical_weather(self, lat: float, lon: float, days_back: int = 30) -> Optional[List[Dict[str, Any]]]:
        """Get historical weather data for the past N days using OpenMeteo (FREE, unlimited).
        
        Args:
            lat: Latitude
            lon: Longitude
            days_back: Number of days to look back (up to 90+ days available)
            
        Returns:
            List of daily weather data or None if error
        """
        if not self.enabled:
            return None
        
        try:
            # OpenMeteo historical API - completely FREE, no key required
            end_date = datetime.now() - timedelta(days=1)  # Yesterday
            start_date = datetime.now() - timedelta(days=days_back)
            
            url = f"{self.archive_url}/archive"
            params = {
                'latitude': lat,
                'longitude': lon,
                'start_date': start_date.strftime('%Y-%m-%d'),
                'end_date': end_date.strftime('%Y-%m-%d'),
                'daily': 'temperature_2m_max,temperature_2m_min,temperature_2m_mean',
                'temperature_unit': 'fahrenheit',
                'timezone': 'auto'
            }
            
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if 'daily' in data:
                    historical_data = []
                    for i in range(len(data['daily']['time'])):
                        historical_data.append({
                            'date': data['daily']['time'][i],
                            'temp_high': data['daily']['temperature_2m_max'][i],
                            'temp_low': data['daily']['temperature_2m_min'][i],
                            'temp_mean': data['daily']['temperature_2m_mean'][i],
                            'humidity': 0,  # Not available in basic free tier
                            'wind_speed': 0,  # Not available in basic free tier
                            'description': 'Historical data'
                        })
                    return historical_data
            else:
                print(f" Historical weather API error: {response.status_code}")
            
            return None
            
        except Exception as e:
            print(f" Error fetching historical weather: {e}")
            return None
    
    def get_weather_forecast(self, lat: float, lon: float, days_forward: int = 16) -> Optional[List[Dict[str, Any]]]:
        """Get weather forecast for the next N days using OpenMeteo (FREE, unlimited).
        
        Args:
            lat: Latitude
            lon: Longitude
            days_forward: Number of days to forecast (up to 16 days available)
            
        Returns:
            List of daily forecast data or None if error
        """
        if not self.enabled:
            return None
        
        try:
            # OpenMeteo forecast API - completely FREE, no key required
            url = f"{self.base_url}/forecast"
            params = {
                'latitude': lat,
                'longitude': lon,
                'daily': 'temperature_2m_max,temperature_2m_min,temperature_2m_mean',
                'temperature_unit': 'fahrenheit',
                'timezone': 'auto',
                'forecast_days': min(days_forward, 16)  # OpenMeteo supports up to 16 days
            }
            
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if 'daily' in data:
                    forecast_list = []
                    for i in range(len(data['daily']['time'])):
                        forecast_list.append({
                            'date': data['daily']['time'][i],
                            'temp_high': data['daily']['temperature_2m_max'][i],
                            'temp_low': data['daily']['temperature_2m_min'][i],
                            'temp_mean': data['daily']['temperature_2m_mean'][i],
                            'humidity': 0,  # Not available in basic free tier
                            'wind_speed': 0,  # Not available in basic free tier
                            'description': 'Forecast data'
                        })
                    return forecast_list
            else:
                print(f" Weather forecast API error: {response.status_code}")
            
            return None
                
        except Exception as e:
            print(f" Error fetching weather forecast: {e}")
            return None
    
    def validate_temperature_prediction(self, market_title: str, ticker: str) -> Dict[str, Any]:
        """Validate a temperature prediction market using weather data.
        
        Args:
            market_title: Market title
            ticker: Market ticker
            
        Returns:
            Validation results with confidence assessment
        """
        if not self.enabled:
            return {
                'enabled': False,
                'reason': 'Weather validation disabled: No API key'
            }
        
        # Parse market details
        parsed = self.parse_kalshi_temp_market(market_title, ticker)
        if not parsed:
            return {
                'enabled': True,
                'valid': False,
                'reason': 'Could not parse market details'
            }
        
        city = parsed['city_name']
        coords = parsed['coords']
        target_date = parsed['target_date']
        temp_range = parsed['temp_range']
        days_until = parsed['days_until']
        
        print(f"🌤️ Validating temperature prediction for {city} on {target_date.strftime('%Y-%m-%d')}")
        print(f"   Target range: {temp_range['min']}°-{temp_range['max']}° ({temp_range['type']})")
        
        # Get historical data
        historical = self.get_historical_weather(coords['lat'], coords['lon'], days_back=7)
        
        # Get forecast data
        forecast = self.get_weather_forecast(coords['lat'], coords['lon'], days_forward=min(days_until + 2, 7))
        
        # Analyze data
        validation = {
            'enabled': True,
            'valid': True,
            'city': city,
            'target_date': target_date.strftime('%Y-%m-%d'),
            'days_until': days_until,
            'temp_range': temp_range,
            'historical_data': historical,
            'forecast_data': forecast,
            'confidence': 0.5,
            'analysis': '',
            'recommendation': 'HOLD'
        }
        
        # Historical analysis
        if historical:
            recent_highs = [day['temp_high'] for day in historical]
            avg_recent_high = sum(recent_highs) / len(recent_highs)
            max_recent_high = max(recent_highs)
            min_recent_high = min(recent_highs)
            
            validation['historical_analysis'] = {
                'avg_recent_high': round(avg_recent_high, 1),
                'max_recent_high': round(max_recent_high, 1),
                'min_recent_high': round(min_recent_high, 1),
                'recent_trend': 'stable',
                'data_points': len(historical)
            }
            
            # Check if target range is historically reasonable
            if temp_range['type'] == 'range':
                if avg_recent_high >= temp_range['min'] and avg_recent_high <= temp_range['max']:
                    validation['confidence'] += 0.2
                    validation['analysis'] += f"Historical avg ({avg_recent_high:.1f}°) supports target range. "
                elif avg_recent_high < temp_range['min']:
                    validation['confidence'] -= 0.1
                    validation['analysis'] += f"Historical avg ({avg_recent_high:.1f}°) below target range. "
                else:
                    validation['confidence'] -= 0.1
                    validation['analysis'] += f"Historical avg ({avg_recent_high:.1f}°) above target range. "
        
        # Forecast analysis
        if forecast and days_until <= 7:
            target_forecast = None
            for day in forecast:
                forecast_date = datetime.strptime(day['date'], '%Y-%m-%d').date()
                if forecast_date == target_date.date():
                    target_forecast = day
                    break
            
            if target_forecast:
                forecast_high = target_forecast['temp_high']
                validation['forecast_analysis'] = {
                    'forecast_high': round(forecast_high, 1),
                    'forecast_description': target_forecast['description']
                }
                
                if temp_range['type'] == 'range':
                    if forecast_high >= temp_range['min'] and forecast_high <= temp_range['max']:
                        validation['confidence'] += 0.3
                        validation['analysis'] += f"Forecast ({forecast_high:.1f}°) supports target range. "
                        validation['recommendation'] = 'BUY_YES'
                    elif forecast_high < temp_range['min']:
                        validation['confidence'] -= 0.2
                        validation['analysis'] += f"Forecast ({forecast_high:.1f}°) below target range. "
                        validation['recommendation'] = 'BUY_NO'
                    else:
                        validation['confidence'] -= 0.2
                        validation['analysis'] += f"Forecast ({forecast_high:.1f}°) above target range. "
                        validation['recommendation'] = 'BUY_NO'
        
        # Seasonal adjustment for NYC December
        if city == 'New York City' and target_date.month == 12:
            # NYC December highs typically 35-45°F
            if temp_range['type'] == 'range' and temp_range['min'] >= 35 and temp_range['max'] <= 50:
                validation['confidence'] += 0.1
                validation['analysis'] += "Range aligns with typical NYC December weather. "
            elif temp_range['type'] == 'above' and temp_range['min'] > 50:
                validation['confidence'] -= 0.2
                validation['analysis'] += "Above 50°F is unusually high for NYC December. "
            elif temp_range['type'] == 'below' and temp_range['max'] < 30:
                validation['confidence'] -= 0.1
                validation['analysis'] += "Below 30°F is unusually low for NYC December. "
        
        # Final confidence adjustment
        validation['confidence'] = max(0.0, min(1.0, validation['confidence']))
        
        return validation
    
    def get_weather_summary_for_opportunity(self, market_title: str, ticker: str) -> str:
        """Get a concise weather validation summary for trading opportunities.
        
        Args:
            market_title: Market title
            ticker: Market ticker
            
        Returns:
            Concise weather validation summary
        """
        validation = self.validate_temperature_prediction(market_title, ticker)
        
        if not validation.get('enabled'):
            return "🌤️ Weather validation unavailable"
        
        if not validation.get('valid'):
            return "🌤️ Unable to parse weather market"
        
        confidence_pct = validation.get('confidence', 0.5) * 100
        recommendation = validation.get('recommendation', 'HOLD')
        analysis = validation.get('analysis', '')
        
        summary = f"🌤️ Weather Validation: {recommendation} ({confidence_pct:.0f}% confidence)"
        
        if validation.get('forecast_analysis'):
            forecast_high = validation['forecast_analysis']['forecast_high']
            summary += f" | Forecast: {forecast_high:.0f}°"
        
        if validation.get('historical_analysis'):
            avg_high = validation['historical_analysis']['avg_recent_high']
            summary += f" | Recent avg: {avg_high:.0f}°"
        
        return summary
