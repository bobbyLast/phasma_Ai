"""
Real-time price fetcher - NO DEFAULTS ALLOWED!
If we can't get a real price, we DON'T TRADE.
Note: Now uses RobustPriceFetcher internally for multi-source reliability
"""
from .robust_price_fetcher import get_robust_price_fetcher
from typing import Optional, Dict

# Global instance
_robust_fetcher = None

def _get_robust_fetcher():
    """Get the robust fetcher instance"""
    global _robust_fetcher
    if _robust_fetcher is None:
        _robust_fetcher = get_robust_price_fetcher()
    return _robust_fetcher

class RealPriceFetcher:
    """Fetches REAL market prices - no fake defaults!"""
    
    def __init__(self):
        # Use robust fetcher internally
        self._robust = _get_robust_fetcher()
    
    def is_valid_stock_symbol(self, symbol: str) -> bool:
        """Validate symbol format to avoid invalid API calls"""
        return self._robust.is_valid_stock_symbol(symbol)
    
    def get_real_price(self, symbol: str) -> Optional[float]:
        """
        Get REAL current price for a symbol.
        Returns None if price cannot be fetched - NO DEFAULTS!
        """
        return self._robust.get_real_price(symbol)
    
    def get_price_with_validation(self, symbol: str) -> Dict:
        """Get price with validation details"""
        return self._robust.get_price_with_validation(symbol)
    
    def get_multiple_prices(self, symbols: list) -> Dict[str, float]:
        """Get prices for multiple symbols"""
        return self._robust.get_multiple_prices(symbols)

# Global instance
_price_fetcher = None

def get_price_fetcher():
    """Get or create the global price fetcher instance."""
    global _price_fetcher
    if _price_fetcher is None:
        _price_fetcher = RealPriceFetcher()
    return _price_fetcher
