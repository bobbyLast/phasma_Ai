# Phasma AI Codebase Investigation Summary

## Overview
- **Total Python Files**: 152
- **Main Entry Point**: main.py
- **Investigation Date**: 2025-12-16

## Actively Used Components (Imported by main.py)

### Core Modules (7 files)
- `core/meta_brain.py` - Main AI brain system
- `core/config.py` - Configuration management
- `core/trade_classifier.py` - Trade classification
- `core/trade_logger.py` - Trade logging
- `core/trade_database.py` - Trade database storage
- `core/portfolio_dashboard.py` - Portfolio dashboard
- `core/performance_tracker.py` - Performance tracking

### Active Engines (13 files)
- `engines/options_engine.py` - Options trading (DISABLED)
- `engines/investment_news_scanner.py` - News scanning
- `engines/signal_convergence_engine.py` - Signal convergence
- `engines/thematic_analysis_engine.py` - Thematic analysis
- `engines/pump_dump_detector.py` - Pump/dump detection ✅ NEW
- `engines/global_macro_monitor.py` - Macro monitoring ✅ NEW
- `engines/insider_signal_integrator.py` - Insider signals ✅ NEW
- `engines/market_intelligence_engine.py` - Market intelligence
- `engines/monte_carlo_engine.py` - Monte Carlo simulations
- `engines/crash_profit_engine.py` - Crash profit (DISABLED)
- `engines/day_trading_scanner.py` - Day trading scanner
- `engines/market_crash_detector_v2.py` - Market crash detection
- `engines/kalshi_engine.py` - Kalshi prediction markets
- `engines/news_collection_network.py` - News collection
- `engines/partnership_engine/` - Partnership engine (has issues)

### Active Utils (16 files)
- `utils/price_fetcher.py` - Price fetching
- `utils/trade_memory.py` - Trade memory
- `utils/timeframe_calculator.py` - Timeframe calculations
- `utils/alert_router.py` - Alert routing
- `utils/volatility_burst_detector.py` - Volatility detection
- `utils/weekly_watchlist.py` - Weekly watchlist
- `utils/winners_gallery.py` - Winners tracking
- `utils/insider_opportunity_analyzer.py` - Insider analysis
- `utils/politician_tracker.py` - Politician trading
- `utils/trader_call_logger.py` - Trader calls
- `utils/exit_strategy_manager.py` - Exit strategies
- `utils/strategy_cue_cards.py` - Strategy cards
- `utils/news_impact_tracker.py` - News impact
- `utils/alert_learning_loop.py` - Alert learning
- `utils/dynamic_portfolio_manager.py` - Portfolio management ✅ NEW
- `utils/moon_shot_detector.py` - Moon shot detection
- `utils/adaptive_position_sizer.py` - Position sizing
- `utils/conviction_watchlist.py` - Conviction watchlist

## Unused Engines (43 files)
These engines exist but are NOT imported by main.py:
- `engines/auto_exit_manager.py`
- `engines/backtest_engine.py`
- `engines/calendar_seasonality_engine.py`
- `engines/causal_counterfactual_engine.py`
- `engines/corporate_actions_engine.py`
- `engines/correlation_tracker.py`
- `engines/cross_venue_radar.py`
- `engines/earnings_drift_engine.py`
- `engines/earnings_scanner.py`
- `engines/event_structure_engine.py`
- `engines/exit_optimizer.py`
- `engines/finnhub_news.py`
- `engines/geopolitical_engine.py`
- `engines/iv_crush_predictor.py`
- `engines/macro_calendar_engine.py`
- `engines/market_crash_detector.py` (old version)
- `engines/market_regime.py`
- `engines/market_scanner_24_7.py`
- `engines/microstructure_engine.py`
- `engines/moonshot_keywords.py`
- `engines/narrative_generator.py`
- `engines/news_engine_analysis.py`
- `engines/news_engine_apis.py`
- `engines/news_engine_core.py`
- `engines/news_engine_utils.py`
- `engines/news_engine_validation.py`
- `engines/news_memory_bank.py`
- `engines/pricing_sources.py`
- `engines/range_barrier_engine.py`
- `engines/risk_engine.py`
- `engines/risk_guardian_meta_agent.py`
- `engines/scenario_graph_engine.py`
- `engines/self_calibrating_probability_engine.py`
- `engines/smart_monte_carlo.py`
- `engines/sports_analysis_engine.py`
- `engines/spread_builder.py`
- `engines/strike_expiry_selector.py`
- `engines/top_10_dashboard.py`
- `engines/trade_analyzer/`
- `engines/volatility_edge_engine.py`
- `engines/weather_engine.py`
- `engines/weather_validation_engine.py`

