"""Worker implementations wrapping existing Phasma stages."""

from __future__ import annotations

import asyncio
import logging
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any, Callable, Dict, Optional, Tuple

from core.supervisor.circuit_breaker import CircuitBreaker, hash_error
from core.supervisor.cycle_context import CycleContext
from core.supervisor.snapshot_store import WorkerSnapshotStore
from core.supervisor.worker_result import WorkerResult, WorkerStatus

logger = logging.getLogger(__name__)

# (engine_groups key, fallback seconds) — ingest must hard-fail; analysis gets more room
_WORKER_TIMEOUTS: Dict[str, Tuple[str, float]] = {
    "NewsIngestWorker": ("ingest", 90.0),
    "MarketDataWorker": ("market", 30.0),
    "CrashDetectorWorker": ("risk_fast", 30.0),
    "SignalGenerationWorker": ("discovery_deep", 300.0),
    "OutcomeGraderWorker": ("learning", 60.0),
    "TelegramWorker": ("reporting", 30.0),
    "DataGatesWorker": ("execution", 30.0),
    "ExecutionWorker": ("execution", 30.0),
    "JuryWorker": ("decision", 60.0),
    "UndergroundWorker": ("underground", 180.0),
    "KalshiIntelWorker": ("discovery_fast", 60.0),
    "SocialWorker": ("discovery_fast", 60.0),
    "GeopoliticalWorker": ("discovery_fast", 60.0),
}


class BaseWorker(ABC):
    name: str = "BaseWorker"
    critical: bool = False
    # Override per subclass when not listed in _WORKER_TIMEOUTS
    default_timeout_seconds: float = 120.0

    def __init__(
        self,
        breaker: CircuitBreaker,
        store: WorkerSnapshotStore,
        *,
        snapshot_key: Optional[str] = None,
        max_snapshot_age_seconds: int = 900,
    ):
        self.breaker = breaker
        self.store = store
        self.snapshot_key = snapshot_key or self.name.replace("Worker", "").lower()
        self.max_snapshot_age_seconds = max_snapshot_age_seconds

    def _resolve_timeout_seconds(self, ctx: CycleContext) -> float:
        group_key, fallback = _WORKER_TIMEOUTS.get(
            self.name, ("", float(self.default_timeout_seconds))
        )
        config = getattr(ctx, "config", None)
        if config is None and getattr(ctx, "app_ctx", None) is not None:
            config = getattr(ctx.app_ctx, "config", None)
        if config is not None and group_key:
            try:
                data = config.data if hasattr(config, "data") else config
                if isinstance(data, dict):
                    groups = data.get("engine_groups") or {}
                else:
                    groups = {}
                gcfg = groups.get(group_key) or {}
                if isinstance(gcfg, dict) and gcfg.get("max_seconds") is not None:
                    # Signal generation needs more than decision's 45s; keep floor for heavy workers
                    configured = float(gcfg["max_seconds"])
                    if self.name == "NewsIngestWorker":
                        return max(configured, 45.0)
                    if self.name == "SignalGenerationWorker":
                        return max(configured, 180.0)
                    return configured
            except Exception:
                pass
        return float(fallback)

    @abstractmethod
    async def _execute(self, ctx: CycleContext) -> WorkerResult:
        raise NotImplementedError

    async def run(self, ctx: CycleContext) -> WorkerResult:
        started = datetime.now(timezone.utc)
        state = self.breaker.get_state(self.name)

        if self.breaker.is_quarantined(self.name):
            state = self.breaker.get_state(self.name)
            return WorkerResult.build(
                self.name,
                WorkerStatus.QUARANTINED,
                started=started,
                detail=f"quarantined until {state.next_retry_at}",
                next_retry_at=state.next_retry_at,
                fail_count=state.fail_count,
                can_continue_pipeline=True,
            )

        timeout = self._resolve_timeout_seconds(ctx)
        try:
            result = await asyncio.wait_for(self._execute(ctx), timeout=timeout)
            if result.status in (WorkerStatus.OK, WorkerStatus.DEGRADED, WorkerStatus.SKIPPED):
                if result.status == WorkerStatus.OK:
                    self.breaker.record_success(self.name)
            elif result.status == WorkerStatus.ERROR and result.error_message:
                fake_exc = RuntimeError(result.error_message)
                self._handle_failure(fake_exc)
            return result
        except asyncio.TimeoutError as exc:
            timeout_exc = TimeoutError(f"{self.name} exceeded {timeout:.0f}s hard timeout")
            logger.error("%s", timeout_exc)
            quarantine_msg = self._handle_failure(timeout_exc)
            st = self.breaker.get_state(self.name)
            return WorkerResult.build(
                self.name,
                WorkerStatus.QUARANTINED if quarantine_msg else WorkerStatus.ERROR,
                started=started,
                error=timeout_exc,
                error_hash=hash_error(timeout_exc),
                fail_count=st.fail_count,
                detail=quarantine_msg or str(timeout_exc),
                next_retry_at=st.next_retry_at,
                can_continue_pipeline=not self.critical,
            )
        except Exception as exc:
            quarantine_msg = self._handle_failure(exc)
            st = self.breaker.get_state(self.name)
            return WorkerResult.build(
                self.name,
                WorkerStatus.QUARANTINED if quarantine_msg else WorkerStatus.ERROR,
                started=started,
                error=exc,
                error_hash=hash_error(exc),
                fail_count=st.fail_count,
                detail=quarantine_msg or str(exc),
                next_retry_at=st.next_retry_at,
                can_continue_pipeline=not self.critical,
            )

    def _handle_failure(self, exc: BaseException) -> Optional[str]:
        return self.breaker.record_failure(self.name, exc)


