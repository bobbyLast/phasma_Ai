"""
============================================================
PHASMA AI - ENVIRONMENT CONFIGURATION
============================================================
Secure management of all API keys and configurations
"""

import os
from pathlib import Path

# Create .env file template
env_template = """
# PHASMA AI - ENVIRONMENT VARIABLES
# =====================================

# NEWS API KEYS
# =============

# World News API
WORLD_NEWS_API_KEY=370a193337cf422b9e4df80b0d37613d

# GNews API
GNEWS_API_KEY=ae4d97e15c89d379dcc9c96174a39ed4

# MediaStack API
MEDIASTACK_API_KEY=ca12fc893f4d0ed4e4b3c7d4e72808b9

# Currents API
CURRENTS_API_KEY=AABfmJz5G8qskiJGNSZxcDXNkzySLreGywQKVloobm-QnEaj

# MARKET DATA API KEYS
# ===================

# Yahoo Finance (Free - no key needed for basic)
YAHOO_FINANCE_ENABLED=true

# IEX Cloud (for production)
IEX_CLOUD_API_KEY=your_iex_key_here
IEX_CLOUD_SANDBOX=true

# Alpha Vantage (alternative)
ALPHA_VANTAGE_API_KEY=your_alpha_vantage_key_here

# BROKER API KEYS
# ===============

# Alpaca (for paper/live trading)
ALPACA_API_KEY=your_alpaca_key_here
ALPACA_API_SECRET=your_alpaca_secret_here
ALPACA_BASE_URL=https://paper-api.alpaca.markets  # Change to live for production

# Interactive Brokers (alternative)
IBKR_HOST=127.0.0.1
IBKR_PORT=7497
IBKR_CLIENT_ID=1

# DATABASE CONFIGURATION
# =====================

# PostgreSQL (for production)
DATABASE_URL=postgresql://user:password@localhost/phasma_ai
DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_NAME=phasma_ai
DATABASE_USER=phasma_user
DATABASE_PASSWORD=secure_password_here

# SQLite (for development)
SQLITE_DATABASE_PATH=./data/phasma_ai.db

# SYSTEM CONFIGURATION
# ===================

# Environment
ENVIRONMENT=development  # development, staging, production

# Logging
LOG_LEVEL=INFO
LOG_FILE=./logs/phasma_ai.log

# Feature Flags
FEATURE_EXECUTION_CHECKS_ENABLED=true
FEATURE_PAPER_MODE_ONLY=true
FEATURE_HUMAN_GATE_ENABLED=true
FEATURE_ROLLBACK_ENABLED=false

# Trading Configuration
DEFAULT_STRATEGY=penny_moonshot
MAX_POSITION_SIZE=10000
DEFAULT_SLIPPAGE_CAP=0.01
MIN_MARKET_CAP=10000000
MAX_MARKET_CAP=500000000

# SECURITY
# ========

# JWT Secret for authentication
JWT_SECRET=your_jwt_secret_here_make_it_long_and_random

# Encryption key for sensitive data
ENCRYPTION_KEY=your_32_character_encryption_key_here

# API Rate Limits
API_RATE_LIMIT_PER_MINUTE=100
NEWS_API_RATE_LIMIT_PER_MINUTE=60

# MONITORING
# ==========

# Slack webhook for alerts
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK

# PagerDuty (for critical alerts)
PAGERDUTY_API_KEY=your_pagerduty_key_here

# DataDog (for metrics)
DATADOG_API_KEY=your_datadog_key_here
DATADOG_APP_KEY=your_datadog_app_key_here

# EXTERNAL SERVICES
# =================

# SEC EDGAR (no key needed)
SEC_EDGAR_BASE_URL=https://www.sec.gov
SEC_EDGAR_FILINGS_URL=https://www.sec.gov/cgi-bin/browse-edgar

# RSS Feeds (no keys needed)
SEEKING_ALPHA_RSS=https://seekingalpha.com/feed.xml
MARKETWATCH_RSS=https://www.marketwatch.com/rss/topstories
BENZINGA_RSS=https://www.benzinga.com/feed

# Options Data (paid services - placeholder)
UNUSUAL_WHALES_API_KEY=your_unusual_whales_key_here
FLOWALGO_API_KEY=your_flowalgo_key_here
"""

# Create .env file
def create_env_file():
    """Create .env file from template"""
    env_path = Path('.env')
    
    if not env_path.exists():
        with open('.env', 'w') as f:
            f.write(env_template)
        print("✅ Created .env file with your API keys")
    else:
        print("⚠️  .env file already exists")
    
    # Set proper permissions
    os.chmod('.env', 0o600)

# Create environment loader
def load_environment():
    """Load environment variables"""
    from dotenv import load_dotenv
    
    # Load .env file
    load_dotenv()
    
    # Validate required keys
    required_keys = [
        'WORLD_NEWS_API_KEY',
        'GNEWS_API_KEY',
        'MEDIASTACK_API_KEY',
        'CURRENTS_API_KEY'
    ]
    
    missing_keys = []
    for key in required_keys:
        if not os.getenv(key):
            missing_keys.append(key)
    
    if missing_keys:
        print(f"⚠️  Missing environment variables: {', '.join(missing_keys)}")
    else:
        print("✅ All required API keys loaded")
    
    return missing_keys

