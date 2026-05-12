"""
Engineering Ticket: Execution Pre-Trade Checks
===========================================

TICKET: US-003 - Implement Execution Controls and Sizing

OVERVIEW:
Add pre-trade execution checks to ensure liquidity, manage position sizing,
and prevent execution on illiquid signals.

ACCEPTANCE CRITERIA:
1. Minimum ADV check ($50K default, strategy-configurable)
2. Spread/depth check (max 2% spread, min $100K daily volume)
3. Dilution flag check (avoid recent dilution events)
4. Position sizing based on liquidity × confidence
5. Paper trading mode for testing

IMPLEMENTATION DETAILS:
```python
def check_execution_readiness(ticker, confidence):
    adv = get_average_daily_volume(ticker)
    if adv < min_adv: return False, "Low ADV"
    
    spread = get_bid_ask_spread(ticker)
    if spread > 0.02: return False, "Wide spread"
    
    dilution = check_recent_dilution(ticker)
    if dilution: return False, "Recent dilution"
    
    size = calculate_position_size(ticker, confidence)
    return True, {"size": size, "max_slippage": 0.5%}
```

SIZING FORMULA:
- Base size = min(2% capital, $10K)
- Liquidity multiplier = min(ADV / $1M, 1.0)
- Confidence multiplier = confidence / 0.9
- Final size = base × liquidity × confidence

UNIT TESTS:
```python
def test_liquidity_check():
    # Given: Ticker with low ADV
    # When: Execution check performed
    # Then: Rejected with reason
    
def test_position_sizing():
    # Given: High confidence, liquid ticker
    # When: Size calculated
    # Then: Size respects limits and liquidity
```

INTEGRATION TEST:
- Test on illiquid penny stocks
- Verify sizing respects risk limits
- Check paper trading execution

ESTIMATE: 3 days
PRIORITY: HIGH
RISK: Execution safety
"""
