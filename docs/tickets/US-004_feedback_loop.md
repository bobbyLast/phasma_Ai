"""
Engineering Ticket: Feedback Loop for Weight Tuning
===============================================

TICKET: US-004 - Instrument Decision Feedback Loop

OVERVIEW:
Persist all human gate decisions (approve/reject) with reason codes and build
automated weekly weight adjustment recommendations based on outcomes.

ACCEPTANCE CRITERIA:
1. All human decisions logged with timestamp, ticker, decision, reason
2. Weekly report analyzes decision patterns and outcomes
3. Weight adjustment recommendations generated automatically
4. Historical performance tracked by decision type
5. Feedback integrated into strategy thresholds

DATA MODEL:
```python
decision_log = {
    'timestamp': '2025-01-01T10:00:00Z',
    'ticker': 'AAPL',
    'decision': 'APPROVE',  # or REJECT
    'reason_code': 'STRONG_AGGREGATION',
    'evidence_score': 0.75,
    'actual_outcome': '+15%',  # tracked after 30 days
    'strategy': 'penny_moonshot'
}
```

WEEKLY REPORT CONTENTS:
- Decision distribution (approve/reject rates)
- Performance by reason code
- Threshold hit rates
- Recommended weight adjustments
- Edge cases needing review

UNIT TESTS:
```python
def test_decision_logging():
    # Given: Human gate decision
    # When: Logged to database
    # Then: All fields captured
    
def test_weight_recommendation():
    # Given: 100 rejections for low buys
    # When: Weekly report generated
    # Then: Recommends lowering low threshold
```

INTEGRATION TEST:
- Simulate 1000 decisions
- Generate weekly report
- Verify recommendations make sense
- Test weight update application

ESTIMATE: 4 days
PRIORITY: MEDIUM
IMPACT: Continuous improvement
"""
