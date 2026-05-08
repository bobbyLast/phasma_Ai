# AI Rework Blueprint (Performance-First)

## Goal
Improve decision throughput and reduce cycle latency before signal processing while preserving current strategy behavior.

## Current Hot Path
- Entry: `main.py` -> `PhasmaTradingSystem.run_full_cycle()`
- Runtime now prints stage timings under `[CYCLE PROFILE]`.

## Phase Plan

### Phase 1 (implemented)
- Added stage timing instrumentation in `run_full_cycle()`:
  - `preflight_and_risk`
  - `signal_generation`
  - `display_and_secondary_scans`
  - `arbitration_and_execution`
- Output is printed every cycle for quick bottleneck identification.

### Phase 2 (safe structural refactor)
Split `run_full_cycle()` into internal stage methods without changing logic:
- `_stage_preflight_and_risk()`
- `_stage_signal_generation()`
- `_stage_display_and_secondary_scans()`
- `_stage_arbitration_and_execution()`

Progress:
- ✅ `_stage_startup_services()` extracted.
- ✅ `_stage_macro_and_fred()` extracted.
- ✅ `_stage_crash_preflight()` extracted.
- ⏳ Remaining: extract signal generation/display/arbitration sections into dedicated methods.

Benefits:
- Easier optimization and testing.
- Smaller blast radius when changing one section.

### Phase 3 (latency wins)
1. Ensure one canonical fetch pass per cycle:
   - Single news snapshot
   - Single macro snapshot
   - Single price snapshot context
2. Remove duplicate scans in same cycle.
3. Route all market reads through `MarketDataCache` consistently.

Progress:
- ✅ Reused cycle news snapshot in secondary scan block (avoids duplicate full news scan).
- ✅ Cache-first reconciliation pricing (`fetch_prices` batch + fallback).
- ✅ Cache-first batch pricing added in social symbol enrichment and undervalued scan flow.

### Phase 4 (parallelization)
1. Introduce bounded concurrency for network-heavy tasks:
   - news source fan-out
   - options chain retrieval
2. Keep hard timeout budgets per source.
3. Keep fallback behavior unchanged.

## File-Level Execution Order
1. `main.py` (stage extraction only)
2. `engines/news_engine_core.py` (single-pass scan context)
3. `engines/news_engine_integrated.py` (remove blocking patterns in async paths)
4. `engines/options_engine.py` (bounded concurrent chain fetch)
5. `utils/market_data_cache.py` (enforce cache-only reads in hot loops)

## Guardrails
- No strategy threshold changes during performance phases.
- No feature removals in first two phases.
- Each phase must pass:
  - `python -m py_compile` on touched files
  - runtime smoke test (`python main.py`)
  - no new `ERROR` lines in startup cycle logs.

## Rollback Strategy
- Keep each phase as isolated commits.
- If behavior changes unexpectedly, revert only the latest phase.
- Stage timing output remains as baseline telemetry.

