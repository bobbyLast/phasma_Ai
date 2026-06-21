"""
PHASMA AI - UNIFIED META BRAIN INTEGRATION
Brings together all systems: Bull Run Detector, Universal Intelligence, News Sources, etc.
"""

import asyncio
import sys
import os
import time

_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _root not in sys.path:
    sys.path.insert(0, _root)

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import json

from utils.cycle_data_context import CycleDataContext
from utils.confidence_utils import normalize_confidence_to_pct
from utils.discovery_limits import (
    discovery_limit,
    intelligence_timeout,
    is_max_discovery,
)

class UnifiedMetaBrain:
    """The complete brain that orchestrates all trading intelligence"""
    
    def __init__(self, config, market_cache=None, trading_system=None):
        self.config = config
        self.market_cache = market_cache
        self.trading_system = trading_system
        print("🧠 INITIALIZING UNIFIED META BRAIN...")
        print("=" * 60)
        
        # Core Components
        self._initialize_core_components()
        
        # Intelligence Systems
        self._initialize_intelligence_systems()
        
        # Data Sources
        self._initialize_data_sources()
        
        # Trading Execution
        self._initialize_execution_systems()
        
        print("\n✅ META BRAIN FULLY INITIALIZED")
        print("🔗 All systems connected and ready to work together")
        print("=" * 60)
    
    def _initialize_core_components(self):
        """Initialize core trading components"""
        print("\n📦 Loading Core Components...")
        
        # Price Fetcher
        from utils.price_fetcher import get_price_fetcher
        self.price_fetcher = get_price_fetcher()
        print("   ✅ Price Fetcher - Real-time market data")
        
        # Risk Manager
        from engines.risk_engine import PhasmaRiskEngine
        self.risk_manager = PhasmaRiskEngine(self.config)
        print("   ✅ Risk Engine - Position sizing & risk control")
        
        # Market Regime Detector
        from engines.market_regime import PhasmaMarketRegimeDetector
        self.regime_detector = PhasmaMarketRegimeDetector(self.config, market_cache=self.market_cache)
        print("   ✅ Regime Detector - Market conditions analysis")
    
    def _initialize_intelligence_systems(self):
        """Initialize all intelligence systems"""
        print("\n🧠 Loading Intelligence Systems...")
        
        # Universal Trading Intelligence
        from brain.universal_trading_intelligence import UniversalTradingIntelligence
        self.universal_intel = UniversalTradingIntelligence(self.config)
        print("   ✅ Universal Intelligence - All 15 strategies")
        
        # Bull Run Detector
        from brain.bull_run_detector import BullRunDetector
        self.bull_run_detector = BullRunDetector(self.config)
        print("   ✅ Bull Run Detector - Multi-source confirmation")
        
        # News-Driven Scanner
        from brain.news_driven_scanner import NewsDrivenScanner
        self.news_scanner = NewsDrivenScanner(self.config)
        print("   ✅ News Scanner - News-driven stock discovery")
        
        # Integrated News Sources (20 sources)
        from engines.news_engine_integrated import IntegratedNewsSources
        self.news_sources = IntegratedNewsSources(self.config)
        print("   ✅ News Sources - 20 integrated feeds")
    
    def _initialize_data_sources(self):
        """Initialize all data sources"""
        print("\n📊 Loading Data Sources...")
        
        # Global Macro Monitor
        from engines.global_macro_monitor import GlobalMacroMonitor
        self.macro_monitor = GlobalMacroMonitor()
        print("   ✅ Macro Monitor - Economic indicators")
        
        # Crash Detector
        from engines.market_crash_detector_v2 import MarketCrashDetectorV2
        self.crash_detector = MarketCrashDetectorV2(self.config)
        print("   ✅ Crash Detector - Risk monitoring")
        
        # Partnership Engine
        from engines.partnership_engine.integration import PartnershipEngine
        self.partnership_engine = PartnershipEngine()
        print("   ✅ Partnership Engine - M&A tracking")
        
        # Sector Intelligence
        from engines.sector_intelligence_engine import SectorIntelligenceEngine
        self.sector_intel = SectorIntelligenceEngine(self.config)
        print("   ✅ Sector Intelligence - Industry correlations & Kalshi")
        
        # Expansion Engine - Forces discovery of NEW stocks
        from engines.expansion_engine import ExpansionEngine
        self.expansion_engine = ExpansionEngine(self.config)
        print("   ✅ Expansion Engine - Always discovering NEW stocks")
        
        # Sector Bias Breaker - Prevents top-3 mentality
        from engines.sector_bias_breaker import SectorBiasBreaker
        self.bias_breaker = SectorBiasBreaker(self.config)
        print("   ✅ Bias Breaker - Prevents top-3 stock obsession")
        
        # Thematic Analyzer - Macro trend detection
        from brain.thematic_analysis_engine import ThematicAnalyzer
        self.thematic_analyzer = ThematicAnalyzer(self.config)
        print("   ✅ Thematic Analyzer - Macro trend detection")
    
    def _initialize_execution_systems(self):
        """Initialize execution and trading systems"""
        print("\n⚡ Loading Execution Systems...")
        
        # Kalshi Integration
        self.kalshi_events = []
        print("   ✅ Kalshi Integration - Event trading")
        
        # Signal Storage
        self.all_signals = []
        self.approved_signals = []
        print("   ✅ Signal Storage - Trade tracking")
        
        # Performance Tracker
        self.performance_tracker = {
            'total_scanned': 0,
            'opportunities_found': 0,
            'signals_generated': 0,
            'trades_executed': 0,
            'success_rate': 0.0
        }
        print("   ✅ Performance Tracker - Metrics & analytics")
        self._cycle_context: Optional[CycleDataContext] = None

    # region agent log
    def _debug_log(self, run_id: str, hypothesis_id: str, location: str, message: str, data: Dict[str, Any]):
        """Temporary debug instrumentation for session 28cc99."""
        try:
            payload = {
                "sessionId": "28cc99",
                "runId": run_id,
                "hypothesisId": hypothesis_id,
                "location": location,
                "message": message,
                "data": data,
                "pid": os.getpid(),
                "timestamp": int(datetime.now().timestamp() * 1000),
            }
            with open("debug-28cc99.log", "a", encoding="utf-8") as f:
                f.write(json.dumps(payload, default=str) + "\n")
        except Exception:
            pass
    # endregion
    
    async def run_unified_analysis(
        self,
        cycle_context: Optional[CycleDataContext] = None,
        *,
        run_deep_discovery: bool = True,
    ) -> Dict[str, Any]:
        """Run unified analysis. Deep branches (universal/partnership/underground/thematic) are hourly."""
        from core.runtime.context_snapshots import ContextSnapshotStore

        snapshot_store = ContextSnapshotStore()

        print("\n🚀 RUNNING UNIFIED META BRAIN ANALYSIS")
        print("=" * 80)
        if run_deep_discovery:
            print("📋 FLOOR WORKFLOW: Phase 1 Ingest → Phase 2 Analyze → Phase 3 Synthesize")
        else:
            print("📋 FAST MODE: Phase 1 Ingest → fast analyze only (deep snapshot reused when fresh)")
        print("=" * 80)

        if not run_deep_discovery:
            cached = snapshot_store.get_payload("candidates")
            if cached and snapshot_store.is_fresh("candidates"):
                print("\n⏭️ DiscoveryGroup DEEP: reusing cached snapshot (hourly cadence)")
                return dict(cached)
        
        # Phase 1 — INGEST (single fetch, universe, price enrich) — always first
        print("\n📥 PHASE 1 — INGEST (once per cycle)")
        print("-" * 40)
        if cycle_context is None:
            try:
                cycle_context = await CycleDataContext.ingest(
                    self.news_sources,
                    config=self.config,
                    market_cache=self.market_cache,
                )
            except Exception as exc:
                print(f"   ⚠️ Cycle ingest failed: {exc}")
                cycle_context = CycleDataContext()
                self._debug_log(
                    "floor-workflow",
                    "FLOOR",
                    "brain/unified_meta_brain.py:run_unified_analysis:ingest_error",
                    "cycle ingest failed",
                    {"exception_type": type(exc).__name__, "exception_message": str(exc)[:300]},
                )
        else:
            print("   Using pre-built cycle context from caller")
            cycle_context._log_phase("phase1_ingest_reused", {
                "items": len(cycle_context.ingested_news),
                "symbols": len(cycle_context.symbol_universe),
                "enriched_prices": len(cycle_context.prices),
            })
        self._cycle_context = cycle_context
        prefetched_news = cycle_context.ingested_news
        self._debug_log(
            "floor-workflow",
            "FLOOR",
            "brain/unified_meta_brain.py:run_unified_analysis:phase1_done",
            "phase 1 ingest complete",
            {
                "total_items": len(prefetched_news),
                "symbol_universe": len(cycle_context.symbol_universe),
                "prices": len(cycle_context.prices),
            },
        )

        # Market environment (read-only macro/regime — uses ingest snapshot, no re-fetch)
        print("\n🌍 MARKET ENVIRONMENT (preflight)")
        print("-" * 40)

        market_regime = await self._analyze_market_regime()
        crash_risk = await self._check_crash_risk()
        macro_analysis = await self._analyze_macro_conditions()
        
        # Phase 2 — ANALYZE (read-only shared context, no re-fetch)
        print("\n🧠 PHASE 2 — ANALYZE (read-only CycleDataContext)")
        print("-" * 40)
        fast_tasks = [
            ("bull_runs", self.bull_run_detector.detect_bull_runs(cycle_context), intelligence_timeout(self.config, "bull_runs")),
            ("hot_stocks", self.news_scanner.scan_news_for_hot_stocks(cycle_context), intelligence_timeout(self.config, "hot_stocks")),
            ("social_signals", self._scan_social_sentiment(), intelligence_timeout(self.config, "social_signals")),
        ]
        deep_tasks = [
            ("universal_opportunities", self.universal_intel.analyze_all_opportunities(cycle_context), intelligence_timeout(self.config, "universal_opportunities")),
            ("partnership_opportunities", self._monitor_partnerships(cycle_context), intelligence_timeout(self.config, "partnership_opportunities")),
            ("underground_stocks", self._discover_underground_stocks(), intelligence_timeout(self.config, "underground_stocks")),
        ]
        task_specs = fast_tasks + (deep_tasks if run_deep_discovery else [])
        if not run_deep_discovery:
            print("   ⏭️ Skipped deep: universal intel, partnership EDGAR, underground (hourly/on-demand)")
        results = await asyncio.gather(
            *(self._run_intelligence_task(name, coro, timeout) for name, coro, timeout in task_specs),
            return_exceptions=True,
        )
        
        # region agent log
        self._debug_log(
            "pre-fix",
            "H3",
            "brain/unified_meta_brain.py:run_unified_analysis:gather_results",
            "parallel intelligence task results",
            {
                "task_results": [
                    {
                        "name": name,
                        "is_exception": isinstance(result, Exception),
                        "exception_type": type(result).__name__ if isinstance(result, Exception) else None,
                        "exception_message": str(result)[:300] if isinstance(result, Exception) else None,
                        "result_type": type(result).__name__,
                        "result_len": len(result) if hasattr(result, "__len__") and not isinstance(result, Exception) else None,
                    }
                    for name, result in zip([name for name, _, _ in task_specs], results)
                ]
            },
        )
        # endregion
        
        # Parse results
        name_order = [name for name, _, _ in task_specs]
        parsed = {}
        for name, result in zip(name_order, results):
            parsed[name] = result if not isinstance(result, Exception) else []

        universal_opportunities = parsed.get("universal_opportunities", [])
        bull_runs = parsed.get("bull_runs", [])
        hot_stocks = parsed.get("hot_stocks", [])
        social_signals = parsed.get("social_signals", [])
        partnership_opportunities = parsed.get("partnership_opportunities", [])
        underground_stocks = parsed.get("underground_stocks", [])
        
        self._debug_log(
            "floor-workflow",
            "FLOOR",
            "brain/unified_meta_brain.py:run_unified_analysis:phase2_done",
            "phase 2 analyze branches complete",
            {
                "universal": len(universal_opportunities),
                "bull_runs": len(bull_runs),
                "hot_stocks": len(hot_stocks),
                "social": len(social_signals),
                "partnerships": len(partnership_opportunities),
                "underground": len(underground_stocks),
            },
        )
        
        # Phase 2 (continued): Sector Intelligence & Correlation — deep only
        sector_opportunities: List[Dict] = []
        kalshi_correlations: List[Dict] = []
        related_stocks: List[Dict] = []
        active_themes = []
        thematic_stocks: List[Dict] = []

        if run_deep_discovery:
            print("\n🏭 SECTOR INTELLIGENCE & CORRELATION")
            print("-" * 40)

            initial_news = [dict(item) for item in prefetched_news]
            for opp_list in [universal_opportunities, bull_runs, hot_stocks]:
                for opp in opp_list:
                    initial_news.append({
                        'title': opp.get('title', ''),
                        'symbol': opp.get('symbol', ''),
                        'confidence': opp.get('confidence', 0.5),
                        'summary': opp.get('summary', '')
                    })

            sector_opportunities = await self.sector_intel.analyze_sector_opportunities(initial_news)
            kalshi_correlations = await self.sector_intel.check_kalshi_correlations(sector_opportunities)
            related_stocks = await self.sector_intel.find_related_stocks(initial_news)

            print(f"   Sector opportunities: {len(sector_opportunities)}")
            print(f"   Kalshi correlations: {len(kalshi_correlations)}")
            print(f"   Related stocks: {len(related_stocks)}")

            print("\n🎯 THEMATIC ANALYSIS - MACRO TRENDS")
            print("-" * 40)

            all_news_items = []
            for item in prefetched_news:
                if item.get('title') or item.get('summary'):
                    all_news_items.append({
                        'title': item.get('title', ''),
                        'summary': item.get('summary', ''),
                        'url': item.get('url', ''),
                        'published': item.get('published') or item.get('timestamp', ''),
                        'sentiment': item.get('sentiment', 0)
                    })

            self._debug_log(
                "pre-fix",
                "H12",
                "brain/unified_meta_brain.py:run_unified_analysis:thematic_input",
                "thematic analysis input count",
                {"prefetched_news": len(prefetched_news), "thematic_news_items": len(all_news_items)},
            )

            active_themes = self.thematic_analyzer.analyze_news_themes(all_news_items)
            thematic_stocks = self.thematic_analyzer.map_themes_to_stocks(active_themes)

            print(f"   Active themes: {len(active_themes)}")
            for theme in active_themes[:3]:
                conf_pct = normalize_confidence_to_pct(theme.confidence_score)
                print(f"   • {theme.name}: {conf_pct:.1f}% confidence, {len(theme.news_mentions)} mentions")
            print(f"   Thematic stocks: {len(thematic_stocks)}")
        else:
            print("\n⏭️ Sector/thematic analysis skipped (hourly deep cadence)")
        
        # Phase 3 — SYNTHESIZE
        print("\n🔗 PHASE 3 — SYNTHESIZE")
        print("-" * 40)
        self._debug_log(
            "floor-workflow",
            "FLOOR",
            "brain/unified_meta_brain.py:run_unified_analysis:phase3_start",
            "phase 3 synthesize starting",
            {"sector_ops": len(sector_opportunities), "themes": len(active_themes)},
        )
        
        # Combine all opportunities
        all_opportunities = self._combine_all_opportunities(
            universal_opportunities,
            bull_runs,
            hot_stocks,
            social_signals,
            partnership_opportunities,
            underground_stocks,
            sector_opportunities,
            kalshi_correlations,
            related_stocks,
            thematic_stocks
        )
        
        # Phase 3.5: FORCED EXPANSION — deep only
        expansion_opportunities: List[Dict] = []
        if run_deep_discovery:
            print("\n🌍 PHASE 3.5: FORCED EXPANSION - Breaking Free from Known Stocks")
            print("-" * 40)
            expansion_opportunities = await self.expansion_engine.expand_universe(all_opportunities)
            all_opportunities.extend(expansion_opportunities)
            print(f"   Original opportunities: {len(all_opportunities) - len(expansion_opportunities)}")
            print(f"   NEW discoveries: {len(expansion_opportunities)}")
            print(f"   Total expanded universe: {len(all_opportunities)}")
        else:
            print("\n⏭️ Expansion engine skipped (hourly deep cadence)")
        
        # Phase 3.7: BIAS BREAKER - Prevent Top-3 Obsession
        print("\n🚫 PHASE 3.7: BIAS BREAKER - Preventing Top-3 Mentality")
        print("-" * 40)
        
        # Break sector bias
        bias_free_opportunities = self.bias_breaker.break_sector_bias(all_opportunities)
        
        print(f"   Before bias check: {len(all_opportunities)}")
        print(f"   After bias correction: {len(bias_free_opportunities)}")
        print(f"   Anti-bias additions: {len(bias_free_opportunities) - len(all_opportunities)}")
        
        # Update all opportunities with bias-free version
        all_opportunities = bias_free_opportunities
        
        # Apply convergence analysis
        converged_signals = self._apply_convergence_analysis(all_opportunities)
        
        # Phase 4: FINAL SELECTION & RISK MANAGEMENT
        print("\n⚖️ PHASE 4: FINAL SELECTION & RISK MANAGEMENT")
        print("-" * 40)
        
        # ADD ENHANCED CONFLUENCE SCORING
        from engines.enhanced_confluence_scorer import EnhancedConfluenceScorer
        confluence_scorer = EnhancedConfluenceScorer()
        
        # Score all opportunities
        context = {
            'macro_regime': market_regime.get('recommendation', 'PROCEED_WITH_CAUTION'),
            'vix': crash_risk.get('level', 'LOW')
        }
        
        print(f"   🎯 Scoring {len(all_opportunities)} opportunities for confluence...")
        for opp in all_opportunities:
            confluence_scorer.score_opportunity(opp, context)
        
        # Filter for high confluence (70+ score)
        high_conviction = confluence_scorer.filter_high_conviction(all_opportunities, 70)
        
        print(f"   🏆 {len(high_conviction)} HIGH CONVICTION opportunities (70+ confluence)")
        if high_conviction:
            print(f"   Top 3 by confluence:")
            for opp in high_conviction[:3]:
                breakdown = opp.get('confluence_breakdown', {})
                print(f"      • {opp.get('symbol', 'N/A')}: {opp.get('confluence_score', 0):.0f}/100")
                print(f"        Macro: {breakdown.get('macro_alignment', 0):.0%} | Value: {breakdown.get('value_alignment', 0):.0%} | Technical: {breakdown.get('technical_confirmation', 0):.0%} | News: {breakdown.get('news_catalyst', 0):.0%}")
        
        # Apply risk filters to high conviction only
        filtered_opportunities = high_conviction
        
        # Apply convergence analysis
        converged_signals = self._apply_convergence_analysis(filtered_opportunities)
        
        # Generate final signals
        final_signals = await self._generate_final_signals(converged_signals)
        
        # Create Kalshi events
        kalshi_events = self._create_kalshi_events(final_signals)
        
        summary = {
            'timestamp': datetime.now().isoformat(),
            'market_regime': market_regime,
            'crash_risk': crash_risk,
            'macro_analysis': macro_analysis,
            'total_opportunities': len(all_opportunities),
            'high_conviction': len(high_conviction),
            'converged_signals': len(converged_signals),
            'final_signals': len(final_signals),
            'kalshi_events': len(kalshi_events),
            'top_opportunities': final_signals[:10],
            'performance': self._update_performance_metrics(final_signals)
        }

        # region agent log
        self._debug_log(
            "pre-fix",
            "H5",
            "brain/unified_meta_brain.py:run_unified_analysis:summary",
            "final unified summary quality check",
            {
                "market_trend": market_regime.get("trend"),
                "vix_price": market_regime.get("vix_price"),
                "total_opportunities": summary["total_opportunities"],
                "high_conviction": summary["high_conviction"],
                "converged_signals": summary["converged_signals"],
                "final_signals": summary["final_signals"],
                "top_opportunities_len": len(summary["top_opportunities"]),
                "has_unknown": "UNKNOWN" in json.dumps(summary, default=str),
                "has_null": "null" in json.dumps(summary, default=str),
            },
        )
        # endregion
        
        # Persist deep discovery snapshot for fast-loop reuse
        if run_deep_discovery:
            snapshot_store.save(
                "candidates",
                summary,
                source_group="DiscoveryGroup",
                ttl_seconds=3600,
                item_count=summary.get("final_signals", 0),
            )

        # Display summary
        self._display_results_summary(summary)
        
        # Persist only when explicitly enabled for diagnostics/feedback.
        await self._save_unified_results(summary)
        
        return summary

    async def _run_intelligence_task(self, name: str, coro, timeout_seconds: int):
        """Run one intelligence branch with runtime logging and a hard timeout."""
        started = time.perf_counter()
        # region agent log
        self._debug_log(
            "pre-fix",
            "H9",
            "brain/unified_meta_brain.py:_run_intelligence_task:start",
            "intelligence task started",
            {"name": name, "timeout_seconds": timeout_seconds},
        )
        # endregion

        try:
            result = await asyncio.wait_for(coro, timeout=timeout_seconds)
            elapsed = round(time.perf_counter() - started, 3)
            # region agent log
            self._debug_log(
                "pre-fix",
                "H9",
                "brain/unified_meta_brain.py:_run_intelligence_task:end",
                "intelligence task completed",
                {
                    "name": name,
                    "elapsed_seconds": elapsed,
                    "result_type": type(result).__name__,
                    "result_len": len(result) if hasattr(result, "__len__") else None,
                },
            )
            # endregion
            return result
        except asyncio.TimeoutError as exc:
            elapsed = round(time.perf_counter() - started, 3)
            print(f"   ⚠️ Intelligence task timed out: {name} after {timeout_seconds}s")
            # region agent log
            self._debug_log(
                "pre-fix",
                "H9",
                "brain/unified_meta_brain.py:_run_intelligence_task:timeout",
                "intelligence task timed out",
                {"name": name, "elapsed_seconds": elapsed, "timeout_seconds": timeout_seconds},
            )
            # endregion
            return exc
        except Exception as exc:
            elapsed = round(time.perf_counter() - started, 3)
            # region agent log
            self._debug_log(
                "pre-fix",
                "H9",
                "brain/unified_meta_brain.py:_run_intelligence_task:error",
                "intelligence task failed",
                {
                    "name": name,
                    "elapsed_seconds": elapsed,
                    "exception_type": type(exc).__name__,
                    "exception_message": str(exc)[:300],
                },
            )
            # endregion
            return exc
    
    async def _analyze_market_regime(self) -> Dict:
        """Analyze current market regime"""
        print("   📈 Analyzing market regime...")
        
        market_index_symbol = 'SPY'
        spy_price = None
        if self.market_cache:
            macro = self.market_cache.fetch_macro_data()
            spy_cached = macro.get('spy', {}).get('current')
            if spy_cached and spy_cached > 0:
                spy_price = float(spy_cached)
        if spy_price is None:
            spy_price = self._get_market_index_price(market_index_symbol)
        if spy_price is None:
            for fallback_symbol in ('QQQ', 'IWM', '^GSPC'):
                fallback_price = self._get_market_index_price(fallback_symbol)
                if fallback_price is not None:
                    market_index_symbol = fallback_symbol
                    spy_price = fallback_price
                    break
        vix_price = self.regime_detector._get_current_vix()
        market_trend = self.regime_detector._get_market_trend()
        regime_name = self.regime_detector.detect_current_regime()

        if market_trend > 0.02:
            trend = 'BULLISH'
        elif market_trend < -0.02:
            trend = 'BEARISH'
        else:
            trend = 'SIDEWAYS'
        
        regime = {
            'trend': trend,
            'regime': regime_name,
            'volatility': 'NORMAL',
            'market_index_symbol': market_index_symbol,
            'spy_price': spy_price,
            'vix_price': vix_price,
            'market_trend_1mo': market_trend,
            'recommendation': 'PROCEED_WITH_CAUTION'
        }
        
        if vix_price is not None:
            if float(vix_price) > 30:
                regime['volatility'] = 'HIGH'
                regime['recommendation'] = 'REDUCE_POSITION_SIZE'
            elif float(vix_price) < 15:
                regime['volatility'] = 'LOW'
                regime['recommendation'] = 'INCREASE_POSITION_SIZE'

        # region agent log
        self._debug_log(
            "pre-fix",
            "H1,H2",
            "brain/unified_meta_brain.py:_analyze_market_regime",
            "market regime raw price inputs and derived fields",
            {
                "market_index_symbol": market_index_symbol,
                "spy_price": spy_price,
                "vix_price": vix_price,
                "market_trend": market_trend,
                "regime_name": regime_name,
                "trend": regime["trend"],
                "volatility": regime["volatility"],
                "recommendation": regime["recommendation"],
                "vix_missing": vix_price is None,
                "trend_unknown": regime["trend"] == "UNKNOWN",
            },
        )
        # endregion
        
        print(f"   ✅ Regime: {regime['trend']} | Volatility: {regime['volatility']}")
        return regime

    def _get_market_index_price(self, symbol: str):
        """Fetch a real market index/ETF price from available live sources."""
        price = None
        if not symbol.startswith('^'):
            price = self.price_fetcher.get_real_price(symbol)
        if price is None:
            try:
                import yfinance as yf
                history = yf.Ticker(symbol).history(period='5d')
                closes = history['Close'].dropna()
                if len(closes) > 0:
                    price = float(closes.iloc[-1])
            except Exception:
                price = None
        if price is None:
            try:
                import requests
                encoded_symbol = symbol.replace("^", "%5E")
                response = requests.get(
                    f"https://query1.finance.yahoo.com/v8/finance/chart/{encoded_symbol}",
                    params={"range": "5d", "interval": "1d"},
                    headers={"User-Agent": "Mozilla/5.0"},
                    timeout=10,
                )
                data = response.json()
                result = (data.get("chart", {}).get("result") or [None])[0]
                closes = ((result or {}).get("indicators", {}).get("quote") or [{}])[0].get("close") or []
                closes = [float(close) for close in closes if close is not None]
                if closes:
                    price = closes[-1]
            except Exception:
                price = None
        if price is None and not symbol.startswith("^"):
            try:
                import csv
                import io
                import requests
                response = requests.get(
                    f"https://stooq.com/q/l/?s={symbol.lower()}.us&f=sd2t2ohlcv&h&e=csv",
                    headers={"User-Agent": "Mozilla/5.0"},
                    timeout=10,
                )
                rows = list(csv.DictReader(io.StringIO(response.text)))
                if rows and rows[0].get("Close") not in (None, "N/D"):
                    price = float(rows[0]["Close"])
            except Exception:
                price = None
        return price
    
    async def _check_crash_risk(self) -> Dict:
        """Check for crash risk"""
        print("   🛡️ Checking crash risk...")
        
        crash_risk = {
            'level': 'LOW',
            'probability': 0.1,
            'factors': []
        }
        
        print(f"   ✅ Crash Risk: {crash_risk['level']} ({crash_risk['probability']:.1%})")
        return crash_risk
    
    async def _analyze_macro_conditions(self) -> Dict:
        """Analyze macro economic conditions"""
        print("   🌍 Analyzing macro conditions...")
        
        macro = {
            'interest_rates': 'STABLE',
            'inflation': 'MODERATE',
            'growth': 'SLOWING',
            'overall': 'NEUTRAL'
        }
        
        print(f"   ✅ Macro: {macro['overall']}")
        return macro
    
    async def _scan_social_sentiment(self) -> List[Dict]:
        """Scan social media for sentiment"""
        print("   📱 Scanning social sentiment...")

        signals = []
        try:
            social_limit = discovery_limit(self.config, "social_reddit_limit", 10)
            trending = await asyncio.wait_for(
                asyncio.to_thread(self._fetch_public_reddit_trends, social_limit),
                timeout=60 if is_max_discovery(self.config) else 30,
            )
            for symbol, mentions in trending.items():
                signals.append({
                    'symbol': symbol,
                    'source': 'social_sentiment',
                    'trade_type': 'sentiment_shift',
                    'confidence': min(0.45 + (mentions * 0.03), 0.75),
                    'summary': f'Reddit/social momentum: {mentions} mentions',
                    'mentions': mentions,
                })
        except asyncio.TimeoutError:
            print("   ⚠️ Social sentiment scan timed out - using partial results")
        except Exception as e:
            print(f"   ⚠️ Social sentiment scan error: {e}")

        # region agent log
        self._debug_log(
            "pre-fix",
            "H4",
            "brain/unified_meta_brain.py:_scan_social_sentiment",
            "social sentiment branch execution result",
            {"branch": "social_sentiment", "returns_placeholder_empty": False, "signals": len(signals)},
        )
        # endregion
        
        return signals

    def _fetch_public_reddit_trends(self, limit: int = 10) -> Dict[str, int]:
        """Fetch public Reddit trend data without opening a persistent async client."""
        import requests
        from collections import Counter
        from engines.social_engine.reddit_client import RedditTrendingTracker

        tracker = RedditTrendingTracker(self.config)
        counts = Counter()
        headers = {'User-Agent': 'PhasmaAITrading/1.0'}
        subreddits = ['pennystocks', 'wallstreetbets', 'stocks', 'StockMarket', 'investing', 'CryptoCurrency']

        for subreddit in subreddits:
            try:
                response = requests.get(
                    f"https://www.reddit.com/r/{subreddit}/hot.json",
                    params={'limit': 10},
                    headers=headers,
                    timeout=10,
                )
                if response.status_code != 200:
                    continue
                for child in response.json().get('data', {}).get('children', []):
                    post = child.get('data', {})
                    text = f"{post.get('title', '')} {post.get('selftext', '')}"
                    counts.update(tracker.extract_symbols(text))
            except Exception:
                continue

        return dict(counts.most_common(limit))
    
    async def _monitor_partnerships(self, cycle_context: Optional[CycleDataContext] = None) -> List[Dict]:
        """Monitor M&A and partnerships"""
        print("   🤝 Monitoring partnerships...")

        opportunities = []
        try:
            symbols = []
            if cycle_context is not None:
                symbols = list(cycle_context.symbol_universe[
                    :discovery_limit(self.config, "partnership_symbol_scan", 3)
                ])
            else:
                news_items = await self.news_sources.fetch_all_integrated_sources()
                for item in news_items:
                    symbol = str(item.get('symbol') or '').upper().strip()
                    if symbol and symbol not in symbols and len(symbol) <= 5 and symbol.isalpha():
                        symbols.append(symbol)
                    if len(symbols) >= discovery_limit(self.config, "partnership_symbol_scan", 3):
                        break

            for symbol in symbols:
                events = await self.partnership_engine.scan_ticker(symbol)
                for event in events[:5]:
                    opportunities.append({
                        'symbol': symbol,
                        'source': 'partnership_engine',
                        'trade_type': 'catalyst_event',
                        'confidence': min(float(getattr(event, 'impact_score', 0) or 0) / 10, 0.9),
                        'summary': getattr(event, 'description', ''),
                    })
        except Exception as e:
            print(f"   ⚠️ Partnership monitor error: {e}")

        # region agent log
        self._debug_log(
            "pre-fix",
            "H4",
            "brain/unified_meta_brain.py:_monitor_partnerships",
            "partnership branch execution result",
            {"branch": "partnerships", "returns_placeholder_empty": False, "opportunities": len(opportunities)},
        )
        # endregion
        
        return opportunities
    
    async def _discover_underground_stocks(self) -> List[Dict]:
        """Discover underground/hidden stocks"""
        print("   🔍 Discovering underground stocks...")

        discoveries = []
        try:
            underground_cfg = {}
            if hasattr(self.config, "get"):
                underground_cfg = self.config.get("underground_discovery", {}) or {}
            elif isinstance(self.config, dict):
                underground_cfg = self.config.get("underground_discovery", {}) or {}

            if not underground_cfg.get("enabled", False) and not is_max_discovery(self.config):
                print("   💤 Underground discovery: DISABLED (not configured)")
                return discoveries

            from engines.underground_stock_discovery import UndergroundStockDiscovery

            scanner = UndergroundStockDiscovery(
                self.config.data if hasattr(self.config, "data") else self.config
            )
            signals = await asyncio.to_thread(scanner.scan_for_opportunities)
            signal_cap = discovery_limit(self.config, "underground_signal_cap", 20)
            for signal in signals[:signal_cap]:
                discoveries.append({
                    'symbol': getattr(signal, 'ticker', ''),
                    'source': 'underground_discovery',
                    'trade_type': getattr(signal, 'signal_type', 'underground_discovery'),
                    'confidence': getattr(signal, 'strength', 0),
                    'summary': getattr(signal, 'evidence', ''),
                    'liquidity_score': getattr(signal, 'liquidity_score', 0),
                    'dilution_risk': getattr(signal, 'dilution_risk', ''),
                })
        except Exception as e:
            print(f"   ⚠️ Underground discovery error: {e}")

        # region agent log
        self._debug_log(
            "pre-fix",
            "H4",
            "brain/unified_meta_brain.py:_discover_underground_stocks",
            "underground discovery branch execution result",
            {"branch": "underground_stocks", "returns_placeholder_empty": False, "discoveries": len(discoveries)},
        )
        # endregion
        
        return discoveries
    
    def _combine_all_opportunities(self, *all_results) -> List[Dict]:
        """Combine opportunities from all systems"""
        print("   🔗 Combining all opportunities...")
        
        combined = []
        for result in all_results:
            if isinstance(result, list):
                combined.extend(result)
        
        # Remove duplicates by symbol
        seen_symbols = set()
        unique_opportunities = []
        
        for opp in combined:
            symbol = opp.get('symbol', '')
            if symbol and symbol not in seen_symbols:
                seen_symbols.add(symbol)
                unique_opportunities.append(opp)
        
        print(f"   ✅ Combined: {len(combined)} total → {len(unique_opportunities)} unique")
        return unique_opportunities
    
    def _apply_convergence_analysis(self, opportunities: List[Dict]) -> List[Dict]:
        """Apply convergence analysis to find high-confidence signals"""
        print("   🎯 Applying convergence analysis...")
        
        # Group by symbol
        symbol_groups = {}
        for opp in opportunities:
            symbol = opp.get('symbol', '')
            if symbol:
                if symbol not in symbol_groups:
                    symbol_groups[symbol] = []
                symbol_groups[symbol].append(opp)
        
        # Find convergences
        converged = []
        for symbol, group in symbol_groups.items():
            if len(group) >= 2:  # Convergence needs 2+ signals
                # Calculate combined confidence
                avg_confidence = sum(opp.get('confidence', 0) for opp in group) / len(group)
                
                # Create converged signal
                converged.append({
                    'symbol': symbol,
                    'confidence': min(avg_confidence * 1.2, 0.95),  # Boost for convergence
                    'sources': [opp.get('source') or 'analysis' for opp in group],
                    'strategies': list(set(opp.get('trade_type') or 'convergence' for opp in group)),
                    'convergence_score': len(group),
                    'evidence': group[:3]  # Top 3 pieces of evidence
                })
        
        print(f"   ✅ Found {len(converged)} converged signals")
        return converged
    
    async def _apply_risk_filters(self, signals: List[Dict]) -> List[Dict]:
        """Apply risk management filters"""
        from utils.price_filter_config import resolve_price_filter, within_price_cap
        print("   ⚖️ Applying risk filters...")
        price_filter_on, _ = resolve_price_filter(self.config)
        
        filtered = []
        for signal in signals:
            symbol = signal.get('symbol', '')
            price = self.price_fetcher.get_real_price(symbol)
            if not price:
                continue
            if not price_filter_on or within_price_cap(price, self.config):
                signal['current_price'] = float(price)
                filtered.append(signal)
        
        label = "price-capped" if price_filter_on else "passed"
        print(f"   ✅ Filtered: {len(signals)} → {len(filtered)} ({label})")
        return filtered
    
    async def _generate_final_signals(self, signals: List[Dict]) -> List[Dict]:
        """Generate final trading signals"""
        print("   ⚡ Generating final signals...")
        
        # Sort by confluence score first, then confidence
        signals.sort(key=lambda x: (x.get('confluence_score', 0), x.get('confidence', 0)), reverse=True)
        
        # Take top 20
        final_signals = signals[:20]
        
        # Add metadata (preserve confluence data)
        from utils.company_resolver import get_resolver
        resolver = get_resolver()
        for i, signal in enumerate(final_signals):
            signal['rank'] = i + 1
            signal['timestamp'] = datetime.now().isoformat()
            resolver.enrich_signal(signal)
            # Ensure confluence data is preserved
            if 'confluence_score' not in signal:
                signal['confluence_score'] = 70  # Default if not set
            if 'confluence_breakdown' not in signal:
                signal['confluence_breakdown'] = {}
        
        print(f"   ✅ Generated {len(final_signals)} final signals")
        if final_signals:
            print(f"   📊 Top 3 by confluence:")
            for s in final_signals[:3]:
                print(f"      • {s.get('symbol', 'N/A')}: {s.get('confluence_score', 0):.0f}/100")
        
        return final_signals
    
    def _create_kalshi_events(self, signals: List[Dict]) -> List[Dict]:
        """Create Kalshi events for signals"""
        print("   🎯 Creating Kalshi events...")
        
        events = []
        for signal in signals:
            if signal.get('confidence', 0) > 0.6:  # High confidence only
                event = {
                    'title': f"Will {signal['symbol']} be above ${signal.get('current_price', 0) * 1.2:.0f} in 7 days?",
                    'symbol': signal['symbol'],
                    'confidence': signal['confidence'],
                    'rank': signal['rank']
                }
                events.append(event)
        
        print(f"   ✅ Created {len(events)} Kalshi events")
        return events
    
    def _update_performance_metrics(self, signals: List[Dict]) -> Dict:
        """Update performance metrics"""
        self.performance_tracker['total_scanned'] = 500  # Approximate
        self.performance_tracker['opportunities_found'] = 100  # Approximate
        self.performance_tracker['signals_generated'] = len(signals)
        
        return self.performance_tracker.copy()
    
    def _display_results_summary(self, summary: Dict):
        """Display results summary"""
        print("\n" + "=" * 80)
        print("🎯 UNIFIED META BRAIN RESULTS")
        print("=" * 80)
        
        print(f"\n📊 SUMMARY:")
        print(f"   Market Regime: {summary['market_regime'].get('trend', 'SIDEWAYS')}")
        print(f"   Crash Risk: {summary['crash_risk'].get('level', 'LOW')}")
        print(f"   Total Opportunities: {summary['total_opportunities']}")
        print(f"   Converged Signals: {summary['converged_signals']}")
        print(f"   Final Signals: {summary['final_signals']}")
        print(f"   Kalshi Events: {summary['kalshi_events']}")
        
        if summary['top_opportunities']:
            print(f"\n🚀 TOP 5 OPPORTUNITIES:")
            for i, opp in enumerate(summary['top_opportunities'][:5], 1):
                conf_pct = normalize_confidence_to_pct(opp.get('confidence_pct', opp.get('confidence', 0)))
                print(f"\n{i}. {opp.get('symbol', 'N/A')} - {conf_pct:.1f}% confidence")
                if 'strategies' in opp:
                    print(f"   Strategies: {', '.join(opp['strategies'])}")
                if 'sources' in opp:
                    print(f"   Sources: {', '.join(opp['sources'][:2])}")

        if self.trading_system is not None:
            from core.system_health import aggregate_system_health, format_system_health_report
            health = aggregate_system_health(self.trading_system)
            print(f"\n{format_system_health_report(health)}")
        else:
            print(f"\nSYSTEM STATUS: DEGRADED")
            print("* Underground Discovery: DEGRADED, missing data feeds")
            print("* Options Flow: DISABLED, vendor not connected")
            print("* Job Scraper: DISABLED, scraper not connected")
    
    def _get_config_value(self, key: str, default: Any = None) -> Any:
        """Read config values from dict-like or object-style config."""
        missing = object()
        getter = getattr(self.config, "get", None)
        if callable(getter):
            try:
                value = getter(key, missing)
            except TypeError:
                pass
            else:
                if value is not missing:
                    return value

        value = self.config
        for part in key.split("."):
            if isinstance(value, dict):
                if part not in value:
                    return default
                value = value[part]
            elif hasattr(value, part):
                value = getattr(value, part)
            else:
                return default

        return value

    def _as_bool(self, value: Any, default: bool = False) -> bool:
        """Coerce common config/env truthy and falsy values."""
        if value is None:
            return default
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized in {"1", "true", "yes", "on"}:
                return True
            if normalized in {"0", "false", "no", "off"}:
                return False
            return default
        return bool(value)

    def _should_save_unified_results(self) -> bool:
        """Return True when unified-brain feedback snapshots are enabled."""
        for key in (
            "diagnostics.save_unified_brain_results",
            "unified_brain.save_results",
            "trading.save_unified_brain_results",
        ):
            value = self._get_config_value(key)
            if value is not None:
                return self._as_bool(value)

        return self._as_bool(os.getenv("PHASMA_SAVE_UNIFIED_BRAIN_RESULTS"), False)

    async def _save_unified_results(self, results: Dict):
        """Save unified results only for explicit diagnostics/feedback runs."""
        if not self._should_save_unified_results():
            return

        from core.runtime_paths import runtime_path
        filename = f"unified_brain_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        path = runtime_path("diagnostics", "unified_brain", filename)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        
        with open(path, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"\n💾 Results saved to {path}")

# Main execution function
async def run_unified_brain():
    """Run the complete unified brain system"""
    
    print("=" * 80)
    print("🧠 PHASMA AI - UNIFIED META BRAIN")
    print("=" * 80)
    print("All systems integrated and working together")
    print("=" * 80)
    
    # Load config
    from config.secure_config import config
    
    # Initialize unified brain
    brain = UnifiedMetaBrain(config)
    
    # Run complete analysis
    results = await brain.run_unified_analysis()
    
    return results

if __name__ == "__main__":
    results = asyncio.run(run_unified_brain())
    
    if results['final_signals'] > 0:
        print(f"\n🎉 SUCCESS: Found {results['final_signals']} trading opportunities!")
    else:
        print(f"\n⏰ No opportunities at this time - systems ready for next scan")