## Test Files (14 files)
- `test_system_integration.py` ✅ NEW
- `test_ai_penny_insider.py`
- `test_fundamental_filters.py`
- `test_insider_analyzer.py`
- `test_insider_mock.py`
- `test_kalshi_discovery.py`
- `test_real_ticker.py`
- `test_retry_logic.py`
- `test_retry_minimal.py`
- `test_scan_all_sources.py`
- `test_weather_validation.py`
- `engines/backtest_engine.py`
- `tests/test_government_contracts.py`
- `utils/create_test_data.py`

## Demo Files (6 files)
- `advanced_brain_demo.py`
- `demo_weather_validation_complete.py`
- `geopolitical_kalshi_demo.py`
- `ultimate_brain_demo.py`
- `ultimate_expansion_demo.py`
- `ultimate_options_brain_demo.py`

## Standalone Scripts (20+ files)
- `check_kalshi_market_types.py`
- `check_recent_trades.py`
- `debug_kalshi_predictions.py`
- `debug_sec_edgar.py`
- `inspect_market_data.py`
- `monitor.py`
- `reddit_monitor.py`
- `reset_portfolio.py`
- `run_with_all_sources.py`
- `simple_test.py`
- `telegram_bot.py`
- `trending_tracker.py`
- `ultimate_easy_trade_detector.py`
- `ultimate_easy_trade_detector_all_categories.py`
- `verify_system.py`
- And more...

## Key Findings

### ✅ Recently Added (Active)
1. **Pump/Dump Detector** - Protects against penny stock dumps
2. **Global Macro Monitor** - Tracks Japan carry trade risk
3. **Insider Signal Integrator** - Detects million-dollar confluence
4. **Dynamic Portfolio Manager** - Splits bankroll ($50 stocks, $50 Kalshi)
5. **System Integration Test** - Verifies all components work together

### ⚠️ Issues Identified
1. **43 Unused Engines** - Large amount of unused code
2. **Multiple Crash Detectors** - Both v1 and v2 exist
3. **6 Demo Files** - Old demos cluttering codebase
4. **20+ Standalone Scripts** - Many single-purpose scripts
5. **Partnership Engine Issues** - Missing API keys causing errors

### 📊 Statistics
- **Active Code**: ~36 files (core + engines + utils)
- **Unused Code**: ~43 files (engines not imported)
- **Test Code**: ~14 files
- **Demo Code**: ~6 files
- **Scripts**: ~20+ files
- **Total**: ~152 files

### 💡 Recommendations

#### Immediate Actions
1. **Archive unused engines** - Move 43 unused engines to `archive/` folder
2. **Remove duplicate crash detector** - Keep only v2
3. **Consolidate news engines** - Multiple news engines doing similar work
4. **Fix partnership engine** - Resolve API key issues or disable

#### Code Cleanup
1. **Create demo archive** - Move old demos to `demos/` folder
2. **Organize scripts** - Move utility scripts to `scripts/` folder
3. **Document active components** - Create README for actively used components
4. **Remove dead code** - Delete truly unused files after testing

#### Architecture Improvements
1. **Modularize imports** - Make engine imports optional/configurable
2. **Plugin system** - Allow engines to be loaded dynamically
3. **Reduce dependencies** - Many engines depend on each other
4. **Simplify main.py** - 5000+ lines, should be broken down

### 🎯 Priority Actions
1. **HIGH**: Archive 43 unused engines (saves ~15,000+ lines of code)
2. **MEDIUM**: Consolidate duplicate functionality
3. **LOW**: Organize demos and scripts

## Conclusion
The codebase has grown significantly with many experimental features that are no longer used. The core trading system uses only ~36 files actively, while the remaining ~116 files are unused, tests, demos, or standalone scripts. A cleanup would significantly improve maintainability and reduce confusion.
