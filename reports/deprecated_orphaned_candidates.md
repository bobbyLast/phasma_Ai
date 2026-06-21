# Deprecated / Orphaned Candidates

Generated: 2026-06-21T03:28:29.192607+00:00

No files deleted or moved in this pass.

## Quarantine Recommendations


### ORPHANED_UNCALLED (15 items)

- **QUARANTINE** — `engines/microstructure_engine.py` `analysis = engine.analyze_microstructure_opportunity(opportunity)`
- **QUARANTINE** — `engines/self_calibrating_probability_engine.py` `calibration_data = self._analyze_calibration_curve(resolved_predictions)`
- **QUARANTINE** — `engines/undervalued_stock_scanner.py` `undervalued = scanner.find_undervalued_stocks(min_score=60)`
- **QUARANTINE** — `engines/undervalued_stock_scanner.py` `analysis = scanner.analyze_value_stock(undervalued[0]['symbol'])`
- **QUARANTINE** — `engines/undervalued_stock_scanner.py` `thesis = scanner.get_investment_thesis(undervalued[0])`
- **QUARANTINE** — `core/emergent_order_theory.py` `for pattern_name, detector in self.patterns.items():`
- **QUARANTINE** — `core/emergent_order_theory.py` `confidence = detector(data)`
- **QUARANTINE** — `utils/finnhub_screener.py` `deep_dive_candidates = filtered[:analyze_top]`
- **QUARANTINE** — `utils/galton_mindset.py` `analysis = self.theory.analyze_system_as_galton(returns_data, asset_name)`
- **QUARANTINE** — `utils/high_speed_async_fetcher.py` `'analyzed_count': len(detailed_data),`
- **QUARANTINE** — `utils/impact_analyzer.py` `price_analysis = self._analyze_price_runup(hist, catalyst_date, current_price)`
- **QUARANTINE** — `utils/impact_analyzer.py` `volume_analysis = self._analyze_volume_spike(hist, catalyst_date)`
- **QUARANTINE** — `utils/impact_analyzer.py` `global _impact_analyzer`
- **QUARANTINE** — `utils/impact_analyzer.py` `return _impact_analyzer`
- **QUARANTINE** — `utils/trader_performance_tracker.py` `'total_calls_analyzed': sum([p.total_calls for p in trader_perfs]),`

### ACTIVE_LEGACY (4 items)

- **MANUAL_REVIEW** — `utils/impact_analyzer.py` `"""Get the global impact analyzer instance"""`
- **MANUAL_REVIEW** — `utils/trader_performance_tracker.py` `Analyzes historical trader calls to calculate performance metrics and trust scores.`
- **MANUAL_REVIEW** — `utils/trader_performance_tracker.py` `call: The trader call to analyze`
- **MANUAL_REVIEW** — `scripts/inventory_analysis.py` `# Code-line banners that aren't stage headings`

### DEMO_ONLY (128 items)

