# ENGINES STATUS - Based on main.py imports

# ACTUALLY USED ENGINES (15 engines)
used_engines = [
    "options_engine.py",              # DISABLED but imported
    "investment_news_scanner.py",     # ACTIVE
    "signal_convergence_engine.py",   # ACTIVE
    "thematic_analysis_engine.py",    # ACTIVE
    "pump_dump_detector.py",          # ACTIVE ✅ NEW
    "global_macro_monitor.py",        # ACTIVE ✅ NEW
    "insider_signal_integrator.py",   # ACTIVE ✅ NEW
    "market_intelligence_engine.py",  # ACTIVE
    "monte_carlo_engine.py",          # ACTIVE
    "crash_profit_engine.py",         # DISABLED
    "day_trading_scanner.py",         # ACTIVE
    "market_crash_detector_v2.py",    # ACTIVE
    "kalshi_engine.py",               # ACTIVE
    "news_collection_network.py",     # ACTIVE
    "partnership_engine/",            # ACTIVE (has issues)
]

# UNUSED ENGINES (55 engines) - These can be safely archived
unused_engines = [
    "auto_exit_manager.py",
    "backtest_engine.py",
    "calendar_seasonality_engine.py",
    "causal_counterfactual_engine.py",
    "corporate_actions_engine.py",
    "correlation_tracker.py",
    "cross_venue_radar.py",
    "earnings_drift_engine.py",
    "earnings_scanner.py",
    "event_structure_engine.py",
    "exit_optimizer.py",
    "finnhub_news.py",
    "geopolitical_engine.py",
    "macro_calendar_engine.py",
    "market_regime.py",
    "market_scanner_24_7.py",
    "microstructure_engine.py",
    "moonshot_keywords.py",
    "narrative_generator.py",
    "news_engine_analysis.py",
    "news_engine_apis.py",
    "news_engine_core.py",
    "news_engine_utils.py",
    "news_engine_validation.py",
    "news_memory_bank.py",
    "pricing_sources.py",
    "range_barrier_engine.py",
    "risk_engine.py",
    "risk_guardian_meta_agent.py",
    "scenario_graph_engine.py",
    "self_calibrating_probability_engine.py",
    "smart_monte_carlo.py",
    "social_engine/",
    "sports_analysis_engine.py",
    "spread_builder.py",
    "strike_expiry_selector.py",
    "top_10_dashboard.py",
    "trade_analyzer/",
    "volatility_edge_engine.py",
    "weather_engine.py",
    "weather_validation_engine.py",
    "long_tier/",
]

print("=== ENGINES CLEANUP REPORT ===")
print(f"\nUSED ENGINES: {len(used_engines)}")
for e in used_engines:
    print(f"  ✅ {e}")

print(f"\nUNUSED ENGINES: {len(unused_engines)}")
for e in unused_engines:
    print(f"  ❌ {e}")

print(f"\nSUMMARY:")
print(f"  Total engines: {len(used_engines) + len(unused_engines)}")
print(f"  Used: {len(used_engines)} ({len(used_engines)/(len(used_engines) + len(unused_engines))*100:.1f}%)")
print(f"  Unused: {len(unused_engines)} ({len(unused_engines)/(len(used_engines) + len(unused_engines))*100:.1f}%)")
print(f"\nRECOMMENDATION: Archive {len(unused_engines)} unused engines to clean up codebase")