class NewsIngestWorker(BaseWorker):
    name = "NewsIngestWorker"

    async def _execute(self, ctx: CycleContext) -> WorkerResult:
        started = datetime.now(timezone.utc)
        system = ctx.system
        app_ctx = ctx.app_ctx

        from utils.cycle_data_context import CycleDataContext
        from brain.unified_meta_brain import UnifiedMetaBrain

        if not hasattr(system, "_unified_brain") or system._unified_brain is None:
            system._unified_brain = UnifiedMetaBrain(app_ctx.config, market_cache=app_ctx.market_cache)
        brain = system._unified_brain

        # Attach shared Kalshi snapshot + base market state if workers already ran
        kalshi_markets = getattr(app_ctx, "kalshi_markets_snapshot", None)
        if kalshi_markets and getattr(brain, "news_sources", None) is not None:
            brain.news_sources._shared_kalshi_markets = kalshi_markets

        base_universe = getattr(app_ctx, "base_universe", None)
        market_snapshot = getattr(app_ctx, "market_snapshot", None)

        # SEC + macro observers (incremental; failures logged, not swallowed)
        sec_extra = []
        macro_extra = []
        try:
            from utils.sec_filings_feed import fetch_recent_sec_filings
            sec_extra = fetch_recent_sec_filings()
        except Exception as exc:
            logger.error("SEC worker failed: %s", exc)
            print(f"ERROR SEC worker failed: {exc}")
        try:
            from utils.macro_snapshot import fetch_macro_snapshot
            macro_extra = fetch_macro_snapshot()
        except Exception as exc:
            logger.error("Macro worker failed: %s", exc)
            print(f"ERROR Macro worker failed: {exc}")

        cycle_data = await CycleDataContext.ingest(
            brain.news_sources,
            config=app_ctx.config,
            market_cache=app_ctx.market_cache,
            kalshi_markets=kalshi_markets,
            base_universe=base_universe,
            market_snapshot=market_snapshot,
            macro_events=macro_extra,
        )
        if sec_extra:
            cycle_data.sec_events = list(cycle_data.sec_events or []) + sec_extra
            cycle_data.ingested_news = list(cycle_data.ingested_news or []) + sec_extra
        # Event ontology + causal hypotheses + relationship expansion
        try:
            from utils.event_ontology import normalize_event_batch
            from utils.causal_hypotheses import hypotheses_for_events
            from utils.relationship_graph import expand_from_news_events, load_relationship_graph

            raw_news = cycle_data.news_events or cycle_data.ingested_news or []
            normalized = normalize_event_batch(list(raw_news) + list(cycle_data.sec_events or []))
            cycle_data.normalized_events = normalized
            if hasattr(cycle_data, "freshness_status"):
                cycle_data.freshness_status = dict(cycle_data.freshness_status or {})
                cycle_data.freshness_status["normalized_events"] = len(normalized)

            hyps = hypotheses_for_events(
                normalized,
                market_snapshot=cycle_data.market_snapshot or market_snapshot,
            )
            cycle_data.causal_hypotheses = hyps

            g = load_relationship_graph()
            cycle_data.relationship_graph_version = g.get("relationship_graph_version") or f"v{g.get('version', 2)}"

            rel = expand_from_news_events(
                normalized or raw_news,
                market_snapshot=cycle_data.market_snapshot or market_snapshot,
            )
            cycle_data.relationship_candidates = rel
            rel_syms = []
            for c in rel:
                sym = str(c.get("candidate_ticker") or c.get("symbol") or "").upper()
                if sym and sym not in cycle_data.event_universe:
                    cycle_data.event_universe.append(sym)
                if sym and sym not in cycle_data.symbol_universe:
                    cycle_data.symbol_universe.append(sym)
                if sym:
                    rel_syms.append(sym)
            cycle_data.relationship_universe = list(dict.fromkeys(rel_syms))
            if rel:
                print(f"   [FLOOR] relationship_candidates: {len(rel)} hypotheses={len(hyps)}")
        except Exception as rel_err:
            logger.warning("relationship/event ontology failed: %s", rel_err)

        # Attach feature funnel finalists if market worker already ran
        funnel = getattr(app_ctx, "feature_funnel", None)
        if funnel and isinstance(funnel, dict):
            cycle_data.freshness_status = dict(cycle_data.freshness_status or {})
            cycle_data.freshness_status["feature_funnel"] = funnel

        ctx.cycle_data = cycle_data
        app_ctx.cycle_data = cycle_data

        snapshot_path = self.store.save_last_good(
            "news_ingest",
            {
                "ingested_news": cycle_data.ingested_news,
                "news_events": cycle_data.news_events,
                "sec_events": cycle_data.sec_events,
                "social_events": cycle_data.social_events,
                "prediction_markets": cycle_data.prediction_markets[:200]
                if isinstance(cycle_data.prediction_markets, list)
                else [],
                "symbol_universe": cycle_data.symbol_universe,
                "base_universe": cycle_data.base_universe,
                "event_universe": cycle_data.event_universe,
                "company_names": cycle_data.company_names,
                "prices": cycle_data.prices,
                "market_snapshot": {
                    k: v for i, (k, v) in enumerate((cycle_data.market_snapshot or {}).items()) if i < 100
                },
            },
            metadata={"items": len(cycle_data.ingested_news)},
        )
        self.breaker.record_success(self.name)
        return WorkerResult.build(
            self.name,
            WorkerStatus.OK,
            started=started,
            output_snapshot_path=snapshot_path,
            metadata={"items": len(cycle_data.ingested_news)},
        )

    async def run(self, ctx: CycleContext) -> WorkerResult:
        started = datetime.now(timezone.utc)
        if self.breaker.is_quarantined(self.name):
            return await self._fallback_snapshot(ctx, started, quarantined=True)

        timeout = self._resolve_timeout_seconds(ctx)
        try:
            return await asyncio.wait_for(self._execute(ctx), timeout=timeout)
        except asyncio.TimeoutError:
            timeout_exc = TimeoutError(f"{self.name} exceeded {timeout:.0f}s hard timeout")
            logger.error("%s — falling back to last-good snapshot", timeout_exc)
            quarantine_msg = self._handle_failure(timeout_exc)
            fallback = await self._fallback_snapshot(ctx, started, error=timeout_exc)
            if quarantine_msg:
                fallback.status = WorkerStatus.QUARANTINED
                fallback.detail = quarantine_msg
                fallback.next_retry_at = self.breaker.get_state(self.name).next_retry_at
            else:
                fallback.detail = str(timeout_exc)
            return fallback
        except Exception as exc:
            quarantine_msg = self._handle_failure(exc)
            fallback = await self._fallback_snapshot(ctx, started, error=exc)
            if quarantine_msg:
                fallback.status = WorkerStatus.QUARANTINED
                fallback.detail = quarantine_msg
                fallback.next_retry_at = self.breaker.get_state(self.name).next_retry_at
            return fallback

    async def _fallback_snapshot(
        self,
        ctx: CycleContext,
        started: datetime,
        *,
        error: Optional[BaseException] = None,
        quarantined: bool = False,
    ) -> WorkerResult:
        from utils.cycle_data_context import CycleDataContext

        snap = self.store.load_last_good("news_ingest")
        # Stale/fallback news may inform research but MUST NOT approve new trades
        if snap and not self.store.is_stale("news_ingest", self.max_snapshot_age_seconds):
            data = snap.get("data") or {}
            ctx.cycle_data = CycleDataContext(
                ingested_news=data.get("ingested_news") or [],
                news_events=data.get("news_events") or data.get("ingested_news") or [],
                sec_events=data.get("sec_events") or [],
                social_events=data.get("social_events") or [],
                prediction_markets=data.get("prediction_markets") or [],
                market_snapshot=data.get("market_snapshot") or {},
                symbol_universe=data.get("symbol_universe") or [],
                base_universe=data.get("base_universe") or [],
                event_universe=data.get("event_universe") or [],
                company_names=data.get("company_names") or {},
                prices=data.get("prices") or {},
                context_mode="STALE_CONTEXT",
                news_from_stale_fallback=True,
                freshness_status={"fallback": True},
            )
            if ctx.app_ctx is not None:
                ctx.app_ctx.cycle_data = ctx.cycle_data
            ctx.news_snapshot_stale = True
            # Block trade signal generation from fallback snapshot
            ctx.skip_news_signals = True
            ctx.block_execution = True
            ctx.execution_blocked_reason = "stale last-good news snapshot — research only"
            return WorkerResult.build(
                self.name,
                WorkerStatus.DEGRADED,
                started=started,
                error=error,
                error_hash=hash_error(error) if error else None,
                stale_data_allowed=True,
                detail="last-good news snapshot — EXECUTION_BLOCKED / skip trade signals",
                output_snapshot_path=self.store._snapshot_path("news_ingest"),
                metadata={"items": len(ctx.cycle_data.ingested_news), "context_mode": "STALE_CONTEXT"},
            )

        ctx.skip_news_signals = True
        ctx.news_snapshot_stale = True
        ctx.block_execution = True
        ctx.execution_blocked_reason = "news snapshot stale or missing"
        return WorkerResult.build(
            self.name,
            WorkerStatus.ERROR if not quarantined else WorkerStatus.QUARANTINED,
            started=started,
            error=error,
            error_hash=hash_error(error) if error else None,
            can_continue_pipeline=True,
            detail="news snapshot stale or missing; skipping news signal generation",
        )