- **KEEP (diagnostics only)** — `scripts/alternate_mains/main_performance_test.py` `PerformanceMonitor`
- **KEEP (diagnostics only)** — `scripts/alternate_mains/main_performance_test.py` `run_with_performance_monitoring`
- **KEEP (diagnostics only)** — `scripts/alternate_mains/main_performance_test.py` `start_monitoring`
- **KEEP (diagnostics only)** — `scripts/demos/demo_three_mind.py` `print("4. Expand universe of analyzed symbols")`
- **KEEP (diagnostics only)** — `scripts/demos/demo_value_investing.py` `undervalued = smart_strategy.value_scanner.find_undervalued_stocks(min_score=60)`
- **KEEP (diagnostics only)** — `scripts/demos/demo_value_investing.py` `'thesis': smart_strategy.value_scanner.get_investment_thesis(stock),`
- **KEEP (diagnostics only)** — `scripts/legacy/analyze_position_logic.py` `def analyze_position_logic():`
- **KEEP (diagnostics only)** — `scripts/legacy/analyze_position_logic.py` `analyze_position_logic()`
- **KEEP (diagnostics only)** — `scripts/legacy/check_integration.py` `# 3. Check if undervalued_stock_scanner.py exists`
- **KEEP (diagnostics only)** — `scripts/legacy/check_integration.py` `if os.path.exists("engines/undervalued_stock_scanner.py"):`
- **KEEP (diagnostics only)** — `scripts/legacy/check_integration.py` `print("✅ Undervalued stock scanner exists")`
- **KEEP (diagnostics only)** — `scripts/legacy/check_integration.py` `print("❌ Undervalued stock scanner missing!")`
- **KEEP (diagnostics only)** — `scripts/legacy/cleanup_root.py` `'unified_main.py',`
- **KEEP (diagnostics only)** — `scripts/legacy/cleanup_root.py` `'ultimate_easy_trade_detector.py',`
- **KEEP (diagnostics only)** — `scripts/legacy/cleanup_root.py` `'ultimate_easy_trade_detector_all_categories.py',`
- **KEEP (diagnostics only)** — `scripts/legacy/cleanup_root.py` `'analyze_archived_engines.py',`
- **KEEP (diagnostics only)** — `scripts/legacy/cleanup_root.py` `'analyze_usage.py',`
- **KEEP (diagnostics only)** — `scripts/legacy/cleanup_root.py` `'unified_main_results.json'`
- **KEEP (diagnostics only)** — `scripts/legacy/clean_main_performance.py` `'phases': {},`
- **KEEP (diagnostics only)** — `scripts/legacy/clean_main_performance.py` `# Phase 1: Configuration`
- **KEEP (diagnostics only)** — `scripts/legacy/clean_main_performance.py` `print("\n[PHASE 1] Loading configuration...")`
- **KEEP (diagnostics only)** — `scripts/legacy/clean_main_performance.py` `phase_start = time.time()`
- **KEEP (diagnostics only)** — `scripts/legacy/clean_main_performance.py` `phase_time = time.time() - phase_start`
- **KEEP (diagnostics only)** — `scripts/legacy/clean_main_performance.py` `metrics['phases']['config'] = phase_time`
- **KEEP (diagnostics only)** — `scripts/legacy/clean_main_performance.py` `print(f"   Configuration loaded in {phase_time:.2f}s")`
- **KEEP (diagnostics only)** — `scripts/legacy/clean_main_performance.py` `# Phase 2: Data Integration`
- **KEEP (diagnostics only)** — `scripts/legacy/clean_main_performance.py` `print("\n[PHASE 2] Initializing data integration...")`
- **KEEP (diagnostics only)** — `scripts/legacy/clean_main_performance.py` `metrics['phases']['initialization'] = phase_time`
- **KEEP (diagnostics only)** — `scripts/legacy/clean_main_performance.py` `print(f"   Integration initialized in {phase_time:.2f}s")`
- **KEEP (diagnostics only)** — `scripts/legacy/clean_main_performance.py` `# Phase 3: Data Fetching`
- **KEEP (diagnostics only)** — `scripts/legacy/clean_main_performance.py` `print("\n[PHASE 3] Fetching data from all sources...")`
- **KEEP (diagnostics only)** — `scripts/legacy/clean_main_performance.py` `metrics['phases']['data_fetch'] = phase_time`
- **KEEP (diagnostics only)** — `scripts/legacy/clean_main_performance.py` `print(f"   Data fetched in {phase_time:.2f}s")`
- **KEEP (diagnostics only)** — `scripts/legacy/clean_main_performance.py` `# Phase 5: Results Processing`
- **KEEP (diagnostics only)** — `scripts/legacy/clean_main_performance.py` `print("\n[PHASE 5] Processing results...")`
- **KEEP (diagnostics only)** — `scripts/legacy/clean_main_performance.py` `'phases': metrics['phases'],`
- **KEEP (diagnostics only)** — `scripts/legacy/clean_main_performance.py` `metrics['phases']['results_processing'] = phase_time`
- **KEEP (diagnostics only)** — `scripts/legacy/clean_main_performance.py` `print(f"   Results processed in {phase_time:.2f}s")`
- **KEEP (diagnostics only)** — `scripts/legacy/clean_main_performance.py` `print(f"\nPHASE BREAKDOWN:")`
- **KEEP (diagnostics only)** — `scripts/legacy/clean_main_performance.py` `for phase, duration in metrics['phases'].items():`
- **KEEP (diagnostics only)** — `scripts/legacy/clean_main_performance.py` `print(f"   {phase}: {duration:.2f}s ({percentage:.1f}%)")`
- **KEEP (diagnostics only)** — `scripts/legacy/complete_system_demo.py` `print("\n📊 PHASE 6: SYSTEM METRICS")`
- **KEEP (diagnostics only)** — `scripts/legacy/complete_system_summary.py` `🧠 PHASMA AI - UNIFIED META BRAIN COMPLETE`
- **KEEP (diagnostics only)** — `scripts/legacy/complete_system_summary.py` `1. 🧠 UNIFIED META BRAIN (The Orchestrator)`
- **KEEP (diagnostics only)** — `scripts/legacy/complete_system_summary.py` `- Runs 5-phase analysis:`
- **KEEP (diagnostics only)** — `scripts/legacy/complete_system_summary.py` `• Phase 2: Intelligence Gathering (All systems in parallel)`
- **KEEP (diagnostics only)** — `scripts/legacy/complete_system_summary.py` `2. 📊 INTELLIGENCE SYSTEMS (All Working Together):`
- **KEEP (diagnostics only)** — `scripts/legacy/complete_system_summary.py` `- All intelligence systems run simultaneously`
- **KEEP (diagnostics only)** — `scripts/legacy/complete_system_summary.py` `Example of Unified Brain in Action:`
- **KEEP (diagnostics only)** — `scripts/legacy/complete_system_summary.py` `The AI is now a TRUE trading intelligence system:`
- ... and 78 more