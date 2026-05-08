"""Base API client with common functionality"""
import time
import logging
from typing import Dict, Any, Optional, List
import requests
from datetime import datetime, timedelta

class BaseAPIClient:
    """Base class for API clients with rate limiting and retry logic"""
    
    def __init__(self, base_url: str, api_key: str = None, rate_limit: int = 10):
        """
        Initialize the API client
        
        Args:
            base_url: Base URL for the API
            api_key: API key if required
            rate_limit: Maximum requests per second
        """
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.rate_limit = rate_limit
        self.last_request_time = 0
        self.session = requests.Session()
        self.logger = logging.getLogger(__name__)
        
        # Set up session headers
        self.session.headers.update({
            'User-Agent': 'PhasmaAI/1.0 (your-email@example.com)',
            'Accept': 'application/json',
        })
        if api_key:
            self.session.headers['Authorization'] = f'Bearer {api_key}'
    
    def _rate_limit(self):
        """Enforce rate limiting"""
        elapsed = time.time() - self.last_request_time
        min_interval = 1.0 / self.rate_limit
        
        if elapsed < min_interval:
            time.sleep(min_interval - elapsed)
        
        self.last_request_time = time.time()
    
    def _request(self, method: str, endpoint: str, **kwargs) -> Optional[Dict[str, Any]]:
        """Make an HTTP request with error handling and retries"""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        max_retries = 3
        retry_delay = 1
        
        for attempt in range(max_retries):
            try:
                self._rate_limit()
                response = self.session.request(method, url, **kwargs)
                response.raise_for_status()
                return response.json() if response.content else {}
                
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 429:  # Rate limited
                    retry_after = int(e.response.headers.get('Retry-After', retry_delay))
                    self.logger.warning(f"Rate limited. Retrying after {retry_after} seconds...")
                    time.sleep(retry_after)
                    continue
                elif e.response.status_code >= 500:
                    self.logger.error(f"Server error: {e}")
                    if attempt == max_retries - 1:
                        raise
                    time.sleep(retry_delay * (attempt + 1))
                    continue
                else:
                    self.logger.error(f"HTTP error: {e}")
                    return None
                    
            except Exception as e:
                self.logger.error(f"Request failed: {e}")
                if attempt == max_retries - 1:
                    raise
                time.sleep(retry_delay * (attempt + 1))
        
        return None
    
    def get(self, endpoint: str, params: Optional[Dict] = None, **kwargs) -> Optional[Dict[str, Any]]:
        """Make a GET request"""
        return self._request('GET', endpoint, params=params, **kwargs)
    
    def post(self, endpoint: str, data: Optional[Dict] = None, **kwargs) -> Optional[Dict[str, Any]]:
        """Make a POST request"""
        return self._request('POST', endpoint, json=data, **kwargs)
    
    def search(self, query: str, **kwargs) -> List[Dict[str, Any]]:
        """Search the API (to be implemented by subclasses)"""
        raise NotImplementedError("Subclasses must implement search method")
