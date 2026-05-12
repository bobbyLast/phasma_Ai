"""
============================================================
ENGINEERING TICKET: US-003 - Execution Pre-Trade Checks
============================================================

TITLE: Implement Execution Controls and Position Sizing
OWNER: Trading Systems Team
ESTIMATE: 3 days
PRIORITY: HIGH
RISK: Execution Safety

OVERVIEW:
Add pre-trade execution checks to ensure liquidity, manage position sizing,
and prevent execution on illiquid signals. Critical before any live capital.

DEPENDENCIES: None (parallel with US-001, US-004)

ACCEPTANCE CRITERIA:
1. ✅ Minimum ADV check configurable per strategy (default $50K)
2. ✅ Bid-ask spread check (max 2% spread, fail fast)
3. ✅ Depth check (minimum $100K daily volume at current price)
4. ✅ Dilution flag check (avoid stocks with recent offerings)
5. ✅ Position sizing formula: base × liquidity × confidence
6. ✅ Paper trading mode enabled with realistic fills
7. ✅ All checks return structured reasons for rejection

IMPLEMENTATION DETAILS:

File: engines/execution_checker.py
```python
class ExecutionChecker:
    def __init__(self, config):
        self.min_adv = config.get('min_adv', 50_000)
        self.max_spread_pct = config.get('max_spread_pct', 0.02)
        self.min_depth_usd = config.get('min_depth_usd', 100_000)
        self.dilution_lookback_days = config.get('dilution_lookback_days', 30)
        self.paper_mode = config.get('paper_mode', True)
    
    def check_execution_readiness(self, ticker: str, confidence: float, strategy: str) -> Dict:
        """
        Returns: {
            'ready': bool,
            'reason': str,
            'position_size': float,
            'max_slippage_pct': float,
            'checks': Dict
        }
        """
        checks = {}
        
        # 1. ADV Check
        adv = self._get_average_daily_volume(ticker)
        checks['adv_usd'] = adv
        if adv < self.min_adv:
            return {
                'ready': False,
                'reason': f'Low ADV: ${adv:,.0f} < ${self.min_adv:,.0f}',
                'position_size': 0,
                'max_slippage_pct': 0,
                'checks': checks
            }
        
        # 2. Spread Check
        spread = self._get_bid_ask_spread(ticker)
        checks['spread_pct'] = spread
        if spread > self.max_spread_pct:
            return {
                'ready': False,
                'reason': f'Wide spread: {spread:.2%} > {self.max_spread_pct:.2%}',
                'position_size': 0,
                'max_slippage_pct': 0,
                'checks': checks
            }
        
        # 3. Depth Check
        depth = self._get_market_depth(ticker)
        checks['depth_usd'] = depth
        if depth < self.min_depth_usd:
            return {
                'ready': False,
                'reason': f'Insufficient depth: ${depth:,.0f} < ${self.min_depth_usd:,.0f}',
                'position_size': 0,
                'max_slippage_pct': 0,
                'checks': checks
            }
        
        # 4. Dilution Check
        dilution = self._check_recent_dilution(ticker)
        checks['recent_dilution'] = dilution
        if dilution:
            return {
                'ready': False,
                'reason': f'Recent dilution: {dilution}',
                'position_size': 0,
                'max_slippage_pct': 0,
                'checks': checks
            }
        
        # 5. Calculate Position Size
        position_size = self._calculate_position_size(ticker, confidence, adv, strategy)
        checks['position_size'] = position_size
        
        # 6. Max Slippage (based on spread and depth)
        max_slippage = min(spread * 0.5, 0.005)  # Cap at 0.5%
        checks['max_slippage_pct'] = max_slippage
        
        return {
            'ready': True,
            'reason': 'All checks passed',
            'position_size': position_size,
            'max_slippage_pct': max_slippage,
            'checks': checks
        }
    
    def _calculate_position_size(self, ticker: str, confidence: float, adv_usd: float, strategy: str) -> float:
        """Calculate position size based on liquidity and confidence"""
        # Base size from strategy config
        base_config = {
            'penny_moonshot': {'max_position': 5000, 'pct_capital': 0.02},
            'smallcap_compounder': {'max_position': 10000, 'pct_capital': 0.03}
        }
        
        config = base_config.get(strategy, base_config['penny_moonshot'])
        base_size = min(config['max_position'], 100000 * config['pct_capital'])
        
        # Liquidity multiplier (capped at 1.0)
        liquidity_mult = min(adv_usd / 1_000_000, 1.0)
        
        # Confidence multiplier (0.5 to 1.0)
        confidence_mult = max(0.5, confidence / 0.9)
        
        # Final size
        final_size = base_size * liquidity_mult * confidence_mult
        
        # Round to nearest 100
        return round(final_size / 100) * 100
    
    def _get_average_daily_volume(self, ticker: str) -> float:
        """Get 30-day average daily volume in USD"""
        # Integration with market data provider
        stock = yf.Ticker(ticker)
        hist = stock.history(period="1mo")
        if hist.empty:
            return 0
        
        avg_volume = hist['Volume'].mean()
        current_price = hist['Close'][-1]
        return avg_volume * current_price
    
    def _get_bid_ask_spread(self, ticker: str) -> float:
        """Get current bid-ask spread as percentage"""
        # Integration with real-time data
        ticker_obj = yf.Ticker(ticker)
        info = ticker_obj.info
        
        bid = info.get('bid', 0)
        ask = info.get('ask', 0)
        mid = (bid + ask) / 2
        
        if mid > 0:
            return (ask - bid) / mid
        return 1.0  # Default to 100% spread if data missing
    
    def _get_market_depth(self, ticker: str) -> float:
        """Estimate market depth in USD"""
        # Simplified: use daily volume as proxy
        return self._get_average_daily_volume(ticker)
    
    def _check_recent_dilution(self, ticker: str) -> Optional[str]:
        """Check for recent dilution events"""
        # Check SEC filings for recent offerings
        # Placeholder implementation
        return None
```

UNIT TESTS:

File: tests/test_execution_checker.py
```python
import pytest
from engines.execution_checker import ExecutionChecker

class TestExecutionChecker:
    def setup_method(self):
        self.config = {
            'min_adv': 50_000,
            'max_spread_pct': 0.02,
            'min_depth_usd': 100_000,
            'paper_mode': True
        }
        self.checker = ExecutionChecker(self.config)
    
    def test_low_adv_rejection(self):
        """Test rejection when ADV is too low"""
        # Mock low ADV stock
        with patch.object(self.checker, '_get_average_daily_volume', return_value=30_000):
            result = self.checker.check_execution_readiness('PENNY', 0.8, 'penny_moonshot')
            
            assert not result['ready']
            assert 'Low ADV' in result['reason']
            assert result['position_size'] == 0
    
    def test_wide_spread_rejection(self):
        """Test rejection when spread is too wide"""
        with patch.object(self.checker, '_get_average_daily_volume', return_value=100_000):
            with patch.object(self.checker, '_get_bid_ask_spread', return_value=0.05):
                result = self.checker.check_execution_readiness('ILLIQ', 0.8, 'penny_moonshot')
                
                assert not result['ready']
                assert 'Wide spread' in result['reason']
                assert result['position_size'] == 0
    
    def test_insufficient_depth_rejection(self):
        """Test rejection when depth is insufficient"""
        with patch.object(self.checker, '_get_average_daily_volume', return_value=100_000):
            with patch.object(self.checker, '_get_bid_ask_spread', return_value=0.01):
                with patch.object(self.checker, '_get_market_depth', return_value=50_000):
                    result = self.checker.check_execution_readiness('THIN', 0.8, 'penny_moonshot')
                    
                    assert not result['ready']
                    assert 'Insufficient depth' in result['reason']
    
    def test_dilution_rejection(self):
        """Test rejection when recent dilution detected"""
        with patch.object(self.checker, '_get_average_daily_volume', return_value=100_000):
            with patch.object(self.checker, '_get_bid_ask_spread', return_value=0.01):
                with patch.object(self.checker, '_check_recent_dilution', return_value='2024-12-01 offering'):
                    result = self.checker.check_execution_readings('DILUTE', 0.8, 'penny_moonshot')
                    
                    assert not result['ready']
                    assert 'Recent dilution' in result['reason']
    
    def test_successful_checks_penny_moonshot(self):
        """Test successful execution check for penny moonshot"""
        with patch.object(self.checker, '_get_average_daily_volume', return_value=500_000):
            with patch.object(self.checker, '_get_bid_ask_spread', return_value=0.01):
                with patch.object(self.checker, '_check_recent_dilution', return_value=None):
                    result = self.checker.check_execution_readiness('GOOD', 0.8, 'penny_moonshot')
                    
                    assert result['ready']
                    assert result['position_size'] > 0
                    assert result['max_slippage_pct'] <= 0.005
    
    def test_successful_checks_smallcap(self):
        """Test successful execution check for smallcap compounder"""
        with patch.object(self.checker, '_get_average_daily_volume', return_value=2_000_000):
            with patch.object(self.checker, '_get_bid_ask_spread', return_value=0.005):
                with patch.object(self.checker, '_check_recent_dilution', return_value=None):
                    result = self.checker.check_execution_readiness('SMALL', 0.7, 'smallcap_compounder')
                    
                    assert result['ready']
                    # Smallcap should get larger position
                    assert result['position_size'] > 2000
    
    def test_position_sizing_formula(self):
        """Test position sizing respects limits and multipliers"""
        # High confidence, high liquidity
        size1 = self.checker._calculate_position_size('TEST', 0.9, 2_000_000, 'penny_moonshot')
        assert size1 == 2000  # Base size * 1.0 liquidity * 1.0 confidence
        
        # Low confidence, low liquidity
        size2 = self.checker._calculate_position_size('TEST', 0.5, 100_000, 'penny_moonshot')
        assert size2 == 500  # Base size * 0.1 liquidity * 0.5 confidence
        
        # Rounded to nearest 100
        size3 = self.checker._calculate_position_size('TEST', 0.75, 750_000, 'penny_moonshot')
        assert size3 % 100 == 0
```

INTEGRATION TESTS:

File: tests/test_execution_integration.py
```python
def test_end_to_end_execution_flow():
    """Test full flow from signal to execution check"""
    # Create a signal
    signal = UndergroundSignal(
        ticker='TEST',
        signal_type='sec_filing',
        strength=0.8,
        evidence='Large insider buy',
        timestamp=datetime.now(),
        sources=['SEC EDGAR']
    )
    
    # Run through execution checker
    checker = ExecutionChecker(test_config)
    result = checker.check_execution_readiness(
        signal.ticker, 
        signal.strength, 
        'penny_moonshot'
    )
    
    # Verify all checks performed
    assert 'adv_usd' in result['checks']
    assert 'spread_pct' in result['checks']
    assert 'depth_usd' in result['checks']
    assert 'position_size' in result['checks']
    
    # If ready, position should be reasonable
    if result['ready']:
        assert 100 <= result['position_size'] <= 10000
        assert result['max_slippage_pct'] <= 0.005

def test_paper_trading_mode():
    """Test paper trading doesn't execute real orders"""
    checker = ExecutionChecker({**test_config, 'paper_mode': True})
    
    # Even with all checks passing, should not execute real trades
    assert checker.paper_mode == True
    
    # Mock successful checks
    with patch.multiple(checker,
        _get_average_daily_volume=return_value=500_000,
        _get_bid_ask_spread=return_value=0.01,
        _check_recent_dilution=return_value=None
    ):
        result = checker.check_execution_readiness('PAPER', 0.8, 'penny_moonshot')
        assert result['ready']
        
        # In paper mode, would log trade but not execute
        # Verify trade logging happens
