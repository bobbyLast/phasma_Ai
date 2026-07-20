"""
SEC EDGAR Company Data Integration
Fetches comprehensive company information from SEC EDGAR database
Free, reliable source for all US public companies
"""

import os
import requests
import json
import time
import re
from typing import Dict, List, Optional
from datetime import datetime
import logging

def _project_root() -> str:
    return os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def _sec_user_agent() -> str:
    ua = (os.getenv('SEC_USER_AGENT') or '').strip()
    if ua:
        return ua
    return 'Phasma AI Trading System (research@phasma.ai)'


def _sec_cache_refresh_seconds() -> float:
    try:
        hours = float(os.getenv('SEC_CACHE_REFRESH_HOURS', '24'))
    except (TypeError, ValueError):
        hours = 24.0
    if hours <= 0:
        hours = 24.0
    return hours * 3600


class SECEdgarIntegration:
    """SEC EDGAR database integration for company data"""
    
    def __init__(self):
        self.base_url = "https://www.sec.gov/files/edgar"
        self.company_db = {}
        self.last_update = 0
        self.cache_file = os.path.join(_project_root(), "data", "sec_company_database.json")
        self.headers = {'User-Agent': _sec_user_agent()}
        self.logger = logging.getLogger(__name__)
        
        self._load_cache()
        if not self.company_db:
            self.download_company_tickers()
    
    def _load_cache(self):
        """Load cached company database"""
        try:
            with open(self.cache_file, 'r') as f:
                data = json.load(f)
            if isinstance(data, dict) and 'companies' in data:
                self.company_db = data.get('companies') or {}
                self.last_update = float(data.get('last_update') or 0)
            elif isinstance(data, dict):
                self.company_db = data
                self.last_update = 0
            else:
                self.company_db = {}
                self.last_update = 0
            self.logger.info(f"Loaded {len(self.company_db)} companies from SEC cache")
        except FileNotFoundError:
            self.logger.info("No SEC cache found, will download fresh data")
            self.company_db = {}
        except Exception as e:
            self.logger.warning(f"Error loading SEC cache: {e}")
            self.company_db = {}
        self._refresh_if_stale()
    
    def _save_cache(self):
        """Save company database to cache"""
        try:
            os.makedirs(os.path.dirname(self.cache_file), exist_ok=True)
            with open(self.cache_file, 'w') as f:
                json.dump(
                    {'last_update': self.last_update, 'companies': self.company_db},
                    f,
                    indent=2,
                )
            self.logger.info(f"Saved {len(self.company_db)} companies to SEC cache")
        except Exception as e:
            self.logger.warning(f"Error saving SEC cache: {e}")

    def _refresh_if_stale(self) -> None:
        refresh_seconds = _sec_cache_refresh_seconds()
        if self.last_update and time.time() - self.last_update <= refresh_seconds:
            return
        if not self.last_update and not self.company_db:
            return
        age_hours = (time.time() - self.last_update) / 3600 if self.last_update else 0
        self.logger.info(f"SEC cache stale ({age_hours:.1f}h), refreshing...")
        self.download_company_tickers()
    
    def download_company_tickers(self) -> bool:
        """Download company ticker data from SEC"""
        try:
            # SEC company ticker file
            url = "https://www.sec.gov/files/company_tickers.json"
            
            self.logger.info("Downloading SEC company tickers...")
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            
            ticker_data = response.json()
            
            # Convert to more usable format
            companies = {}
            for item in ticker_data.values():
                symbol = item['ticker']
                companies[symbol] = {
                    'symbol': symbol,
                    'name': item['title'],
                    'cik': item['cik_str'],
                    'exchange': self._get_exchange_from_symbol(symbol),
                    'sector': 'Unknown',
                    'industry': 'Unknown',
                    'validation_method': 'sec_edgar',
                    'is_valid': True,
                    'real_ticker': True
                }
            
            self.company_db = companies
            self.last_update = time.time()
            self._save_cache()
            
            self.logger.info(f"Downloaded {len(companies)} companies from SEC EDGAR")
            return True
            
        except Exception as e:
            self.logger.error(f"Error downloading SEC tickers: {e}")
            return False
    
    def _get_exchange_from_symbol(self, symbol: str) -> str:
        """Determine exchange from symbol pattern"""
        # Simple heuristics for exchange detection
        if '.' in symbol:
            return 'NYSE'  # NYSE stocks often have . for class shares
        elif len(symbol) <= 4 and symbol.isalpha():
            return 'NASDAQ'  # Most NASDAQ symbols are 1-4 letters
        elif len(symbol) <= 3 and symbol.isalpha():
            return 'NYSE'  # NYSE symbols are typically 1-3 letters
        else:
            return 'Unknown'
    
    def get_company_info(self, symbol: str) -> Optional[Dict]:
        """Get company information for a symbol"""
        symbol = symbol.upper()
        
        self._refresh_if_stale()
        return self.company_db.get(symbol)
    
    def search_companies_by_name(self, name_query: str) -> List[Dict]:
        """Search companies by name"""
        name_query = name_query.lower()
        results = []
        
        for symbol, company in self.company_db.items():
            if name_query in company['name'].lower():
                results.append(company)
        
        return results
    
    def get_all_symbols(self) -> List[str]:
        """Get all available symbols"""
        return list(self.company_db.keys())
    
    def update_company_details(self, symbol: str, additional_data: Dict):
        """Update company with additional details"""
        if symbol in self.company_db:
            self.company_db[symbol].update(additional_data)
            self._save_cache()
    
    def get_stats(self) -> Dict:
        """Get database statistics"""
        return {
            'total_companies': len(self.company_db),
            'last_update': datetime.fromtimestamp(self.last_update).isoformat() if self.last_update else None,
            'cache_file': self.cache_file
        }

# Test the integration
if __name__ == "__main__":
    sec = SECEdgarIntegration()
    
    # Download data
    if sec.download_company_tickers():
        print(f"Successfully downloaded {len(sec.company_db)} companies")
        
        # Test lookup
        kss_info = sec.get_company_info('KSS')
        if kss_info:
            print(f"KSS: {kss_info['name']}")
        
        # Test search
        apple_companies = sec.search_companies_by_name('Apple')
        print(f"Found {len(apple_companies)} companies with 'Apple' in name")
        
        print(f"Stats: {sec.get_stats()}")
    else:
        print("Failed to download SEC data")
