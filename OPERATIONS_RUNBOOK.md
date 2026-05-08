"""
============================================================
EXECUTION CHECKER OPERATIONS RUNBOOK
============================================================

VERSION: 1.0
OWNER: Trading Systems Team
LAST UPDATED: 2025-01-01

OVERVIEW:
This runbook covers operational procedures for the ExecutionChecker v2 system,
including monitoring, troubleshooting, and emergency response procedures.

TABLE OF CONTENTS:
1. System Overview
2. Monitoring Dashboard
3. Common Failure Scenarios
4. Emergency Procedures
5. Maintenance Procedures
6. Contact Information

============================================
1. SYSTEM OVERVIEW
============================================

COMPONENTS:
- ExecutionChecker: Pre-trade validation engine
- MarketDataService: Real-time market data
- FilingsService: SEC dilution detection
- HumanGate: Manual review queue
- ExecutionAdapter: Order execution interface

KEY METRICS:
- Execution check rate: ~100 checks/minute
- Expected rejection rate: 10-20%
- Target slippage: <0.5%
- Human gate SLA: <3 minutes review

============================================
2. MONITORING DASHBOARD
============================================

DASHBOARD URL: https://phasma.ai/dashboards/execution

KEY PANELS:

Panel 1: Execution Throughput
- Checks per minute (target: 100)
- Allow rate (target: 80-90%)
- Rejection rate (alert if >20%)

Panel 2: Rejection Breakdown
- LOW_ADV count
- HIGH_SPREAD count
- INSUFFICIENT_DEPTH count
- DILUTION_RISK count
- SLIPPAGE_RISK count

Panel 3: Market Conditions
- VIX level (alert if >30)
- Average spread
- Market depth
- Halted securities count

Panel 4: Human Gate
- Queue size (alert if >10)
- Average review time
- Approval rate
- Escalations to compliance

============================================
3. COMMON FAILURE SCENARIOS
============================================

SCENARIO 1: MARKET DATA OUTAGE
Symptoms:
- All checks failing with "No market data"
- Execution check rate drops to 0
- Dashboard shows red market data status

Impact:
- No new trades can be executed
- Existing positions unaffected

Troubleshooting:
1. Check market data service status
2. Verify network connectivity to exchange
3. Check API rate limits
4. Review recent deployments

Resolution:
1. If market data down, switch to backup provider
2. If rate limited, increase limits or reduce check frequency
3. If network issue, contact network team
4. If recent deploy, rollback deployment

Prevention:
- Implement redundant market data feeds
- Add circuit breaker pattern
- Monitor API usage proactively

SCENARIO 2: HIGH REJECTION RATE
Symptoms:
- Rejection rate >20% for 5 minutes
- Specific rejection reason spiking
- Human gate queue growing

Impact:
- Reduced trading activity
- Potential missed opportunities

Troubleshooting:
1. Identify which rejection reason is spiking
2. Check market volatility (VIX)
3. Review recent market events
4. Check for configuration changes

Resolution:
1. If market volatility high, expected behavior
2. If configuration issue, rollback changes
3. If market structure changed, adjust thresholds
4. If data quality issue, fix data source

Prevention:
- Implement adaptive thresholds
- Add market regime detection
- Regular threshold review

SCENARIO 3: DILUTION FLAG SPIKE
Symptoms:
- DILUTION_RISK rejection rate >5x baseline
- Multiple securities flagged simultaneously
- Compliance team escalations

Impact:
- Reduced opportunity set
- Increased manual review

Troubleshooting:
1. Check for market-wide offering activity
2. Verify filings service data quality
3. Review recent SEC filing patterns
4. Check for false positives

Resolution:
1. If real offering activity, normal market condition
2. If data issue, fix filings service
3. If false positives, adjust detection logic
4. Document market event for future reference

Prevention:
- Implement offering calendar tracking
- Add false positive detection
- Regular model retraining

SCENARIO 4: SLIPPAGE EXCEEDANCE
Symptoms:
- Realized slippage > estimated by 2x
- Multiple orders with high slippage
- Execution adapter warnings

Impact:
- Higher trading costs
- Potential losses

Troubleshooting:
1. Check market volatility
2. Review order sizes vs market depth
3. Verify execution venue performance
4. Check for liquidity issues

Resolution:
1. Reduce position sizes immediately
2. Tighten slippage caps
3. Consider execution venue changes
4. Update slippage models

Prevention:
- Real-time slippage monitoring
- Adaptive sizing based on conditions
- Multiple execution venues

SCENARIO 5: HUMAN GATE BACKLOG
Symptoms:
- Queue size >20 items
- Review time >10 minutes
- Missed time-sensitive trades

Impact:
- Delayed executions
- Lost opportunities

Troubleshooting:
1. Check reviewer availability
2. Review complexity of items
3. Check UI performance issues
4. Verify notification system

Resolution:
1. Add additional reviewers
2. Simplify decision interface
3. Auto-approve low-risk items
4. Escalate to senior traders

Prevention:
- Auto-approval rules
- Tiered review system
- Performance monitoring

============================================
4. EMERGENCY PROCEDURES
============================================

EMERGENCY STOP ALL TRADING:
Trigger:
- System error causing losses
- Regulatory inquiry
- Unknown market condition

Steps:
1. Set feature flag: execution_checks_enabled = false
2. Set feature flag: order_submission_enabled = false
3. Cancel all open orders via broker API
4. Notify trading team and compliance
5. Post incident in Slack #trading-alerts

Verification:
- Confirm no new orders submitted
- Verify all open orders cancelled
- Check dashboard shows 0 activity

EMERGENCY THRESHOLD ADJUSTMENT:
Trigger:
- Market crisis (VIX > 50)
- Exchange technical issues
- Regulatory intervention

Steps:
1. Set feature flag: sensitivity_override = true
2. Tighten all thresholds by 50%
3. Reduce max position sizes by 50%
4. Enable additional compliance review
5. Notify all traders of new limits

EMERGENCY DATA SOURCE SWITCH:
Trigger:
- Primary market data failure
- Filings service outage
- Broker API issues

Steps:
1. Identify affected component
2. Switch to backup data source
3. Validate data quality
4. Monitor for anomalies
5. Notify data vendors

============================================
5. MAINTENANCE PROCEDURES
============================================

DAILY CHECKLIST (9:00 AM UTC):
- [ ] Check dashboard for any red alerts
- [ ] Review rejection rate from previous day
- [ ] Verify human gate cleared overnight
- [ ] Check for failed market data connections
- [ ] Review system error logs

WEEKLY MAINTENANCE (Monday 10:00 AM UTC):
- [ ] Review rejection reason trends
- [ ] Update threshold parameters if needed
- [ ] Check model drift indicators
- [ ] Backup configuration changes
- [ ] Review compliance escalations

MONTHLY MAINTENANCE:
- [ ] Full system health check
- [ ] Review and update runbook
- [ ] Performance optimization review
- [ ] Security audit of access controls
- [ ] Disaster recovery test

QUARTERLY REVIEW:
- [ ] Threshold optimization analysis
- [ ] Model performance review
- [ ] Cost-benefit analysis of features
- [ ] Regulatory compliance review
- [ ] System capacity planning

============================================
6. CONTACT INFORMATION
============================================

ON-CALL ROTATION:
- Primary: +1-555-0123 (Trading Ops)
- Secondary: +1-555-0124 (Engineering)
- Escalation: +1-555-0125 (CTO)

ESCALATION MATRIX:
Issue Severity | Response Time | Escalation
--------------|---------------|----------
Critical      | 5 minutes    | CTO
High          | 15 minutes   | Head of Trading
Medium        | 1 hour       | Engineering Lead
Low           | 4 hours      | Team Lead

SLACK CHANNELS:
- #trading-alerts: Critical alerts
- #execution-ops: Daily operations
- #execution-dev: Development issues

EMAIL DISTRIBUTION:
- trading-alerts@phasma.ai: Critical notifications
- execution-ops@phasma.ai: Daily reports
- compliance@phasma.ai: Regulatory issues

EXTERNAL CONTACTS:
- Broker Support: +1-800-BROKER
- Exchange Tech: +1-800-EXCHANGE
- Data Vendor: +1-800-DATA

============================================
APPENDIX: QUICK REFERENCE
============================================

FEATURE FLAGS:
- execution_checks_enabled: Master switch
- paper_mode_only: Live trading control
- sensitivity_override: Threshold adjustment
- human_gate_enabled: Manual review toggle

COMMON COMMANDS:
# Check current feature flags
curl -X GET https://api.phasma.ai/flags

# Update feature flag
curl -X POST https://api.phasma.ai/flags/execution_checks_enabled \
  -d '{"value": false}'

# Cancel all orders
python scripts/cancel_all_orders.py

# Get system status
python scripts/health_check.py

DASHBOARD URLS:
- Main: https://phasma.ai/dashboards/execution
- Alerts: https://phasma.ai/dashboards/alerts
- Performance: https://phasma.ai/dashboards/performance

============================================
END OF RUNBOOK
============================================
"""
