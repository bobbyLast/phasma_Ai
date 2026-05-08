"""
============================================================
US-008 IMPLEMENTATION SPECIFICATION
Automated Rollback System - Detailed Design
============================================================

VERSION: 1.0
OWNER: Trading Systems Team
DATE: 2025-01-01

1. CORE ROLLBACK TRIGGERS
==========================

1.1 PERFORMANCE_DROP_TRIGGER
Trigger: 7-day return drops below -5%
- Metric: return_7d (rolling 7-day portfolio return)
- Threshold: -0.05 (-5%)
- Operator: <
- Window: 7 days
- Consecutive breaches: 3
- Action: IMMEDIATE_ROLLBACK
- Rationale: Significant capital loss indicates strategy failure

Implementation:
```python
class PerformanceDropTrigger(RollbackTrigger):
    def __init__(self):
        super().__init__(
            name="performance_drop",
            metric="return_7d",
            threshold=-0.05,
            operator="<",
            window_days=7,
            consecutive=3,
            action=RollbackAction.IMMEDIATE
        )
    
    def calculate_metric(self, trades):
        """Calculate 7-day rolling return"""
        cutoff = datetime.now() - timedelta(days=7)
        recent_trades = [t for t in trades if t.execution_date >= cutoff]
        
        if not recent_trades:
            return 0.0
        
        total_pnl = sum(t.realized_pnl for t in recent_trades)
        total_invested = sum(t.notional for t in recent_trades)
        
        return total_pnl / total_invested if total_invested > 0 else 0.0
```

1.2 SLIPPAGE_BREACH_TRIGGER
Trigger: Average slippage exceeds 1.5% over 1 day
- Metric: avg_slippage_1d
- Threshold: 0.015 (1.5%)
- Operator: >
- Window: 1 day
- Consecutive breaches: 3
- Action: IMMEDIATE_ROLLBACK
- Rationale: Execution costs eroding alpha

Implementation:
```python
class SlippageBreachTrigger(RollbackTrigger):
    def __init__(self):
        super().__init__(
            name="slippage_breach",
            metric="avg_slippage_1d",
            threshold=0.015,
            operator=">",
            window_days=1,
            consecutive=3,
            action=RollbackAction.IMMEDIATE
        )
    
    def calculate_metric(self, trades):
        """Calculate average slippage"""
        today = datetime.now().date()
        today_trades = [t for t in trades if t.execution_date.date() == today]
        
        if not today_trades:
            return 0.0
        
        slippages = [t.slippage_realized for t in today_trades]
        return np.mean(slippages)
```

1.3 ERROR_RATE_TRIGGER
Trigger: System error rate exceeds 10% in 1 hour
- Metric: error_rate_1h
- Threshold: 0.10 (10%)
- Operator: >
- Window: 1 hour
- Consecutive breaches: 2
- Action: PAUSE_NEW_TRADES
- Rationale: System instability

1.4 HUMAN_OVERRIDE_SPIKE_TRIGGER
Trigger: Human gate override rate > 25% in 24h
- Metric: human_override_rate_24h
- Threshold: 0.25 (25%)
- Operator: >
- Window: 24 hours
- Consecutive breaches: 1
- Action: GRADUAL_REDUCTION
- Rationale: Strategy misalignment with human judgment

1.5 DILUTION_FLAG_SPIKE_TRIGGER
Trigger: Dilution flags > 3x baseline in 24h
- Metric: dilution_flag_ratio_24h
- Threshold: 3.0
- Operator: >
- Window: 24 hours
- Consecutive breaches: 1
- Action: PAUSE_NEW_TRADES
- Rationale: Market structure change

2. ROLLBACK ACTIONS
==================

2.1 IMMEDIATE_ROLLBACK
- Revert all weights to last known good configuration
- Cancel all pending orders
- Pause new trade generation
- Alert ops and quant teams
- Requires: Immediate execution (< 1 second)

2.2 GRADUAL_REDUCTION
- Reduce position sizes by 50% over 1 hour
- Tighten risk limits
- Continue monitoring
- Alert ops team
- Requires: 5 steps over 12 minutes each

2.3 PAUSE_NEW_TRADES
- Stop new trade generation
- Keep existing positions
- Monitor existing trades
- Alert ops team
- Requires: Immediate effect

3. COOLDOWNS AND LIMITS
======================

3.1 Per-Rule Cooldowns
- performance_drop: 30 minutes
- slippage_breach: 15 minutes
- error_rate: 10 minutes
- human_override_spike: 60 minutes
- dilution_flag_spike: 45 minutes

3.2 Global Limits
- Max rollbacks per day: 5
- Max rollbacks per hour: 2
- Max immediate rollbacks per day: 3
- Manual override lock: 5 minutes after automated rollback

3.3 Implementation:
```python
class RollbackLimiter:
    def __init__(self, config):
        self.rule_cooldowns = config.get('rule_cooldowns', {})
        self.global_limits = config.get('global_limits', {})
        self.rollback_history = []
        self.manual_override_lock = False
    
    def can_execute_rollback(self, trigger_name):
        """Check if rollback can be executed"""
        # Check rule cooldown
        last_rollback = self._get_last_rollback(trigger_name)
        if last_rollback:
            cooldown = self.rule_cooldowns.get(trigger_name, 0)
            time_since = datetime.now() - last_rollback['timestamp']
            if time_since.total_seconds() < cooldown * 60:
                return False, f"Rule {trigger_name} in cooldown"
        
        # Check global limits
        today_count = self._count_today_rollbacks()
        if today_count >= self.global_limits.get('per_day', 5):
            return False, "Daily rollback limit reached"
        
        # Check manual override lock
        if self.manual_override_lock:
            return False, "Manual override lock active"
        
        return True, "Rollback allowed"
```

4. AUDIT TRAIL SCHEMA
=====================

4.1 Rollback Events Table:
```sql
CREATE TABLE rollback_events (
    event_id VARCHAR(50) PRIMARY KEY,
    trigger_name VARCHAR(50) NOT NULL,
    metric_value DECIMAL(10,6),
    threshold_value DECIMAL(10,6),
    trigger_timestamp TIMESTAMP NOT NULL,
    execution_timestamp TIMESTAMP NOT NULL,
    action_taken VARCHAR(20) NOT NULL,
    weights_before JSONB,
    weights_after JSONB,
    affected_trades INTEGER,
    operator_id VARCHAR(50),
    manual_override BOOLEAN DEFAULT FALSE,
    override_reason TEXT,
    recovery_time INTERVAL,
    post_rollback_performance DECIMAL(10,6),
    evidence_payload JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);
```

4.2 Trigger Inputs Table:
```sql
CREATE TABLE rollback_trigger_inputs (
    input_id SERIAL PRIMARY KEY,
    event_id VARCHAR(50) REFERENCES rollback_events(event_id),
    metric_name VARCHAR(50),
    metric_value DECIMAL(10,6),
    threshold_value DECIMAL(10,6),
    window_start TIMESTAMP,
    window_end TIMESTAMP,
    sample_size INTEGER,
    raw_data JSONB
);
```

5. DIAGNOSTICS PAYLOAD
======================

5.1 Payload Structure:
```json
{
  "event_id": "RB_20250101_143022_performance_drop",
  "trigger": {
    "name": "performance_drop",
    "metric": "return_7d",
    "value": -0.0623,
    "threshold": -0.05,
    "breach_count": 3
  },
  "market_context": {
    "vix": 28.5,
    "sector_performance": {
      "technology": -0.03,
      "healthcare": -0.08
    },
    "market_regime": "risk_off"
  },
  "recent_trades": {
    "last_24h": {
      "count": 45,
      "total_pnl": -12500,
      "win_rate": 0.31,
      "avg_slippage": 0.014
    },
    "last_7d": {
      "count": 210,
      "total_pnl": -45800,
      "win_rate": 0.34,
      "avg_slippage": 0.013
    }
  },
  "execution_diagnostics": {
    "realized_vs_modeled_slippage": {
      "modeled": 0.008,
      "realized": 0.014,
      "deviation": 0.006
    },
    "fill_rate": 0.87,
    "avg_latency_ms": 234
  },
  "human_gate_activity": {
    "reviews_24h": 12,
    "override_rate": 0.33,
    "common_reasons": ["HIGH_VOLATILITY", "LIQUIDITY_CONCERNS"]
  },
  "evidence_summary": {
    "signals_with_2_plus_evidence": 8,
    "signals_with_insider_only": 37,
    "recent_dilution_flags": 5
  },
  "weights": {
    "before": {
      "max_slippage_pct": 0.012,
      "position_size_multiplier": 1.2,
      "confidence_threshold": 0.6
    },
    "after": {
      "max_slippage_pct": 0.008,
      "position_size_multiplier": 1.0,
      "confidence_threshold": 0.7
    }
  }
}
```

6. TESTING SCENARIOS
===================

6.1 Unit Test Scenarios:
```python
class TestRollbackTriggers:
    def test_performance_drop_consecutive_breaches(self):
        """Test 3 consecutive days of -6% returns triggers rollback"""
        # Simulate 3 days of -6% returns
        # Verify rollback triggers on 3rd day
        # Verify cooldown prevents immediate re-trigger
    
    def test_slippage_breach_immediate_rollback(self):
        """Test slippage >1.5% for 3 trades triggers immediate rollback"""
        # Simulate 3 trades with 2% slippage
        # Verify immediate rollback
        # Verify all pending orders cancelled
    
    def test_error_rate_pause_only(self):
        """Test high error rate pauses but doesn't rollback"""
        # Simulate 15% error rate
        # Verify new trades paused
        # Verify existing positions maintained
    
    def test_false_positive_suppression(self):
        """Test single breach doesn't trigger rollback"""
        # Simulate one day of -6% return
        # Verify no rollback
        # Verify warning logged
