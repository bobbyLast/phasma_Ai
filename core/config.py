"""
Phasma AI - Configuration Management
Centralized configuration system for all Phasma AI components
"""

import json
import os

from core.execution.execution_modes import (
    format_execution_startup_message,
    normalize_execution_config,
)
from core.execution.paper_readiness_guard import normalize_paper_trading_safety

class PhasmaConfig:
    """Enhanced configuration management for Phasma AI"""

    def __init__(self, config_path = None):
        """Initialize configuration system"""
        self.config_path = config_path or "config.json"
        self.data = self._load_config()
        self.data["execution"] = normalize_execution_config(self.data)
        self.data["paper_trading_safety"] = normalize_paper_trading_safety(self.data)
        self._execution_startup_message = format_execution_startup_message(self.data)

    def _load_config(self):
        """Load configuration from file or create default"""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                print(f"Warning: Could not load config from {self.config_path}: {e}")
                return self._get_default_config()
        else:
            return self._get_default_config()

    def _get_default_config(self):
        """Get default configuration"""
        return {
            # Core Trading Settings
            "bankroll": 2000,  # Level 2 account maximum
            "pop_threshold": 0.5,  # Lowered from 0.7 to allow more trades
            "risk_per_trade": 0.01,  # 1% per trade
            "max_drawdown": 0.1,     # 10% max drawdown
            "daily_loss_limit": 0.02, # 2% daily loss limit
            "max_concurrent_trades": 5,  # Increased to allow more positions

            # System Settings
            "webull_level2_enabled": True,
            "news_apis_enabled": True,
            "kalshi_enabled": True,
            "crypto_enabled": True,
            "telegram_enabled": True,
            "debug_mode": False,

            # Data Sources (REAL-TIME ONLY!)
            "data_sources": [
                "finnhub",  # REAL-TIME NEWS - TOP PRIORITY!
                # "saurav_newsapi",  # DISABLED - Returns 3.5 year old cached news from May 2022!
                "reuters_rss",  # Live feed
                "cnbc_rss",  # Live feed
                "bbc_rss",  # Live feed
                "reddit_wsb",  # Live posts
                "thenews_api",
                "marketaux",
                "yahoo_rss",
                "x_search",
                "etherscan"
            ],

            # API Keys and Endpoints
            "apis": {
                "saurav_newsapi": "https://saurav.tech/NewsAPI/top-headlines/category/business/us.json",
                "thenews_api": "https://api.thenewsapi.com/v1/news/top?locale=us&categories=finance",
                "marketaux": "https://api.marketaux.com/v1/news/all?symbols={symbol}&filter_entities=true",
                "yahoo_rss": "https://feeds.finance.yahoo.com/rss/2.0/headline?s={symbol}",
                "reuters_rss": "https://www.reuters.com/arc/outboundfeeds/newsroom/all/?outputType=xml",
                "bbc_rss": "http://feeds.bbci.co.uk/news/business/rss.xml",
                "cnbc_rss": "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=100003114",
                "reddit_wsb": "https://www.reddit.com/r/wallstreetbets/.rss",
                # REAL Company Data APIs (all currently working)
                "alpha_vantage": {
                    "api_key": "YOUR_ALPHA_VANTAGE_KEY",  # Get from https://www.alphavantage.co/support/#api-key
                    "enabled": False,  # Set to True when API key is configured
                    "free_tier": "5 calls/minute"
                },
                "financial_modeling_prep": {
                    "api_key": "YOUR_FMP_KEY",  # Get from https://site.financialmodelingprep.com/developer/docs
                    "enabled": False,  # Set to True when API key is configured
                    "free_tier": "250 calls/day"
                },
                "polygon_io": {
                    "api_key": "YOUR_POLYGON_KEY",  # Get from https://polygon.io/
                    "enabled": False,  # Set to True when API key is configured
                    "free_tier": "5 calls/minute"
                },
                "sec_edgar": {
                    "url": "https://www.sec.gov/files/edgar",
                    "enabled": True,  # Always enabled (free)
                    "free_tier": "Unlimited"
                }
            },

            # Risk Management
            "risk": {
                "stop_loss_pct": 0.1,      # 10% stop loss
                "take_profit_pct": 1.0,    # 100% take profit
                "trailing_stop": True,
                "vix_adjustment": True,    # Adjust risk based on VIX
                "correlation_limit": 0.7   # Max correlation between positions
            },

            # Trading Parameters
            "trading": {
                "min_option_price": 0.1,   # Minimum option premium
                "max_option_price": 10.0,  # Maximum option premium
                "preferred_dte": [7, 30],  # Days to expiration preference
                "strike_selection": "atm", # ATM, ITM, OTM
                "order_type": "limit",     # Market or limit orders
                "time_in_force": "day",    # Day or GTC
                "all_sectors_mode": True,    # ENABLE: Scan all sectors, not just AI
                "ai_focus_only": False,      # DISABLE: Don't restrict to AI only
                "min_options_volume": 100,   # LOWERED: More realistic (was 5000)
                "min_implied_volatility": 20.0,  # LOWERED: More realistic (was 50.0)
                "industry_scan_limit": 7     # Scan more industries for diversity
            },

            # News Analysis
            "news": {
                "sentiment_threshold": 0.05, # Lowered from 0.1 to allow more signals
                "catalyst_keywords": [
                    "surge", "deal", "partnership", "breakout", "earnings",
                    "soar", "plunge", "moon", "rocket", "pump", "buzz"
                ],
                "scan_interval_minutes": 5,
                "max_articles_per_source": 15  # Increased to get more news
            },

            # Performance Tracking
            "performance": {
                "save_state_interval": 60,  # Minutes
                "log_trades": True,
                "benchmark_symbol": "SPY",
                "tracking_enabled": True
            },

            # Execution (safe defaults — no live trading)
            "execution": {
                "mode": "ALERT_ONLY",
                "allow_live_trading": False,
                "kalshi_execution_enabled": False,
                "require_price": True,
                "require_valid_symbol": True,
                "require_fresh_data": True,
                "max_data_age_seconds": 900,
            },

            "paper_trading_safety": {
                "enabled": True,
                "max_orders_per_cycle": 3,
                "max_orders_per_day": 10,
                "max_notional_per_order": 100,
                "max_total_daily_notional": 500,
                "cooldown_minutes_per_symbol": 120,
                "stock_only": True,
                "block_low_confidence_below": 65,
                "require_outcome_tracking": True,
                "require_fresh_price": True,
                "kill_switch": False,
            },

            "paper_trading_safety": {
                "enabled": True,
                "max_orders_per_cycle": 3,
                "max_orders_per_day": 10,
                "max_notional_per_order": 100,
                "max_total_daily_notional": 500,
                "cooldown_minutes_per_symbol": 120,
                "stock_only": True,
                "block_low_confidence_below": 65,
                "require_outcome_tracking": True,
                "require_fresh_price": True,
                "kill_switch": False,
            },

            # Assets Configuration - REAL MARKET SECTORS ONLY
            "assets": {
                "sector_watchlist": {
                    "AI": {
                        "keywords": ["ai", "artificial intelligence", "machine learning", "neural", "automation", "tech"],
                        "focus": "AI and Technology sector - Real companies only",
                        "potential": "3-10x",
                        "symbols": ["NVDA", "MSFT", "GOOGL", "AMD", "CRM", "PLTR", "SNOW", "CRWD", "AI", "SOUN", "NOW", "WDAY", "DDOG", "PATH", "RGTI", "BBAI"],
                        "weight": 1.0
                    },
                    "ENERGY": {
                        "keywords": ["oil", "energy", "crude", "gas", "pipeline", "refinery", "commodity"],
                        "focus": "Energy and Oil sector - Real companies only",
                        "potential": "2-5x",
                        "symbols": ["XOM", "CVX", "COP", "EOG", "PXD", "OXY", "MPC", "VLO"],
                        "weight": 0.8
                    },
                    "FOOD": {
                        "keywords": ["food", "beverage", "restaurant", "retail", "consumer", "grocery"],
                        "focus": "Food and Consumer sector - Real companies only",
                        "potential": "1-3x",
                        "symbols": ["MCD", "SBUX", "KO", "PEP", "WMT", "TGT", "HD", "LOW", "COST", "YUM"],
                        "weight": 0.7
                    },
                    "BIOTECH": {
                        "keywords": ["fda", "clinical", "trial", "drug", "biotech", "pharma", "vaccine"],
                        "focus": "Biotechnology and Healthcare sector - Real companies only",
                        "potential": "3-15x",
                        "symbols": ["GILD", "AMGN", "BIIB", "VRTX", "MRNA", "REGN", "ISRG", "DXCM", "TEM"],
                        "weight": 0.9
                    },
                    "CONSTRUCTION": {
                        "keywords": ["construction", "infrastructure", "building", "materials", "engineering"],
                        "focus": "Construction and Industrial sector - Real companies only",
                        "potential": "2-5x",
                        "symbols": ["CAT", "DE", "CMI", "PCAR", "OSK", "TEX", "MTW", "ALG"],
                        "weight": 0.6
                    },
                    "MINING": {
                        "keywords": ["mining", "metal", "gold", "copper", "commodity", "mineral"],
                        "focus": "Mining and Materials sector - Real companies only",
                        "potential": "2-8x",
                        "symbols": ["FCX", "NEM", "ABX", "GOLD", "RIO", "BHP", "VALE", "SCCO"],
                        "weight": 0.7
                    },
                    "ECOM": {
                        "keywords": ["ecommerce", "retail", "online", "shopping", "delivery", "marketplace"],
                        "focus": "E-commerce and Retail sector - Real companies only",
                        "potential": "2-5x",
                        "symbols": ["AMZN", "EBAY", "ETSY", "SHOP", "WMT", "TGT", "HD", "LOW"],
                        "weight": 0.8
                    },
                    "GAMING": {
                        "keywords": ["gaming", "esports", "console", "mobile", "entertainment", "streaming"],
                        "focus": "Gaming and Entertainment sector - Real companies only",
                        "potential": "3-8x",
                        "symbols": ["ATVI", "EA", "TTWO", "NTDOY", "UBSFY", "SONY", "RBLX", "U"],
                        "weight": 0.7
                    },
                    "CRYPTO": {
                        "keywords": ["bitcoin", "ethereum", "crypto", "cryptocurrency", "blockchain", "btc", "eth", "mining", "digital currency", "web3", "defi"],
                        "focus": "Cryptocurrency and Blockchain sector - Crypto-exposed stocks",
                        "potential": "5-20x",
                        "symbols": ["MSTR", "COIN", "MARA", "RIOT", "CLSK", "HUT", "BITF", "CIFR", "SQ", "PYPL", "HOOD"],
                        "weight": 1.0
                    }
                },
                "crypto_symbols": ["BTC", "ETH", "MSTR", "COIN", "MARA", "RIOT"],
                "kalshi_events": ["Best AI 2025", "Election 2024", "Fed Rate Decision"]
            }
        }

    def get(self, key, default = None):
        """Get configuration value with dot notation support"""
        keys = key.split('.')
        value = self.data

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    def set(self, key, value):
        """Set configuration value with dot notation support"""
        keys = key.split('.')
        data = self.data

        for k in keys[:-1]:
            if k not in data:
                data[k] = {}
            data = data[k]

        data[keys[-1]] = value

    def update(self, updates):
        """Update multiple configuration values"""
        def merge_dicts(original, updates):
            """Recursively merge dictionaries"""
            for key, value in updates.items():
                if isinstance(value, dict) and key in original and isinstance(original[key], dict):
                    merge_dicts(original[key], value)
                else:
                    original[key] = value
            return original

        self.data = merge_dicts(self.data, updates)

    def save(self):
        """Save configuration to file"""
        try:
            with open(self.config_path, 'w') as f:
                json.dump(self.data, f, indent=4)
            print(f"✅ Configuration saved to {self.config_path}")
        except IOError as e:
            print(f"❌ Error saving configuration: {e}")

    def get_api_url(self, api_name, **kwargs):
        """Get formatted API URL"""
        template = self.get(f"apis.{api_name}", "")
        if not template:
            return ""

        # Format URL with parameters
        for key, value in kwargs.items():
            template = template.replace(f"{{{key}}}", str(value))

        return template

    def is_enabled(self, component):
        """Check if component is enabled"""
        return self.get(f"{component}_enabled", False)

    @property
    def max_discovery(self) -> bool:
        return bool(self.get("max_discovery", False))

    def apply_max_discovery_overrides(self) -> bool:
        """When max_discovery is on, enable discovery subsystems in-memory."""
        if not self.max_discovery:
            return False

        self.data["options_enabled"] = True
        underground = self.data.setdefault("underground_discovery", {})
        if isinstance(underground, dict):
            underground["enabled"] = True

        profit = self.data.setdefault("profit_maximization", {})
        if isinstance(profit, dict):
            profit["enabled"] = True
        else:
            self.data["profit_maximization"] = {"enabled": True}

        return True

    def get_watchlist(self):
        """Get asset watchlist"""
        return self.get("assets.watchlist", [])

    def get_risk_params(self):
        """Get risk management parameters"""
        return self.get("risk", {})

    def get_execution_config(self):
        """Get normalized execution configuration."""
        self.data["execution"] = normalize_execution_config(self.data)
        return self.data["execution"]

    def get_paper_trading_safety(self):
        """Get normalized paper trading safety configuration."""
        self.data["paper_trading_safety"] = normalize_paper_trading_safety(self.data)
        return self.data["paper_trading_safety"]

    def get_paper_trading_safety(self):
        """Get normalized paper trading safety configuration."""
        self.data["paper_trading_safety"] = normalize_paper_trading_safety(self.data)
        return self.data["paper_trading_safety"]

    def get_execution_mode(self):
        return self.get_execution_config().get("mode", "ALERT_ONLY")

    def get_execution_startup_message(self) -> str:
        """Log-friendly summary of execution.mode vs legacy paper_trading.enabled."""
        self.data["execution"] = normalize_execution_config(self.data)
        self._execution_startup_message = format_execution_startup_message(self.data)
        return self._execution_startup_message

    def get_trading_params(self):
        """Get trading parameters"""
        return self.get("trading", {})

    def to_dict(self):
        """Export configuration as dictionary"""
        return self.data.copy()