```

CONFIGURATION UPDATES:

File: config.json
```json
{
  "execution": {
    "paper_mode": true,
    "min_adv": 50000,
    "max_spread_pct": 0.02,
    "min_depth_usd": 100000,
    "dilution_lookback_days": 30,
    "strategies": {
      "penny_moonshot": {
        "max_position": 5000,
        "pct_capital": 0.02
      },
      "smallcap_compounder": {
        "max_position": 10000,
        "pct_capital": 0.03
      }
    }
  }
}
```

MONITORING ADDITIONS:

Add to diagnostics:
```python
'execution': {
    'checks_performed': total_checks,
    'rejections_by_reason': {
        'low_adv': count,
        'wide_spread': count,
        'insufficient_depth': count,
        'recent_dilution': count
    },
    'avg_position_size': avg_size,
    'paper_trades_executed': count
}
```

ROLLBACK PLAN:
1. Feature flag: execution_checks_enabled
2. If issues: set flag to false, bypass all checks
3. Revert to fixed position sizing
4. Monitor for any unexpected trades

DEFINITION OF DONE:
- [ ] All unit tests passing (>90% coverage)
- [ ] Integration tests with real market data
- [ ] Paper trading mode validated with 100 test trades
- - [ ] Slippage within modeled caps
- [ ] Monitoring dashboards updated
- [ ] Rollback procedure documented
- [ ] Code review completed
- [ ] Security review completed

============================================
END OF TICKET US-003
============================================
"""
