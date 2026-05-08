"""Infinite Symbol Provider - Ensures unlimited symbol availability"""

import json
import yfinance as yf
import pandas as pd
from typing import List, Dict, Set
import logging
import os
from datetime import datetime
import random

class InfiniteSymbolProvider:
    """Provides unlimited symbols from various sources with fallbacks"""
    
    def __init__(self, config_path: str = None):
        self.logger = logging.getLogger(__name__)
        self.config_path = config_path or os.path.join(os.path.dirname(__file__), '..', 'config', 'trading_config.json')
        self.config = self._load_config()
        
        # Cache for symbols
        self._symbol_cache = {}
        self._last_update = None
        
        # Initialize symbol pools
        self.symbol_pools = {
            'stocks': set(),
            'crypto': set(),
            'etf': set(),
            'commodities': set(),
            'forex': set()
        }
        
        # Refresh symbol pools on initialization
        self._refresh_symbol_pools()
        
    def _load_config(self) -> Dict:
        """Load configuration from file"""
        try:
            with open(self.config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            self.logger.warning(f"Could not load config: {e}")
            return {
                "symbol_sources": {
                    "fallback_symbols": [
                        "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA", "SPY", "QQQ", "BTC-USD"
                    ]
                }
            }
    
    def get_symbols(self, category: str = 'all', limit: int = None) -> List[str]:
        """Get symbols from specified category"""
        # Refresh cache if needed
        if not self._last_update or (datetime.now() - self._last_update).days > 1:
            self._refresh_symbol_pools()
        
        if category == 'all':
            symbols = []
            for pool in self.symbol_pools.values():
                symbols.extend(list(pool))
        else:
            symbols = list(self.symbol_pools.get(category, set()))
        
        # Add fallback symbols if needed
        if len(symbols) < 50:
            fallback = self.config.get('symbol_sources', {}).get('fallback_symbols', [])
            symbols.extend(fallback)
        
        # Remove duplicates and limit if specified
        symbols = list(set(symbols))
        if limit:
            symbols = symbols[:limit]
        
        return symbols
    
    def _refresh_symbol_pools(self):
        """Refresh all symbol pools from various sources"""
        self.logger.info("Refreshing symbol pools...")
        
        # Stock symbols
        try:
            # S&P 500
            sp500 = self._get_sp500_symbols()
            self.symbol_pools['stocks'].update(sp500)
            
            # NASDAQ 100
            nasdaq100 = self._get_nasdaq100_symbols()
            self.symbol_pools['stocks'].update(nasdaq100)
            
            # Russell 2000 (small caps)
            russell2000 = self._get_russell2000_symbols()
            self.symbol_pools['stocks'].update(russell2000)
            
        except Exception as e:
            self.logger.warning(f"Failed to fetch stock symbols: {e}")
        
        # Crypto symbols
        try:
            crypto_symbols = self._get_crypto_symbols()
            self.symbol_pools['crypto'].update(crypto_symbols)
        except Exception as e:
            self.logger.warning(f"Failed to fetch crypto symbols: {e}")
        
        # ETF symbols
        try:
            etf_symbols = self._get_etf_symbols()
            self.symbol_pools['etf'].update(etf_symbols)
        except Exception as e:
            self.logger.warning(f"Failed to fetch ETF symbols: {e}")
        
        self._last_update = datetime.now()
        self.logger.info(f"Symbol pools refreshed. Total symbols: {self.get_total_symbol_count()}")
    
    def _get_sp500_symbols(self) -> List[str]:
        """Get S&P 500 symbols"""
        try:
            # Wikipedia table of S&P 500 companies
            url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
            tables = pd.read_html(url)
            df = tables[0]
            return df['Symbol'].tolist()
        except:
            # Fallback to hardcoded list
            return [
                "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA", "BRK.B", "JPM", "V",
                "JNJ", "WMT", "PG", "MA", "UNH", "HD", "BAC", "XOM", "PFE", "CSCO",
                "ADBE", "CRM", "NFLX", "INTC", "CMCSA", "PEP", "COST", "TMO", "AVGO", "TXN"
            ]
    
    def _get_nasdaq100_symbols(self) -> List[str]:
        """Get NASDAQ 100 symbols"""
        try:
            url = "https://en.wikipedia.org/wiki/NASDAQ-100"
            tables = pd.read_html(url)
            df = tables[4]  # The NASDAQ-100 table is usually the 4th table
            return df['Ticker'].tolist()
        except:
            # Fallback to major tech stocks
            return [
                "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA", "ADBE", "CRM", "NFLX",
                "INTC", "CSCO", "CMCSA", "PEP", "COST", "AVGO", "TXN", "QCOM", "TMUS", "SBUX"
            ]
    
    def _get_russell2000_symbols(self) -> List[str]:
        """Get Russell 2000 symbols (sample)"""
        # Return a sample of small-cap stocks
        return [
            "SIRI", "AMC", "BNGO", "MVIS", "NOK", "BB", "GME", "KOSS", "EXPR", "FCEL",
            "PLUG", "NKTR", "SPCE", "RKT", "HOOD", "SOFI", "UPST", "COIN", "RIVN", "LCID"
        ]
    
    def _get_crypto_symbols(self) -> List[str]:
        """Get cryptocurrency symbols"""
        return [
            "BTC-USD", "ETH-USD", "BNB-USD", "XRP-USD", "ADA-USD", "SOL-USD", "DOGE-USD",
            "DOT-USD", "MATIC-USD", "SHIB-USD", "LTC-USD", "AVAX-USD", "LINK-USD", "UNI-USD",
            "ATOM-USD", "XLM-USD", "ETC-USD", "FIL-USD", "TRX-USD", "ALGO-USD"
        ]
    
    def _get_etf_symbols(self) -> List[str]:
        """Get ETF symbols"""
        return [
            "SPY", "QQQ", "DIA", "IWM", "GLD", "SLV", "TLT", "HYG", "LQD", "USO",
            "XLF", "XLK", "XLE", "XLV", "XLI", "XLU", "XLP", "XLY", "XLB", "XLRE",
            "VTI", "VOO", "IVV", "VO", "VTV", "VUG", "VYM", "VEA", "VWO", "BND"
        ]
    
    def get_total_symbol_count(self) -> int:
        """Get total count of all symbols"""
        return sum(len(pool) for pool in self.symbol_pools.values())
    
    def get_random_symbols(self, count: int = 100) -> List[str]:
        """Get random symbols from all pools"""
        import random
        all_symbols = self.get_symbols()
        return random.sample(all_symbols, min(count, len(all_symbols)))
    
    def validate_symbol(self, symbol: str) -> bool:
        """Check if a symbol is valid by trying to fetch data"""
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="1d")
            return not hist.empty
        except:
            return False
    
    def get_available_symbols(self, count: int = 50) -> List[str]:
        """Get symbols that are confirmed to have data available"""
        symbols = self.get_random_symbols(count * 2)  # Get more to account for failures
        valid_symbols = []
        
        for symbol in symbols:
            if self.validate_symbol(symbol):
                valid_symbols.append(symbol)
                if len(valid_symbols) >= count:
                    break
        
        return valid_symbols


# Global instance
_symbol_provider = None

def get_symbol_provider() -> InfiniteSymbolProvider:
    """Get global symbol provider instance"""
    global _symbol_provider
    if _symbol_provider is None:
        _symbol_provider = InfiniteSymbolProvider()
    return _symbol_provider