class CrashDetectorWorker(BaseWorker):
    name = "CrashDetectorWorker"

    async def _execute(self, ctx: CycleContext) -> WorkerResult:
        started = datetime.now(timezone.utc)
        system = ctx.system
        app_ctx = ctx.app_ctx
        all_signals = ctx.all_signals

        if not getattr(app_ctx, "crash_detector", None):
            ctx.crash_risk_unknown = True
            return WorkerResult.build(
                self.name,
                WorkerStatus.DEGRADED,
                started=started,
                detail="crash detector unavailable; risk UNKNOWN",
                metadata={"crash_risk": "UNKNOWN"},
            )

        crash_assessment, market_safe, index_crash, crypto_assessments = system._stage_crash_preflight(
            app_ctx,
            all_signals,
            ctx.metadata.get("macro_risk", False),
        )
        ctx.crash_assessment = crash_assessment
        ctx.market_safe = market_safe
        ctx.index_crash = index_crash
        ctx.crypto_assessments = crypto_assessments
        ctx.crash_risk_unknown = crash_assessment is None

        status = WorkerStatus.DEGRADED if ctx.crash_risk_unknown else WorkerStatus.OK
        self.breaker.record_success(self.name)
        return WorkerResult.build(
            self.name,
            WorkerStatus.OK if not ctx.crash_risk_unknown else WorkerStatus.DEGRADED,
            started=started,
            detail="crash risk UNKNOWN" if ctx.crash_risk_unknown else "crash assessment complete",
            metadata={"market_safe": market_safe, "crash_risk": "UNKNOWN" if ctx.crash_risk_unknown else "KNOWN"},
        )

    async def run(self, ctx: CycleContext) -> WorkerResult:
        started = datetime.now(timezone.utc)
        if self.breaker.is_quarantined(self.name):
            ctx.crash_risk_unknown = True
            ctx.market_safe = True
            return WorkerResult.build(
                self.name,
                WorkerStatus.QUARANTINED,
                started=started,
                detail="quarantined; crash risk UNKNOWN",
                can_continue_pipeline=True,
                metadata={"crash_risk": "UNKNOWN"},
            )
        try:
            return await self._execute(ctx)
        except Exception as exc:
            self._handle_failure(exc)
            ctx.crash_risk_unknown = True
            ctx.market_safe = True
            return WorkerResult.build(
                self.name,
                WorkerStatus.DEGRADED,
                started=started,
                error=exc,
                error_hash=hash_error(exc),
                detail="crash risk UNKNOWN after failure",
                can_continue_pipeline=True,
                metadata={"crash_risk": "UNKNOWN"},
            )