```

6.2 Integration Test Scenarios:
```python
class TestRollbackIntegration:
    def test_end_to_end_rollback_flow(self):
        """Test complete rollback from trigger to recovery"""
        # 1. Generate trades that breach threshold
        # 2. Verify rollback triggers
        # 3. Verify weights reverted
        # 4. Verify alerts sent
        # 5. Verify audit trail complete
        # 6. Verify recovery monitoring
    
    def test_concurrent_trigger_handling(self):
        """Test multiple triggers firing simultaneously"""
        # Fire performance_drop and slippage_breach
        # Verify most severe action taken
        # Verify both events logged
    
    def test_manual_override_during_rollback(self):
        """Test manual override during automated rollback"""
        # Trigger automated rollback
        # Attempt manual override within lock period
        # Verify override rejected
        # Verify override allowed after lock period
```

7. MONITORING DASHBOARD
======================

7.1 Active Rollbacks Panel:
```javascript
// Real-time display of active rollbacks
{
  "active_rollbacks": [
    {
      "event_id": "RB_001",
      "trigger": "performance_drop",
      "start_time": "2025-01-01T14:30:22Z",
      "duration": "00:12:45",
      "status": "RECOVERING",
      "metrics": {
        "current_return": -0.045,
        "target_return": -0.02
      }
    }
  ]
}
```

7.2 Trigger Status Panel:
```javascript
// Status of all triggers
{
  "triggers": [
    {
      "name": "performance_drop",
      "status": "NORMAL",
      "last_check": "2025-01-01T14:45:00Z",
      "current_value": -0.023,
      "distance_to_threshold": 0.027,
      "trend": "improving"
    },
    {
      "name": "slippage_breach",
      "status": "WARNING",
      "last_check": "2025-01-01T14:45:00Z",
      "current_value": 0.012,
      "distance_to_threshold": 0.003,
      "trend": "worsening"
    }
  ]
}
```

8. FEATURE FLAGS CONFIGURATION
=============================

8.1 Flags:
```json
{
  "rollback": {
    "enabled": true,
    "auto_execute": true,
    "require_approval": false,
    "execution_mode": "immediate"
  },
  "triggers": {
    "performance_drop": {
      "enabled": true,
      "threshold_override": null,
      "action_override": null
    },
    "slippage_breach": {
      "enabled": true,
      "threshold_override": 0.02,
      "action_override": null
    }
  }
}
```

9. RUNBOOK PROCEDURES
====================

9.1 Immediate Response Checklist:
```
□ Verify rollback event in dashboard
□ Check affected trades and positions
□ Review market conditions
□ Notify trading desk
□ Document initial assessment
□ Set monitoring for recovery
```

9.2 Recovery Procedures:
```
1. Performance Drop Recovery:
   - Monitor returns for 24 hours
   - Gradually increase position sizes
   - Validate signal quality
   
2. Slippage Recovery:
   - Check market liquidity
   - Adjust execution venues
   - Re-tune slippage model
   
3. Error Rate Recovery:
   - Check system logs
   - Verify data feeds
   - Restart affected services
```

9.3 Escalation Matrix:
```
Severity 1 (Critical): Immediate rollback + CTO notification
Severity 2 (High): Rollback + Head of Trading notification  
Severity 3 (Medium): Pause + Ops team notification
Severity 4 (Low): Warning + Log entry only
```

10. IMPLEMENTATION TIMELINE
=========================

Day 1-2: Core trigger implementation
- Performance drop trigger
- Slippage breach trigger
- Basic rollback actions

Day 3: Advanced features
- Error rate trigger
- Human override spike trigger
- Dilution flag spike trigger
- Cooldowns and limits

Day 4: Integration and testing
- Database schema
- Audit trail implementation
- Unit and integration tests

Day 5: Monitoring and deployment
- Dashboard widgets
- Feature flags
- Staging deployment
- Production rollout

11. SUCCESS METRICS
==================

- Rollback response time: <1 second
- False positive rate: <5%
- Recovery time: <4 hours
- Audit completeness: 100%
- Alert accuracy: >95%

============================================
END OF SPECIFICATION
============================================
"""
