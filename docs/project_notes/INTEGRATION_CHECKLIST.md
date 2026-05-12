"""
============================================================
EXECUTION CHECKER INTEGRATION CHECKLIST
============================================================

TICKET: US-003-INTEGRATION - Wire ExecutionChecker into Pipeline
OWNER: Trading Systems Team
ESTIMATE: 2 days
PRIORITY: HIGH

INTEGRATION TASKS:

1. CONFLUENCE SERVICE INTEGRATION
   [ ] Add ExecutionChecker.evaluate() call in confluence_service.py
   [ ] Pass evidence_payload from confluence to execution checker
   [ ] Store execution diagnostics in confluence result
   [ ] Update confluence signal strength based on execution readiness

2. HUMAN GATE ROUTING
   [ ] Route all allowed=False to human gate with diagnostics
   [ ] Route soft rejections (INSUFFICIENT_DEPTH) to human gate
   [ ] Auto-escalate LEGAL_REVIEW_REQUIRED to compliance
   [ ] Auto-escalate DILUTION_RISK to senior trader
   [ ] Include order_plan preview in human gate UI

3. FEATURE FLAGS
   [ ] Add execution_checks_enabled flag (default: true)
   [ ] Add paper_mode_only flag (default: true)
   [ ] Add sensitivity_override flag (default: false)
   [ ] Configure flags per environment (dev/staging/prod)

4. EXECUTION ADAPTER
   [ ] Create ExecutionAdapter class to bridge order_plan to broker
   [ ] Implement limit laddering for large orders
   [ ] Add tranche submission with slippage monitoring
   [ ] Implement slippage abort (cancel if exceeds cap)

5. ERROR HANDLING
   [ ] Add circuit breaker for market data service
   [ ] Add timeout handling for filings service
   [ ] Add fallback pricing when snapshot unavailable
   [ ] Log all failures with detailed context

CODE CHANGES REQUIRED:

File: engines/confluence_service.py (excerpt)
```python
from engines.execution_checker_v2 import ExecutionChecker

class ConfluenceService:
    def __init__(self, config):
        # ... existing init ...
        self.execution_checker = ExecutionChecker(
            config.get('execution', {}),
            self.market_data_service,
            self.filings_service
        )
    
    def evaluate_signals(self, signals: List[Signal]) -> List[ConfluenceResult]:
        results = []
        for signal in signals:
            # ... existing evaluation ...
            
            # Add execution check
            execution_result = self.execution_checker.evaluate(
                ticker=signal.ticker,
                desired_shares=self._calculate_desired_shares(signal),
                strategy_name=self.strategy,
                confluence_score=signal.strength,
                evidence_payload=signal.evidence
            )
            
            result.execution_diagnostics = execution_result
            result.ready_for_execution = execution_result['allowed']
            
            # Route to human gate if needed
            if not execution_result['allowed']:
                self._route_to_human_gate(signal, execution_result)
            
            results.append(result)
        
        return results
```

File: engines/execution_adapter.py (new)
```python
class ExecutionAdapter:
    def __init__(self, broker_client, config):
        self.broker = broker_client
        self.config = config
        self.paper_mode = config.get('paper_mode', True)
    
    def execute_order_plan(self, order_plan: OrderPlan, ticker: str) -> Dict:
        """Execute order plan with tranche management"""
        if self.paper_mode:
            return self._simulate_execution(order_plan, ticker)
        
        fills = []
        for tranche in order_plan.tranches:
            # Submit tranche
            result = self.broker.submit_limit_order(
                symbol=ticker,
                side='BUY',
                quantity=tranche['shares'],
                price=tranche['price'],
                time_in_force=tranche['time_in_force']
            )
            
            # Monitor for slippage
            if self._check_slippage_exceeded(result, order_plan.max_slippage_pct):
                # Cancel remaining tranches
                self._cancel_remaining_orders(ticker)
                break
            
            fills.append(result)
        
        return {
            'status': 'FILLED' if len(fills) == len(order_plan.tranches) else 'PARTIAL',
            'fills': fills,
            'order_id': result.get('order_id')
        }
```

ACCEPTANCE TESTS:

File: tests/test_integration_execution.py
```python
def test_confluence_execution_integration():
    """Test full confluence to execution flow"""
    # Setup
    confluence = ConfluenceService(test_config)
    signals = [create_test_signal()]
    
    # Execute
    results = confluence.evaluate_signals(signals)
    
    # Verify
    assert len(results) == 1
    result = results[0]
    assert hasattr(result, 'execution_diagnostics')
    assert result.ready_for_execution == result.execution_diagnostics['allowed']
    
    # If not allowed, should be routed to human gate
    if not result.ready_for_execution:
        assert mock_human_gate.called
        call_args = mock_human_gate.call_args[0][1]  # execution_result
        assert 'reason_codes' in call_args
        assert 'order_plan' in call_args

def test_paper_execution_flow():
    """Test paper trading end-to-end"""
    # Create signal that passes execution checks
    signal = create_liquid_signal()
    
    # Run through pipeline
    result = confluence.evaluate_signals([signal])[0]
    
    # Execute in paper mode
    adapter = ExecutionAdapter(mock_broker, {'paper_mode': True})
    execution = adapter.execute_order_plan(
        result.execution_diagnostics['order_plan'],
        signal.ticker
    )
    
    # Verify paper execution
    assert execution['simulated'] == True
    assert execution['status'] == 'FILLED'
    assert len(execution['fills']) > 0

def test_market_volatility_regime():
    """Test that high volatility blocks trades"""
    # Mock high VIX environment
    with patch('market_data_service.get_snapshot') as mock_snapshot:
        mock_snapshot.return_value = create_high_vol_snapshot()
        
        signal = create_test_signal()
        result = confluence.evaluate_signals([signal])[0]
        
        # Should be rejected due to volatility
        assert not result.ready_for_execution
        assert 'VOLATILITY_OVERRIDE' in result.execution_diagnostics['reason_codes']

def test_dilution_escalation():
    """Test that dilution triggers escalation"""
    # Mock recent offering
    with patch('filings_service.has_recent_offering', return_value=True):
        signal = create_test_signal()
        result = confluence.evaluate_signals([signal])[0]
        
        # Should have dilution flag
        assert 'DILUTION_RISK' in result.execution_diagnostics['reason_codes']
        
        # Should escalate to compliance
        assert mock_compliance.escalation.called
```

MONITORING CONFIGURATION:

File: monitoring/execution_metrics.py
```python
from prometheus_client import Counter, Histogram, Gauge

# Metrics
execution_checks_total = Counter('execution_checks_total', 'Total execution checks', ['strategy', 'result'])
execution_rejections = Counter('execution_rejections_total', 'Execution rejections', ['reason'])
execution_size = Histogram('execution_size_shares', 'Recommended position size', ['strategy'])
execution_slippage = Histogram('execution_slippage_pct', 'Execution slippage percentage')
human_gate_queue_size = Gauge('human_gate_queue_size', 'Number of items in human gate')

# Alert rules
ALERT_RULES = """
- alert: HighRejectionRate
  expr: rate(execution_rejections_total[5m]) / rate(execution_checks_total[5m]) > 0.2
  for: 5m
  labels:
    severity: warning
  annotations:
    summary: "High execution rejection rate"

