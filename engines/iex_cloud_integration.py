"""
IEX Cloud Integration for Company Data
Free tier: 50,000 requests/month
Provides comprehensive company information, fundamentals, and real-time data
"""

import requests
import json
import time
from typing import Dict, Optional, List
from datetime import datetime
import logging

class IEXCloudIntegration:
    """IEX Cloud API integration for company data"""
    
    def __init__(self, config=None):
        self.config = config or {}
        self.api_key = self.config.get('apis', {}).get('iex_cloud', {}).get('api_key', 'pk_YOUR_FREE_API_KEY')
        self.base_url = self.config.get('apis', {}).get('iex_cloud', {}).get('url', 'https://cloud.iexapis.com/stable')
        self.enabled = self.config.get('apis', {}).get('iex_cloud', {}).get('enabled', False)
        
        self.cache = {}
        self.cache_expiry = 3600  # 1 hour cache
        self.logger = logging.getLogger(__name__)
        self.rate_limit_delay = 0.1  # 100ms between requests
        
    def _make_request(self, endpoint: str, params: Dict = None) -> Optional[Dict]:
        """Make authenticated request to IEX Cloud"""
        if not self.enabled or self.api_key == "pk_YOUR_FREE_API_KEY":
            self.logger.debug("IEX Cloud API not enabled or key not configured")
            return None
        
        try:
            url = f"{self.base_url}/{endpoint}"
            params = params or {}
            params['token'] = self.api_key
            
            # Rate limiting
            time.sleep(self.rate_limit_delay)
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            return response.json()
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"IEX Cloud API error: {e}")
            return None
        except Exception as e:
            self.logger.error(f"IEX Cloud request error: {e}")
            return None
    
    def get_company_profile(self, symbol: str) -> Optional[Dict]:
        """Get comprehensive company profile"""
        cache_key = f"profile_{symbol}"
        current_time = time.time()
        
        # Check cache
        if cache_key in self.cache:
            cache_entry = self.cache[cache_key]
            if current_time - cache_entry['timestamp'] < self.cache_expiry:
                return cache_entry['data']
        
        # Fetch from API
        data = self._make_request(f"stock/{symbol}/company")
        if not data:
            return None
        
        # Standardize format
        company_info = {
            'symbol': symbol.upper(),
            'name': data.get('companyName', symbol),
            'sector': data.get('sector', 'Unknown'),
            'industry': data.get('industry', 'Unknown'),
            'description': data.get('description', ''),
            'ceo': data.get('CEO', ''),
            'employees': data.get('employees', 0),
            'country': data.get('country', ''),
            'currency': data.get('currency', 'USD'),
            'website': data.get('website', ''),
            'phone': data.get('phone', ''),
            'address': data.get('address', ''),
            'city': data.get('city', ''),
            'state': data.get('state', ''),
            'zip': data.get('zip', ''),
            'exchange': data.get('exchange', 'Unknown'),
            'market_cap': data.get('marketCap', 0),
            'tags': data.get('tags', []),
            'validation_method': 'iex_cloud',
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
    
    def get_advanced_stats(self, symbol: str) -> Optional[Dict]:
        """Get advanced company statistics"""
        data = self._make_request(f"stock/{symbol}/advanced-stats")
        if not data:
            return None
        
        return {
            'market_cap': data.get('marketcap', 0),
            'pe_ratio': data.get('peRatio', 0),
            'forward_pe': data.get('forwardPE', 0),
            'dividend_yield': data.get('dividendYield', 0),
            'beta': data.get('beta', 0),
            'eps': data.get('latestEPS', 0),
            'revenue': data.get('revenue', 0),
            'gross_profit': data.get('grossProfit', 0),
            'cash': data.get('cash', 0),
            'debt': data.get('debt', 0),
            'return_on_equity': data.get('roe', 0),
            'return_on_assets': data.get('roa', 0),
            'profit_margin': data.get('profitMargin', 0),
            'price_to_book': data.get('priceToBook', 0),
            'price_to_sales': data.get('priceToSales', 0)
        }
    
    def get_financials(self, symbol: str) -> Optional[Dict]:
        """Get financial statements"""
        data = self._make_request(f"stock/{symbol}/financials")
        if not data:
            return None
        
        return {
            'financials': data.get('financials', []),
            'symbol': symbol.upper()
        }
    
    def get_earnings(self, symbol: str) -> Optional[Dict]:
        """Get earnings data"""
        data = self._make_request(f"stock/{symbol}/earnings")
        if not data:
            return None
        
        return {
            'earnings': data.get('earnings', []),
            'symbol': symbol.upper()
        }
    
    def get_dividends(self, symbol: str) -> Optional[Dict]:
        """Get dividend information"""
        data = self._make_request(f"stock/{symbol}/dividends")
        if not data:
            return None
        
        return {
            'dividends': data.get('dividends', []),
            'symbol': symbol.upper()
        }
    
    def search_symbols(self, query: str) -> List[Dict]:
        """Search for symbols by company name"""
        data = self._make_request(f"search/{query}")
        if not data:
            return []
        
        results = []
        for item in data[:10]:  # Limit to 10 results
            results.append({
                'symbol': item.get('symbol', ''),
                'name': item.get('securityName', ''),
                'sector': item.get('sector', ''),
                'exchange': item.get('exchange', ''),
                'type': item.get('issueType', '')
            })
        
        return results
    
    def validate_symbol(self, symbol: str) -> Dict:
        """Validate if symbol exists and get basic info"""
        profile = self.get_company_profile(symbol)
        if profile:
            return {
                'is_valid': True,
                'validation_score': 0.95,  # High confidence for IEX Cloud
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
                    'validation_method': 'iex_cloud_failed'
                },
                'risk_level': 'INVALID'
            }
    
    def get_cache_stats(self) -> Dict:
        """Get cache statistics"""
        return {
            'cache_size': len(self.cache),
            'cache_entries': list(self.cache.keys()),
            'api_key_configured': self.api_key != "pk_YOUR_FREE_API_KEY"
        }

# Test the integration
if __name__ == "__main__":
    # Note: You need to get a free API key from https://iexcloud.io/
    iex = IEXCloudIntegration()
    
    # Test with a known symbol
    if iex.api_key != "pk_YOUR_FREE_API_KEY":
        profile = iex.get_company_profile('AAPL')
        if profile:
            print(f"AAPL: {profile['name']} - {profile['sector']}")
        
        stats = iex.get_advanced_stats('AAPL')
        if stats:
            print(f"Market Cap: ${stats['market_cap']:,.0f}")
        
        search_results = iex.search_symbols('Apple')
        print(f"Found {len(search_results)} Apple-related companies")
    else:
        print("Please configure IEX Cloud API key to test")
    
    print(f"Cache stats: {iex.get_cache_stats()}")
