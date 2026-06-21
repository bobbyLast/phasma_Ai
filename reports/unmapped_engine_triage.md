# Unmapped Engine Triage Report

Generated: 2026-06-21T03:28:29.192607+00:00

## UNMAPPED TRIAGE SUMMARY

- **Starting unmapped:** 530
- **Utility/not-engine:** 88
- **Duplicate aliases:** 37
- **Active current:** 257
- **Active legacy:** 4
- **Replaced by new engine:** 0
- **Orphaned uncalled:** 15
- **Demo only:** 128
- **Test only:** 1
- **Unknown needs review:** 0
- **Final unmapped remaining:** 0

## Deduped Inventory Quality

- **raw_items_found:** 5676
- **unique_log_banners:** 4853
- **unique_source_symbols:** 5194
- **unique_logical_engines:** 3753
- **utilities_excluded:** 88
- **duplicates_merged:** 37
- **unmapped_remaining:** 0

## TOP PRIORITY UNMAPPED (High Risk)

- `# Phase 6: Summary` (scripts/legacy/live_trading_cycle.py:217) — **DEMO_ONLY** → Deprecated (action: QUARANTINE — legacy demo script, not in main path, confidence: 95%)
- `updated_position = s.day_trading_scanner.calculate_position_size(` (main.py:3131) — **ACTIVE_CURRENT** → ReportingGroup (action: MAP_TO_GROUP, confidence: 82%)
- `'regulatory_approval', 'patent_approval', 'phase_advancement'` (utils/moon_shot_detector.py:42) — **ACTIVE_CURRENT** → Utility (action: MAP_TO_GROUP, confidence: 82%)

## Classification Breakdown

- **ACTIVE_CURRENT:** 257
- **DEMO_ONLY:** 128
- **UTILITY_NOT_ENGINE:** 88
- **DUPLICATE_ALIAS:** 37
- **ORPHANED_UNCALLED:** 15
- **ACTIVE_LEGACY:** 4
- **TEST_ONLY:** 1

## Sample: Active Current (mapped to groups)

- `unified_config = {` → **ReportingGroup** (main.py) callers: main.py
- `intelligence_strength = float(intelligence_strength) if intelligence_strength is not None else None` → **ReportingGroup** (main.py) callers: group_coordinator.py, main.py, supervisor.py
- `intelligence_strength = None` → **ReportingGroup** (main.py) callers: group_coordinator.py, main.py, supervisor.py
- `meta_parts.append(f"Intel: {intelligence_strength:.0f}/100")` → **ReportingGroup** (main.py) callers: main.py
- `print("\n🧠 UNIFIED META BRAIN ACTIVATED")` → **ReportingGroup** (main.py) callers: main.py, workers.py
- `brain = s._unified_brain` → **ReportingGroup** (main.py) callers: main.py
- `'source': 'UnifiedMetaBrain',` → **ReportingGroup** (main.py) callers: main.py, workers.py
- `s._display_unified_results(regular_trades, overnight_moonshots, ctx=ctx)` → **ReportingGroup** (main.py) callers: main.py
- `high_confidence_approved = self._stage_apply_platform_limits(ctx, high_confidence_approved)` → **ReportingGroup** (main.py) callers: main.py
- `pro_data = pro_analyzer.get_robinhood_style_chain(symbol, days_out=30)` → **ReportingGroup** (main.py) callers: main.py
- `# Analyze conviction watchlist for dip buying opportunities` → **ReportingGroup** (main.py) callers: main.py
- `updated_position = s.day_trading_scanner.calculate_position_size(` → **ReportingGroup** (main.py) callers: main.py
- `symbols_to_analyze = set()` → **ReportingGroup** (main.py) callers: main.py
- `symbols_to_analyze.add(symbol)` → **ReportingGroup** (main.py) callers: main.py
- `print(f"   🔍 Analyzing {len(symbols_to_analyze)} stocks for value opportunities...")` → **ReportingGroup** (main.py) callers: main.py
- `pe_analysis = s.pe_analyzer.analyze_pe_ratio(symbol)` → **ReportingGroup** (main.py) callers: main.py
- `ctx.track_symbol(symbol, "unified_analysis")` → **ReportingGroup** (main.py) callers: main.py
- `sports_opportunities = s.sports_odds_api.analyze_betting_opportunities()` → **ReportingGroup** (main.py) callers: main.py
- `'unified_confidence': confidence_val,` → **ReportingGroup** (main.py) callers: main.py
- `unified_results = s.unified_system.run_unified_analysis()` → **ReportingGroup** (main.py) callers: main.py
- `'source': 'unified_trading',` → **ReportingGroup** (main.py) callers: main.py
- `'source': 'unified_thesis',` → **ReportingGroup** (main.py) callers: main.py
- `s.unified_system.run_active_management()` → **ReportingGroup** (main.py) callers: main.py
- `fresh_opportunities = scanner.get_fresh_opportunities(total_limit=25)` → **ReportingGroup** (main.py) callers: main.py
- `'engines_used': [sig.get('source', 'UNIFIED_ANALYSIS')],` → **ReportingGroup** (main.py) callers: main.py
- `"""Run complete unified trading cycle with all analysis methods"""` → **ReportingGroup** (main.py) callers: main.py
- `ctx = ApplicationContext.bind(self, cycle_stage_timings)` → **ReportingGroup** (main.py) callers: main.py
- `_stage_start = time.perf_counter()` → **ReportingGroup** (main.py) callers: main.py
- `print("\n--- STAGE: preflight ---")` → **ReportingGroup** (main.py) callers: main.py
- `cycle_stage_timings[_stage_name] = time.perf_counter() - _stage_start` → **ReportingGroup** (main.py) callers: main.py
- `_stage_name = "display_and_secondary_scans"` → **ReportingGroup** (main.py) callers: main.py
- `print("\n--- STAGE: secondary scans ---")` → **ReportingGroup** (main.py) callers: main.py
- `print("\n--- STAGE: filter & execute ---")` → **ReportingGroup** (main.py) callers: main.py
- `unified_confidence = (` → **ReportingGroup** (main.py) callers: main.py
- `unified_confidence = unified_confidence * volume_multiplier + investment_boost` → **ReportingGroup** (main.py) callers: main.py
- `unified_confidence = min(0.95, unified_confidence)  # Cap at 95%` → **ReportingGroup** (main.py) callers: main.py
- `unified_confidence = min(0.95, unified_confidence + rb)` → **ReportingGroup** (main.py) callers: main.py
- `unified_confidence = max(min_confidence, unified_confidence)` → **ReportingGroup** (main.py) callers: main.py
- `unified_confidence = max(0.35, unified_confidence)  # Min 35% confidence` → **ReportingGroup** (main.py) callers: main.py
- `unified_confidence *= 1.0 + 0.15 * latent_score` → **ReportingGroup** (main.py) callers: main.py
- `unified_confidence *= 1.0 - 0.1 * latent_score` → **ReportingGroup** (main.py) callers: main.py
- `unified_confidence = max(0.01, min(0.99, unified_confidence))` → **ReportingGroup** (main.py) callers: main.py
- `'confidence': unified_confidence,` → **ReportingGroup** (main.py) callers: main.py
- `initial_confidence = unified_confidence` → **ReportingGroup** (main.py) callers: main.py
- `'rationale': f"UNIFIED Analysis: {', '.join(patterns)} patterns + {divergence_analysis['divergence_score']:.1%} divergen` → **ReportingGroup** (main.py) callers: main.py
- `'source': 'UNIFIED_ANALYSIS',` → **ReportingGroup** (main.py) callers: main.py
- `'unified_confidence': unified_confidence,` → **ReportingGroup** (main.py) callers: main.py
- `"""Display unified results with regular trades and overnight moonshots"""` → **ReportingGroup** (main.py) callers: main.py

