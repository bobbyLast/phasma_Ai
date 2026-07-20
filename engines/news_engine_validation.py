"""
News Engine Validation Module - Enhanced with SEC EDGAR and IEX Cloud
Validates companies mentioned in news articles using multiple data sources
"""

import yfinance as market_data
import requests
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import json
import os
import re

# Import new integrations
from .sec_edgar_integration import SECEdgarIntegration
from .real_company_data import AlphaVantageIntegration, FinancialModelingPrepIntegration, PolygonIOIntegration
from utils.company_resolver import get_resolver, is_placeholder

class CompanyValidator:
    """
    Validates companies using dynamic provider bridge API
    Replaces static hardcoded database with real-time data
    """

    def __init__(self, config=None):
        # Initialize logger
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        
        # Add console handler if not already added
        if not self.logger.handlers:
            ch = logging.StreamHandler()
            ch.setLevel(logging.INFO)
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            ch.setFormatter(formatter)
            self.logger.addHandler(ch)
        # Prevent double-printing if root logger also has handlers
        self.logger.propagate = False

        # Initialize new data sources
        self.config = config or {}
        self.sec_edgar = SECEdgarIntegration()
        self.alpha_vantage = AlphaVantageIntegration()
        self.fmp = FinancialModelingPrepIntegration()
        self.polygon = PolygonIOIntegration()
        
        # NON-TRADEABLE SYMBOLS - Never trade these under any circumstances
        self.blocked_symbols = {
            # Currency pairs (not stocks)
            'EURUSD', 'GBPUSD', 'USDJPY', 'AUDUSD', 'USDCAD', 'USDCHF', 'NZDUSD',
            'EURJPY', 'GBPJPY', 'AUDJPY', 'CADJPY', 'CHFJPY', 'EURGBP', 'EURCAD',
            'GBPCAD', 'AUDCAD', 'NZDCAD', 'EURCHF', 'GBPCHF', 'AUDCHF', 'NZDCHF',
            # Commodities (not stocks)
            'GOLD', 'SILVER', 'COPPER', 'CRUDE', 'NATURALGAS', 'CORN', 'WHEAT',
            'SOYBEANS', 'COTTON', 'SUGAR', 'COFFEE', 'COCOA', 'PLATINUM', 'PALLADIUM'
        }

        # INDICES - Can be traded under specific conditions (not blanket exclusion)
        self.indices = {
            'VIX', 'SPY', 'SPX', 'QQQ', 'IWM', 'VTI', 'VOO', 'IVV', 'SCHB',
            'DIA', 'ONEQ', 'VTWO', 'SCHX', 'SCHA', 'SCHM', 'SCHV', 'SCHG',
            'IJR', 'IJH', 'IJJ', 'IJK', 'IJT', 'IJS', 'IWN', 'IWO', 'IWP', 'IWS',
            'SPYG', 'SPYV', 'SPYD', 'SPYL', 'SPTM', 'SPTS', 'SPTL', 'SPTB',
            'QQQE', 'QQQM', 'PSQ', 'QID', 'QLD', 'TQQQ', 'SQQQ', 'UPRO', 'SPXL', 'SPXS',
            # Additional indices
            'RUT', 'NDX', 'COMPX', 'DJIA', 'NYA', 'XAX', 'BATX', 'HGX',
            'SOX', 'BKX', 'XBD', 'XED', 'XEO', 'XSP', 'ES', 'NQ', 'RTY', 'YM'
        }

        # Cache for validation results (24h expiry)
        self.validation_cache = {}
        self.cache_expiry = 24 * 60 * 60  # 24 hours for valid companies

        # Cache for rejected symbols (1h expiry - shorter for flexibility)
        self.rejected_cache = {}
        self.rejected_cache_expiry = 1 * 60 * 60  # 1 hour

        self.invalid_cache = {}

        # API rate limiting
        self.api_call_count = 0
        self.last_api_reset = time.time()

        # Persistent cache file
        self.cache_file = os.path.join(os.path.dirname(__file__), "..", "data", "company_validation_cache.json")
        self._load_validation_cache()

        # Fallback database for essential companies if API fails
        self.fallback_db = {
            'AAPL': {'name': 'Apple Inc.', 'sector': 'Technology', 'industry': 'Tech/AI'},
            'MSFT': {'name': 'Microsoft Corporation', 'sector': 'Technology', 'industry': 'Tech/AI'},
            'GOOGL': {'name': 'Alphabet Inc.', 'sector': 'Technology', 'industry': 'Tech/AI'},
            'NVDA': {'name': 'NVIDIA Corporation', 'sector': 'Technology', 'industry': 'Tech/AI'},
            'TSLA': {'name': 'Tesla, Inc.', 'sector': 'Automotive', 'industry': 'EV/Auto'},
            'TXN': {'name': 'Texas Instruments Incorporated', 'sector': 'Technology', 'industry': 'Tech/AI'},
            'AMD': {'name': 'Advanced Micro Devices, Inc.', 'sector': 'Technology', 'industry': 'Tech/AI'},
            'META': {'name': 'Meta Platforms, Inc.', 'sector': 'Technology', 'industry': 'Tech/AI'},
            'CRM': {'name': 'Salesforce, Inc.', 'sector': 'Technology', 'industry': 'Tech/AI'},
            'AMZN': {'name': 'Amazon.com, Inc.', 'sector': 'Consumer Cyclical', 'industry': 'E-commerce'},
            # Crypto-exposed stocks
            'MSTR': {'name': 'MicroStrategy Incorporated', 'sector': 'Technology', 'industry': 'Crypto/Blockchain'},
            'COIN': {'name': 'Coinbase Global, Inc.', 'sector': 'Financial Services', 'industry': 'Crypto/Blockchain'},
            'MARA': {'name': 'Marathon Digital Holdings', 'sector': 'Technology', 'industry': 'Crypto/Blockchain'},
            'RIOT': {'name': 'Riot Platforms, Inc.', 'sector': 'Technology', 'industry': 'Crypto/Blockchain'},
            'CLSK': {'name': 'CleanSpark, Inc.', 'sector': 'Technology', 'industry': 'Crypto/Blockchain'},
            'HUT': {'name': 'Hut 8 Mining Corp.', 'sector': 'Technology', 'industry': 'Crypto/Blockchain'},
            'SQ': {'name': 'Block, Inc.', 'sector': 'Financial Services', 'industry': 'Crypto/Blockchain'},
            'PYPL': {'name': 'PayPal Holdings, Inc.', 'sector': 'Financial Services', 'industry': 'Crypto/Blockchain'},
            'HOOD': {'name': 'Robinhood Markets, Inc.', 'sector': 'Financial Services', 'industry': 'Crypto/Blockchain'}
        }

        # Load symbols from phasma_state.json watchlist instead of hardcoded lists
        self.high_vol_industries = self._load_symbols_from_config()

        # Clean industry symbols to remove any indices that might have been included
        for industry, symbols in self.high_vol_industries.items():
            self.high_vol_industries[industry] = [s for s in symbols if s.upper() not in self.indices]

        # API rate limiting
        self.api_call_count = 0
        self.last_api_reset = time.time()

        # Build once — never rebuild on every property access (was a major cycle cost)
        self._company_db = self._build_company_db()

    def _load_symbols_from_config(self) -> Dict[str, List[str]]:
        """Load symbols from phasma_state.json sector watchlist instead of hardcoded lists."""
        try:
            from core.runtime_paths import phasma_state_file
            config_path = phasma_state_file()
            with open(config_path, 'r') as f:
                config = json.load(f)
            
            # Extract symbols from sector watchlist
            high_vol_industries = {}
            sector_watchlist = config.get('config', {}).get('assets', {}).get('sector_watchlist', {})
            
            for sector_name, sector_data in sector_watchlist.items():
                if 'symbols' in sector_data:
                    # Convert sector name to industry format
                    industry_name = sector_data.get('focus', sector_name)
                    symbols = sector_data['symbols']
                    
                    # Filter out blocked symbols and indices
                    filtered_symbols = []
                    for symbol in symbols:
                        sym_upper = symbol.upper()
                        if sym_upper not in self.blocked_symbols and sym_upper not in self.indices:
                            filtered_symbols.append(symbol)
                    
                    high_vol_industries[industry_name] = filtered_symbols
            
            print(f"🔍 NEWS DEBUG: Loaded {len(high_vol_industries)} industries from phasma_state.json")
            for industry, symbols in high_vol_industries.items():
                print(f"🔍 NEWS DEBUG: {industry}: {len(symbols)} symbols")
            
            return high_vol_industries
            
        except Exception as e:
            print(f"⚠️ Could not load symbols from phasma_state.json: {e}")
            # Fallback to minimal hardcoded list
            return {
                'Tech/AI': ['NVDA', 'AMD', 'TSLA'],
                'Crypto/Blockchain': ['MSTR', 'COIN', 'MARA']
            }

    def _get_sector_for_symbol(self, symbol: str) -> Optional[str]:
        """Safely resolve sector for a symbol from cached validation or fallback db."""
        sym = symbol.upper()
        if sym in self.validation_cache:
            return self.validation_cache[sym].get('sector')
        if sym in self.fallback_db:
            return self.fallback_db[sym].get('sector')
        return None

    def _load_validation_cache(self) -> None:
        """Load persisted validation cache if available."""
        try:
            cache_path = os.path.abspath(self.cache_file)
            os.makedirs(os.path.dirname(cache_path), exist_ok=True)
            if os.path.exists(cache_path):
                with open(cache_path, "r") as f:
                    data = json.load(f)
                    # Only keep entries that are not expired
                    now = time.time()
                    fresh = {}
                    for k, v in data.items():
                        ts = v.get("timestamp", 0)
                        if now - ts <= self.cache_expiry:
                            fresh[k] = v
                    self.validation_cache = fresh
        except Exception as e:
            self.logger.warning(f"Could not load validation cache: {e}")

    def _persist_validation_cache(self) -> None:
        """Persist validation cache to disk."""
        try:
            cache_path = os.path.abspath(self.cache_file)
            os.makedirs(os.path.dirname(cache_path), exist_ok=True)
            with open(cache_path, "w") as f:
                json.dump(self.validation_cache, f, indent=2)
        except Exception as e:
            self.logger.warning(f"Could not persist validation cache: {e}")

    def validate_company_enhanced(self, symbol: str) -> Dict:
        """Enhanced company validation using multiple REAL sources"""
        symbol_upper = symbol.upper()
        current_time = time.time()
        
        # Check blocked symbols first
        if symbol_upper in self.blocked_symbols:
            return {
                'is_valid': False,
                'validation_score': 0.0,
                'company_info': {
                    'symbol': symbol_upper,
                    'name': f"{symbol_upper} - Non-Tradeable",
                    'sector': 'BLOCKED',
                    'industry': 'Currency or Commodity',
                    'validation_method': 'blocked_symbol'
                },
                'risk_level': 'INVALID'
            }
        
        # Check indices
        if symbol_upper in self.indices:
            return self._validate_index(symbol_upper, {})
        
        # Try SEC EDGAR first (most reliable, free)
        sec_data = self.sec_edgar.get_company_info(symbol_upper)
        if sec_data:
            sec_data = dict(sec_data)
            sec_data["resolver_status"] = "sec_exact"
            sec_data["validation_method"] = "sec_edgar"
            self.logger.info(f"✅ SEC EDGAR found: {symbol_upper} - {sec_data['name']}")
            return {
                'is_valid': True,
                'validation_score': 0.9,
                'company_info': sec_data,
                'risk_level': self._calculate_risk_level(sec_data)
            }
        
        # Try Alpha Vantage second (if API key configured)
        alpha_data = self.alpha_vantage.get_company_overview(symbol_upper)
        if alpha_data:
            alpha_data = dict(alpha_data)
            alpha_data["resolver_status"] = "quote_exact"
            self.logger.info(f"✅ Alpha Vantage found: {symbol_upper} - {alpha_data['name']}")
            return {
                'is_valid': True,
                'validation_score': 0.95,  # Very high confidence for Alpha Vantage
                'company_info': alpha_data,
                'risk_level': self._calculate_risk_level(alpha_data)
            }
        
        # Try Financial Modeling Prep third (if API key configured)
        fmp_data = self.fmp.get_company_profile(symbol_upper)
        if fmp_data:
            fmp_data = dict(fmp_data)
            fmp_data["resolver_status"] = "quote_exact"
            self.logger.info(f"✅ FMP found: {symbol_upper} - {fmp_data['name']}")
            return {
                'is_valid': True,
                'validation_score': 0.9,  # High confidence for FMP
                'company_info': fmp_data,
                'risk_level': self._calculate_risk_level(fmp_data)
            }
        
        # Try Polygon.io fourth (if API key configured)
        polygon_data = self.polygon.get_ticker_details(symbol_upper)
        if polygon_data:
            polygon_data = dict(polygon_data)
            polygon_data["resolver_status"] = "quote_exact"
            self.logger.info(f"✅ Polygon found: {symbol_upper} - {polygon_data['name']}")
            return {
                'is_valid': True,
                'validation_score': 0.95,  # Very high confidence for Polygon
                'company_info': polygon_data,
                'risk_level': self._calculate_risk_level(polygon_data)
            }
        
        # Fallback to provider bridge
        self.logger.info(f"🔄 Falling back to provider bridge for: {symbol_upper}")
        return self.validate_company_provider(symbol)
    
    def validate_company_provider(self, symbol: str) -> Dict:
        """Validate company using provider bridge API."""
        current_time = time.time()

        # Reset counter every hour
        if current_time - self.last_api_reset > 3600:
            self.api_call_count = 0
            self.last_api_reset = current_time

        # Rate limiting: max 100 calls per hour
        if self.api_call_count > 100:
            logging.warning("API rate limit reached for provider validation")
            return self._fallback_validation(symbol)

        symbol_upper = symbol.upper()
        if symbol_upper in self.blocked_symbols:
            return {
                'is_valid': False,
                'validation_score': 0.0,
                'company_info': {
                    'symbol': symbol_upper,
                    'name': f"{symbol_upper} - Non-Tradeable",
                    'sector': 'BLOCKED',
                    'industry': 'Currency or Commodity',
                    'validation_method': 'blocked_symbol'
                },
                'risk_level': 'INVALID'
            }

        if symbol_upper in self.indices:
            return self._validate_index(symbol_upper, {})

        if self._is_kalshi_symbol(symbol_upper):
            return {
                'is_valid': False,
                'validation_score': 0.0,
                'company_info': {
                    'symbol': symbol_upper,
                    'name': f"{symbol_upper} - Prediction Market Ticker",
                    'sector': 'PREDICTION',
                    'industry': 'Prediction Market',
                    'validation_method': 'kalshi_ticker'
                },
                'risk_level': 'INVALID'
            }

        try:
            self.api_call_count += 1
            ticker = market_data.Ticker(symbol)

            # Get basic info
            info = ticker.info

            # Check if company exists and is actively traded
            if not info.get('regularMarketPrice'):
                # INVALID - Cache the rejection
                self.invalid_cache[symbol_upper] = {
                    'is_valid': False,
                    'company_info': {
                        'symbol': symbol_upper,
                        'name': f"{symbol_upper} - No Data/Invalid",
                        'sector': 'INVALID',
                        'industry': 'Invalid Symbol',
                        'validation_method': 'no_market_data'
                    },
                    'timestamp': current_time
                }
                return self._fallback_validation(symbol)

            resolved = get_resolver().resolve(symbol_upper)
            # Extract key information
            company_data = {
                'symbol': symbol_upper,
                'name': info.get('longName') or resolved['company_name'],
                'full_name': info.get('longName') or resolved['full_name'],
                'sector': info.get('sector') or resolved['sector'],
                'industry': info.get('industry') or resolved['industry'],
                'market_cap': info.get('marketCap', 0),
                'avg_volume': info.get('averageVolume', 0),
                'price': info.get('regularMarketPrice', 0),
                'currency': info.get('currency', 'USD'),
                'exchange': info.get('exchange', 'Unknown'),
                'is_valid': True,
                'real_ticker': True,  # Mark as real stock ticker
                'validation_method': 'provider_api',
                'timestamp': current_time
            }

            # Cache the VALID result
            self.validation_cache[symbol_upper] = company_data
            self._persist_validation_cache()

            return {
                'is_valid': True,
                'validation_score': 0.9,
                'company_info': company_data,
                'risk_level': self._calculate_risk_level(company_data)
            }

        except Exception as e:
            logging.warning(f"Provider validation failed for {symbol}: {e}")
            # INVALID - Cache the rejection
            self.invalid_cache[symbol_upper] = {
                'is_valid': False,
                'company_info': {
                    'symbol': symbol_upper,
                    'name': f"{symbol_upper} - Validation Failed",
                    'sector': 'ERROR',
                    'industry': 'Validation Error',
                    'validation_method': 'api_error'
                },
                'timestamp': current_time
            }
            return self._fallback_validation(symbol)

    def _fallback_validation(self, symbol: str) -> Dict:
        """Fallback validation using cached database"""
        symbol_upper = symbol.upper()
        current_time = time.time()

        # BLOCKED SYMBOLS - They are not tradeable stocks
        if symbol_upper in self.blocked_symbols:
            return {
                'is_valid': False,
                'validation_score': 0.0,
                'company_info': {
                    'symbol': symbol_upper,
                    'name': f"{symbol_upper} Index/Non-Tradeable",
                    'sector': 'INDEX',
                    'industry': 'Market Index or Non-Tradeable',
                    'validation_method': 'blocked_symbol'
                },
                'risk_level': 'INVALID'
            }

        if symbol_upper in self.fallback_db:
            # VALID company - Cache it
            company_data = self.fallback_db[symbol_upper].copy()
            company_data.update({
                'validation_method': 'fallback_cache',
                'timestamp': current_time,
                'is_valid': True,
                'real_ticker': True,  # Mark fallback cached symbols as real tickers
                'validation_score': company_data.get('validation_score', 0.6)
            })
            self.validation_cache[symbol_upper] = company_data

            return {
                'is_valid': True,
                'validation_score': company_data.get('validation_score', 0.6),
                'company_info': company_data,
                'risk_level': self._calculate_risk_level(company_data)
            }

        # Unverified symbol — structured metadata without UNKNOWN placeholders
        resolved = get_resolver().resolve(symbol_upper)
        company_data = {
            'symbol': symbol_upper,
            'name': resolved['company_name'],
            'full_name': resolved['full_name'],
            'sector': resolved['sector'],
            'industry': resolved['industry'],
            'market_cap': 0,
            'avg_volume': 0,
            'price': 0,
            'currency': 'USD',
            'is_valid': False,
            'validation_method': 'not_found',
            'validation_score': 0.0,
            'timestamp': current_time
        }
        self.validation_cache[symbol_upper] = company_data

        return {
            'is_valid': False,
            'validation_score': 0.0,
            'company_info': company_data,
            'risk_level': 'HIGH'
        }

    def _calculate_risk_level(self, company_data: Dict) -> str:
        """Calculate risk level based on company characteristics"""
        try:
            market_cap = float(company_data.get('market_cap') or 0.0)
        except (TypeError, ValueError):
            market_cap = 0.0
        try:
            avg_volume = float(company_data.get('avg_volume') or 0.0)
        except (TypeError, ValueError):
            avg_volume = 0.0

        # High risk if small market cap or low volume
        if market_cap < 1e9 or avg_volume < 100000:  # $1B market cap, 100k avg volume
            return 'HIGH'
        elif market_cap < 10e9 or avg_volume < 1000000:  # $10B market cap, 1M avg volume
            return 'MEDIUM'
        else:
            return 'LOW'

    def _get_all_tradable_symbols(self) -> set:
        """Get all potentially tradable symbols from our industry mapping"""
        all_symbols = set()
        for symbols in self.high_vol_industries.values():
            # Filter out only blocked symbols (allow indices to be considered)
            filtered_symbols = [s for s in symbols if s.upper() not in self.blocked_symbols]
            all_symbols.update(filtered_symbols)
        return all_symbols

    def _is_kalshi_symbol(self, symbol: str) -> bool:
        s = symbol.upper()
        if not s.startswith('KX'):
            return False
        if '-' not in s:
            return False
        return any(ch.isdigit() for ch in s)

    def fact_check_company(self, news_item: Dict, all_sectors_mode: bool = False) -> Dict:
        """Enhanced fact check using multiple data sources"""
        symbol = news_item.get('symbol', '')

        # Basic validation
        if not symbol:
            return {'is_valid': False, 'validation_score': 0}

        symbol_upper = symbol.upper()
        current_time = time.time()

        # 0. IDENTITY REGISTRY — reuse known company names across engines
        try:
            from utils.company_identity_registry import get_identity_registry
            reg = get_identity_registry()
            reg_row = reg.get(symbol_upper)
            if reg_row and reg_row.get("company_name") and reg_row.get("is_tradeable", True):
                name = str(reg_row["company_name"]).strip()
                if name and not name.startswith("$") and name.lower() not in ("unknown", "n/a"):
                    result = {
                        "is_valid": True,
                        "validation_score": 0.85,
                        "company_info": {
                            "symbol": symbol_upper,
                            "name": name,
                            "full_name": name,
                            "company_name": name,
                            "sector": reg_row.get("sector") or "Equities",
                            "industry": reg_row.get("sector") or "Equities",
                            "avg_volume": reg_row.get("avg_volume") or "N/A",
                            "validation_method": "identity_registry",
                            "resolver_status": reg_row.get("resolver_status") or "registry",
                        },
                        "risk_level": "MEDIUM",
                    }
                    if reg_row.get("last_price"):
                        result["company_info"]["price_range"] = f"${float(reg_row['last_price']):.2f}"
                    return result
        except Exception:
            pass

        # 1. BLOCKED SYMBOLS - Never trade these (currencies, commodities)
        if symbol_upper in self.blocked_symbols:
            self.logger.info(f"Blocked symbol: {symbol_upper} - not tradeable")
            return {
                'is_valid': False,
                'validation_score': 0.0,
                'company_info': {
                    'symbol': symbol_upper,
                    'name': f"{symbol_upper} - Non-Tradeable",
                    'sector': 'BLOCKED',
                    'industry': 'Currency or Commodity',
                    'validation_method': 'blocked_symbol'
                },
                'risk_level': 'INVALID'
            }

        # 2. INDICES - Can be traded under specific conditions
        if symbol_upper in self.indices:
            return self._validate_index(symbol_upper, news_item)

        # 3. VALIDATION CACHE - Recently validated symbols (skip stale negatives if registry knows name)
        if symbol_upper in self.validation_cache:
            cached_data = self.validation_cache[symbol_upper]
            if current_time - cached_data.get('timestamp', 0) < self.cache_expiry:
                skip_negative = False
                if cached_data.get('is_valid') is False:
                    try:
                        from utils.company_identity_registry import get_identity_registry
                        if get_identity_registry().company_name(symbol_upper):
                            skip_negative = True
                    except Exception:
                        pass
                if not skip_negative and cached_data.get('is_valid') is not False:
                    self.logger.info(f"Valid cache hit: {symbol_upper} - using cached validation")
                    cached_data = dict(cached_data)
                    cached_data["resolver_status"] = "cache_exact"
                    return self._normalize_fact_check({
                        'is_valid': cached_data.get('is_valid', False),
                        'validation_score': cached_data.get('validation_score', 0.0),
                        'company_info': cached_data,
                        'risk_level': self._calculate_risk_level(cached_data)
                    }, symbol_upper, news_item.get('title'))
                if not skip_negative and cached_data.get('is_valid') is False:
                    # Keep old negative behavior only when registry has no name
                    pass

        # 4. REJECTED CACHE - Recently rejected symbols
        if symbol_upper in self.rejected_cache:
            cached_data = self.rejected_cache[symbol_upper]
            if current_time - cached_data.get('timestamp', 0) < self.rejected_cache_expiry:
                try:
                    from utils.company_identity_registry import get_identity_registry
                    if get_identity_registry().company_name(symbol_upper):
                        cached_data = None
                except Exception:
                    pass
                if cached_data is not None:
                    self.logger.info(f"Rejected cache hit: {symbol_upper} - using cached rejection")
                    return {
                        'is_valid': False,
                        'validation_score': 0.0,
                        'company_info': cached_data,
                        'risk_level': 'INVALID'
                    }

        # 5. NEW SYMBOL - Use enhanced validation with multiple sources
        self.logger.info(f"New symbol: {symbol_upper} - using enhanced validation")
        result = self.validate_company_enhanced(symbol)
        return self._normalize_fact_check(result, symbol_upper, news_item.get('title'))

    def _normalize_fact_check(self, fact_check: Dict, symbol: str, title: Optional[str] = None) -> Dict:
        """Ensure company_info fields are populated with real or derived labels."""
        if not isinstance(fact_check, dict):
            return fact_check
        info = get_resolver().enrich_company_info(
            fact_check.get('company_info'), symbol, title
        )
        fact_check['company_info'] = info
        if is_placeholder(fact_check.get('risk_level')):
            fact_check['risk_level'] = 'HIGH' if not fact_check.get('is_valid') else 'MEDIUM'
        return fact_check

    def _validate_index(self, symbol: str, news_item: Dict) -> Dict:
        """Validate indices with flexible criteria based on market conditions"""
        symbol_upper = symbol.upper()
        current_time = time.time()

        # Check if recently validated
        if symbol_upper in self.validation_cache:
            cached_data = self.validation_cache[symbol_upper]
            if current_time - cached_data.get('timestamp', 0) < self.cache_expiry:
                cached_valid = bool(cached_data.get('is_valid', False))
                return {
                    'is_valid': cached_valid,
                    'validation_score': 0.8 if cached_valid else 0.2,
                    'company_info': cached_data,
                    'risk_level': 'MEDIUM' if cached_valid else 'HIGH'
                }

        try:
            import yfinance as market_data
            ticker = market_data.Ticker(symbol)

            # Get basic info
            info = ticker.info

            # Check if index exists and has trading data
            if not info.get('regularMarketPrice'):
                # Cache rejection and return
                self.rejected_cache[symbol_upper] = {
                    'is_valid': False,
                    'company_info': {
                        'symbol': symbol_upper,
                        'name': f"{symbol_upper} Index - No Trading Data",
                        'sector': 'INDEX',
                        'industry': 'Market Index',
                        'validation_method': 'no_trading_data'
                    },
                    'timestamp': current_time
                }
                return self._fallback_validation(symbol)

            # Index-specific validation criteria
            validation_score = self._calculate_index_validation_score(symbol_upper, info)

            # Make decision based on score and market conditions
            # Be more lenient with indices - they have different characteristics than stocks
            is_valid = validation_score >= 0.4  # Even lower threshold for indices

            # Extract key information
            company_data = {
                'symbol': symbol_upper,
                'name': info.get('longName', f"{symbol_upper} Index"),
                'sector': 'INDEX',
                'industry': 'Market Index',
                'market_cap': info.get('marketCap', 0),
                'avg_volume': info.get('averageVolume', 0),
                'price': info.get('regularMarketPrice', 0),
                'currency': info.get('currency', 'USD'),
                'exchange': info.get('exchange', 'Unknown'),
                'is_valid': is_valid,
                'validation_method': 'index_validation',
                'validation_score': validation_score,
                'timestamp': current_time
            }

            # Cache the result
            self.validation_cache[symbol_upper] = company_data

            return {
                'is_valid': is_valid,
                'validation_score': validation_score,
                'company_info': company_data,
                'risk_level': 'MEDIUM' if is_valid else 'HIGH'
            }

        except Exception as e:
            logging.warning(f"Index validation failed for {symbol}: {e}")
            # Cache rejection for shorter time (1 hour)
            self.rejected_cache[symbol_upper] = {
                'is_valid': False,
                'company_info': {
                    'symbol': symbol_upper,
                    'name': f"{symbol_upper} - Validation Failed",
                    'sector': 'ERROR',
                    'industry': 'Validation Error',
                    'validation_method': 'validation_error'
                },
                'timestamp': current_time
            }
            return self._fallback_validation(symbol)

    def _calculate_index_validation_score(self, symbol: str, info: Dict) -> float:
        """Calculate validation score for indices based on trading potential"""
        score = 0.0
        symbol_upper = symbol.upper()

        # Base score for existence
        if info.get('regularMarketPrice'):
            score += 0.4  # Increased base score

        # Volume criteria (more lenient for indices)
        avg_volume = info.get('averageVolume', 0)
        if avg_volume > 500000:  # 500K+ volume (reduced from 1M)
            score += 0.4
        elif avg_volume > 50000:  # 50K+ volume (reduced from 100K)
            score += 0.3
        elif avg_volume > 10000:  # 10K+ volume (new tier)
            score += 0.2

        # Market cap/price criteria (more flexible)
        price = info.get('regularMarketPrice', 0)
        if price > 5:  # Lowered from 10
            score += 0.2

        # Index-specific bonuses
        if symbol_upper == 'VIX':
            # Special handling for VIX - it often has lower volume but is highly tradeable
            score += 0.3  # Increased bonus for VIX
            if avg_volume > 10000:  # VIX with any reasonable volume
                score += 0.2
        elif symbol_upper in ['SPY', 'QQQ', 'IWM', 'SPX', 'NDX']:
            # Major indices with good liquidity
            score += 0.2

        # Less severe penalties for low volume/price
        if avg_volume < 5000:  # Increased from 10000
            score -= 0.1  # Reduced from 0.3

        # Less severe penalty for low price
        if price < 0.5:  # Only penalize very low prices
            score -= 0.1  # Reduced from 0.2

        return max(0.0, min(1.0, score))  # Clamp between 0 and 1

    def _get_industry_for_symbol(self, symbol: str) -> str:
        """Get industry for symbol (legacy method)"""
        return "Technology"  # Default fallback

    # Legacy methods for backward compatibility
    def _build_company_db(self) -> Dict:
        """Build comprehensive company database once (local aliases only — no web resolve)."""
        comprehensive_db = self.fallback_db.copy()

        # Add all symbols from high_vol_industries with company name aliases
        company_names = {
            # Tech/AI
            'AAPL': ['Apple', 'iPhone', 'iPad', 'Mac'], 'MSFT': ['Microsoft', 'Windows', 'Azure'],
            'GOOGL': ['Google', 'Alphabet', 'YouTube'], 'NVDA': ['NVIDIA', 'Nvidia'],
            'AMD': ['AMD', 'Advanced Micro Devices'], 'META': ['Meta', 'Facebook', 'Instagram'],
            'CRM': ['Salesforce'], 'ORCL': ['Oracle'], 'INTC': ['Intel'],
            'QCOM': ['Qualcomm'], 'TXN': ['Texas Instruments'], 'ADBE': ['Adobe'],
            'TSLA': ['Tesla'], 'NFLX': ['Netflix'], 'AMZN': ['Amazon'],

            # Energy
            'XOM': ['Exxon', 'ExxonMobil'], 'CVX': ['Chevron'], 'COP': ['ConocoPhillips'],
            'EOG': ['EOG Resources'], 'SLB': ['Schlumberger'], 'MPC': ['Marathon Petroleum'],
            'PSX': ['Phillips 66'], 'VLO': ['Valero'], 'OXY': ['Occidental', 'Occidental Petroleum'],
            'BP': ['BP', 'British Petroleum'],

            # Consumer/Food
            'WMT': ['Walmart'], 'HD': ['Home Depot'], 'MCD': ['McDonald', 'McDonalds'],
            'KO': ['Coca-Cola', 'Coke'], 'PEP': ['Pepsi', 'PepsiCo'], 'PG': ['Procter & Gamble', 'P&G'],
            'COST': ['Costco'], 'TGT': ['Target'], 'LOW': ['Lowes', "Lowe's"],
            'DIS': ['Disney', 'Walt Disney'], 'NKE': ['Nike'],
            'GME': ['GameStop', 'Gamestop'], 'BBY': ['Best Buy'], 'BB': ['BlackBerry'],
            'KSS': ['Kohl\'s', 'Kohls'],

            # EV/Auto
            'F': ['Ford'], 'GM': ['General Motors', 'GM'], 'TM': ['Toyota'],
            'HMC': ['Honda'], 'RIVN': ['Rivian'], 'LCID': ['Lucid', 'Lucid Motors'],

            # Biotech/Health
            'JNJ': ['Johnson & Johnson', 'J&J'], 'PFE': ['Pfizer'], 'UNH': ['UnitedHealth'],
            'ABBV': ['AbbVie'], 'LLY': ['Eli Lilly', 'Lilly'], 'TMO': ['Thermo Fisher'],
            'ABT': ['Abbott'], 'DHR': ['Danaher'], 'BMY': ['Bristol-Myers', 'Bristol Myers Squibb'],
            'AMGN': ['Amgen'], 'GILD': ['Gilead'], 'MRNA': ['Moderna'],

            # Finance
            'JPM': ['JPMorgan', 'JP Morgan'], 'BAC': ['Bank of America', 'BofA'],
            'WFC': ['Wells Fargo'], 'C': ['Citigroup', 'Citi'], 'GS': ['Goldman Sachs'],
            'MS': ['Morgan Stanley'], 'BLK': ['BlackRock'], 'SCHW': ['Charles Schwab', 'Schwab'],
            'AXP': ['American Express', 'Amex'], 'USB': ['US Bank', 'U.S. Bank'],

            # Mining/Metals
            'FCX': ['Freeport', 'Freeport-McMoRan'], 'NEM': ['Newmont'], 'GOLD': ['Barrick Gold'],
            'AA': ['Alcoa'], 'X': ['US Steel', 'U.S. Steel'], 'CLF': ['Cleveland-Cliffs'],

            # Crypto
            'COIN': ['Coinbase'], 'MSTR': ['MicroStrategy'], 'RIOT': ['Riot Platforms', 'Riot Blockchain'],
            'MARA': ['Marathon Digital'], 'SQ': ['Block', 'Square'], 'PYPL': ['PayPal'],

            # Other major companies
            'BRK.B': ['Berkshire', 'Berkshire Hathaway', 'Buffett'], 'ATVI': ['Activision', 'Activision Blizzard'],
            'MRVL': ['Marvell', 'Marvell Technology'], 'BHC': ['Bausch', 'Bausch Health'],
        }

        for industry, symbols in self.high_vol_industries.items():
            for symbol in symbols:
                if symbol not in comprehensive_db:
                    aliases = company_names.get(symbol, [])
                    comprehensive_db[symbol] = {
                        'name': aliases[0] if aliases else symbol,
                        'sector': self._get_sector_from_industry(industry),
                        'industry': industry,
                        'aliases': aliases,
                    }

        for symbol, aliases in company_names.items():
            if symbol not in comprehensive_db:
                comprehensive_db[symbol] = {
                    'name': aliases[0] if aliases else symbol,
                    'sector': 'Equities',
                    'industry': 'Equities',
                    'aliases': aliases,
                }

        return comprehensive_db

    @property
    def company_db(self):
        """Cached company database (built once at init)."""
        if not getattr(self, "_company_db", None):
            self._company_db = self._build_company_db()
        return self._company_db

    def _get_sector_from_industry(self, industry: str) -> str:
        """Map industry to sector"""
        industry_sector_map = {
            'Tech/AI': 'Technology',
            'Energy': 'Energy',
            'Consumer/Food': 'Consumer',
            'EV/Auto': 'Automotive',
            'Biotech/Health': 'Healthcare',
            'Politics/Finance': 'Finance',
            'Mining/Metals': 'Mining',
            'Crypto/Blockchain': 'Technology'
        }
        return industry_sector_map.get(industry, 'Equities')

    def get_industry_symbols(self, industry: str) -> List[str]:
        """Get all symbols for a specific industry"""
        return self.high_vol_industries.get(industry, [])

    def get_all_industries(self) -> List[str]:
        """Get all available industries"""
        return list(self.high_vol_industries.keys())

    def get_company_industry(self, symbol: str) -> Optional[str]:
        """Get the industry for a specific company"""
        company_info = self.company_db.get(symbol.upper())
        return company_info.get('industry') if company_info else None

    def get_high_volume_symbols(self) -> List[str]:
        """Get all high volume symbols across industries"""
        high_vol_symbols = []
        for symbols in self.high_vol_industries.values():
            # Filter out only blocked symbols (allow indices to be considered)
            filtered_symbols = [s for s in symbols if s.upper() not in self.blocked_symbols]
            high_vol_symbols.extend(filtered_symbols)
        return list(set(high_vol_symbols))  # Remove duplicates

    def is_real_company(self, symbol: str) -> bool:
        """Check if symbol represents a real company"""
        symbol_upper = symbol.upper()
        current_time = time.time()

        # BLOCKED SYMBOLS - They are not tradeable stocks
        if symbol_upper in self.blocked_symbols:
            return False

        # INDICES - Check if they meet trading criteria
        if symbol_upper in self.indices:
            # For indices, check if they have trading potential
            if symbol_upper in self.validation_cache:
                cached_data = self.validation_cache[symbol_upper]
                if current_time - cached_data.get('timestamp', 0) < self.cache_expiry:
                    return cached_data.get('is_valid', False)

            # Check if index has trading data
            try:
                import yfinance as market_data
                ticker = market_data.Ticker(symbol)
                info = ticker.info
                return info.get('regularMarketPrice', 0) > 0 and info.get('averageVolume', 0) > 10000
            except:
                return False

        # Check rejected cache
        if symbol_upper in self.rejected_cache:
            cached_data = self.rejected_cache[symbol_upper]
            if current_time - cached_data.get('timestamp', 0) < self.rejected_cache_expiry:
                return False

        # Check valid cache
        if symbol_upper in self.validation_cache:
            cached_data = self.validation_cache[symbol_upper]
            if current_time - cached_data.get('timestamp', 0) < self.cache_expiry:
                return cached_data.get('is_valid', False)

        # Check fallback database
        return symbol_upper in self.fallback_db

    def get_company_info(self, symbol: str) -> Optional[Dict]:
        """Get detailed company information"""
        cached_data = self.validation_cache.get(symbol.upper())
        if cached_data:
            return cached_data
        return self.fallback_db.get(symbol.upper())

    def get_cache_statistics(self) -> Dict:
        """Get cache performance statistics"""
        current_time = time.time()

        valid_count = len(self.validation_cache)
        invalid_count = len(self.rejected_cache)
        permanent_count = len(self.blocked_symbols) + len(self.indices)

        # Count expired cache entries
        expired_valid = sum(1 for data in self.validation_cache.values()
                          if current_time - data.get('timestamp', 0) >= self.cache_expiry)
        expired_invalid = sum(1 for data in self.rejected_cache.values()
                            if current_time - data.get('timestamp', 0) >= self.rejected_cache_expiry)

        return {
            'valid_companies_cached': valid_count,
            'invalid_symbols_cached': invalid_count,
            'blocked_symbols': len(self.blocked_symbols),
            'tradeable_indices': len(self.indices),
            'expired_valid_entries': expired_valid,
            'expired_invalid_entries': expired_invalid,
            'total_cache_size': valid_count + invalid_count + permanent_count,
            'cache_hit_rate': self._calculate_cache_hit_rate()
        }

    def _calculate_cache_hit_rate(self) -> float:
        """Calculate cache hit rate (simplified)"""
        # This is a simplified calculation - in a real system you'd track actual hits
        total_requests = len(self.validation_cache) + len(self.rejected_cache)
        if total_requests == 0:
            return 0.0
        return min(0.95, (len(self.validation_cache) / total_requests) * 0.8)

    def clear_expired_cache(self) -> int:
        """Clear expired cache entries and return count of cleared items"""
        current_time = time.time()
        cleared_count = 0

        # Clear expired valid cache
        expired_valid = [symbol for symbol, data in self.validation_cache.items()
                        if current_time - data.get('timestamp', 0) >= self.cache_expiry]
        for symbol in expired_valid:
            del self.validation_cache[symbol]
            cleared_count += 1

        # Clear expired rejected cache
        expired_invalid = [symbol for symbol, data in self.rejected_cache.items()
                          if current_time - data.get('timestamp', 0) >= self.rejected_cache_expiry]
        for symbol in expired_invalid:
            del self.rejected_cache[symbol]
            cleared_count += 1

        return cleared_count
