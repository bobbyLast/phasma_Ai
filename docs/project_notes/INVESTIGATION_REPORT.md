# PHASMA AI - FULL SYSTEM INVESTIGATION REPORT
**Date:** February 8, 2026  
**Scope:** Every active module, top to bottom  
**Goal:** Find what can be improved for fewer API pulls, better crash prediction (especially Bitcoin), more thorough analysis, and overall system efficiency

---

## EXECUTIVE SUMMARY

After investigating **65+ files** with **128 direct `yf.Ticker()` calls**, I found **7 critical issues** and **12 improvement opportunities**. The biggest problems are:

1. **Bitcoin crash prediction is fundamentally broken** - the on-chain analysis is a stub returning 0.5 (neutral) always
2. **~100+ redundant yfinance calls per cycle** across engines that don't use the new cache
3. **A bug: `refresh_cache()` is called in `run_full_cycle` but doesn't exist** in `MarketDataCache`
4. **Duplicate rate limiting** - `RobustPriceFetcher` applies TWO rate limits per call (its own + the global one)
5. **`_get_cached_price` in main.py doesn't use `MarketDataCache`** - it uses a separate `_price_cache` dict with `RobustPriceFetcher`
6. **Global Macro Monitor makes 6 unthrottled yfinance calls** every cycle with no cache
7. **Sentiment analysis is too simplistic** - just checks 14-day price change, doesn't use actual sentiment data

---

## SECTION 1: CRITICAL BUGS (Must Fix)

### BUG 1: `refresh_cache()` method does not exist
**File:** `utils/market_data_cache.py`  
**Called from:** `main.py` line 2135  
**Impact:** `run_full_cycle` calls `self.market_cache.refresh_cache()` but `MarketDataCache` has no such method. This will throw an `AttributeError` every cycle, caught by the try/except but meaning the cache never refreshes.  
**Fix:** Either add a `refresh_cache()` method to `MarketDataCache` (that calls `clear_cache()` + `fetch_macro_data(force_refresh=True)`), or change the call in `main.py` to use `clear_cache()` followed by `fetch_macro_data()`.

### BUG 2: Double rate limiting in `RobustPriceFetcher`
**File:** `utils/robust_price_fetcher.py` lines 77-78  
**Impact:** `_fetch_yfinance()` calls BOTH `self._rate_limit('yfinance')` (0.5s) AND `rate_limit()` (1.5s global). That's **2.0 seconds minimum per price fetch** - double what's needed. Every symbol fetched through `get_real_price()` pays this double penalty.  
**Fix:** Remove the local `self._rate_limit('yfinance')` call since the global `rate_limit()` already handles throttling.

### BUG 3: Two separate price caches competing
**File:** `main.py` line 523-537 (`_get_cached_price`) vs `utils/market_data_cache.py`  
**Impact:** `main.py` has its own `_price_cache` dict that goes through `RobustPriceFetcher`, completely separate from `MarketDataCache.fetch_prices()`. The affordable-items filter at line 2711 uses `_get_cached_price` (the old one), not the new `MarketDataCache`. This means prices are fetched twice through different paths.  
**Fix:** Unify `_get_cached_price` to check `self.market_cache` first, then fall back to `price_fetcher`.

---

## SECTION 2: BITCOIN / CRYPTO CRASH PREDICTION FAILURES

### ISSUE 1: On-chain analysis is a STUB (THE #1 REASON BITCOIN CRASHES ARE MISSED)
**File:** `engines/market_crash_detector_v2.py` lines 311-333  
**Impact:** `_analyze_onchain_flows()` literally returns `0.5` (neutral) every time. The comments say "placeholder" and list what SHOULD be fetched (whale movements, exchange flows, funding rates, stablecoin ratios, miner flow). But none of it is implemented. Since on-chain gets **25% weight** in the crash score, this permanently anchors 25% of the score at neutral, making it nearly impossible to reach HIGH_CRASH_RISK (0.55 threshold).  
**Fix:** Integrate real on-chain data APIs:
- **CryptoQuant** or **Glassnode** for exchange inflows/outflows (whales moving BTC to exchanges = sell signal)
- **Coinglass** for funding rates and open interest (high funding + high OI = liquidation cascade risk)
- **Alternative.me Fear & Greed Index** (free API) for crypto-specific sentiment
- At minimum, use yfinance to check BTC futures premium (BITO vs BTC-USD spread) as a leverage proxy

### ISSUE 2: Sentiment analysis doesn't use crypto-specific data
**File:** `engines/market_crash_detector_v2.py` lines 335-374  
**Impact:** `_analyze_sentiment()` only looks at 14-day price change and volatility. For Bitcoin, this misses:
- Social media sentiment (Twitter/X crypto sentiment)
- Fear & Greed Index (crypto-specific, free API)
- Google Trends for "bitcoin crash" or "sell bitcoin"
- Stablecoin market cap changes (USDT/USDC flows)
**Fix:** Add crypto-specific sentiment sources. The Fear & Greed Index alone (api.alternative.me) would dramatically improve crypto crash detection.

