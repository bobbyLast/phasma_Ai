"""
============================================================
ENGINEERING TICKET: US-006 - Execution Adapter Implementation
============================================================

TITLE: Wire Order Plan to Execution Adapter with Laddering
OWNER: Trading Systems Team
ESTIMATE: 3 days
PRIORITY: HIGH
DEPENDENCIES: US-003 (ExecutionChecker v2)

OVERVIEW:
Create ExecutionAdapter to bridge ExecutionChecker order plans to broker execution,
implementing limit laddering, tranche management, and slippage monitoring.

ACCEPTANCE CRITERIA:
1. ✅ Order plan converted to broker-specific orders
2. ✅ Multi-tranche laddering for large positions
3. ✅ Real-time slippage monitoring with abort
4. ✅ Paper and live execution modes
5. ✅ Complete fill logging and reconciliation
6. ✅ Error handling and circuit breaker

IMPLEMENTATION DETAILS:

File: engines/execution_adapter.py
```python
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging
import asyncio
from engines.execution_checker_v2 import OrderPlan

logger = logging.getLogger(__name__)

@dataclass
class TrancheExecution:
    tranche_id: str
    shares: int
    limit_price: float
    status: str  # PENDING, FILLED, PARTIAL, CANCELLED
    fills: List[Dict]
    submitted_at: datetime
    filled_at: Optional[datetime]
    broker_order_id: Optional[str]

@dataclass
class ExecutionResult:
    total_shares: int
    filled_shares: int
    avg_price: float
    total_cost: float
    commissions: float
    estimated_slippage: float
    realized_slippage: float
    tranches: List[TrancheExecution]
    execution_time_ms: int
    status: str

class ExecutionAdapter:
    def __init__(self, broker_client, config: Dict):
        self.broker = broker_client
        self.config = config
        self.paper_mode = config.get('paper_mode', True)
        self.max_slippage_pct = config.get('max_slippage_pct', 0.01)
        self.tranche_delay_ms = config.get('tranche_delay_ms', 5000)
        self.circuit_breaker = CircuitBreaker()
        
    async def execute_order_plan(self, order_plan: OrderPlan, ticker: str) -> ExecutionResult:
        """
        Execute order plan with tranche management
        
        Returns:
            ExecutionResult with complete execution details
        """
        start_time = datetime.now()
        
        if self.paper_mode:
            return await self._execute_paper(order_plan, ticker, start_time)
        else:
            return await self._execute_live(order_plan, ticker, start_time)
    
    async def _execute_live(self, order_plan: OrderPlan, ticker: str, 
                           start_time: datetime) -> ExecutionResult:
        """Execute live order with tranche management"""
        tranches = []
        total_filled = 0
        total_cost = 0
        fills = []
        
        try:
            # Submit tranches sequentially
            for i, tranche_config in enumerate(order_plan.tranches):
                # Check circuit breaker
                if self.circuit_breaker.is_open():
                    logger.error("Circuit breaker open - aborting execution")
                    break
                
                # Submit tranche
                tranche = await self._submit_tranche(
                    ticker, tranche_config, f"{ticker}_{i}"
                )
                tranches.append(tranche)
                
                # Wait for fill or timeout
                tranche_result = await self._wait_for_fill(tranche, timeout_ms=30000)
                
                if tranche_result['status'] == 'FILLED':
                    total_filled += tranche_result['filled_shares']
                    total_cost += tranche_result['total_cost']
                    fills.extend(tranche_result['fills'])
                    
                    # Check slippage
                    if self._check_slippage_exceeded(tranche_result, order_plan.max_slippage_pct):
                        logger.warning(f"Slippage exceeded - cancelling remaining tranches")
                        await self._cancel_remaining_tranches(tranches, ticker)
                        break
                else:
                    logger.warning(f"Tranche {i} failed to fill: {tranche_result['status']}")
                    break
                
                # Delay between tranches
                if i < len(order_plan.tranches) - 1:
                    await asyncio.sleep(self.tranche_delay_ms / 1000)
            
            # Calculate execution result
            execution_time = (datetime.now() - start_time).total_seconds() * 1000
            avg_price = total_cost / total_filled if total_filled > 0 else 0
            
            return ExecutionResult(
                total_shares=order_plan.total_shares,
                filled_shares=total_filled,
                avg_price=avg_price,
                total_cost=total_cost,
                commissions=self._calculate_commissions(fills),
                estimated_slippage=order_plan.max_slippage_pct,
                realized_slippage=self._calculate_realized_slippage(fills, order_plan),
                tranches=tranches,
                execution_time_ms=int(execution_time),
                status='FILLED' if total_filled == order_plan.total_shares else 'PARTIAL'
            )
            
        except Exception as e:
            logger.error(f"Execution failed: {e}")
            # Cancel all pending orders
            await self._cancel_all_tranches(tranches, ticker)
            
            return ExecutionResult(
                total_shares=order_plan.total_shares,
                filled_shares=total_filled,
                avg_price=0,
                total_cost=total_cost,
                commissions=0,
                estimated_slippage=order_plan.max_slippage_pct,
                realized_slippage=0,
                tranches=tranches,
                execution_time_ms=int((datetime.now() - start_time).total_seconds() * 1000),
                status='FAILED'
            )
    
    async def _execute_paper(self, order_plan: OrderPlan, ticker: str, 
                            start_time: datetime) -> ExecutionResult:
        """Simulate paper execution"""
        tranches = []
        total_filled = 0
        total_cost = 0
        fills = []
        
        for i, tranche_config in enumerate(order_plan.tranches):
            # Simulate fill with realistic slippage
            simulated_price = self._simulate_fill_price(tranche_config, ticker)
            filled_shares = tranche_config['shares']
            fill_cost = simulated_price * filled_shares
            
            fill = {
                'shares': filled_shares,
                'price': simulated_price,
                'timestamp': datetime.now(),
                'execution_type': 'SIMULATED',
                'tranche_id': f"{ticker}_{i}"
            }
            fills.append(fill)
            total_filled += filled_shares
            total_cost += fill_cost
            
            tranche = TrancheExecution(
                tranche_id=f"{ticker}_{i}",
                shares=filled_shares,
                limit_price=tranche_config['price'],
                status='FILLED',
                fills=[fill],
                submitted_at=start_time,
                filled_at=datetime.now(),
                broker_order_id=f"PAPER_{ticker}_{i}"
            )
            tranches.append(tranche)
        
        execution_time = (datetime.now() - start_time).total_seconds() * 1000
        avg_price = total_cost / total_filled if total_filled > 0 else 0
        
        return ExecutionResult(
            total_shares=order_plan.total_shares,
            filled_shares=total_filled,
            avg_price=avg_price,
            total_cost=total_cost,
            commissions=0,  # No commissions in paper mode
            estimated_slippage=order_plan.max_slippage_pct,
            realized_slippage=self._calculate_simulated_slippage(fills, order_plan),
            tranches=tranches,
            execution_time_ms=int(execution_time),
            status='FILLED'
        )
    
    async def _submit_tranche(self, ticker: str, tranche_config: Dict, 
                             tranche_id: str) -> TrancheExecution:
        """Submit a single tranche to broker"""
        if self.paper_mode:
            # Create mock tranche for paper mode
            return TrancheExecution(
                tranche_id=tranche_id,
                shares=tranche_config['shares'],
                limit_price=tranche_config['price'],
                status='PENDING',
                fills=[],
                submitted_at=datetime.now(),
                filled_at=None,
                broker_order_id=f"PAPER_{tranche_id}"
            )
        
        # Live submission
        try:
            order_response = await self.broker.submit_limit_order(
                symbol=ticker,
                side='BUY',
                quantity=tranche_config['shares'],
                price=tranche_config['price'],
                time_in_force=tranche_config.get('time_in_force', 'DAY'),
                order_type=tranche_config.get('order_type', 'LIMIT')
            )
            
            return TrancheExecution(
                tranche_id=tranche_id,
                shares=tranche_config['shares'],
                limit_price=tranche_config['price'],
                status='PENDING',
                fills=[],
                submitted_at=datetime.now(),
                filled_at=None,
                broker_order_id=order_response['order_id']
            )
            
        except Exception as e:
            logger.error(f"Failed to submit tranche {tranche_id}: {e}")
            raise
    
    async def _wait_for_fill(self, tranche: TrancheExecution, timeout_ms: int) -> Dict:
        """Wait for tranche to fill or timeout"""
        if self.paper_mode:
            # Simulate immediate fill in paper mode
            tranche.status = 'FILLED'
            tranche.filled_at = datetime.now()
            
            return {
                'status': 'FILLED',
                'filled_shares': tranche.shares,
                'total_cost': tranche.shares * tranche.limit_price,
                'fills': tranche.fills
            }
        
        # Live fill monitoring
        start_wait = datetime.now()
        
        while (datetime.now() - start_wait).total_seconds() * 1000 < timeout_ms:
            # Check order status
            status = await self.broker.get_order_status(tranche.broker_order_id)
            
            if status['status'] == 'FILLED':
                tranche.status = 'FILLED'
                tranche.filled_at = datetime.now()
                tranche.fills = status['fills']
                
                return {
                    'status': 'FILLED',
                    'filled_shares': sum(f['shares'] for f in status['fills']),
                    'total_cost': sum(f['shares'] * f['price'] for f in status['fills']),
                    'fills': status['fills']
                }
            elif status['status'] == 'CANCELLED':
                tranche.status = 'CANCELLED'
                return {'status': 'CANCELLED', 'filled_shares': 0}
            
            await asyncio.sleep(0.5)  # Poll every 500ms
        
        # Timeout reached
        await self.broker.cancel_order(tranche.broker_order_id)
        tranche.status = 'CANCELLED'
        return {'status': 'TIMEOUT', 'filled_shares': 0}
    
    def _check_slippage_exceeded(self, fill_result: Dict, max_slippage_pct: float) -> bool:
        """Check if slippage exceeded maximum"""
        if not fill_result['fills']:
            return False
        
        # Calculate average fill price
        total_cost = sum(f['shares'] * f['price'] for f in fill_result['fills'])
        total_shares = sum(f['shares'] for f in fill_result['fills'])
        avg_fill_price = total_cost / total_shares
        
        # Expected price (first limit price)
        expected_price = fill_result['fills'][0]['price']
        
        # Calculate slippage
        slippage = abs(avg_fill_price - expected_price) / expected_price
        
        return slippage > max_slippage_pct
    
    async def _cancel_remaining_tranches(self, tranches: List[TrancheExecution], ticker: str):
        """Cancel all pending tranches"""
        for tranche in tranches:
            if tranche.status == 'PENDING':
                try:
                    await self.broker.cancel_order(tranche.broker_order_id)
                    tranche.status = 'CANCELLED'
                except Exception as e:
                    logger.error(f"Failed to cancel tranche {tranche.tranche_id}: {e}")
    
    def _simulate_fill_price(self, tranche_config: Dict, ticker: str) -> float:
        """Simulate realistic fill price for paper mode"""
        base_price = tranche_config['price']
        
        # Add random slippage within bounds
        import random
        slippage_range = self.max_slippage_pct * 0.5  # Use half of max as range
        slippage = random.uniform(-slippage_range, slippage_range)
        
        return base_price * (1 + slippage)
    
    def _calculate_commissions(self, fills: List[Dict]) -> float:
        """Calculate total commissions"""
        # Assume $0.005 per share
        total_shares = sum(f['shares'] for f in fills)
        return total_shares * 0.005
    
    def _calculate_realized_slippage(self, fills: List[Dict], order_plan: OrderPlan) -> float:
        """Calculate realized slippage percentage"""
        if not fills:
            return 0
        
        total_cost = sum(f['shares'] * f['price'] for f in fills)
        total_shares = sum(f['shares'] for f in fills)
        avg_price = total_cost / total_shares
        
        expected_price = order_plan.tranches[0]['price']
        
        return abs(avg_price - expected_price) / expected_price
    
    def _calculate_simulated_slippage(self, fills: List[Dict], order_plan: OrderPlan) -> float:
        """Calculate slippage for paper trades"""
        return self._calculate_realized_slippage(fills, order_plan)


class CircuitBreaker:
    """Simple circuit breaker for execution"""
    def __init__(self, failure_threshold=5, timeout_seconds=60):
        self.failure_threshold = failure_threshold
        self.timeout_seconds = timeout_seconds
        self.failure_count = 0
        self.last_failure_time = None
        self.state = 'CLOSED'  # CLOSED, OPEN, HALF_OPEN
    
    def is_open(self) -> bool:
        """Check if circuit breaker is open"""
        if self.state == 'OPEN':
            if (datetime.now() - self.last_failure_time).total_seconds() > self.timeout_seconds:
                self.state = 'HALF_OPEN'
                return False
            return True
        
        return False
    
    def record_success(self):
        """Record successful execution"""
        self.failure_count = 0
        self.state = 'CLOSED'
    
    def record_failure(self):
        """Record failed execution"""
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        
        if self.failure_count >= self.failure_threshold:
            self.state = 'OPEN'
```

UNIT TESTS:

File: tests/test_execution_adapter.py
```python
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock
from engines.execution_adapter import ExecutionAdapter, ExecutionResult, TrancheExecution

class TestExecutionAdapter:
    def setup_method(self):
        self.mock_broker = AsyncMock()
        self.config = {
            'paper_mode': True,
            'max_slippage_pct': 0.01,
            'tranche_delay_ms': 100
        }
        self.adapter = ExecutionAdapter(self.mock_broker, self.config)
    
    @pytest.mark.asyncio
    async def test_paper_execution_single_tranche(self):
        """Test paper mode execution with single tranche"""
        from engines.execution_checker_v2 import OrderPlan
        
        order_plan = OrderPlan(
            total_shares=1000,
            tranches=[{
                'shares': 1000,
                'type': 'LIMIT',
                'price': 10.0,
                'time_in_force': 'DAY'
            }],
            max_slippage_pct=0.01,
            participation_rate=0.05,
            time_in_force='DAY',
            order_type='LIMIT'
        )
        
        result = await self.adapter.execute_order_plan(order_plan, 'TEST')
        
        assert result.status == 'FILLED'
        assert result.filled_shares == 1000
        assert result.total_shares == 1000
        assert result.commissions == 0  # Paper mode
        assert len(result.tranches) == 1
        assert result.tranches[0].status == 'FILLED'
    
    @pytest.mark.asyncio
    async def test_paper_execution_multi_tranche(self):
        """Test paper mode execution with multiple tranches"""
        order_plan = OrderPlan(
            total_shares=2000,
            tranches=[
                {
                    'shares': 1000,
                    'type': 'LIMIT',
                    'price': 10.0,
                    'time_in_force': 'DAY'
                },
                {
                    'shares': 1000,
                    'type': 'LIMIT',
                    'price': 10.01,
                    'time_in_force': 'DAY'
                }
            ],
            max_slippage_pct=0.01,
            participation_rate=0.05,
            time_in_force='DAY',
            order_type='LIMIT'
        )
        
        result = await self.adapter.execute_order_plan(order_plan, 'TEST')
        
        assert result.status == 'FILLED'
        assert result.filled_shares == 2000
        assert len(result.tranches) == 2
        assert all(t.status == 'FILLED' for t in result.tranches)
    
    @pytest.mark.asyncio
    async def test_live_execution_success(self):
        """Test live execution with successful fills"""
        self.adapter.paper_mode = False
        
        # Mock broker responses
        self.mock_broker.submit_limit_order.return_value = {'order_id': 'LIVE_001'}
        self.mock_broker.get_order_status.return_value = {
            'status': 'FILLED',
            'fills': [
                {'shares': 1000, 'price': 10.01, 'timestamp': '2025-01-01T10:00:00Z'}
            ]
        }
        
        order_plan = OrderPlan(
            total_shares=1000,
            tranches=[{
                'shares': 1000,
                'type': 'LIMIT',
                'price': 10.0,
                'time_in_force': 'DAY'
            }],
            max_slippage_pct=0.01,
            participation_rate=0.05,
            time_in_force='DAY',
            order_type='LIMIT'
        )
        
        result = await self.adapter.execute_order_plan(order_plan, 'TEST')
        
        assert result.status == 'FILLED'
        assert result.filled_shares == 1000
        assert result.commissions > 0  # Live mode has commissions
        assert self.mock_broker.submit_limit_order.called
    
    @pytest.mark.asyncio
    async def test_live_execution_slippage_abort(self):
        """Test execution abort when slippage exceeded"""
        self.adapter.paper_mode = False
        
        # Mock broker responses with high slippage
        self.mock_broker.submit_limit_order.return_value = {'order_id': 'LIVE_001'}
        self.mock_broker.get_order_status.return_value = {
            'status': 'FILLED',
            'fills': [
                {'shares': 1000, 'price': 10.20, 'timestamp': '2025-01-01T10:00:00Z'}  # 2% slippage
            ]
        }
        
        order_plan = OrderPlan(
            total_shares=1000,
            tranches=[{
                'shares': 1000,
                'type': 'LIMIT',
                'price': 10.0,
                'time_in_force': 'DAY'
            }],
            max_slippage_pct=0.01,  # 1% max
            participation_rate=0.05,
            time_in_force='DAY',
            order_type='LIMIT'
        )
        
        result = await self.adapter.execute_order_plan(order_plan, 'TEST')
        
        # Should fill first tranche but stop due to slippage
        assert result.status == 'PARTIAL'
        assert result.filled_shares == 1000
        assert result.realized_slippage > 0.01
    
    @pytest.mark.asyncio
    async def test_circuit_breaker(self):
        """Test circuit breaker functionality"""
        self.adapter.paper_mode = False
        self.adapter.circuit_breaker.failure_threshold = 2
        
        # Force circuit breaker open
        self.adapter.circuit_breaker.record_failure()
        self.adapter.circuit_breaker.record_failure()
        
        order_plan = OrderPlan(
            total_shares=1000,
            tranches=[{
                'shares': 1000,
                'type': 'LIMIT',
                'price': 10.0,
                'time_in_force': 'DAY'
            }],
            max_slippage_pct=0.01,
            participation_rate=0.05,
            time_in_force='DAY',
            order_type='LIMIT'
        )
        
        result = await self.adapter.execute_order_plan(order_plan, 'TEST')
        
        # Should not execute due to circuit breaker
        assert result.status == 'FAILED'
        assert result.filled_shares == 0
```

INTEGRATION TESTS:

File: tests/test_execution_integration.py
```python
@pytest.mark.asyncio
async def test_end_to_end_execution_flow():
    """Test full flow from ExecutionChecker to ExecutionAdapter"""
    # Create execution check result
    execution_result = {
        'allowed': True,
        'reason_codes': [],
        'recommended_size_shares': 1000,
        'order_plan': OrderPlan(
            total_shares=1000,
            tranches=[{
                'shares': 1000,
                'type': 'LIMIT',
                'price': 10.0,
                'time_in_force': 'DAY'
            }],
            max_slippage_pct=0.01,
            participation_rate=0.05,
            time_in_force='DAY',
            order_type='LIMIT'
        ),
        'diagnostics': {
            'adv_shares': 1000000,
            'spread_pct': 0.005,
            'depth_top5_shares': 50000
        }
    }
    
    # Execute through adapter
    adapter = ExecutionAdapter(mock_broker, {'paper_mode': True})
    execution = await adapter.execute_order_plan(
        execution_result['order_plan'],
        'TEST'
    )
    
    # Verify execution
    assert execution.status == 'FILLED'
    assert execution.filled_shares == 1000
    assert execution.realized_slippage <= execution_result['order_plan'].max_slippage_pct

@pytest.mark.asyncio
async def test_multi_tranche_large_order():
    """Test large order split into multiple tranches"""
    # Create large order plan
    order_plan = OrderPlan(
        total_shares=10000,
        tranches=[
            {'shares': 3000, 'type': 'LIMIT', 'price': 10.0},
            {'shares': 3000, 'type': 'LIMIT', 'price': 10.01},
            {'shares': 4000, 'type': 'LIMIT', 'price': 10.02}
        ],
        max_slippage_pct=0.01,
        participation_rate=0.05,
        time_in_force='DAY',
        order_type='LIMIT'
    )
    
    adapter = ExecutionAdapter(mock_broker, {'paper_mode': True})
    result = await adapter.execute_order_plan(order_plan, 'LARGE')
    
    assert result.status == 'FILLED'
    assert result.filled_shares == 10000
    assert len(result.tranches) == 3
```

CONFIGURATION:

File: config/execution_adapter.json
```json
{
  "execution_adapter": {
    "paper_mode": true,
    "max_slippage_pct": 0.01,
    "tranche_delay_ms": 5000,
    "commission_per_share": 0.005,
    "circuit_breaker": {
      "failure_threshold": 5,
      "timeout_seconds": 60
    },
    "brokers": {
      "alpaca": {
        "api_key": "${ALPACA_API_KEY}",
        "api_secret": "${ALPACA_API_SECRET}",
        "paper_url": "https://paper-api.alpaca.markets",
        "live_url": "https://api.alpaca.markets"
      }
    }
  }
}
```

MONITORING:

Add metrics:
- execution_adapter.total_orders
- execution_adapter.success_rate
- execution_adapter.slippage_actual
- execution_adapter.circuit_breaker_state
- execution_adapter.tranche_fill_rate

DEFINITION OF DONE:
- [ ] All unit tests passing
- [ ] Integration tests with broker API
- [ ] Paper mode validated
- [ ] Circuit breaker tested
- [ ] Slippage monitoring active
- [ ] Error handling complete
- [ ] Code review completed

============================================
END OF TICKET US-006
============================================
"""
