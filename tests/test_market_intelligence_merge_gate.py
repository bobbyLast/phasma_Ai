"""Anti-regression suite for Profitable Market Intelligence merge gate."""

from __future__ import annotations

import pytest


def test_prediction_markets_excluded_from_event_ontology():
    from utils.event_ontology import normalize_event_batch

    items = [
        {"title": "Company wins contract", "symbol": "AAA", "source": "Reuters"},
        {"title": "Will BTC hit 100k?", "prediction_market": True, "symbol": "KXBTCD"},
    ]
    events = normalize_event_batch(items)
    assert len(events) == 1
    assert events[0]["symbol"] == "AAA"
    assert all(not e.get("prediction_market") for e in events)


def test_context_mode_blocks_empty_market():
    from utils.context_mode import ContextMode, derive_context_mode, execution_allowed

    mode = derive_context_mode(
        market_snapshot={},
        prices={},
        snapshot_ages={"market": 9999, "news": 10},
        price_fetch_failed=True,
        news_from_stale_fallback=False,
    )
    assert mode == ContextMode.EXECUTION_BLOCKED.value
    assert not execution_allowed(mode)


def test_stale_news_fallback_blocks_execution():
    from utils.context_mode import ContextMode, derive_context_mode, execution_allowed

    mode = derive_context_mode(
        market_snapshot={"AAPL": {"price": 180}},
        prices={"AAPL": 180.0},
        snapshot_ages={"market": 30, "news": 5000},
        price_fetch_failed=False,
        news_from_stale_fallback=True,
    )
    assert mode == ContextMode.STALE_CONTEXT.value
    assert not execution_allowed(mode)


def test_graph_edges_have_provenance():
    from utils.relationship_graph import all_edges_have_provenance, enrich_edge, load_relationship_graph

    g = load_relationship_graph()
    assert all_edges_have_provenance(g)
    if g.get("edges"):
        e = enrich_edge(g["edges"][0])
        assert e.get("evidence")
        assert e.get("last_verified")
        assert e.get("edge_type") or e.get("relationship")


def test_related_opportunity_research_only_without_market_confirm():
    from utils.relationship_graph import expand_relationship_candidates

    # Empty snapshot → research_only or empty
    cands = expand_relationship_candidates(
        "NVDA",
        market_snapshot={"AMD": {"change_pct": 0.01, "volume": 100}},  # weak confirm
        allow_research_only=True,
        limit=5,
    )
    for c in cands:
        if float(c.get("market_confirmation") or 0) < 0.15:
            assert c.get("research_only") is True


def test_causal_seed_never_trade_fact():
    from engines.causal_counterfactual_engine import CausalCounterfactualEngine

    class _SG:
        pass

    eng = CausalCounterfactualEngine(_SG())
    assert eng.as_trade_fact("FED_RATE_DECISION", "NVDA") is False
    assert getattr(eng, "TRADE_CONTROL", False) is False
    # No hard-coded FDA→NVDA fact in seed
    keys = list(eng.causal_relationships.keys())
    assert ("FDA_AI_DRUG_APPROVAL", "NVDA") not in keys
    assert ("AI_BREAKTHROUGH", "NVDA") not in keys


def test_causal_hypothesis_trade_control_false():
    from utils.causal_hypotheses import generate_causal_hypotheses

    h = generate_causal_hypotheses({
        "event_id": "evt_1",
        "symbol": "AAA",
        "event_type": "contract_loss",
        "directional_interpretation": "down",
        "materiality": 0.8,
        "source_tier": 1,
        "facts": ["lost contract"],
        "title": "AAA loses contract",
    })
    assert h.get("trade_control") is False
    assert h.get("hypotheses")


def test_forecast_contract_required_fields():
    from utils.forecast_contract import apply_forecast_to_signal, forecast_gate_ok

    sig = {
        "symbol": "AAA",
        "side": "BUY",
        "confidence": 70,
        "entry": 10.0,
        "target": 12.0,
        "stop": 9.5,
        "pop_pct": 62,
        "freshness_class": "INTRADAY",
    }
    apply_forecast_to_signal(sig)
    ok, reason = forecast_gate_ok(sig)
    assert ok, reason
    fc = sig["forecast"]
    assert fc["horizon"]
    assert fc["probability"] is not None
    assert "expected_return_after_costs" in fc