### ISSUE 3: Technical analysis uses stock-market indicators only
**File:** `engines/market_crash_detector_v2.py` lines 376-422  
**Impact:** Uses MACD, RSI, and 50-day MA. These work for stocks but miss crypto-specific patterns:
- **Funding rate divergence** (positive funding + falling price = imminent liquidation cascade)
- **Exchange reserve changes** (BTC leaving exchanges = bullish, entering = bearish)
- **Hash rate drops** (miner capitulation signals)
- **Realized price vs market price** (MVRV ratio - when market price >> realized price, correction likely)
**Fix:** Add crypto-specific technical indicators alongside existing ones. Weight them higher when analyzing crypto assets.

### ISSUE 4: Crash score weighting doesn't adapt to asset type
**File:** `engines/market_crash_detector_v2.py` lines 463-486  
**Impact:** The weights are fixed: macro 35%, on-chain 25%, sentiment 20%, technical 20%. For Bitcoin:
- On-chain should be **40-50%** (it's the most predictive for crypto)
- Macro should be **20-25%** (crypto is less macro-correlated than stocks)
- Sentiment should be **20-25%** (crypto is heavily sentiment-driven)
**Fix:** Make weights dynamic based on asset type (crypto vs stock vs ETF).

### ISSUE 5: Monte Carlo simulations are fake
**File:** `engines/market_crash_detector_v2.py` lines 877-917  
**Impact:** `_run_crash_simulations()` says it runs 500 simulations but actually just does `crash_score * 1.2` and `crash_score * 1.0` for tail probabilities. No actual Monte Carlo simulation runs. The comment says "In production, call actual simulation engine" but it never does, even though `self.simulation_engine` exists.  
**Fix:** Actually call `self.simulation_engine` to run real Monte Carlo simulations. The engine exists and is initialized.

---

## SECTION 3: REDUNDANT API CALLS (Efficiency)

### 40+ Active Files Still Making Direct yfinance Calls

**High-frequency callers (not using cache):**

| File | Calls | Impact |
|------|-------|--------|
| `engines/exit_optimizer.py` | 6 calls | Every exit check = 6 separate yfinance fetches for RSI, MACD, Bollinger, MA, ATR, volume |
| `brain/market_intelligence_engine.py` | 4 calls | Sector analysis + fundamentals + technicals + psychology |
| `engines/paper_trading_portfolio.py` | 4 calls | Open position pricing + unrealized P&L |
| `engines/insider_signal_integrator.py` | 3 calls | Price check + analyst data + P/E ratio |
| `engines/correlation_tracker.py` | 3 calls | Correlation matrix building |
| `engines/dynamic_market_scanner.py` | 3 calls | Market scanning |
| `services/confluence_service.py` | 3 calls | Budget filter + analysis |
| `utils/dynamic_profit_targets.py` | 3 calls | Target calculation |
| `utils/simulation_exit_manager.py` | 3 calls | Exit simulation |
| `engines/global_macro_monitor.py` | 1 call per indicator (6 indicators) | 6 unthrottled calls every cycle |
| `main.py` (`send_telegram_alert`) | 1 call | Fundamentals check for every alert |
| `main.py` (`_generate_investment_thesis`) | 1 call | Full `.info` fetch per stock |
| `brain/thematic_analysis_engine.py` | 1 call | Stock data + price per theme stock |
| `engines/news_engine_validation.py` | 3 calls | Validation checks |
| `utils/pe_ratio_analyzer.py` | 1 call | P/E analysis per stock |

**Estimated total per cycle:** A single `run_full_cycle` analyzing 20 stocks could make **100-200+ yfinance calls**, each with 1.5s throttle = **2.5 to 5+ minutes just waiting on rate limits**.

### Global Macro Monitor is completely unoptimized
**File:** `engines/global_macro_monitor.py` lines 116-153  
**Impact:** `update_indicators()` makes 6 separate `yf.Ticker().history()` calls (Japan 10Y, Japan 30Y, USD/JPY, Nikkei, US 10Y, Fed Funds) with NO rate limiting and NO cache. These overlap with `MarketDataCache` macro data (which already fetches VIX, DXY, US10Y, SPY).  
**Fix:** Integrate with `MarketDataCache`. Add Japan-specific symbols to the cache's macro fetch. Share the cache instance.

### Exit Optimizer makes 6 separate calls per position
**File:** `engines/exit_optimizer.py`  
**Impact:** Each method (`_check_rsi_exit`, `_check_macd_exit`, `_check_bollinger_exit`, `_check_ma_crossover`, `_check_atr_spike`, volume check) fetches history independently. For a portfolio with 5 positions, that's **30 yfinance calls** just for exit checking.  
**Fix:** Fetch history ONCE per symbol, pass the DataFrame to all indicator methods.

### Paper Trading Portfolio fetches prices in loops
**File:** `engines/paper_trading_portfolio.py` lines 448-500  
**Impact:** `_get_open_positions_details()` and `_update_unrealized_pnl()` both loop through positions making individual `yf.Ticker().history()` calls. If you have 10 positions, that's 20 calls.  
**Fix:** Use `MarketDataCache.fetch_prices()` to batch-fetch all position prices at once.

---

## SECTION 4: ANALYSIS DEPTH ISSUES

### PE Ratio Analyzer fetches independently
**File:** `utils/pe_ratio_analyzer.py`  
**Impact:** Called in the undervalued stock scan loop (line 2892 of main.py) for potentially 70+ symbols. Each call fetches `yf.Ticker(ticker).info` independently.  
**Fix:** Pass cached ticker info from `MarketDataCache`.

### Thesis Manager creates thesis for every undervalued stock
**File:** `main.py` line 2938  
**Impact:** For every undervalued stock found, `create_thesis()` is called. Even with the cache refactor, this triggers database writes and complex analysis. If 10 undervalued stocks are found, that's 10 thesis creations.  
**Fix:** Only create theses for stocks that pass ALL filters (undervalued + affordable + not recently traded).

### `send_telegram_alert` makes uncached yfinance call
**File:** `main.py` lines 1834-1842  
**Impact:** Every Telegram alert triggers `yf.Ticker(ticker).info` to check long-term fundamentals. This is uncached and unthrottled.  
**Fix:** Use `MarketDataCache.fetch_ticker_info()`.

### `_generate_investment_thesis` makes uncached yfinance call
**File:** `main.py` lines 2055-2124  
**Impact:** Every call to generate a thesis explanation fetches full `.info` from yfinance.  
**Fix:** Accept cached info as parameter, fall back to yfinance only if not provided.

---

## SECTION 5: ARCHITECTURAL IMPROVEMENTS

### 1. Centralize ALL data fetching through MarketDataCache
Currently, `MarketDataCache` is only used by 3 modules (crash detector, thesis manager, paper exits). **40+ other modules** still make direct calls. The cache should be the SINGLE source of truth.

**Recommendation:** Pass `market_cache` to every engine at initialization. Add a `get_or_fetch()` pattern so engines never call yfinance directly.

### 2. Pre-fetch all needed symbols at cycle start
Instead of fetching on-demand throughout the cycle, collect ALL symbols needed at the start of `run_full_cycle` and batch-fetch everything:
- Macro indicators (DXY, VIX, US10Y, SPY + Japan indicators)
- All watchlist symbols (prices + info)
- All open position symbols (prices)
- Popular stocks for fundamental scan

This could reduce a 200-call cycle to ~30-40 calls.

### 3. Use yfinance `download()` for batch price fetching
**Current:** `MarketDataCache.fetch_prices()` loops through symbols one at a time.  
**Better:** Use `yf.download(['AAPL', 'MSFT', 'GOOGL', ...], period='1d')` which fetches ALL symbols in a single HTTP request. This is the single biggest optimization available.

### 4. Add a "data freshness" tier system
Not all data needs to be equally fresh:
- **Real-time (< 1 min):** Current prices for trade execution
- **Near-real-time (< 10 min):** Prices for analysis and exit checks
- **Periodic (< 1 hour):** Macro indicators, sector data, fundamentals
- **Daily:** P/E ratios, analyst ratings, company info

### 5. Implement proper crypto data sources
For Bitcoin/crypto crash prediction, yfinance alone is insufficient. Need:
- **Free:** Alternative.me Fear & Greed API, CoinGecko API (free tier)
- **Paid (recommended):** CryptoQuant, Glassnode, or Coinglass for on-chain + derivatives data
- **Proxy indicators via yfinance:** BITO (BTC futures ETF), MSTR, MARA, COIN correlation

---

## SECTION 6: SIGNAL FLOW ISSUES

### 1. UnifiedMetaBrain creates a NEW instance every cycle
**File:** `main.py` line 2459  
**Impact:** `brain = UnifiedMetaBrain(self.config)` creates a fresh instance every `run_full_cycle`. This means no learning between cycles, no state persistence, and wasted initialization time.  
**Fix:** Initialize once in `__init__`, reuse across cycles.

### 2. Convergence engine gets duplicate signals
**File:** `main.py` lines 3020-3180  
**Impact:** The same stock can be added to the convergence engine from multiple sources (news, day trading, unified, insider, Kalshi) with slightly different formats. The convergence engine may count these as separate "sources" even though they originate from the same underlying data.

### 3. Undervalued stock scan hardcodes 20 popular stocks
**File:** `main.py` lines 2883-2885  
**Impact:** `popular_stocks = ['AAPL', 'MSFT', ...]` is hardcoded. These are mega-caps that will almost never be "undervalued" by P/E standards, wasting 20 yfinance calls per cycle.  
**Fix:** Remove hardcoded list. Only analyze stocks discovered from news/signals.

### 4. Day trading scanner runs BEFORE crash risk is fully assessed
**File:** `main.py` line 2578  
**Impact:** Day trading signals are generated before the crash assessment is complete. If a crash is detected, these signals should be suppressed or modified, but they're already generated.

---

## SECTION 7: PRIORITIZED ACTION PLAN

### Phase 1: Critical Fixes (Do First)
1. **Add `refresh_cache()` method** to `MarketDataCache` (or fix the call)
2. **Fix double rate limiting** in `RobustPriceFetcher`
3. **Unify `_get_cached_price`** to use `MarketDataCache` first
4. **Implement real on-chain analysis** for crypto (even basic Fear & Greed API)
5. **Make crash score weights dynamic** by asset type

### Phase 2: Efficiency (Reduce API Calls by 80%)
6. **Use `yf.download()` batch fetching** in `MarketDataCache.fetch_prices()`
7. **Integrate `GlobalMacroMonitor`** with `MarketDataCache`
8. **Refactor `ExitOptimizer`** to fetch history once per symbol
9. **Refactor `PaperTradingPortfolio`** to use cached prices
10. **Pass `market_cache` to all engines** at initialization

### Phase 3: Analysis Quality
11. **Add crypto-specific sentiment** (Fear & Greed Index API)
12. **Add crypto-specific technicals** (funding rate proxy, exchange flow proxy)
13. **Actually run Monte Carlo simulations** instead of fake calculations
14. **Remove hardcoded popular stocks** from undervalued scan
15. **Initialize UnifiedMetaBrain once**, reuse across cycles

### Phase 4: Architecture
16. **Pre-fetch all symbols at cycle start** (collect → batch fetch → distribute)
17. **Implement data freshness tiers** (real-time vs periodic vs daily)
18. **Add on-chain data API integration** (CryptoQuant/Glassnode/Coinglass)
19. **Add prediction accuracy tracking** (compare predictions to actual outcomes)

---

## APPENDIX: FILES INVESTIGATED

| File | Status | Issues Found |
|------|--------|-------------|
| `utils/market_data_cache.py` | Reviewed | Missing `refresh_cache()`, no batch download |
| `utils/yfinance_rate_limiter.py` | Reviewed | Working correctly |
| `utils/robust_price_fetcher.py` | Reviewed | Double rate limiting bug |
| `utils/thesis_manager.py` | Reviewed | Properly refactored (uses cache) |
| `utils/pe_ratio_analyzer.py` | Reviewed | Not using cache |
| `utils/dynamic_profit_targets.py` | Reviewed | Not using cache |
| `utils/simulation_exit_manager.py` | Reviewed | Not using cache |
| `engines/market_crash_detector_v2.py` | Reviewed | Stub on-chain, fake Monte Carlo, fixed weights |
| `engines/global_macro_monitor.py` | Reviewed | 6 unthrottled calls, no cache |
| `engines/exit_optimizer.py` | Reviewed | 6 calls per position, no cache |
| `engines/paper_trading_portfolio.py` | Reviewed | Loop fetching, no cache |
| `engines/insider_signal_integrator.py` | Reviewed | 3 calls per stock, no cache |
| `engines/correlation_tracker.py` | Reviewed | Not using cache |
| `engines/dynamic_market_scanner.py` | Reviewed | Not using cache |
| `engines/news_engine_validation.py` | Reviewed | Not using cache |
| `engines/human_validator.py` | Reviewed | Not using cache |
| `engines/iv_crush_predictor.py` | Reviewed | Not using cache |
| `engines/pump_dump_detector.py` | Reviewed | Not using cache |
| `engines/options_flow_filter.py` | Reviewed | Not using cache |
| `engines/day_trading_scanner.py` | Reviewed | Not using cache |
| `services/confluence_service.py` | Reviewed | Not using cache |
| `brain/market_intelligence_engine.py` | Reviewed | 4 calls, not using cache |
| `brain/thematic_analysis_engine.py` | Reviewed | Not using cache |
| `main.py` | Reviewed | Multiple issues (see above) |
| `unified_meta_brain.py` | Reviewed | No direct yfinance (clean) |

---

*End of Investigation Report*
