# Phasma AI - Usage Analysis

## ✅ **ACTIVELY USED (In Main Trading Loop)**

### **Core Components (Always Used)**
- **news_engine** - NewsAPIIntegration: Scans news sources ✅
- **day_trading_scanner** - Finds momentum stocks ✅
- **moon_shot_detector** - Detects high-potential stocks ✅
- **pump_dump_detector** - Detects pump & dumps ✅
- **global_macro_monitor** - Tracks macro indicators ✅
- **insider_signal_integrator** - Integrates insider signals ✅
- **thematic_analyzer** - Analyzes themes ✅
- **convergence_engine** - Combines signals ✅
- **market_intelligence** - Market context analysis ✅
- **position_sizer** - Calculates position sizes ✅
- **real_portfolio_manager** - Manages portfolio ✅
- **meta_brain** - Central AI decision maker ✅

### **Conditionally Used (Based on Config)**
- **options_engine** - Only if options enabled in config ❌ (Currently disabled)
- **social_engine** - Only if social trading enabled ✅
- **crash_detector** - Only if crash detection enabled ✅
- **kalshi_engine** - Only if Kalshi enabled ✅
- **partnership_engine** - Only if partnerships enabled ❌ (Currently None)
- **profit_exit_manager** - Only if profit maximization enabled ❌ (Currently disabled)

### **Utils Used**
- **price_fetcher** - Gets stock prices ✅
- **affordable_stock_filter** - Filters by affordability ✅
- **trade_memory** - Tracks trade history ✅
- **timeframe_calculator** - Calculates timeframes ✅
- **exit_strategy_manager** - Manages exits ✅
- **news_impact_tracker** - Tracks news impact ✅
- **winners_gallery** - Shows winning trades ✅
- **insider_opportunity_analyzer** - Analyzes insider trades ✅
- **politician_tracker** - Tracks politician trades ✅
- **trader_call_logger** - Logs trader calls ✅

## ❌ **NOT USED (Imported but Not Used in Trading Loop)**

### **Engines Not Used**
1. **advanced_sentiment_engine** - Sentiment analysis (unused)
2. **auto_exit_manager** - Auto exit (unused, has exit_strategy_manager)
3. **backtest_engine** - Backtesting (for testing only)
4. **calendar_seasonality_engine** - Seasonality analysis (unused)
5. **corporate_actions_engine** - Corporate actions (unused)
6. **correlation_tracker** - Correlation tracking (unused)
7. **cross_venue_radar** - Cross-venue analysis (unused)
8. **dynamic_market_scanner** - Market scanning (duplicate)
9. **earnings_drift_engine** - Earnings drift (unused)
10. **earnings_scanner** - Earnings scanner (unused)
11. **event_structure_engine** - Event analysis (unused)
12. **exit_optimizer** - Exit optimization (unused)
13. **geopolitical_engine** - Geopolitical analysis (unused)
14. **iv_crush_predictor** - IV crush prediction (unused)
15. **macro_calendar_engine** - Macro calendar (unused)
16. **market_regime** - Market regime detection (unused)
17. **market_scanner_24_7** - 24/7 scanning (unused)
18. **microstructure_engine** - Microstructure analysis (unused)
19. **monte_carlo_engine** - Monte Carlo simulation (unused)
20. **moonshot_keywords** - Moonshot keywords (unused)
21. **narrative_generator** - Narrative generation (unused)
22. **news_collection_network** - News collection (unused)
23. **news_engine_analysis** - News analysis (unused)
24. **news_engine_apis** - News APIs (unused)
25. **news_engine_core** - News core (unused)
26. **news_engine_validation** - News validation (unused)
27. **news_insider_correlator** - News-insider correlation (unused)
28. **news_memory_bank** - News memory (unused)
29. **news_pattern_recognition** - News patterns (unused)
30. **pricing_sources** - Pricing sources (unused)
31. **range_barrier_engine** - Range barriers (unused)
32. **risk_engine** - Risk management (unused)
33. **risk_guardian_meta_agent** - Risk guardian (unused)
34. **scenario_graph_engine** - Scenario analysis (unused)
35. **self_calibrating_probability_engine** - Probability calibration (unused)
36. **smart_monte_carlo** - Smart Monte Carlo (unused)
37. **spread_builder** - Spread building (unused)
38. **strike_expiry_selector** - Strike/expiry selection (unused)
39. **top_10_dashboard** - Dashboard (unused)
40. **volatility_edge_engine** - Volatility edge (unused)
41. **weather_consistency_engine** - Weather consistency (unused)
42. **weather_engine** - Weather engine (unused)
43. **weather_validation_engine** - Weather validation (unused)

### **Utils Not Used**
1. **robust_price_fetcher** - Backup price fetcher (unused)
2. **trade_recommendation_memory** - Recommendation memory (unused)
3. **alert_router** - Alert routing (unused)
4. **volatility_burst_detector** - Volatility bursts (unused)
5. **cooldown_memory** - Trade cooldown memory (duplicate)
6. **dynamic_profit_targets** - Dynamic targets (unused)
7. **alert_learning_loop** - Alert learning (unused)
8. **randomness_pattern_analyzer** - Randomness patterns (unused)

### **Brain Components Not Used**
1. **narrative_generator** - Story telling (unused)
2. **causal_counterfactual_engine** - What-if analysis (unused)
3. **emergent_order_theory** - Emergent patterns (unused)

## 🤔 **WHY Some Things Aren't Used**

### **Intentionally Disabled**
- **options_engine** - Options trading disabled in config
- **partnership_engine** - Set to None (not needed)
- **profit_exit_manager** - Profit maximization disabled

### **Duplicates/Redundancy**
- **robust_price_fetcher** - Have main price_fetcher
- **cooldown_memory** - Duplicate of trade_memory
- **multiple news engines** - NewsAPIIntegration handles all

### **Specialized/Unused Features**
- **backtest_engine** - Only for testing
- **weather engines** - Weather trading not active
- **geopolitical_engine** - Geopolitical analysis not integrated
- **many specialized engines** - Built for specific strategies not currently used

### **Brain Components Not Integrated**
- **narrative_generator** - Stories not needed for trading
- **causal_counterfactual** - What-if analysis not implemented
- **emergent_order_theory** - Complex pattern detection not used

## 📊 **Usage Summary**

- **Total Engines**: 159
- **Actively Used**: ~15
- **Conditionally Used**: ~5
- **Not Used**: ~139

- **Total Utils**: 88
- **Actively Used**: ~15
- **Not Used**: ~73

- **Total Brain Components**: 8
- **Actively Used**: 5
- **Not Used**: 3

## 💡 **Recommendations**

1. **Remove Unused Engines**: Delete 100+ unused engine files
2. **Archive Specialized Code**: Move to archive folder
3. **Clean Up Imports**: Remove unused imports
4. **Simplify System**: Keep only what's actually used
5. **Document Better**: Clearly mark what each component does

The system is extremely bloated with unused code that could be removed to improve clarity and performance.
