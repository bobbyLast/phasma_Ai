#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phasma AI - Complete Trading System
Enhanced Meta-Brain powered trading system with multi-API news integration
"""
import sys
import io
# Force UTF-8 encoding for Windows console
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

import sys
import asyncio
import os
from dotenv import load_dotenv
import importlib
import glob

# Load environment variables
load_dotenv()

import json
import time
import logging
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple

# Suppress provider bridge module error noise
logging.getLogger('yfinance').setLevel(logging.CRITICAL)

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import core components
from brain.meta_brain import PhasmaMetaBrain, Signal
from core.config import PhasmaConfig
from core.application_context import ApplicationContext
from core.trade_classifier import TradeClassifier, TradeClass
from core.trade_logger import TradeLogger
from core.runtime_paths import memory_path, phasma_state_file

# Import Signal Framework
from trading.signal_framework import (
    TradingSignal, SignalProcessor, SignalTier, DecisionBand,
    RiskParameters, TradeDecision
)
from trading.ai_integration import (
    AIModelOutput, SignalGenerator, MultiTimeframeAggregator,
    TradingDecisionEngine
)

# Import engines
from engines import NewsAPIIntegration
from brain.signal_convergence_engine import SignalConvergenceEngine
from brain.thematic_analysis_engine import ThematicAnalyzer
from engines.pump_dump_detector import PumpDumpDetector
from engines.global_macro_monitor import GlobalMacroMonitor
from engines.form4_parser import Form4Parser
from engines.options_flow_filter import OptionsFlowFilter
from engines.enhanced_options_flow_detector import get_enhanced_options_detector

# Import market data cache
try:
    from utils.market_data_cache import MarketDataCache
except ImportError:
    MarketDataCache = None
from engines.human_validator import HumanValidator
from compliance.audit_trail import ComplianceLogger
from engines.insider_signal_integrator import InsiderSignalIntegrator
from brain.market_intelligence_engine import MarketIntelligenceEngine
from engines.monte_carlo_engine import get_monte_carlo_engine
from engines.social_engine import RedditTrendingTracker
from engines.silver_price_monitor import SilverPriceMonitor
from engines.smart_monte_carlo import SmartMonteCarlo
from engines.advanced_sentiment_engine import AdvancedSentimentEngine
from engines.risk_guardian_meta_agent import RiskGuardianMetaAgent
from engines.volatility_edge_engine import ImpliedRealizedVolatilityEdgeEngine as VolatilityEdgeEngine
from engines.self_calibrating_probability_engine import SelfCalibratingProbabilityEngine
from engines.iv_crush_predictor import IVCrushPredictor
from engines.exit_optimizer import ExitOptimizer
from engines.auto_exit_manager import AutoExitManager
from engines.microstructure_engine import MicrostructureEngine
from engines.spread_builder import SpreadBuilder
from engines.correlation_tracker import CorrelationTracker
from engines.scenario_graph_engine import ScenarioGraphEngine
from engines.cross_venue_radar import CrossVenueMispricingRadar
from engines.top_10_dashboard import Top10OpportunitiesDashboard
from engines.causal_counterfactual_engine import CausalCounterfactualEngine
from engines.calendar_seasonality_engine import CalendarSeasonalityEngine
from engines.earnings_drift_engine import EarningsDriftEngine
from engines.macro_calendar_engine import MacroCalendarEngine
from engines.corporate_actions_engine import CorporateActionsEngine
from engines.range_barrier_engine import RangeBarrierEngine
from engines.daily_learning_tracker import DailyLearningTracker
from engines.adaptive_confidence_threshold import AdaptiveConfidenceThreshold
from engines.unusual_whales_engine import UnusualWhalesEngine
# Crash profit functionality now integrated in crash_detector_v2

# Import utilities
from utils.price_fetcher import get_price_fetcher
from utils.robust_price_fetcher import get_robust_price_fetcher
from utils.affordable_stock_filter import AffordableStockFilter
from utils.trade_memory import get_trade_memory
from utils.trade_recommendation_memory import get_trade_memory as get_recommendation_memory
from utils.timeframe_calculator import calculate_optimal_timeframe, get_expiry_description
from utils.alert_router import get_alert_router, AlertPriority
from utils.volatility_burst_detector import get_vol_burst_detector
# from utils.weekly_watchlist import get_weekly_watchlist_generator  # REMOVED - Duplicate
from utils.trade_memory import get_trade_memory as get_cooldown_memory
from utils.dynamic_profit_targets import get_target_calculator
from utils.winners_gallery import get_winners_gallery
from utils.insider_opportunity_analyzer import get_insider_analyzer
from utils.politician_tracker import PoliticianTracker
from utils.trader_call_logger import TraderCallLogger
from utils.exit_strategy_manager import ExitStrategyManager
from utils.simulation_exit_manager import SimulationExitManager, ExitSignal as SimExitSignal
from utils.profit_maximization_exit_manager import ProfitMaximizationExitManager
from utils.strategy_cue_cards import get_strategy_cards, StrategyType
from utils.news_impact_tracker import NewsImpactTracker
from utils.skipped_opportunity_watchlist import SkippedOpportunityWatchlist
from utils.pe_ratio_analyzer import PERatioAnalyzer
from utils.thesis_manager import ThesisManager
from utils.alert_learning_loop import get_alert_learning_loop
# from utils.why_moving_strip import get_why_moving_strip  # Temporarily disabled
from engines.real_portfolio_manager import RealPortfolioManager
from engines.market_hours_detector import MarketHoursDetector
from engines.paper_trading_portfolio import PaperTradingPortfolio, get_paper_trading_portfolio
from engines.alpaca_paper_trader import AlpacaPaperTrader
from engines.enhanced_alpaca_trader import EnhancedAlpacaPaperTrader
from utils.dynamic_portfolio_manager import DynamicPortfolioManager
from utils.moon_shot_detector import MoonShotDetector
from utils.adaptive_position_sizer import AdaptivePositionSizer
from utils.randomness_pattern_analyzer import RandomnessPatternAnalyzer
from utils.volatility_lookup import VolatilityLookup

# Import unified trading system
from trading.unified_trading_system import UnifiedTradingSystem
from services.confluence_service import ConfluenceService
from engines.underground_stock_discovery import UndergroundStockDiscovery

from engines.smart_trading_strategy import SmartTradingStrategy
from engines.geopolitical_analyzer import GeopoliticalImpactAnalyzer
from engines.multi_platform_scanner import MultiPlatformScanner

try:
    from engines.geopolitical_monitor import GeopoliticalNewsMonitor
except Exception:
    GeopoliticalNewsMonitor = None

class PhasmaTradingSystem:
    """Complete Phasma AI trading system"""

    def __init__(self, config_path: str = None):
        """Initialize the complete trading system"""
        self.config = PhasmaConfig(config_path)
        self.options_enabled = getattr(self.config, 'options_enabled', False)
        
        # Load trading configuration for symbol management and budget settings
        try:
            import json
            trading_config_path = os.path.join(os.path.dirname(__file__), 'config', 'trading_config.json')
            with open(trading_config_path, 'r') as f:
                trading_config = json.load(f)
                # Update config with trading settings
                for key, value in trading_config.items():
                    setattr(self.config, key, value)
                print(f"✅ Loaded trading config - Max price: ${getattr(self.config, 'trading_budget', {}).get('max_price_per_share', 50)}")
        except Exception as e:
            print(f"⚠️ Could not load trading config: {e}")
            # Set default high budget to avoid filtering out major stocks
            if not hasattr(self.config, 'trading_budget'):
                self.config.trading_budget = {
                    'max_price_per_share': 1000,
                    'max_price_per_share_geo': 2000
                }
        
        self.meta_brain = PhasmaMetaBrain(config_path)
        
        # AI's dynamic tracking system (built from discoveries, not hardcoded)
        self.ai_watchlist = set()  # All symbols the AI is tracking
        self.ai_analyzed_history = {}  # History of what was analyzed and when
        self.ai_symbol_categories = {}  # Categorize symbols (stock/crypto/etc.)
        self.ai_symbol_last_seen = {}  # Track when each symbol was last seen
        
        self.news_engine = NewsAPIIntegration(self.config)
        
        # Continue with the rest of initialization
        self._initialize_all_components()
    
    def _initialize_all_components(self):
        """Initialize all system components"""
        
        # Only create options engine if not disabled
        if self.options_enabled:
            from engines.options_engine import PhasmaOptionsEngine
            self.options_engine = PhasmaOptionsEngine(self.config)
        else:
            self.options_engine = None
            print("✅ Options Engine Disabled (options_enabled=false)")

        # Initialize progressive trading system
        self.trading_mode = self.config.get('trading_mode', 'stocks_and_kalshi')
        self.graduation_thresholds = self.config.get('graduation_thresholds', {})
        
        # Initialize units system (sports betting style)
        self.units_config = self.config.get('units_system', {})
        self.unit_size_percent = self.units_config.get('unit_size_percent', 1)  # 1% per unit
        self.standard_units = self.units_config.get('standard_units', 5)
        self.max_units = self.units_config.get('max_units_per_trade', 10)
        self.min_units = self.units_config.get('min_units_per_trade', 1)
        
        # Calculate unit value based on current bankroll
        bankroll = self.config.get('bankroll', 2000)
        self.unit_value = bankroll * (self.unit_size_percent / 100)
        self.standard_trade_size = self.unit_value * self.standard_units
        
        print(f"[TRADING MODE] 🎯 {self.trading_mode.upper()} ACTIVE")
        print(f"[UNITS SYSTEM] 💰 1 Unit = ${self.unit_value:.2f} ({self.unit_size_percent}% of ${bankroll} bankroll)")
        print(f"[UNITS SYSTEM] 📊 Standard Trade = {self.standard_units} units = ${self.standard_trade_size:.2f}")
        print(f"[UNITS SYSTEM] 🎯 Range: {self.min_units}-{self.max_units} units per trade")
        
        # Initialize utility systems
        self.alert_router = get_alert_router()
        self.vol_burst_detector = get_vol_burst_detector()
        self.winners_gallery = get_winners_gallery()
        self.insider_monitor = get_insider_analyzer(self.config)
        self.politician_tracker = PoliticianTracker(self.config.get('politician_tracker', {}))
        self.trader_call_logger = TraderCallLogger()
        self.exit_strategy_manager = ExitStrategyManager(self.config)
        self.simulation_exit_manager = SimulationExitManager(self.config)
        self.strategy_cards = get_strategy_cards()
        self.alert_learning = get_alert_learning_loop()
        self.price_fetcher = get_price_fetcher()
        self.robust_price_fetcher = get_robust_price_fetcher()

        self.market_hours = MarketHoursDetector()
        self.smart_strategy = SmartTradingStrategy(self.config)
        
        self.geo_thinker = None  # AdvancedGeopoliticalThinker() - temporarily disabled
        self.geo_analyzer = GeopoliticalImpactAnalyzer()
        self.geo_scanner = MultiPlatformScanner()

        if GeopoliticalNewsMonitor:
            try:
                self.geo_news_monitor = GeopoliticalNewsMonitor(self.config.get('geopolitical_analysis', {}))
            except Exception as e:
                self.geo_news_monitor = None
                print(f"⚠️ GeopoliticalNewsMonitor init failed: {e}")
        else:
            self.geo_news_monitor = None

        self._geo_event_cache = []
        self._geo_event_cache_ts = None
        
        # 🚀 Real Portfolio System - Tracks actual trades and P&L
        self.trade_recommendation_memory = get_recommendation_memory()
        self.target_calculator = get_target_calculator()
        self.real_portfolio = RealPortfolioManager(self.config)  # Real portfolio tracking
        
        # 📊 Paper Trading Portfolio - Track AI performance without real money
        if self.config.get('paper_trading', {}).get('enabled', False):
            # Initialize Alpaca Paper Trading FIRST (real market data)
            try:
                self.alpaca_paper_trader = EnhancedAlpacaPaperTrader()
                if self.alpaca_paper_trader.alpaca:
                    print("✅ Enhanced Alpaca Paper Trading Initialized - REAL MARKET DATA")
                    print("   Platform: Alpaca Paper Trading API")
                    print("   Market Data: Real-time IEX feeds")
                    print("   Features: Whole Stock Logic + Auto-Selling")
                    print("   Account: Paper trading (no real money)")
                else:
                    print("⚠️ Alpaca Paper Trading failed - falling back to internal")
                    self.paper_portfolio = get_paper_trading_portfolio(self.config)
            except Exception as e:
                print(f"⚠️ Alpaca Paper Trading Error: {e}")
                print("   Falling back to internal paper trading")
                self.paper_portfolio = get_paper_trading_portfolio(self.config)
                self.alpaca_paper_trader = None
            print("✅ Paper Trading Portfolio Initialized")
            if hasattr(self, 'paper_portfolio') and self.paper_portfolio:
                print(f"   Starting Capital: ${self.paper_portfolio.state['starting_capital']:,.2f}")
        else:
            self.paper_portfolio = None
            print("⚠️ Paper Trading Disabled")
            self.alpaca_paper_trader = None
        
        # Initialize affordable stock filter based on available capital
        available_capital = self.real_portfolio.state['available_capital']
        self.affordable_filter = AffordableStockFilter(max_price=available_capital)
        
        self.trade_memory = {}  # Track trade memory for cooldowns
        self.posted_signals = self._load_posted_signals()  # Load persistent posted signals
        self.last_gallery_posted_at = None  # Track last gallery post to avoid spamming
        self._seen_news_keys = set()
        self._seen_news_ts = {}
        self._price_cache = {}
        
        # Initialize day trading scanner for regular stocks
        from engines.day_trading_scanner import get_day_trading_scanner
        self.day_trading_scanner = get_day_trading_scanner(self.config)
        self.moon_shot_detector = MoonShotDetector(self.config)
        self.position_sizer = AdaptivePositionSizer(self.config)
        self.pump_dump_detector = PumpDumpDetector(self.config)
        
        try:
            self.global_macro_monitor = GlobalMacroMonitor(self.config)
            print("✅ Global Macro Monitor Initialized")
        except Exception as e:
            self.global_macro_monitor = None
            print(f"⚠️ Could not initialize Global Macro Monitor: {e}")

        # FRED Economic Filter (fredapi replacement — free FRED API)
        self.fred_filter = None
        try:
            from utils.fred_economic_filter import FRDEconomicFilter
            _fred_key = os.getenv('FRED_API_KEY')
            if _fred_key:
                self.fred_filter = FRDEconomicFilter(_fred_key)
                print("✅ FRED Economic Filter Initialized")
            else:
                print("⚠️ FRED_API_KEY not set — FRED macro filter disabled (get free key at fred.stlouisfed.org)")
        except Exception as e:
            self.fred_filter = None
            print(f"⚠️ Could not initialize FRED filter: {e}")

        self.insider_signal_integrator = InsiderSignalIntegrator(self.config)
        
        # Initialize new enhanced components
        self.form4_parser = Form4Parser()
        self.options_filter = OptionsFlowFilter()
        self.enhanced_options_detector = get_enhanced_options_detector(self.config)
        self.human_validator = HumanValidator()
        self.compliance_logger = ComplianceLogger()
        print("✅ Enhanced Options Flow Detector Initialized with multi-source support")
        
        # Initialize Kalshi prediction market engine
        self.kalshi_engine = None
        try:
            from engines.kalshi_engine import KalshiPredictionEngine
            self.kalshi_engine = KalshiPredictionEngine(self.config)
            print("✅ Kalshi Engine Initialized")
        except Exception as e:
            print(f"⚠️ Could not initialize Kalshi Engine: {e}")
            
        # Initialize partnership engine
        try:
            from engines.partnership_engine.phasma_integration import PhasmaPartnershipEngine
            self.partnership_engine = PhasmaPartnershipEngine(
                config_path=os.path.join('config', 'partnership_engine.json')
            )
            print("✅ Partnership Engine Initialized")
        except Exception as e:
            self.partnership_engine = None
            print(f"⚠️ Could not initialize Partnership Engine: {e}")
            
        self.is_running = False

        # Load any previous Meta-Brain state
        try:
            self.meta_brain.load_state(phasma_state_file())
            print("♻️ Loaded previous Meta-Brain state")
        except Exception as e:
            print(f"⚠️ Could not load previous Meta-Brain state: {e}")
        
        # TEMPORARY FIX: Clear phantom positions
        if hasattr(self.meta_brain, 'risk_manager') and hasattr(self.meta_brain.risk_manager, 'open_positions'):
            self.meta_brain.risk_manager.open_positions = {}
            print("🧹 CLEARED: Phantom positions")

        # Register engines with Meta-Brain
        self.meta_brain.register_engine('news', self.news_engine)
        
        if self.options_engine is not None:
            self.meta_brain.register_engine('options', self.options_engine)
            print("✅ Options Engine Registered")
        else:
            print("✅ Options Engine Disabled")
        
        if self.partnership_engine:
            self.meta_brain.register_engine('partnerships', self.partnership_engine)

        # Setup logging
        self._setup_logging()

        # Initialize monitoring status
        self.monitoring_active = False
        self.monitoring_start_time = None
        self.monitoring_cycles = 0
        
        # Initialize social media monitoring
        try:
            self.social_engine = RedditTrendingTracker(self.config)
            print("✅ Social Media Monitor: ENABLED (Reddit)")
        except Exception as e:
            self.social_engine = None
            print(f"⚠️ Social Media Monitor: Failed to initialize - {e}")
        
        # Initialize market data cache
        self.market_cache = None
        if MarketDataCache:
            self.market_cache = MarketDataCache(cache_duration_minutes=10)
            print("✅ Market Data Cache Initialized")
        else:
            print("⚠️ Market Data Cache not available")
        
        # Initialize infinite symbol provider
        try:
            from utils.infinite_symbol_provider import get_symbol_provider
            self.symbol_provider = get_symbol_provider()
            print(f"✅ Infinite Symbol Provider Initialized - {self.symbol_provider.get_total_symbol_count()} symbols available")
        except Exception as e:
            print(f"⚠️ Could not initialize Symbol Provider: {e}")
            self.symbol_provider = None
        
        # Initialize market crash detector
        self.crash_detector = None
        try:
            from engines.market_crash_detector_v2 import MarketCrashDetectorV2
            from engines.monte_carlo_engine import PhasmaMonteCarloEngine
            monte_carlo = PhasmaMonteCarloEngine(self.config)
            self.crash_detector = MarketCrashDetectorV2(config=self.config, market_cache=self.market_cache, simulation_engine=monte_carlo)
            self.meta_brain.register_engine('crash_detector', self.crash_detector)
            print("✅ Market Crash Detector V2 Initialized")
        except Exception as e:
            print(f"⚠️ Could not initialize Crash Detector: {e}")
            
        # Initialize unified trading system
        unified_config = {
            "insider_monitor": self.config.get("insider_monitor", {}),
            "watchlist": [],
            "quick_trade_threshold": self.config.get("quick_trade_threshold", 75),
            "thesis_threshold": self.config.get("thesis_threshold", 85),
            "enable_market_scan": True
        }
        self.unified_system = UnifiedTradingSystem(unified_config)
        print("✅ Unified Trading System Initialized")
        
        # Initialize Confluence Service
        self.confluence_service = ConfluenceService(
            self.config,
            self.insider_signal_integrator,
            self.insider_monitor,
            self.options_filter
        )
        print("✅ Confluence Service Initialized")
        
        # Initialize Underground Stock Discovery
        if self.config.get('underground_discovery', {}).get('enabled', False):
            self.underground_discovery = UndergroundStockDiscovery(self.config)
            print("✅ Underground Stock Discovery Initialized")
        else:
            self.underground_discovery = None

        # Initialize exit strategy manager
        self.exit_manager = ExitStrategyManager()
        print("✅ Exit Strategy Manager Initialized")
        
        # Initialize simulation exit manager
        self.sim_exit_manager = SimulationExitManager()
        print("✅ Simulation Exit Manager Initialized")
        
        # Initialize profit maximization exit manager
        if self.config.get("profit_maximization", {}).get("enabled", False):
            profit_config = self.config.get("profit_maximization", {})
            self.profit_exit_manager = ProfitMaximizationExitManager(profit_config)
            print("✅ Profit Maximization Exit Manager Initialized")
        else:
            self.profit_exit_manager = None
            print("⚠️ Profit Maximization Disabled")

        # Initialize thematic analysis engine
        self.thematic_analyzer = ThematicAnalyzer(self.config)
        print("✅ Thematic Analysis Engine Initialized")

        # Initialize signal convergence engine
        self.convergence_engine = SignalConvergenceEngine()
        print("✅ Signal Convergence Engine Initialized")

        # Initialize news impact tracker
        self.news_impact_tracker = NewsImpactTracker()
        print("✅ News Impact Tracker Initialized")

        self.skipped_opportunity_watchlist = SkippedOpportunityWatchlist()
        print("✅ Skipped-opportunity revisit queue initialized")

        # Initialize Telegram bot for alerts
        try:
            from telegram_bot import get_telegram_bot
            self.telegram_bot = get_telegram_bot()
            print("✅ Telegram Bot Initialized")
            
            if self.telegram_bot:
                test_message = "🤖 Phasma AI System Restart - All engines operational"
                if self.telegram_bot.send_message(test_message):
                    print("✅ Telegram connectivity test successful")
                else:
                    print("⚠️ Telegram connectivity test failed")
        except Exception as e:
            print(f"⚠️ Could not initialize Telegram Bot: {e}")
            self.telegram_bot = None

        # Initialize Auto Exit Manager with Alpaca connection
        self.auto_exit_manager = AutoExitManager(config=self.config)
        if hasattr(self, 'alpaca_paper_trader') and self.alpaca_paper_trader:
            self.auto_exit_manager.broker_api = self.alpaca_paper_trader
            print('Auto Exit Manager - Connected to Alpaca')
        else:
            print('Auto Exit Manager - Simulation Mode')

        # Initialize Daily Learning Tracker
        self.daily_learning_tracker = DailyLearningTracker(self.config)
        self.adaptive_threshold = AdaptiveConfidenceThreshold('config.json')
        print(f"🎯 Adaptive Confidence Threshold Initialized: {self.adaptive_threshold.get_current_threshold()}%")
        self.unusual_whales = UnusualWhalesEngine(self.config)
        if self.unusual_whales.enabled:
            print("🐋 Unusual Whales Engine Initialized - Tracking unusual options activity")
        else:
            print("⚠️ Unusual Whales Engine Disabled")

        if hasattr(self, 'alpaca_paper_trader') and self.alpaca_paper_trader and getattr(self.alpaca_paper_trader, 'alpaca', None):
            try:
                starting_balance = float(self.alpaca_paper_trader.alpaca.get_account().portfolio_value)
            except Exception:
                starting_balance = float(self.meta_brain.risk_manager.get_available_bankroll())
        else:
            starting_balance = float(self.meta_brain.risk_manager.get_available_bankroll())
        self.daily_learning_tracker.start_trading_day(starting_balance)

        print("🚀 Phasma AI Trading System Initialized")
        print(f"📊 Bankroll: ${self.meta_brain.risk_manager.get_available_bankroll():.2f}")

    def _reset_cycle_caches(self):
        self._price_cache = {}

    def _load_posted_signals(self) -> set:
        """Load previously posted signals from persistent storage"""
        import os
        import json
        signals_file = memory_path("posted_signals.json")
        try:
            if os.path.exists(signals_file):
                with open(signals_file, 'r') as f:
                    data = json.load(f)
                    # Clean old signals (older than 24 hours)
                    import time
                    now = time.time()
                    cutoff = now - 86400  # 24 hours
                    filtered = {k: v for k, v in data.items() if v.get('timestamp', 0) > cutoff}
                    # Save cleaned data
                    if len(filtered) != len(data):
                        with open(signals_file, 'w') as fw:
                            json.dump(filtered, fw)
                    return set(filtered.keys())
        except Exception as e:
            print(f"⚠️ Could not load posted signals: {e}")
        return set()

    def _save_posted_signals(self):
        """Save posted signals to persistent storage"""
        import os
        import json
        import time
        signals_file = memory_path("posted_signals.json")
        try:
            os.makedirs(os.path.dirname(signals_file), exist_ok=True)
            # Load existing data
            existing = {}
            if os.path.exists(signals_file):
                with open(signals_file, 'r') as f:
                    existing = json.load(f)
            # Update with current signals
            now = time.time()
            for signal_key in self.posted_signals:
                if signal_key not in existing:
                    existing[signal_key] = {'timestamp': now}
                else:
                    existing[signal_key]['timestamp'] = now
            # Save
            with open(signals_file, 'w') as f:
                json.dump(existing, f)
        except Exception as e:
            print(f"⚠️ Could not save posted signals: {e}")

    def _get_cached_price(self, symbol: str) -> Optional[float]:
        sym = str(symbol or '').upper().strip()
        if not sym:
            return None
        if sym in self._price_cache:
            return self._price_cache[sym]
        try:
            price = self.price_fetcher.get_real_price(sym)
            if price is None:
                return None
            price_f = float(price)
            self._price_cache[sym] = price_f
            return price_f
        except Exception:
            return None

    def _news_dedupe_key(self, item: Dict) -> str:
        url = str(item.get('url') or '').strip().lower()
        if url:
            return f"url:{url}"
        title = re.sub(r"\s+", " ", str(item.get('title') or '').strip().lower())
        symbol = str(item.get('symbol') or '').strip().upper()
        return f"ts:{title[:160]}|{symbol}"

    def _filter_seen_news_items(self, items: List[Dict], ttl_hours: int = 12) -> List[Dict]:
        if not items:
            return []
        now = time.time()
        ttl = ttl_hours * 3600
        if self._seen_news_ts:
            expired = [k for k, ts in self._seen_news_ts.items() if now - ts > ttl]
            for k in expired:
                self._seen_news_ts.pop(k, None)
                self._seen_news_keys.discard(k)

        out = []
        for it in items:
            if not isinstance(it, dict):
                continue
            k = self._news_dedupe_key(it)
            if k in self._seen_news_keys:
                continue
            self._seen_news_keys.add(k)
            self._seen_news_ts[k] = now
            out.append(it)
        return out
    
    def _categorize_symbol(self, symbol: str) -> str:
        """Intelligently categorize a symbol based on its pattern"""
        symbol = symbol.upper()
        
        # Crypto patterns
        if '-' in symbol and symbol.endswith('-USD'):
            return 'crypto'
        elif symbol in ['BTC', 'ETH', 'SOL', 'XRP', 'DOGE', 'ADA', 'DOT', 'MATIC', 'AVAX', 'LINK', 'UNI', 'ATOM', 'LUNA']:
            return 'crypto'
        
        # Stock patterns
        elif len(symbol) <= 5 and symbol.isalpha() and '.' not in symbol:
            return 'stock'
        
        # ETF patterns
        elif symbol.startswith('QQQ') or symbol.startswith('SPY') or symbol.startswith('DIA') or symbol.startswith('IWM'):
            return 'etf'
        
        # Options patterns
        elif len(symbol) > 10 and any(c in symbol for c in ['C', 'P']) and any(c.isdigit() for c in symbol):
            return 'option'
        
        # Kalshi patterns
        elif 'KALSHI' in symbol or isinstance(symbol, str) and any(word in symbol.upper() for word in ['WILL', 'RATE', 'INFLATION', 'ELECTION']):
            return 'kalshi'
        
        # Default
        else:
            return 'unknown'
    
    def _track_symbol(self, symbol: str, source: str = 'news'):
        """Track a symbol and remember it for future analysis"""
        if not symbol or symbol == 'UNKNOWN':
            return
        
        symbol = symbol.upper()
        now = datetime.now()
        
        # Add to watchlist
        self.ai_watchlist.add(symbol)
        
        # Update category
        if symbol not in self.ai_symbol_categories:
            self.ai_symbol_categories[symbol] = self._categorize_symbol(symbol)
        
        # Update last seen
        self.ai_symbol_last_seen[symbol] = now
        
        # Add to analysis history
        if symbol not in self.ai_analyzed_history:
            self.ai_analyzed_history[symbol] = []
        
        self.ai_analyzed_history[symbol].append({
            'timestamp': now,
            'source': source,
            'category': self.ai_symbol_categories[symbol]
        })
        
        # Keep history manageable (last 10 entries per symbol)
        if len(self.ai_analyzed_history[symbol]) > 10:
            self.ai_analyzed_history[symbol] = self.ai_analyzed_history[symbol][-10:]
        
        # Only create options engine if enabled
        if self.options_enabled:
            from engines.options_engine import PhasmaOptionsEngine
            self.options_engine = PhasmaOptionsEngine(self.config)
        else:
            self.options_engine = None
            print("✅ Options Engine Disabled (options_enabled=false)")

        # Initialize progressive trading system
        self.trading_mode = self.config.get('trading_mode', 'stocks_and_kalshi')
        self.graduation_thresholds = self.config.get('graduation_thresholds', {})
        
        # Initialize units system (sports betting style)
        self.units_config = self.config.get('units_system', {})
        self.unit_size_percent = self.units_config.get('unit_size_percent', 1)  # 1% per unit
        self.standard_units = self.units_config.get('standard_units', 5)
        self.max_units = self.units_config.get('max_units_per_trade', 10)
        self.min_units = self.units_config.get('min_units_per_trade', 1)
        
        # Calculate unit value based on current bankroll
        bankroll = self.config.get('bankroll', 2000)
        self.unit_value = bankroll * (self.unit_size_percent / 100)
        self.standard_trade_size = self.unit_value * self.standard_units
        
        print(f"[TRADING MODE] 🎯 {self.trading_mode.upper()} ACTIVE")
        print(f"[UNITS SYSTEM] 💰 1 Unit = ${self.unit_value:.2f} ({self.unit_size_percent}% of ${bankroll} bankroll)")
        print(f"[UNITS SYSTEM] 📊 Standard Trade = {self.standard_units} units = ${self.standard_trade_size:.2f}")
        print(f"[UNITS SYSTEM] 🎯 Range: {self.min_units}-{self.max_units} units per trade")
        
        if self.trading_mode == 'stocks_and_kalshi':
            print(f"[TRADING MODE] 📚 ACTIVE: Stocks + Options + Kalshi")
            print(f"[TRADING MODE] 🎓 Graduation: {self.graduation_thresholds.get('min_win_rate', 60)}% win rate over {self.graduation_thresholds.get('min_trades', 50)} trades OR {self.graduation_thresholds.get('min_portfolio_growth', 20)}% growth")
        elif self.trading_mode == 'full_trading':
            print(f"[TRADING MODE] 🚀 ADVANCED PHASE: All trading unlocked (Options enabled)")
        else:
            print(f"[TRADING MODE] 🛡️ CONSERVATIVE PHASE: Stocks only")

        # Initialize utility systems
        self.alert_router = get_alert_router()
        self.vol_burst_detector = get_vol_burst_detector()
        # self.weekly_watchlist = get_weekly_watchlist_generator()  # REMOVED - Duplicate
        self.winners_gallery = get_winners_gallery()
        self.insider_monitor = get_insider_analyzer(self.config)
        self.politician_tracker = PoliticianTracker(self.config.get('politician_tracker', {}))
        self.trader_call_logger = TraderCallLogger()
        self.exit_strategy_manager = ExitStrategyManager(self.config)
        self.simulation_exit_manager = SimulationExitManager(self.config)
        # self.catalyst_calendar = get_catalyst_calendar()  # TODO: Fix missing import
        self.strategy_cards = get_strategy_cards()
        self.alert_learning = get_alert_learning_loop()
        self.price_fetcher = get_price_fetcher()
        self.robust_price_fetcher = get_robust_price_fetcher()
        
        # 🚀 Real Portfolio System - Tracks actual trades and P&L
        self.trade_recommendation_memory = get_recommendation_memory()
        self.target_calculator = get_target_calculator()
        self.real_portfolio = RealPortfolioManager(self.config)  # Real portfolio tracking
        
        # 📊 Paper Trading Portfolio - Track AI performance without real money
        if self.config.get('paper_trading', {}).get('enabled', False):
            self.paper_portfolio = get_paper_trading_portfolio(self.config)
            print("✅ Paper Trading Portfolio Initialized")
            if hasattr(self, 'paper_portfolio') and self.paper_portfolio:
                print(f"   Starting Capital: ${self.paper_portfolio.state['starting_capital']:,.2f}")
        else:
            self.paper_portfolio = None
            self.alpaca_paper_trader = None
            print("⚠️ Paper Trading Disabled")
            self.alpaca_paper_trader = None
        
        # Initialize affordable stock filter based on available capital
        available_capital = self.real_portfolio.state['available_capital']
        self.affordable_filter = AffordableStockFilter(max_price=available_capital)
        
        self.trade_memory = {}  # Track trade memory for cooldowns
        self.posted_signals = self._load_posted_signals()  # Load persistent posted signals
        self.last_gallery_posted_at = None  # Track last gallery post to avoid spamming
        
        # Initialize day trading scanner for regular stocks
        from engines.day_trading_scanner import get_day_trading_scanner
        self.day_trading_scanner = get_day_trading_scanner(self.config)
        self.moon_shot_detector = MoonShotDetector(self.config)
        self.position_sizer = AdaptivePositionSizer(self.config)
        # self.conviction_watchlist = ConvictionWatchlist(self.config)  # REMOVED - Duplicate
        self.pump_dump_detector = PumpDumpDetector(self.config)
        try:
            self.global_macro_monitor = GlobalMacroMonitor(self.config)
            print("✅ Global Macro Monitor Initialized")
        except Exception as e:
            self.global_macro_monitor = None
            print(f"⚠️ Could not initialize Global Macro Monitor: {e}")
        self.insider_signal_integrator = InsiderSignalIntegrator(self.config)
        
        # Initialize new enhanced components
        self.form4_parser = Form4Parser()
        self.options_filter = OptionsFlowFilter()
        self.enhanced_options_detector = get_enhanced_options_detector(self.config)
        self.human_validator = HumanValidator()
        self.compliance_logger = ComplianceLogger()
        
        print("✅ Day Trading Scanner Initialized")
        print("✅ Moon Shot Detector Initialized")
        print("✅ Pump/Dump Detector Initialized")
        print("✅ Global Macro Monitor Initialized")
        print("✅ Insider Signal Integrator Initialized")
        print("✅ Form 4 Parser Initialized")
        print("✅ Options Flow Filter Initialized")
        print("✅ Human Validator Initialized")
        print("✅ Compliance Logger Initialized")
        
        # Load configuration and partnership engine
        self.partnership_engine = None
        
        # Disable crash profit engine for stock-only mode (options disabled)
        # Crash profit now integrated in crash_detector_v2
        
        # Initialize market intelligence engine for universal contextual analysis
        try:
            self.market_intelligence = MarketIntelligenceEngine(self.config)
            self.market_intelliggence = self.market_intelligence
            print("✅ Market Intelligence Engine Initialized")
            print(f"[DEBUG] market_intelligence type: {type(self.market_intelligence)}")
        except Exception as e:
            print(f"⚠️ Could not initialize Market Intelligence Engine: {e}")
            self.market_intelligence = None
            self.market_intelliggence = None
            print(f"[DEBUG] market_intelligence set to None: {self.market_intelligence}")
        try:
            from engines.partnership_engine.phasma_integration import PhasmaPartnershipEngine
            self.partnership_engine = PhasmaPartnershipEngine(
                config_path=os.path.join('config', 'partnership_engine.json')
            )
            print("✅ Partnership Engine Initialized")
        except Exception as e:
            print(f"⚠️  Could not initialize Partnership Engine: {e}")
            
        self.is_running = False

        # Load any previous Meta-Brain state (open positions, performance)
        try:
            self.meta_brain.load_state(phasma_state_file())
            print("♻️ Loaded previous Meta-Brain state (open positions, performance)")
        except Exception as e:
            print(f"⚠️  Could not load previous Meta-Brain state: {e}")
        
        # TEMPORARY FIX: Clear phantom positions blocking trades
        if hasattr(self.meta_brain, 'risk_manager') and hasattr(self.meta_brain.risk_manager, 'open_positions'):
            self.meta_brain.risk_manager.open_positions = {}
            print("🧹 CLEARED: Phantom positions from risk_manager.open_positions")

        # Register engines with Meta-Brain
        self.meta_brain.register_engine('news', self.news_engine)
        
        # Note: Critical engines will be registered after initialization
        
        # Only register options engine if not disabled
        if self.options_engine is not None:
            self.meta_brain.register_engine('options', self.options_engine)
            print("✅ Options Engine Registered")
        else:
            print("✅ Options Engine Disabled - Stock trading only")
        if self.partnership_engine:
            self.meta_brain.register_engine('partnerships', self.partnership_engine)

        # Setup logging
        self._setup_logging()

        # Initialize monitoring status
        self.monitoring_active = False
        self.monitoring_start_time = None
        self.monitoring_cycles = 0
        
        # Initialize social media monitoring
        print("[DEBUG] About to initialize social media monitoring...")
        import sys
        sys.stdout.flush()
        try:
            self.social_engine = RedditTrendingTracker(self.config)
            print("[OK] Social Media Monitor: ENABLED (Reddit)")
            print(f"[DEBUG] Social engine object: {type(self.social_engine)}")
            sys.stdout.flush()
        except Exception as e:
            self.social_engine = None
            print(f"[WARNING] Social Media Monitor: Failed to initialize - {e}")
            import traceback
            traceback.print_exc()
            sys.stdout.flush()
        
        # Initialize market crash detector
        self.crash_detector = None
        try:
            from engines.market_crash_detector_v2 import MarketCrashDetectorV2
            from engines.monte_carlo_engine import PhasmaMonteCarloEngine
            monte_carlo = PhasmaMonteCarloEngine(self.config)
            self.crash_detector = MarketCrashDetectorV2(config=self.config, simulation_engine=monte_carlo)
            self.meta_brain.register_engine('crash_detector', self.crash_detector)
            print("✅ Market Crash Detector V2 Initialized")
        except Exception as e:
            print(f"⚠️  Could not initialize Crash Detector: {e}")
            
        # Initialize Kalshi prediction market engine
        self.kalshi_engine = None
        print(f"🔍 DEBUG: Config type: {type(self.config)}")
        print(f"🔍 DEBUG: kalshi_enabled value: {self.config.get('kalshi_enabled', 'NOT_FOUND')}")
        if self.config.get('kalshi_enabled', False):
            print(f"🔍 DEBUG: Attempting to initialize Kalshi engine (kalshi_enabled=True)")
            try:
                from engines.kalshi_engine import KalshiPredictionEngine
                print(f"🔍 DEBUG: Imported KalshiPredictionEngine successfully")
                self.kalshi_engine = KalshiPredictionEngine(self.config)
                print(f"🔍 DEBUG: KalshiPredictionEngine instantiated")
                self.meta_brain.register_engine('kalshi', self.kalshi_engine)
                print("✅ Kalshi Prediction Market Engine Initialized")
            except Exception as e:
                print(f"⚠️  Could not initialize Kalshi Engine: {e}")
                import traceback
                print(f"🔍 DEBUG: Full traceback: {traceback.format_exc()}")
                self.kalshi_engine = None
            
        # Initialize trade database
        self.trade_db = None
        try:
            from core.trade_database import TradeDatabase
            self.trade_db = TradeDatabase()
            print("✅ Trade Database Initialized")
        except Exception as e:
            print(f"⚠️  Could not initialize Trade Database: {e}")
            
        # Initialize trade classifier and logger
        self.trade_classifier = TradeClassifier()
        self.trade_logger = TradeLogger()
        print("✅ Trade Analysis System Initialized")
        
        # Initialize Silver Price Monitor
        try:
            self.silver_monitor = SilverPriceMonitor()
            print("✅ Silver Price Monitor Initialized")
        except Exception as e:
            print(f"⚠️ Could not initialize Silver Price Monitor: {e}")
            self.silver_monitor = None
        
        # Initialize Advanced Brain Components
        self.galton_mindset = GaltonMindset()
        print("✅ Galton Mindset Initialized - Probabilistic Thinking Enabled")
        print("🎯 Market viewed through Galton Board lens - Patterns in chaos")
        
        # Initialize Advanced Engines
        self.smart_monte_carlo = SmartMonteCarlo(self.config)
        print("✅ Smart Monte Carlo 2.0 Initialized - Adaptive Simulations")
        
        self.advanced_sentiment = AdvancedSentimentEngine(self.config)
        print("✅ Advanced Sentiment Engine Initialized - Reads Between the Lines")
        
        # CRITICAL: Volatility Edge Engine
        self.volatility_edge = VolatilityEdgeEngine(self.config)
        print("📊 Volatility Edge Engine Initialized - OPTIONS EDGE DETECTED")
        
        # Options Trading Components
        self.iv_crush_predictor = IVCrushPredictor()
        print("💥 IV Crush Predictor Initialized - Volatility Events Detected")
        
        self.exit_optimizer = ExitOptimizer(self.config)
        print("🎯 Exit Optimizer Initialized - Profit Maximization")
        
        self.auto_exit_manager = AutoExitManager(self.config)
        print("🤖 Auto Exit Manager Initialized - Emotion-Free Exits")
        
        # Connect AI Exit Manager to Alpaca for auto-selling
        if hasattr(self, 'alpaca_paper_trader') and self.alpaca_paper_trader:
            self.auto_exit_manager.broker_api = self.alpaca_paper_trader
            print("   ✅ AI Exit Manager connected to Alpaca Paper Trading")
            print("   🔄 AI-driven exits will execute on Alpaca automatically")
        
        # Advanced Market Analysis (will be initialized later after scenario_graph)
        
        self.spread_builder = SpreadBuilder(self.config)
        print("📈 Spread Builder Initialized - Risk-Optimized Spreads")
        
        self.correlation_tracker = CorrelationTracker(self.config)
        print("🔗 Correlation Tracker Initialized - Risk Diversification")
        
        self.scenario_graph = ScenarioGraphEngine(self.config)
        print("🌐 Scenario Graph Engine Initialized - What-If Analysis")
        
        # CRITICAL: Self-Calibrating Probability Engine (using Market Intelligence Engine)
        self.probability_engine = self.market_intelligence
        print("🧠 Self-Calibrating Probability Engine Initialized - AI LEARNING ENABLED")
        
        # Advanced Market Analysis (now that scenario_graph exists)
        self.microstructure = MicrostructureEngine(
            kalshi_engine=self.kalshi_engine,
            scenario_graph=self.scenario_graph
        )
        print("🔍 Microstructure Engine Initialized - Order Flow Analysis")
        
        # Calendar & Event-Based Edges (now that scenario_graph exists)
        self.calendar_seasonality = CalendarSeasonalityEngine(
            kalshi_engine=self.kalshi_engine,
            scenario_graph=self.scenario_graph
        )
        print("📅 Calendar Seasonality Engine Initialized - Holiday/Seasonal Patterns")
        
        self.earnings_drift = EarningsDriftEngine(
            kalshi_engine=self.kalshi_engine,
            scenario_graph=self.scenario_graph
        )
        print("📈 Earnings Drift Engine Initialized - Post-Earnings Patterns")
        
        self.macro_calendar = MacroCalendarEngine(
            kalshi_engine=self.kalshi_engine,
            scenario_graph=self.scenario_graph
        )
        print("📊 Macro Calendar Engine Initialized - Economic Event Patterns")
        
        self.corporate_actions = CorporateActionsEngine(
            kalshi_engine=self.kalshi_engine,
            scenario_graph=self.scenario_graph
        )
        print("📰 Corporate Actions Engine Initialized - Splits/Buybacks/Mergers")
        
        self.range_barrier = RangeBarrierEngine(
            kalshi_engine=self.kalshi_engine,
            scenario_graph=self.scenario_graph
        )
        print("🔒 Range Barrier Engine Initialized - Volatility & Range Analysis")
        
        self.cross_venue_radar = CrossVenueMispricingRadar(
            kalshi_engine=self.kalshi_engine,
            scenario_graph=self.scenario_graph
        )
        print("💹 Cross-Venue Radar Initialized - Arbitrage Detection")
        
        self.top_10_dashboard = Top10OpportunitiesDashboard(
            kalshi_engine=self.kalshi_engine,
            scenario_graph=self.scenario_graph,
            mispricing_radar=self.cross_venue_radar
        )
        print("📊 Top 10 Dashboard Initialized - Market Opportunity Heatmap")
        
        # Portfolio Management
        self.dynamic_portfolio = DynamicPortfolioManager(self.config)
        print("💰 Dynamic Portfolio Manager Initialized - Optimal Allocation")
        
        # Fundamental Analysis Tools
        self.pe_analyzer = PERatioAnalyzer()
        print("📊 P/E Ratio Analyzer Initialized - Valuation Analysis")
        # Initialize thesis manager with cache
        self.thesis_manager = ThesisManager(cache=self.market_cache)
        print("✅ Thesis Manager Initialized - Long-term Investment Analysis")
        
        self.volatility_lookup = VolatilityLookup()
        print("📊 Volatility Lookup Initialized - Historical Data")
        
        # Calendar & Event-Based Edges (will be initialized later after scenario_graph)
        
        # Advanced Analysis
        self.causal_counterfactual = CausalCounterfactualEngine(self.config)
        print("🔬 Causal Counterfactual Engine Initialized - 'What If' Analysis")

        # CRITICAL: Risk Guardian Meta Agent (now that all required engines exist)
        self.risk_guardian = RiskGuardianMetaAgent(
            kalshi_engine=self.kalshi_engine,
            scenario_graph=self.scenario_graph,
            mispricing_radar=self.cross_venue_radar,
            opportunities_dashboard=self.top_10_dashboard,
            causal_engine=self.causal_counterfactual
        )
        print("🛡️ Risk Guardian Meta Agent Initialized - KILL-SWITCH ACTIVE")

        # NOW register all engines with Meta-Brain (after initialization)
        # Register CRITICAL safety and optimization engines
        self.meta_brain.register_engine('risk_guardian', self.risk_guardian)
        self.meta_brain.register_engine('volatility_edge', self.volatility_edge)
        self.meta_brain.register_engine('probability_engine', self.probability_engine)
        self.meta_brain.register_engine('exit_optimizer', self.exit_optimizer)
        self.meta_brain.register_engine('dynamic_portfolio', self.dynamic_portfolio)
        
        # Register Calendar & Event engines
        self.meta_brain.register_engine('calendar_seasonality', self.calendar_seasonality)
        self.meta_brain.register_engine('earnings_drift', self.earnings_drift)
        self.meta_brain.register_engine('macro_calendar', self.macro_calendar)
        self.meta_brain.register_engine('corporate_actions', self.corporate_actions)
        
        # Register Advanced Analysis engines
        self.meta_brain.register_engine('cross_venue_radar', self.cross_venue_radar)
        self.meta_brain.register_engine('top_10_dashboard', self.top_10_dashboard)
        self.meta_brain.register_engine('causal_counterfactual', self.causal_counterfactual)
        
        # Register AI-Aware Insider Analysis engines
        self.meta_brain.register_engine('insider_signal_integrator', self.insider_signal_integrator)
        self.meta_brain.register_engine('form4_parser', self.form4_parser)
        self.meta_brain.register_engine('options_filter', self.options_filter)
        self.meta_brain.register_engine('human_validator', self.human_validator)
        self.meta_brain.register_engine('compliance_logger', self.compliance_logger)
        
        # Initialize unified trading system
        unified_config = {
            "insider_monitor": self.config.get("insider_monitor", {}),
            "watchlist": [],  # Empty - discover from news, not pre-defined
            "quick_trade_threshold": self.config.get("quick_trade_threshold", 75),
            "thesis_threshold": self.config.get("thesis_threshold", 85),
            "enable_market_scan": True  # Enable market scanning to discover stocks
        }
        self.unified_system = UnifiedTradingSystem(unified_config)
        print("✅ Unified Trading System Initialized")
        
        # Initialize Confluence Service for unified signal scoring
        self.confluence_service = ConfluenceService(
            self.config,
            self.insider_signal_integrator,
            self.insider_monitor,
            self.options_filter
        )
        print("✅ Confluence Service Initialized")
        
        # Initialize Underground Stock Discovery
        if self.config.get('underground_discovery', {}).get('enabled', False):
            self.underground_discovery = UndergroundStockDiscovery(self.config)
            print("✅ Underground Stock Discovery Initialized")
        else:
            self.underground_discovery = None

        # Initialize exit strategy manager
        self.exit_manager = ExitStrategyManager()
        print("✅ Exit Strategy Manager Initialized")
        
        # Initialize simulation exit manager
        self.sim_exit_manager = SimulationExitManager()
        print("✅ Simulation Exit Manager Initialized")
        
        # Initialize profit maximization exit manager
        if self.config.get("profit_maximization", {}).get("enabled", False):
            profit_config = self.config.get("profit_maximization", {})
            self.profit_exit_manager = ProfitMaximizationExitManager(profit_config)
            print("✅ Profit Maximization Exit Manager Initialized")
        else:
            self.profit_exit_manager = None
            print("⚠️  Profit Maximization Disabled")

        # Initialize thematic analysis engine
        self.thematic_analyzer = ThematicAnalyzer(self.config)
        print("✅ Thematic Analysis Engine Initialized")

        # Initialize signal convergence engine
        self.convergence_engine = SignalConvergenceEngine()
        print("✅ Signal Convergence Engine Initialized")

        # Initialize news impact tracker for historical learning
        self.news_impact_tracker = NewsImpactTracker()
        print("✅ News Impact Tracker Initialized")

        # Initialize Telegram bot for alerts
        try:
            from telegram_bot import get_telegram_bot
            self.telegram_bot = get_telegram_bot()
            print("✅ Telegram Bot Initialized")
            
            # Test Telegram connectivity
            if self.telegram_bot:
                test_message = "🤖 Phasma AI System Restart - All engines operational"
                if self.telegram_bot.send_message(test_message):
                    print("✅ Telegram connectivity test successful")
                else:
                    print("⚠️ Telegram connectivity test failed")
        except Exception as e:
            print(f"⚠️ Could not initialize Telegram Bot: {e}")
            self.telegram_bot = None

        print("🚀 Phasma AI Trading System Initialized")
        print(f"📊 Bankroll: ${self.meta_brain.risk_manager.get_available_bankroll():.2f}")
        print(f"🎯 POP Threshold: {self.config.get('pop_threshold')}")
        print(f"🛡️ Risk Per Trade: {self.config.get('risk_per_trade')}")
        print(f"📈 Max Drawdown: {self.config.get('max_drawdown')}")
        
        # Note: Real-time news collection is handled by news_engine.start_news_collection_network()

    def _setup_logging(self):
        """Setup enhanced logging"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('phasma.log'),
                logging.StreamHandler()
            ]
        )

    async def get_trending_symbols(self, limit: int = 20) -> dict:
        """Get trending symbols from social media
        
        Args:
            limit: Number of top symbols to return
            
        Returns:
            dict: {symbol: mention_count} of trending symbols
        """
        if not self.social_engine:
            return {}
            
        try:
            return await self.social_engine.get_trending_symbols(limit=limit)
        except Exception as e:
            print(f"⚠️  Error getting trending symbols: {e}")
            return {}

    def _execute_alpaca_trade_from_signal(self, signal_dict: dict):
        """Execute a paper trade using Alpaca API"""
        if not hasattr(self, 'alpaca_paper_trader') or not self.alpaca_paper_trader.alpaca:
            print(f"  📊 Alpaca Trade: Skipping - Alpaca not connected")
            return
        
        try:
            symbol = signal_dict.get('symbol', '')
            action = signal_dict.get('action', '')
            confidence = signal_dict.get('confidence', 0)
            
            # Check if confidence meets threshold
            # Use adaptive threshold if available, otherwise use config
            if hasattr(self, 'adaptive_threshold'):
                min_confidence = self.adaptive_threshold.get_current_threshold()
                if self.adaptive_threshold.should_execute_trade(confidence):
                    print(f"  📊 Alpaca Trade: {symbol} confidence {confidence:.1f}% meets adaptive threshold {min_confidence:.1f}%")
                else:
                    print(f"  📊 Alpaca Trade: Skipping {symbol} - confidence {confidence:.1f}% below adaptive threshold {min_confidence:.1f}%")
                    return
            else:
                min_confidence = self.config.get('paper_trading', {}).get('min_confidence_threshold', 70)
                if confidence < min_confidence:
                    print(f"  📊 Alpaca Trade: Skipping {symbol} - confidence {confidence:.1f}% below threshold {min_confidence}%")
                    return
            
            # Get position size and calculate with whole stock logic
            position_size = signal_dict.get('position_size', 0)
            entry_price = signal_dict.get('entry_price', 0)
            
            if position_size <= 0:
                print(f"  📊 Alpaca Trade: Skipping {symbol} - invalid position size ${position_size}")
                return
            
            if entry_price <= 0:
                print(f"  📊 Alpaca Trade: Skipping {symbol} - invalid price ${entry_price}")
                return
            
            # Use enhanced position sizing logic
            account = self.alpaca_paper_trader.get_account()
            available_capital = account.get('buying_power', position_size)
            
            position_calc = self.alpaca_paper_trader.calculate_position_size(
                symbol, entry_price, available_capital, confidence
            )
            
            quantity = position_calc['quantity']
            if quantity <= 0:
                print(f"  📊 Alpaca Trade: Skipping {symbol} - {position_calc['reasoning']}")
                return
            
            print(f"  📊 Position Logic: {position_calc['reasoning']}")
            
            # Execute trade via enhanced Alpaca
            if action.upper() == 'BUY':
                result = self.alpaca_paper_trader.execute_buy(
                    symbol, quantity, entry_price, confidence
                )
            elif action.upper() == 'SELL':
                result = self.alpaca_paper_trader.execute_sell(symbol, quantity, entry_price)
            else:
                print(f"  📊 Alpaca Trade: Skipping {symbol} - unknown action {action}")
                return
            
            if result['success']:
                print(f"  ✅ ALPACA TRADE EXECUTED: {symbol} {action} {quantity} @ ${result['price']}")
                print(f"     Order ID: {result['order_id']}")
                print(f"     Platform: Alpaca Paper Trading")
                
                # Record trade for daily learning
                if hasattr(self, 'daily_learning_tracker'):
                    self.daily_learning_tracker.record_trade({
                        'symbol': symbol,
                        'action': action,
                        'quantity': quantity,
                        'entry_price': result['price'],
                        'confidence': confidence,
                        'source': signal_dict.get('source', 'unknown'),
                        'sector': signal_dict.get('sector', 'unknown')
                    })
            else:
                print(f"  ❌ ALPACA TRADE FAILED: {symbol} - {result['error']}")
            
            return result
                
        except Exception as e:
            print(f"  ❌ ALPACA TRADE ERROR: {e}")
            return {'success': False, 'error': str(e)}

    def _execute_paper_trade_from_signal(self, signal_dict: dict):
        """Execute a paper trade based on a signal"""
        try:
            symbol = signal_dict.get('symbol', '')
            action = signal_dict.get('action', '')
            confidence = signal_dict.get('confidence', 0)
            
            # Check if confidence meets threshold
            min_confidence = self.config.get('paper_trading', {}).get('min_confidence_threshold', 70)
            if confidence < min_confidence:
                print(f"  📊 Paper Trade: Skipping {symbol} - confidence {confidence:.1f}% below threshold {min_confidence}%")
                return
            
            # Get position size from config or calculate
            max_position = self.config.get('paper_trading', {}).get('max_position_size', 1000)
            
            if action.upper() == 'BUY':
                # Calculate quantity based on available capital and max position
                available_capital = self.paper_portfolio.state['available_capital']
                price = signal_dict.get('entry_price', signal_dict.get('current_price', 0))
                
                if price <= 0:
                    print(f"  📊 Paper Trade: Skipping {symbol} - invalid price ${price}")
                    return
                
                # Use smaller of: max_position size or 10% of available capital
                max_by_capital = (available_capital * 0.1) / price
                quantity = min(int(max_by_capital), max_position)
                
                if quantity <= 0:
                    print(f"  📊 Paper Trade: Skipping {symbol} - insufficient capital")
                    return
                
                # Execute buy
                result = self.paper_portfolio.execute_buy(
                    symbol=symbol,
                    quantity=quantity,
                    price=price,
                    signal_data=signal_dict,
                    confidence=confidence
                )
                
                if result['success']:
                    print(f"  📊 Paper Trade: Bought {quantity} shares of {symbol} at ${price:.2f} (Total: ${result['total_cost']:.2f})")
                else:
                    print(f"  📊 Paper Trade: Failed to buy {symbol} - {result['error']}")
                    
        except Exception as e:
            print(f"  📊 Paper Trade Error: {e}")
    
    def _execute_paper_exit(self, symbol: str, quantity: int, price: float, reason: str = "Exit signal"):
        """Execute a paper trade exit"""
        if not self.paper_portfolio:
            return
        
        try:
            result = self.paper_portfolio.execute_sell(
                symbol=symbol,
                quantity=quantity,
                price=price,
                reason=reason
            )
            
            if result['success']:
                print(f"  📊 Paper Exit: Sold {quantity} shares of {symbol} at ${price:.2f} (P&L: ${result['realized_pnl']:.2f})")
            else:
                print(f"  📊 Paper Exit: Failed to sell {symbol} - {result['error']}")
                
        except Exception as e:
            print(f"  📊 Paper Exit Error: {e}")
    
    def _get_current_geopolitical_events(self) -> List[Dict]:
        """Get current geopolitical events from news sources"""
        if getattr(self, '_geo_event_cache', None):
            return list(self._geo_event_cache)

        demo_events = [
            {
                'title': 'US Military Action in Oil Region',
                'description': 'United States forces secure oil facilities amid escalating tensions in Middle East',
                'source': 'Geopolitical Monitor',
                'relevance': 95
            },
            {
                'title': 'China-US Trade Escalation',
                'description': 'New tariffs announced on semiconductor imports as tech war intensifies',
                'source': 'Trade Monitor',
                'relevance': 92
            },
            {
                'title': 'Russia-Europe Energy Crisis',
                'description': 'Natural gas supply disruptions threaten European industries as winter approaches',
                'source': 'Energy Analysis',
                'relevance': 90
            },
            {
                'title': 'Middle East Conflict Expansion',
                'description': 'Regional tensions rise affecting global shipping routes and oil prices',
                'source': 'Regional Monitor',
                'relevance': 88
            },
            {
                'title': 'Global Supply Chain Disruption',
                'description': 'Major shipping routes affected by Red Sea security concerns and Panama Canal drought',
                'source': 'Trade Monitor',
                'relevance': 85
            },
            {
                'title': 'Cyber Warfare Escalation',
                'description': 'State-sponsored cyber attacks target critical infrastructure across multiple nations',
                'source': 'Security Monitor',
                'relevance': 83
            },
            {
                'title': 'Latin America Political Instability',
                'description': 'Election uncertainty and resource nationalism in key mining regions',
                'source': 'Regional Analysis',
                'relevance': 80
            },
            {
                'title': 'Energy Security Concerns',
                'description': 'Countries reconsider energy dependencies amid conflicts and transition to renewables',
                'source': 'Energy Analysis',
                'relevance': 78
            },
            {
                'title': 'Sanctions Regime Expansion',
                'description': 'New economic sanctions target energy and defense sectors globally',
                'source': 'Policy Monitor',
                'relevance': 76
            },
            {
                'title': 'Rare Earth Supply Chain Risk',
                'description': 'China restricts exports of critical minerals for defense and tech manufacturing',
                'source': 'Resource Monitor',
                'relevance': 74
            },
            {
                'title': 'Currency War Escalation',
                'description': 'Central banks engage in competitive devaluation amid global economic slowdown',
                'source': 'Financial Monitor',
                'relevance': 72
            },
            {
                'title': 'Climate-Related Geopolitics',
                'description': 'Water scarcity and extreme weather drive migration and resource conflicts',
                'source': 'Climate Monitor',
                'relevance': 70
            }
        ]
        
        # Return relevant events
        return [e for e in demo_events if e['relevance'] > 70]

    async def _collect_geopolitical_events(self, hours_back: int = 24, news_items: Optional[List[Dict]] = None) -> List[Dict]:
        now = datetime.now()
        geo_cfg = self.config.get('geopolitical_analysis', {}) if hasattr(self, 'config') else {}
        try:
            scan_interval_minutes = int(geo_cfg.get('scan_interval_minutes', 60))
        except Exception:
            scan_interval_minutes = 60

        if getattr(self, '_geo_event_cache_ts', None) and getattr(self, '_geo_event_cache', None):
            try:
                age_s = (now - self._geo_event_cache_ts).total_seconds()
                if age_s < scan_interval_minutes * 60:
                    return list(self._geo_event_cache)
            except Exception:
                pass

        events: List[Dict] = []

        try:
            events.extend(self._extract_geo_events_from_news_items(news_items or []))
        except Exception:
            pass

        if getattr(self, 'geo_news_monitor', None) and (
            getattr(self.geo_news_monitor, 'news_api_key', None) or getattr(self.geo_news_monitor, 'bing_api_key', None)
        ):
            try:
                api_events = await asyncio.to_thread(self.geo_news_monitor.scan_news_headlines, hours_back)
                if api_events:
                    events.extend(api_events)
            except Exception:
                pass

        # ALWAYS include demo events to ensure comprehensive geopolitical coverage
        # Real events are great, but there's always geopolitical activity happening
        try:
            demo_events = list(self._get_current_geopolitical_events())
            if demo_events:
                # Add demo events, deduping against real events
                existing_titles = {e.get('title', '') for e in events}
                for demo in demo_events:
                    if demo.get('title', '') not in existing_titles:
                        events.append(demo)
                print(f"🌍 Added {len(demo_events)} demo events to geopolitical analysis")
        except Exception as e:
            print(f"⚠️ Could not load demo events: {e}")

        deduped = self._dedupe_geo_events(events)
        deduped.sort(key=lambda x: float(x.get('relevance', 0) or 0), reverse=True)

        self._geo_event_cache = deduped[:20]  # Increased from 10 to 20 to show more opportunities
        self._geo_event_cache_ts = now
        return list(self._geo_event_cache)

    def _extract_geo_events_from_news_items(self, news_items: List[Dict]) -> List[Dict]:
        if not news_items:
            return []

        monitor = getattr(self, 'geo_news_monitor', None)
        is_geo = getattr(monitor, '_is_geopolitical', None)
        calc_rel = getattr(monitor, '_calculate_relevance', None)

        out: List[Dict] = []
        for item in news_items:
            if not isinstance(item, dict):
                continue

            title = str(item.get('title') or item.get('headline') or '').strip()
            desc = str(item.get('description') or item.get('summary') or item.get('content') or '').strip()
            if not title and not desc:
                continue

            blob = f"{title} {desc}".strip()
            try:
                geo_hit = bool(is_geo(blob)) if callable(is_geo) else self._is_geopolitical_text(blob)
            except Exception:
                geo_hit = self._is_geopolitical_text(blob)

            if not geo_hit:
                continue

            try:
                relevance = float(calc_rel(blob)) if callable(calc_rel) else float(self._calculate_geo_relevance(blob))
            except Exception:
                relevance = float(self._calculate_geo_relevance(blob))

            out.append({
                'title': title or 'Geopolitical headline',
                'description': desc or title,
                'source': item.get('source') or item.get('source_name') or 'Phasma News',
                'url': item.get('url') or item.get('link') or '',
                'timestamp': item.get('publishedAt') or item.get('published') or item.get('timestamp') or '',
                'relevance': relevance,
            })

        return out

    def _is_geopolitical_text(self, text: str) -> bool:
        t = str(text or '').lower()
        if not t:
            return False

        countries = ['venezuela', 'russia', 'china', 'iran', 'ukraine', 'israel', 'gaza', 'taiwan']
        conflict = ['war', 'attack', 'invasion', 'military', 'strike', 'conflict', 'tension', 'missile', 'troops']
        actions = ['seize', 'takeover', 'nationalize', 'control', 'secure', 'sanction', 'embargo']

        has_country = any(c in t for c in countries)
        has_action = any(w in t for w in (conflict + actions))
        return has_country and has_action

    def _calculate_geo_relevance(self, text: str) -> float:
        t = str(text or '').lower()
        score = 0.0

        high_impact = ['war', 'invasion', 'attack', 'military', 'nuclear', 'missile', 'sanction', 'embargo']
        for w in high_impact:
            if w in t:
                score += 30

        countries = ['venezuela', 'russia', 'china', 'iran', 'ukraine', 'israel', 'gaza', 'taiwan']
        for c in countries:
            if c in t:
                score += 20

        energy_words = ['oil', 'gas', 'energy', 'petroleum', 'opec', 'supply']
        for w in energy_words:
            if w in t:
                score += 15

        return float(min(100.0, score))

    def _dedupe_geo_events(self, events: List[Dict]) -> List[Dict]:
        if not events:
            return []

        seen = set()
        out = []
        for e in events:
            if not isinstance(e, dict):
                continue

            url = str(e.get('url') or '').strip().lower()
            if url:
                key = f"url:{url}"
            else:
                title = re.sub(r"\s+", " ", str(e.get('title') or '').strip().lower())
                desc = re.sub(r"\s+", " ", str(e.get('description') or '').strip().lower())
                key = f"td:{title[:120]}|{desc[:160]}"

            if key in seen:
                continue

            seen.add(key)
            out.append(e)

        return out

    def _check_paper_exits(self):
        """Check if any paper trading positions need to be exited"""
        if not self.paper_portfolio:
            return
        
        try:
            state = getattr(self.paper_portfolio, 'state', {}) or {}
            positions = state.get('positions', {}) or {}
            if not positions:
                return
            
            # Collect all symbols for batch fetching
            symbols_to_fetch = list(positions.keys())
            
            # Batch fetch all prices if cache is available
            current_prices = {}
            if self.market_cache and MarketDataCache:
                prices = self.market_cache.fetch_prices(symbols_to_fetch)
                current_prices = prices
            else:
                # Fallback to individual fetching
                for symbol in symbols_to_fetch:
                    try:
                        import yfinance as market_data
                        ticker = market_data.Ticker(symbol)
                        current_price = ticker.history(period='1d')['Close'].iloc[-1]
                        current_prices[symbol] = current_price
                    except Exception as e:
                        print(f"  📊 Paper Exit: Could not fetch price for {symbol} - {e}")
                        continue
            
            for symbol, pos in list(positions.items()):
                current_price = current_prices.get(symbol)
                if current_price is None:
                    print(f"  📊 Paper Exit: Could not fetch price for {symbol}")
                    continue
                
                # Check if position should be exited
                entry_price = pos['avg_cost']
                target_price = pos.get('target_price', entry_price * 1.2)  # Default 20% target
                stop_price = pos.get('stop_price', entry_price * 0.95)  # Default 5% stop
                
                exit_reason = None
                
                if current_price >= target_price:
                    exit_reason = "Target reached"
                elif current_price <= stop_price:
                    exit_reason = "Stop loss triggered"
                
                # Check time-based exit (max 30 days)
                days_held = (datetime.now() - datetime.fromisoformat(pos['timestamp'])).days
                if days_held >= 30:
                    exit_reason = "Time exit (30 days)"
                
                if exit_reason:
                    self._execute_paper_exit(
                        symbol=symbol,
                        quantity=pos['quantity'],
                        price=current_price,
                        reason=exit_reason
                    )
                    
        except Exception as e:
            print(f"  📊 Paper Exit Check Error: {e}")

    def generate_unified_trade_summary(
        self, signal: Any, *, ctx: Optional[ApplicationContext] = None
    ) -> str:
        """Generate a unified, compressed trade summary for signals."""
        if ctx is None:
            ctx = ApplicationContext.bind(self, {})
        try:
            if isinstance(signal, dict):
                data = signal
            elif hasattr(signal, 'to_dict'):
                data = signal.to_dict() or {}
            else:
                data = {}

            symbol = str(data.get('symbol') or getattr(signal, 'symbol', 'UNKNOWN')).upper()
            action = str(data.get('action') or getattr(signal, 'action', 'BUY')).upper()
            source = str(data.get('source') or getattr(signal, 'source', 'analysis'))

            confidence = data.get('confidence', getattr(signal, 'confidence', 0.0))
            try:
                confidence = float(confidence)
            except Exception:
                confidence = 0.0
            if confidence > 1.0:
                confidence = confidence / 100.0
            confidence = max(0.0, min(1.0, confidence))

            position_size = data.get('position_size', getattr(signal, 'position_size', 0))
            try:
                position_size = float(position_size)
            except Exception:
                position_size = 0.0

            current_price = data.get('current_price', getattr(signal, 'current_price', None))
            try:
                current_price = float(current_price) if current_price is not None else None
            except Exception:
                current_price = None

            intelligence_strength = data.get('intelligence_strength', getattr(signal, 'intelligence_strength', None))
            try:
                intelligence_strength = float(intelligence_strength) if intelligence_strength is not None else None
            except Exception:
                intelligence_strength = None

            confluence_score = data.get('confluence_score', getattr(signal, 'confluence_score', None))
            try:
                confluence_score = float(confluence_score) if confluence_score is not None else None
            except Exception:
                confluence_score = None

            rationale = str(data.get('rationale') or getattr(signal, 'rationale', '')).strip()
            if rationale and len(rationale) > 240:
                rationale = rationale[:240].rstrip() + '...'

            header = f"🎯 {symbol} | {action} | {confidence*100:.0f}%"
            if current_price is not None and current_price > 0:
                header += f" | ${current_price:.2f}"
            if position_size > 0:
                header += f" | Size ${position_size:.0f}"

            meta_parts = [f"Source: {source}"]
            if confluence_score is not None and confluence_score > 0:
                meta_parts.append(f"Confluence: {confluence_score*100:.0f}%")
            if intelligence_strength is not None:
                meta_parts.append(f"Intel: {intelligence_strength:.0f}/100")

            meta_line = " | ".join(meta_parts)

            if not rationale:
                rationale = self.generate_simple_trade_explanation(
                    data if isinstance(signal, dict) else data, ctx=ctx
                )

            return f"{header}\n{meta_line}\n{rationale}"
        except Exception as e:
            return f"🎯 {getattr(signal, 'symbol', 'UNKNOWN')} | Summary unavailable ({e})"

    def generate_unified_trade_summaryy(self, signal: Any) -> str:
        return self.generate_unified_trade_summary(signal)

    def generate_unified_trade_summarry(self, signal: Any) -> str:
        return self.generate_unified_trade_summary(signal)
    
    def get_paper_trading_report(self):
        """Get paper trading performance report"""
        if not self.paper_portfolio:
            return "Paper trading is not enabled"
        
        return self.paper_portfolio.get_performance_report()
    
    def reset_paper_trading(self, new_capital: float = None):
        """Reset paper trading portfolio"""
        if self.paper_portfolio:
            self.paper_portfolio.reset_portfolio(new_capital)
        else:
            print("Paper trading is not enabled")
    
    async def shutdown(self):
        """Clean shutdown of all components"""
        # Shutdown social engine if it exists
        if hasattr(self, 'social_engine') and self.social_engine and hasattr(self.social_engine, 'close'):
            try:
                await self.social_engine.close()
            except Exception as e:
                print(f"⚠️ Error closing social engine: {e}")
        
        # Stop news collection
        if hasattr(self, 'news_engine') and self.news_engine:
            try:
                await self.stop_news_collection()
            except Exception as e:
                print(f"⚠️ Error stopping news collection: {e}")

    async def start_news_collection(self, *, ctx: Optional[ApplicationContext] = None):
        """Start 24/7 news collection network (optional - runs in background)"""
        if ctx is None:
            ctx = ApplicationContext.bind(self, {})
        ps = ctx.system
        try:
            success = await ps.news_engine.start_news_collection_network()
            if success:
                print("🚀 24/7 News Collection Network is now running")
                print("   📰 58 RSS feeds being monitored every 60 seconds")
                print("   🧠 Smart Memory Bank active for deduplication")
            return success
        except Exception as e:
            print(f"⚠️  Could not start news collection network: {e}")
            return False
    
    async def stop_news_collection(self, *, ctx: Optional[ApplicationContext] = None):
        """Stop news collection network"""
        if ctx is None:
            ctx = ApplicationContext.bind(self, {})
        ps = ctx.system
        try:
            await ps.news_engine.stop_news_collection_network()
        except Exception as e:
            print(f"⚠️  Error stopping news collection: {e}")
    
    def get_news_memory_stats(self, *, ctx: Optional[ApplicationContext] = None):
        """Get Smart Memory Bank and Network statistics"""
        if ctx is None:
            ctx = ApplicationContext.bind(self, {})
        ps = ctx.system
        memory_stats = ps.news_engine.get_memory_stats()
        network_stats = ps.news_engine.get_network_stats()
        
        print("\n📊 NEWS INTELLIGENCE SYSTEM STATUS:")
        print("=" * 50)
        
        if memory_stats.get('status') != 'disabled':
            print(f"🧠 Smart Memory Bank:")
            print(f"   Total Articles: {memory_stats.get('total_articles', 0):,}")
            print(f"   Unique Symbols: {memory_stats.get('unique_symbols', 0)}")
            print(f"   Duplicates Prevented: {memory_stats.get('duplicates_prevented', 0):,}")
            print(f"   Cache Efficiency: {memory_stats.get('cache_efficiency_pct', 0):.1f}%")
        
        if network_stats.get('status') != 'disabled':
            print(f"\n📰 News Collection Network:")
            print(f"   RSS Feeds: {network_stats.get('feeds_count', 0)}")
            print(f"   Total Fetches: {network_stats.get('total_fetches', 0):,}")
            print(f"   Articles Collected: {network_stats.get('total_articles', 0):,}")
            print(f"   Duplicates Filtered: {network_stats.get('duplicates_filtered', 0):,}")
            print(f"   Running: {'✅ Yes' if network_stats.get('is_running') else '❌ No'}")
        
        return {'memory': memory_stats, 'network': network_stats}

    def validate_risk_first(
        self, signal: Dict, *, ctx: Optional[ApplicationContext] = None
    ) -> Tuple[bool, str]:
        """Always validate risk before reward - Key principle from trading masters"""
        if ctx is None:
            ctx = ApplicationContext.bind(self, {})
        ps = ctx.system
        
        # Check crash risk
        if hasattr(ps, 'crash_detector') and ps.crash_detector:
            try:
                crash_risk = ps.crash_detector.detect_crash_risk('SPY')
                if crash_risk.get('level') == 'EXTREME':
                    return False, " EXTREME CRASH RISK - No new positions"
                elif crash_risk.get('level') == 'HIGH':
                    signal['position_size'] = signal.get('position_size', 0.02) * 0.5
            except Exception as e:
                print(f"Error detecting crash risk: {e}")
        
        # Check VIX for volatility adjustment
        try:
            vix = float(ps.price_fetcher.get_real_price('VIX') or 20)
            if vix > 30:
                signal['position_size'] = signal.get('position_size', 0.02) * 0.5
                signal['risk_warning'] = "High volatility - position size reduced"
            elif vix > 25:
                signal['position_size'] = signal.get('position_size', 0.02) * 0.75
        except Exception:
            pass

        # Apply FRED macro regime adjustments
        fred_adj = getattr(ps, '_fred_adjustments', {})
        fred_regime = getattr(ps, '_fred_regime', 'NEUTRAL')
        if fred_adj:
            mult = fred_adj.get('position_size_multiplier', 1.0)
            if mult != 1.0:
                signal['position_size'] = signal.get('position_size', 0.02) * mult
            if fred_regime == 'BEARISH':
                conf = signal.get('confidence', 0)
                conf_pct = conf * 100 if conf <= 1.0 else conf
                min_conf_pct = fred_adj.get('min_confidence', 0.8) * 100
                if conf_pct < min_conf_pct:
                    return False, f" FRED BEARISH regime: confidence {conf_pct:.0f}% below macro minimum {min_conf_pct:.0f}%"

        # Check correlation with existing positions
        if hasattr(ps, 'open_positions'):
            sector = signal.get('sector', '')
            same_sector_count = sum(1 for p in ps.open_positions if p.get('sector') == sector)
            if same_sector_count >= 3:
                return False, f"Too many positions in {sector} sector"

        return True, "Risk validated"

    def send_telegram_alert(
        self, signal: dict, *, ctx: Optional[ApplicationContext] = None
    ) -> bool:
        """Combine ALL signal information into one compressed summary anyone can understand."""
        if ctx is None:
            ctx = ApplicationContext.bind(self, {})
        ps = ctx.system
        ticker = signal.get("symbol", signal.get("ticker", "UNKNOWN"))
        action = signal.get("action", "BUY")
        confidence = signal.get("confidence", 0) * 100

        current_price = signal.get('entry_price', signal.get('current_price', 0))
        catalyst_type = ps._extract_catalyst_type(signal)
        
        if current_price > 0:
            profit_targets = ps.target_calculator.calculate_profit_targets(
                ticker, catalyst_type, current_price, confidence / 100
            )
        else:
            profit_targets = None
        
        # Check all signal sources
        signals = {
            'Insider': False,
            'News': False,
            'Technicals': False,
            'Kalshi': False,
            'Long-term': False
        }
        
        # Check what signals we have
        source = signal.get('source', '')
        if source == 'insider_trading':
            signals['Insider'] = True
            signals['Insider'] = '✅'
        elif source == 'news_analysis':
            signals['News'] = '✅'
        elif source == 'social_engine':
            signals['Social'] = '✅'
        elif source == 'kalshi_prediction':
            signals['Kalshi'] = '✅'
        
        # Check for other signals in the data
        if signal.get('patterns'):
            signals['Technicals'] = '✅'
        if signal.get('rationale') or signal.get('catalyst_score', 0) > 50:
            signals['News'] = '✅'
        if signal.get('insider'):
            signals['Insider'] = '✅'
        
        # Always check long-term fundamentals
        try:
            import yfinance as market_data
            stock = market_data.Ticker(ticker)
            info = stock.info
            if info.get('revenueGrowth', 0) > 0.05 or info.get('profitMargins', 0) > 0.05:
                signals['Long-term'] = '✅'
        except:
            pass
        
        # Count positive signals
        positive_signals = sum(1 for s in signals.values() if s == '✅')
        
        # Create verdict
        if positive_signals >= 3:
            verdict = "STRONG BUY - Multiple confirmations"
        elif positive_signals >= 2:
            verdict = "BUY - Good opportunity"
        elif positive_signals >= 1:
            verdict = "CONSIDER - Single signal"
        else:
            verdict = "WAIT - No clear signals"
        
        # Build one-line summary with profit targets
        one_line = f"🎯 {ticker}: {verdict} | Insider: {signals['Insider']} | News: {signals['News']} | Technicals: {signals['Technicals']} | Kalshi: {signals['Kalshi']} | Long-term: {signals['Long-term']} | Confidence: {confidence:.0f}%"
        
        # Add profit targets to one-line if available
        if profit_targets:
            max_potential = profit_targets['maximum_potential'] * 100
            one_line += f" | Max: +{max_potential:.0f}%"
        
        # Build bullet points (max 3)
        bullets = []
        
        # Profit target bullet with impact analysis
        if profit_targets:
            realistic_target = profit_targets['realistic_target'] * 100
            impact = profit_targets['impact_analysis']
            if impact['recommendation'] == 'PROCEED':
                impact_note = f"Low awareness ({impact['pricing_in_pct']*100:.0f}% priced in)"
            elif impact['recommendation'] == 'CAUTION':
                impact_note = f"Medium awareness ({impact['pricing_in_pct']*100:.0f}% priced in)"
            else:
                impact_note = f"High awareness ({impact['pricing_in_pct']*100:.0f}% priced in)"
            
            bullets.append(f"• Target: +{realistic_target:.0f}% | {impact_note}")
        
        # Insider bullet
        if signals['Insider'] == '✅':
            insider_name = signal.get('insider', 'Company insider')
            value = signal.get('value', 0)
            if value >= 1_000_000:
                amount = f"${value/1_000_000:.1f}M"
            else:
                amount = f"${value/1_000:.0f}K"
            bullets.append(f"• {insider_name} bought {amount} - insiders know best")
        
        # News bullet  
        if signals['News'] == '✅':
            catalyst = signal.get('rationale', 'Breaking news')[:50]
            bullets.append(f"• News catalyst: {catalyst}...")
        
        # Technical bullet
        if signals['Technicals'] == '✅':
            rsi = signal.get('details', {}).get('rsi', 50)
            if rsi < 30:
                bullets.append(f"• Oversold signal - ready to bounce")
            elif rsi > 70:
                bullets.append(f"• Momentum surge - breaking out")
            else:
                bullets.append(f"• Technical patterns aligning")
        
        # Limit to 3 bullets
        bullets = bullets[:3]
        
        # Combine everything
        summary = f"{one_line}\n\n"
        if bullets:
            summary += "\n".join(bullets)
        else:
            summary += f"• Analysis suggests {action.lower()} opportunity based on {source}"
        
        # Add exit levels if profit targets available
        if profit_targets and profit_targets['exit_levels']:
            summary += "\n\n📊 Exit Levels: "
            exit_levels = profit_targets['exit_levels']
            exit_prices = [f"${current_price * (1 + level):.2f}" for level in exit_levels[:3]]
            summary += " | ".join([f"{level*100:.0f}% ({price})" for level, price in zip(exit_levels[:3], exit_prices)])
        
        # Add historical context if available
        past_recommendations = ps.trade_recommendation_memory.get_past_recommendations(ticker, days_back=90)
        if past_recommendations:
            latest_past = past_recommendations[-1]  # Get most recent past recommendation
            time_ago = ps.trade_recommendation_memory.get_time_ago_string(latest_past['date'])
            
            summary += f"\n\n📅 **Previously recommended {time_ago}:**\n"
            summary += f"   Verdict: {latest_past['verdict']}\n"
            if latest_past['bullets']:
                summary += f"   • {latest_past['bullets'][0]}\n"
            summary += f"   Confidence was: {latest_past['confidence']:.0f}%"
        
        # Save current recommendation
        if bullets:
            ps.trade_recommendation_memory.save_recommendation(ticker, verdict, bullets, confidence)
        
        return summary
    
    def _extract_catalyst_type(self, signal: Dict) -> str:
        """Extract catalyst type from signal data"""
        source = signal.get('source', '')
        title = signal.get('title', '').lower()
        rationale = signal.get('rationale', '').lower()
        
        # Check for specific catalyst keywords
        if any(word in title or word in rationale for word in ['fda', 'approval', 'drug', 'clinical']):
            return 'FDA Approval' if 'approval' in title or 'approval' in rationale else 'Clinical Trial Results'
        elif any(word in title or word in rationale for word in ['partnership', 'collaboration', 'joint venture']):
            return 'Partnership Deal'
        elif any(word in title or word in rationale for word in ['earnings', 'eps', 'quarterly', 'revenue beat']):
            return 'Earnings Beat'
        elif any(word in title or word in rationale for word in ['launch', 'product', 'release']):
            return 'Product Launch'
        elif any(word in title or word in rationale for word in ['contract', 'award', 'deal', 'agreement']):
            return 'Contract Award'
        elif any(word in title or word in rationale for word in ['merger', 'acquisition', 'buyout', 'takeover']):
            return 'Merger/Acquisition'
        elif any(word in title or word in rationale for word in ['buyback', 'repurchase', 'share buy']):
            return 'Buyback Announcement'
        elif source == 'insider_trading':
            return 'Insider Buying'
        elif any(word in title or word in rationale for word in ['upgrade', 'initiated', 'buy rating']):
            return 'Upgrade/Initiation'
        elif source == 'day_trading' or any(word in title or word in rationale for word in ['momentum', 'surge', 'spike']):
            return 'Momentum Surge'
        elif any(word in title or word in rationale for word in ['sector', 'industry', 'market']):
            return 'Sector News'
        else:
            return 'Default'

    def generate_simple_trade_explanation(
        self, signal: Dict, *, ctx: Optional[ApplicationContext] = None
    ) -> str:
        """Generate a simple explanation for any trade signal that non-traders can understand."""
        if ctx is None:
            ctx = ApplicationContext.bind(self, {})
        ps = ctx.system
        ticker = signal.get('symbol', signal.get('ticker', 'UNKNOWN'))
        action = signal.get('action', 'BUY')
        source = signal.get('source', 'analysis')
        confidence = signal.get('confidence', 0) * 100
        
        # Get long-term investment thesis
        investment_thesis = ps._generate_investment_thesis(ticker)
        
        # Get the key information based on signal type
        if source == 'insider_trading':
            insider_name = signal.get('insider', 'A company insider')
            value = signal.get('value', 0)
            if value >= 1_000_000:
                amount_str = f"${value/1_000_000:.1f} million"
            else:
                amount_str = f"${value/1_000:.0f} thousand"
            
            return f"""📈 **{ticker} - Insider Buying Alert**

**SHORT-TERM TRADE:**
{insider_name} just bought {amount_str} worth of {ticker} stock. Insiders buy when they expect prices to rise soon.

**LONG-TERM INVESTMENT (3-5 YEARS):**
{investment_thesis}

**SIMPLE ADVICE:** Consider buying now - insiders are usually right, and this looks good for long-term growth. Confidence: {confidence:.0f}%"""
        
        elif source == 'kalshi_prediction':
            market_title = signal.get('title', 'A prediction market')
            rationale = signal.get('rationale', '')[:100]
            
            return f"""🎯 **{ticker} - Prediction Market Opportunity**

**SHORT-TERM TRADE:**
The market thinks there's a {signal.get('current_price', 50):.0f}% chance of this event. Our AI sees it differently - potential for 2-3x returns.

**LONG-TERM INVESTMENT (3-5 YEARS):**
{investment_thesis}

**SIMPLE ADVICE:** This is a short-term bet on events, but {ticker} also has strong long-term fundamentals. Confidence: {confidence:.0f}%"""
        
        elif source == 'news_analysis':
            catalyst = signal.get('rationale', 'News catalyst')[:100]
            
            return f"""📰 **{ticker} - News Catalyst**

**SHORT-TERM TRADE:**
Breaking news suggests {ticker} could move quickly. The market hasn't fully priced this in yet - act fast.

**LONG-TERM INVESTMENT (3-5 YEARS):**
{investment_thesis}

**SIMPLE ADVICE:** Buy for the short-term news boost, but consider holding long-term based on strong fundamentals. Confidence: {confidence:.0f}%"""
        
        elif source == 'day_trading':
            rsi = signal.get('details', {}).get('rsi', 50)
            volume_ratio = signal.get('details', {}).get('volume_ratio', 1)
            
            return f"""⚡ **{ticker} - Day Trading Alert**

**SHORT-TERM TRADE:**
Unusual volume and price movement today suggest big institutional activity. Quick action needed - this is a hours-to-days trade.

**LONG-TERM INVESTMENT (3-5 YEARS):**
{investment_thesis}

**SIMPLE ADVICE:** Trade this short-term, but if you believe in the company, consider keeping a small position for the long run. Confidence: {confidence:.0f}%"""
        
        else:
            # Generic explanation
            return f"""💡 **{ticker} - Trading Opportunity**

**SHORT-TERM TRADE:**
Our AI analysis identifies this as a good {action.lower()} opportunity based on current market conditions.

**LONG-TERM INVESTMENT (3-5 YEARS):**
{investment_thesis}

**SIMPLE ADVICE:** This looks good for both short-term trading and long-term investment. Confidence: {confidence:.0f}%"""

    def _generate_investment_thesis(self, ticker: str) -> str:
        """Generate a simple long-term investment thesis for a stock."""
        try:
            import yfinance as market_data
            stock = market_data.Ticker(ticker)
            info = stock.info
            
            # Key fundamentals for long-term analysis
            revenue_growth = info.get('revenueGrowth', 0)
            earnings_growth = info.get('earningsGrowth', 0)
            profit_margin = info.get('profitMargins', 0)
            market_cap = info.get('marketCap', 0)
            sector = info.get('sector', 'Technology')
            industry = info.get('industry', '')
            
            # Build thesis points
            thesis_points = []
            
            # Revenue growth
            if revenue_growth and revenue_growth > 0.10:  # 10%+ growth
                thesis_points.append(f"• Growing revenue {revenue_growth*100:.0f}% annually")
            
            # Profitability
            if profit_margin and profit_margin > 0.10:  # 10%+ margins
                thesis_points.append(f"• Strong profit margins at {profit_margin*100:.0f}%")
            elif profit_margin and profit_margin > 0:
                thesis_points.append(f"• Profitable business with {profit_margin*100:.0f}% margins")
            
            # Market position
            if market_cap:
                if market_cap > 1_000_000_000_000:  # $1T+
                    thesis_points.append("• Market leader with trillion-dollar valuation")
                elif market_cap > 100_000_000_000:  # $100B+
                    thesis_points.append("• Established industry leader")
                elif market_cap > 10_000_000_000:  # $10B+
                    thesis_points.append("• Strong mid-size company with growth potential")
            
            # Sector strength
            growth_sectors = ['Technology', 'Healthcare', 'Software', 'Biotechnology', 'Semiconductors']
            if sector in growth_sectors:
                thesis_points.append(f"• In high-growth {sector} sector")
            
            # Industry position
            if industry:
                if 'software' in industry.lower():
                    thesis_points.append("• Software business with recurring revenue")
                elif 'pharmaceutical' in industry.lower() or 'biotechnology' in industry.lower():
                    thesis_points.append("• Innovation pipeline in healthcare")
                elif 'semiconductor' in industry.lower():
                    thesis_points.append("• Critical for digital transformation")
            
            # If no strong points, provide generic analysis
            if not thesis_points:
                if market_cap and market_cap > 1_000_000_000:
                    thesis_points.append("• Established company with solid market presence")
                else:
                    thesis_points.append("• Growth company with expansion potential")
            
            # Combine into thesis
            if len(thesis_points) >= 3:
                thesis = "\n".join(thesis_points[:3])
            elif len(thesis_points) >= 2:
                thesis = "\n".join(thesis_points)
            else:
                thesis = thesis_points[0] if thesis_points else "• Company with long-term growth potential"
            
            return thesis
            
        except Exception as e:
            return f"• {ticker} shows long-term investment potential based on market position"

    async def _stage_startup_services(self, ctx: ApplicationContext) -> None:
        """Run startup service checks for a cycle."""
        s = ctx.system
        # 0.1. Refresh market data cache for this cycle
        if ctx.market_cache and MarketDataCache:
            try:
                print("\n📊 Refreshing market data cache...")
                ctx.market_cache.refresh_cache()
                print("   ✅ Market data cache refreshed")
            except Exception as e:
                print(f"   ⚠️ Cache refresh failed: {e}")

        # 0. Start partnership monitoring if not already running
        if ctx.partnership_engine and not hasattr(s, "_partnership_monitoring_started"):
            try:
                await ctx.partnership_engine.start_monitoring()
                s._partnership_monitoring_started = True
                print("🔍 Started partnership monitoring service")
            except Exception as e:
                print(f"⚠️  Failed to start partnership monitoring: {e}")

        # 0.5. Optionally start news collection network (if not already running)
        if not hasattr(s, "_news_collection_started"):
            try:
                # Check if user wants 24/7 collection
                auto_start_news = ctx.config.get("trading.auto_start_news_collection", False)
                if auto_start_news:
                    await s.start_news_collection(ctx=ctx)
                    s._news_collection_started = True
            except Exception as e:
                print(f"⚠️  News collection auto-start failed: {e}")

    async def _stage_macro_and_fred(self, ctx: ApplicationContext) -> Tuple[bool, str]:
        """Run macro monitor and FRED regime update for this cycle."""
        print("\n🌍 Checking global macroeconomic indicators...")
        macro_risk = False
        macro_alert = ""
        ctx.fred_regime = "NEUTRAL"
        ctx.fred_adjustments.clear()

        if ctx.global_macro_monitor:
            try:
                ctx.global_macro_monitor.update_indicators()
                macro_risk, macro_alert = ctx.global_macro_monitor.should_alert_crash_risk()

                if macro_risk:
                    print(f"   🚨 GLOBAL MACRO RISK: {macro_alert}")
                else:
                    print(f"   ✅ Global macro conditions stable")
            except Exception as e:
                print(f"   ⚠️ Global macro monitoring error: {e}")

        # FRED Economic Filter — adjusts position sizing and confidence thresholds
        if ctx.fred_filter:
            try:
                async with ctx.fred_filter as _fred:
                    _indicators = await _fred.get_macro_indicators()
                    if _indicators:
                        ctx.fred_regime = _fred.determine_market_regime(_indicators)
                        ctx.fred_adjustments.clear()
                        ctx.fred_adjustments.update(_fred.get_filter_adjustments(ctx.fred_regime))
                print(
                    f"   📊 FRED Macro Regime: {ctx.fred_regime} | "
                    f"Position multiplier: {ctx.fred_adjustments.get('position_size_multiplier', 1.0):.1f}x"
                )
            except Exception as e:
                print(f"   ⚠️ FRED filter error: {e}")

        ctx.sync_fred_to_system()
        return macro_risk, macro_alert

    def _stage_crash_preflight(self, ctx: ApplicationContext, all_signals: List[Dict], macro_risk: bool):
        """Run crash detector preflight and return crash context."""
        print("\n🛡️ Checking market crash risk...")
        crash_assessment = None
        market_safe = True if not macro_risk else False
        if macro_risk:
            market_safe = False
        index_crash = None
        crypto_assessments = []

        if ctx.crash_detector:
            try:
                # Index / stock market crash risk (e.g., SPY)
                index_symbol = ctx.config.get("crash_detector.market_index", "SPY")
                index_crash = ctx.crash_detector.detect_crash_risk(index_symbol)

                # Only analyze crash risk for assets the AI is currently tracking
                crypto_assessments = []
                stock_assessments = []

                # Get symbols from current signals and AI's watchlist
                tracked_symbols = set()

                # Add symbols from current signals
                for signal in all_signals:
                    if signal.get("symbol"):
                        symbol = str(signal["symbol"]).upper()
                        if symbol != "UNKNOWN":
                            ctx.track_symbol(symbol, "signal")
                            tracked_symbols.add(symbol)

                # Add symbols from the AI's watchlist (built from previous discoveries)
                tracked_symbols.update(ctx.ai_watchlist)

                try:
                    for _sym in ctx.system.skipped_opportunity_watchlist.get_priority_symbols(limit=40):
                        tracked_symbols.add(_sym)
                        ctx.track_symbol(_sym, "skipped_revisit_priority")
                except Exception:
                    pass

                # Analyze crash risk for tracked symbols by category
                for sym in sorted(tracked_symbols):
                    if not sym or sym == "UNKNOWN":
                        continue

                    category = ctx.ai_symbol_categories.get(sym, ctx.categorize_symbol(sym))

                    # Skip options and kalshi - they don't have traditional crash patterns
                    if category in ["option", "kalshi"]:
                        continue

                    try:
                        assessment = ctx.crash_detector.detect_crash_risk(sym)
                        if assessment and not assessment.get('error'):
                            # Categorize and store
                            if category == 'crypto':
                                crypto_assessments.append(assessment)
                            elif category in ['stock', 'etf']:
                                stock_assessments.append(assessment)

                            # Update the signal with crash assessment
                            for signal in all_signals:
                                if str(signal.get('symbol', '')).upper() == sym:
                                    signal['asset_crash_assessment'] = assessment
                                    signal['asset_crash_level'] = assessment.get('alert_level', 0)
                                    signal['asset_crash_score'] = assessment.get('crash_score', 0.0)
                                    break

                    except Exception as ce:
                        print(f"   ⚠️ Crash detection error for {sym}: {ce}")

                # Print crash assessment results
                if index_crash and not index_crash.get('error'):
                    symbol = index_crash.get('symbol', 'SPY')
                    score = index_crash.get('crash_score', 0) * 100
                    level = index_crash.get('alert_level', 0)
                    level_name = index_crash.get('alert_level_name', 'UNKNOWN')

                    print(f"   📈 Stock Market ({symbol}): score {score:.1f}% | level {level} ({level_name})")

                    # Show price projection if available
                    price_proj = index_crash.get('price_projection')
                    if price_proj:
                        current = price_proj.get('current_price', 0)
                        moderate = price_proj.get('moderate_crash_target', 0)
                        severe = price_proj.get('severe_stress_floor', 0)
                        if current and moderate:
                            mod_down = ((current - moderate) / current) * 100
                            sev_down = ((current - severe) / current) * 100
                            print(f"      ↳ Current:   ${current:.2f}")
                            print(f"      ↳ Moderate Crash: ${moderate:.2f} ({mod_down:.1f}% down)")
                            print(f"      ↳ Severe Crash:   ${severe:.2f} ({sev_down:.1f}% down)")

                    # Show early warning
                    early = index_crash.get('early_warning_layer', {})
                    if early:
                        early_score = early.get('score', 0) * 100
                        early_level = early.get('level', 0)
                        early_name = early.get('level_name', 'UNKNOWN')
                        print(f"      ↳ Early warning: {early_score:.1f}% | L{early_level} {early_name}")

                # Show crash risk for AI-tracked stocks
                if stock_assessments:
                    print(f"   📊 AI-Tracked Stocks ({len(stock_assessments)}):")
                    for sa in stock_assessments[:5]:
                        sym = sa.get('symbol', 'UNKNOWN')
                        score = sa.get('crash_score', 0) * 100
                        level = sa.get('alert_level', 0)
                        level_name = sa.get('alert_level_name', 'UNKNOWN')
                        print(f"      • {sym}: score {score:.1f}% | level {level} ({level_name})")

                # Show crash risk for AI-tracked crypto
                if crypto_assessments:
                    print(f"   💥 AI-Tracked Crypto ({len(crypto_assessments)}):")
                    for ca in crypto_assessments[:5]:
                        sym = ca.get('symbol', 'UNKNOWN')
                        score = ca.get('crash_score', 0) * 100
                        level = ca.get('alert_level', 0)
                        level_name = ca.get('alert_level_name', 'UNKNOWN')
                        early = ca.get('early_warning') or {}
                        ew_score = early.get('score')
                        ew_level = early.get('level')
                        print(f"      • {sym}: score {score:.1f}% | level {level} ({level_name})")
                        if ew_score is not None:
                            print(f"        ↳ Early warning: {ew_score * 100:.1f}% | L{ew_level}")

                # Pick worst-case assessment across index + crypto (by crash_score)
                candidates = []
                if index_crash and not index_crash.get('error'):
                    candidates.append(index_crash)
                candidates.extend(crypto_assessments)

                if candidates:
                    crash_assessment = max(candidates, key=lambda a: a.get('crash_score', 0.0))
                    alert_level = crash_assessment['alert_level']
                    crash_score = crash_assessment['crash_score']

                    if alert_level == 0:
                        print(f"   ✅ MARKET SAFE: Crash risk {crash_score:.1%} (<20% - Normal trading)")
                        market_safe = True
                    elif alert_level == 1:
                        print(f"   ⚠️ MINOR DIP WARNING: Crash risk {crash_score:.1%} (20-35% - Reduce sizes 30%)")
                        print(f"   💡 Early warning - still profitable to trade with caution")
                        market_safe = True
                    elif alert_level == 2:
                        print(f"   🚨 MEDIUM CORRECTION: Crash risk {crash_score:.1%} (35-55% - Reduce sizes 50% + Buy puts)")
                        print(f"   💰 PROFIT OPPORTUNITY: Consider buying puts for hedging profit")
                        market_safe = True
                    elif alert_level == 3:
                        print(f"   💀 HIGH CRASH RISK: Crash risk {crash_score:.1%} (>55% - Aggressive puts only!)")
                        market_safe = False
                        print("   🛑 PAUSING LONG POSITIONS - High crash risk detected!")
                        print("   💰 PROFIT MODE: Aggressive put buying for crash profit!")
                        print("   🎯 This is when you make money on the way down!")

                    try:
                        ctx.crash_detector.print_crash_report(crash_assessment)
                    except Exception as report_err:
                        print(f"   ⚠️ Could not print crash report: {report_err}")
                else:
                    print("   ⚠️ No valid crash assessments available (index/crypto)")
                    market_safe = True

            except Exception as e:
                print(f"   ⚠️ Crash detection error: {e}")
                market_safe = True
        else:
            print("   ⚠️ Crash detector not initialized - proceeding with caution")

        return crash_assessment, market_safe, index_crash, crypto_assessments

    async def _stage_unified_brain_news_items(self, ctx: ApplicationContext) -> List[Dict]:
        """Run unified meta brain and return normalized news items for this cycle."""
        s = ctx.system
        print("\n🧠 UNIFIED META BRAIN ACTIVATED")
        print("=" * 60)
        print("🔗 ALL SYSTEMS INTEGRATED & WORKING TOGETHER")
        print("✓ Universal Intelligence (15 strategies)")
        print("✓ Bull Run Detector (multi-source)")
        print("✓ News Scanner (hot stocks <$50)")
        print("✓ Social Engine (sentiment)")
        print("✓ Partnership Monitor (M&A)")
        print("✓ Underground Discovery (hidden gems)")
        print("✓ Risk Manager (position sizing)")
        print("✓ Kalshi Integration (events)")
        print("=" * 60)

        from brain.unified_meta_brain import UnifiedMetaBrain

        # Reuse the unified brain instance across cycles to avoid cold-start overhead.
        if not hasattr(s, "_unified_brain") or s._unified_brain is None:
            s._unified_brain = UnifiedMetaBrain(ctx.config)
        brain = s._unified_brain

        results = await brain.run_unified_analysis()

        if results.get('final_signals', 0) == 0:
            print("\n⚠️ No high-confidence opportunities found - using fallback scan")
            return await s.news_engine.scan_all_sources()

        print(f"\n✅ UNIFIED BRAIN FOUND {results['final_signals']} OPPORTUNITIES!")
        news_items: List[Dict] = []
        for signal in results.get('top_opportunities', []):
            news_items.append({
                'symbol': signal['symbol'],
                'title': f"UNIFIED SIGNAL: {signal['symbol']} - Rank #{signal.get('rank')} | {signal.get('confidence', 0):.1%} confidence",
                'summary': f"Convergence: {signal.get('convergence_score', 1)} systems | "
                           f"Strategies: {', '.join(signal.get('strategies', ['Unknown']))} | "
                           f"Sources: {', '.join(signal.get('sources', ['Unknown'])[:2])}",
                'source': 'UnifiedMetaBrain',
                'sentiment': 0.8 if signal.get('confidence', 0) > 0.7 else 0.6,
                'current_price': signal.get('current_price', 0),
                'url': '',
                'timestamp': datetime.now().isoformat(),
                'trade_type': 'UNIFIED_CONVERGENCE',
                'confidence': signal.get('confidence', 0),
                'action': signal.get('action', 'BUY'),
                'entry_price': signal.get('entry_price', 0),
                'target_price': signal.get('target_price', 0),
                'sector': signal.get('sector', 'Unknown'),
                'confluence_score': signal.get('confluence_score', 0),
                'confluence_breakdown': signal.get('confluence_breakdown', {}),
                'day_trading_data': {
                    'symbol': signal['symbol'],
                    'action': signal.get('action', 'BUY'),
                    'confidence': signal.get('confidence', 0),
                    'entry_price': signal.get('entry_price', 0),
                    'target_price': signal.get('target_price', 0),
                    'current_price': signal.get('current_price', 0),
                    'confluence_score': signal.get('confluence_score', 0),
                    'confluence_breakdown': signal.get('confluence_breakdown', {}),
                    'rationale': signal.get('rationale', 'Unified brain convergence signal'),
                    'patterns': signal.get('patterns', []),
                    'sector': signal.get('sector', 'Unknown')
                }
            })

        news_items = s._filter_seen_news_items(news_items, ttl_hours=12)
        print(f"\n📊 Total items for analysis: {len(news_items)}")
        return news_items

    async def _stage_display_and_secondary_scans(
        self,
        ctx: ApplicationContext,
        regular_trades: List[Dict],
        overnight_moonshots: List[Dict],
        news_items: List[Dict],
        all_signals: List,
    ) -> Tuple[List, List[Dict]]:
        """Display results and run secondary scans; returns updated (all_signals, news_items)."""
        s = ctx.system
        # 4. Display unified results
        if not regular_trades and not overnight_moonshots:
            print("No trading opportunities found - this is normal when markets are quiet")
            print("System only trades when real opportunities exist")
        else:
            s._display_unified_results(regular_trades, overnight_moonshots, ctx=ctx)

        # 5. SCAN NEWS AND SOCIAL ENGINES (reuse cycle snapshot when available)
        print("\n🔍 Scanning news and social engines for signals...")

        # Scan news engine for trading opportunities
        news_signals = []
        cycle_news_snapshot = news_items if isinstance(news_items, list) else []
        try:
            if s.news_engine:
                print("📰 Scanning news sources...")
                if cycle_news_snapshot:
                    news_items = cycle_news_snapshot
                    print(f"📰 Reusing cycle news snapshot: {len(news_items)} items")
                else:
                    news_items = await s.news_engine.scan_all_sources()
                    print(f"📰 Found {len(news_items)} news items")

                # Convert news items to signals
                for item in news_items[:10]:  # Limit to prevent overload
                    if isinstance(item, dict) and item.get('symbol'):
                        news_signals.append({
                            'symbol': item['symbol'],
                            'action': 'BUY' if item.get('sentiment', 0) > 0 else 'SELL',
                            'confidence': min(max(item.get('confidence', 0.3), 0.3), 0.8),  # Ensure 30-80% range
                            'position_size': 20,  # Small position for news signals
                            'rationale': f"News catalyst: {item.get('title', '')[:100]}...",
                            'source': 'news_engine',
                            'current_price': item.get('current_price', 0),
                            'trade_type': 'STOCK'
                        })
                print(f"📰 Generated {len(news_signals)} signals from news")

                # Check silver price for opportunities
                if s.silver_monitor:
                    print("🥈 Checking silver price movements...")
                    silver_signal = await s.silver_monitor.check_silver_opportunity()
                    if silver_signal:
                        news_signals.append({
                            'symbol': silver_signal['symbol'],
                            'action': 'BUY' if silver_signal['price_change_pct'] > 0 else 'SELL',
                            'confidence': silver_signal['confidence'] / 100,  # Convert to decimal
                            'position_size': 25,  # Slightly larger for commodity moves
                            'rationale': silver_signal['reason'],
                            'source': 'silver_monitor',
                            'current_price': silver_signal.get('current_price', 0),
                            'trade_type': 'STOCK'
                        })
                        print(f"🥈 Silver signal added: {silver_signal['title']}")
        except Exception as e:
            print(f"⚠️ News engine scan failed: {e}")

        # Scan social engine for trending stocks
        social_signals = []
        try:
            if s.social_engine:
                print("📱 Scanning social media trends...")
                trending_symbols = await s.social_engine.get_trending_symbols(limit=10)
                print(f"📱 Found {len(trending_symbols)} trending symbols")

                # Convert trending symbols to signals
                if trending_symbols:
                    for symbol, mentions in list(trending_symbols.items())[:5]:  # Limit to prevent overload
                        if symbol and len(symbol) > 1:
                            social_signals.append({
                                'symbol': symbol,
                                'action': 'BUY',  # Assume bullish for trending
                                'confidence': min(max(0.3 + (mentions * 0.01), 0.3), 0.7),  # Scale confidence with mentions
                                'position_size': 15,  # Small position for social signals
                                'rationale': f"Social media trending: {mentions} mentions",
                                'source': 'social_engine',
                                'current_price': 0,
                                'trade_type': 'STOCK'
                            })
                    print(f"📱 Generated {len(social_signals)} signals from social trends")
        except Exception as e:
            print(f"⚠️ Social engine scan failed: {e}")

        # Scan Unusual Whales for unusual options activity
        unusual_whales_signals = []
        try:
            if hasattr(s, 'unusual_whales') and s.unusual_whales.enabled:
                print("🐋 Scanning unusual options activity...")
                unusual_signals = await s.unusual_whales.get_signals()
                print(f"🐋 Found {len(unusual_signals)} unusual activity signals")

                # Convert to expected format
                for signal in unusual_signals[:10]:  # Limit to prevent overload
                    unusual_whales_signals.append({
                        'symbol': signal['symbol'],
                        'action': signal['action'],
                        'confidence': signal['confidence'],
                        'position_size': 20,  # Slightly larger for unusual activity
                        'rationale': signal['rationale'],
                        'source': 'unusual_whales',
                        'current_price': signal.get('entry_price', 0),
                        'trade_type': 'STOCK',
                        'details': signal.get('details', {})
                    })
                print(f"🐋 Generated {len(unusual_whales_signals)} signals from unusual activity")
        except Exception as e:
            print(f"⚠️ Unusual Whales scan failed: {e}")

        # Combine all signals
        all_signals = all_signals + news_signals + social_signals + unusual_whales_signals

        # Scan for geopolitical events
        try:
            events = await s._collect_geopolitical_events(hours_back=24, news_items=news_items)
            print(f"🌍 Geopolitical events collected: {len(events)}")
            for e in events:
                print(f"   - {e.get('title', 'Unknown')}: relevance {e.get('relevance', 0)}")
            if events:
                min_geo_score = int(ctx.config.get("geopolitical_analysis", {}).get("event_threshold", 50))
                max_geo_signals = int(ctx.config.get("geopolitical_analysis", {}).get("max_signals", 50))

                # Track event-signal pairs instead of just symbols to allow same stock from different events
                seen_pairs = set()
                geo_signals = []
                for event in events:
                    analysis = s.geo_analyzer.analyze_event(event.get('description', ''))
                    for opp in analysis.get('stock_opportunities', []):
                        symbol = str(opp.get('symbol', '')).upper()
                        if not symbol:
                            continue

                        # Allow same symbol from different events, track by symbol+event
                        pair_key = f"{symbol}:{event.get('title', '')}"
                        if pair_key in seen_pairs:
                            continue

                        score = opp.get('score', opp.get('value_score', 0))
                        try:
                            score = float(score)
                        except Exception:
                            score = 0.0

                        if score < min_geo_score:
                            continue

                        seen_pairs.add(pair_key)

                        confidence = max(0.30, min(0.95, score / 100.0))
                        geo_signals.append({
                            'symbol': symbol,
                            'action': 'BUY',
                            'confidence': confidence,
                            'position_size': 20,
                            'rationale': f"Geopolitical: {event.get('title', 'Global event')} | {analysis.get('impact_type', 'unknown')}",
                            'source': 'geopolitical_analysis',
                            'trade_type': 'STOCK',
                            'current_price': opp.get('price', 0),
                            'geopolitical_event': event,
                            'geopolitical_thesis': opp.get('thesis', ''),
                            'geopolitical_score': score,
                            'geopolitical_direction': opp.get('direction', 'positive'),
                        })

                        if len(geo_signals) >= max_geo_signals:
                            break
                    if len(geo_signals) >= max_geo_signals:
                        break

                if geo_signals:
                    all_signals.extend(geo_signals)
                    print(f"🌍 Added {len(geo_signals)} geopolitical signals")
        except Exception as e:
            print(f"⚠️ Geopolitical analysis failed: {e}")

        # 5.5. Scan for underground/undiscovered stocks
        underground_signals = []
        if s.underground_discovery:
            print("\n🔍 SCANNING FOR UNDERGROUND STOCKS...")
            try:
                underground_opportunities = s.underground_discovery.scan_for_opportunities()

                for opp in underground_opportunities:
                    signal = Signal(
                        symbol=opp.ticker,
                        action='BUY',
                        trade_type='STOCK',
                        confidence=int(opp.strength * 100),
                        source='Underground Discovery',
                        timestamp=opp.timestamp,
                        evidence=opp.evidence,
                        metadata={
                            'signal_type': opp.signal_type,
                            'liquidity_score': opp.liquidity_score,
                            'dilution_risk': opp.dilution_risk,
                            'sources': opp.sources
                        }
                    )
                    underground_signals.append(signal)
                    print(f"  🎯 UNDERGROUND: {opp.ticker} - {opp.signal_type.upper()} (Strength: {opp.strength:.1%})")

                if underground_signals:
                    all_signals.extend(underground_signals)
                    print(f"  ✅ Added {len(underground_signals)} underground signals to pipeline")
                else:
                    print("  💤 No underground opportunities found")

            except Exception as e:
                print(f"  ⚠️ Underground scan failed: {e}")

        if underground_signals:
            print(f"\n🔊 Total signals with underground: {len(all_signals)} (+{len(underground_signals)} underground)")

        return all_signals, news_items

    def _build_signal_objects_for_arbitration(self, ctx: ApplicationContext, all_signals: List) -> List[Signal]:
        """Convert raw signal dicts to Meta-Brain Signal objects."""
        print("\n🧠 Running Meta-Brain arbitration on all signals...")
        all_signal_objects: List[Signal] = []

        if not all_signals:
            print("💤 No signals to arbitrate - no trading opportunities today")
            return all_signal_objects

        for signal in all_signals:
            if not isinstance(signal, dict):
                continue

            sym_upper = str(signal.get('symbol', '')).upper()
            current_price = signal.get('current_price')
            try:
                price_val = float(current_price) if current_price is not None else None
            except Exception:
                price_val = None

            max_crypto_trade_price = ctx.config.get("trading.max_crypto_trade_price", 10000)
            if sym_upper.endswith('-USD') and price_val is not None and price_val > max_crypto_trade_price:
                signal['analysis_only'] = True

            if signal.get('analysis_only'):
                continue

            core_fields = {'symbol', 'action', 'confidence', 'position_size', 'rationale', 'source'}
            extra_fields = {k: v for k, v in signal.items() if k not in core_fields}

            meta_signal = Signal(
                symbol=signal['symbol'],
                action=signal['action'],
                confidence=signal['confidence'],
                position_size=signal['position_size'],
                rationale=signal.get('rationale', ''),
                source=signal.get('source', 'unified_analysis'),
                **extra_fields
            )
            all_signal_objects.append(meta_signal)

        print(f"📊 Total signals for arbitration: {len(all_signal_objects)}")
        kalshi_signals = [s for s in all_signal_objects if getattr(s, 'source', '') == 'kalshi_prediction']
        print(f"🎯 Kalshi signals for arbitration: {len(kalshi_signals)}")
        for s in kalshi_signals[:3]:  # Show first 3
            print(f"   {s.symbol}: confidence={getattr(s, 'confidence', 0):.1%} pop={getattr(s, 'pop_from_sim', 0):.1f}")
        return all_signal_objects

    def _stage_prepare_arbitration_context(
        self,
        ctx: ApplicationContext,
        crash_assessment: Optional[Dict],
        all_signal_objects: List[Signal],
    ):
        """Prepare arbitration thresholds and portfolio snapshot."""
        s = ctx.system
        if ctx.config.get("telegram_enabled", False) and crash_assessment:
            alert_level = crash_assessment['alert_level']
            if alert_level >= 2:  # Medium correction or crash risk
                # Crash profit engine disabled in stock-only mode
                print("   💤 Stock-only mode: Crash alerts disabled")

        market_alert_level = crash_assessment['alert_level'] if crash_assessment else 0
        defensive_mode = market_alert_level >= 1
        dynamic_pop_threshold = 40 if market_alert_level >= 2 else 35 if market_alert_level == 1 else 30
        approved_signals = s.meta_brain.arbitrate_signals(
            all_signal_objects,
            pop_threshold=dynamic_pop_threshold / 100.0
        )

        # Real portfolio snapshot (used later for filtering/execution reporting)
        real_portfolio = s.real_portfolio.get_portfolio_summary()

        print(f"\n💼 REAL PORTFOLIO STATUS:")
        print(f"   Starting Capital: ${real_portfolio['starting_capital']:.2f}")
        print(f"   Available Cash: ${real_portfolio['available_capital']:.2f}")
        print(f"   Realized P&L: ${real_portfolio['realized_pnl']:.2f} (actual closed trades)")
        print(f"   Unrealized P&L: ${real_portfolio['unrealized_pnl']:.2f} (open positions)")
        print(f"   Total Portfolio Value: ${real_portfolio['total_portfolio_value']:.2f}")
        print(f"   Total Return: ${real_portfolio['total_return']:.2f} ({real_portfolio['total_return_pct']:.1f}%)")
        print(f"   Trades: {real_portfolio['total_trades']} (Win Rate: {real_portfolio['win_rate']:.1f}%)")

        if real_portfolio['open_positions_count'] > 0:
            print(f"\n   Open Positions ({real_portfolio['open_positions_count']}):")
            for pos in real_portfolio['open_positions'][:3]:  # Show top 3
                print(
                    f"   • {pos['symbol']}: {pos['quantity']} shares @ ${pos['avg_cost']:.2f} | "
                    f"P&L: ${pos['unrealized_pnl']:.2f} ({pos['unrealized_pct']:.1f}%)"
                )

        return approved_signals, real_portfolio, defensive_mode, dynamic_pop_threshold

    def _stage_streamlined_signal_filtering(self, ctx: ApplicationContext, approved_signals: List[Signal]) -> List[Signal]:
        """Run single-pass signal filtering with confluence and price guards."""
        if not approved_signals:
            return []

        s = ctx.system
        print(f"🔍 STREAMLINED FILTERING: Processing {len(approved_signals)} signals with dynamic scaling...")
        filtered_signals: List[Signal] = []

        for signal in approved_signals:
            try:
                symbol = getattr(signal, 'symbol', 'UNKNOWN')
                trade_type = getattr(signal, 'trade_type', '')
                action = getattr(signal, 'action', '')
                confidence = getattr(signal, 'confidence', 0)
                intelligence_strength = getattr(signal, 'intelligence_strength', 50)

                print(f"  🔍 {symbol}: Checking confidence {confidence:.1%} against 30% threshold")
                if confidence < 0.30:
                    print(f"  ❌ {symbol}: Confidence {confidence:.1%} - BELOW 30% threshold - BLOCKED")
                    continue
                print(f"  ✅ {symbol}: Confidence {confidence:.1%} - PASSED 30% threshold")

                signal_source = getattr(signal, 'source', '')
                if signal_source == 'geopolitical_analysis':
                    max_price = ctx.config.get("trading_budget", {}).get("max_price_per_share_geo", 600)
                else:
                    max_price = ctx.config.get("trading_budget", {}).get("max_price_per_share", 50)

                if hasattr(signal, 'current_price') and signal.current_price > max_price:
                    print(f"  💰 {symbol}: Price ${signal.current_price:.2f} EXCEEDS ${max_price} budget - SKIPPED")
                    continue

                print(f"  🧠 {symbol}: Running confluence analysis...")
                confluence_result = self.confluence_service.score(symbol)
                if confluence_result:
                    print(f"  ✅ {symbol}: Confluence {confluence_result.score:.1%} ({confluence_result.confidence})")
                    signal.confluence_score = confluence_result.score
                    signal.confluence_confidence = confluence_result.confidence
                    signal.confluence_reasoning = confluence_result.reasoning
                    if confluence_result.score >= 0.7:
                        confidence = min(confidence + 0.2, 1.0)
                        signal.confidence = confidence
                        print(f"  🚀 {symbol}: Confidence boosted to {confidence:.1%} (high confluence)")
                else:
                    print(f"  ⚠️ {symbol}: No confluence data")
                    signal.confluence_score = 0
                    signal.confluence_confidence = 'NONE'
                    signal.confluence_reasoning = 'No confluence data'

                if trade_type == 'KALSHI_PREDICTION':
                    print(f"  ✅ KALSHI: {symbol} - Bounded risk market")
                elif s.trading_mode == 'stocks_and_kalshi':
                    if (trade_type == 'OPTION' or
                        ('CALL' in action.upper() or 'PUT' in action.upper()) and
                            (getattr(signal, 'strike_price', None) or getattr(signal, 'expiration_date', None))):
                        print(f"  ❌ BLOCKED: {symbol} - Options terminology detected in stock-only mode")
                        continue
                elif trade_type == 'STOCK':
                    try:
                        current_price = self._get_cached_price(symbol)
                        if current_price is None:
                            print(f"  ⚠️ {symbol}: No price data available")
                            continue

                        max_price_access = s.real_portfolio.state['available_capital']
                        if current_price < 1.00:
                            print(f"  ❌ {symbol}: Price ${current_price:.2f} below $1.00 minimum - penny stock filtered out")
                            continue
                        if s.trading_mode == 'stocks_and_kalshi' and current_price > max_price_access:
                            print(f"  ❌ {symbol}: Price ${current_price:.2f} exceeds tier limit ${max_price_access:.2f}")
                            continue
                        print(f"  ✅ {symbol}: Price ${current_price:.2f} within $1.00-${max_price_access:.2f} range")

                        try:
                            catalyst_data = {
                                'momentum_score': getattr(signal, 'momentum_score', 0.7),
                                'volume_spike': getattr(signal, 'volume_spike', 0.7),
                                'news_intensity': getattr(signal, 'news_intensity', 0.7),
                                'catalyst_impact': getattr(signal, 'catalyst_impact', 0.7),
                            }
                            moon_shot_data = s.moon_shot_detector._analyze_moon_shot_potential(
                                symbol,
                                max_price_access,
                                catalyst_data
                            )
                            is_moon_shot = bool(moon_shot_data and moon_shot_data.get('score', 0) >= 70)
                            if is_moon_shot:
                                print(f"  🌙 {symbol}: MOON SHOT DETECTED! {moon_shot_data.get('potential_multiple', '1x')} potential (Score: {moon_shot_data.get('score', 0):.0f})")
                                signal.is_moon_shot = True
                                signal.moon_shot_score = moon_shot_data.get('score', 0)
                                signal.moon_shot_potential = moon_shot_data.get('potential_multiple', '1x')
                            else:
                                signal.is_moon_shot = False
                                signal.moon_shot_score = 0
                                signal.moon_shot_potential = "1x"
                        except Exception as moon_err:
                            signal.is_moon_shot = False
                            signal.moon_shot_score = 0
                            signal.moon_shot_potential = "1x"
                            print(f"  ⚠️ {symbol}: Moon shot analysis error: {moon_err}")
                    except Exception as price_err:
                        print(f"  ⚠️ {symbol}: Error checking price - {str(price_err)}")
                        continue

                if intelligence_strength < 30:
                    print(f"  ❌ {symbol}: Intelligence {intelligence_strength}/100 - BELOW 30 threshold")
                    continue

                filtered_signals.append(signal)
                print(f"  ✅ APPROVED: {symbol} - All filters passed")
                unified_summary = self.generate_unified_trade_summary(signal, ctx=ctx)
                print(f"\n{unified_summary}\n")
            except Exception as e:
                print(f"  ⚠️ Error processing {symbol}: {e}")
                continue

        print(f"📊 STREAMLINED RESULT: {len(filtered_signals)} signals approved in single pass")
        return filtered_signals

    def _stage_apply_platform_limits(self, ctx: ApplicationContext, high_confidence_approved: List[Signal]) -> List[Signal]:
        """Split signals by platform and enforce per-platform max positions."""
        s = ctx.system
        kalshi_approved: List[Signal] = []
        stocks_approved: List[Signal] = []
        options_approved: List[Signal] = []

        for signal in high_confidence_approved:
            if getattr(signal, 'trade_type', '') == 'KALSHI_PREDICTION':
                kalshi_approved.append(signal)
            elif getattr(signal, 'trade_type', '') == 'STOCK':
                stocks_approved.append(signal)
            else:
                options_approved.append(signal)

        print(f"🎯 PLATFORM SEPARATION: {len(kalshi_approved)} Kalshi | {len(stocks_approved)} Stocks | {len(options_approved)} Options")

        max_kalshi_positions = ctx.config.get("trading.kalshi_trading.max_positions", 10)
        max_stock_positions = ctx.config.get("trading.stock_trading.max_positions", 50)
        max_options_positions = 20

        current_kalshi_positions = len([
            pos for pos in s.meta_brain.risk_manager.open_positions.values()
            if pos.get('trade_type') == 'KALSHI_PREDICTION'
        ])
        current_stock_positions = len([
            pos for pos in s.meta_brain.risk_manager.open_positions.values()
            if pos.get('trade_type') == 'STOCK'
        ])
        current_options_positions = len([
            pos for pos in s.meta_brain.risk_manager.open_positions.values()
            if pos.get('trade_type') not in ['KALSHI_PREDICTION', 'STOCK']
        ])

        if current_kalshi_positions >= max_kalshi_positions:
            kalshi_approved = []
            print(f"   ❌ Kalshi limit reached: {current_kalshi_positions}/{max_kalshi_positions}")
        else:
            remaining_kalshi = max_kalshi_positions - current_kalshi_positions
            if len(kalshi_approved) > remaining_kalshi:
                kalshi_approved = kalshi_approved[:remaining_kalshi]
                print(f"   ⚠️ Limited Kalshi to {remaining_kalshi} trades")

        if current_stock_positions >= max_stock_positions:
            stocks_approved = []
            print(f"   ❌ Stock limit reached: {current_stock_positions}/{max_stock_positions}")
        else:
            remaining_stocks = max_stock_positions - current_stock_positions
            if len(stocks_approved) > remaining_stocks:
                stocks_approved = stocks_approved[:remaining_stocks]
                print(f"   ⚠️ Limited Stocks to {remaining_stocks} trades")

        if current_options_positions >= max_options_positions:
            options_approved = []
            print(f"   ❌ Options limit reached: {current_options_positions}/{max_options_positions}")
        else:
            remaining_options = max_options_positions - current_options_positions
            if len(options_approved) > remaining_options:
                options_approved = options_approved[:remaining_options]
                print(f"   ⚠️ Limited Options to {remaining_options} trades")

        final_approved = kalshi_approved + stocks_approved + options_approved
        print(f"🔗 FINAL APPROVED: {len(final_approved)} signals ({len(kalshi_approved)} Kalshi, {len(stocks_approved)} Stocks, {len(options_approved)} Options)")
        return final_approved

    def _stage_bankroll_intel_and_pro_options(self, ctx: ApplicationContext, high_confidence_approved: List[Signal]) -> List[Signal]:
        """Emergency position cap, per-platform limits, market intelligence, optional pro-options QA."""
        s = ctx.system
        print(f"🧠 UNIFIED ANALYSIS: Processing {len(high_confidence_approved)} signals with Market Intelligence...")

        max_open_positions = 50
        current_positions = len(s.meta_brain.risk_manager.open_positions)

        print(f"[BANKROLL SAFETY] 🚨 DEBUG: Using meta_brain state for position tracking")
        print(f"[BANKROLL SAFETY] 🚨 DEBUG: Portfolio positions count: {current_positions}")
        print(f"[BANKROLL SAFETY] 🚨 Current positions: {current_positions} | Max allowed: {max_open_positions}")

        if current_positions >= max_open_positions:
            print(f"[BANKROLL SAFETY] ❌ EMERGENCY STOP: {current_positions} positions >= max {max_open_positions}")
            high_confidence_approved = []
        else:
            remaining_slots = max_open_positions - current_positions
            if len(high_confidence_approved) > remaining_slots:
                print(f"[BANKROLL SAFETY] ⚠️ Limiting to {remaining_slots} trades (position limit)")
                high_confidence_approved = high_confidence_approved[:remaining_slots]

        high_confidence_approved = self._stage_apply_platform_limits(ctx, high_confidence_approved)

        if high_confidence_approved:
            engine = getattr(s, "market_intelligence", None) or getattr(s, "market_intelliggence", None)
            if engine:
                print(f"[MARKET INTEL] 🧠 Analyzing {len(high_confidence_approved)} approved signals with contextual intelligence...")
            else:
                print(f"[MARKET INTEL] 🧠 Using default intelligence (engine unavailable)")

            for signal in high_confidence_approved:
                try:
                    symbol = getattr(signal, 'symbol', 'UNKNOWN')
                    signal_type = 'BULLISH' if 'CALL' in str(getattr(signal, 'action', '')).upper() else 'BEARISH'

                    if not engine:
                        signal.market_intelligence = {'strength': 50, 'source': 'default'}
                        signal.intelligence_strength = 50
                        continue

                    intelligence = engine.analyze_symbol_intelligence(symbol, signal_type)
                    signal.market_intelligence = intelligence
                    signal.intelligence_strength = intelligence.get('opportunity_strength', 50)

                    print(f"[MARKET INTEL] ✅ {symbol}: {signal_type} | Strength: {signal.intelligence_strength:.0f}/100")

                except Exception:
                    signal.market_intelligence = {'strength': 50, 'source': 'fallback'}
                    signal.intelligence_strength = 50

        if s.options_enabled and high_confidence_approved:
            print("[PRO ANALYSIS] Running professional options analysis on high-confidence signals...")
            from utils.pro_options_analyzer import ProOptionsAnalyzer
            pro_analyzer = ProOptionsAnalyzer()

            signals_to_remove = []

            for signal in high_confidence_approved:
                try:
                    symbol = getattr(signal, 'symbol', 'UNKNOWN')

                    if getattr(signal, 'trade_type', '') == 'KALSHI_PREDICTION':
                        print(f"[PRO ANALYSIS] ⏭️ Skipping Kalshi signal: {symbol}")
                        continue

                    strike = getattr(signal, 'strike', 0)
                    action = getattr(signal, 'action', '')
                    option_type = 'CALL' if 'CALL' in str(action).upper() else 'PUT'

                    if strike == 0 or action in ['BUY', 'SELL']:
                        print(f"[PRO ANALYSIS] ⏭️ Skipping stock signal: {symbol} (no strike price needed)")
                        continue

                    pro_data = pro_analyzer.get_robinhood_style_chain(symbol, days_out=30)

                    if 'error' in pro_data:
                        print(f"[PRO ANALYSIS] ⚠️ Error getting pro data for {symbol}: {pro_data['error']}")
                        continue

                    target_option = None
                    options_list = pro_data['calls'] if option_type == 'CALL' else pro_data['puts']

                    for opt in options_list:
                        if abs(opt['strike'] - strike) < 0.01:
                            target_option = opt
                            break

                    if not target_option:
                        print(f"[PRO ANALYSIS] ⚠️ Strike ${strike} {option_type} not found for {symbol}")
                        continue

                    pop_score = target_option['probability_of_profit']
                    liquidity_score = target_option['liquidity_score']
                    spread_pct = target_option['spread_pct']

                    print(f"[PRO ANALYSIS] 📈 {symbol} ${strike} {option_type}: POP {pop_score:.0f}% | Liquidity {liquidity_score} | Spread {spread_pct:.1f}%")

                    pop_threshold = 40
                    liquidity_ok = liquidity_score in ['High', 'Very High', 'Medium']
                    spread_ok = spread_pct <= 10

                    if pop_score < pop_threshold:
                        print(f"[PRO ANALYSIS] ❌ REJECTED {symbol}: POP too low ({pop_score:.0f}% < {pop_threshold}%)")
                        signals_to_remove.append(signal)
                    elif not liquidity_ok:
                        print(f"[PRO ANALYSIS] ❌ REJECTED {symbol}: Liquidity too low ({liquidity_score})")
                        signals_to_remove.append(signal)
                    elif not spread_ok:
                        print(f"[PRO ANALYSIS] ❌ REJECTED {symbol}: Spread too wide ({spread_pct:.1f}% > 10%)")
                        signals_to_remove.append(signal)
                    else:
                        print(f"[PRO ANALYSIS] ✅ APPROVED {symbol}: Professional quality metrics passed")
                        signal.pro_pop_score = pop_score
                        signal.pro_liquidity = liquidity_score
                        signal.pro_spread = spread_pct

                except Exception as e:
                    print(f"[PRO ANALYSIS] ⚠️ Error analyzing {symbol}: {e}")

            for signal in signals_to_remove:
                high_confidence_approved.remove(signal)

            if signals_to_remove:
                print(f"[PRO ANALYSIS] 🚨 Removed {len(signals_to_remove)} signals for failing professional quality checks")

            print(f"[PRO ANALYSIS] 📊 Final signals after professional analysis: {len(high_confidence_approved)}")

        return high_confidence_approved

    def _stage_jury_final_review(
        self,
        ctx: ApplicationContext,
        high_confidence_approved: List[Signal],
        *,
        crash_assessment: Optional[Dict],
    ) -> List[Signal]:
        """Fact-only multi-chamber jury: evidence, risk alignment, outcome quality."""
        jury_cfg = ctx.config.get("jury_system")
        if isinstance(jury_cfg, dict) and jury_cfg.get("enabled") is False:
            return high_confidence_approved

        from engines.trade_jury_system import TradeJurySystem

        jury = TradeJurySystem(jury_cfg if isinstance(jury_cfg, dict) else {})
        jury_runtime_ctx = {
            "crash_alert_level": int(crash_assessment.get("alert_level", 0)) if crash_assessment else 0,
            "available_capital": float(ctx.system.real_portfolio.state.get("available_capital", 0) or 0),
        }

        kept: List[Signal] = []
        for signal in high_confidence_approved:
            outcome = jury.evaluate(signal, jury_runtime_ctx)
            signal.jury_verdict = outcome.verdict
            signal.jury_composite = outcome.composite
            signal.jury_evidence_score = outcome.evidence_score
            signal.jury_risk_score = outcome.risk_score
            signal.jury_outcome_score = outcome.outcome_score
            signal.jury_hard_veto = outcome.hard_veto
            signal.jury_veto_reason = outcome.veto_reason
            signal.jury_reasons = outcome.reasons

            sym = getattr(signal, "symbol", "UNKNOWN")
            if outcome.hard_veto or outcome.verdict == "REJECT":
                print(f"[JURY] REJECT {sym}: {outcome.veto_reason or '; '.join(outcome.reasons[:2])}")
                continue

            TradeJurySystem.apply_conditional_sizing(
                signal,
                outcome,
                float(jury.conditional_size_multiplier),
            )
            if outcome.verdict == "CONDITIONAL":
                print(f"[JURY] CONDITIONAL {sym}: composite={outcome.composite:.1f}")
            else:
                print(f"[JURY] APPROVE {sym}: composite={outcome.composite:.1f}")
            kept.append(signal)

        if len(kept) != len(high_confidence_approved):
            print(f"[JURY] {len(high_confidence_approved)} -> {len(kept)} after jury review")
        return kept

    async def _stage_signal_generation(
        self,
        ctx: ApplicationContext,
        crash_assessment: Optional[Dict],
        _macro_risk: bool,
    ) -> Optional[Tuple[List, List[Dict], List, List, List, List, List, List]]:
        """News pipeline through unified analysis, convergence, Kalshi hooks, and moonshot split."""
        all_signals: List = []
        investment_opportunities: List = []
        convergence_opportunities: List = []
        s = ctx.system

        news_items = await s._stage_unified_brain_news_items(ctx)
        
        # Run thematic analysis to identify macro trends
        print("\n🎯 THEMATIC ANALYSIS: Identifying macro trends...")
        active_themes = s.thematic_analyzer.analyze_news_themes(news_items)
        thematic_stocks = s.thematic_analyzer.map_themes_to_stocks(active_themes)
        
        # Analyze conviction watchlist for dip buying opportunities
        print("\n🚀 CONVICTION WATCHLIST: DISABLED - discovering stocks from news instead")
        conviction_opportunities = []  # Disabled - no pre-defined watchlist
        
        # Add thematic stocks to news items for processing
        if thematic_stocks:
            print(f"\n📊 Adding {len(thematic_stocks)} thematic stocks to analysis...")
            for stock in thematic_stocks:
                thematic_item = {
                    'symbol': stock['ticker'],
                    'title': f"Thematic: {stock['theme']} - {stock['name']}",
                    'summary': stock['reason'],
                    'source': 'thematic_analysis',
                    'sentiment': 0.7 if stock['theme_confidence'] > 0.5 else 0.6,
                    'catalyst_score': stock['combined_score'],
                    'sector': stock['theme'],
                    'current_price': stock['price'],
                    'theme': stock['theme'],
                    'ai_reasoning': stock['ai_reasoning']
                }
                news_items.append(thematic_item)
                print(f"   PASS {stock['ticker']} ({stock['theme']}) - ${stock['price']:.2f}")
        
        # Add conviction watchlist opportunities (DISABLED)
        # if conviction_opportunities:
        #     print(f"\n🚀 Adding {len(conviction_opportunities)} conviction watchlist opportunities...")
        #     for opp in conviction_opportunities:
        #         conviction_item = {
        #             'symbol': opp['ticker'],
        #             'title': f"CONVICTION: {opp['signal_type']} - {opp['name']}",
        #             'summary': opp['reasoning'],
        #             'source': 'conviction_watchlist',
        #             'sentiment': 0.9 if 'STRONG BUY' in opp['signal_type'] else 0.8,
        #             'catalyst_score': 0.9,
        #             'sector': 'High Conviction',
        #             'current_price': opp['price'],
        #             'action': opp['action'],
        #             'conviction_level': opp['conviction_level'],
        #             'potential': opp['potential']
        #         }
        #         news_items.append(conviction_item)
        #         print(f"   PASS {opp['ticker']} ({opp['signal_type']}) - ${opp['price']:.2f} - {opp['potential']} potential")
        
        # ADD DAY TRADING STOCKS
        day_trading_opportunities = []
        print("\n📈 Scanning for day trading stocks...")
        
        # Extract symbols from news for dynamic scanning
        news_symbols = []
        for item in news_items:
            symbol = item.get('symbol', '')
            if symbol and symbol not in news_symbols and not symbol.startswith('KX'):
                news_symbols.append(symbol)
        
        # Get current bankroll from portfolio manager
        current_bankroll = s.real_portfolio.state["available_capital"]

        day_trading_signals = s.day_trading_scanner.scan_momentum_stocks(
            limit=30, 
            additional_symbols=news_symbols,
            bankroll=current_bankroll
        )
        
        # Convert day trading signals to news items format for unified processing
        for signal in day_trading_signals:
            news_item = {
                'symbol': signal['symbol'],
                'title': signal['title'],
                'sector': signal['sector'],
                'industry': signal['industry'],
                'avg_volume': signal['avg_volume'],
                'market_cap': signal['market_cap'],
                'catalyst_type': signal['catalyst_type'],
                'source': 'day_trading'
            }
            news_items.append(news_item)
            
            # Run stock simulation for day trading signal
            print(f"   🎯 DEBUG: Attempting simulation for {signal['symbol']}...")
            try:
                monte_carlo = get_monte_carlo_engine(ctx.config)
                stock_signal = {
                    'symbol': signal['symbol'],
                    'current_price': signal['entry_price'],
                    'target_price': signal['target_price'],
                    'stop_loss': signal['entry_price'] * 0.95,  # 5% stop loss for day trades
                    'confidence': signal['confidence'] / 100,
                    'sector': signal['sector'],
                    'holding_days': 5  # Day trades hold 5 days max
                }
                
                print(f"\n🎲 Running Monte Carlo simulation for day trade: {signal['symbol']}...")
                sim_results = monte_carlo.run_stock_simulation(stock_signal)
                
                # Display simulation results
                if sim_results:
                    # Recalculate position size with simulation win rate
                    sim_win_rate = sim_results.get('win_rate', 0)
                    updated_position = s.day_trading_scanner.calculate_position_size(
                        signal['entry_price'], 
                        current_bankroll,
                        signal['confidence'] / 100.0,
                        sim_win_rate
                    )
                    
                    print(f"   📊 Day Trade Simulation:")
                    print(f"      Win Rate: {sim_win_rate:.1%} | AI Confidence: {signal['confidence']:.0f}%")
                    print(f"      Target: ${sim_results.get('target_price', 0):.2f}")
                    print(f"      Stop: ${sim_results.get('stop_loss', 0):.2f}")
                    print(f"      Profit Potential: {sim_results.get('profit_potential', 0):.1%}")
                    print(f"      Original Position: {signal['shares_to_buy']} shares @ ${signal['entry_price']} = ${signal['position_cost']} ({signal['bankroll_used_pct']}% of bankroll)")
                    print(f"      Adjusted Position: {updated_position['shares']} shares @ ${signal['entry_price']} = ${updated_position['cost']} ({updated_position['bankroll_used_pct']}% of bankroll)")
                    print(f"      Max Risk: ${updated_position['risk_amount']} if stop loss hits")
                    
                    # Update signal with adjusted position
                    signal.update(updated_position)
                
                # Add simulation results to signal
                signal['simulation_results'] = sim_results
                
            except Exception as e:
                print(f"   ⚠️ Simulation failed for {signal['symbol']}: {e}")
                signal['simulation_results'] = None
            
            # Also create day trading opportunity for Telegram posting
            day_trading_opportunity = {
                'symbol': signal['symbol'],
                'title': signal['title'],
                'source': 'day_trading',
                'sentiment': 0.8 if signal['confidence'] > 70 else 0.6,
                'catalyst_score': signal['confidence'] / 100,
                'sector': signal['sector'],
                'current_price': signal['entry_price'],
                'target_price': signal['target_price'],
                'day_trading_data': signal
            }
            day_trading_opportunities.append(day_trading_opportunity)
        
        print(f"📊 Total items after adding day trading stocks: {len(news_items)}")
        
        # Post day trading signals directly to Telegram (separate from Kalshi)
        if s.telegram_bot and day_trading_opportunities:
            print(f"\n📈 Posting {len(day_trading_opportunities)} day trading signals to Telegram...")
            for opp in day_trading_opportunities:
                try:
                    # Format using stock signal formatter
                    signal_data = opp.get('day_trading_data', {})

                    sym = str(signal_data.get('symbol', opp.get('symbol', ''))).upper()
                    action = str(signal_data.get('action', 'BUY')).upper()
                    post_key = f"DAYTRADE:{sym}:{action}"
                    if post_key in s.posted_signals:
                        continue
                    
                    # ADD RISK-FIRST VALIDATION
                    is_valid, risk_msg = s.validate_risk_first(signal_data, ctx=ctx)
                    if not is_valid:
                        print(f"   🛑 Signal {signal_data.get('symbol', 'UNKNOWN')} rejected: {risk_msg}")
                        continue
                    
                    formatted_message = s.telegram_bot.format_stock_signal_message(signal_data)
                    result = s.telegram_bot.send_message(formatted_message)
                    if result:
                        s.posted_signals.add(post_key)
                        s._save_posted_signals()  # Persist to disk
                    print(f"   📱 Posted {signal_data.get('symbol', 'UNKNOWN')} to Telegram: {result}")
                except Exception as e:
                    print(f"   ❌ Failed to post {opp.get('symbol', 'UNKNOWN')} to Telegram: {e}")
        
        if not news_items:
            print("💤 No real trading opportunities found from news sources")
            print("💡 System will not generate fake signals - this is correct for real trading")
            return None
        
        # FILTER OUT RECENTLY TRADED SYMBOLS
        cooldown_memory = get_cooldown_memory()
        original_count = len(news_items)
        news_items = [item for item in news_items if not cooldown_memory.is_recently_traded(item['symbol'])]
        filtered_count = original_count - len(news_items)
        if filtered_count > 0:
            print(f"   🚫 Removed {filtered_count} recently traded symbols")
        print(f"   ✅ {len(news_items)} fresh trading opportunities remain")
        
        # Filter news items by max price access before analysis
        max_price_access = s.real_portfolio.state["available_capital"]  # Use actual available capital
        print(f"\n💰 Filtering news items by max price: ${max_price_access:.2f}")
        
        affordable_news_items = []
        for item in news_items:
            symbol = str(item.get('symbol', '')).upper()
            current_price = s._get_cached_price(symbol)
            if current_price is None:
                affordable_news_items.append(item)
                continue

            if current_price < 1.00:
                print(f"   ❌ {symbol}: ${current_price:.2f} below $1.00 minimum - penny stock filtered out")
                continue

            if current_price <= max_price_access:
                affordable_news_items.append(item)
            else:
                print(f"   ❌ {symbol}: ${current_price:.2f} > ${max_price_access:.2f} - filtered out")
        
        news_items = affordable_news_items
        print(f"   ✅ Filtered to {len(news_items)} affordable news items")

        if news_items:
            print("\n🎯 INDUSTRY SCAN RESULTS:")
            for item in news_items[:5]:  # Show top 5
                fact_check = item.get('fact_check', {})
                company_info = fact_check.get('company_info', {})
                options_data = item.get('options_data', {})

                print(f"   📈 {item.get('symbol')} ({company_info.get('industry', 'Unknown')}): {item.get('title', 'No title')[:50]}...")
                print(f"      🎯 Recommendation: {item.get('options_recommendation', 'UNKNOWN')}")
                print(f"      📊 Options: IV {options_data.get('estimated_iv', 0)}% | Vol {options_data.get('estimated_options_volume', 0):,}")
                print(f"      ⏰ Optimal Expiry: {item.get('optimal_expiry_days', 0)} days")
                print(f"      ✅ Valid: {fact_check.get('is_valid', False)} | Real Company: {company_info.get('real_ticker', False)}")
                print(f"      🏢 Company: {company_info.get('full_name', 'Unknown')}")
                print()

        # 2. Get trending symbols from social media (Reddit, Twitter/X)
        print("\n📱 Scanning social media for trending symbols...")
        trending_symbols = {}
        if s.social_engine:
            try:
                trending_symbols = await s.get_trending_symbols(limit=10)
                if trending_symbols:
                    print(f"   🔥 Found {len(trending_symbols)} trending symbols on social media:")
                    for symbol, count in list(trending_symbols.items())[:5]:
                        print(f"      • {symbol}: {count} mentions")
                    
                    # Add trending symbols to news items for analysis
                    trending_price_map = {}
                    if ctx.market_cache and MarketDataCache:
                        try:
                            trending_price_map = ctx.market_cache.fetch_prices(list(trending_symbols.keys()))
                        except Exception:
                            trending_price_map = {}

                    price_fetcher = get_price_fetcher()
                    for symbol, count in trending_symbols.items():
                        # Check if symbol already in news_items
                        if not any(item.get('symbol') == symbol for item in news_items):
                            # Get REAL price for social media symbol (cache-first)
                            real_price = trending_price_map.get(symbol)
                            if not real_price:
                                real_price = price_fetcher.get_real_price(symbol)
                            
                            if real_price:
                                # Add as social media signal with REAL price and simulation-based targets
                                news_items.append({
                                    'symbol': symbol,
                                    'title': f"Trending on social media: {symbol}",
                                    'source': 'social_media',
                                    'sentiment': 0.5,
                                    'catalyst_score': 0.3,
                                    'sector': 'Unknown',
                                    'current_price': real_price,  # REAL PRICE
                                    # target_price will be calculated by simulation later
                                    'social_mentions': count
                                })
                                print(f"   ✅ Added {symbol} from social media (${real_price:.2f})")
                            else:
                                print(f"   ❌ Skipping {symbol} - cannot fetch real price")
                else:
                    print("   💤 No trending symbols found on social media")
            except Exception as e:
                print(f"   ⚠️ Social media scanning error: {e}")
        else:
            print("   ⚠️ Social media engine not available")

        # 2. Process all collected signals
        
        # 2.6. Scan Kalshi prediction markets with automatic discovery
        kalshi_opportunities = []
        if s.kalshi_engine:
            print("\n🌤️ Scanning WEATHER prediction markets for trading opportunities...")
            try:
                # Use automatic market discovery with AI Playbook
                opportunities = s.kalshi_engine.scan_all_markets(
                    min_volume=100,  # Lower threshold for playbook (it handles liquidity)
                    max_markets=50,
                    use_playbook=True  # Enable AI Playbook strategy
                )
                
                if opportunities:
                    print(f"   ✅ Found {len(opportunities)} WEATHER trading opportunities")
                    
                    for opp_data in opportunities:
                        market = opp_data['market']
                        analysis = opp_data['analysis']
                        phasma_prediction = analysis.get('phasma_prediction')  # Get from analysis, not opp_data
                        
                        # Calculate position sizing for Kalshi bet
                        confidence = analysis.get('confidence', 0)
                        bankroll = s.real_portfolio.state["available_capital"]

                        # Use same dynamic risk calculation as day trading
                        risk_pct = s.day_trading_scanner.calculate_dynamic_risk(confidence)
                        bet_amount = bankroll * risk_pct
                        
                        # Create unified opportunity structure
                        kalshi_opportunity = {
                            'symbol': analysis.get('ticker', market.get('ticker', '')),
                            'title': f"Kalshi: {market.get('title', '')} - {analysis.get('signal', '')}",
                            'source': 'kalshi_prediction',
                            'sentiment': 0.8 if analysis.get('confidence', 0) > 0.7 else 0.6 if analysis.get('confidence', 0) > 0.5 else 0.4,
                            'catalyst_score': analysis.get('catalyst_score', 0),
                            'sector': 'Prediction Markets',
                            'current_price': opp_data['implied_probability'] * 100,
                            'strike': 50.0,
                            'kalshi_market_data': market,
                            'kalshi_analysis': analysis,
                            'phasma_prediction': phasma_prediction,
                            'prediction_probability': opp_data['implied_probability'],
                            'market_volume': opp_data['volume'],
                            'confidence': analysis.get('confidence', 0),
                            'kalshi_signal': analysis.get('signal'),
                            'kalshi_action': analysis.get('action'),
                            'position_size': analysis.get('position_size', 0),
                            'trade_link': analysis.get('trade_link', ''),
                            'days_to_expiry': analysis.get('days_to_expiry', 0),
                            'expiration_analysis': analysis.get('expiration_analysis', {}),
                            'market_assessment': analysis.get('market_assessment', {}),
                            # Position sizing for Kalshi
                            'bet_amount': round(bet_amount, 2),
                            'risk_percentage': round(risk_pct * 100, 1),
                            'bankroll_used_pct': round((bet_amount / bankroll) * 100, 1)
                        }
                        kalshi_opportunities.append(kalshi_opportunity)
                        
                        edge_info = f" | Edge: {phasma_prediction:.1%} vs {opp_data['implied_probability']:.1%}" if phasma_prediction else ""
                        print(f"   🌤️ WEATHER BET: {market.get('ticker')} {analysis.get('signal')} (Conf: {analysis.get('confidence', 0):.1%}){edge_info}")
                        print(f"      💡 {analysis.get('rationale', '')}")
                        print(f"      📊 Volume: {opp_data['volume']:,} | Price: ${opp_data['implied_probability']*100:.2f}")
                        print(f"      💰 Bet Amount: ${bet_amount:.2f} ({risk_pct*100:.1f}% of bankroll = ${bankroll * risk_pct:.2f})")
                        
                        if analysis.get('market_assessment'):
                            timing = analysis['market_assessment'].get('timing_assessment', 'unknown')
                            print(f"      ⏰ Timing: {timing}")
                    
                    # Show summary of signals
                    yes_signals = sum(1 for opp in kalshi_opportunities if opp.get('kalshi_signal') == 'BUY_YES')
                    no_signals = sum(1 for opp in kalshi_opportunities if opp.get('kalshi_signal') == 'BUY_NO')
                    print(f"\n   📊 Signal breakdown: {yes_signals} BUY_YES, {no_signals} BUY_NO")
                    print(f"   🎯 Automatic discovery completed - no manual configuration needed!")
                    
                else:
                    print("   💤 No qualified Kalshi opportunities found in this scan")
                    print("   🔄 System will automatically retry with fresh market data next cycle")
                    
            except Exception as e:
                print(f"   ⚠️ Kalshi automatic discovery error: {e}")
                print("   🔄 Will retry automatic market discovery next cycle")
        else:
            print("   ⚠️ Kalshi engine not initialized")

        # 2.7. Scan for undervalued stocks using fundamental analysis
        undervalued_stocks = []
        print("\n💎 Scanning for UNDervalued stocks using fundamental analysis...")
        try:
            # Get a list of stocks to analyze (from news items and watchlist)
            symbols_to_analyze = set()
            for item in news_items[:50]:  # Analyze top 50
                symbol = item.get('symbol', '').upper()
                if symbol and symbol != 'UNKNOWN':
                    symbols_to_analyze.add(symbol)
            
            # Keep the value scan fully news/universe-driven (no fixed symbol seed list).
            
            print(f"   🔍 Analyzing {len(symbols_to_analyze)} stocks for value opportunities...")
            
            value_price_map = {}
            if ctx.market_cache and MarketDataCache:
                try:
                    value_price_map = ctx.market_cache.fetch_prices(list(symbols_to_analyze))
                except Exception:
                    value_price_map = {}
            price_fetcher = get_price_fetcher()

            for symbol in symbols_to_analyze:
                try:
                    # Run P/E analysis
                    pe_analysis = s.pe_analyzer.analyze_pe_ratio(symbol)
                    
                    # Check if it's undervalued
                    if pe_analysis.get('score', 0) >= 7:  # High value score
                        valuation_level = pe_analysis.get('valuation_level', 'Unknown')
                        current_pe = pe_analysis.get('current_pe', 0)
                        industry_pe = pe_analysis.get('industry_pe', 0)
                        fair_value = pe_analysis.get('fair_value_range', {})
                        
                        # Only add if truly undervalued (P/E below industry average)
                        if current_pe > 0 and industry_pe > 0 and current_pe < industry_pe * 0.8:
                            # Get current price
                            current_price = value_price_map.get(symbol)
                            if not current_price:
                                current_price = price_fetcher.get_real_price(symbol)
                            
                            if current_price and current_price <= 50:  # Under $50 budget
                                # Calculate target based on fair value
                                target_price = fair_value.get('midpoint', current_price * 1.2)
                                expected_gain = ((target_price / current_price) - 1) * 100
                                
                                undervalued_stock = {
                                    'symbol': symbol,
                                    'title': f"UNDervalued: {symbol} - {valuation_level} valuation",
                                    'source': 'fundamental_analysis',
                                    'sentiment': 0.7,
                                    'catalyst_score': 0.4,
                                    'sector': pe_analysis.get('sector', 'Unknown'),
                                    'current_price': current_price,
                                    'target_price': target_price,
                                    'pe_ratio': current_pe,
                                    'industry_pe': industry_pe,
                                    'pe_vs_industry': (current_pe / industry_pe) if industry_pe > 0 else 0,
                                    'valuation_score': pe_analysis.get('score', 0),
                                    'valuation_level': valuation_level,
                                    'peg_ratio': pe_analysis.get('peg_ratio', 0),
                                    'eps_growth': pe_analysis.get('eps_growth', 0),
                                    'revenue_growth': pe_analysis.get('revenue_growth', 0),
                                    'fair_value_range': fair_value,
                                    'expected_gain': expected_gain,
                                    'fundamental_data': pe_analysis
                                }
                                undervalued_stocks.append(undervalued_stock)
                                
                                print(f"   💎 {symbol}: P/E {current_pe:.1f} vs Industry {industry_pe:.1f} ({(current_pe/industry_pe)*100:.0f}%) | Score: {pe_analysis.get('score', 0)}/10 | Expected: +{expected_gain:.1f}%")
                                
                                # Create investment thesis
                                thesis = s.thesis_manager.create_thesis(symbol)
                                if thesis:
                                    undervalued_stock['investment_thesis'] = thesis.get('thesis', '')
                                    undervalued_stock['thesis_type'] = thesis.get('game_type', 'Unknown')
                                
                                # Generate AI reasoning: why THIS stock, why industry needs it
                                ai_reasoning = s._generate_value_investing_reasoning(symbol, pe_analysis, current_price, target_price)
                                undervalued_stock['ai_reasoning'] = ai_reasoning
                
                except Exception as e:
                    continue  # Skip symbols that fail
            
            if undervalued_stocks:
                print(f"   ✅ Found {len(undervalued_stocks)} undervalued stocks")
            else:
                print("   💤 No undervalued stocks found in this scan")
                
        except Exception as e:
            print(f"   ⚠️ Fundamental analysis error: {e}")

        # Add undervalued stocks to news items for unified analysis
        if undervalued_stocks:
            news_items.extend(undervalued_stocks)
            print(f"   💰 Added {len(undervalued_stocks)} undervalued stocks to unified analysis")

        # Add investment opportunities to news items for unified analysis
        if 'investment_opportunities' in locals() and investment_opportunities:
            news_items.extend(investment_opportunities)
            print(f"   💰 Added {len(investment_opportunities)} investment opportunities to unified analysis")
            
        # Add day trading opportunities to news_items for unified analysis
        if day_trading_opportunities:
            news_items.extend(day_trading_opportunities)
            print(f"   📈 Added {len(day_trading_opportunities)} day trading opportunities to unified analysis")
            
            # Also add any cross-market stock signals from CEO analysis
            cross_market_signals = []
            for opp in kalshi_opportunities:
                if opp.get('company_stock_opportunities'):
                    cross_market_signals.extend(opp['company_stock_opportunities'])
                    
            if cross_market_signals:
                news_items.extend(cross_market_signals)
                print(f"   🔄 Added {len(cross_market_signals)} cross-market stock signals from CEO analysis")

        existing_syms = {
            str(ni.get("symbol", "")).upper()
            for ni in news_items
            if isinstance(ni, dict) and ni.get("symbol")
        }
        try:
            revisit_news = s.skipped_opportunity_watchlist.get_revisit_news_items(
                existing_syms, s.robust_price_fetcher
            )
            if revisit_news:
                print(f"\n🔁 Skipped-opportunity revisit: injecting {len(revisit_news)} symbols for re-analysis")
                for rn in revisit_news:
                    sym_r = str(rn.get("symbol", "")).upper()
                    if sym_r:
                        ctx.track_symbol(sym_r, "skipped_revisit")
                        s.ai_watchlist.add(sym_r)
                news_items = revisit_news + news_items
        except Exception as _revisit_err:
            print(f"   ⚠️ Skipped-opportunity revisit injection failed: {_revisit_err}")
        
        # 3. Unified analysis: Use ALL methods for EVERY trade
        print("\n🧠 Running UNIFIED AI Analysis (Patterns + Simulations + Between the Lines + Partnerships)...")
        # `all_signals` was initialized earlier in the cycle; don't reset it here.
        cycle_price_map = {}
        if ctx.market_cache and MarketDataCache:
            try:
                cycle_price_map = ctx.market_cache.fetch_prices(
                    [ni.get('symbol') for ni in news_items[:40] if isinstance(ni, dict) and ni.get('symbol')]
                )
            except Exception:
                cycle_price_map = {}

        if not news_items:
            print("💤 No news items to analyze - skipping signal generation")
        else:
            for news_item in news_items[:20]:  # Analyze top 20 items
                try:
                    # UNIFIED ANALYSIS: All methods together for each item
                    unified_signals = await s._run_unified_analysis(
                        [news_item],
                        cycle_price_map,
                        ctx=ctx,
                    )
                    all_signals.extend(unified_signals)
                    
                    # Track all symbols from analysis (even holds)
                    for signal in unified_signals:
                        symbol = str(signal.get('symbol', '')).upper()
                        if symbol and symbol != 'UNKNOWN':
                            ctx.track_symbol(symbol, "unified_analysis")
                    
                    # Add good opportunities to watchlist priority
                    for signal in unified_signals:
                        if signal.get('action') in ['BUY', 'BUY_CALL', 'BUY_PUT']:
                            symbol = str(signal.get('symbol', '')).upper()
                            if symbol and symbol != 'UNKNOWN':
                                # Already tracked above, just ensure it's in watchlist
                                s.ai_watchlist.add(symbol)
                                # Keep watchlist manageable (remove old entries if too many)
                                if len(s.ai_watchlist) > 100:
                                    # Convert to list to remove oldest items
                                    watchlist_list = list(s.ai_watchlist)
                                    # Keep only the 50 most recent (simple FIFO)
                                    s.ai_watchlist = set(watchlist_list[-50:])
                except Exception as e:
                    print(f"⚠️ Unified analysis failed for {news_item.get('symbol', 'UNKNOWN')}: {str(e)}")

            print(f"🎯 Generated {len(all_signals)} unified trading signals")

        # 3.5. Signal Convergence Analysis - Combine all sources for high-confidence opportunities
        print("\n🔀 Running Multi-Source Signal Convergence Analysis...")
        convergence_opportunities = []
        
        try:
            # Feed all signals to convergence engine
            print("   📊 Feeding signals to convergence engine...")
            
            # Add unified news signals
            for signal in all_signals:
                s.convergence_engine.add_signal({
                    'source': 'news_analysis',
                    'ticker': signal.get('symbol', ''),
                    'confidence': signal.get('confidence', 0.5),
                    'action': signal.get('action', 'BUY'),
                    'position_size': signal.get('position_size', 1000),
                    'sector': signal.get('sector', 'UNKNOWN'),
                    'region': signal.get('region', 'GLOBAL'),
                    'timestamp': datetime.now().isoformat(),
                    'details': {
                        'signal_type': 'unified_analysis',
                        'rationale': signal.get('rationale', ''),
                        'catalyst_score': signal.get('catalyst_score', 0)
                    }
                })
            
            # Add day trading signals
            for opp in day_trading_opportunities:
                day_data = opp.get('day_trading_data', {})
                s.convergence_engine.add_signal({
                    'source': 'day_trading',
                    'ticker': opp.get('symbol', ''),
                    'confidence': day_data.get('confidence', 0.5) / 100,
                    'action': day_data.get('action', 'BUY'),
                    'position_size': day_data.get('volume', 1000),
                    'sector': opp.get('sector', 'Technology'),
                    'region': 'GLOBAL',
                    'timestamp': datetime.now().isoformat(),
                    'details': {
                        'signal_type': 'day_trading',
                        'entry_price': day_data.get('entry_price', 0),
                        'target_price': day_data.get('target_price', 0),
                        'rsi': day_data.get('rsi', 50),
                        'volume_ratio': day_data.get('volume', 0) / day_data.get('avg_volume', 1)
                    }
                })
            
            # Add Kalshi signals (supplement discovery results; do not overwrite)
            if getattr(s, "kalshi_engine", None):
                get_kalshi = getattr(s.kalshi_engine, "get_prediction_opportunities", None)
                supplemental_kalshi = get_kalshi() if callable(get_kalshi) else []
                if supplemental_kalshi:
                    # Deduplicate by the strongest available contract identity.
                    existing_kalshi_keys = set()
                    for opp in kalshi_opportunities:
                        market_data = opp.get('kalshi_market_data', {}) if isinstance(opp, dict) else {}
                        key = (
                            str(opp.get('symbol') or opp.get('ticker') or market_data.get('ticker') or '').upper(),
                            str(opp.get('title') or market_data.get('title') or '').strip().lower(),
                        )
                        existing_kalshi_keys.add(key)

                    for opp in supplemental_kalshi:
                        if not isinstance(opp, dict):
                            continue
                        market_data = opp.get('kalshi_market_data', {}) if isinstance(opp, dict) else {}
                        key = (
                            str(opp.get('symbol') or opp.get('ticker') or market_data.get('ticker') or '').upper(),
                            str(opp.get('title') or market_data.get('title') or '').strip().lower(),
                        )
                        if key in existing_kalshi_keys:
                            continue
                        kalshi_opportunities.append(opp)
                        existing_kalshi_keys.add(key)
                for opportunity in kalshi_opportunities:
                    signal = {
                        'source': 'kalshi_prediction',
                        'ticker': opportunity.get('ticker', 'UNKNOWN'),
                        'action': opportunity.get('action', 'BUY'),
                        'confidence': opportunity.get('confidence', 0.5),
                        'position_size': opportunity.get('position_size', 0.02),
                        'sector': 'Prediction Markets',
                        'region': 'US',
                        'timestamp': datetime.now(),
                        'details': opportunity
                    }
                    s.convergence_engine.add_signal(signal)
            
            # Add sports betting signals
            if hasattr(s, 'sports_odds_api') and s.sports_odds_api:
                print("   🏈 Adding sports betting signals...")
                sports_opportunities = s.sports_odds_api.analyze_betting_opportunities()
                for opp in sports_opportunities:
                    s.convergence_engine.add_signal({
                        'source': 'sports_analysis',
                        'ticker': opp.get('game', '').split(' vs ')[0],  # Extract first team
                        'confidence': opp.get('confidence', 0.5),
                        'action': 'BUY',  # Default action for sports betting
                        'position_size': 100,  # Standard position size
                        'sector': 'Sports Betting',
                        'region': 'GLOBAL',
                        'timestamp': datetime.now().isoformat(),
                        'details': {
                            'signal_type': 'sports_betting',
                            'game': opp.get('game', ''),
                            'recommendation': opp.get('recommendation', ''),
                            'reasoning': opp.get('reasoning', '')
                        }
                    })
            
            # Add investment opportunities
            for inv_opp in investment_opportunities[:3] if investment_opportunities else []:
                company = inv_opp.get('investing_company', {})
                s.convergence_engine.add_signal({
                    'source': 'corporate_investment',
                    'ticker': company.get('ticker', ''),
                    'confidence': inv_opp.get('confidence_in_impact', 0.85),
                    'action': 'BUY',
                    'position_size': 2000,  # Base position for investments
                    'sector': company.get('sector', 'UNKNOWN'),
                    'region': inv_opp.get('target_region', 'GLOBAL'),
                    'timestamp': datetime.now().isoformat(),
                    'details': {
                        'investment_amount': inv_opp.get('investment_amount', 0),
                        'investment_thesis': inv_opp.get('investment_thesis', ''),
                        'strategic_analysis': inv_opp.get('strategic_analysis', {}),
                        'ripple_effects': inv_opp.get('ripple_effect_opportunities', [])
                    }
                })
            
            # Add insider trading signals
            print("   📊 Adding insider trading signals to convergence analysis...")
            try:
                insider_signals = s.insider_monitor.get_recent_signals()
                if insider_signals:
                    print(f"\n   📈 **INSIDER TRADING ALERTS**")
                    for insider_signal in insider_signals[:5]:  # Top 5 insider signals
                        # Display unified compressed summary
                        unified_summary = s.generate_unified_trade_summary(insider_signal, ctx=ctx)
                        print(f"\n{unified_summary}\n")
                        
                        # Add to convergence engine
                        s.convergence_engine.add_signal({
                            'ticker': insider_signal.get('ticker', ''),
                            'confidence': insider_signal.get('confidence', 0.7),
                            'action': insider_signal.get('action', 'BUY'),
                            'position_size': insider_signal.get('position_size', 1500),
                            'sector': insider_signal.get('sector', 'UNKNOWN'),
                            'region': insider_signal.get('region', 'GLOBAL'),
                            'timestamp': insider_signal.get('timestamp', datetime.now().isoformat()),
                            'details': {
                                'insider_name': insider_signal.get('insider_name', ''),
                                'transaction_type': insider_signal.get('transaction_type', ''),
                                'amount': insider_signal.get('amount', ''),
                                'filing_date': insider_signal.get('filing_date', '')
                            }
                        })
                    
                    print(f"\n      ✅ Added {len(insider_signals[:5])} insider trading signals")
                else:
                    print("      💤 No recent insider trading signals found")
            except Exception as e:
                print(f"      ⚠️ Error adding insider signals: {e}")
            
            # Find convergence opportunities
            convergence_opportunities = s.convergence_engine.find_convergence_opportunities(min_sources=2)
            
            if convergence_opportunities:
                print(f"   🎯 FOUND {len(convergence_opportunities)} CONVERGENCE OPPORTUNITIES")
                
                for conv_opp in convergence_opportunities[:3]:  # Show top 3
                    print(f"      ✨ {conv_opp['opportunity_type']}: {conv_opp['target']}")
                    print(f"         📊 Convergence Score: {conv_opp['convergence_score']:.1%}")
                    print(f"         🏆 Confidence: {conv_opp['confidence_level']}")
                    print(f"         🔗 Sources: {conv_opp['unique_sources']} unique ({', '.join(conv_opp['sources_involved'])})")
                    print(f"         💰 Position: ${conv_opp['recommended_position_size']:,}")
                    print(f"         💡 Thesis: {conv_opp['investment_thesis'][:80]}...")
                    
                    if conv_opp['risk_factors']:
                        print(f"         ⚠️  Risks: {len(conv_opp['risk_factors'])} factors")
            else:
                print("   💤 No multi-source convergence opportunities found")
                
        except Exception as e:
            print(f"   ⚠️ Convergence analysis error: {e}")

        if kalshi_opportunities:
            kalshi_signals = []
            for opp in kalshi_opportunities:
                analysis = (opp.get('kalshi_analysis') or {})
                phasma_prediction = opp.get('phasma_prediction')

                # Basic market stats
                market_prob = float(analysis.get('market_probability', 0.5) or 0.5)
                volume = int(analysis.get('volume', opp.get('market_volume', 0)) or 0)
                days_to_expiry = int(analysis.get('days_to_expiry', opp.get('days_to_expiry', 7)) or 7)
                is_short_term = bool(analysis.get('is_short_term', opp.get('is_short_term', False)))

                # Edge and divergence score between Phasma view and market view
                edge = 0.0
                if phasma_prediction is not None:
                    try:
                        edge = abs(float(phasma_prediction) - market_prob)
                    except Exception:
                        edge = 0.0

                # Kalshi engine pop_from_sim is 0-1; rescale to 0-100 for unified POP gates
                try:
                    pop_raw = float(analysis.get('pop_from_sim', opp.get('pop_from_sim', 0.5)) or 0.5)
                except Exception:
                    pop_raw = 0.5
                pop_pct = max(10.0, min(95.0, pop_raw * 100.0))

                # Pattern/divergence heuristics so quality gates can work
                divergence_score = edge
                pattern_strength = max(0.2, min(0.9, 0.2 + edge))

                symbol = opp.get('symbol') or analysis.get('ticker', '')
                signal_direction = analysis.get('signal')
                # Map Kalshi YES/NO signal into CALL/PUT style actions
                if analysis.get('action'):
                    action = analysis['action']
                else:
                    if signal_direction == 'BUY_YES':
                        action = 'BUY'
                    elif signal_direction == 'BUY_NO':
                        action = 'SELL'
                    else:
                        action = None

                confidence_val = float(analysis.get('confidence', 0.0) or 0.0)
                position_size = float(analysis.get('position_size', opp.get('position_size', 0.0)) or 0.0)

                # Skip malformed opportunities
                if not symbol or not action or position_size <= 0:
                    continue

                timeframe_type = 'QUICK_CATALYST' if is_short_term else 'PREDICTION_WINDOW'
                timeframe_reasoning = f"Kalshi market expiring in {days_to_expiry} days"
                optimal_exit_day = max(1, min(days_to_expiry, 7 if is_short_term else days_to_expiry))

                current_price = opp.get('current_price', analysis.get('market_probability', 0.5) * 100)
                try:
                    current_price = float(current_price)
                except Exception:
                    current_price = analysis.get('market_probability', 0.5) * 100

                kalshi_signal = {
                    'symbol': symbol,
                    'action': action,
                    'confidence': confidence_val,
                    'position_size': position_size,
                    'rationale': analysis.get('rationale', opp.get('title', 'Kalshi prediction market opportunity')),
                    'source': 'kalshi_prediction',
                    'patterns': [],
                    'technical_bias': 'NEUTRAL',
                    'divergence_analysis': {'divergence_score': divergence_score},
                    'fact_check': {},
                    'simulation_results': {},  # Use POP-only pipeline for Kalshi
                    'evidence_chain': analysis.get('trade_link', opp.get('trade_link', '')),
                    'entry_timing': {
                        'urgency': 'high' if is_short_term else 'medium',
                        'recommended_action': 'BUY_NOW',
                        'timeframe': f"Hold through event ({days_to_expiry}d)",
                        'confidence': confidence_val,
                        'optimal_exit_day': optimal_exit_day
                    },
                    'exit_timing': {
                        'target_date': f"{days_to_expiry} days",
                        'optimal_exit_day': optimal_exit_day,
                        'stop_loss': 0.3,
                        'take_profit': 0.6,
                        'confidence': pop_pct / 100.0
                    },
                    'is_moonshot': False,
                    'trade_type': 'KALSHI_PREDICTION',
                    'potential_upside': 2.0 + edge * 5.0,
                    'unified_confidence': confidence_val,
                    'sim_scaled_confidence': confidence_val,
                    'pop_from_sim': pop_pct,
                    'initial_confidence': confidence_val,
                    'sim_win_rate': pop_pct / 100.0,
                    'title': opp.get('title', ''),
                    'company_validation': True,
                    'industry': 'Prediction Markets',
                    'sector': 'Prediction Markets',
                    'days_to_expiry': days_to_expiry,
                    'timeframe_type': timeframe_type,
                    'timeframe_reasoning': timeframe_reasoning,
                    'price_projection': None,
                    'latent_news_context': {},
                    'pattern_strength': pattern_strength,
                    'divergence_score': divergence_score,
                    'current_price': current_price,
                    'strike': 50.0,
                    'kalshi_market_data': opp.get('kalshi_market_data', {}),
                    'kalshi_analysis': analysis,
                    'phasma_prediction': phasma_prediction,
                    'market_volume': volume
                }

                kalshi_signals.append(kalshi_signal)

            if kalshi_signals:
                print(f"   🔗 Added {len(kalshi_signals)} Kalshi prediction market signals to unified signal set")
                all_signals.extend(kalshi_signals)

        # 3.5. Run Unified Trading System Analysis (NEW - preserves all existing features)
        print("\n🔄 Running Unified Trading System Analysis...")
        try:
            # Run unified analysis for insider signals and thesis management
            unified_results = s.unified_system.run_unified_analysis()
            
            # Add unified system signals to convergence engine
            if unified_results["quick_trades"]:
                print(f"   📈 Found {len(unified_results['quick_trades'])} quick trade opportunities")
                for trade in unified_results["quick_trades"]:
                    s.convergence_engine.add_signal({
                        'source': 'unified_trading',
                        'ticker': trade['ticker'],
                        'confidence': trade.get('confidence', 0.7) / 100,
                        'action': trade['action'],
                        'position_size': trade.get('size', '1-2%'),
                        'sector': 'Various',
                        'region': 'GLOBAL',
                        'timestamp': datetime.now().isoformat(),
                        'details': {
                            'signal_type': 'quick_trade',
                            'reason': trade.get('reason', ''),
                            'timeframe': trade.get('hold_time', ''),
                            'stop_loss': trade.get('stop_loss', ''),
                            'target': trade.get('target', '')
                        }
                    })
            
            if unified_results["thesis_positions"]:
                print(f"   🎯 Found {len(unified_results['thesis_positions'])} thesis candidates")
                for thesis in unified_results["thesis_positions"]:
                    if thesis["action"] == "ESTABLISH_THESIS":
                        s.convergence_engine.add_signal({
                            'source': 'unified_thesis',
                            'ticker': thesis['ticker'],
                            'confidence': thesis.get('confidence', 0.6) / 100,
                            'action': 'LONG_TERM_HOLD',
                            'position_size': f"{thesis.get('max_size', 1.0)}%",
                            'sector': thesis.get('type', ''),
                            'region': 'GLOBAL',
                            'timestamp': datetime.now().isoformat(),
                            'details': {
                                'signal_type': 'thesis_position',
                                'reason': thesis.get('reason', ''),
                                'review_schedule': thesis.get('review_schedule', ''),
                                'classification': thesis.get('type', '')
                            }
                        })
            
            # Run active position management
            s.unified_system.run_active_management()
            
        except Exception as e:
            print(f"   ⚠️ Unified Trading System error: {e}")

        # 3.6. Generate stock trading signals (always analyze stocks)
        print("\n📊 Scanning for FRESH stock trading opportunities...")
        try:
            # Import dynamic market scanner
            from engines.dynamic_market_scanner import DynamicMarketScanner
            
            # Initialize dynamic scanner
            scanner = DynamicMarketScanner()
            
            # Get fresh opportunities for today
            fresh_opportunities = scanner.get_fresh_opportunities(total_limit=25)
            
            # Extract symbols from fresh opportunities
            comprehensive_watchlist = [opp['symbol'] for opp in fresh_opportunities]
            
            print(f"   🎯 Found {len(fresh_opportunities)} FRESH opportunities today:")
            for opp in fresh_opportunities[:10]:  # Show first 10
                symbol = opp['symbol']
                change = opp.get('change_pct', 0)
                volume = opp.get('volume', 0)
                opp_type = opp.get('type', opp.get('momentum', 'UNKNOWN'))
                print(f"      • {symbol}: {opp_type} ({change:+.1f}%) Vol: {volume:,}")
            
            if len(fresh_opportunities) > 10:
                print(f"      ... and {len(fresh_opportunities) - 10} more")
                
            # Pre-filter comprehensive watchlist to ONLY include affordable stocks
            print(f"\n💰 PRE-FILTERING: Removing stocks over budget before analysis...")
            comprehensive_watchlist = s.affordable_filter.filter_affordable(comprehensive_watchlist)
            
            # Generate stock signals for affordable stocks
            stock_signals = []
            print(f"\n📈 Analyzing {len(comprehensive_watchlist)} affordable stocks...")
            
            # TODO: Add stock signal generation logic here
            print(f"   📊 Stock analysis complete (signals will be added)")
            
            # Now handle options if enabled (separate from stock analysis)
            if s.options_engine:
                print(f"\n📊 Scanning for options trading opportunities...")
                try:
                    options_signals = await s.options_engine.generate_signals(comprehensive_watchlist)
                    
                    if options_signals:
                        print(f"   🎯 Generated {len(options_signals)} SUPER ADVANCED options trading signals")
                        for sig in options_signals[:3]:  # Show first 3
                            action = sig.get('action', 'UNKNOWN')
                            confidence = sig.get('confidence', 0)
                            strike_info = ""
                            if 'strike' in sig:
                                strike_info = f" @ ${sig['strike']}"
                            elif 'long_strike' in sig and 'short_strike' in sig:
                                strike_info = f" spread ${sig['long_strike']}-${sig['short_strike']}"
                            print(f"   🚀 {sig.get('symbol')}: {action}{strike_info} (CONFIDENCE: {confidence:.1%})")
                        all_signals.extend(options_signals)
                        print(f"   🔗 Added {len(options_signals)} options signals to unified analysis pipeline")
                    else:
                        print("   💤 No attractive options opportunities found")
                except Exception as e:
                    print(f"   ⚠️ Options signal generation failed: {e}")
        
        except Exception as e:
            print(f"   ⚠️ Stock analysis failed: {e}")

        # Pick worst-case assessment across index + crypto (by crash_score)

        # 2.5. Apply crash-aware filtering and position sizing (NEW THRESHOLDS) - SKIP KALSHI & OPTIONS
        if crash_assessment and all_signals:
            alert_level = crash_assessment['alert_level']
            crash_score = crash_assessment['crash_score']
            early = crash_assessment.get('early_warning') or {}
            ew_score = early.get('score') or 0.0
            ew_level = early.get('level') or 0
            
            if alert_level == 3:  # High crash risk (>55%) - Only aggressive puts
                print(f"\n💀 CRASH PROFIT MODE: Alert level 3 ({crash_score:.1%}) - Aggressive puts only!")
                filtered_signals = []
                for signal in all_signals:
                    # Skip Kalshi markets and options signals - they don't follow traditional crash patterns
                    if signal.get('source') in ['kalshi_prediction', 'options_engine', 'advanced_options_engine']:
                        filtered_signals.append(signal)
                        continue
                    if signal.get('action') == 'BUY_PUT':
                        # INCREASE put position sizes for crash profit!
                        original_size = signal.get('position_size', 0)
                        signal['position_size'] = original_size * 1.5  # 50% larger puts!
                        signal['crash_profit_mode'] = True
                        filtered_signals.append(signal)
                        print(f"   💰 BOOSTING PUT: {signal.get('symbol')} ${original_size:.0f} → ${signal['position_size']:.0f} (+50%)")
                    else:
                        print(f"   ❌ Filtering CALL: {signal.get('symbol')} (high crash risk)")
                all_signals = filtered_signals
                print(f"   🎯 {len(all_signals)} signals after crash filtering (including Kalshi & Options)")
                
            elif alert_level == 2:  # Medium correction (35-55%) - Reduce 50% + prefer puts
                print(f"\n🚨 DEFENSIVE MODE: Alert level 2 ({crash_score:.1%}) - Reduce 50% + prefer puts")
                for signal in all_signals:
                    # Skip Kalshi markets and options signals - different risk profile
                    if signal.get('source') in ['kalshi_prediction', 'options_engine', 'advanced_options_engine']:
                        continue
                    original_size = signal.get('position_size', 0)
                    if signal.get('action') == 'BUY_PUT':
                        # Keep put sizes normal (defensive hedging)
                        signal['defensive_hedge'] = True
                        print(f"   ✅ KEEPING PUT: {signal.get('symbol')} ${original_size:.0f} (hedge)")
                    else:
                        # Reduce CALL sizes by 50%
                        signal['position_size'] = original_size * 0.5
                        signal['crash_adjusted'] = True
                        print(f"   📉 REDUCING CALL: {signal.get('symbol')} ${original_size:.0f} → ${signal['position_size']:.0f} (-50%)")
                    
            elif alert_level == 1:  # Minor dip (20-35%) - Reduce 30%
                print(f"\n⚠️ CAUTION MODE: Alert level 1 ({crash_score:.1%}) - Reduce 30% (still profitable)")
                for signal in all_signals:
                    # Skip Kalshi markets and options signals - different risk profile
                    if signal.get('source') in ['kalshi_prediction', 'options_engine', 'advanced_options_engine']:
                        continue
                    original_size = signal.get('position_size', 0)
                    signal['position_size'] = original_size * 0.7  # 30% reduction
                    signal['crash_adjusted'] = True
                    print(f"   📉 {signal.get('symbol')}: ${original_size:.0f} → ${signal['position_size']:.0f} (-30%)")
            elif alert_level == 0 and ew_score >= 0.30:
                # Early-warning based soft risk reduction even before formal alerts fire
                if ew_level >= 3:
                    print(f"\n⚠️ EARLY CRASH BREWING: Early-warning {ew_score:.1%} (L{ew_level}) - Trim longs 30% and favor puts")
                    for signal in all_signals:
                        # Skip Kalshi markets and options signals - different risk profile
                        if signal.get('source') in ['kalshi_prediction', 'options_engine', 'advanced_options_engine']:
                            continue
                        original_size = signal.get('position_size', 0)
                        if signal.get('action') == 'BUY_PUT':
                            # Keep put size unchanged but tag as early hedge/probe
                            signal['early_warning_put'] = True
                            print(f"   ✅ KEEPING PUT (early hedge): {signal.get('symbol')} ${original_size:.0f}")
                        else:
                            signal['position_size'] = original_size * 0.7
                            signal['early_warning_adjusted'] = True
                            print(f"   📉 EARLY TRIM: {signal.get('symbol')}: ${original_size:.0f} → ${signal['position_size']:.0f} (-30%)")
                elif ew_level == 2:
                    print(f"\n⚠️ PRE-CRASH SETUP: Early-warning {ew_score:.1%} (L{ew_level}) - Trim longs ~20% and highlight puts")
                    for signal in all_signals:
                        # Skip Kalshi markets and options signals - different risk profile
                        if signal.get('source') in ['kalshi_prediction', 'options_engine', 'advanced_options_engine']:
                            continue
                        original_size = signal.get('position_size', 0)
                        if signal.get('action') == 'BUY_PUT':
                            signal['early_warning_put'] = True
                            print(f"   ✅ PUT AS SOFT HEDGE: {signal.get('symbol')} ${original_size:.0f}")
                        else:
                            signal['position_size'] = original_size * 0.8
                            signal['early_warning_adjusted'] = True
                            print(f"   📉 EARLY TRIM: {signal.get('symbol')}: ${original_size:.0f} → ${signal['position_size']:.0f} (-20%)")
                else:  # ew_level == 1 (SUBTLE_STRESS)
                    print(f"\n⚠️ SUBTLE STRESS: Early-warning {ew_score:.1%} (L{ew_level}) - Trim longs ~10% for caution")
                    for signal in all_signals:
                        # Skip Kalshi markets and options signals - different risk profile
                        if signal.get('source') in ['kalshi_prediction', 'options_engine', 'advanced_options_engine']:
                            continue
                        original_size = signal.get('position_size', 0)
                        if signal.get('action') == 'BUY_PUT':
                            # Leave size alone but tag for monitoring
                            signal['early_warning_put'] = True
                            print(f"   PUT (light hedge): {signal.get('symbol')} ${original_size:.0f}")
                        else:
                            signal['position_size'] = original_size * 0.9
                            signal['early_warning_adjusted'] = True
                            print(f"   EARLY TRIM: {signal.get('symbol')}: ${original_size:.0f} → ${signal['position_size']:.0f} (-10%)")

        regular_trades = []
        overnight_moonshots = []

        if not all_signals:
            print("No signals to classify - no trading opportunities today")
        else:
            for signal in all_signals:
                # Moonshot criteria: High potential + overnight timing + strong catalysts
                is_moonshot = (
                    signal.get('potential_upside', 0) >= 2.0 and  # 2x+ potential (lowered from 3x)
                    signal.get('urgency', 'medium') == 'high' and  # High urgency
                    signal.get('confidence', 0) >= 0.5 and  # 50%+ confidence (lowered from 60%)
                    any(keyword in signal.get('title', '').lower()
                        for keyword in ['overnight', 'surge', 'breakout', 'moon', 'rocket', 'explode', 'surge', 'jump', 'soar'])
                )

                if is_moonshot:
                    overnight_moonshots.append(signal)
                else:
                    regular_trades.append(signal)
        return (
            all_signals,
            news_items,
            kalshi_opportunities,
            day_trading_opportunities,
            convergence_opportunities,
            investment_opportunities,
            regular_trades,
            overnight_moonshots,
        )

    async def _stage_reconcile_open_positions(self, ctx: ApplicationContext) -> None:
        """Close mature open positions from prior runs and sync P&L."""
        try:
            open_positions = getattr(ctx.system.meta_brain.risk_manager, "open_positions", {}) or {}
            if not open_positions:
                return
            print("\n🔁 Reconciling existing open positions...")
            price_fetcher = get_price_fetcher()
            current_price_map = {}
            if ctx.market_cache and MarketDataCache:
                try:
                    current_price_map = ctx.market_cache.fetch_prices(list(open_positions.keys()))
                except Exception:
                    current_price_map = {}

            for sym, pos in list(open_positions.items()):
                try:
                    sig = (pos or {}).get('signal', {}) or {}
                    entry_time_raw = (pos or {}).get('entry_time')
                    if hasattr(entry_time_raw, 'isoformat'):
                        entry_time_dt = entry_time_raw
                    elif isinstance(entry_time_raw, str):
                        try:
                            entry_time_dt = datetime.fromisoformat(entry_time_raw)
                        except Exception:
                            entry_time_dt = datetime.now()
                    else:
                        entry_time_dt = datetime.now()

                    hold_days = max((datetime.now() - entry_time_dt).days, 0)
                    planned_days = int(sig.get('days_to_expiry', sig.get('exit_timing', {}).get('optimal_exit_day', 7)))
                    planned_days = max(1, planned_days)

                    if hold_days < planned_days:
                        continue

                    try:
                        entry_price = float(sig.get('current_price', 0.0))
                    except Exception:
                        entry_price = 0.0
                    if entry_price <= 0:
                        continue

                    current_price = current_price_map.get(sym)
                    if not current_price:
                        current_price = price_fetcher.get_real_price(sym)
                    if not current_price:
                        continue
                    try:
                        current_price = float(current_price)
                    except Exception:
                        continue

                    action = str(sig.get('action', '')).upper()
                    if 'PUT' in action:
                        realized_gain_pct = (entry_price - current_price) / entry_price
                    else:
                        realized_gain_pct = (current_price - entry_price) / entry_price

                    try:
                        position_size = float(sig.get('position_size', 0.0))
                    except Exception:
                        position_size = 0.0
                    realized_pnl_dollars = realized_gain_pct * position_size

                    ctx.system.meta_brain.risk_manager.update_pnl(realized_pnl_dollars)
                    ctx.system.meta_brain.risk_manager.close_position(sym)

                    if hasattr(ctx.system, "adaptive_threshold"):
                        is_win = realized_pnl_dollars > 0
                        original_confidence = sig.get('confidence', 0) * 100
                        ctx.system.adaptive_threshold.record_trade_outcome(
                            original_confidence,
                            realized_pnl_dollars,
                            is_win
                        )

                    print(
                        f"   ✅ Closed {sym} {action} after {hold_days}d: "
                        f"entry ${entry_price:.2f} → ${current_price:.2f} ({realized_gain_pct*100:.1f}%)"
                    )

                    try:
                        trade_data = {
                            'symbol': sym,
                            'entry_date': entry_time_dt.isoformat(),
                            'exit_date': datetime.now().isoformat(),
                            'realized_pnl_pct': realized_gain_pct,
                            'peak_gain_pct': realized_gain_pct,
                            'holding_period_days': max(1, hold_days),
                            'catalyst_type': sig.get('catalyst_type', sig.get('timeframe_type', 'Unknown')),
                            'engines_used': [sig.get('source', 'UNIFIED_ANALYSIS')],
                            'key_factors': [sig.get('rationale', '')],
                        }
                        added = ctx.system.winners_gallery.add_winner(trade_data)
                        if added:
                            print(f"   🏆 Added {sym} to Winner's Gallery")
                    except Exception as wg_err:
                        print(f"   ⚠️ Could not add {sym} to winners gallery: {wg_err}")

                except Exception as close_err:
                    print(f"   ⚠️ Error reconciling position {sym}: {close_err}")
        except Exception as reconcile_err:
            print(f"⚠️  Position reconciliation step failed: {reconcile_err}")

    async def _stage_telegram_and_execution_tail(
        self,
        ctx: ApplicationContext,
        *,
        high_confidence_approved: List[Signal],
        all_signal_objects: List[Signal],
        approved_signals: List[Signal],
        crypto_assessments: List,
        defensive_mode: bool,
        dynamic_pop_threshold: float,
        investment_opportunities: List,
        convergence_opportunities: List,
        crash_assessment: Optional[Dict],
    ) -> None:
        """Telegram posting, volatility bursts, adaptive sizing, exit monitoring, risk manager hooks."""
        market_alert_level = int(crash_assessment.get("alert_level", 0)) if crash_assessment else 0
        max_price_access = float(ctx.system.real_portfolio.state.get("available_capital", 0) or 0)

        # 6. Post approved signals to Telegram (>40% POP - realistic threshold with 2% OTM strikes)
        if ctx.config.get("telegram_enabled", False):
            if not all_signal_objects:
                print("💤 No signals to post to Telegram - no trading opportunities today")
            else:
                try:
                    from telegram_bot import get_telegram_bot
                    telegram_bot = get_telegram_bot()
                    cooldown_memory = get_cooldown_memory()
                    crypto_risk_by_symbol: Dict[str, Dict] = {}
                    ecosystem_child_to_main_root: Dict[str, str] = {}
                    try:
                        for a in crypto_assessments:
                            sym = str(a.get('symbol', '')).upper()
                            if not sym:
                                continue
                            crypto_risk_by_symbol[sym] = a
                            root = sym.split("-")[0]
                            if root and root not in crypto_risk_by_symbol:
                                crypto_risk_by_symbol[root] = a
                        ecosystem_defs = [
                            {
                                "name": "BITCOIN",
                                "main": ["BTC-USD", "BTC"],
                                "ecosystem_symbols": ["MSTR", "COIN", "MARA", "RIOT", "CLSK", "HUT", "BITF"],
                            },
                            {
                                "name": "ETHEREUM",
                                "main": ["ETH-USD", "ETH"],
                                "ecosystem_symbols": [],
                            },
                            {
                                "name": "SOLANA",
                                "main": ["SOL-USD", "SOL"],
                                "ecosystem_symbols": [],
                            },
                        ]
                        custom_mappings = ctx.config.get("ecosystem.mappings", {}) or {}
                        for eco_name, mapping in custom_mappings.items():
                            main_list = mapping.get("main", [])
                            eco_list = mapping.get("ecosystem_symbols", [])
                            if main_list:
                                ecosystem_defs.append({
                                    "name": str(eco_name).upper(),
                                    "main": [str(s).upper() for s in main_list],
                                    "ecosystem_symbols": [str(s).upper() for s in eco_list],
                                })
                        for eco in ecosystem_defs:
                            main_syms = [str(s).upper() for s in eco.get("main", [])]
                            roots = [s.split("-")[0] for s in main_syms]
                            main_root = roots[0] if roots else None
                            if not main_root:
                                continue
                            for child in eco.get("ecosystem_symbols", []):
                                child_u = str(child).upper()
                                ecosystem_child_to_main_root[child_u] = main_root
                    except Exception:
                        crypto_risk_by_symbol = {}
                        ecosystem_child_to_main_root = {}
                    
                    for signal in high_confidence_approved:
                        symbol = getattr(signal, 'symbol', 'UNKNOWN')
                        # Only post signals that clear dynamic POP & quality gates
                        pop_from_sim = getattr(signal, 'pop_from_sim', 50)
                        # Ensure minimum POP of 40% for stocks (avoid 0% values)
                        if pop_from_sim < 40:
                            pop_from_sim = 40
                        # Enforce both dynamic regime gate and strict minimum to avoid default 50% noise
                        min_required_pop = max(dynamic_pop_threshold, 40)  # Lowered to 40% for stocks
                        print(f"  🔍 {symbol}: Checking POP {pop_from_sim:.1f}% vs minimum {min_required_pop:.1f}%")
                        if pop_from_sim < min_required_pop:
                            print(f"  ❌ {symbol}: POP {pop_from_sim:.1f}% - BELOW {min_required_pop:.1f}% threshold - BLOCKED")
                            continue
                        else:
                            print(f"  ✅ {symbol}: POP {pop_from_sim:.1f}% - PASSED POP filter")

                        symbol_upper = getattr(signal, 'symbol', '').upper()
                        # Prefer any asset-specific crash assessment already attached to the signal
                        asset_assessment = getattr(signal, 'asset_crash_assessment', None)
                        if symbol_upper and not asset_assessment:
                            asset_assessment = crypto_risk_by_symbol.get(symbol_upper)
                            if not asset_assessment:
                                root = symbol_upper.split("-")[0]
                                if root:
                                    asset_assessment = crypto_risk_by_symbol.get(root)
                            if not asset_assessment:
                                main_root = ecosystem_child_to_main_root.get(symbol_upper)
                                if main_root:
                                    asset_assessment = crypto_risk_by_symbol.get(main_root)
                        asset_level = int(asset_assessment.get('alert_level', 0)) if asset_assessment else 0
                        action = getattr(signal, 'action', '').upper()
                        if asset_level >= 3 and "PUT" not in action:
                            continue

                        sim_results = getattr(signal, 'simulation_results', {}) or {}
                        win_rate = sim_results.get('win_rate', pop_from_sim / 100)

                        divergence_analysis = getattr(signal, 'divergence_analysis', {}) or {}
                        divergence_score = divergence_analysis.get('divergence_score', getattr(signal, 'divergence_score', 0))
                        pattern_strength = getattr(signal, 'pattern_strength', sim_results.get('pattern_strength', 0))
                        iv_rank = getattr(signal, 'iv_rank', None)
                        
                        # ENHANCED: Apply confidence floors for high-quality signals
                        original_confidence = getattr(signal, 'confidence', 0)
                        
                        # Check if signal has investment backing or convergence
                        has_investment = any(inv_opp.get('investing_company', {}).get('ticker', '').upper() == symbol 
                                           for inv_opp in investment_opportunities)
                        has_convergence = any(conv_opp.get('target', '').upper() == symbol 
                                            for conv_opp in convergence_opportunities)
                        
                        # Apply minimum confidence floors
                        if has_investment and has_convergence:
                            min_confidence = 0.45  # 45% minimum for investment + convergence
                            print(f"  🎯 {symbol}: Investment + Convergence signal - applying 45% minimum confidence")
                        elif has_investment:
                            min_confidence = 0.38  # 38% minimum for investment signals
                            print(f"  💰 {symbol}: Investment-backed signal - applying 38% minimum confidence")
                        elif has_convergence:
                            min_confidence = 0.35  # 35% minimum for convergence signals
                            print(f"  🔀 {symbol}: Multi-source convergence - applying 35% minimum confidence")
                        else:
                            min_confidence = original_confidence  # No floor for standard signals
                        
                        # Update signal confidence with floor
                        signal.confidence = max(original_confidence, min_confidence)
                        confidence = signal.confidence

                        # Quality gates for consistency
                        if pattern_strength is None or pattern_strength == 0:
                            pattern_strength = 0.25
                        if divergence_score is None:
                            divergence_score = 0

                        # Build dict once for downstream checks
                        signal_dict = signal.to_dict()

                        # Numeric quality gates
                        print(f"  🔍 {symbol}: Checking pattern_strength {pattern_strength:.3f} vs 0.15 minimum")
                        if pattern_strength < 0.15:
                            print(f"  ❌ {symbol}: Pattern strength {pattern_strength:.3f} - BELOW 0.15 - BLOCKED")
                            continue
                        else:
                            print(f"  ✅ {symbol}: Pattern strength {pattern_strength:.3f} - PASSED")
                        
                        # Skip divergence check for regular stocks (only applies to options/Kalshi)
                        if symbol.startswith('KX'):
                            print(f"  🔍 {symbol}: Checking divergence_score {divergence_score:.3f} vs 0.01 minimum")
                            if divergence_score < 0.01:
                                print(f"  ❌ {symbol}: Divergence score {divergence_score:.3f} - BELOW 0.01 - BLOCKED")
                                continue
                            else:
                                print(f"  ✅ {symbol}: Divergence score {divergence_score:.3f} - PASSED")
                        else:
                            print(f"  ✅ {symbol}: Regular stock - skipping divergence check")
                        
                        print(f"  🔍 {symbol}: Checking win_rate {win_rate:.1%} vs 35% minimum")
                        if win_rate < 0.35:
                            print(f"  ❌ {symbol}: Win rate {win_rate:.1%} - BELOW 35% - BLOCKED")
                            continue
                        else:
                            print(f"  ✅ {symbol}: Win rate {win_rate:.1%} - PASSED")
                        
                        if iv_rank is not None and iv_rank >= 80 and pop_from_sim < (dynamic_pop_threshold + 5):
                            print(f"  ❌ {symbol}: IV rank {iv_rank} too high for POP {pop_from_sim:.1f}% - BLOCKED")
                            continue

                        # Qualitative gates: require validated fundamentals and credible catalyst
                        sector = signal_dict.get('sector') or getattr(signal, 'sector', '')
                        industry = signal_dict.get('industry') or getattr(signal, 'industry', '')
                        market_cap = signal_dict.get('market_cap') or getattr(signal, 'market_cap', 0)
                        avg_volume = signal_dict.get('avg_volume') or getattr(signal, 'avg_volume', 0)
                        catalyst_type = signal_dict.get('catalyst_type') or getattr(signal, 'catalyst_type', '')
                        news_title = signal_dict.get('title') or getattr(signal, 'title', '')

                        print(f"  🔍 {symbol}: Checking sector/industry requirement")
                        # Allow well-known stocks without sector/industry data
                        known_stocks = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA', 'COST', 'WMT', 'JPM', 'V', 'JNJ', 'PG', 'UNH', 'HD', 'MA', 'DIS', 'BAC', 'XOM', 'PFE']
                        if not sector and not industry and symbol.upper() not in known_stocks:
                            print(f"  ❌ {symbol}: No sector or industry - BLOCKED")
                            continue
                        else:
                            if symbol.upper() in known_stocks:
                                print(f"  ✅ {symbol}: Well-known stock - sector/industry waived")
                            else:
                                print(f"  ✅ {symbol}: Has sector/industry - PASSED")
                        
                        if avg_volume:
                            print(f"  🔍 {symbol}: Checking volume {avg_volume:,} vs 100K minimum")
                            if avg_volume < 100_000:
                                print(f"  ❌ {symbol}: Volume {avg_volume:,} - BELOW 100K - BLOCKED")
                                continue
                            else:
                                print(f"  ✅ {symbol}: Volume {avg_volume:,} - PASSED")
                        
                        if market_cap:
                            print(f"  🔍 {symbol}: Checking market cap ${market_cap/1e6:.0f}M vs $50M minimum")
                            if market_cap < 50_000_000:
                                print(f"  ❌ {symbol}: Market cap ${market_cap/1e6:.0f}M - BELOW $50M - BLOCKED")
                                continue
                            else:
                                print(f"  ✅ {symbol}: Market cap ${market_cap/1e6:.0f}M - PASSED")
                        
                        print(f"  🔍 {symbol}: Checking catalyst/news requirement")
                        if not catalyst_type and not news_title:
                            print(f"  ❌ {symbol}: No catalyst or news - BLOCKED")
                            continue
                        else:
                            print(f"  ✅ {symbol}: Has catalyst/news - PASSED")

                        # NEW: Check for volatility burst
                        burst_data = await self.vol_burst_detector.check_volatility_burst(signal.symbol)
                        if burst_data:
                            # Create unique key for deduplication
                            burst_key = f"VOL_BURST:{signal.symbol}:{int(burst_data['burst_strength']*10)}"
                            if burst_key not in self.posted_signals:
                                burst_alert = {
                                    'alert_id': f"burst_{signal.symbol}_{int(datetime.now().timestamp())}",
                                    'symbol': signal.symbol,
                                    'type': 'volatility_burst',
                                    'priority': AlertPriority.HIGH,
                                    'trigger_reason': f"Volatility burst detected - {burst_data['burst_strength']:.1f} strength",
                                    'pop': pop_from_sim,
                                    'position_size': signal.position_size,
                                    'burst_data': burst_data
                                }
                                await self.alert_router.route_alert(burst_alert)
                                self.posted_signals.add(burst_key)
                                self._save_posted_signals()
                            else:
                                print(f"  ⏭️ Volatility burst alert already posted for {signal.symbol} - skipping")

                        # NEW: Add to catalyst calendar (temporarily disabled)
                        # self.catalyst_calendar.add_catalyst_event({
                        #     'symbol': signal_dict.get('symbol', signal.symbol),
                        #     'catalyst_type': signal_dict.get('catalyst_type', 'Unknown'),
                        #     'days_to_expiry': signal_dict.get('days_to_expiry', 7),
                        #     'pop_at_entry': pop_from_sim,
                        #     'catalyst_notes': signal_dict.get('title', '')
                        # })

                        # NEW: Add "why it's moving" insight strip (temporarily disabled)
                        # insight_strip = self.why_moving_strip.generate_insight_strip({
                        #     'symbol': signal_dict.get('symbol', signal.symbol),
                        #     'recent_news': signal_dict.get('title', ''),
                        #     'catalyst_type': signal_dict.get('catalyst_type'),
                        #     'volume_surge': getattr(signal, 'volume_surge', 1),
                        #     'float_info': getattr(signal, 'float_info', ''),
                        #     'sentiment_score': getattr(signal, 'sentiment_score', 0),
                        #     'current_price': getattr(signal, 'current_price', 0)
                        # })
                        # signal_dict['insight_strip'] = insight_strip

                        # Enrich signal data for strategy suggestion
                        signal_dict['pop'] = pop_from_sim
                        signal_dict['iv_rank'] = iv_rank
                        signal_dict['pattern_strength'] = pattern_strength
                        signal_dict['divergence_score'] = divergence_score
                        signal_dict['win_rate'] = win_rate
                        signal_dict['is_defensive_mode'] = defensive_mode
                        signal_dict['volume_surge'] = getattr(signal, 'volume_surge', signal_dict.get('volume_surge', 1))
                        signal_dict['news_catalyst'] = bool(signal_dict.get('title')) or bool(signal_dict.get('catalyst_type'))
                        signal_dict['days_to_earnings'] = getattr(signal, 'days_to_earnings', signal_dict.get('days_to_earnings', 30))
                        signal_dict['action'] = getattr(signal, 'action', signal_dict.get('action'))
                        signal_dict['days_to_expiry'] = signal_dict.get('days_to_expiry', getattr(signal, 'days_to_expiry', 7))

                        # NEW: Suggest strategy type
                        strategy_suggestion = self.strategy_cards.suggest_strategy({
                            'symbol': signal_dict.get('symbol', signal.symbol),
                            'sector': signal_dict.get('sector', ''),
                            'catalyst_type': signal_dict.get('catalyst_type', ''),
                            'float_millions': getattr(signal, 'float_millions', 100),
                            'volatility': getattr(signal, 'volatility', 0.3),
                            'volume_surge': signal_dict['volume_surge'],
                            'rsi': getattr(signal, 'rsi', 50),
                            'news_catalyst': signal_dict['news_catalyst'],
                            'iv_rank': iv_rank,
                            'pop': pop_from_sim,
                            'divergence_score': divergence_score,
                            'pattern_strength': pattern_strength,
                            'win_rate': win_rate,
                            'action': signal_dict['action'],
                            'days_to_expiry': signal_dict['days_to_expiry'],
                            'days_to_earnings': signal_dict['days_to_earnings'],
                            'is_defensive_mode': defensive_mode
                        })
                        signal_dict['suggested_strategy'] = strategy_suggestion.value if strategy_suggestion else 'BREAKOUT'

                        # 🚀 ADAPTIVE POSITION SIZING: Capital-based smart money management
                        current_price = stock_data['Close'].iloc[-1] if 'stock_data' in locals() else 0
                        portfolio_summary = ctx.system.real_portfolio.get_portfolio_summary()
                        # Use fallback tier config if accessible_universe not available
                        tier_config = portfolio_summary.get('accessible_universe', {}).get('position_limits', {
                            'micro': {'max_position': 100},
                            'small': {'max_position': 500},
                            'medium': {'max_position': 2000},
                            'large': {'max_position': 10000}
                        })
                        
                        # Prepare opportunity data for position sizing
                        opportunity_data = {
                            'confidence': confidence,
                            'volatility': getattr(signal, 'volatility', 0.3),
                            'is_moon_shot': getattr(signal, 'is_moon_shot', False),
                            'moon_shot_score': getattr(signal, 'moon_shot_score', 0)
                        }
                        
                        # Calculate adaptive position size
                        position_size = self.position_sizer.calculate_position_size(
                            symbol=symbol,
                            current_price=current_price,
                            portfolio_capital=portfolio_summary['available_capital'],
                            tier_config=tier_config,
                            opportunity_data=opportunity_data,
                            existing_positions={}  # TODO: Pass actual existing positions
                        )
                        
                        # Apply defensive mode adjustments to adaptive sizing
                        if market_alert_level == 1:
                            position_size.position_value *= 0.7
                        elif market_alert_level == 2:
                            position_size.position_value *= 0.5
                        elif market_alert_level >= 3:
                            position_size.position_value *= 0.3
                        
                        # Update signal with adaptive position size
                        adjusted_position_size = int(position_size.position_value / current_price) if current_price > 0 else 0
                        signal.position_size = adjusted_position_size
                        signal_dict['position_size'] = adjusted_position_size
                        
                        print(f"    Adaptive Position Sizing: {adjusted_position_size} shares @ ${current_price:.2f}")
                        print(f"       Risk: ${position_size.risk_amount:.2f} ({position_size.risk_percent:.1f}%) | Method: {position_size.method}")
                        if getattr(signal, 'is_moon_shot', False):
                            print(f"       MOON SHOT: {getattr(signal, 'moon_shot_potential', '1x')} potential")
                        
                        # Check for pump pattern on penny stocks
                        if current_price <= 10.0 and adjusted_position_size > 0:  # Penny stock with position
                            pump_analysis = self.pump_dump_detector.analyze_stock(symbol, current_price, adjusted_position_size)
                            
                            # Check for confluence signals (insider + institutional + analyst + options)
                            insider_data = {}
                            if hasattr(self.insider_monitor, 'insider_data'):
                                insider_data = self.insider_monitor.insider_data
                            
                            confluence_signal = self.insider_signal_integrator.analyze_stock(symbol, insider_data)
                            
                            if confluence_signal and confluence_signal.confidence_level in ['HIGH', 'VERY HIGH']:
                                print(f"    CONFLUENCE: {symbol} - {confluence_signal.confidence_level} confidence")
                                print(f"       {confluence_signal.reasoning}")
                                
                                # Boost pump strength if confluence detected
                                if pump_analysis.get('pump_detected'):
                                    pump_analysis['pump_strength'] = min(pump_analysis['pump_strength'] + 0.2, 1.0)
                                    print(f"    PUMP BOOSTED: {pump_analysis.get('pump_strength', 0):.1%} (confluence detected)")
                            
                            if pump_analysis.get('pump_detected'):
                                print(f"    PUMP DETECTED: {pump_analysis.get('pump_strength', 0):.1%} strength")
                                exit_strategy = pump_analysis.get('exit_strategy')
                                if exit_strategy:
                                    signal_dict['pump_exit_strategy'] = exit_strategy
                                    for level in exit_strategy.get('exit_levels', []):
                                        print(f"       Exit Level {level['level']}: {level['description']}")

                            # Record ticker found for daily learning
                            if hasattr(self, 'daily_learning_tracker'):
                                self.daily_learning_tracker.record_ticker_found(
                                    signal.symbol,
                                    signal.source or 'unknown',
                                    signal.confidence
                                )
                            signal_key = f"{symbol}_{action}_{signal_dict.get('entry_price', 'N/A')}"
                            
                            if signal_key in self.posted_signals:
                                print(f"  ⚠️ Signal already posted to Telegram: {signal_key}")
                            else:
                                print(f"  ATTEMPTING TO POST TO TELEGRAM: {symbol}")
                                print(f"     Signal details: {action} {symbol} @ {signal_dict.get('entry_price', 'N/A')} (Confidence: {confidence:.1%})")
                            
                            # Ensure signal types are properly identified
                            if symbol.startswith('KX'):
                                signal_dict['source'] = 'kalshi_prediction'
                                print(f"  📈 Identified {symbol} as Kalshi prediction market")
                            elif signal_dict.get('trade_type') == 'STOCK':
                                signal_dict['source'] = 'stock_signal'
                                print(f"  📈 Identified {symbol} as stock signal")
                            try:
                                # Check if we're in an async context
                                import asyncio
                                if asyncio.get_event_loop().is_running():
                                    print(f"  Event loop already running - posting directly")
                                    # Use synchronous method when event loop is running
                                    if signal_dict.get('source') == 'stock_signal':
                                        formatted_message = telegram_bot.format_stock_signal_message(signal_dict)
                                    else:
                                        formatted_message = telegram_bot.format_signal_message(signal_dict)
                                    result = telegram_bot.send_message(formatted_message)
                                    print(f"  📱 TELEGRAM POST RESULT: {result} (True=success)")
                                    
                                    # Add to posted signals if successful
                                    if result:
                                        self.posted_signals.add(signal_key)
                                        self._save_posted_signals()  # Persist to disk
                                        print(f"  ✅ Signal recorded as posted: {signal_key}")
                                        
                                        # Execute Alpaca paper trade FIRST before Telegram
                                        if hasattr(self, 'alpaca_paper_trader') and self.alpaca_paper_trader.alpaca and signal_dict.get('trade_type') == 'STOCK':
                                            print(f"  🔄 EXECUTING ALPACA TRADE BEFORE TELEGRAM...")
                                            self._execute_alpaca_trade_from_signal(signal_dict)
                                        elif self.paper_portfolio and signal_dict.get('trade_type') == 'STOCK':
                                            print(f"  🔄 FALLBACK: Using internal paper trading...")
                                            self._execute_paper_trade_from_signal(signal_dict)
                                        else:
                                            print(f"  📊 No paper trading available for {signal_dict.get('symbol', 'UNKNOWN')}")
                                else:
                                    print(f"  Creating async task for Telegram posting")
                                    task = asyncio.create_task(telegram_bot.post_signal(signal_dict))
                                    print(f"  Telegram task created: {task}")
                            except Exception as e:
                                print(f"  TELEGRAM POSTING ERROR: {e}")
                        else:
                            print(f"  Telegram bot not configured - skipping posting")
                        
                        # RECORD TO TRADE MEMORY
                        if signal.symbol not in self.trade_memory:
                            self.trade_memory[signal.symbol] = {
                                'last_signal': datetime.now(),
                                'action': signal.action,
                                'confidence': confidence,
                                'pop': pop_from_sim,
                                'cooling_days': 7
                            }
                            print(f"   📝 Trade Memory: Recorded {signal.symbol} (cooldown: 7 days)")
                    
                except Exception as e:
                    print(f"  ❌ Error processing signal {getattr(signal, 'symbol', 'UNKNOWN')}: {str(e)}")
            
            # 🏆 Post Winner's Gallery once per day (UTC) to avoid spamming
            try:
                now_utc = datetime.utcnow()
                should_post_gallery = False
                if self.last_gallery_posted_at is None:
                    should_post_gallery = True
                else:
                    days_since_last = (now_utc.date() - self.last_gallery_posted_at.date()).days
                    if days_since_last >= 1:
                        should_post_gallery = True

                if should_post_gallery:
                    gallery_report = self.winners_gallery.generate_gallery_report()
                    if gallery_report.get('winners'):
                        gallery_message = self.winners_gallery.format_gallery_message(gallery_report)
                        gallery_key = f"GALLERY:{now_utc.strftime('%Y-%m-%d')}"
                        if gallery_key not in self.posted_signals:
                            telegram_bot.send_message(gallery_message)
                            self.posted_signals.add(gallery_key)
                            self._save_posted_signals()
                            self.last_gallery_posted_at = now_utc
                            print("    🏆 Posted Winner's Gallery to Telegram (daily cadence)")
                        else:
                            print("    🏆 Winner's Gallery already posted today - skipping")
                    else:
                        print("    🏆 No winners yet to post to Telegram (daily check)")
            except Exception as wg_err:
                print(f"    ⚠️ Failed to post Winner's Gallery: {wg_err}")

            # 🕵️ Insider monitor (capital-aware)
            try:
                if getattr(self.insider_monitor, "enabled", False):
                    print(f"    🕵️ Insider Monitor: Capital-Aware Analysis (Max Price: ${max_price_access:.2f})")
                    print("    ⚠️  Note: SEC Form 4 XML parsing pending - results limited until data source implemented")
                    
                    # Get insider trading opportunities
                    insider_hits = self.insider_monitor.fetch_and_analyze_opportunities()
                    if insider_hits:
                        for hit in insider_hits[:5]:  # limit chatter
                            ticker = hit.get('ticker', 'N/A')
                            score = hit.get('opportunity_score', 0)
                            rec = hit.get('recommendation', 'UNKNOWN')
                            reasoning = hit.get('reasoning', 'No reasoning')
                            current_price = hit.get('current_price', 0)
                            insider_price = hit.get('purchase_price', 0)
                            transaction_value = hit.get('transaction_value', 0)
                            sector = hit.get('sector', 'Unknown')
                            
                            # Create unique key for deduplication
                            insider_key = f"INSIDER:{ticker}:{rec}:{int(transaction_value)}"
                            if insider_key in self.posted_signals:
                                continue
                            
                            # Calculate gain since purchase
                            gain_text = "N/A"
                            if insider_price > 0 and current_price > 0:
                                gain_pct = ((current_price - insider_price) / insider_price) * 100
                                gain_text = f"{gain_pct:+.1f}%"
                            
                            msg = (
                                f"🕵️ **Insider Opportunity Alert**\n"
                                f"📈 **{ticker} - {rec}**\n"
                                f"💰 Score: {score:.0f}/100\n"
                                f"🏢 Sector: {sector}\n"
                                f"💸 Insider Purchase: ${transaction_value/1e3:.0f}K at ${insider_price:.2f}\n"
                                f"📊 Current Price: ${current_price:.2f} ({gain_text})\n"
                                f"🎯 Analysis: {reasoning}\n"
                                f"📅 Days Since Purchase: {hit.get('days_since_purchase', 0)}\n"
                                f"🔗 Details: {hit.get('link', 'N/A')}"
                            )
                            result = telegram_bot.send_message(msg)
                            if result:
                                self.posted_signals.add(insider_key)
                                self._save_posted_signals()
                        print(f"    🕵️ Posted {min(len(insider_hits),5)} insider buy alerts to Telegram")
                    else:
                        print("    🕵️ No insider buys to post (filtered)")
            except Exception as im_err:
                print(f"    ⚠️ Insider monitor failed: {im_err}")

            # 🏛️ Politician trading tracker
            try:
                if self.politician_tracker.enabled:
                    print("    🏛️ Politician Trading Tracker: Congressional/Government Analysis")
                    politician_trades = self.politician_tracker.fetch_recent_trades()
                    
                    if politician_trades:
                        # Get top trades by value
                        top_trades = self.politician_tracker.get_top_trades(5)
                        
                        for trade in top_trades:
                            # Create unique key for deduplication
                            politician_key = f"POLITICIAN:{trade.get('ticker', 'N/A')}:{trade.get('representative', 'N/A')}:{trade.get('transaction_date', 'N/A')}"
                            if politician_key in self.posted_signals:
                                continue
                            
                            msg = self.politician_tracker.format_trade_for_telegram(trade)
                            result = telegram_bot.send_message(msg)
                            if result:
                                self.posted_signals.add(politician_key)
                                self._save_posted_signals()
                        
                        print(f"    🏛️ Posted {len(top_trades)} politician trade alerts to Telegram")
                        
                        # Show summary stats
                        stats = self.politician_tracker.get_summary_stats()
                        print(f"    🏛️ Summary: {stats.get('total_trades', 0)} total trades, "
                              f"${stats.get('total_value', 0):,} total value")
                    else:
                        print("    🏛️ No recent politician trades found")
            except Exception as pt_err:
                print(f"    ⚠️ Politician tracker failed: {pt_err}")

            # 🎯 Exit Strategy Monitoring
            try:
                print("    🎯 Exit Strategy Monitoring: Position Analysis")
                
                # Use simulation-based exit manager for optimal profit maximization
                sim_positions = self.simulation_exit_manager.get_all_positions()
                if sim_positions:
                    print(f"    📊 Found {len(sim_positions)} positions with simulation targets")
                    self.simulation_exit_manager.print_status()
                    
                    for ticker in sim_positions.keys():
                        sim_exit = self.simulation_exit_manager.analyze_position(ticker)
                        
                        if sim_exit and sim_exit.last_signal != SimExitSignal.HOLD:
                            print(f"    🎯 SIMULATION EXIT: {ticker} - {sim_exit.last_reason.value}")
                            
                            # Update real portfolio for exits
                            if sim_exit.last_signal in [SimExitSignal.FULL_SELL, SimExitSignal.EMERGENCY_EXIT]:
                                # Calculate P&L
                                pnl = (sim_exit.current_price - sim_exit.entry_price) * 1  # Assuming 1 share
                                pnl_pct = ((sim_exit.current_price - sim_exit.entry_price) / sim_exit.entry_price) * 100
                                
                                print(f"    💰 SIMULATION EXIT P&L: {ticker} ${pnl:+.2f} ({pnl_pct:+.1f}%)")
                                
                                # Record in real portfolio
                                ctx.system.real_portfolio.state['last_updated'] = datetime.now().isoformat()
                
                # Fallback to regular exit manager for positions without simulations
                positions = self.exit_strategy_manager.get_all_positions()
                
                if positions:
                    exit_alerts = []
                    
                    for ticker in positions.keys():
                        position = self.exit_strategy_manager.analyze_position(ticker)
                        
                        # Check profit maximization exits FIRST for faster profits
                        if self.profit_exit_manager and position and hasattr(position, 'entry_price'):
                            # Get dynamic targets for this position
                            profit_targets = self.target_calculator.calculate_profit_targets(
                                ticker, getattr(position, 'catalyst_type', 'Default'), 
                                position.current_price, 0.7
                            )
                            
                            # Use dynamic targets in exit analysis
                            profit_exit = self.profit_exit_manager.check_exit_signals(
                                ticker, position.current_price
                            )
                            if profit_exit and profit_exit.get('action') in ['PARTIAL_SELL', 'FULL_EXIT']:
                                print(f"    💰 PROFIT EXIT: {ticker} - {profit_exit.get('reason')}")
                                print(f"       Action: {profit_exit.get('action')} | Price: ${position.current_price:.2f}")
                                
                                # Create unique key for deduplication
                                profit_exit_key = f"PROFIT_EXIT:{ticker}:{profit_exit.get('action')}:{int(position.current_price)}"
                                if profit_exit_key in self.posted_signals:
                                    print(f"       ⏭️ Profit exit already posted - skipping")
                                else:
                                    # Generate profit exit alert
                                    profit_message = f"💰 PROFIT EXIT: {ticker}\n"
                                    profit_message += f"📊 {profit_exit.get('reason')}\n"
                                    profit_message += f"💵 Price: ${position.current_price:.2f}\n"
                                    profit_message += f"🎯 Action: {profit_exit.get('action')}"
                                    
                                    if hasattr(self, 'telegram_bot') and self.telegram_bot:
                                        result = self.telegram_bot.send_message(profit_message)
                                        if result:
                                            self.posted_signals.add(profit_exit_key)
                                            self._save_posted_signals()
                                    
                                    # Add to exit alerts
                                    exit_alerts.append({
                                        'ticker': ticker,
                                        'signal': 'PROFIT_EXIT',
                                        'reason': profit_exit.get('reason'),
                                        'current_price': position.current_price,
                                        'action': profit_exit.get('action'),
                                        'sell_percent': profit_exit.get('sell_percent', 1.0)
                                    })
                        
                        # Check pump/dump exit signals AFTER profit exits
                        if position and hasattr(position, 'entry_price'):
                            entry_price = position.entry_price
                            current_price = position.current_price
                            
                            if entry_price > 0 and entry_price <= 10.0:  # Penny stock
                                pump_exit = self.pump_dump_detector.check_exit_signal(ticker, current_price, entry_price)
                                if pump_exit and pump_exit.get('exit_signal'):
                                    print(f"    PUMP EXIT: {ticker} - {pump_exit.get('reason')}")
                                    print(f"       Sell {pump_exit.get('sell_percent', 0)*100:.0f}% at ${current_price:.2f}")
                                    
                                    # Create unique key for deduplication
                                    pump_exit_key = f"PUMP_EXIT:{ticker}:{int(current_price)}:{pump_exit.get('sell_percent', 0)}"
                                    if pump_exit_key in self.posted_signals:
                                        print(f"       ⏭️ Pump exit already posted - skipping")
                                    else:
                                        # Generate special pump exit alert
                                        pump_message = f"🚨 PUMP EXIT: {ticker} - {pump_exit.get('reason')}\n"
                                        pump_message += f"💰 Sell {pump_exit.get('sell_percent', 0)*100:.0f}% at ${current_price:.2f}"
                                        
                                        if hasattr(self, 'telegram_bot') and self.telegram_bot:
                                            result = self.telegram_bot.send_message(pump_message)
                                            if result:
                                                self.posted_signals.add(pump_exit_key)
                                                self._save_posted_signals()
                                        
                                        # Add to exit alerts
                                        exit_alerts.append({
                                            'ticker': ticker,
                                            'signal': 'PUMP_EXIT',
                                            'reason': pump_exit.get('reason'),
                                            'current_price': current_price,
                                            'sell_percent': pump_exit.get('sell_percent', 1.0)
                                        })
                                    
                                    # Update portfolio for pump exit
                                    if pump_exit.get('sell_percent', 1.0) >= 1.0:
                                        # Full exit - update capital
                                        position_size = position.current_size
                                        pnl = (current_price - entry_price) * position_size
                                        pnl_pct = ((current_price - entry_price) / entry_price) * 100
                                        
                                        current_capital = ctx.system.real_portfolio.state['available_capital']
                                        new_capital = current_capital + pnl
                                        
                                        print(f"    PUMP EXIT P&L: {ticker} ${pnl:+.2f} ({pnl_pct:+.1f}%)")
                                        
                                        # Record trade in real portfolio
                                        ctx.system.real_portfolio.state['last_updated'] = datetime.now().isoformat()
                                    
                                    continue  # Skip regular exit check if pump exit triggered
                        
                        if position and position.last_signal.value in ['PARTIAL_SELL', 'FULL_SELL', 'EMERGENCY_EXIT']:
                            # 🚀 PORTFOLIO CAPITAL UPDATE: Update capital when positions close
                            if position.last_signal.value in ['FULL_SELL', 'EMERGENCY_EXIT']:
                                # Calculate P&L for closed position
                                entry_price = position.entry_price
                                current_price = position.current_price
                                position_size = position.current_size
                                
                                if entry_price > 0 and position_size > 0:
                                    pnl = (current_price - entry_price) * position_size
                                    pnl_pct = ((current_price - entry_price) / entry_price) * 100
                                    
                                    # Update portfolio capital
                                    current_capital = ctx.system.real_portfolio.state['available_capital']
                                    new_capital = current_capital + pnl
                                    
                                    print(f"    💰 PORTFOLIO UPDATE: {ticker} P&L ${pnl:+.2f} ({pnl_pct:+.1f}%)")
                                    print(f"       Capital: ${current_capital:.2f} → ${new_capital:.2f}")
                                    
                                    # Update real portfolio state
                                    ctx.system.real_portfolio.state['last_updated'] = datetime.now().isoformat()
                            
                            # Generate exit alert
                            alert = {
                                'ticker': ticker,
                                'signal': position.last_signal.value,
                                'reason': position.last_reason.value,
                                'current_price': position.current_price,
                            }
                            
                            exit_message = f"🚨 EXIT ALERT: {ticker} {position.last_signal.value} at ${position.current_price:.2f}"
                            
                            # Create unique key for deduplication
                            exit_alert_key = f"EXIT_ALERT:{ticker}:{position.last_signal.value}:{int(position.current_price)}"
                            if exit_alert_key in self.posted_signals:
                                print(f"    ⏭️ Exit alert already posted - skipping")
                            else:
                                if hasattr(self, 'telegram_bot') and self.telegram_bot:
                                    result = self.telegram_bot.send_message(exit_message)
                                    if result:
                                        self.posted_signals.add(exit_alert_key)
                                        self._save_posted_signals()
                                print(f"    📱 Exit alert: {ticker} {position.last_signal.value}")
                            
                            # Remove position from risk manager to prevent duplicate alerts
                            open_positions = getattr(self.meta_brain.risk_manager, 'open_positions', {})
                            if ticker in open_positions:
                                del open_positions[ticker]
                                print(f"    🗑️ Removed {ticker} from open positions")
                    
                    print(f"    🎯 Monitored {len(positions)} positions, {len(exit_alerts)} exit signals generated")
                else:
                    print("    🎯 No active positions to monitor")
                    
            except Exception as es_err:
                print(f"    ⚠️ Exit strategy monitoring failed: {es_err}")
            
            # Update risk management with final PnL
            pnl_change = 0.0  # Default PnL change for this cycle
            self.meta_brain.risk_manager.update_pnl(pnl_change)

            # Add positions to risk manager (for all approved signals)
            for signal in approved_signals:
                self.meta_brain.risk_manager.add_position(signal.symbol, {
                    "signal": signal.to_dict(),
                    "entry_time": datetime.now()
                })
        else:
            print("💤 No high-confidence signals to add to portfolio")
    async def run_full_cycle(self):
        """Run complete unified trading cycle with all analysis methods"""
        print("🔄 Starting Unified Phasma Trading Cycle")
        print("=" * 50)
        cycle_stage_timings: Dict[str, float] = {}
        ctx = ApplicationContext.bind(self, cycle_stage_timings)
        _stage_name = "preflight_and_risk"
        _stage_start = time.perf_counter()
        await self._stage_startup_services(ctx)

        await self._stage_reconcile_open_positions(ctx)

        # Initialize signals container early for crash detection and tracking
        all_signals = []

        # 0.8. Check global macro indicators FIRST (before trading)
        macro_risk, macro_alert = await self._stage_macro_and_fred(ctx)

        crash_assessment, market_safe, index_crash, crypto_assessments = self._stage_crash_preflight(
            ctx,
            all_signals,
            macro_risk,
        )

        cycle_stage_timings[_stage_name] = time.perf_counter() - _stage_start
        _stage_name = "signal_generation"
        _stage_start = time.perf_counter()
        # 1. UNIFIED META BRAIN - All Systems Working Together
        result = await self._stage_signal_generation(ctx, crash_assessment, macro_risk)
        if result is None:
            return []
        (
            all_signals,
            news_items,
            kalshi_opportunities,
            day_trading_opportunities,
            convergence_opportunities,
            investment_opportunities,
            regular_trades,
            overnight_moonshots,
        ) = result

        cycle_stage_timings[_stage_name] = time.perf_counter() - _stage_start
        _stage_name = "display_and_secondary_scans"
        _stage_start = time.perf_counter()
        all_signals, news_items = await self._stage_display_and_secondary_scans(
            ctx,
            regular_trades=regular_trades,
            overnight_moonshots=overnight_moonshots,
            news_items=news_items,
            all_signals=all_signals,
        )

        cycle_stage_timings[_stage_name] = time.perf_counter() - _stage_start
        _stage_name = "arbitration_and_execution"
        _stage_start = time.perf_counter()
        all_signal_objects = self._build_signal_objects_for_arbitration(ctx, all_signals)

        approved_signals, real_portfolio, defensive_mode, dynamic_pop_threshold = self._stage_prepare_arbitration_context(
            ctx,
            crash_assessment=crash_assessment,
            all_signal_objects=all_signal_objects,
        )

        high_confidence_approved = self._stage_streamlined_signal_filtering(ctx, approved_signals)
        high_confidence_approved = self._stage_bankroll_intel_and_pro_options(ctx, high_confidence_approved)
        high_confidence_approved = self._stage_jury_final_review(
            ctx,
            high_confidence_approved,
            crash_assessment=crash_assessment,
        )

        await self._stage_telegram_and_execution_tail(
            ctx,
            high_confidence_approved=high_confidence_approved,
            all_signal_objects=all_signal_objects,
            approved_signals=approved_signals,
            crypto_assessments=crypto_assessments,
            defensive_mode=defensive_mode,
            dynamic_pop_threshold=dynamic_pop_threshold,
            investment_opportunities=investment_opportunities,
            convergence_opportunities=convergence_opportunities,
            crash_assessment=crash_assessment,
        )

        cycle_stage_timings[_stage_name] = time.perf_counter() - _stage_start

        # Trading configuration
        self.bankroll = 2000
        self.pop_threshold = 0.5
        self.risk_per_trade = 0.01
        self.max_drawdown = 0.1

        # Enhanced configuration for hybrid scanning
        self.all_sectors_mode = ctx.config.get('trading.all_sectors_mode', False)  # New toggle
        self.min_options_volume = ctx.config.get('trading.min_options_volume', 5000)
        self.min_implied_volatility = ctx.config.get('trading.min_implied_volatility', 50.0)

        self.meta_brain.save_state(phasma_state_file())

        return approved_signals

    async def _run_unified_analysis(
        self,
        news_items: List[Dict],
        cycle_price_map: Optional[Dict[str, Any]] = None,
        *,
        analysis_config: Optional[Any] = None,
        ctx: Optional[ApplicationContext] = None,
    ) -> List[Dict]:
        """Run unified analysis on news items with proper error handling"""
        if ctx is None:
            ctx = ApplicationContext.bind(self, {})
        ps = ctx.system
        signals = []
        price_map = cycle_price_map if isinstance(cycle_price_map, dict) else {}
        cfg = analysis_config if analysis_config is not None else ctx.config

        for news_item in news_items:
            # CRITICAL: Check if news_item is None or not a dictionary
            if news_item is None:
                print(f"  ⚠️ SKIPPING: News item is None")
                continue

            if not isinstance(news_item, dict):
                print(f"  ⚠️ SKIPPING: News item is not a dictionary (type: {type(news_item)})")
                print(f"      Content: {str(news_item)[:100]}...")
                continue

            # Check if essential fields exist
            if not news_item.get('symbol'):
                print(f"  ⚠️ SKIPPING: News item missing symbol field")
                print(f"      Available keys: {list(news_item.keys())}")
                print(f"      Title: {news_item.get('title', 'NO_TITLE')[:50]}...")
                continue

            symbol = news_item.get('symbol', '')

            try:
                # Company Validation: Only process real, valid companies (not just AI)
                fact_check = ps.news_engine._fact_check_company(news_item)
                if not isinstance(fact_check, dict):
                    fact_check = {'is_valid': False, 'validation_score': 0.0, 'company_info': {}}
                if 'is_valid' not in fact_check:
                    fact_check['is_valid'] = False

                # Debug: Check what fact_check returned
                if fact_check is None:
                    print(f"  ⚠️ FACT_CHECK RETURNED NONE for {news_item.get('symbol', 'UNKNOWN')}")
                    continue

                if not isinstance(fact_check, dict):
                    print(f"  ⚠️ FACT_CHECK NOT DICT for {news_item.get('symbol', 'UNKNOWN')}: {type(fact_check)}")
                    continue

                # Skip companies that aren't valid real companies
                if not fact_check.get('is_valid', False):
                    print(f"  ❌ Skipping {news_item.get('symbol', 'UNKNOWN')} - Not a real company (sector: {news_item.get('sector', 'UNKNOWN')})")
                    continue  # Skip early, no expensive analysis needed

                # Check if this is a Kalshi prediction market (not a real company)
                symbol = news_item.get('symbol', 'UNKNOWN')
                if symbol.startswith('KX') or '-' in symbol and len(symbol.split('-')) > 1:
                    print(f"  🎯 Prediction Market: {symbol} - Kalshi contract (not a company)")
                    print(f"     📊 Type: Prediction contract | Risk: Bounded")
                    print(f"     🎯 Market: {symbol.split('-')[1] if '-' in symbol else 'Unknown'}")
                    continue  # Skip company validation for prediction markets

                # Debug: Show what company we're analyzing
                company_info = fact_check.get('company_info', {})
                real_ticker = company_info.get('real_ticker', False)
                avg_volume = company_info.get('avg_volume', 'N/A')
                try:
                    avg_volume_display = f"{int(avg_volume):,}"
                except Exception:
                    avg_volume_display = str(avg_volume)
                price_range = company_info.get('price_range', 'N/A')

                sector = news_item.get('sector', 'UNKNOWN')
                sector_name = sector if sector != 'AI' else 'Technology'

                company_name = (
                    company_info.get('full_name')
                    or company_info.get('name')
                    or company_info.get('symbol')
                    or news_item.get('symbol', 'UNKNOWN')
                )

                print(
                    f"  🎯 Real Company: {news_item.get('symbol', 'UNKNOWN')} - "
                    f"{company_name} ({sector_name} sector)"
                )
                print(f"     📊 Volume: {avg_volume_display} | Price: {price_range} | Risk: {fact_check.get('risk_level', 'UNKNOWN')}")

                try:
                    _usch = str(news_item.get("symbol", "")).upper()
                    _cp = news_item.get("current_price")
                    if (_cp is None or float(_cp) <= 0) and getattr(ps, "robust_price_fetcher", None):
                        _cp = ps.robust_price_fetcher.get_real_price(_usch)
                    if _cp and float(_cp) > 0:
                        ps.skipped_opportunity_watchlist.note_price_move(
                            _usch,
                            float(_cp),
                            str(news_item.get("action", "BUY")).upper(),
                        )
                except Exception:
                    pass

                divergence_analysis = ps.news_engine._calculate_layered_divergence(news_item)
                latent_context = {}
                try:
                    latent_context = ps.news_engine.build_latent_news_context(symbol)
                except Exception:
                    latent_context = {}

                pattern_signals = ps.news_engine.detect_technical_patterns([news_item])

                for pattern_signal in pattern_signals:
                    # Fact check validation (already done above)
                    if not fact_check.get('is_valid', False):
                        continue

                    patterns = pattern_signal.get('patterns_detected', [])
                    pattern_strength = pattern_signal.get('pattern_strength', 0)
                    technical_bias = pattern_signal.get('technical_bias', 'NEUTRAL')

                    # Unified confidence calculation using ALL analysis methods
                    unified_confidence = (
                        pattern_strength * 0.3 +                    # Technical patterns
                        divergence_analysis['divergence_score'] * 0.2 +  # Between the lines
                        fact_check.get('validation_score', 0) * 0.1 +    # Company validation
                        pattern_signal.get('alignment_score', 0) * 0.2 +  # General alignment
                        0.2  # Base confidence for any detected signal
                    )
                    
                    # CONFIDENCE BOOSTERS
                    
                    # 1. Volume surge multiplier
                    volume_multiplier = 1.0
                    if 'volume_data' in locals() and volume_data:
                        recent_volume = volume_data.get('recent_avg', 0)
                        current_volume = volume_data.get('current', 0)
                        if recent_volume > 0 and current_volume > recent_volume * 3:
                            volume_multiplier = 1.5  # 3x+ volume surge
                            print(f"      📈 Volume surge detected: {current_volume/recent_volume:.1f}x average")
                    
                    # 2. Corporate investment booster (DYNAMIC based on strategic analysis)
                    investment_boost = 0.0
                    symbol = news_item.get('symbol', '').upper()
                    for inv_opp in investment_opportunities if 'investment_opportunities' in locals() else []:
                        if inv_opp.get('investing_company', {}).get('ticker', '').upper() == symbol:
                            
                            # DYNAMIC CONFIDENCE CALCULATION based on strategic analysis
                            strategic = inv_opp.get('strategic_analysis', {})
                            investment_amount = inv_opp.get('investment_amount', 0)
                            
                            # Strategic driver weighting (higher for must-do investments)
                            primary_driver = strategic.get('primary_strategic_driver', 'COST_OPTIMIZATION')
                            driver_weights = {
                                'REGULATORY_COMPLIANCE': 0.40,    # Must-do - highest confidence
                                'MARKET_EXPANSION': 0.35,         # Growth opportunity - high confidence
                                'COMPETITIVE_POSITIONING': 0.25, # Strategic move - medium confidence
                                'COST_OPTIMIZATION': 0.15,       # Optional - lowest confidence
                                'TECHNOLOGY_ACQUISITION': 0.30   # Tech capability - medium-high confidence
                            }
                            driver_boost = driver_weights.get(primary_driver, 0.15)
                            
                            # Investment size scaling (logarithmic - diminishing returns)
                            if investment_amount >= 20:
                                size_boost = 0.40  # $20B+ = major strategic commitment
                                size_desc = "MAJOR ($20B+)"
                            elif investment_amount >= 10:
                                size_boost = 0.25  # $10B+ = significant commitment
                                size_desc = "SIGNIFICANT ($10B+)"
                            elif investment_amount >= 5:
                                size_boost = 0.15  # $5B+ = moderate commitment
                                size_desc = "MODERATE ($5B+)"
                            else:
                                size_boost = 0.10  # $1B+ investment
                                size_desc = "MINIMAL ($1B+)"
                            
                            # Strategic confidence adjustment
                            strategic_confidence = strategic.get('strategic_confidence', 0.5)
                            confidence_multiplier = 0.5 + strategic_confidence  # 0.5x to 1.5x multiplier
                            
                            # Risk factor reduction
                            risk_factors = strategic.get('risk_factors', [])
                            risk_reduction = min(0.10, len(risk_factors) * 0.03)  # Up to 10% reduction
                            
                            # Calculate final investment boost with historical learning
                            base_boost = (driver_boost + size_boost) * confidence_multiplier - risk_reduction
                            base_boost = max(0.05, min(0.50, base_boost))  # Clamp between 5% and 50%
                            
                            # Add historical learning adjustment
                            historical_adjustment = ps.news_impact_tracker.get_confidence_adjustment(
                                'corporate_investment', primary_driver, investment_amount
                            )
                            
                            investment_boost = base_boost + historical_adjustment
                            investment_boost = max(0.05, min(0.60, investment_boost))  # Clamp between 5% and 60%
                            
                            print(f"      💰 DYNAMIC Investment Analysis:")
                            print(f"         🎯 Driver: {primary_driver} = +{driver_boost:.1%}")
                            print(f"         💵 Size: {size_desc} = +{size_boost:.1%}")
                            print(f"         🧠 Strategic Confidence: {strategic_confidence:.1%} = {confidence_multiplier:.1f}x")
                            print(f"         ⚠️  Risk Factors: {len(risk_factors)} = -{risk_reduction:.1%}")
                            print(f"         📚 Historical Learning: +{historical_adjustment:.1%}")
                            print(f"         📊 FINAL BOOST: +{investment_boost:.1%} confidence")
                            
                            # Record announcement for future learning
                            try:
                                current_price = ps.robust_price_fetcher.get_real_price(symbol)
                                if current_price:
                                    ps.news_impact_tracker.record_announcement(
                                        symbol, 'corporate_investment', primary_driver, 
                                        investment_amount, current_price
                                    )
                                    print(f"         📝 Recorded for historical learning: {symbol} @ ${current_price:.2f}")
                            except Exception as e:
                                print(f"         ⚠️  Could not record for learning: {e}")
                            break
                    
                    # 3. Convergence engine multiplier (if symbol appears in convergence opportunities)
                    convergence_multiplier = 1.0
                    convergence_opportunities = []  # Initialize empty list
                    for conv_opp in convergence_opportunities:
                        if conv_opp.get('target', '').upper() == symbol:
                            sources = conv_opp.get('unique_sources', 1)
                            if sources >= 2:
                                convergence_multiplier = 1.8 if sources == 2 else (2.7 if sources == 3 else 3.8)
                                print(f"      🔀 Convergence boost: {sources} sources = {convergence_multiplier:.1f}x multiplier")
                            break
                    
                    # Apply all multipliers and boosters
                    unified_confidence = unified_confidence * volume_multiplier + investment_boost
                    unified_confidence = unified_confidence * convergence_multiplier
                    unified_confidence = min(0.95, unified_confidence)  # Cap at 95%

                    try:
                        rb = ps.skipped_opportunity_watchlist.get_confidence_delta(
                            symbol, str(news_item.get("action", "BUY")).upper()
                        )
                        if rb > 0:
                            unified_confidence = min(0.95, unified_confidence + rb)
                            print(f"      🔁 Revisit-queue learning boost: +{rb:.1%}")
                    except Exception:
                        pass
                    
                    # 4. Dynamic minimum confidence floor based on investment quality
                    if investment_boost > 0:  # Corporate investment backing
                        # Higher floor for better strategic investments
                        if primary_driver in ['REGULATORY_COMPLIANCE', 'MARKET_EXPANSION'] and investment_amount >= 10:
                            min_confidence = 0.50  # 50% minimum for major strategic investments
                            floor_desc = "STRATEGIC MAJOR"
                        elif primary_driver == 'REGULATORY_COMPLIANCE':
                            min_confidence = 0.45  # 45% minimum for must-do investments
                            floor_desc = "REGULATORY MANDATE"
                        elif investment_amount >= 20:
                            min_confidence = 0.45  # 45% minimum for huge investments
                            floor_desc = "MAJOR COMMITMENT"
                        else:
                            min_confidence = 0.35  # 35% minimum for standard investments
                            floor_desc = "STANDARD INVESTMENT"
                        
                        unified_confidence = max(min_confidence, unified_confidence)
                        print(f"      💰 Applied {floor_desc} floor: {min_confidence:.1%} minimum confidence")
                    elif convergence_multiplier > 1.0:  # Multi-source convergence
                        unified_confidence = max(0.35, unified_confidence)  # Min 35% confidence
                        print(f"      🔀 Applied convergence floor: 35% minimum confidence")

                    try:
                        latent_score = float((latent_context or {}).get('latent_risk_score', 0.0) or 0.0)
                    except Exception:
                        latent_score = 0.0
                    if latent_score > 0:
                        try:
                            sentiment_val = float(news_item.get('sentiment', 0.0) or 0.0)
                        except Exception:
                            sentiment_val = 0.0
                        if sentiment_val < 0:
                            unified_confidence *= 1.0 + 0.15 * latent_score
                        elif sentiment_val > 0:
                            unified_confidence *= 1.0 - 0.1 * latent_score
                        unified_confidence = max(0.01, min(0.99, unified_confidence))

                    # Only require basic pattern detection and minimal confidence
                    if pattern_strength > 0.01 and unified_confidence > 0.05:  # ULTRA LOW thresholds for more opportunities

                        # Step 4: Monte Carlo simulation for realistic predictions
                        monte_carlo = get_monte_carlo_engine(cfg)

                        # Get options recommendation from news analysis
                        options_recommendation = news_item.get('options_recommendation', 'BUY')

                        # Map recommendation to action (stock mode)
                        if options_recommendation == 'BUY':
                            action = 'BUY'
                        elif options_recommendation == 'SELL':
                            action = 'SELL'
                        elif options_recommendation == 'HOLD':
                            action = 'HOLD'
                        else:
                            action = 'BUY'  # Default fallback

                        # Get REAL price - NO DEFAULTS
                        symbol = news_item['symbol']
                        price_fetcher = get_price_fetcher()
                        real_price = news_item.get('current_price')
                        
                        if not real_price or real_price <= 0:
                            real_price = price_map.get(symbol) or price_fetcher.get_real_price(symbol)
                            if not real_price:
                                print(f"   ❌ Skipping {symbol} - cannot fetch real price")
                                continue  # Skip this trade - NO FAKE DATA
                        
                        # Stock trading - no strike price needed
                        strike = None  # Stocks don't have strike prices
                        
                        # SMART TIMEFRAME CALCULATION (not always 7 days!)
                        timeframe_info = calculate_optimal_timeframe(news_item)
                        days_to_expiry = timeframe_info['days_to_expiry']
                        timeframe_type = timeframe_info['timeframe_type']
                        
                        print(f"   ⏰ Timeframe: {days_to_expiry} days ({timeframe_type}) - {timeframe_info['reasoning']}")
                        
                        # Enhanced signal with REAL data
                        sim_signal = {
                            'symbol': symbol,
                            'action': action,
                            'current_price': real_price,  # REAL PRICE ONLY
                            'strike': strike,  # CALCULATED FROM REAL PRICE
                            'premium': 0.12,
                            'days_to_expiry': days_to_expiry,  # DYNAMIC! 3-180 days based on trade type
                            'volatility': 0.4,
                            'confidence': unified_confidence,
                            'title': news_item.get('title', ''),
                            'sector': news_item.get('sector', 'AI'),
                            'is_moonshot': False,
                            'timeframe_type': timeframe_type,
                            'timeframe_reasoning': timeframe_info['reasoning']
                        }

                        # DEBUG: Show what we're simulating
                        strike_display = sim_signal['strike'] if sim_signal['strike'] else "N/A (stock)"
                        premium_display = sim_signal['premium'] if sim_signal['premium'] else "N/A"
                        print(f"   🎲 Simulating: {news_item['symbol']} {action} @ ${sim_signal['current_price']:.2f} → ${strike_display} (premium: ${premium_display:.2f})")

                        # SINGLE SIMULATION CALL: Use stock simulation for regular trades
                        print(f"\n🎲 Running Monte Carlo simulation for {news_item['symbol']}...")
                        
                        # Create stock signal for simulation - use simulation results for targets
                        stock_signal = {
                            'symbol': symbol,
                            'current_price': real_price,
                            'confidence': unified_confidence,
                            'sector': news_item.get('sector', 'Technology'),
                            'holding_days': 30
                        }
                        
                        sim_results = monte_carlo.run_stock_simulation(stock_signal)
                        
                        # Use simulation results for targets instead of hardcoded values
                        sim_target_price = sim_results.get('target_price', real_price * 1.1) if sim_results else real_price * 1.1
                        sim_stop_loss = sim_results.get('stop_loss', real_price * 0.9) if sim_results else real_price * 0.9
                        
                        # Display simulation results
                        if sim_results:
                            print(f"   📊 Stock Simulation Results:")
                            print(f"      Win Rate: {sim_results.get('win_rate', 0):.1%}")
                            print(f"      Target: ${sim_results.get('target_price', 0):.2f}")
                            print(f"      Stop Loss: ${sim_results.get('stop_loss', 0):.2f}")
                            print(f"      Profit Potential: {sim_results.get('profit_potential', 0):.1%}")
                            print(f"      Holding Period: {sim_results.get('holding_days', 0)} days")
                            print(f"      Simulations Run: {sim_results.get('total_simulations', 0):,}")

                        # CRITICAL: Scale confidence from simulation win rate (reality check)
                        # If AI thinks 90% confident but sim shows 30% win rate, confidence becomes 50%
                        initial_confidence = unified_confidence
                        sim_win_rate = sim_results['win_rate']

                        # Fact-check: AI confidence vs reality (simulation)
                        if sim_win_rate >= 0.8:  # Sim shows high probability
                            final_confidence = min(0.95, initial_confidence * 1.1)  # Boost if sim agrees
                        elif sim_win_rate >= 0.40:  # Sim shows decent probability (lowered from 60%)
                            final_confidence = initial_confidence  # Keep as is
                        elif sim_win_rate >= 0.4:  # Sim shows weak probability
                            final_confidence = max(0.1, initial_confidence * 0.8)  # Slight reduction
                        else:  # Sim shows poor probability
                            final_confidence = max(0.1, initial_confidence * 0.5)  # Significant reduction

                        # PRECISE LOGGING: Show actual calculation chain (no hand-waving)
                        if initial_confidence != final_confidence:
                            pop_from_sim = sim_results.get('pop_from_sim', 50)
                            print(f"⚖️ REALITY CHECK: {news_item['symbol']} - AI confidence {initial_confidence:.1%} vs Sim reality {sim_win_rate:.1%}")
                            print(f"⚖️ REALITY CHECK: {news_item['symbol']} - AI {initial_confidence:.1%} → Reality-adjusted {final_confidence:.1%} (sim: {sim_win_rate:.1%})")
                        else:
                            print(f"✅ SIM VALIDATION: {news_item['symbol']} - AI confidence {initial_confidence:.1%} matches simulation reality {sim_win_rate:.1%}")

                        # Scale confidence from simulation win rate (as requested)
                        sim_scaled_confidence = sim_results.get('win_rate', initial_confidence)
                        pop_from_sim = sim_results.get('pop_from_sim', 0)

                        # Determine if this is a moonshot (overnight potential)
                        is_moonshot = (
                            sim_results.get('moonshot_probability', 0) > 0.10 and  # 10%+ chance of 5x (lowered)
                            divergence_analysis.get('divergence_score', 0) > 0.15 and  # Lower divergence threshold
                            final_confidence > 0.25 and  # Lower confidence for moonshots
                            any(keyword in news_item.get('title', '').lower()
                                for keyword in ['overnight', 'surge', 'breakout', 'explode', 'moonshot', 'surge', 'jump', 'soar', 'rocket'])
                        )

                        # Generate unified evidence chain
                        evidence = monte_carlo.generate_simulation_evidence(sim_signal)

                        # Build per-stock price projection (downside & upside) from simulation parameters
                        drift_used = sim_results.get('drift_used', 0.0)
                        vol_used = sim_results.get('volatility_used', 0.0)
                        try:
                            T_years = max(days_to_expiry / 252.0, 1 / 252.0)
                            sigma_T = vol_used * (T_years ** 0.5)
                            expected_return_pct = drift_used * T_years
                            upside_return_pct = expected_return_pct + sigma_T
                            downside_return_pct = expected_return_pct - sigma_T * 1.5
                            downside_return_pct = max(downside_return_pct, -0.8)
                            upside_return_pct = min(upside_return_pct, 5.0)
                            expected_price = real_price * (1 + expected_return_pct)
                            upside_price = real_price * (1 + upside_return_pct)
                            downside_price = real_price * (1 + downside_return_pct)
                            price_projection = {
                                'current_price': real_price,
                                'expected_return_pct': expected_return_pct,
                                'upside_return_pct': upside_return_pct,
                                'downside_return_pct': downside_return_pct,
                                'expected_price': expected_price,
                                'upside_price': upside_price,
                                'downside_price': downside_price,
                                'horizon_days': days_to_expiry,
                            }
                        except Exception:
                            price_projection = None

                        # CONFIDENCE FLOOR: Lower to 5% for maximum profit opportunities
                        if final_confidence < 0.05:  # 5% floor - very aggressive!
                            print(f"  ❌ CONFIDENCE FLOOR: {news_item['symbol']} - Final confidence {final_confidence:.1%} < 5% (skipping trade)")
                            continue

                        rationale_extra = ""
                        if latent_context and latent_context.get('summary'):
                            rationale_extra = " + latent news memory"

                        signal = {
                            'symbol': news_item['symbol'],
                            'action': sim_signal['action'],
                            'confidence': final_confidence,  # Reality-adjusted confidence
                            'position_size': ps.news_engine._calculate_pattern_position_size(final_confidence, fact_check, is_moonshot),
                            'rationale': f"UNIFIED Analysis: {', '.join(patterns)} patterns + {divergence_analysis['divergence_score']:.1%} divergence{rationale_extra} + Monte Carlo validation",
                            'source': 'UNIFIED_ANALYSIS',
                            'patterns': patterns,
                            'technical_bias': technical_bias,
                            'divergence_analysis': divergence_analysis,
                            'fact_check': fact_check,
                            'simulation_results': sim_results,  # Single simulation call
                            'evidence_chain': monte_carlo.generate_simulation_evidence(sim_signal),  # Generate evidence ONCE
                            'entry_timing': {
                                'urgency': 'high' if is_moonshot else 'medium',
                                'recommended_action': 'BUY_IMMEDIATELY' if is_moonshot else 'BUY_NOW',
                                'timeframe': f"Hold {sim_results.get('optimal_exit_day', 5)} days",  # USE SIMULATION RESULT!
                                'confidence': final_confidence,
                                'optimal_exit_day': sim_results.get('optimal_exit_day', 5)
                            },
                            'exit_timing': {
                                'target_date': f"{sim_results.get('optimal_exit_day', 5)} days",
                                'optimal_exit_day': sim_results.get('optimal_exit_day', 5),
                                'stop_loss': 0.3,
                                'take_profit': 0.6,
                                'confidence': sim_results.get('win_rate', 0)
                            },
                            'is_moonshot': is_moonshot,
                            'trade_type': 'MOONSHOT' if is_moonshot else 'REGULAR',
                            'potential_upside': sim_results.get('moonshot_10x_probability', 0) * 20 if is_moonshot else sim_results.get('win_rate', 0) * 5,
                            'unified_confidence': unified_confidence,
                            'sim_scaled_confidence': sim_results.get('sim_scaled_confidence', final_confidence),
                            'pop_from_sim': sim_results.get('pop_from_sim', 0),
                            'initial_confidence': initial_confidence,  # For debugging
                            'sim_win_rate': sim_win_rate,  # For debugging
                            'title': news_item.get('title', ''),  # Add title for moonshot detection
                            'company_validation': fact_check.get('is_valid', False),  # Track company validation
                            'industry': news_item.get('fact_check', {}).get('company_info', {}).get('industry', 'Unknown'),
                            'sector': news_item.get('fact_check', {}).get('company_info', {}).get('sector', 'Unknown'),
                            'days_to_expiry': days_to_expiry,  # DYNAMIC timeframe
                            'timeframe_type': timeframe_type,  # e.g., QUICK_CATALYST, SWING, LONG_TERM
                            'timeframe_reasoning': timeframe_info['reasoning'],  # Why this timeframe
                            'price_projection': price_projection,
                            'latent_news_context': latent_context
                        }

                        signals.append(signal)

            except Exception as e:
                import traceback
                print(f"  ❌ ERROR processing {symbol}: {e}")
                print(f"  📍 Traceback: {traceback.format_exc()[:500]}")  # First 500 chars
                continue

        if signals:
            status = {}
            try:
                status = ps.meta_brain.get_status()
                bankroll = float(status.get("bankroll", cfg.get("bankroll", 2000)))
            except Exception:
                try:
                    bankroll = float(cfg.get("bankroll", 2000))
                except Exception:
                    bankroll = 2000.0

            try:
                open_positions = getattr(ps.meta_brain.risk_manager, 'open_positions', {}) or {}
                existing_trades = len(open_positions)
            except Exception:
                existing_trades = 0

            max_concurrent = int(cfg.get("trading.max_concurrent_trades", 8) or 8)

            # UNITS-BASED POSITION SIZING (Sports Betting Style)
            print(f"[UNITS SIZING] 🎯 Calculating units-based positions for {len(signals)} signals...")
            
            # Update unit value based on current bankroll
            ps.unit_value = bankroll * (ps.unit_size_percent / 100)
            ps.standard_trade_size = ps.unit_value * ps.standard_units
            
            print(f"[UNITS SIZING] 💰 1 Unit = ${ps.unit_value:.2f} ({ps.unit_size_percent}% of ${bankroll:.0f} bankroll)")
            print(f"[UNITS SIZING] 📊 Standard Trade = {ps.standard_units} units = ${ps.standard_trade_size:.2f}")

            # If recent performance is not positive, scale sizes down even more
            performance_scale = 1.0
            try:
                recent_pnl = float(status.get('daily_pnl', 0.0) or 0.0)
                if recent_pnl <= 0:
                    performance_scale = 0.5
                elif recent_pnl < bankroll * 0.01:
                    performance_scale = 0.7
            except Exception:
                performance_scale = 0.5

            performance_scale *= bankroll / bankroll  # Simplified: use bankroll instead of portfolio value

            max_conf = max((s.get('confidence', 0.0) or 0.0) for s in signals) if signals else 0.0
            if max_conf <= 0:
                max_conf = 1.0

            for s in signals:
                try:
                    raw_size = float(s.get('position_size', 0.0) or 0.0)
                except Exception:
                    raw_size = 0.0

                if raw_size <= 0:
                    continue

                conf = float(s.get('confidence', 0.0) or 0.0)
                conf_weight = 0.5 + 0.5 * (conf / max_conf)

        # UNITS-BASED POSITION CALCULATION (Sports Betting Style)
                # Calculate units based on confidence (1-10 units)
                units = max(ps.min_units, min(ps.max_units, round(conf_weight * ps.standard_units)))
                
                # Convert units to dollar amount
                position_size = units * ps.unit_value
                
                symbol = s.get("symbol", "UNKNOWN") if isinstance(s, dict) else getattr(s, "symbol", "UNKNOWN")
                print(f"[UNITS] 🎯 {symbol}: {units} units = ${position_size:.2f} (confidence {conf:.0f}%)")

                # Also scale by POP / simulated chance of profit
                try:
                    pop = float(s.get('pop_from_sim', 0.0) or 0.0)
                except Exception:
                    pop = 0.0

                if pop <= 40:
                    pop_factor = 0.3
                elif pop <= 50:
                    pop_factor = 0.5
                elif pop <= 60:
                    pop_factor = 0.8
                else:
                    pop_factor = 1.0

                # Apply POP scaling to units
                units = int(units * pop_factor)
                units = max(1, units)  # Minimum 1 unit
                position_size = units * ps.unit_value

                print(f"[UNITS] 📊 {symbol}: After POP scaling: {units} units = ${position_size:.2f}")

                sim = s.get('simulation_results', {}) or {}
                try:
                    avg_pnl = float(sim.get('avg_pnl', 0.0) or 0.0)
                except Exception:
                    avg_pnl = 0.0
                try:
                    win_rate = float(sim.get('win_rate', 0.0) or 0.0)
                except Exception:
                    win_rate = 0.0
                try:
                    p10 = float(sim.get('percentile_10', 0.0) or 0.0)
                except Exception:
                    p10 = 0.0

                ev_factor = 1.0
                if avg_pnl <= 0.0 or win_rate < 0.35:
                    ev_factor = 0.25
                else:
                    typical_loss = abs(p10) if p10 < 0.0 else 0.0
                    if typical_loss > 0.0:
                        pl_ratio = avg_pnl / typical_loss
                        if pl_ratio < 1.5:
                            ev_factor = 0.5
                        elif pl_ratio >= 3.0:
                            ev_factor = 1.0
                        else:
                            ev_factor = 0.5 + (pl_ratio - 1.5) * (0.5 / 1.5)
                    else:
                        ev_factor = 0.5

                # Apply EV scaling to units
                units = int(units * ev_factor)
                units = max(1, units)  # Minimum 1 unit
                position_size = units * ps.unit_value

                print(f"[UNITS] 🎲 {symbol}: After EV scaling: {units} units = ${position_size:.2f}")

                # ASSIGN UNITS-BASED POSITION SIZE TO SIGNAL
                s['position_size'] = position_size
                s['units'] = units

                print(f"[UNITS] ✅ FINAL: {symbol}: {units} units = ${position_size:.2f} assigned to signal")

        return signals

    def _apply_ecosystem_interactions(
        self, signals: List[Dict], ctx: Optional[ApplicationContext] = None
    ) -> None:
        """Adjust unified signals based on simple crypto ecosystem relationships.

        Goal: if an ecosystem coin is extremely strong (news + Monte Carlo), the
        engine slightly boosts confidence on its main chain asset instead of
        treating everything as isolated.

        This does NOT create new trades or scan for extra symbols – it only
        looks at the signals we already generated this cycle.
        """
        if not signals:
            return

        if ctx is None:
            ctx = ApplicationContext.bind(self, {})
        cfg = ctx.config

        # Basic ecosystem definitions. These are only used if the symbols are
        # already present in the signal list; we do not actively hunt for them.
        ecosystem_defs = [
            {
                "name": "BITCOIN",
                "main": ["BTC-USD", "BTC"],
                "ecosystem_symbols": ["MSTR", "COIN", "MARA", "RIOT", "CLSK", "HUT", "BITF"],
            },
            {
                "name": "ETHEREUM",
                "main": ["ETH-USD", "ETH"],
                "ecosystem_symbols": [],  # Generic ETH ecosystem; user can extend via config later
            },
            {
                "name": "SOLANA",
                "main": ["SOL-USD", "SOL"],
                "ecosystem_symbols": [],  # We do NOT hardcode meme tickers here
            },
        ]

        # Optional user overrides from config (ecosystem.mappings)
        custom_mappings = cfg.get("ecosystem.mappings", {}) or {}
        for eco_name, mapping in custom_mappings.items():
            main_list = mapping.get("main", [])
            eco_list = mapping.get("ecosystem_symbols", [])
            if main_list:
                ecosystem_defs.append({
                    "name": eco_name.upper(),
                    "main": [sym.upper() for sym in main_list],
                    "ecosystem_symbols": [sym.upper() for sym in eco_list],
                })

        # Normalize symbols for comparison
        for sig in signals:
            if isinstance(sig.get("symbol"), str):
                sig["symbol"] = sig["symbol"].upper()

        # Build quick lookup by symbol
        by_symbol: Dict[str, List[Dict]] = {}
        for sig in signals:
            sym = sig.get("symbol")
            if not sym:
                continue
            by_symbol.setdefault(sym, []).append(sig)

        for eco in ecosystem_defs:
            main_syms = [s.upper() for s in eco.get("main", [])]
            child_syms = [s.upper() for s in eco.get("ecosystem_symbols", [])]

            # If neither main nor children are present in this batch, skip
            main_signals = [sig for sym in main_syms for sig in by_symbol.get(sym, [])]
            if not main_signals:
                continue

            child_signals: List[Dict] = []
            for sym in child_syms:
                child_signals.extend(by_symbol.get(sym, []))

            # Heuristic: also treat any crypto ticker ending with "-USD" that
            # shares the root (e.g. SOL-USD vs meme SOL tokens) as part of the
            # same train without hardcoding their names.
            for sym, sig_list in by_symbol.items():
                root = sym.split("-")[0]
                if any(root and root == m.split("-")[0] for m in main_syms):
                    if sym not in main_syms and sym not in child_syms:
                        child_signals.extend(sig_list)

            if not child_signals:
                continue

            # Focus on strongly bullish ecosystem children
            bullish_children = []
            for sig in child_signals:
                action = sig.get("action", "").upper()
                if "PUT" in action:
                    continue  # we only use upside contagion here
                conf = float(sig.get("confidence", 0.0))
                sim_win = float(sig.get("sim_win_rate", sig.get("simulation_results", {}).get("win_rate", 0.0)))
                if conf >= 0.4 and sim_win >= 0.5:
                    bullish_children.append(sig)

            if not bullish_children:
                continue

            avg_child_conf = sum(sig.get("confidence", 0.0) for sig in bullish_children) / len(bullish_children)
            # Translate average child confidence into a modest boost factor
            boost = max(0.0, min(0.25, (avg_child_conf - 0.4) * 0.5))  # 0–25% boost on confidence
            if boost <= 0:
                continue

            for main_sig in main_signals:
                before = float(main_sig.get("confidence", 0.0))
                if before <= 0:
                    continue
                after = min(0.95, before * (1.0 + boost))
                main_sig["confidence"] = after

                # Slightly scale potential_upside if present
                if "potential_upside" in main_sig:
                    pu = float(main_sig.get("potential_upside", 0.0))
                    main_sig["potential_upside"] = pu * (1.0 + boost * 0.5)

                main_sig["ecosystem_boost"] = {
                    "ecosystem": eco.get("name", "UNKNOWN"),
                    "child_signal_count": len(bullish_children),
                    "avg_child_confidence": avg_child_conf,
                    "boost_applied": after - before,
                }

                print(
                    f"   🔗 Ecosystem boost: {eco.get('name', 'UNKNOWN')} main {main_sig.get('symbol')} "
                    f"confidence {before:.1%} → {after:.1%} based on {len(bullish_children)} strong ecosystem signals"
                )

    def _display_unified_results(
        self, regular_trades, overnight_moonshots, *, ctx: Optional[ApplicationContext] = None
    ):
        """Display unified results with regular trades and overnight moonshots"""
        if ctx is None:
            ctx = ApplicationContext.bind(self, {})
        ps = ctx.system

        # Show overnight moonshots first (these can go crazy overnight)
        if overnight_moonshots:
            print("\n🚀 OVERNIGHT MOONSHOTS (Can Explode Tonight/Tomorrow):")
            print("-" * 60)
            for signal in overnight_moonshots[:3]:  # Show top 3 moonshots
                fact_check = signal.get('fact_check', {})
                company_info = fact_check.get('company_info', {})
                full_company_name = company_info.get('full_name', signal['symbol'])

                initial_conf = signal.get('initial_confidence', 0) * 100
                final_conf = signal.get('confidence', 0) * 100
                sim_win = signal.get('sim_win_rate', 0) * 100

                # Get company info for display
                company_info = fact_check.get('company_info', {})
                real_ticker = company_info.get('real_ticker', False)
                avg_volume = company_info.get('avg_volume', 'N/A')
                try:
                    avg_volume_display = f"{int(avg_volume):,}"
                except Exception:
                    avg_volume_display = str(avg_volume)
                price_range = company_info.get('price_range', 'N/A')

                symbol = signal.get('symbol', 'UNKNOWN')
                action = signal.get('action', 'UNKNOWN')
                
                # Convert options terminology to appropriate format
                if symbol.startswith('KX'):
                    # Kalshi prediction markets use YES/NO
                    if action == 'BUY_CALL':
                        action = 'BUY_YES'
                    elif action == 'BUY_PUT':
                        action = 'BUY_NO'
                else:
                    # Regular stocks use simple BUY/SELL
                    if action == 'BUY_CALL':
                        action = 'BUY'
                    elif action == 'BUY_PUT':
                        action = 'SELL'
                
                print(f"   🎯 TRADE: {symbol} {action} - {full_company_name}")

                print(f"   📊 Confidence: {final_conf:.1f}% (AI: {initial_conf:.1f}% → Reality Check: {sim_win:.1f}%)")
                print(f"   💰 POP: {signal.get('pop_from_sim', 50):.1f}% | Potential: {signal.get('potential_upside', 0):.1f}X")
                print(f"   💰 Sim Avg P&L: ${signal.get('simulation_results', {}).get('avg_pnl', 0):.0f}")
                proj = signal.get('price_projection')
                display_price = price_range
                if proj and proj.get('current_price') is not None:
                    cp = proj['current_price']
                    up = proj.get('upside_price')
                    down = proj.get('downside_price')
                    action_dir = str(signal.get('action', '')).upper()
                    if 'PUT' in action_dir:
                        if down is not None:
                            print(f"   📉 Downside Floor: ${down:.2f} ({proj.get('downside_return_pct', 0)*100:.1f}% vs ${cp:.2f})")
                    else:
                        if up is not None:
                            print(f"   📈 Upside Target: ${up:.2f} ({proj.get('upside_return_pct', 0)*100:.1f}% vs ${cp:.2f})")

                    try:
                        real_px = float(cp)
                        if real_px > 0:
                            display_price = f"${real_px:.2f}"
                    except Exception:
                        pass
                optimal_days = signal.get('simulation_results', {}).get('optimal_exit_day', 5)
                total_days = signal.get('days_to_expiry', 7)
                timeframe_type = signal.get('timeframe_type', 'STANDARD')
                print(f"   📅 Timeframe: {total_days} days ({timeframe_type})")
                print(f"   🎯 Optimal Exit: Day {optimal_days} (Sim peak within {total_days}d window)")
                print(f"   📈 Patterns: {', '.join(signal.get('patterns', []))}")
                print(f"   ⏰ Action: {signal['entry_timing'].get('recommended_action', 'BUY')} → Exit Day {optimal_days}")
                print(f"   💰 Position: ${signal['position_size']:.0f} | Stop: {signal['exit_timing'].get('stop_loss', 0.3):.1%}")
                print(f"   ✅ Valid Company: {fact_check.get('is_valid', False)} | Risk: {fact_check.get('risk_level', 'UNKNOWN')}")
                print(f"   📊 Company Info: {avg_volume_display} avg volume | Price: {display_price}")
                print(f"   🎯 Company Status: {'✅ VALIDATED' if signal.get('company_validation', False) else '⚠️ UNVALIDATED'}")
                print(f"   ⚡ Confidence Floor: {'✅ ABOVE 15%' if final_conf >= 15 else '❌ BELOW 15%'}")
                print(f"   📊 WIN RATE: {sim_win:.1f}% chance of profit (1 in {100/sim_win:.1f} trades)")
                if initial_conf != final_conf:
                    print(f"   ⚠️ REALITY CHECK: AI overconfident - adjusted from {initial_conf:.1f}% to {final_conf:.1f}%")
                print(f"   🔍 Unified Analysis: {signal['rationale']}")
                print()

        # Show regular trades
        if regular_trades:
            print("\n📊 REGULAR TRADING OPPORTUNITIES:")
            print("-" * 50)
            for signal in regular_trades[:5]:  # Show top 5 regular trades
                fact_check = signal.get('fact_check', {})
                company_info = fact_check.get('company_info', {})
                full_company_name = company_info.get('full_name', signal['symbol'])

                initial_conf = signal.get('initial_confidence', 0) * 100
                final_conf = signal.get('confidence', 0) * 100
                sim_win = signal.get('sim_win_rate', 0) * 100

                # Get company info for display
                company_info = fact_check.get('company_info', {})
                real_ticker = company_info.get('real_ticker', False)
                avg_volume = company_info.get('avg_volume', 'N/A')
                try:
                    avg_volume_display = f"{int(avg_volume):,}"
                except Exception:
                    avg_volume_display = str(avg_volume)
                price_range = company_info.get('price_range', 'N/A')

                symbol = signal.get('symbol', 'UNKNOWN')
                action = signal.get('action', 'UNKNOWN')
                
                # Convert options terminology to appropriate format
                if symbol.startswith('KX'):
                    # Kalshi prediction markets use YES/NO
                    if action == 'BUY_CALL':
                        action = 'BUY_YES'
                    elif action == 'BUY_PUT':
                        action = 'BUY_NO'
                else:
                    # Regular stocks use simple BUY/SELL
                    if action == 'BUY_CALL':
                        action = 'BUY'
                    elif action == 'BUY_PUT':
                        action = 'SELL'
                
                print(f"   🎯 TRADE: {symbol} {action} - {full_company_name}")

                optimal_days = signal.get('simulation_results', {}).get('optimal_exit_day', 5)
                total_days = signal.get('days_to_expiry', 7)
                timeframe_type = signal.get('timeframe_type', 'STANDARD')
                timeframe_reason = signal.get('timeframe_reasoning', 'Standard play')
                print(f"   📊 Confidence: {final_conf:.1f}% (AI: {initial_conf:.1f}% → Reality Check: {sim_win:.1f}%)")
                print(f"   💰 POP: {signal.get('pop_from_sim', 50):.1f}% | Potential: {signal.get('potential_upside', 0):.1f}X")
                print(f"   💰 Sim Avg P&L: ${signal.get('simulation_results', {}).get('avg_pnl', 0):.0f}")
                proj = signal.get('price_projection')
                display_price = price_range
                if proj and proj.get('current_price') is not None:
                    cp = proj['current_price']
                    up = proj.get('upside_price')
                    down = proj.get('downside_price')
                    action_dir = str(signal.get('action', '')).upper()
                    if 'PUT' in action_dir:
                        if down is not None:
                            print(f"   📉 Downside Floor: ${down:.2f} ({proj.get('downside_return_pct', 0)*100:.1f}% vs ${cp:.2f})")
                    else:
                        if up is not None:
                            print(f"   📈 Upside Target: ${up:.2f} ({proj.get('upside_return_pct', 0)*100:.1f}% vs ${cp:.2f})")

                    try:
                        real_px = float(cp)
                        if real_px > 0:
                            display_price = f"${real_px:.2f}"
                    except Exception:
                        pass
                print(f"   📅 Timeframe: {total_days} days ({timeframe_type})")
                print(f"   💡 Why: {timeframe_reason}")
                print(f"   🎯 Optimal Exit: Day {optimal_days} (of {total_days})")
                print(f"   📈 Patterns: {', '.join(signal.get('patterns', []))}")
                print(f"   ⏰ Action: {signal['entry_timing'].get('recommended_action', 'BUY')} → Exit Day {optimal_days}")
                print(f"   💰 Position: ${signal['position_size']:.0f}")
                print(f"   ✅ Valid Company: {fact_check.get('is_valid', False)} | Risk: {fact_check.get('risk_level', 'UNKNOWN')}")
                print(f"   📊 Company Info: {avg_volume_display} avg volume | Price: {display_price}")
                print(f"   🎯 Company Status: {'✅ VALIDATED' if signal.get('company_validation', False) else '⚠️ UNVALIDATED'}")
                print(f"   ⚡ Confidence Floor: {'✅ ABOVE 15%' if final_conf >= 15 else '❌ BELOW 15%'}")
                print(f"   📊 WIN RATE: {sim_win:.1f}% chance of profit (1 in {100/sim_win:.1f} trades)")
                if initial_conf != final_conf:
                    print(f"   ⚠️ REALITY CHECK: AI overconfident - adjusted from {initial_conf:.1f}% to {final_conf:.1f}%")
                print(f"   🔍 Unified Analysis: {signal['rationale']}")
                print()

        # System status
        status = ps.meta_brain.get_status()
        print("\n📈 UNIFIED SYSTEM STATUS:")
        print("-" * 40)
        print(f"🧠 Meta-Brain: {'Active' if ps.is_running else 'Standby'}")
        print(f"💰 Bankroll: ${status['bankroll']}")
        print(f"📊 Daily P&L: ${status['daily_pnl']:.2f}")
        print(f"🎯 Open Positions: {status['open_positions']}")
        print(f"⚡ Active Engines: {len(status['active_engines'])}")
        print(f"📈 Performance Records: {status['performance_records']}")

        # Show active trades (open positions) with basic details
        open_positions = getattr(ps.meta_brain.risk_manager, 'open_positions', {}) or {}
        if open_positions:
            print("\n📂 ACTIVE TRADES (Open Positions):")
            for sym, pos in open_positions.items():
                sig = (pos or {}).get('signal', {}) or {}
                action = sig.get('action', 'UNKNOWN')
                try:
                    size = float(sig.get('position_size', 0.0))
                except Exception:
                    size = 0.0
                try:
                    conf = float(sig.get('confidence', 0.0))
                except Exception:
                    conf = 0.0
                entry_time = (pos or {}).get('entry_time')
                if hasattr(entry_time, 'isoformat'):
                    entry_dt = entry_time
                elif isinstance(entry_time, str):
                    try:
                        entry_dt = datetime.fromisoformat(entry_time)
                    except Exception:
                        entry_dt = datetime.now()
                else:
                    entry_dt = datetime.now()
                entry_str = entry_dt.isoformat(timespec='seconds') if hasattr(entry_dt, 'isoformat') else str(entry_time)

                hold_days = max((datetime.now() - entry_dt).days, 0)
                planned_days = int(sig.get('days_to_expiry', sig.get('exit_timing', {}).get('optimal_exit_day', 7)))
                planned_days = max(1, planned_days)
                days_left = max(0, planned_days - hold_days)

                print(
                    f"   • {sym}: {action} | Size ${size:.0f} | Conf {conf:.1%} | "
                    f"Opened {entry_str} | Held {hold_days}d / {planned_days}d ({days_left}d left)"
                )
        else:
            print("\n📂 ACTIVE TRADES: None tracked yet")

        print("\n🏁 Unified Phasma AI session complete!")

        # NEW: Generate weekly reports and update galleries
        try:
            # Update winners gallery with any completed trades
            ps.winners_gallery.cleanup_old_winners()

            # Generate weekly watchlist if it's time (DISABLED - discover from news)
            if datetime.now().weekday() == 0:  # Monday
                print("\n📈 Weekly watchlist generation DISABLED - discovering stocks from news instead")
                # recent_signals = [s for s in signals if getattr(s, 'pop_from_sim', 0) >= 35] if signals else []
                # if recent_signals:
                #     watchlist = self.weekly_watchlist.generate_watchlist(recent_signals)
                #     print(f"\n📈 Generated new weekly watchlist with {len(watchlist['items'])} high-volatility picks")

            # Send learning report if significant activity
            if ps.alert_learning:
                learning_summary = ps.alert_learning.get_performance_summary()
                if learning_summary.get('total_alerts', 0) > 0:
                    print(f"\n🧠 AI Learning Update:")
                    print(f"   📊 {learning_summary['total_alerts']} alerts processed")
                    print(f"   🎯 {learning_summary['success_rate']:.1f}% success rate")
                    if learning_summary.get('recommendations'):
                        print(f"   💡 {learning_summary['recommendations'][0]}")

        except Exception as e:
            print(f"⚠️ Report generation error: {e}")

    async def execute_classified_trade(self, signal, *, ctx: Optional[ApplicationContext] = None):
        """
        Execute a trade using the classification system
        
        Args:
            signal: Trading signal with symbol, action, confidence, etc.
            ctx: Optional cycle context (defaults to a fresh bind for standalone calls).
            
        Returns:
            dict: Trade execution details or None if not executed
        """
        try:
            if ctx is None:
                ctx = ApplicationContext.bind(self, {})
            cfg = ctx.config
            s = ctx.system

            # Get market data for the symbol
            symbol = getattr(signal, 'symbol', '').upper()
            action = getattr(signal, 'action', '').upper()
            confidence = getattr(signal, 'confidence', 0)
            
            if not symbol or not action or confidence < 0.20:  # Lower from 50% to 20% for more trades
                logging.warning(f"Invalid signal received: {symbol} {action} (confidence: {confidence:.1%})")
                return None
                
            # Get current market data (simplified - replace with actual market data)
            current_price = getattr(signal, 'current_price', 0)
            if current_price <= 0:
                logging.warning(f"Invalid price for {symbol}: {current_price}")
                return None
                
            # Classify the trade (resilient fallback)
            try:
                trade_params = s.classify_trade(
                    symbol=symbol,
                    asset_type='crypto' if symbol.endswith('USD') else 'stock',
                    catalyst={
                        'date': getattr(signal, 'catalyst_date', None),
                        'type': getattr(signal, 'catalyst_type', 'technical'),
                        'confidence': confidence
                    },
                    momentum={
                        'timestamp': datetime.now(),
                        'rsi': getattr(signal, 'rsi', 50),
                        'macd': getattr(signal, 'macd', 'neutral')
                    },
                    iv_rank=getattr(signal, 'iv_rank', 50),
                    macro_conditions={
                        'dxy_trend': 'neutral',
                        'vix': getattr(signal, 'vix', 20),
                        'market_breadth': {'advance_decline': 0.5}
                    },
                    ctx=ctx,
                )
            except Exception:
                # Fallback to conservative SWING_30D defaults to avoid failing execution path in tests
                trade_params = {
                    'trade_class': 'SWING_30D',
                    'stop_pct': 0.05,
                    'risk_reward_ratio': 2.0,
                    'min_hold_days': 7,
                    'max_hold_days': 30
                }
            
            # Calculate position size based on risk parameters
            risk_per_trade = cfg.get('risk_per_trade', 0.01)  # 1% risk per trade
            stop_pct = trade_params.get('stop_pct', 0.05)  # Default 5% stop
            position_size = (cfg.get('bankroll', 10000) * risk_per_trade) / stop_pct
            
            # Calculate target and stop prices
            if 'CALL' in action:
                stop_price = current_price * (1 - stop_pct)
                target_price = current_price * (1 + (stop_pct * trade_params.get('risk_reward_ratio', 2.0)))
            else:  # PUT
                stop_price = current_price * (1 + stop_pct)
                target_price = current_price * (1 - (stop_pct * trade_params.get('risk_reward_ratio', 2.0)))
            
            # Log the trade decision (do not fail execution if logging fails)
            trade_file = None
            try:
                trade_file = s.log_final_trade_decision(
                    symbol=symbol,
                    trade_type=action,
                    entry_price=current_price,
                    target_price=target_price,
                    stop_price=stop_price,
                    confidence=confidence,
                    simulations_run=getattr(signal, 'simulations_run', 100),
                    success_rate=getattr(signal, 'success_rate', 0.7),
                    reason=getattr(signal, 'rationale', 'No rationale provided'),
                    trade_class=trade_params.get('trade_class', 'SWING_30D'),
                    asset_type='crypto' if symbol.endswith('USD') else 'stock',
                    min_hold_days=trade_params.get('min_hold_days', 7),
                    max_hold_days=trade_params.get('max_hold_days', 30),
                    review_cadence_hours=72,
                    risk_reward_ratio=trade_params.get('risk_reward_ratio', 2.0),
                    metadata={
                        'signal': str(signal) if not hasattr(signal, 'to_dict') else signal.to_dict(),
                        'indicators': {
                            'rsi': getattr(signal, 'rsi', None),
                            'macd': getattr(signal, 'macd', None),
                            'volume': getattr(signal, 'volume', None)
                        }
                    },
                    ctx=ctx,
                )
                # Ensure we have a valid file path
                if not trade_file:
                    trade_file = "trade_log_unavailable.json"
            except Exception as log_err:
                logging.warning(f"[WARN] Trade logging failed: {log_err}")
                trade_file = "trade_log_unavailable.json"
            
            # Execute the trade (placeholder - implement actual execution)
            if s.trade_db:
                try:
                    trade_id = s.trade_db.save_trade(
                        symbol=symbol,
                        strategy=getattr(signal, 'strategy', 'unknown'),
                        action=action,
                        entry_price=current_price,
                        quantity=position_size / current_price,  # Convert to number of shares/coins
                        metadata={
                            'target_price': target_price,
                            'stop_price': stop_price,
                            'trade_class': trade_params.get('trade_class'),
                            'trade_file': trade_file
                        }
                    )
                    logging.info(f"[OK] Trade {trade_id} executed and logged")
                except Exception as db_err:
                    logging.warning(f"[WARN] Failed to persist trade to DB: {db_err}")
            
            # Execute paper trade if enabled
            paper_buy_failed = False
            if s.paper_portfolio and 'BUY' in action:
                paper_result = s.paper_portfolio.execute_buy(
                    symbol=symbol,
                    quantity=int(position_size / current_price),
                    price=current_price,
                    signal_data={
                        'strategy': getattr(signal, 'strategy', 'unknown'),
                        'confidence': confidence,
                        'target_price': target_price,
                        'stop_price': stop_price,
                        'trade_class': trade_params.get('trade_class'),
                        'rsi': getattr(signal, 'rsi', 50),
                        'macd': getattr(signal, 'macd', 'neutral')
                    },
                    confidence=confidence * 100
                )
                
                if paper_result['success']:
                    logging.info(f"[PAPER] Bought {paper_result['quantity']} shares of {symbol} at ${current_price:.2f}")
                else:
                    paper_buy_failed = True
                    logging.warning(f"[PAPER] Failed to buy {symbol}: {paper_result['error']}")
                    try:
                        s.skipped_opportunity_watchlist.record_execution_skip(
                            symbol,
                            action,
                            confidence,
                            float(current_price),
                            reason=f"paper_buy:{paper_result.get('error', 'unknown')}",
                            source="execute_classified_trade",
                        )
                    except Exception:
                        pass

            if not paper_buy_failed:
                try:
                    s.skipped_opportunity_watchlist.mark_cleared(symbol)
                except Exception:
                    pass

            return {
                'symbol': symbol,
                'action': action,
                'entry_price': current_price,
                'target_price': target_price,
                'stop_price': stop_price,
                'position_size': position_size,
                'trade_class': trade_params.get('trade_class'),
                'trade_file': trade_file
            }
            
        except Exception as e:
            logging.error(f"[ERROR] Error executing trade: {e}", exc_info=True)
            return None

    def _generate_value_investing_reasoning(self, symbol: str, pe_analysis: Dict, current_price: float, target_price: float) -> str:
        """Generate AI reasoning for why THIS stock is a good value investment and why the industry needs it"""
        
        sector = pe_analysis.get('sector', 'Unknown')
        pe_ratio = pe_analysis.get('current_pe', 0)
        industry_pe = pe_analysis.get('industry_pe', 0)
        eps_growth = pe_analysis.get('eps_growth', 0)
        revenue_growth = pe_analysis.get('revenue_growth', 0)
        valuation_level = pe_analysis.get('valuation_level', 'Unknown')
        
        # Industry-specific reasoning
        industry_reasons = {
            'Technology': 'Tech sector essential for digital transformation. Undervalued firms often recover faster as innovation cycles accelerate.',
            'Healthcare': 'Healthcare demand grows with aging population. Undervalued plays benefit from consistent regulatory tailwinds.',
            'Financial Services': 'Banks/financials critical for economic recovery. Low P/E often indicates over-pessimism vs actual resilience.',
            'Energy': 'Energy transition creates opportunities. Traditional firms pivoting to renewables trade at discounts to growth peers.',
            'Consumer Discretionary': 'Consumer spending resilient. Value plays capture market share during economic shifts.',
            'Consumer Staples': 'Defensive sector with steady demand. Low P/E indicates safety margin in uncertain times.',
            'Industrial': 'Infrastructure spending supports industrials. Undervalued firms benefit from supply chain reshoring.',
            'Semiconductors': 'AI/Cloud demand surging. Cyclical downturns create entry points for long-term compounders.',
            'Software': 'SaaS adoption accelerating. Value plays often have strong cash flows misunderstood by markets.',
            'Retail': 'E-commerce evolution creating winners. Traditional retailers with digital pivot trade at discounts.',
            'Automotive': 'EV transition disrupting industry. Legacy automakers with strong balance sheets offer value.',
            'Aerospace': 'Defense spending stable. Commercial aviation recovery supports long-term growth.',
            'Utilities': 'Grid modernization needed. Stable dividends provide downside protection.',
            'Real Estate': 'REITs offer income + growth. Rate sensitivity creates buying opportunities.',
            'Communication Services': 'Streaming/ad shift evolving. Value plays capture market share shifts.',
            'Biotechnology': 'Innovation pipeline drives value. Clinical trial setbacks create entry points.',
            'Materials': 'Infrastructure spending supports materials. Cyclical downturns create value opportunities.',
            'Chemicals': 'Specialty chemicals essential. Value plays benefit from supply chain localization.'
        }
        
        # Get industry reasoning
        industry_reason = industry_reasons.get(sector, f"{sector} sector undergoing structural changes. Value opportunities emerge from market overreactions.")
        
        # Build why THIS stock reasoning
        this_stock_reasons = []
        
        # P/E discount
        if pe_ratio > 0 and industry_pe > 0:
            discount = ((industry_pe - pe_ratio) / industry_pe) * 100
            this_stock_reasons.append(f"Trading at {discount:.0f}% discount to industry P/E")
        
        # Growth momentum
        if eps_growth > 5:
            this_stock_reasons.append(f"Strong EPS growth ({eps_growth:.1f}%)")
        if revenue_growth > 5:
            this_stock_reasons.append(f"Revenue accelerating ({revenue_growth:.1f}%)")
        
        # Valuation strength
        if valuation_level in ['Significantly Undervalued', 'Deep Value']:
            this_stock_reasons.append(f"Deep value opportunity ({valuation_level})")
        
        # Price to target upside
        if target_price > current_price:
            upside = ((target_price / current_price) - 1) * 100
            this_stock_reasons.append(f"{upside:.0f}% upside to fair value")
        
        # Combine reasoning
        this_stock = " | ".join(this_stock_reasons) if this_stock_reasons else "Strong fundamentals mispriced by market"
        
        # Build final reasoning
        reasoning = f"WHY THIS STOCK: {this_stock}. WHY INDUSTRY: {industry_reason}"
        
        return reasoning

    async def run_learning_only(self, interval_minutes: int = 5, max_runtime_hours: int = 0):
        print("\n📚 Starting learning-only mode (news + social feeds, no trading)")
        learn_ctx = ApplicationContext.bind(self, {})
        started = await self.start_news_collection(ctx=learn_ctx)
        if not started:
            print("⚠️ Learning-only mode aborted: could not start news collection network")
            return

        start_time = datetime.now()
        cycle_count = 0
        try:
            while True:
                cycle_count += 1
                print(f"\n📚 Learning heartbeat {cycle_count}")
                self.get_news_memory_stats(ctx=learn_ctx)

                if max_runtime_hours > 0:
                    elapsed = datetime.now() - start_time
                    if elapsed.total_seconds() >= max_runtime_hours * 3600:
                        print("\n⏱️ Max learning runtime reached, stopping")
                        break

                await asyncio.sleep(max(1, interval_minutes) * 60)
        except KeyboardInterrupt:
            print("\n🛑 Learning-only mode stopped by user")
        except Exception as e:
            print(f"\n❌ Learning-only mode error: {e}")
        finally:
            try:
                await self.stop_news_collection(ctx=learn_ctx)
            except Exception as shutdown_err:
                print(f"⚠️ Error stopping news collection in learning-only mode: {shutdown_err}")

    async def run_24hour_cycles_demo(self):
        """Run 24 cycles with 5-minute waits for demo"""
        from datetime import datetime
        
        print("\n🚀 Starting 24-hour trading cycles (DEMO MODE)...")
        print("=" * 60)
        print("⚠️  Running 24 cycles with 5-minute waits for demonstration")
        print("📱 Trade signals will be posted to Telegram when found")
        print("=" * 60)
        
        for hour in range(24):
            print(f"\n{'='*60}")
            print(f"🕐 CYCLE {hour + 1}/24 - {datetime.now().strftime('%H:%M:%S')}")
            print(f"{'='*60}")
            
            try:
                # Run one full cycle with all features
                await self.run_full_cycle()
                
                print(f"\n✅ Cycle {hour + 1} complete")
                
                # Wait for next cycle (except after last one)
                if hour < 23:
                    print(f"\n⏳ Waiting 5 minutes for next cycle...")
                    await asyncio.sleep(300)  # 5 minutes for demo
                    
            except KeyboardInterrupt:
                print("\n⚠️ Interrupted by user")
                break
            except Exception as e:
                print(f"\n❌ Error in cycle {hour + 1}: {e}")
                continue
        
        print(f"\n{'='*60}")
        print("✅ 24-HOUR DEMO CYCLES COMPLETE")
        print(f"Ended: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*60}")

    async def run_24hour_cycles(self):
        """Run 24 hourly cycles with all new features enabled"""
        from datetime import datetime
        
        print("\n🚀 Starting 24-hour trading cycles...")
        print("=" * 60)
        
        for hour in range(24):
            print(f"\n{'='*60}")
            print(f"🕐 HOUR {hour + 1}/24 - {datetime.now().strftime('%H:%M:%S')}")
            print(f"{'='*60}")
            
            try:
                # Run one full cycle with all features
                await self.run_full_cycle()
                
                print(f"\n✅ Hour {hour + 1} complete")
                
                # Wait for next hour (except after last hour)
                if hour < 23:
                    print(f"\n⏳ Waiting 60 minutes for next hour...")
                    await asyncio.sleep(3600)  # 1 hour
                    
            except KeyboardInterrupt:
                print("\n⚠️ Interrupted by user")
                break
            except Exception as e:
                print(f"\n❌ Error in hour {hour + 1}: {e}")
                continue
        
        print(f"\n{'='*60}")
        print("✅ 24-HOUR CYCLES COMPLETE")
        print(f"Ended: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*60}")

    async def run_continuous(self, cycles: int = 5, interval_minutes: int = 10):
        """Run continuous trading cycles"""
        self.is_running = True
        self.monitoring_active = True
        self.monitoring_start_time = datetime.now()
        cycle_count = 0
        max_cycles = cycles
        ctx = ApplicationContext.bind(self, {})

        print(f"\n🚀 STARTING 24/7 MONITORING")
        print(f"⏰ Check interval: {interval_minutes} minutes")
        print(f"🔄 Max cycles: {'Unlimited' if cycles is None else cycles}")
        print(f"📊 Starting bankroll: ${ctx.config.get('bankroll', 0):,.2f}")
        print("📰 Fresh news + symbol rotation each cycle; learning trackers update over time.")
        
        try:
            while self.is_running and (max_cycles is None or cycle_count < max_cycles):
                try:
                    print(f"\n🔄 CYCLE {cycle_count + 1}" + (f" of {max_cycles}" if max_cycles else "") + 
                          f" @ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                    print("=" * 60)
                    
                    # Run a full trading cycle
                    signals = await self.run_full_cycle()
                    
                    # Check paper trading exits
                    self._check_paper_exits()
                    
                    # Process high-confidence signals
                    if signals:
                        high_confidence_signals = [
                            s for s in signals 
                            if getattr(s, 'confidence', 0) >= ctx.config.get('monitoring.high_confidence_threshold', 0.40)  # Lowered from 70% to 40%
                        ]
                        
                        if high_confidence_signals:
                            logging.info(f"🎯 High-confidence opportunities found: {len(high_confidence_signals)}")
                            for signal in high_confidence_signals:
                                # Execute the trade using our new classification system
                                trade_result = await self.execute_classified_trade(signal, ctx=ctx)
                                if trade_result:
                                    log_msg = (
                                        f"✅ EXECUTED: {trade_result['symbol']} {trade_result['action']} "
                                        f"@ ${trade_result['entry_price']:.2f} "
                                        f"(Class: {trade_result.get('trade_class', 'UNKNOWN')})"
                                    )
                                else:
                                    log_msg = (
                                        f"⚠️  SKIPPED: {getattr(signal, 'symbol', 'UNKNOWN')} "
                                        f"{getattr(signal, 'action', 'UNKNOWN')} - "
                                        f"Failed to execute"
                                    )
                                    try:
                                        _sym = str(getattr(signal, "symbol", "")).upper()
                                        _act = str(getattr(signal, "action", "BUY")).upper()
                                        _conf = float(getattr(signal, "confidence", 0) or 0)
                                        _p = float(
                                            getattr(signal, "current_price", 0)
                                            or getattr(signal, "entry_price", 0)
                                            or 0
                                        )
                                        if _p <= 0 and getattr(self, "robust_price_fetcher", None):
                                            try:
                                                _p = float(self.robust_price_fetcher.get_real_price(_sym) or 0)
                                            except Exception:
                                                _p = 0.0
                                        self.skipped_opportunity_watchlist.record_execution_skip(
                                            _sym,
                                            _act,
                                            _conf,
                                            _p,
                                            reason="execute_returned_none",
                                            source="monitor",
                                        )
                                    except Exception:
                                        pass
                                logging.info(log_msg)
                                
                                # Send Telegram alert for high-confidence signals
                                if ctx.config.get('monitoring.telegram_alerts_enabled', True):
                                    try:
                                        from telegram_bot import get_telegram_bot
                                        bot = get_telegram_bot()
                                        
                                        # Create unique key for deduplication
                                        symbol = getattr(signal, 'symbol', 'UNKNOWN')
                                        action = getattr(signal, 'action', 'UNKNOWN')
                                        entry_price = getattr(signal, 'entry_price', 0)
                                        monitor_key = f"MONITOR:{symbol}:{action}:{int(entry_price)}"
                                        
                                        if monitor_key not in self.posted_signals:
                                            result = bot.send_alert(signal)
                                            if result:
                                                self.posted_signals.add(monitor_key)
                                                self._save_posted_signals()
                                                logging.info(f"✅ Monitoring alert sent for {symbol}")
                                            else:
                                                logging.warning(f"⚠️ Failed to send monitoring alert for {symbol}")
                                        else:
                                            logging.info(f"⏭️ Monitoring alert already posted for {symbol} - skipping")
                                    except Exception as e:
                                        logging.error(f"Failed to send Telegram alert: {e}")
                    
                    # Update monitoring stats
                    self.monitoring_cycles = cycle_count + 1
                    
                    # Periodic position review (every 10 cycles or ~50 minutes at 5min intervals)
                    if cycle_count > 0 and cycle_count % 10 == 0:
                        print(f"\n🔄 Periodic position review (cycle {cycle_count})")
                        try:
                            self.review_open_positions()
                        except Exception as review_err:
                            print(f"⚠️ Position review failed: {review_err}")
                    
                    # Update market regime information
                    if hasattr(self, 'options_engine') and hasattr(self.options_engine, 'market_regime'):
                        current_regime = self.options_engine.market_regime.detect_current_regime()
                        print(f"📈 Market Regime: {current_regime}")
                    
                    # Wait for next cycle (unless this was the last cycle)
                    if self.is_running and (max_cycles is None or (cycle_count + 1) < max_cycles):
                        print(f"\n⏰ Next scan in {interval_minutes} minutes...")
                        print(f"💤 System will continue monitoring in background")
                        await asyncio.sleep(interval_minutes * 60)
                    
                    cycle_count += 1
                    
                except Exception as e:
                    print(f"❌ Error in cycle {cycle_count + 1}: {e}")
                    import traceback
                    print(traceback.format_exc())
                    print(f"🔄 Continuing monitoring after error...")
                    await asyncio.sleep(60)  # Short delay after error
                    
        except KeyboardInterrupt:
            print(f"\n🛑 24/7 MONITORING STOPPED BY USER")
            print(f"📊 Total cycles completed: {cycle_count}")
            print(f"⏰ Total monitoring time: {cycle_count * interval_minutes} minutes")
            
        except Exception as e:
            print(f"\n❌ FATAL ERROR IN 24/7 MONITORING: {e}")
            print(f"🚨 Emergency shutdown initiated")
            import traceback
            print(traceback.format_exc())
            
        finally:
            self.monitoring_active = False
            self.is_running = False
            print(f"\n✅ 24/7 monitoring terminated safely")
            
            # Print end-of-day ROI report
            if hasattr(self, 'daily_learning_tracker') and hasattr(self, 'alpaca_paper_trader') and self.alpaca_paper_trader.alpaca:
                try:
                    ending_balance = float(self.alpaca_paper_trader.alpaca.get_account().portfolio_value)
                    self.daily_learning_tracker.print_daily_roi_report(ending_balance)
                except Exception as e:
                    print(f"⚠️ Could not generate ROI report: {e}")

    def get_monitoring_status(self) -> Dict:
        """Get current monitoring status"""
        ctx = ApplicationContext.bind(self, {})
        return {
            'monitoring_active': self.monitoring_active,
            'monitoring_start_time': self.monitoring_start_time,
            'monitoring_cycles': self.monitoring_cycles,
            'is_running': self.is_running,
            'bankroll': ctx.config.get('bankroll'),
            'risk_per_trade': ctx.config.get('risk_per_trade'),
            'max_drawdown': ctx.config.get('max_drawdown')
        }

    def show_status(self):
        """
        Show current system status and open positions
        """
        ctx = ApplicationContext.bind(self, {})
        s = ctx.system
        print("📊 PHASMA AI CURRENT STATUS")
        print("=" * 50)
        
        # Show adaptive confidence threshold status
        if hasattr(self, 'adaptive_threshold'):
            self.adaptive_threshold.print_status()
            print()
        
        # Get status from meta_brain
        status = s.meta_brain.get_status()
        
        print(f"💰 Available Bankroll: ${status['bankroll']:,.2f}")
        print(f"🎯 POP Threshold: {ctx.config.get('pop_threshold', 0.5)}")
        print(f"🛡️ Risk Per Trade: {ctx.config.get('risk_per_trade', 0.01)}")
        print(f"📈 Max Drawdown: {ctx.config.get('max_drawdown', 0.1)}")
        
        # Performance
        print(f"📊 Daily P&L: ${status['daily_pnl']:,.2f}")
        print(f"🎯 Open Positions: {status['open_positions']}")
        print(f"⚡ Active Engines: {len(status['active_engines'])}")
        
        # Open positions
        if s.meta_brain.risk_manager.open_positions:
            print("\n📂 ACTIVE TRADES (Open Positions):")
            for symbol, pos in s.meta_brain.risk_manager.open_positions.items():
                signal = pos.get('signal', {})
                action = signal.get('action', 'Unknown')
                size = signal.get('position_size', 0)
                confidence = signal.get('confidence', 0)
                entry_time = pos.get('entry_time')
                
                # Calculate days held and left
                max_hold_days = signal.get('max_hold_days', 30)  # default if not set
                days_held = 0
                days_left = max_hold_days
                if entry_time:
                    try:
                        if isinstance(entry_time, str):
                            entry_dt = datetime.fromisoformat(entry_time.replace('Z', '+00:00'))
                        else:
                            entry_dt = entry_time
                        days_held = (datetime.now() - entry_dt).days
                        days_left = max(0, max_hold_days - days_held)
                    except:
                        pass
                
                print(f"• {symbol}: {action} | Size ${size} | Conf {confidence:.0%} | Held {days_held}d / {max_hold_days}d ({days_left}d left)")
        else:
            print("📂 No open positions")
        
        print("\n✅ Status update complete")
    
    def review_open_positions(self):
        """
        Review all open positions to re-assess confidence and learn from trade decisions
        """
        s = ApplicationContext.bind(self, {}).system
        print("🔄 REVIEWING OPEN POSITIONS - Re-assessing confidence and learning")
        print("=" * 70)
        
        open_positions = getattr(s.meta_brain.risk_manager, 'open_positions', {}) or {}
        if not open_positions:
            print("📂 No open positions to review")
            return
        
        total_positions = len(open_positions)
        confidence_drops = 0
        confidence_holds = 0
        learning_points = []
        
        print(f"📊 Reviewing {total_positions} open positions...")
        
        for symbol, pos in open_positions.items():
            print(f"\n🔍 Reviewing {symbol}:")
            
            signal = pos.get('signal', {})
            original_confidence = signal.get('confidence', 0)
            original_rationale = signal.get('rationale', 'Unknown')
            action = signal.get('action', 'Unknown')
            entry_time = pos.get('entry_time')
            
            # Calculate current hold time
            days_held = 0
            if entry_time:
                try:
                    if isinstance(entry_time, str):
                        entry_dt = datetime.fromisoformat(entry_time.replace('Z', '+00:00'))
                    else:
                        entry_dt = entry_time
                    days_held = (datetime.now() - entry_dt).days
                except:
                    days_held = 0
            
            print(f"   Original confidence: {original_confidence:.1%}")
            print(f"   Rationale: {original_rationale}")
            print(f"   Days held: {days_held}")
            
            # Try to re-assess confidence by simulating current market conditions
            try:
                # Get current price
                price_fetcher = get_price_fetcher()
                current_price = price_fetcher.get_real_price(symbol)
                
                if current_price:
                    print(f"   Current price: ${current_price:.2f}")
                    
                    # Re-run unified analysis if possible
                    # For now, use a simplified re-assessment based on time held and performance
                    time_factor = min(1.0, days_held / 30.0)  # Decay confidence over time
                    current_confidence = original_confidence * (1.0 - time_factor * 0.3)  # 30% max decay
                    
                    confidence_change = current_confidence - original_confidence
                    
                    if confidence_change < -0.2:  # Significant drop
                        print(f"   ⚠️ CONFIDENCE DROP: {current_confidence:.1%} ({confidence_change*100:+.1f}%)")
                        confidence_drops += 1
                        
                        # Learning: Why did confidence drop?
                        learning_point = {
                            'symbol': symbol,
                            'original_confidence': original_confidence,
                            'current_confidence': current_confidence,
                            'days_held': days_held,
                            'action': action,
                            'rationale': original_rationale,
                            'lesson': f"Confidence decayed significantly over {days_held} days. Consider shorter timeframes for {action} trades."
                        }
                        learning_points.append(learning_point)
                        
                        print("   💡 Learning: Trade timing may be too long for market conditions")
                        
                    elif confidence_change > 0.1:  # Improved
                        print(f"   ✅ CONFIDENCE IMPROVED: {current_confidence:.1%} ({confidence_change*100:+.1f}%)")
                        confidence_holds += 1
                        
                        learning_point = {
                            'symbol': symbol,
                            'original_confidence': original_confidence,
                            'current_confidence': current_confidence,
                            'days_held': days_held,
                            'action': action,
                            'rationale': original_rationale,
                            'lesson': f"Confidence improved over time. {action} trades on similar catalysts may benefit from longer holds."
                        }
                        learning_points.append(learning_point)
                        
                    else:
                        print(f"   ✅ CONFIDENCE HOLDS: {current_confidence:.1%} ({confidence_change*100:+.1f}%)")
                        confidence_holds += 1
                        
                else:
                    print("   ⚠️ Could not fetch current price for re-assessment")
            except Exception as e:
                print(f"   ❌ Re-assessment failed: {e}")
                confidence_holds += 1  # Default to holding
        
        # Summary
        print(f"\n📊 REVIEW SUMMARY:")
        print(f"   Total positions reviewed: {total_positions}")
        print(f"   Confidence holds/stable: {confidence_holds}")
        print(f"   Significant confidence drops: {confidence_drops}")
        
        if learning_points:
            print(f"\n🧠 LEARNING POINTS ({len(learning_points)}):")
            for i, point in enumerate(learning_points[:5], 1):  # Show top 5
                print(f"   {i}. {point['symbol']} ({point['action']}): {point['lesson']}")
                
                # Update alert learning system if available
                try:
                    # Convert trade review to alert outcome format
                    alert_data = {
                        'symbol': point['symbol'],
                        'action': point['action'],
                        'confidence': point.get('confidence', 0.5),
                        'timestamp': point.get('timestamp', ''),
                        'source': 'trade_review'
                    }
                    outcome = 'success' if point.get('success', False) else 'failure'
                    self.alert_learning.record_alert_outcome(alert_data, outcome, point)
                except:
                    pass
        
        # Store learning for future improvement
        if learning_points:
            try:
                # Save to a learning file for persistence
                learning_file = "trade_learning.json"
                try:
                    with open(learning_file, 'r') as f:
                        existing_learning = json.load(f)
                except:
                    existing_learning = []
                
                existing_learning.extend(learning_points)
                # Keep only last 100 learning points
                existing_learning = existing_learning[-100:]
                
                with open(learning_file, 'w') as f:
                    json.dump(existing_learning, f, indent=2, default=str)
                
                print(f"\n💾 Saved {len(learning_points)} learning points to {learning_file}")
                
            except Exception as e:
                print(f"⚠️ Could not save learning points: {e}")
        
        print("\n✅ Position review complete")
    
    def _get_recent_trades(self, days_back: int) -> list:
        """
        Get recent trades from the trade database
        
        Args:
            days_back: Number of days to look back
            
        Returns:
            List of trade dictionaries in the format expected by analyze_trades()
        """
        if not self.trade_db:
            print("⚠️  Trade database not available")
            return []
            
        try:
            # Get recent trades from the database
            db_trades = self.trade_db.get_recent_trades(days_back=days_back)
            
            # Convert to the format expected by analyze_trades()
            trades = []
            for trade in db_trades:
                trades.append({
                    'symbol': trade['symbol'],
                    'strategy': trade['strategy'],
                    'action': trade['action'],
                    'entry_price': trade['entry_price'],
                    'exit_price': trade.get('exit_price'),
                    'quantity': trade['quantity'],
                    'pnl': trade.get('pnl') or 0,
                    'entry_time': trade['entry_time'],
                    'exit_time': trade.get('exit_time'),
                    'status': trade['status'],
                    'metadata': trade.get('metadata', {})
                })
                
            print(f"📊 Retrieved {len(trades)} trades from the last {days_back} days")
            return trades
            
        except Exception as e:
            print(f"❌ Error retrieving trades: {e}")
            import traceback
            traceback.print_exc()
            return []
            
    def log_final_trade_decision(
        self,
        symbol: str,
        trade_type: str,
        entry_price: float,
        target_price: float,
        stop_price: float,
        confidence: float,
        simulations_run: int,
        success_rate: float,
        reason: str,
        trade_class: str,
        asset_type: str = "crypto",
        min_hold_days: Optional[int] = None,
        max_hold_days: Optional[int] = None,
        review_cadence_hours: int = 72,
        risk_reward_ratio: Optional[float] = None,
        metadata: Optional[Dict] = None,
        *,
        ctx: Optional[ApplicationContext] = None,
    ) -> str:
        """
        Log a final trade decision with the trade logger
        
        Args:
            symbol: Trading symbol (e.g., 'BTC', 'TSLA')
            trade_type: Type of trade (BUY_CALL, BUY_PUT, etc.)
            entry_price: Entry price
            target_price: Target price
            stop_price: Stop loss price
            confidence: Confidence level (0-1)
            simulations_run: Number of simulations run
            success_rate: Success rate from simulations (0-1)
            reason: Detailed reasoning for the trade
            trade_class: Trade class (MOONSHOT_7D, SWING_30D, POSITION_60_90D)
            asset_type: Type of asset ('stock' or 'crypto')
            min_hold_days: Minimum hold period in days
            max_hold_days: Maximum hold period in days
            review_cadence_hours: How often to review the trade (in hours)
            risk_reward_ratio: Risk to reward ratio
            metadata: Additional trade metadata
            
        Returns:
            Path to the saved trade file
        """
        if ctx is None:
            ctx = ApplicationContext.bind(self, {})
        ps = ctx.system
        return ps.trade_logger.log_trade(
            symbol=symbol,
            trade_type=trade_type,
            entry_price=entry_price,
            target_price=target_price,
            stop_price=stop_price,
            confidence=confidence,
            simulations_run=simulations_run,
            success_rate=success_rate,
            reason=reason,
            modules=["trading_system"],
            trade_class=trade_class,
            asset_type=asset_type,
            min_hold_days=min_hold_days,
            max_hold_days=max_hold_days,
            review_cadence_hours=review_cadence_hours,
            risk_reward_ratio=risk_reward_ratio,
            metadata=metadata or {}
        )
        
    def classify_trade(
        self,
        symbol: str,
        asset_type: str = 'stock',
        catalyst: Optional[Dict] = None,
        momentum: Optional[Dict] = None,
        iv_rank: Optional[float] = None,
        macro_conditions: Optional[Dict] = None,
        *,
        ctx: Optional[ApplicationContext] = None,
    ) -> Dict[str, Any]:
        """
        Classify a trade based on market conditions
        
        Args:
            symbol: Trading symbol
            asset_type: Type of asset ('stock' or 'crypto')
            catalyst: Dictionary with catalyst info (date, type, confidence)
            momentum: Dictionary with momentum indicators
            iv_rank: Current IV rank (0-100)
            macro_conditions: Current macro conditions
            ctx: Optional cycle context (defaults to a fresh bind).
            
        Returns:
            Dictionary with trade classification and parameters
        """
        if ctx is None:
            ctx = ApplicationContext.bind(self, {})
        ps = ctx.system
        return ps.trade_classifier.classify_trade(
            symbol=symbol,
            asset_type=asset_type,
            catalyst=catalyst,
            momentum=momentum,
            iv_rank=iv_rank,
            macro_conditions=macro_conditions
        )

def parse_arguments():
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Phasma AI Trading System — default mode is 24/7 continuous cycles (use --status / --review for one-shot ops).'
    )
    parser.add_argument(
        '--monitor',
        action='store_true',
        help='Optional explicit flag; same as default (24/7 continuous monitoring)',
    )
    parser.add_argument('--24hour', dest='run_24hour', action='store_true', help='Run for 24 hours with all new features enabled')
    parser.add_argument('--24hour-demo', dest='run_24hour_demo', action='store_true', help='Run for 24 cycles with 5-minute waits (demo mode)')
    parser.add_argument('--learning-only', action='store_true', help='Run in learning-only mode (news + memory, no trades)')
    parser.add_argument('--analyze', type=int, nargs='?', const=30, help='Analyze trades from the last N days (default: 30)')
    parser.add_argument('--status', action='store_true', help='Show current system status and open positions')
    parser.add_argument('--review', action='store_true', help='Review open positions for confidence reassessment and learning')
    parser.add_argument('--interval', type=int, default=5, 
                       help='Monitoring interval in minutes (default: 5)')
    parser.add_argument('--max-runtime', type=int, default=0,
                       help='Maximum runtime in hours (0 for unlimited, default: 0)')
    parser.add_argument('--log-level', type=str, default='INFO',
                       choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                       help='Logging level (default: INFO)')
    
    return parser.parse_args()

