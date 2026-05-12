"""
Engineering Ticket: Integration Smoke & Backtest
=============================================

TICKET: US-005 - End-to-End Testing with Historical Data

OVERVIEW:
Run comprehensive integration tests and lag-aware backtests using 1k historical
tickers through discovery → confluence → human gate pipeline.

ACCEPTANCE CRITERIA:
1. 1000 historical tickers processed through full pipeline
2. Lag-aware backtest accounts for filing delays (1-2 days)
3. Performance metrics calculated (precision, recall, ROI)
4. Edge cases tested (delistings, reverse splits, halts)
5. Backtest results reviewed and thresholds tuned

BACKTEST PARAMETERS:
- Period: Last 12 months of historical data
- Lag: 2 days (realistic filing-to-execution delay)
- Universe: Stocks $10M-$500M market cap
- Metrics: Win rate, avg return, max drawdown, Sharpe

EDGE CASES TO TEST:
- Stocks that delisted after signals
- Reverse splits affecting price
- Trading halts on news
- Massive dilution events
- Low float securities

PERFORMANCE TARGETS:
- Precision: >30% signals profitable
- Recall: >60% of major moves captured
- Max drawdown: <20%
- Annual return: >25% (paper)

UNIT TESTS:
```python
def test_lag_aware_execution():
    # Given: Signal on day 0
    # When: Executed on day 2
    # Then: Price reflects realistic slippage
    
def test_delisting_handling():
    # Given: Signal before delisting
    # When: Backtest runs
    # Then: Loss limited to stop-loss
```

INTEGRATION TEST:
- Full pipeline test with mock human gate
- Performance report generation
- Threshold optimization based on results

ESTIMATE: 5 days
PRIORITY: HIGH
BLOCKER: Historical data acquisition
"""