class MarketDataWorker(BaseWorker):
    name = "MarketDataWorker"

    async def _execute(self, ctx: CycleContext) -> WorkerResult:
        started = datetime.now(timezone.utc)
        cache = getattr(ctx.app_ctx, "market_cache", None) or getattr(ctx.system, "market_cache", None)
        config = getattr(ctx, "config", None) or getattr(ctx.app_ctx, "config", None)

        # Macro refresh (correct method name)
        if cache:
            try:
                if hasattr(cache, "fetch_macro_data"):
                    cache.fetch_macro_data()
                elif hasattr(cache, "refresh_macro_data"):
                    cache.refresh_macro_data()
            except Exception as exc:
                logger.warning("MarketDataWorker macro refresh failed: %s", exc)

        base_universe: list = []
        try:
            from utils.infinite_symbol_provider import get_symbol_provider
            base_universe = list(get_symbol_provider().get_symbols(limit=500) or [])
        except Exception as exc:
            logger.warning("MarketDataWorker base universe failed: %s", exc)

        market_snapshot: dict = {}
        prices: dict = {}
        if cache and base_universe:
            # Rolling refresh: prefer symbols missing/stale; batch in chunks
            batch_size = 80
            refreshed = 0
            for i in range(0, min(len(base_universe), 500), batch_size):
                chunk = base_universe[i : i + batch_size]
                try:
                    batch = cache.fetch_prices(chunk) or {}
                except Exception as exc:
                    logger.error("MarketDataWorker price batch failed: %s", exc)
                    print(f"ERROR MarketDataWorker price batch failed: {exc}")
                    batch = {}
                    if not market_snapshot:
                        # Mark failure for context_mode when we have nothing
                        if getattr(ctx, "app_ctx", None) is not None:
                            ctx.app_ctx.price_fetch_failed = True
                for sym, pdata in batch.items():
                    su = str(sym).upper()
                    price = None
                    volume = None
                    change = None
                    if isinstance(pdata, dict):
                        price = pdata.get("current") or pdata.get("price") or pdata.get("regularMarketPrice")
                        volume = pdata.get("volume") or pdata.get("avg_volume")
                        change = pdata.get("change_pct") or pdata.get("day_change_pct")
                    else:
                        try:
                            price = float(pdata)
                        except (TypeError, ValueError):
                            price = None
                    if price is None:
                        continue
                    try:
                        pf = float(price)
                    except (TypeError, ValueError):
                        continue
                    if pf <= 0:
                        continue
                    prices[su] = pf
                    market_snapshot[su] = {
                        "price": pf,
                        "volume": volume,
                        "change_pct": change,
                        "ts": datetime.now(timezone.utc).isoformat(),
                    }
                    refreshed += 1
                    try:
                        from utils.company_identity_registry import get_identity_registry
                        get_identity_registry().remember(su, last_price=pf, source="market_data_worker")
                    except Exception:
                        pass
                # Soft budget: stop after first 2 chunks if cycle is tight (~160 symbols)
                if i >= batch_size and refreshed >= 100:
                    break

            if prices:
                try:
                    from utils.robust_price_fetcher import register_cycle_prices
                    register_cycle_prices(prices)
                except Exception:
                    pass

        # Fast numerical screen over snapshot
        from utils.feature_funnel import build_feature_matrix, funnel_candidates
        features = build_feature_matrix(market_snapshot, base_universe=base_universe)
        funnel = funnel_candidates(features)
        movers = [r.to_dict() for r in features[:40]]

        # Attach to cycle context for downstream
        if getattr(ctx, "app_ctx", None) is not None:
            ctx.app_ctx.base_universe = base_universe
            ctx.app_ctx.market_snapshot = market_snapshot
            ctx.app_ctx.fast_movers = movers
            ctx.app_ctx.feature_funnel = funnel
            ctx.app_ctx.feature_matrix = [r.to_dict() for r in features[:500]]
        ctx.metadata = getattr(ctx, "metadata", None) or {}
        if isinstance(ctx.metadata, dict):
            ctx.metadata["base_universe_count"] = len(base_universe)
            ctx.metadata["market_snapshot_count"] = len(market_snapshot)
            ctx.metadata["deep_ai_finalists"] = funnel.get("deep_ai_finalists") or []

        path = self.store.save_last_good(
            "market_data",
            {
                "refreshed": True,
                "base_universe": base_universe[:500],
                "market_snapshot": market_snapshot,
                "fast_movers": movers[:40],
                "feature_funnel": funnel,
                "prices": prices,
            },
        )
        self.breaker.record_success(self.name)
        return WorkerResult.build(
            self.name,
            WorkerStatus.OK,
            started=started,
            output_snapshot_path=path,
            metadata={"symbols": len(market_snapshot), "base": len(base_universe), "funnel": len(funnel.get("deep_ai_finalists") or [])},
        )