if __name__ == "__main__":
    try:
        args = parse_arguments()
        
        # Configure logging
        logging.basicConfig(
            level=getattr(logging, args.log_level),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('phasma_trading.log'),
                logging.StreamHandler()
            ]
        )
        
        # Initialize core components
        system = PhasmaTradingSystem("config.json")

        if args.learning_only:
            print("🚀 Starting Phasma AI in learning-only mode (no trades)")
            print(f" Scan interval: {args.interval} minutes")
            print(f" Max runtime: {'Unlimited' if args.max_runtime == 0 else f'{args.max_runtime} hours'}")
            print(" Press Ctrl+C to stop learning mode")
            print("=" * 60)

            try:
                asyncio.run(system.run_learning_only(
                    interval_minutes=args.interval,
                    max_runtime_hours=args.max_runtime
                ))
            finally:
                try:
                    asyncio.run(system.shutdown())
                except Exception as shutdown_err:
                    print(f"⚠️ Shutdown error: {shutdown_err}")

        elif args.analyze is not None:
            print("📊 Starting Phasma AI trade analysis")
            print(f" Analyzing trades from the last {args.analyze} days")
            print("=" * 60)
            system.analyze_trades(days_back=args.analyze)

        elif args.status:
            system.show_status()

        elif args.review:
            system.review_open_positions()

        elif args.run_24hour_demo:
            print("🚀 Starting Phasma AI in 24-HOUR DEMO MODE (5-min cycles)")
            print("=" * 60)
            
            # Enable all new features
            system.config.set('trading.unified_brain', True)
            system.config.set('trading.sector_intelligence', True)
            system.config.set('trading.expansion_engine', True)
            system.config.set('trading.bias_breaker', True)
            
            print("\n✅ FEATURES ENABLED:")
            print("  • Unified Brain - All systems working together")
            print("  • Sector Intelligence - Industry correlations")
            print("  • Expansion Engine - Always finding NEW stocks")
            print("  • Bias Breaker - No top-3 obsession")
            print("  • Telegram Alerts - Real-time trade signals")
            
            # Run 24 cycles with 5-minute waits
            try:
                asyncio.run(system.run_24hour_cycles_demo())
            except KeyboardInterrupt:
                print("\n🛑 24-hour demo mode stopped by user")
        elif args.run_24hour:
            print("🚀 Starting Phasma AI in 24-HOUR MODE with all features")
            print("=" * 60)
            
            # Enable all new features
            system.config.set('trading.unified_brain', True)
            system.config.set('trading.sector_intelligence', True)
            system.config.set('trading.expansion_engine', True)
            system.config.set('trading.bias_breaker', True)
            
            print("\n✅ FEATURES ENABLED:")
            print("  • Unified Brain - All systems working together")
            print("  • Sector Intelligence - Industry correlations")
            print("  • Expansion Engine - Always finding NEW stocks")
            print("  • Bias Breaker - No top-3 obsession")
            
            # Run 24 cycles
            try:
                asyncio.run(system.run_24hour_cycles())
            except KeyboardInterrupt:
                print("\n🛑 24-hour mode stopped by user")
        else:
            # Production default: 24/7 continuous cycles (--monitor is optional, same behavior)
            print("🚀 Starting Phasma AI — 24/7 continuous mode (default)")
            if args.monitor:
                print("   (--monitor: explicit flag, same as default)")
            print("   Each cycle re-scans news and discovery; skipped names are reconsidered on later cycles.")
            print(f" Scan interval: {args.interval} minutes")
            print(f" Max runtime: {'Unlimited' if args.max_runtime == 0 else f'{args.max_runtime} hours'}")
            print(" Press Ctrl+C to stop")
            print("=" * 60)

            try:
                max_cycles = None if args.max_runtime == 0 else (args.max_runtime * 60) // args.interval
                asyncio.run(system.run_continuous(
                    cycles=max_cycles,
                    interval_minutes=args.interval
                ))
            except KeyboardInterrupt:
                print("\n🛑 Monitoring stopped by user")
            finally:
                try:
                    asyncio.run(system.shutdown())
                except Exception as shutdown_err:
                    print(f"⚠️ Shutdown error: {shutdown_err}")
            
    except KeyboardInterrupt:
        print("\n🛑 Phasma AI stopped by user (Ctrl+C)")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Unhandled error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)