## Sample: Orphaned / Replaced

- `analysis = engine.analyze_microstructure_opportunity(opportunity)` (engines/microstructure_engine.py) — ORPHANED_UNCALLED
- `calibration_data = self._analyze_calibration_curve(resolved_predictions)` (engines/self_calibrating_probability_engine.py) — ORPHANED_UNCALLED
- `undervalued = scanner.find_undervalued_stocks(min_score=60)` (engines/undervalued_stock_scanner.py) — ORPHANED_UNCALLED
- `analysis = scanner.analyze_value_stock(undervalued[0]['symbol'])` (engines/undervalued_stock_scanner.py) — ORPHANED_UNCALLED
- `thesis = scanner.get_investment_thesis(undervalued[0])` (engines/undervalued_stock_scanner.py) — ORPHANED_UNCALLED
- `for pattern_name, detector in self.patterns.items():` (core/emergent_order_theory.py) — ORPHANED_UNCALLED
- `confidence = detector(data)` (core/emergent_order_theory.py) — ORPHANED_UNCALLED
- `deep_dive_candidates = filtered[:analyze_top]` (utils/finnhub_screener.py) — ORPHANED_UNCALLED
- `analysis = self.theory.analyze_system_as_galton(returns_data, asset_name)` (utils/galton_mindset.py) — ORPHANED_UNCALLED
- `'analyzed_count': len(detailed_data),` (utils/high_speed_async_fetcher.py) — ORPHANED_UNCALLED
- `price_analysis = self._analyze_price_runup(hist, catalyst_date, current_price)` (utils/impact_analyzer.py) — ORPHANED_UNCALLED
- `volume_analysis = self._analyze_volume_spike(hist, catalyst_date)` (utils/impact_analyzer.py) — ORPHANED_UNCALLED
- `global _impact_analyzer` (utils/impact_analyzer.py) — ORPHANED_UNCALLED
- `return _impact_analyzer` (utils/impact_analyzer.py) — ORPHANED_UNCALLED
- `'total_calls_analyzed': sum([p.total_calls for p in trader_perfs]),` (utils/trader_performance_tracker.py) — ORPHANED_UNCALLED