class SignalGenerationWorker(BaseWorker):
    name = "SignalGenerationWorker"

    async def _execute(self, ctx: CycleContext) -> WorkerResult:
        started = datetime.now(timezone.utc)
        if ctx.skip_news_signals:
            return WorkerResult.build(
                self.name,
                WorkerStatus.SKIPPED,
                started=started,
                detail="news snapshot stale",
                can_continue_pipeline=True,
            )
        return WorkerResult.build(self.name, WorkerStatus.OK, started=started, detail="ready for signal pipeline")


class ExecutionWorker(BaseWorker):
    name = "ExecutionWorker"
    critical = True

    async def _execute(self, ctx: CycleContext) -> WorkerResult:
        started = datetime.now(timezone.utc)
        from core.execution.execution_modes import ExecutionMode, normalize_execution_config

        cfg = ctx.config.data if hasattr(ctx.config, "data") else ctx.config
        exec_cfg = normalize_execution_config(cfg if isinstance(cfg, dict) else {})
        mode = exec_cfg.get("mode", ExecutionMode.ALERT_ONLY)

        router = getattr(ctx.system, "execution_router", None)
        if router is None:
            ctx.block_execution = True
            ctx.execution_blocked_reason = "ExecutionRouter unavailable"
            return WorkerResult.build(
                self.name,
                WorkerStatus.ERROR,
                started=started,
                detail=ctx.execution_blocked_reason,
                can_continue_pipeline=False,
            )

        if ctx.block_execution:
            return WorkerResult.build(
                self.name,
                WorkerStatus.ERROR,
                started=started,
                detail=ctx.execution_blocked_reason or "execution blocked",
                can_continue_pipeline=False,
            )

        self.breaker.record_success(self.name)
        return WorkerResult.build(
            self.name,
            WorkerStatus.OK,
            started=started,
            detail=f"mode={mode}",
            metadata={"execution_mode": mode},
        )


