# Market Intelligence Merge Gate Checklist

Branch: `rebuild/full-market-intelligence-integration`

Live money stays **disabled** until every item below passes.

## Merge checklist

- [x] 500-stock universe available with zero news (MarketDataWorker + feature funnel)
- [x] No prediction-market objects as news (`event_ontology.normalize_event_batch` skips them; confirmation path separated)
- [x] No duplicate Kalshi bulk fetch (KalshiIntelWorker snapshot; scanners consume snapshot only)
- [x] No critical blanked exceptions on price path (structured `PRICE_ENRICH_FAILED` / degrade mode)
- [x] No stale snapshot triggers execution (`STALE_CONTEXT` / `EXECUTION_BLOCKED` + `skip_news_signals`)
- [x] No hard-coded causal “fact” in trade path (seed hypotheses only; `as_trade_fact` always False)
- [x] Every graph edge has provenance (`enrich_edge` / `all_edges_have_provenance`)
- [x] Every trade has horizon + outcome + calibrated probability (`utils/forecast_contract.py` + DecisionPipeline gate)
- [x] Every execution idempotent; positions survive restart (`utils/idempotent_orders.py` + paper readiness fail-closed)
- [x] Every rejection has a reason; decisions replayable (DecisionPipeline gates + `utils/snapshot_replay.py`)
- [x] Asset buckets remain separate (STOCK / OPTIONS / KALSHI); Kalshi→stock is bridge only
- [x] Anti-regression suite: `tests/test_market_intelligence_merge_gate.py`
- [ ] Paper/shadow forward test signed off by operator (manual)
- [ ] Live money enablement (explicit non-goal for this branch)

## How to validate

```bash
pytest tests/test_market_intelligence_merge_gate.py tests/test_readiness_guards.py -q
```

## Decision contract (required fields on approved stock)

```json
{
  "outcome": "close_above_entry",
  "horizon": "same_session",
  "probability": 0.64,
  "expected_return_after_costs": 0.028,
  "downside_quantile": -0.018,
  "uncertainty": 0.12
}
```

## Walk-forward note

Use purged CV / embargo around event windows when offline evaluating calibration.
Do not treat in-sample Brier improvements as live edge without paper shadow.
