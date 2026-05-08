"""
Real Company Data Integration - Working APIs Only
Uses actually available APIs for company information
"""

import requests
import json
import time
import os
from typing import Dict, Optional, List
from datetime import datetime
import logging

class AlphaVantageIntegration:
    """Alpha Vantage API integration - REAL and WORKING"""
    
    def __init__(self, api_key: str = None):
        # Load from environment variable if no key provided
        self.api_key = api_key or os.getenv('ALPHA_VANTAGE_KEY', 'YOUR_ALPHA_VANTAGE_KEY')
        self.base_url = "https://www.alphavantage.co/query"
        self.cache = {}
        self.cache_expiry = 3600  # 1 hour cache
        self.logger = logging.getLogger(__name__)
        self.rate_limit_delay = 12  # Alpha Vantage free tier: 5 calls/minute
        
    def _make_request(self, params: Dict) -> Optional[Dict]:
        """Make request to Alpha Vantage API"""
        if self.api_key == "YOUR_ALPHA_VANTAGE_KEY":
            self.logger.warning("Alpha Vantage API key not configured")
            return None
        
        try:
            params['apikey'] = self.api_key
            time.sleep(self.rate_limit_delay)  # Rate limiting
            
            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            # Check for API limit messages
            if 'Note' in data:
                self.logger.warning(f"Alpha Vantage API limit reached: {data['Note']}")
                return None
                
            return data
            
        except Exception as e:
            self.logger.error(f"Alpha Vantage API error: {e}")
            return None
    
    def get_company_overview(self, symbol: str) -> Optional[Dict]:
        """Get comprehensive company overview"""
        cache_key = f"overview_{symbol}"
        current_time = time.time()
        
        # Check cache
        if cache_key in self.cache:
            cache_entry = self.cache[cache_key]
            if current_time - cache_entry['timestamp'] < self.cache_expiry:
                return cache_entry['data']
        
        # Fetch from API
        params = {'function': 'OVERVIEW', 'symbol': symbol}
        data = self._make_request(params)
        
        if not data or 'Symbol' not in data:
            return None
        
        # Debug: Print what we got
        self.logger.info(f"Alpha Vantage returned for {symbol}: {list(data.keys())[:10]}")
        
        # Helper function to safely convert to float
        def safe_float(value):
            if value is None or value == 'None' or value == '':
                return 0.0
            try:
                return float(value)
            except (ValueError, TypeError):
                return 0.0
        
        # Helper function to safely convert to int
        def safe_int(value):
            if value is None or value == 'None' or value == '':
                return 0
            try:
                return int(value)
            except (ValueError, TypeError):
                return 0
        
        # Standardize format
        company_info = {
            'symbol': symbol.upper(),
            'name': data.get('Name', symbol),
            'sector': data.get('Sector', 'Unknown'),
            'industry': data.get('Industry', 'Unknown'),
            'description': data.get('Description', ''),
            'market_cap': safe_int(data.get('MarketCapitalization')),
            'pe_ratio': safe_float(data.get('PERatio')),
            'dividend_yield': safe_float(data.get('DividendYield')),
            'beta': safe_float(data.get('Beta')),
            'eps': safe_float(data.get('EPS')),
            'revenue': safe_int(data.get('RevenueTTM')),
            'book_value': safe_float(data.get('BookValue')),
            'price_to_book': safe_float(data.get('PriceToBookRatio')),
            'country': data.get('Country', ''),
            'currency': data.get('Currency', 'USD'),
            'exchange': data.get('Exchange', 'Unknown'),
            'validation_method': 'alpha_vantage',
            'is_valid': True,
            'real_ticker': True,
            'timestamp': current_time
        }
        
        # Cache result
        self.cache[cache_key] = {
            'data': company_info,
            'timestamp': current_time
        }
        
        return company_info
    
    def validate_symbol(self, symbol: str) -> Dict:
        """Validate if symbol exists"""
        profile = self.get_company_overview(symbol)
        if profile:
            return {
                'is_valid': True,
                'validation_score': 0.95,  # High confidence for Alpha Vantage
                'company_info': profile,
                'risk_level': 'LOW'
            }
        else:
            return {
                'is_valid': False,
                'validation_score': 0.0,
                'company_info': {
                    'symbol': symbol.upper(),
                    'name': f"{symbol.upper()} - Not Found",
                    'sector': 'UNKNOWN',
                    'industry': 'Invalid Symbol',
                    'validation_method': 'alpha_vantage_failed'
                },
                'risk_level': 'INVALID'
            }