class DataGatesWorker(BaseWorker):
    name = "DataGatesWorker"
    critical = True

    async def _execute(self, ctx: CycleContext) -> WorkerResult:
        started = datetime.now(timezone.utc)
        if ctx.block_execution:
            return WorkerResult.build(
                self.name,
                WorkerStatus.ERROR,
                started=started,
                detail=ctx.execution_blocked_reason or "execution already blocked",
                can_continue_pipeline=False,
            )
        self.breaker.record_success(self.name)
        return WorkerResult.build(self.name, WorkerStatus.OK, started=started)


class OutcomeGraderWorker(BaseWorker):
    name = "OutcomeGraderWorker"

    async def _execute(self, ctx: CycleContext) -> WorkerResult:
        started = datetime.now(timezone.utc)
        grader = getattr(ctx.system, "outcome_grader", None)
        if not grader:
            return WorkerResult.build(
                self.name,
                WorkerStatus.SKIPPED,
                started=started,
                detail="outcome grader unavailable",
            )
        try:
            stats = grader.grade_pending()
            self.breaker.record_success(self.name)
            return WorkerResult.build(
                self.name,
                WorkerStatus.OK,
                started=started,
                metadata=stats or {},
            )
        except Exception as exc:
            logger.warning("OutcomeGraderWorker failed: %s", exc)
            return WorkerResult.build(
                self.name,
                WorkerStatus.ERROR,
                started=started,
                error=exc,
                can_continue_pipeline=True,
                detail="logged and continuing",
            )