- alert: SlippageExceeded
  expr: execution_slippage > 0.01
  for: 1m
  labels:
    severity: critical
  annotations:
    summary: "Slippage exceeded 1%"
"""

ROLLBACK PROCEDURE:

1. FEATURE FLAGS
   - Set execution_checks_enabled = false
   - Set paper_mode_only = true
   - Notify ops team via Slack

2. ORDER PAUSE
   - Call broker API to cancel all open orders
   - Set order_submission_enabled = false

3. VERIFY
   - Check no new orders submitted
   - Monitor dashboard for compliance

4. POST-MORTEM
   - Collect logs from failure period
   - Analyze rejection patterns
   - Update runbook within 48 hours

DEPLOYMENT CHECKLIST:

Pre-deploy:
- [ ] All unit tests pass
- [ ] Integration tests pass in staging
- [ ] Feature flags configured
- [ ] Monitoring dashboards updated
- [ ] Runbook distributed to on-call

Deploy:
- [ ] Deploy to staging with paper_mode_only = true
- [ ] Run smoke test with 100 symbols
- [ ] Verify metrics collection
- [ ] Deploy to production with paper_mode_only = true

Post-deploy:
- [ ] Monitor for 1 hour
- [ ] Check rejection rates
- [ ] Verify human gate routing
- [ ] Review paper trade quality

CANARY PROCEDURE:

1. Enable for single strategy
2. Monitor for 30 minutes
3. Check all metrics green
4. Enable for second strategy
5. Continue gradual rollout

SUCCESS CRITERIA:
- Rejection rate < 20%
- Paper slippage within model
- Human gate review time < 3 minutes
- No live execution errors

============================================================
END OF INTEGRATION CHECKLIST
============================================================
"""
