# Phasma Engine Inventory

Generated: 2026-06-21T03:27:45.640803+00:00

Raw items found: **5676**
Unique logical engines: **3825**
Utilities excluded: **0**
Unmapped (pre-triage): **530**

## By Group

- **DiscoveryGroup**: 2845
- **RiskGroup**: 992
- **Unmapped**: 530
- **MarketGroup**: 285
- **SignalGroup**: 264
- **IngestGroup**: 264
- **ReportingGroup**: 232
- **EnrichmentGroup**: 93
- **DecisionGroup**: 64
- **ExecutionGroup**: 55
- **LearningGroup**: 36
- **Utility**: 16

## Sample Entries

- `get_monitoring_status` — main.py → Unmapped
- `RiskParameters, TradeDecision` — main.py → RiskGroup
- `from brain.signal_convergence_engine import SignalConvergenceEngine` — main.py → DiscoveryGroup
- `from brain.thematic_analysis_engine import ThematicAnalyzer` — main.py → DiscoveryGroup
- `from engines.pump_dump_detector import PumpDumpDetector` — main.py → DiscoveryGroup
- `from engines.enhanced_options_flow_detector import get_enhanced_options_detector` — main.py → SignalGroup
- `kalshi_intel_only,` — main.py → DiscoveryGroup
- `from engines.insider_signal_integrator import InsiderSignalIntegrator` — main.py → DiscoveryGroup
- `from brain.market_intelligence_engine import MarketIntelligenceEngine` — main.py → MarketGroup
- `# RiskGuardianMetaAgent, SelfCalibratingProbabilityEngine, ScenarioGraphEngine,` — main.py → RiskGroup
- `# Crash profit functionality now integrated in crash_detector_v2` — main.py → RiskGroup
- `from utils.volatility_burst_detector import get_vol_burst_detector` — main.py → Unmapped
- `from utils.insider_opportunity_analyzer import get_insider_analyzer` — main.py → DiscoveryGroup
- `from utils.politician_tracker import PoliticianTracker` — main.py → DiscoveryGroup
- `from utils.pe_ratio_analyzer import PERatioAnalyzer` — main.py → Unmapped
- `from engines.market_hours_detector import MarketHoursDetector` — main.py → MarketGroup
- `from utils.moon_shot_detector import MoonShotDetector` — main.py → Unmapped
- `from utils.randomness_pattern_analyzer import RandomnessPatternAnalyzer` — main.py → Unmapped
- `# Import unified trading system` — main.py → Unmapped
- `from trading.unified_trading_system import UnifiedTradingSystem` — main.py → Unmapped
- `from engines.underground_stock_discovery import UndergroundStockDiscovery` — main.py → DiscoveryGroup
- `from engines.geopolitical_analyzer import GeopoliticalImpactAnalyzer` — main.py → DiscoveryGroup
- `from engines.multi_platform_scanner import MultiPlatformScanner` — main.py → Unmapped
- `self.max_discovery = self.config.apply_max_discovery_overrides()` — main.py → DiscoveryGroup
- `if self.max_discovery:` — main.py → DiscoveryGroup
- `print("🔍 MAX DISCOVERY MODE ACTIVE")` — main.py → DiscoveryGroup
- `self.ai_analyzed_history = {}  # History of what was analyzed and when` — main.py → Unmapped
- `self.trading_mode = self.config.get('trading_mode', 'stocks_and_kalshi')` — main.py → DiscoveryGroup
- `self.vol_burst_detector = get_vol_burst_detector()` — main.py → Unmapped
- `self.insider_monitor = get_insider_analyzer(self.config)` — main.py → DiscoveryGroup
- `self.politician_tracker = PoliticianTracker(self.config.get('politician_tracker', {}))` — main.py → DiscoveryGroup
- `self.market_hours = MarketHoursDetector()` — main.py → MarketGroup
- `self.geo_analyzer = GeopoliticalImpactAnalyzer()` — main.py → DiscoveryGroup
- `self.geo_scanner = MultiPlatformScanner()` — main.py → DiscoveryGroup
- `# Initialize day trading scanner for regular stocks` — main.py → Unmapped
- `from engines.day_trading_scanner import get_day_trading_scanner` — main.py → Unmapped
- `self.day_trading_scanner = get_day_trading_scanner(self.config)` — main.py → Unmapped
- `self.moon_shot_detector = MoonShotDetector(self.config)` — main.py → Unmapped
- `self.pump_dump_detector = PumpDumpDetector(self.config)` — main.py → DiscoveryGroup
- `self.insider_signal_integrator = InsiderSignalIntegrator(self.config)` — main.py → DiscoveryGroup