class TelegramWorker(BaseWorker):
    name = "TelegramWorker"

    async def _execute(self, ctx: CycleContext) -> WorkerResult:
        started = datetime.now(timezone.utc)
        pending = self.store.load_pending_telegram()
        if not pending:
            return WorkerResult.build(self.name, WorkerStatus.SKIPPED, started=started, detail="no pending alerts")
        self.breaker.record_success(self.name)
        return WorkerResult.build(
            self.name,
            WorkerStatus.OK,
            started=started,
            metadata={"pending_count": len(pending)},
        )


class JuryWorker(BaseWorker):
    name = "JuryWorker"

    async def _execute(self, ctx: CycleContext) -> WorkerResult:
        started = datetime.now(timezone.utc)
        jury_cfg = ctx.config.get("jury_system") if hasattr(ctx.config, "get") else {}
        if isinstance(jury_cfg, dict) and jury_cfg.get("enabled") is False:
            return WorkerResult.build(self.name, WorkerStatus.SKIPPED, started=started, detail="jury disabled")
        return WorkerResult.build(self.name, WorkerStatus.OK, started=started)


class KalshiIntelWorker(BaseWorker):
    name = "KalshiIntelWorker"

    async def _execute(self, ctx: CycleContext) -> WorkerResult:
        started = datetime.now(timezone.utc)
        from utils.config_helpers import config_get
        intel_only = config_get(ctx.config, "kalshi_intel_only", True)

        markets = []
        engine = getattr(ctx.system, "kalshi_engine", None)
        if engine is not None and hasattr(engine, "_fetch_open_markets_bulk"):
            try:
                max_pages = int(getattr(engine, "_max_market_pages", 4) or 4)
                markets = engine._fetch_open_markets_bulk(max_pages=max_pages) or []
            except Exception as exc:
                logger.warning("Kalshi snapshot fetch failed: %s", exc)
                markets = []

        if getattr(ctx, "app_ctx", None) is not None:
            ctx.app_ctx.kalshi_markets_snapshot = markets
            # Also stamp onto news sources for same-cycle reuse
            brain = getattr(ctx.system, "_unified_brain", None)
            if brain and getattr(brain, "news_sources", None) is not None:
                brain.news_sources._shared_kalshi_markets = markets
            cycle_data = getattr(ctx.app_ctx, "cycle_data", None) or getattr(ctx, "cycle_data", None)
            if cycle_data is not None and markets:
                cycle_data.prediction_markets = list(markets)

        path = self.store.save_last_good(
            "kalshi_snapshot",
            {"markets": markets[:300], "count": len(markets)},
            metadata={"count": len(markets)},
        )
        return WorkerResult.build(
            self.name,
            WorkerStatus.OK,
            started=started,
            output_snapshot_path=path,
            detail=("INTEL_ONLY" if intel_only else "ENABLED") + f" snapshot={len(markets)}",
            metadata={"markets": len(markets)},
        )