# Configuration validation
def validate_config(config):
    """Validate configuration and return list of issues"""
    issues = []

    # Check bankroll
    bankroll = config.get("bankroll", 0)
    if bankroll < 1000:
        issues.append("Bankroll too low (minimum $1,000 recommended)")

    # Check risk parameters
    risk_per_trade = config.get("risk_per_trade", 0)
    if risk_per_trade > 0.05:  # 5%
        issues.append("Risk per trade too high (maximum 5% recommended)")

    # Check POP threshold
    pop_threshold = config.get("pop_threshold", 0)
    if pop_threshold < 0.5 or pop_threshold > 0.9:
        issues.append("POP threshold should be between 0.5 and 0.9")

    # Check data sources
    data_sources = config.get("data_sources", [])
    if not data_sources:
        issues.append("No data sources configured")

    return issues

# Test configuration system
def test_config():
    """Test configuration system"""
    print("🧪 Testing Phasma Configuration System")

    # Test default config
    config = PhasmaConfig()

    print(f"Bankroll: ${config.get('bankroll')}")
    print(f"POP Threshold: {config.get('pop_threshold')}")
    print(f"Risk Per Trade: {config.get('risk_per_trade')}")
    print(f"Data Sources: {len(config.get('data_sources', []))}")
    print(f"Watchlist: {config.get('assets.watchlist', [])}")

    # Test API URLs
    amd_api = config.get_api_url("marketaux", symbol="AMD")
    print(f"Marketaux API for AMD: {amd_api}")

    # Test configuration updates
    config.set("bankroll", 50000)
    config.set("pop_threshold", 0.75)
    config.save()

    print("✅ Configuration test complete!")

if __name__ == "__main__":
    test_config()