def test_background_freshness_blocks_day_trade_confidence():
    from utils.forecast_contract import apply_freshness_to_day_trade_confidence

    sig = {
        "symbol": "AAA",
        "confidence": 80,
        "freshness_class": "BACKGROUND",
        "day_trade": True,
        "horizon": "same_session",
    }
    apply_freshness_to_day_trade_confidence(sig)
    assert sig.get("day_trade_blocked_by_freshness") is True
    assert float(sig.get("confidence") or 0) == 0.0


def test_microstructure_limited_no_easy_trades():
    from engines.microstructure_engine import MicrostructureEngine

    class _K:
        pass

    class _S:
        pass

    eng = MicrostructureEngine(_K(), _S())
    assert eng.capability == "limited_quote_microstructure"
    assert eng.get_easy_microstructure_trades() == []
    perm = eng.assess_entry_permission({"symbol": "SPY"})
    assert perm["claims_easy_trade"] is False
    assert perm["capability"] == "limited_quote_microstructure"


def test_stock_rr_gate_five_to_one():
    from utils.stock_reward_risk import passes_stock_rr_gate

    bad = {
        "symbol": "AAA",
        "asset_type": "STOCK",
        "entry_price": 10,
        "stop_loss": 9.5,
        "target_price": 11,
        "current_price": 10,
    }
    ok, _ = passes_stock_rr_gate(bad, config={"min_reward_risk_ratio": 5.0})
    assert ok is False
    good = {
        "symbol": "AAA",
        "asset_type": "STOCK",
        "entry_price": 10,
        "stop_loss": 9.5,
        "target_price": 13.0,
        "current_price": 10,
    }
    ok2, reason = passes_stock_rr_gate(good, config={"min_reward_risk_ratio": 5.0})
    assert ok2 is True, reason


def test_idempotent_order_ledger():
    from utils.idempotent_orders import IdempotentOrderLedger

    ledger = IdempotentOrderLedger()
    sig = {"symbol": "AAA", "side": "BUY", "strategy": "swing", "entry": 10, "forecast": {"horizon": "1d"}}
    ok1, key1, _ = ledger.try_claim(sig, cycle_id="c1")
    ok2, key2, reason = ledger.try_claim(sig, cycle_id="c1")
    assert ok1 and key1
    assert not ok2
    assert reason == "duplicate_idempotency_key"


def test_multi_axis_grader_separates_causal_from_pnl():
    from core.execution.outcome_grader import OutcomeGrader

    grader = OutcomeGrader(tracker=type("T", (), {"get_all_records": lambda self: [], "_save": lambda self: None})())
    record = {
        "confidence": 70,
        "event_type": "contract_loss",
        "causal_status": "unknown",
        "causal_contradicted": False,
        "calibrated_probability": 0.6,
        "grading": {
            "horizons": {
                "1d": {
                    "outcome": "win",
                    "direction_correct": True,
                    "timing_quality": "good",
                    "return_pct": 2.0,
                }
            }
        },
    }
    axes = grader.multi_axis_grade(record)
    assert axes["pnl_outcome"] == "win"
    assert axes["cause"]["grade"] != "pass"  # win alone does not confirm cause
    assert axes["cause"]["note"] == "win+bad_reasoning_does_not_strengthen"


def test_pattern_indicator_families_no_triple_count():
    from utils.pattern_families import indicator_family_confirmations

    conf = indicator_family_confirmations({
        "rsi": 70,
        "stoch": 80,
        "williams_r": -20,
        "momentum": 70,
        "relative_volume": 2.0,
    })
    # momentum family is one slot even if multiple oscillators provided
    assert conf["families"]["momentum"] is True
    assert conf["independent_confirmations"] <= conf["max_families"]


def test_decision_pipeline_context_mode_gate():
    from core.signals.decision_pipeline import DecisionPipeline

    pipe = DecisionPipeline({"min_reward_risk_ratio": 5.0}, execution_mode="ALERT_ONLY")
    sig = {
        "symbol": "AAPL",
        "ticker": "AAPL",
        "company_name": "Apple Inc",
        "current_price": 180,
        "entry": 180,
        "stop": 175,
        "target": 210,
        "confidence": 70,
        "position_size": 1,
        "source": "unit_test",
        "strategy": "swing_news",
        "action": "BUY",
        "context_mode": "EXECUTION_BLOCKED",
        "freshness_class": "INTRADAY",
        "pop_pct": 60,
    }
    d = pipe.evaluate(sig, has_catalyst=True)
    assert "context_mode" in (d.gates_failed or [])
