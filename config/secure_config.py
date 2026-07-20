"""
============================================================
PHASMA AI - SECURE ENVIRONMENT LOADER
============================================================
Loads all API keys from .env file securely
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

class PhasmaConfig:
    """Secure configuration loader for Phasma AI"""
    
    def __init__(self):
        # Load .env file
        env_path = Path('.env')
        if env_path.exists():
            load_dotenv()
            print("✅ Loaded environment variables from .env")
        else:
            print("⚠️  .env file not found")
        
        # Load all configurations
        self._load_news_apis()
        self._load_market_data()
        self._load_social_apis()
        self._load_system_config()
        self._load_security()
    
    def _load_news_apis(self):
        """Load news API keys"""
        self.world_news_api_key = os.getenv('WORLD_NEWS_API_KEY')
        self.gnews_api_key = os.getenv('GNEWS_API_KEY')
        self.mediastack_api_key = os.getenv('MEDIASTACK_API_KEY')
        self.currents_api_key = os.getenv('CURRENTS_API_KEY')
        
        # Validate news APIs
        self.news_apis_loaded = all([
            self.world_news_api_key,
            self.gnews_api_key,
            self.mediastack_api_key,
            self.currents_api_key
        ])
    
    def _load_market_data(self):
        """Load market data APIs"""
        self.polygon_api_key = os.getenv('POLYGON_API_KEY')
        self.alpha_vantage_key = os.getenv('ALPHA_VANTAGE_KEY')
        self.finnhub_api_key = os.getenv('FINNHUB_API_KEY')
        self.fmp_api_key = os.getenv('FMP_API_KEY')
        
        # Free sources (no keys needed)
        self.yahoo_finance_enabled = True
        self.sec_edgar_enabled = True
    
    def _load_social_apis(self):
        """Load social media APIs"""
        self.telegram_bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.telegram_chat_id = os.getenv('TELEGRAM_CHAT_ID')
        self.reddit_client_id = os.getenv('REDDIT_CLIENT_ID')
        self.reddit_secret = os.getenv('REDDIT_SECRET')
        self.reddit_user_agent = os.getenv('REDDIT_USER_AGENT')
        self.stocktwits_token = os.getenv('STOCKTWITS_ACCESS_TOKEN')
        
        # Government API
        self.sam_gov_api_key = os.getenv('SAM_GOV_API_KEY')
        
        # Kalshi for prediction markets
        self.kalshi_api_key = os.getenv('KALSHI_API_KEY')
    
    def _load_system_config(self):
        """Load system configuration"""
        self.environment = os.getenv('ENVIRONMENT', 'development')
        self.log_level = os.getenv('LOG_LEVEL', 'INFO')
        self.log_file = os.getenv('LOG_FILE', './logs/phasma_ai.log')
        
        # Feature flags
        self.feature_execution_checks = os.getenv('FEATURE_EXECUTION_CHECKS_ENABLED', 'true').lower() == 'true'
        self.feature_paper_mode_only = os.getenv('FEATURE_PAPER_MODE_ONLY', 'true').lower() == 'true'
        self.feature_human_gate = os.getenv('FEATURE_HUMAN_GATE_ENABLED', 'true').lower() == 'true'
        self.feature_rollback = os.getenv('FEATURE_ROLLBACK_ENABLED', 'false').lower() == 'true'
        
        # Trading config
        self.default_strategy = os.getenv('DEFAULT_STRATEGY', 'penny_moonshot')
        self.max_position_size = int(os.getenv('MAX_POSITION_SIZE', '10000'))
        self.default_slippage_cap = float(os.getenv('DEFAULT_SLIPPAGE_CAP', '0.01'))
        self.min_market_cap = int(os.getenv('MIN_MARKET_CAP', '10000000'))
        self.max_market_cap = int(os.getenv('MAX_MARKET_CAP', '500000000'))
        
        # Database
        self.sqlite_db_path = os.getenv('SQLITE_DATABASE_PATH', './data/phasma_ai.db')
        self.database_url = os.getenv('DATABASE_URL', f'sqlite:///{self.sqlite_db_path}')
    
    def _load_security(self):
        """Load security configuration"""
        self.jwt_secret = os.getenv('JWT_SECRET', 'phasma_ai_jwt_secret')
        self.encryption_key = os.getenv('ENCRYPTION_KEY', 'phasma_ai_encryption_key_32_chars')
        
        # Monitoring
        self.slack_webhook = os.getenv('SLACK_WEBHOOK_URL')
        
        # RSS feeds (no keys needed)
        self.rss_feeds = {
            'seeking_alpha': 'https://seekingalpha.com/feed.xml',
            'marketwatch': 'https://www.marketwatch.com/rss/topstories',
            'benzinga': 'https://www.benzinga.com/feed',
            'yahoo_finance': 'https://finance.yahoo.com/news/rssindex'
        }
        
        # SEC EDGAR
        self.sec_edgar_base = 'https://www.sec.gov'
        self.sec_edgar_filings = 'https://www.sec.gov/cgi-bin/browse-edgar'
    
    def validate_all(self):
        """Validate all required configurations"""
        errors = []
        warnings = []
        
        # Check news APIs
        if not self.news_apis_loaded:
            errors.append("Some news API keys are missing")
        
        # Check security for production
        if self.environment == 'production':
            if self.jwt_secret == 'phasma_ai_jwt_secret':
                errors.append("JWT secret must be changed in production")
            if self.encryption_key == 'phasma_ai_encryption_key_32_chars':
                errors.append("Encryption key must be changed in production")
        
        # Check optional APIs
        if not self.telegram_bot_token:
            warnings.append("Telegram bot token not set - notifications disabled")
        
        if not self.polygon_api_key:
            warnings.append("Polygon API key not set - using free data sources")
        
        return errors, warnings

    def get(self, key, default=None):
        """Get configuration value with dot-notation support."""
        value = self
        for part in str(key).split('.'):
            if isinstance(value, dict):
                if part not in value:
                    return default
                value = value[part]
            elif hasattr(value, part):
                value = getattr(value, part)
            else:
                return default
        return value
    
    def print_status(self):
        """Print configuration status"""
        print("\n" + "="*80)
        print("🔐 PHASMA AI - SECURE CONFIGURATION STATUS")
        print("="*80)
        
        print(f"\n📊 Environment: {self.environment.upper()}")
        print(f"📈 Default Strategy: {self.default_strategy}")
        print(f"💰 Max Position: ${self.max_position_size:,}")
        print(f"📉 Slippage Cap: {self.default_slippage_cap:.1%}")
        
        print("\n🔑 API Keys Status:")
        
        # News APIs
        news_status = "✅ All Loaded" if self.news_apis_loaded else "❌ Missing Keys"
        print(f"  📰 News APIs: {news_status}")
        
        # Individual status
        apis = [
            ("World News", self.world_news_api_key),
            ("GNews", self.gnews_api_key),
            ("MediaStack", self.mediastack_api_key),
            ("Currents", self.currents_api_key),
            ("Polygon", self.polygon_api_key),
            ("Alpha Vantage", self.alpha_vantage_key),
            ("Telegram", self.telegram_bot_token),
            ("Reddit", self.reddit_client_id),
            ("SAM Gov", self.sam_gov_api_key),
            ("Kalshi", self.kalshi_api_key)
        ]
        
        for name, key in apis:
            status = "✅" if key else "❌"
            print(f"    {status} {name}")
        
        print("\n⚙️ Feature Flags:")
        print(f"  • Execution Checks: {'✅' if self.feature_execution_checks else '❌'}")
        print(f"  • Paper Mode Only: {'✅' if self.feature_paper_mode_only else '❌'}")
        print(f"  • Human Gate: {'✅' if self.feature_human_gate else '❌'}")
        print(f"  • Rollback: {'✅' if self.feature_rollback else '❌'}")
        
        print("\n📡 Data Sources:")
        data_sources = [
            ("Yahoo Finance", self.yahoo_finance_enabled),
            ("SEC EDGAR", self.sec_edgar_enabled),
            ("RSS Feeds", len(self.rss_feeds))
        ]
        
        for name, status in data_sources:
            if isinstance(status, bool):
                icon = "✅" if status else "❌"
                print(f"  • {icon} {name}")
            else:
                print(f"  • ✅ {name}: {status} feeds")
        
        # Validate
        errors, warnings = self.validate_all()
        
        if errors:
            print("\n❌ ERRORS:")
            for error in errors:
                print(f"  • {error}")
        
        if warnings:
            print("\n⚠️  WARNINGS:")
            for warning in warnings:
                print(f"  • {warning}")
        
        if not errors and not warnings:
            print("\n✅ All configurations valid!")
        
        print("\n" + "="*80)
        
        return len(errors) == 0

# Create singleton instance
config = PhasmaConfig()

# Export configuration
__all__ = ['config', 'PhasmaConfig']

if __name__ == "__main__":
    # Test configuration
    success = config.print_status()
    
    if success:
        print("\n🎉 Configuration is ready!")
    else:
        print("\n⚠️  Please fix configuration errors before proceeding.")