# Create configuration class
class Config:
    """Configuration class for Phasma AI"""
    
    def __init__(self):
        self.load_from_env()
    
    def load_from_env(self):
        """Load configuration from environment"""
        # News APIs
        self.world_news_api_key = os.getenv('WORLD_NEWS_API_KEY')
        self.gnews_api_key = os.getenv('GNEWS_API_KEY')
        self.mediastack_api_key = os.getenv('MEDIASTACK_API_KEY')
        self.currents_api_key = os.getenv('CURRENTS_API_KEY')
        
        # Market Data
        self.iex_cloud_api_key = os.getenv('IEX_CLOUD_API_KEY')
        self.alpha_vantage_api_key = os.getenv('ALPHA_VANTAGE_API_KEY')
        
        # Broker
        self.alpaca_api_key = os.getenv('ALPACA_API_KEY')
        self.alpaca_api_secret = os.getenv('ALPACA_API_SECRET')
        self.alpaca_base_url = os.getenv('ALPACA_BASE_URL', 'https://paper-api.alpaca.markets')
        
        # Database
        self.database_url = os.getenv('DATABASE_URL', 'sqlite:///./data/phasma_ai.db')
        
        # System
        self.environment = os.getenv('ENVIRONMENT', 'development')
        self.log_level = os.getenv('LOG_LEVEL', 'INFO')
        
        # Feature Flags
        self.feature_execution_checks_enabled = os.getenv('FEATURE_EXECUTION_CHECKS_ENABLED', 'true').lower() == 'true'
        self.feature_paper_mode_only = os.getenv('FEATURE_PAPER_MODE_ONLY', 'true').lower() == 'true'
        self.feature_human_gate_enabled = os.getenv('FEATURE_HUMAN_GATE_ENABLED', 'true').lower() == 'true'
        self.feature_rollback_enabled = os.getenv('FEATURE_ROLLBACK_ENABLED', 'false').lower() == 'true'
        
        # Trading
        self.default_strategy = os.getenv('DEFAULT_STRATEGY', 'penny_moonshot')
        self.max_position_size = int(os.getenv('MAX_POSITION_SIZE', '10000'))
        self.default_slippage_cap = float(os.getenv('DEFAULT_SLIPPAGE_CAP', '0.01'))
        
        # Security
        self.jwt_secret = os.getenv('JWT_SECRET')
        self.encryption_key = os.getenv('ENCRYPTION_KEY')
    
    def validate(self):
        """Validate configuration"""
        errors = []
        
        # Check required API keys
        if not self.world_news_api_key:
            errors.append("World News API key is required")
        
        if not self.gnews_api_key:
            errors.append("GNews API key is required")
        
        # Check security
        if self.environment == 'production':
            if not self.jwt_secret:
                errors.append("JWT secret is required in production")
            if not self.encryption_key:
                errors.append("Encryption key is required in production")
        
        return errors
    
    def print_summary(self):
        """Print configuration summary"""
        print("\n" + "="*60)
        print("🔧 PHASMA AI - CONFIGURATION SUMMARY")
        print("="*60)
        
        print(f"\nEnvironment: {self.environment}")
        print(f"Default Strategy: {self.default_strategy}")
        print(f"Max Position Size: ${self.max_position_size:,}")
        print(f"Default Slippage Cap: {self.default_slippage_cap:.1%}")
        
        print("\nFeature Flags:")
        print(f"  • Execution Checks: {'✅' if self.feature_execution_checks_enabled else '❌'}")
        print(f"  • Paper Mode Only: {'✅' if self.feature_paper_mode_only else '❌'}")
        print(f"  • Human Gate: {'✅' if self.feature_human_gate_enabled else '❌'}")
        print(f"  • Rollback: {'✅' if self.feature_rollback_enabled else '❌'}")
        
        print("\nAPI Keys Status:")
        apis = [
            ('World News', self.world_news_api_key),
            ('GNews', self.gnews_api_key),
            ('MediaStack', self.mediastack_api_key),
            ('Currents', self.currents_api_key),
            ('IEX Cloud', self.iex_cloud_api_key),
            ('Alpaca', self.alpaca_api_key)
        ]
        
        for name, key in apis:
            status = "✅ Set" if key else "❌ Missing"
            print(f"  • {name}: {status}")
        
        print("\n" + "="*60)

# Create secure key generator
def generate_secure_keys():
    """Generate secure keys for production"""
    import secrets
    
    keys = {
        'jwt_secret': secrets.token_urlsafe(32),
        'encryption_key': secrets.token_urlsafe(32)[:32]
    }
    
    print("\n🔐 Generated Secure Keys:")
    print(f"JWT_SECRET={keys['jwt_secret']}")
    print(f"ENCRYPTION_KEY={keys['encryption_key']}")
    
    return keys

# Update data integration to use environment
class SecureNewsDataIntegrator:
    """News data integrator using environment variables"""
    
    def __init__(self):
        from dotenv import load_dotenv
        load_dotenv()
        
        # Load keys from environment
        self.world_news_key = os.getenv('WORLD_NEWS_API_KEY')
        self.gnews_key = os.getenv('GNEWS_API_KEY')
        self.mediastack_key = os.getenv('MEDIASTACK_API_KEY')
        self.currents_key = os.getenv('CURRENTS_API_KEY')
        
        # Validate keys
        self.validate_keys()
    
    def validate_keys(self):
        """Validate that required keys are present"""
        required = ['world_news_key', 'gnews_key', 'mediastack_key', 'currents_key']
        
        for key in required:
            if not getattr(self, key):
                raise ValueError(f"Missing required API key: {key.upper()}")
        
        print("✅ All news API keys loaded from environment")

if __name__ == "__main__":
    # Create .env file
    create_env_file()
    
    # Load environment
    missing = load_environment()
    
    # Create and validate configuration
    config = Config()
    errors = config.validate()
    
    if errors:
        print("\n❌ Configuration Errors:")
        for error in errors:
            print(f"  • {error}")
    else:
        print("\n✅ Configuration is valid!")
    
    # Print summary
    config.print_summary()
    
    # Generate secure keys if needed
    if config.environment == 'production' and not config.jwt_secret:
        print("\n🔐 Generating secure keys for production...")
        generate_secure_keys()