class FinancialModelingPrepIntegration:
    """Financial Modeling Prep API integration - REAL and WORKING"""
    
    def __init__(self, api_key: str = None):
        # Load from environment variable if no key provided
        self.api_key = api_key or os.getenv('FMP_API_KEY', 'YOUR_FMP_KEY')
        self.base_url = "https://financialmodelingprep.com/api/v3"
        self.cache = {}
        self.cache_expiry = 3600  # 1 hour cache
        self.logger = logging.getLogger(__name__)
        self.rate_limit_delay = 0.2  # FMP free tier: 250 requests/day
        
    def _make_request(self, endpoint: str) -> Optional[Dict]:
        """Make request to FMP API"""
        if self.api_key == "YOUR_FMP_KEY":
            self.logger.warning("FMP API key not configured")
            return None
        
        try:
            url = f"{self.base_url}/{endpoint}?apikey={self.api_key}"
            time.sleep(self.rate_limit_delay)  # Rate limiting
            
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            # Check for error messages
            if isinstance(data, dict) and 'error' in data:
                self.logger.warning(f"FMP API error: {data['error']}")
                return None
                
            return data
            
        except Exception as e:
            self.logger.error(f"FMP API error: {e}")
            return None
    
    def get_company_profile(self, symbol: str) -> Optional[Dict]:
        """Get company profile"""
        cache_key = f"profile_{symbol}"
        current_time = time.time()
        
        # Check cache
        if cache_key in self.cache:
            cache_entry = self.cache[cache_key]
            if current_time - cache_entry['timestamp'] < self.cache_expiry:
                return cache_entry['data']
        
        # Fetch from API
        data = self._make_request(f"profile/{symbol}")
        
        if not data or not isinstance(data, list) or len(data) == 0:
            return None
        
        company_data = data[0]
        
        # Standardize format
        company_info = {
            'symbol': symbol.upper(),
            'name': company_data.get('companyName', symbol),
            'sector': company_data.get('sector', 'Unknown'),
            'industry': company_data.get('industry', 'Unknown'),
            'description': company_data.get('description', ''),
            'market_cap': company_data.get('mktCap', 0),
            'price': company_data.get('price', 0),
            'beta': company_data.get('beta', 0),
            'website': company_data.get('website', ''),
            'ceo': company_data.get('ceo', ''),
            'employees': company_data.get('fullTimeEmployees', 0),
            'country': company_data.get('country', ''),
            'currency': company_data.get('currency', 'USD'),
            'exchange': company_data.get('exchange', 'Unknown'),
            'validation_method': 'fmp',
            'is_valid': True,
            'real_ticker': True,
            'timestamp': current_time
        }
        
        # Cache result
        self.cache[cache_key] = {
            'data': company_info,
            'timestamp': current_time
        }
        
        return company_info
    
    def validate_symbol(self, symbol: str) -> Dict:
        """Validate if symbol exists"""
        profile = self.get_company_profile(symbol)
        if profile:
            return {
                'is_valid': True,
                'validation_score': 0.9,  # High confidence for FMP
                'company_info': profile,
                'risk_level': 'LOW'
            }
        else:
            return {
                'is_valid': False,
                'validation_score': 0.0,
                'company_info': {
                    'symbol': symbol.upper(),
                    'name': f"{symbol.upper()} - Not Found",
                    'sector': 'UNKNOWN',
                    'industry': 'Invalid Symbol',
                    'validation_method': 'fmp_failed'
                },
                'risk_level': 'INVALID'
            }

