"""
============================================================
ENGINEERING TICKET: US-008 - Automated Rollback Rules
============================================================

TITLE: Implement Automated Rollback System for Weight Changes
OWNER: Trading Systems Team
ESTIMATE: 3 days
PRIORITY: HIGH
DEPENDENCIES: US-003, US-006, US-007

OVERVIEW:
Implement automated rollback system that monitors deployed weight changes
and automatically reverts to safe defaults when performance thresholds are breached.

ACCEPTANCE CRITERIA:
1. ✅ Real-time monitoring of key performance metrics
2. ✅ Configurable rollback triggers with thresholds
3. ✅ Automatic weight reversion with audit trail
4. ✅ Alert notifications for operations team
5. ✅ Gradual and immediate rollback modes
6. ✅ Diagnostic capture for post-mortem analysis

IMPLEMENTATION DETAILS:

File: engines/rollback_monitor.py
```python
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import asyncio
import logging
from enum import Enum

logger = logging.getLogger(__name__)

class RollbackAction(Enum):
    IMMEDIATE = "immediate"
    GRADUAL = "gradual"
    PAUSE_NEW = "pause_new"

@dataclass
class RollbackTrigger:
    name: str
    metric: str
    threshold: float
    operator: str  # '>', '<', '>=', '<='
    window: int  # Number of trades/days
    consecutive: int  # Consecutive breaches
    action: RollbackAction
    enabled: bool = True

@dataclass
class RollbackEvent:
    event_id: str
    trigger_name: str
    metric_value: float
    threshold: float
    timestamp: datetime
    weights_before: Dict[str, float]
    weights_after: Dict[str, float]
    action_taken: RollbackAction
    reason: str
    trades_affected: int

class RollbackMonitor:
    def __init__(self, config: Dict, weight_manager, alert_service):
        self.config = config
        self.weight_manager = weight_manager
        self.alert_service = alert_service
        self.db_engine = create_engine(config['database_url'])
        
        # Rollback state
        self.active_rollbacks = {}
        self.rollback_history = []
        
        # Configure triggers
        self.triggers = self._load_triggers()
        
        # Monitoring intervals
        self.check_interval_seconds = config.get('check_interval_seconds', 60)
        self.performance_window_days = config.get('performance_window_days', 7)
        
        # Safety limits
        self.max_rollbacks_per_day = config.get('max_rollbacks_per_day', 3)
        self.rollback_cooldown_minutes = config.get('rollback_cooldown_minutes', 30)
    
    def _load_triggers(self) -> List[RollbackTrigger]:
        """Load rollback trigger configurations"""
        triggers = [
            # Performance triggers
            RollbackTrigger(
                name="performance_drop",
                metric="return_7d",
                threshold=-0.05,  # 5% drop
                operator="<",
                window=7,
                consecutive=3,
                action=RollbackAction.IMMEDIATE
            ),
            RollbackTrigger(
                name="sharpe_decline",
                metric="sharpe_ratio_7d",
                threshold=0.5,
                operator="<",
                window=7,
                consecutive=2,
                action=RollbackAction.GRADUAL
            ),
            
            # Execution triggers
            RollbackTrigger(
                name="slippage_breach",
                metric="avg_slippage_1d",
                threshold=0.015,  # 1.5%
                operator=">",
                window=1,
                consecutive=3,
                action=RollbackAction.IMMEDIATE
            ),
            RollbackTrigger(
                name="fill_rate_drop",
                metric="fill_rate_1d",
                threshold=0.8,
                operator="<",
                window=1,
                consecutive=5,
                action=RollbackAction.PAUSE_NEW
            ),
            
            # Risk triggers
            RollbackTrigger(
                name="max_drawdown_breach",
                metric="max_drawdown_7d",
                threshold=0.15,  # 15%
                operator=">",
                window=7,
                consecutive=1,
                action=RollbackAction.IMMEDIATE
            ),
            RollbackTrigger(
                name="volatility_spike",
                metric="volatility_ratio",
                threshold=2.0,  # 2x normal
                operator=">",
                window=1,
                consecutive=1,
                action=RollbackAction.GRADUAL
            ),
            
            # System triggers
            RollbackTrigger(
                name="error_rate_high",
                metric="error_rate_1h",
                threshold=0.1,  # 10%
                operator=">",
                window=1,
                consecutive=2,
                action=RollbackAction.IMMEDIATE
            ),
            RollbackTrigger(
                name="latency_high",
                metric="avg_latency_ms",
                threshold=5000,  # 5 seconds
                operator=">",
                window=1,
                consecutive=3,
                action=RollbackAction.PAUSE_NEW
            )
        ]
        
        return triggers
    
    async def start_monitoring(self):
        """Start the monitoring loop"""
        logger.info("Starting rollback monitoring")
        
        while True:
            try:
                await self._check_all_triggers()
                await asyncio.sleep(self.check_interval_seconds)
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await self.alert_service.send_critical(
                    "Rollback monitor error",
                    str(e)
                )
                await asyncio.sleep(10)  # Short sleep on error
    
    async def _check_all_triggers(self):
        """Check all configured triggers"""
        current_metrics = await self._gather_metrics()
        
        for trigger in self.triggers:
            if not trigger.enabled:
                continue
            
            try:
                await self._check_trigger(trigger, current_metrics)
            except Exception as e:
                logger.error(f"Error checking trigger {trigger.name}: {e}")
    
    async def _check_trigger(self, trigger: RollbackTrigger, metrics: Dict):
        """Check a specific trigger"""
        metric_value = metrics.get(trigger.metric)
        if metric_value is None:
            logger.warning(f"Metric {trigger.metric} not available")
            return
        
        # Check if threshold breached
        breached = self._evaluate_threshold(metric_value, trigger)
        
        if breached:
            logger.warning(f"Trigger {trigger.name} breached: {metric_value} {trigger.operator} {trigger.threshold}")
            
            # Check if we should rollback
            if await self._should_execute_rollback(trigger):
                await self._execute_rollback(trigger, metric_value, metrics)
    
    def _evaluate_threshold(self, value: float, trigger: RollbackTrigger) -> bool:
        """Evaluate if threshold is breached"""
        if trigger.operator == '>':
            return value > trigger.threshold
        elif trigger.operator == '<':
            return value < trigger.threshold
        elif trigger.operator == '>=':
            return value >= trigger.threshold
        elif trigger.operator == '<=':
            return value <= trigger.threshold
        else:
            return False
    
    async def _should_execute_rollback(self, trigger: RollbackTrigger) -> bool:
        """Check if rollback should be executed"""
        # Check cooldown
        if trigger.name in self.active_rollbacks:
            last_rollback = self.active_rollbacks[trigger.name]['timestamp']
            cooldown_expired = (datetime.now() - last_rollback) > timedelta(minutes=self.rollback_cooldown_minutes)
            if not cooldown_expired:
                logger.info(f"Trigger {trigger.name} in cooldown period")
                return False
        
        # Check daily limit
        today = datetime.now().date()
        today_count = sum(1 for r in self.rollback_history 
                         if r['timestamp'].date() == today)
        if today_count >= self.max_rollbacks_per_day:
            logger.warning(f"Daily rollback limit exceeded: {today_count}")
            return False
        
        # Check consecutive breaches
        recent_metrics = await self._get_recent_metrics(trigger.metric, trigger.window)
        consecutive_breaches = sum(1 for m in recent_metrics 
                                  if self._evaluate_threshold(m, trigger))
        
        return consecutive_breaches >= trigger.consecutive
    
    async def _execute_rollback(self, trigger: RollbackTrigger, metric_value: float, 
                               all_metrics: Dict):
        """Execute the rollback action"""
        event_id = f"RB_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{trigger.name}"
        
        # Capture current state
        weights_before = await self.weight_manager.get_current_weights()
        
        # Determine rollback target
        weights_after = await self._get_rollback_weights(trigger.action)
        
        # Execute rollback based on action type
        if trigger.action == RollbackAction.IMMEDIATE:
            await self._immediate_rollback(weights_after)
        elif trigger.action == RollbackAction.GRADUAL:
            await self._gradual_rollback(weights_before, weights_after)
        elif trigger.action == RollbackAction.PAUSE_NEW:
            await self._pause_new_trades()
        
        # Record event
        event = RollbackEvent(
            event_id=event_id,
            trigger_name=trigger.name,
            metric_value=metric_value,
            threshold=trigger.threshold,
            timestamp=datetime.now(),
            weights_before=weights_before,
            weights_after=weights_after,
            action_taken=trigger.action,
            reason=self._generate_rollback_reason(trigger, metric_value, all_metrics),
            trades_affected=await self._count_affected_trades()
        )
        
        # Store event
        await self._store_rollback_event(event)
        
        # Update active rollbacks
        self.active_rollbacks[trigger.name] = {
            'timestamp': datetime.now(),
            'event_id': event_id
        }
        
        # Send alert
        await self._send_rollback_alert(event)
        
        logger.info(f"Rollback executed: {event_id} - {trigger.name}")
    
    async def _immediate_rollback(self, weights: Dict[str, float]):
        """Execute immediate rollback to safe weights"""
        await self.weight_manager.apply_weights(weights, reason="IMMEDIATE_ROLLBACK")
        
        # Cancel all pending orders
        await self.weight_manager.cancel_all_orders()
    
    async def _gradual_rollback(self, current_weights: Dict[str, float], 
                               target_weights: Dict[str, float]):
        """Execute gradual rollback over time"""
        steps = 5  # 5 steps over 1 hour
        
        for step in range(steps):
            # Interpolate weights
            progress = (step + 1) / steps
            interim_weights = {}
            
            for key in target_weights:
                current = current_weights.get(key, 0)
                target = target_weights.get(key, 0)
                interim_weights[key] = current + (target - current) * progress
            
            # Apply interim weights
            await self.weight_manager.apply_weights(
                interim_weights, 
                reason=f"GRADUAL_ROLLBACK_STEP_{step+1}"
            )
            
            # Wait between steps
            await asyncio.sleep(720)  # 12 minutes
    
    async def _pause_new_trades(self):
        """Pause new trade execution"""
        await self.weight_manager.pause_execution(reason="ROLLBACK_PAUSE")
    
    async def _get_rollback_weights(self, action: RollbackAction) -> Dict[str, float]:
        """Get target weights for rollback"""
        if action == RollbackAction.IMMEDIATE:
            # Return to last known good weights
            return await self.weight_manager.get_safe_weights()
        elif action == RollbackAction.GRADUAL:
            # Return to conservative weights
            return await self.weight_manager.get_conservative_weights()
        else:
            # Keep current weights but pause new trades
            return await self.weight_manager.get_current_weights()
    
    async def _gather_metrics(self) -> Dict[str, float]:
        """Gather current performance metrics"""
        metrics = {}
        
        # Performance metrics
        metrics['return_7d'] = await self._calculate_return(7)
        metrics['sharpe_ratio_7d'] = await self._calculate_sharpe_ratio(7)
        metrics['max_drawdown_7d'] = await self._calculate_max_drawdown(7)
        
        # Execution metrics
        metrics['avg_slippage_1d'] = await self._get_avg_slippage(1)
        metrics['fill_rate_1d'] = await self._get_fill_rate(1)
        metrics['avg_latency_ms'] = await self._get_avg_latency(1)
        
        # Risk metrics
        metrics['volatility_ratio'] = await self._get_volatility_ratio()
        
        # System metrics
        metrics['error_rate_1h'] = await self._get_error_rate(1)
        
        return metrics
    
    async def _calculate_return(self, days: int) -> float:
        """Calculate return over N days"""
        query = """
        SELECT 
            SUM(CASE WHEN side = 'BUY' THEN -quantity * price ELSE quantity * price END) / 
            SUM(CASE WHEN side = 'BUY' THEN -quantity * price ELSE 0 END) as return_pct
        FROM trades 
        WHERE execution_date >= NOW() - INTERVAL '%s days'
        AND status = 'FILLED'
        """
        
        result = await self.db_engine.execute(query % days)
        return result.fetchone()[0] or 0.0
    
    async def _get_avg_slippage(self, days: int) -> float:
        """Get average slippage over N days"""
        query = """
        SELECT AVG(slippage_realized) as avg_slippage
        FROM trades 
        WHERE execution_date >= NOW() - INTERVAL '%s days'
        AND status = 'FILLED'
        """
        
        result = await self.db_engine.execute(query % days)
        return result.fetchone()[0] or 0.0
    
    async def _get_fill_rate(self, days: int) -> float:
        """Get fill rate over N days"""
        query = """
        SELECT 
            COUNT(CASE WHEN status = 'FILLED' THEN 1 END) / COUNT(*) as fill_rate
        FROM trades 
        WHERE execution_date >= NOW() - INTERVAL '%s days'
        """
        
        result = await self.db_engine.execute(query % days)
        return result.fetchone()[0] or 0.0
    
    async def _store_rollback_event(self, event: RollbackEvent):
        """Store rollback event in database"""
        query = """
        INSERT INTO rollback_events (
            event_id, trigger_name, metric_value, threshold, timestamp,
            weights_before, weights_after, action_taken, reason, trades_affected
        ) VALUES (
            %(event_id)s, %(trigger_name)s, %(metric_value)s, %(threshold)s,
            %(timestamp)s, %(weights_before)s, %(weights_after)s,
            %(action_taken)s, %(reason)s, %(trades_affected)s
        )
        """
        
        await self.db_engine.execute(query, asdict(event))
        self.rollback_history.append(asdict(event))
    
    async def _send_rollback_alert(self, event: RollbackEvent):
        """Send rollback notification"""
        message = f"""
        🚨 AUTOMATIC ROLLBACK TRIGGERED 🚨
        
        Event: {event.event_id}
        Trigger: {event.trigger_name}
        Metric: {event.metric_value} (threshold: {event.threshold})
        Action: {event.action_taken.value}
        Reason: {event.reason}
        
        Trades Affected: {event.trades_affected}
        Time: {event.timestamp}
        
        Check dashboard for details: https://phasma.ai/dashboards/rollback
        """
        
        await self.alert_service.send_critical(
            f"Rollback: {event.trigger_name}",
            message
        )
    
    def _generate_rollback_reason(self, trigger: RollbackTrigger, 
                                 metric_value: float, metrics: Dict) -> str:
        """Generate human-readable rollback reason"""
        reasons = {
            "performance_drop": f"7-day return dropped to {metric_value:.1%} (threshold: {trigger.threshold:.1%})",
            "sharpe_decline": f"Sharpe ratio declined to {metric_value:.2f} (threshold: {trigger.threshold:.2f})",
            "slippage_breach": f"Average slippage {metric_value:.2%} exceeded cap of {trigger.threshold:.2%}",
            "fill_rate_drop": f"Fill rate dropped to {metric_value:.1%} (threshold: {trigger.threshold:.1%})",
            "max_drawdown_breach": f"Maximum drawdown {metric_value:.1%} exceeded limit of {trigger.threshold:.1%}",
            "volatility_spike": f"Volatility {metric_value:.1f}x normal levels",
            "error_rate_high": f"Error rate {metric_value:.1%} exceeded threshold",
            "latency_high": f"Average latency {metric_value:.0f}ms exceeded threshold"
        }
        
        return reasons.get(trigger.name, f"Threshold breach: {metric_value} {trigger.operator} {trigger.threshold}")
    
    async def manual_rollback(self, reason: str, target_weights: Optional[Dict] = None):
        """Allow manual rollback by operations"""
        event_id = f"MANUAL_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        weights_before = await self.weight_manager.get_current_weights()
        weights_after = target_weights or await self.weight_manager.get_safe_weights()
        
        await self._immediate_rollback(weights_after)
        
        event = RollbackEvent(
            event_id=event_id,
            trigger_name="MANUAL",
            metric_value=0,
            threshold=0,
            timestamp=datetime.now(),
            weights_before=weights_before,
            weights_after=weights_after,
            action_taken=RollbackAction.IMMEDIATE,
            reason=f"Manual rollback: {reason}",
            trades_affected=await self._count_affected_trades()
        )
        
        await self._store_rollback_event(event)
        await self._send_rollback_alert(event)
    
    async def get_rollback_status(self) -> Dict:
        """Get current rollback system status"""
        return {
            'active_rollbacks': self.active_rollbacks,
            'total_rollbacks_24h': sum(1 for r in self.rollback_history 
                                    if r['timestamp'] > datetime.now() - timedelta(days=1)),
            'last_rollback': self.rollback_history[-1] if self.rollback_history else None,
            'triggers_status': {
                trigger.name: {
                    'enabled': trigger.enabled,
                    'last_check': datetime.now(),
                    'last_breach': self._get_last_breach(trigger.name)
                }
                for trigger in self.triggers
            }
        }
```

UNIT TESTS:

File: tests/test_rollback_monitor.py
```python
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta
from engines.rollback_monitor import RollbackMonitor, RollbackTrigger, RollbackAction

class TestRollbackMonitor:
    def setup_method(self):
        self.config = {
            'database_url': 'sqlite:///:memory:',
            'check_interval_seconds': 1,
            'max_rollbacks_per_day': 5,
            'rollback_cooldown_minutes': 30
        }
        
        self.mock_weight_manager = AsyncMock()
        self.mock_alert_service = AsyncMock()
        
        self.monitor = RollbackMonitor(
            self.config,
            self.mock_weight_manager,
            self.mock_alert_service
        )
    
    @pytest.mark.asyncio
    async def test_performance_drop_trigger(self):
        """Test rollback on performance drop"""
        # Mock metrics showing performance drop
        metrics = {
            'return_7d': -0.06,  # Below -5% threshold
            'sharpe_ratio_7d': 0.3,
            'avg_slippage_1d': 0.01
        }
        
        trigger = RollbackTrigger(
            name="performance_drop",
            metric="return_7d",
            threshold=-0.05,
            operator="<",
            window=7,
            consecutive=3,
            action=RollbackAction.IMMEDIATE
        )
        
        # Mock consecutive breaches
        with patch.object(self.monitor, '_get_recent_metrics', 
                         return_value=[-0.06, -0.07, -0.08]):
            with patch.object(self.monitor, '_should_execute_rollback', 
                             return_value=True):
                with patch.object(self.monitor, '_execute_rollback') as mock_execute:
                    await self.monitor._check_trigger(trigger, metrics)
                    
                    # Verify rollback executed
                    mock_execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_slippage_breach_immediate_rollback(self):
        """Test immediate rollback on slippage breach"""
        metrics = {'avg_slippage_1d': 0.02}  # Above 1.5% threshold
        
        trigger = RollbackTrigger(
            name="slippage_breach",
            metric="avg_slippage_1d",
            threshold=0.015,
            operator=">",
            window=1,
            consecutive=3,
            action=RollbackAction.IMMEDIATE
        )
        
        with patch.object(self.monitor, '_should_execute_rollback', 
                         return_value=True):
            with patch.object(self.monitor, '_execute_rollback') as mock_execute:
                await self.monitor._check_trigger(trigger, metrics)
                
                # Verify immediate rollback action
                mock_execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_gradual_rollback_execution(self):
        """Test gradual rollback steps"""
        current_weights = {'max_slippage_pct': 0.015, 'position_size': 10000}
        target_weights = {'max_slippage_pct': 0.01, 'position_size': 5000}
        
        with patch.object(self.monitor, 'weight_manager') as mock_manager:
            await self.monitor._gradual_rollback(current_weights, target_weights)
            
            # Verify 5 steps executed
            assert mock_manager.apply_weights.call_count == 5
            
            # Verify weights interpolated correctly
            calls = mock_manager.apply_weights.call_args_list
            step3_weights = calls[2][0][0]  # Third step
            
            # Should be 60% of the way to target
            expected_slippage = 0.015 + (0.01 - 0.015) * 0.6
            assert abs(step3_weights['max_slippage_pct'] - expected_slippage) < 0.001
    
    @pytest.mark.asyncio
    async def test_cooldown_period(self):
        """Test rollback cooldown prevents excessive rollbacks"""
        # Simulate recent rollback
        self.monitor.active_rollbacks['performance_drop'] = {
            'timestamp': datetime.now() - timedelta(minutes=10),  # 10 minutes ago
            'event_id': 'TEST_001'
        }
        
        # Try to rollback again
        should_rollback = await self.monitor._should_execute_rollback(
            RollbackTrigger(
                name="performance_drop",
                metric="return_7d",
                threshold=-0.05,
                operator="<",
                window=7,
                consecutive=3,
                action=RollbackAction.IMMEDIATE
            )
        )
        
        # Should not rollback due to cooldown
        assert not should_rollback
    
    @pytest.mark.asyncio
    async def test_daily_limit_enforcement(self):
        """Test daily rollback limit"""
        # Simulate hitting daily limit
        today = datetime.now().date()
        for i in range(5):  # Max rollbacks per day
            self.monitor.rollback_history.append({
                'timestamp': datetime.now(),
                'trigger_name': f'test_{i}'
            })
        
        # Try another rollback
        should_rollback = await self.monitor._should_execute_rollback(
            RollbackTrigger(
                name="test_trigger",
                metric="test_metric",
                threshold=0,
                operator=">",
                window=1,
                consecutive=1,
                action=RollbackAction.IMMEDIATE
            )
        )
        
        # Should not rollback due to daily limit
        assert not should_rollback
    
    @pytest.mark.asyncio
    async def test_manual_rollback(self):
        """Test manual rollback functionality"""
        reason = "Manual testing"
        target_weights = {'max_slippage_pct': 0.01}
        
        await self.monitor.manual_rollback(reason, target_weights)
        
        # Verify immediate rollback called
        self.monitor.weight_manager.cancel_all_orders.assert_called_once()
        
        # Verify event stored
        assert len(self.monitor.rollback_history) == 1
        assert self.monitor.rollback_history[0]['trigger_name'] == 'MANUAL'
        assert 'Manual testing' in self.monitor.rollback_history[0]['reason']
    
    def test_threshold_evaluation(self):
        """Test threshold evaluation logic"""
        trigger = RollbackTrigger(
            name="test",
            metric="test_metric",
            threshold=0.05,
            operator=">",
            window=1,
            consecutive=1,
            action=RollbackAction.IMMEDIATE
        )
        
        # Test operators
        assert self.monitor._evaluate_threshold(0.06, trigger) == True
        assert self.monitor._evaluate_threshold(0.04, trigger) == False
        
        trigger.operator = "<"
        assert self.monitor._evaluate_threshold(0.04, trigger) == True
        assert self.monitor._evaluate_threshold(0.06, trigger) == False
        
        trigger.operator = ">="
        assert self.monitor._evaluate_threshold(0.05, trigger) == True
        assert self.monitor._evaluate_threshold(0.06, trigger) == True
        assert self.monitor._evaluate_threshold(0.04, trigger) == False
```

CONFIGURATION:

File: config/rollback_monitor.json
```json
{
  "rollback_monitor": {
    "check_interval_seconds": 60,
    "performance_window_days": 7,
    "max_rollbacks_per_day": 3,
    "rollback_cooldown_minutes": 30,
    "triggers": {
      "performance_drop": {
        "enabled": true,
        "threshold": -0.05,
        "consecutive": 3,
        "action": "immediate"
      },
      "slippage_breach": {
        "enabled": true,
        "threshold": 0.015,
        "consecutive": 3,
        "action": "immediate"
      },
      "sharpe_decline": {
        "enabled": true,
        "threshold": 0.5,
        "consecutive": 2,
        "action": "gradual"
      }
    }
  }
}
```

MONITORING DASHBOARD:

File: dashboards/rollback_monitoring.py
```python
import plotly.graph_objects as go
import pandas as pd

def create_rollback_timeline(rollback_events):
    """Create rollback event timeline"""
    fig = go.Figure()
    
    # Add events
    for event in rollback_events:
        fig.add_shape(
            type="line",
            x0=event['timestamp'],
            x1=event['timestamp'],
            y0=0,
            y1=1,
            line=dict(color="red", width=2)
        )
        fig.add_annotation(
            x=event['timestamp'],
            y=1,
            text=event['trigger_name'],
            showarrow=True,
            arrowhead=1
        )
    
    fig.update_layout(
        title="Rollback Events Timeline",
        xaxis_title="Time",
        yaxis_title="System Status",
        showlegend=False
    )
    
    return fig

def create_trigger_status_panel(triggers):
    """Create trigger status visualization"""
    status_data = []
    
    for trigger in triggers:
        status_data.append({
            'trigger': trigger.name,
            'status': 'Active' if trigger.enabled else 'Disabled',
            'last_breach': trigger.last_breach or 'Never',
            'breach_count': trigger.breach_count
        })
    
    return pd.DataFrame(status_data)
```

DEFINITION OF DONE:
- [ ] All rollback triggers implemented
- [ ] Immediate rollback working
- [ ] Gradual rollback with steps
- [ ] Cooldown and limits enforced
- [ ] Alert integration complete
- [ ] Manual rollback endpoint
- [ ] Dashboard widgets created
- [ ] All unit tests passing
- [ ] Integration tests with weight manager
- [ ] Documentation updated

============================================
END OF TICKET US-008
============================================
"""
