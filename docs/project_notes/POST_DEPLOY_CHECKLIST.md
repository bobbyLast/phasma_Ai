"""
============================================================
POST-DEPLOY CHECKLIST - FIRST 100 TRADES
============================================================

VERSION: 1.0
OWNER: Trading Systems Team
DATE: 2025-01-01

OVERVIEW:
This checklist ensures safe deployment and monitoring of the ExecutionChecker v2
system during the critical first 100 trades period.

PRE-DEPLOY VERIFICATIONS:
============================================

ENVIRONMENT CHECKS:
- [ ] Staging environment healthy
- [ ] All unit tests passing (100% coverage)
- [ ] Integration tests passing
- [ ] Feature flags configured:
  - execution_checks_enabled = true
  - paper_mode_only = true
  - sensitivity_override = false

CONFIGURATION VERIFICATION:
- [ ] Strategy profiles loaded correctly
- [ ] Threshold values match design doc
- [ ] Market data connections active
- [ ] Filings service responding
- [ ] Broker API credentials valid

MONITORING SETUP:
- [ ] Dashboards displaying data
- [ ] Alert rules configured
- [ ] Log aggregation working
- [ ] Metrics collection active
- [ ] Error tracking enabled

DEPLOYMENT PROCEDURE:
============================================

STEP 1 - STAGING DEPLOYMENT:
1. Deploy code to staging
2. Run smoke test: python scripts/smoke_test.py
3. Verify paper mode execution
4. Check all metrics flowing
5. Validate human gate routing

STEP 2 - PRODUCTION DEPLOYMENT (PAPER MODE):
1. Deploy to production
2. Confirm paper_mode_only = true
3. Run 10 trade simulation
4. Verify no live orders placed
5. Check slippage estimates reasonable

STEP 3 - LIMITED CANARY:
1. Enable for penny_moonshot strategy only
2. Limit to $1,000 max position size
3. Monitor for 30 minutes
4. Verify all checks passing
5. Check rejection rates <20%

FIRST 100 TRADES MONITORING:
============================================

TRAKE EXECUTION TRACKING:

Trade # | Ticker | Strategy | Allowed | Reason Codes | Size | Slippage Est | Status
--------|--------|----------|---------|--------------|------|--------------|--------
[ ]     | [ ]    | [ ]      | [ ]     | [ ]          | [ ]  | [ ]          | [ ]
[ ]     | [ ]    | [ ]      | [ ]     | [ ]          | [ ]  | [ ]          | [ ]
... (continue for 100 trades)

REAL-TIME MONITORING CHECKS (Every 10 trades):
- [ ] Rejection rate between 10-20%
- [ ] No single reason >50% of rejections
- [ ] Average slippage estimate <0.5%
- [ ] Human gate queue <5 items
- [ ] No system errors or exceptions

QUALITY GATES:

After 25 trades:
- [ ] All diagnostics captured
- [ ] Paper trades executing correctly
- [ ] No unexpected rejections
- [ ] Slippage model accurate within 20%

After 50 trades:
- [ ] Review rejection patterns
- [ ] Validate threshold effectiveness
- [ ] Check human gate review times
- [ ] Verify position sizing logic

After 100 trades:
- [ ] Complete performance review
- [ ] Document any adjustments needed
- [ ] Prepare go-live recommendation
- [ ] Update runbook with lessons learned

ISSUE RESPONSE PROCEDURES:
============================================

IF REJECTION RATE >30%:
1. Pause new evaluations
2. Analyze rejection reasons
3. Check market conditions
4. Adjust thresholds if needed
5. Resume with caution

IF SLIPPAGE ESTIMATE INACCURATE:
1. Compare estimated vs actual
2. Update slippage model
3. Adjust participation rates
4. Document findings
5. Retest with paper trades

IF HUMAN GATE BACKLOG:
1. Add additional reviewers
2. Simplify decision interface
3. Auto-approve low-risk items
4. Escalate per protocol

IF SYSTEM ERRORS:
1. Check logs immediately
2. Identify root cause
3. Implement hotfix
4. Test thoroughly
5. Deploy with oversight

SUCCESS METRICS:
============================================

PERFORMANCE TARGETS:
- Execution check latency: <100ms
- Rejection rate: 10-20%
- Slippage estimate accuracy: ±20%
- Human gate review time: <3 minutes
- System uptime: >99.9%

QUALITY METRICS:
- Zero missed safety checks
- All evidence payloads preserved
- Complete audit trail
- No regulatory violations
- No financial losses

ROLLBACK CRITERIA:
============================================

IMMEDIATE ROLLBACK IF:
- Any safety check bypassed
- Regulatory compliance issue
- Financial loss >$100
- System uptime <95%
- Data corruption detected

PLANNED ROLLBACK IF:
- Rejection rate >40%
- Slippage errors >50%
- Human gate overwhelmed
- Performance degradation >50%

POST-100 TRADES REVIEW:
============================================

ANALYSIS REPORT INCLUDES:
1. Execution statistics
2. Rejection reason analysis
3. Slippage model performance
4. Human gate efficiency
5. System performance metrics
6. Issues and resolutions
7. Recommendations for go-live

GO-LIVE DECISION CHECKLIST:
- [ ] All success criteria met
- [ ] No critical issues outstanding
- [ ] Team trained on procedures
- [ ] Compliance approval received
- [ ] Risk management sign-off
- [ ] Executive approval obtained

============================================
APPENDIX: SCRIPTS AND COMMANDS
============================================

SMOKE TEST SCRIPT:
```bash
#!/bin/bash
python scripts/smoke_test.py \
  --environment production \
  --paper-mode true \
  --trade-count 10 \
  --verify-no-live-orders
```

MONITORING COMMANDS:
```bash
# Check current metrics
curl -s https://api.phasma.ai/metrics/execution | jq .

# Get rejection reasons
curl -s https://api.phasma.ai/rejections/last_hour | jq .

# Human gate status
curl -s https://api.phasma.ai/human_gate/status | jq .
```

EMERGENCY COMMANDS:
```bash
# Disable execution
curl -X POST https://api.phasma.ai/flags/execution_checks_enabled \
  -d '{"value": false}'

# Force paper mode
curl -X POST https://api.phasma.ai/flags/paper_mode_only \
  -d '{"value": true}'

# Cancel all orders
python scripts/emergency_cancel.py
```

============================================
END OF CHECKLIST
============================================
"""
