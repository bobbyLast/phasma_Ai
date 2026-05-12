"""
Engineering Ticket: Enable Fallback Sensitivity → Human Gate
===========================================================

TICKET: US-001 - Fallback Sensitivity with Human Gate Routing

OVERVIEW:
When buy rate drops below baseline (7 days with 0 buys), automatically lower thresholds
and route borderline candidates to human gate for review instead of auto-rejecting.

ACCEPTANCE CRITERIA:
1. System detects 0 buys in 7-day window → triggers fallback mode
2. Thresholds temporarily lowered to $25K minimum OR 2+ insiders with $10K+
3. Borderline candidates routed to human gate with evidence payload
4. Human gate receives one-page summary with top 3 evidence items
5. All decisions logged with reason codes for weight tuning

IMPLEMENTATION DETAILS:
- Already implemented: check_fallback_sensitivity() method
- Already implemented: _generate_borderline_candidates() method
- TODO: Human gate integration (webhook/queue)
- TODO: Evidence payload formatting
- TODO: Decision logging

UNIT TESTS:
```python
def test_fallback_sensitivity_trigger():
    # Given: 7 days with no buys
    # When: check_fallback_sensitivity() called
    # Then: Returns borderline candidates
    
def test_borderline_candidate_payload():
    # Given: Ticker with $30K in buys
    # When: Generated for human review
    # Then: Contains audit, transactions, recommendation
```

INTEGRATION TEST:
- Simulate 7-day period with no buys
- Verify fallback mode activation
- Verify human gate receives payload
- Verify logging captures decision

ESTIMATE: 2 days
PRIORITY: HIGH
"""