class SocialWorker(BaseWorker):
    name = "SocialWorker"

    async def _execute(self, ctx: CycleContext) -> WorkerResult:
        started = datetime.now(timezone.utc)
        engine = getattr(ctx.system, "social_engine", None)
        if not engine:
            return WorkerResult.build(self.name, WorkerStatus.DISABLED, started=started, detail="social engine not connected")
        return WorkerResult.build(self.name, WorkerStatus.OK, started=started)


class GeopoliticalWorker(BaseWorker):
    name = "GeopoliticalWorker"

    async def _execute(self, ctx: CycleContext) -> WorkerResult:
        started = datetime.now(timezone.utc)
        from core.source_status import demo_allowed_in_pipeline
        cfg = ctx.config.data if hasattr(ctx.config, "data") else (ctx.config if isinstance(ctx.config, dict) else {})
        if not demo_allowed_in_pipeline(cfg):
            return WorkerResult.build(
                self.name,
                WorkerStatus.DEGRADED,
                started=started,
                detail="DEMO_ONLY disabled from trade pipeline",
            )
        return WorkerResult.build(self.name, WorkerStatus.OK, started=started)


class UndergroundWorker(BaseWorker):
    name = "UndergroundWorker"

    async def _execute(self, ctx: CycleContext) -> WorkerResult:
        started = datetime.now(timezone.utc)
        ud = getattr(ctx.system, "underground_discovery", None)
        if not ud:
            return WorkerResult.build(self.name, WorkerStatus.DISABLED, started=started, detail="not enabled")
        if hasattr(ud, "get_feed_status"):
            feeds = ud.get_feed_status()
            bad = [k for k, v in feeds.items() if v not in ("OK",)]
            if bad:
                return WorkerResult.build(
                    self.name,
                    WorkerStatus.DEGRADED,
                    started=started,
                    detail="missing data feeds: " + ", ".join(bad),
                )
        return WorkerResult.build(self.name, WorkerStatus.OK, started=started)


def build_default_workers(breaker: CircuitBreaker, store: WorkerSnapshotStore) -> dict:
    return {
        w.name: w
        for w in (
            NewsIngestWorker(breaker, store),
            MarketDataWorker(breaker, store),
            CrashDetectorWorker(breaker, store),
            SignalGenerationWorker(breaker, store),
            JuryWorker(breaker, store),
            ExecutionWorker(breaker, store),
            DataGatesWorker(breaker, store),
            TelegramWorker(breaker, store),
            OutcomeGraderWorker(breaker, store),
            KalshiIntelWorker(breaker, store),
            SocialWorker(breaker, store),
            GeopoliticalWorker(breaker, store),
            UndergroundWorker(breaker, store),
        )
    }