class PolygonIOIntegration:
    """Polygon.io API integration - REAL and WORKING"""
    
    def __init__(self, api_key: str = None):
        # Load from environment variable if no key provided
        self.api_key = api_key or os.getenv('POLYGON_API_KEY', 'YOUR_POLYGON_KEY')
        self.base_url = "https://api.polygon.io/v3"
        self.cache = {}
        self.cache_expiry = 3600  # 1 hour cache
        self.logger = logging.getLogger(__name__)
        self.rate_limit_delay = 0.1  # Polygon free tier: 5 calls/minute
        
    def _make_request(self, endpoint: str) -> Optional[Dict]:
        """Make request to Polygon API"""
        if self.api_key == "YOUR_POLYGON_KEY":
            self.logger.warning("Polygon API key not configured")
            return None
        
        try:
            url = f"{self.base_url}/{endpoint}?apikey={self.api_key}"
            time.sleep(self.rate_limit_delay)  # Rate limiting
            
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            # Check for error messages
            if 'error' in data:
                self.logger.warning(f"Polygon API error: {data['error']}")
                return None
                
            return data
            
        except Exception as e:
            self.logger.error(f"Polygon API error: {e}")
            return None
    
    def get_ticker_details(self, symbol: str) -> Optional[Dict]:
        """Get ticker details"""
        cache_key = f"ticker_{symbol}"
        current_time = time.time()
        
        # Check cache
        if cache_key in self.cache:
            cache_entry = self.cache[cache_key]
            if current_time - cache_entry['timestamp'] < self.cache_expiry:
                return cache_entry['data']
        
        # Fetch from API
        data = self._make_request(f"reference/tickers/{symbol.upper()}")
        
        if not data or 'results' not in data:
            return None
        
        ticker_data = data['results']
        
        # Standardize format
        company_info = {
            'symbol': symbol.upper(),
            'name': ticker_data.get('name', symbol),
            'sector': ticker_data.get('sector', 'Unknown'),
            'industry': ticker_data.get('industry', 'Unknown'),
            'description': ticker_data.get('description', ''),
            'market_cap': ticker_data.get('market_cap', 0),
            'address': ticker_data.get('address', {}).get('address1', ''),
            'city': ticker_data.get('address', {}).get('city', ''),
            'state': ticker_data.get('address', {}).get('state', ''),
            'country': ticker_data.get('address', {}).get('country', ''),
            'website': ticker_data.get('homepage_url', ''),
            'employees': ticker_data.get('employee_count', 0),
            'currency': ticker_data.get('currency_name', 'USD'),
            'exchange': ticker_data.get('primary_exchange', 'Unknown'),
            'validation_method': 'polygon',
            'is_valid': True,
            'real_ticker': True,
            'timestamp': current_time
        }
        
        # Cache result
        self.cache[cache_key] = {
            'data': company_info,
            'timestamp': current_time
        }
        
        return company_info
    
    def validate_symbol(self, symbol: str) -> Dict:
        """Validate if symbol exists"""
        profile = self.get_ticker_details(symbol)
        if profile:
            return {
                'is_valid': True,
                'validation_score': 0.95,  # Very high confidence for Polygon
                'company_info': profile,
                'risk_level': 'LOW'
            }
        else:
            return {
                'is_valid': False,
                'validation_score': 0.0,
                'company_info': {
                    'symbol': symbol.upper(),
                    'name': f"{symbol.upper()} - Not Found",
                    'sector': 'UNKNOWN',
                    'industry': 'Invalid Symbol',
                    'validation_method': 'polygon_failed'
                },
                'risk_level': 'INVALID'
            }

# Test the integrations
if __name__ == "__main__":
    print("🧪 Testing REAL Company Data APIs")
    print("=" * 40)
    
    # Test Alpha Vantage
    print("\n1. Alpha Vantage (5 calls/min free):")
    alpha = AlphaVantageIntegration()
    if alpha.api_key != "YOUR_ALPHA_VANTAGE_KEY":
        profile = alpha.get_company_overview('AAPL')
        if profile:
            print(f"✅ AAPL: {profile['name']} - {profile['sector']}")
        else:
            print("❌ Failed to get AAPL data")
    else:
        print("⚠️ API key not configured")
    
    # Test FMP
    print("\n2. Financial Modeling Prep (250 calls/day free):")
    fmp = FinancialModelingPrepIntegration()
    if fmp.api_key != "YOUR_FMP_KEY":
        profile = fmp.get_company_profile('AAPL')
        if profile:
            print(f"✅ AAPL: {profile['name']} - {profile['sector']}")
        else:
            print("❌ Failed to get AAPL data")
    else:
        print("⚠️ API key not configured")
    
    # Test Polygon
    print("\n3. Polygon.io (5 calls/min free):")
    polygon = PolygonIOIntegration()
    if polygon.api_key != "YOUR_POLYGON_KEY":
        profile = polygon.get_ticker_details('AAPL')
        if profile:
            print(f"✅ AAPL: {profile['name']} - {profile['sector']}")
        else:
            print("❌ Failed to get AAPL data")
    else:
        print("⚠️ API key not configured")
    
    print("\n📝 Get API keys:")
    print("   Alpha Vantage: https://www.alphavantage.co/support/#api-key")
    print("   FMP: https://site.financialmodelingprep.com/developer/docs")
    print("   Polygon: https://polygon.io/")
