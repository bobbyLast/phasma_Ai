"""
============================================================
ENGINEERING TICKET: US-009 - A/B Test Harness
============================================================

TITLE: Implement A/B Testing Framework for Weight Changes
OWNER: Quant Analytics Team
ESTIMATE: 5 days
PRIORITY: HIGH
DEPENDENCIES: US-003, US-006, US-007

OVERVIEW:
Build A/B testing framework that safely validates weight changes by splitting
traffic between control and test groups, collecting performance metrics, and
automatically determining statistical significance.

ACCEPTANCE CRITERIA:
1. ✅ Dynamic traffic allocation between control and test groups
2. ✅ Statistical significance calculation for key metrics
3. ✅ Automatic winner selection based on predefined criteria
4. ✅ Real-time monitoring and early stopping rules
5. ✅ Multi-metric evaluation with custom weights
6. ✅ Complete audit trail for regulatory compliance

IMPLEMENTATION DETAILS:

File: engines/ab_test_harness.py
```python
from typing import Dict, List, Optional, Tuple, Callable
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import asyncio
import logging
import numpy as np
from scipy import stats
from enum import Enum

logger = logging.getLogger(__name__)

class TestStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    STOPPED_EARLY = "stopped_early"
    FAILED = "failed"

class TestOutcome(Enum):
    CONTROL_WIN = "control_win"
    TEST_WIN = "test_win"
    INCONCLUSIVE = "inconclusive"
    NO_DIFFERENCE = "no_difference"

@dataclass
class TestConfig:
    test_id: str
    name: str
    description: str
    control_weights: Dict[str, float]
    test_weights: Dict[str, float]
    allocation_ratio: float  # Test group allocation (0.0-1.0)
    min_trades: int
    max_duration_days: int
    significance_level: float
    metrics: List[str]
    metric_weights: Dict[str, float]
    early_stopping_rules: Dict[str, Dict]
    target_improvement: Dict[str, float]  # Expected improvement per metric

@dataclass
class TestResult:
    test_id: str
    status: TestStatus
    outcome: Optional[TestOutcome]
    control_stats: Dict[str, Dict]
    test_stats: Dict[str, Dict]
    significance_tests: Dict[str, Dict]
    confidence_intervals: Dict[str, Tuple[float, float]]
    recommendation: str
    completed_at: Optional[datetime]
    total_trades: int
    duration_days: float

class ABTestHarness:
    def __init__(self, config: Dict, weight_manager, execution_adapter):
        self.config = config
        self.weight_manager = weight_manager
        self.execution_adapter = execution_adapter
        self.db_engine = create_engine(config['database_url'])
        
        # Active tests
        self.active_tests = {}
        self.test_history = []
        
        # Statistical parameters
        self.default_significance = config.get('default_significance', 0.05)
        self.min_effect_size = config.get('min_effect_size', 0.1)
        self.max_concurrent_tests = config.get('max_concurrent_tests', 5)
        
    async def create_test(self, test_config: TestConfig) -> str:
        """Create a new A/B test"""
        # Validate test configuration
        await self._validate_test_config(test_config)
        
        # Check for conflicts
        await self._check_test_conflicts(test_config)
        
        # Store test
        await self._store_test(test_config)
        
        # Initialize test tracking
        self.active_tests[test_config.test_id] = {
            'config': test_config,
            'status': TestStatus.PENDING,
            'start_time': None,
            'control_trades': [],
            'test_trades': [],
            'metrics': {metric: [] for metric in test_config.metrics}
        }
        
        logger.info(f"Created A/B test: {test_config.test_id}")
        return test_config.test_id
    
    async def start_test(self, test_id: str):
        """Start an A/B test"""
        if test_id not in self.active_tests:
            raise ValueError(f"Test {test_id} not found")
        
        test = self.active_tests[test_id]
        
        # Check if we can start
        if len([t for t in self.active_tests.values() 
                if t['status'] == TestStatus.RUNNING]) >= self.max_concurrent_tests:
            raise RuntimeError("Maximum concurrent tests reached")
        
        # Configure weight manager for A/B testing
        await self.weight_manager.configure_ab_test(
            test_id=test_id,
            control_weights=test['config'].control_weights,
            test_weights=test['config'].test_weights,
            allocation_ratio=test['config'].allocation_ratio
        )
        
        # Update status
        test['status'] = TestStatus.RUNNING
        test['start_time'] = datetime.now()
        
        # Store in database
        await self._update_test_status(test_id, TestStatus.RUNNING)
        
        logger.info(f"Started A/B test: {test_id}")
    
    async def record_trade(self, test_id: str, trade_result: Dict):
        """Record a trade result for A/B testing"""
        if test_id not in self.active_tests:
            return
        
        test = self.active_tests[test_id]
        
        if test['status'] != TestStatus.RUNNING:
            return
        
        # Determine group
        group = trade_result.get('ab_test_group', 'control')
        
        # Record trade
        trade_data = {
            'timestamp': datetime.now(),
            'trade_id': trade_result['trade_id'],
            'ticker': trade_result['ticker'],
            'group': group,
            'metrics': self._extract_trade_metrics(trade_result)
        }
        
        if group == 'control':
            test['control_trades'].append(trade_data)
        else:
            test['test_trades'].append(trade_data)
        
        # Update running metrics
        for metric, value in trade_data['metrics'].items():
            if metric in test['metrics']:
                test['metrics'][metric].append(value)
        
        # Check early stopping
        await self._check_early_stopping(test_id)
        
        # Check if test should complete
        await self._check_test_completion(test_id)
    
    async def stop_test(self, test_id: str, reason: str = "Manual stop"):
        """Stop an A/B test"""
        if test_id not in self.active_tests:
            raise ValueError(f"Test {test_id} not found")
        
        test = self.active_tests[test_id]
        
        # Update status
        test['status'] = TestStatus.STOPPED_EARLY
        
        # Generate results
        results = await self._calculate_test_results(test_id)
        results.recommendation = f"Test stopped early: {reason}"
        
        # Store results
        await self._store_test_results(results)
        
        # Clean up weight manager
        await self.weight_manager.cleanup_ab_test(test_id)
        
        logger.info(f"Stopped A/B test: {test_id} - {reason}")
    
    async def _check_early_stopping(self, test_id: str):
        """Check if test should stop early"""
        test = self.active_tests[test_id]
        config = test['config']
        
        for metric, rule in config.early_stopping_rules.items():
            if metric not in test['metrics']:
                continue
            
            # Check if we have enough data
            if len(test['metrics'][metric]) < rule.get('min_observations', 100):
                continue
            
            # Calculate current performance
            control_values = [t['metrics'].get(metric, 0) 
                            for t in test['control_trades'] 
                            if metric in t['metrics']]
            test_values = [t['metrics'].get(metric, 0) 
                         for t in test['test_trades'] 
                         if metric in t['metrics']]
            
            if len(control_values) == 0 or len(test_values) == 0:
                continue
            
            # Perform early stopping test
            control_mean = np.mean(control_values)
            test_mean = np.mean(test_values)
            
            # Check for overwhelming evidence
            if rule['type'] == 'superiority':
                if test_mean > control_mean * (1 + rule.get('threshold', 0.1)):
                    await self.stop_test(test_id, f"Early stop: {metric} superiority")
                    return
            elif rule['type'] == 'futility':
                if test_mean < control_mean * (1 - rule.get('threshold', 0.05)):
                    await self.stop_test(test_id, f"Early stop: {metric} futility")
                    return
    
    async def _check_test_completion(self, test_id: str):
        """Check if test should complete"""
        test = self.active_tests[test_id]
        config = test['config']
        
        # Check minimum trades
        total_trades = len(test['control_trades']) + len(test['test_trades'])
        if total_trades < config.min_trades:
            return
        
        # Check duration
        if test['start_time']:
            duration = (datetime.now() - test['start_time']).days
            if duration < config.max_duration_days:
                return
        
        # Check statistical significance
        significant = await self._check_statistical_significance(test_id)
        if not significant:
            return
        
        # Complete test
        await self._complete_test(test_id)
    
    async def _complete_test(self, test_id: str):
        """Complete an A/B test and generate results"""
        test = self.active_tests[test_id]
        
        # Update status
        test['status'] = TestStatus.COMPLETED
        
        # Calculate final results
        results = await self._calculate_test_results(test_id)
        
        # Determine winner
        results.outcome = await self._determine_winner(results)
        results.recommendation = self._generate_recommendation(results)
        
        # Store results
        await self._store_test_results(results)
        
        # Apply winning weights if conclusive
        if results.outcome in [TestOutcome.TEST_WIN, TestOutcome.CONTROL_WIN]:
            winning_weights = (test['config'].test_weights 
                             if results.outcome == TestOutcome.TEST_WIN 
                             else test['config'].control_weights)
            await self.weight_manager.apply_weights(
                winning_weights, 
                reason=f"A/B test winner: {test_id}"
            )
        
        # Clean up
        await self.weight_manager.cleanup_ab_test(test_id)
        
        # Move to history
        self.test_history.append(results)
        del self.active_tests[test_id]
        
        logger.info(f"Completed A/B test: {test_id} - Outcome: {results.outcome.value}")
    
    async def _calculate_test_results(self, test_id: str) -> TestResult:
        """Calculate comprehensive test results"""
        test = self.active_tests[test_id]
        config = test['config']
        
        # Calculate statistics for each group
        control_stats = {}
        test_stats = {}
        
        for metric in config.metrics:
            control_values = [t['metrics'].get(metric, 0) 
                            for t in test['control_trades'] 
                            if metric in t['metrics']]
            test_values = [t['metrics'].get(metric, 0) 
                         for t in test['test_trades'] 
                         if metric in t['metrics']]
            
            control_stats[metric] = self._calculate_statistics(control_values)
            test_stats[metric] = self._calculate_statistics(test_values)
        
        # Perform significance tests
        significance_tests = {}
        confidence_intervals = {}
        
        for metric in config.metrics:
            if metric in control_stats and metric in test_stats:
                sig_result = self._perform_significance_test(
                    control_stats[metric],
                    test_stats[metric],
                    config.significance_level
                )
                significance_tests[metric] = sig_result
                
                # Calculate confidence interval for difference
                ci = self._calculate_confidence_interval(
                    control_stats[metric],
                    test_stats[metric],
                    config.significance_level
                )
                confidence_intervals[metric] = ci
        
        # Determine duration
        duration = 0
        if test['start_time']:
            duration = (datetime.now() - test['start_time']).days
        
        return TestResult(
            test_id=test_id,
            status=test['status'],
            outcome=None,  # To be determined
            control_stats=control_stats,
            test_stats=test_stats,
            significance_tests=significance_tests,
            confidence_intervals=confidence_intervals,
            recommendation="",  # To be generated
            completed_at=datetime.now(),
            total_trades=len(test['control_trades']) + len(test['test_trades']),
            duration_days=duration
        )
    
    def _calculate_statistics(self, values: List[float]) -> Dict:
        """Calculate descriptive statistics"""
        if not values:
            return {}
        
        values_array = np.array(values)
        
        return {
            'count': len(values),
            'mean': np.mean(values_array),
            'std': np.std(values_array, ddof=1),
            'min': np.min(values_array),
            'max': np.max(values_array),
            'median': np.median(values_array),
            'q25': np.percentile(values_array, 25),
            'q75': np.percentile(values_array, 75)
        }
    
    def _perform_significance_test(self, control_stats: Dict, 
                                  test_stats: Dict, 
                                  alpha: float) -> Dict:
        """Perform statistical significance test"""
        # Use t-test for means
        t_stat, p_value = stats.ttest_ind(
            control_stats['values'] if 'values' in control_stats else [],
            test_stats['values'] if 'values' in test_stats else [],
            equal_var=False
        )
        
        # Calculate effect size (Cohen's d)
        pooled_std = np.sqrt(((len(control_stats) - 1) * control_stats['std']**2 + 
                             (len(test_stats) - 1) * test_stats['std']**2) / 
                            (len(control_stats) + len(test_stats) - 2))
        
        effect_size = (test_stats['mean'] - control_stats['mean']) / pooled_std
        
        return {
            'test_type': 't_test',
            't_statistic': t_stat,
            'p_value': p_value,
            'significant': p_value < alpha,
            'effect_size': effect_size,
            'power': self._calculate_statistical_power(effect_size, len(control_stats), len(test_stats))
        }
    
    def _calculate_confidence_interval(self, control_stats: Dict, 
                                      test_stats: Dict, 
                                      alpha: float) -> Tuple[float, float]:
        """Calculate confidence interval for difference"""
        # Standard error of difference
        se_diff = np.sqrt(
            (control_stats['std']**2 / len(control_stats)) + 
            (test_stats['std']**2 / len(test_stats))
        )
        
        # Difference in means
        diff = test_stats['mean'] - control_stats['mean']
        
        # Critical value for confidence interval
        t_critical = stats.t.ppf(1 - alpha/2, len(control_stats) + len(test_stats) - 2)
        
        # Confidence interval
        ci_lower = diff - t_critical * se_diff
        ci_upper = diff + t_critical * se_diff
        
        return (ci_lower, ci_upper)
    
    async def _determine_winner(self, results: TestResult) -> TestOutcome:
        """Determine test winner based on all metrics"""
        config = self.active_tests[results.test_id]['config']
        
        # Calculate weighted score
        control_score = 0
        test_score = 0
        
        for metric in config.metrics:
            if metric not in results.significance_tests:
                continue
            
            sig_test = results.significance_tests[metric]
            weight = config.metric_weights.get(metric, 1.0)
            
            if sig_test['significant']:
                if results.test_stats[metric]['mean'] > results.control_stats[metric]['mean']:
                    test_score += weight
                else:
                    control_score += weight
        
        # Determine outcome
        if test_score > control_score and test_score > 0:
            return TestOutcome.TEST_WIN
        elif control_score > test_score and control_score > 0:
            return TestOutcome.CONTROL_WIN
        elif test_score == 0 and control_score == 0:
            return TestOutcome.NO_DIFFERENCE
        else:
            return TestOutcome.INCONCLUSIVE
    
    def _generate_recommendation(self, results: TestResult) -> str:
        """Generate human-readable recommendation"""
        if results.outcome == TestOutcome.TEST_WIN:
            return "Test variant shows statistically significant improvement. Recommend deploying test weights."
        elif results.outcome == TestOutcome.CONTROL_WIN:
            return "Control variant outperforms test. Recommend keeping current weights."
        elif results.outcome == TestOutcome.NO_DIFFERENCE:
            return "No significant difference detected. Consider running longer test or test larger effect."
        else:
            return "Results inconclusive. Review metrics and consider test design."
    
    def _extract_trade_metrics(self, trade_result: Dict) -> Dict[str, float]:
        """Extract relevant metrics from trade result"""
        metrics = {}
        
        # Performance metrics
        if 'return' in trade_result:
            metrics['return'] = trade_result['return']
        if 'sharpe_ratio' in trade_result:
            metrics['sharpe_ratio'] = trade_result['sharpe_ratio']
        
        # Execution metrics
        if 'slippage' in trade_result:
            metrics['slippage'] = -trade_result['slippage']  # Lower slippage is better
        if 'fill_rate' in trade_result:
            metrics['fill_rate'] = trade_result['fill_rate']
        
        # Risk metrics
        if 'max_drawdown' in trade_result:
            metrics['max_drawdown'] = -trade_result['max_drawdown']  # Lower drawdown is better
        
        return metrics
    
    async def get_test_status(self, test_id: str) -> Dict:
        """Get current test status"""
        if test_id not in self.active_tests:
            # Check history
            for result in self.test_history:
                if result.test_id == test_id:
                    return asdict(result)
            return {}
        
        test = self.active_tests[test_id]
        
        return {
            'test_id': test_id,
            'status': test['status'].value,
            'config': asdict(test['config']),
            'start_time': test['start_time'],
            'control_trades': len(test['control_trades']),
            'test_trades': len(test['test_trades']),
            'current_metrics': {
                metric: {
                    'control_mean': np.mean([t['metrics'].get(metric, 0) 
                                           for t in test['control_trades'] 
                                           if metric in t['metrics']]) if test['control_trades'] else 0,
                    'test_mean': np.mean([t['metrics'].get(metric, 0) 
                                         for t in test['test_trades'] 
                                         if metric in t['metrics']]) if test['test_trades'] else 0
                }
                for metric in test['config'].metrics
            }
        }
    
    async def get_test_summary(self, test_id: str) -> Dict:
        """Get comprehensive test summary"""
        if test_id in self.active_tests:
            # Calculate interim results
            results = await self._calculate_test_results(test_id)
        else:
            # Get from history
            for result in self.test_history:
                if result.test_id == test_id:
                    results = result
                    break
            else:
                return {}
        
        return {
            'test_id': results.test_id,
            'status': results.status.value,
            'outcome': results.outcome.value if results.outcome else None,
            'recommendation': results.recommendation,
            'total_trades': results.total_trades,
            'duration_days': results.duration_days,
            'metrics_summary': {
                metric: {
                    'control': results.control_stats[metric],
                    'test': results.test_stats[metric],
                    'significance': results.significance_tests[metric],
                    'confidence_interval': results.confidence_intervals[metric]
                }
                for metric in results.control_stats.keys()
            }
        }
```

UNIT TESTS:

File: tests/test_ab_test_harness.py
```python
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta
import numpy as np
from engines.ab_test_harness import ABTestHarness, TestConfig, TestStatus, TestOutcome

class TestABTestHarness:
    def setup_method(self):
        self.config = {
            'database_url': 'sqlite:///:memory:',
            'default_significance': 0.05,
            'min_effect_size': 0.1,
            'max_concurrent_tests': 5
        }
        
        self.mock_weight_manager = AsyncMock()
        self.mock_execution_adapter = AsyncMock()
        
        self.harness = ABTestHarness(
            self.config,
            self.mock_weight_manager,
            self.mock_execution_adapter
        )
    
    def test_create_test(self):
        """Test A/B test creation"""
        test_config = TestConfig(
            test_id="TEST_001",
            name="Slippage Cap Test",
            description="Test increasing slippage cap",
            control_weights={"max_slippage_pct": 0.01},
            test_weights={"max_slippage_pct": 0.015},
            allocation_ratio=0.3,
            min_trades=100,
            max_duration_days=14,
            significance_level=0.05,
            metrics=["return", "slippage"],
            metric_weights={"return": 0.7, "slippage": 0.3},
            early_stopping_rules={},
            target_improvement={"return": 0.02}
        )
        
        test_id = asyncio.run(self.harness.create_test(test_config))
        
        assert test_id == "TEST_001"
        assert test_id in self.harness.active_tests
        assert self.harness.active_tests[test_id]['status'] == TestStatus.PENDING
    
    @pytest.mark.asyncio
    async def test_start_test(self):
        """Test starting an A/B test"""
        # Create test first
        test_config = TestConfig(
            test_id="TEST_002",
            name="Test Start",
            description="Test start functionality",
            control_weights={"param1": 0.1},
            test_weights={"param1": 0.2},
            allocation_ratio=0.5,
            min_trades=50,
            max_duration_days=7,
            significance_level=0.05,
            metrics=["return"],
            metric_weights={"return": 1.0},
            early_stopping_rules={},
            target_improvement={}
        )
        
        await self.harness.create_test(test_config)
        await self.harness.start_test("TEST_002")
        
        # Verify weight manager configured
        self.harness.weight_manager.configure_ab_test.assert_called_once()
        
        # Verify status updated
        assert self.harness.active_tests["TEST_002"]['status'] == TestStatus.RUNNING
        assert self.harness.active_tests["TEST_002"]['start_time'] is not None
    
    @pytest.mark.asyncio
    async def test_record_trade(self):
        """Test recording trade results"""
        # Setup test
        test_config = TestConfig(
            test_id="TEST_003",
            name="Trade Recording",
            description="Test trade recording",
            control_weights={"p1": 0.1},
            test_weights={"p1": 0.2},
            allocation_ratio=0.5,
            min_trades=10,
            max_duration_days=7,
            significance_level=0.05,
            metrics=["return"],
            metric_weights={"return": 1.0},
            early_stopping_rules={},
            target_improvement={}
        )
        
        await self.harness.create_test(test_config)
        await self.harness.start_test("TEST_003")
        
        # Record control trade
        control_trade = {
            'trade_id': 'T001',
            'ticker': 'AAPL',
            'ab_test_group': 'control',
            'return': 0.05,
            'slippage': 0.001
        }
        
        await self.harness.record_trade("TEST_003", control_trade)
        
        test = self.harness.active_tests["TEST_003"]
        assert len(test['control_trades']) == 1
        assert len(test['test_trades']) == 0
        
        # Record test trade
        test_trade = {
            'trade_id': 'T002',
            'ticker': 'GOOGL',
            'ab_test_group': 'test',
            'return': 0.07,
            'slippage': 0.0015
        }
        
        await self.harness.record_trade("TEST_003", test_trade)
        
        assert len(test['control_trades']) == 1
        assert len(test['test_trades']) == 1
    
    @pytest.mark.asyncio
    async def test_statistical_significance(self):
        """Test statistical significance calculation"""
        # Create test with completed trades
        test_config = TestConfig(
            test_id="TEST_004",
            name="Significance Test",
            description="Test statistical significance",
            control_weights={"p1": 0.1},
            test_weights={"p1": 0.2},
            allocation_ratio=0.5,
            min_trades=10,
            max_duration_days=7,
            significance_level=0.05,
            metrics=["return"],
            metric_weights={"return": 1.0},
            early_stopping_rules={},
            target_improvement={}
        )
        
        await self.harness.create_test(test_config)
        
        # Simulate trades with significant difference
        test = self.harness.active_tests["TEST_004"]
        
        # Control group: 5% average return
        for i in range(50):
            test['control_trades'].append({
                'timestamp': datetime.now(),
                'trade_id': f'C{i}',
                'ticker': 'TEST',
                'group': 'control',
                'metrics': {'return': np.random.normal(0.05, 0.02)}
            })
        
        # Test group: 7% average return (significant improvement)
        for i in range(50):
            test['test_trades'].append({
                'timestamp': datetime.now(),
                'trade_id': f'T{i}',
                'ticker': 'TEST',
                'group': 'test',
                'metrics': {'return': np.random.normal(0.07, 0.02)}
            })
        
        # Calculate results
        results = await self.harness._calculate_test_results("TEST_004")
        
        # Verify significance
        assert 'return' in results.significance_tests
        assert results.significance_tests['return']['significant'] == True
        assert results.significance_tests['return']['effect_size'] > self.harness.min_effect_size
    
    @pytest.mark.asyncio
    async def test_early_stopping(self):
        """Test early stopping functionality"""
        test_config = TestConfig(
            test_id="TEST_005",
            name="Early Stop Test",
            description="Test early stopping",
            control_weights={"p1": 0.1},
            test_weights={"p1": 0.2},
            allocation_ratio=0.5,
            min_trades=100,
            max_duration_days=14,
            significance_level=0.05,
            metrics=["return"],
            metric_weights={"return": 1.0},
            early_stopping_rules={
                "return": {
                    "type": "superiority",
                    "threshold": 0.1,
                    "min_observations": 50
                }
            },
            target_improvement={}
        )
        
        await self.harness.create_test(test_config)
        await self.harness.start_test("TEST_005")
        
        # Simulate overwhelming superiority
        test = self.harness.active_tests["TEST_005"]
        
        # Test group performing much better
        for i in range(60):
            # Control: 2% returns
            test['control_trades'].append({
                'timestamp': datetime.now(),
                'trade_id': f'C{i}',
                'group': 'control',
                'metrics': {'return': 0.02}
            })
            
            # Test: 15% returns (much higher)
            test['test_trades'].append({
                'timestamp': datetime.now(),
                'trade_id': f'T{i}',
                'group': 'test',
                'metrics': {'return': 0.15}
            })
        
        # Record a trade to trigger early stopping check
        await self.harness.record_trade("TEST_005", {
            'trade_id': 'T_LAST',
            'ab_test_group': 'test',
            'return': 0.15
        })
        
        # Test should be stopped early
        assert test['status'] == TestStatus.STOPPED_EARLY
    
    @pytest.mark.asyncio
    async def test_winner_determination(self):
        """Test winner determination logic"""
        # Create mock results
        from engines.ab_test_harness import TestResult
        
        results = TestResult(
            test_id="TEST_WINNER",
            status=TestStatus.COMPLETED,
            outcome=None,
            control_stats={
                'return': {
                    'mean': 0.05,
                    'std': 0.02,
                    'values': [0.04, 0.05, 0.06]
                }
            },
            test_stats={
                'return': {
                    'mean': 0.08,
                    'std': 0.02,
                    'values': [0.07, 0.08, 0.09]
                }
            },
            significance_tests={
                'return': {
                    'significant': True,
                    'effect_size': 1.5
                }
            },
            confidence_intervals={
                'return': (0.02, 0.04)
            },
            recommendation="",
            completed_at=datetime.now(),
            total_trades=100,
            duration_days=10
        )
        
        # Mock test config
        self.harness.active_tests["TEST_WINNER"] = {
            'config': Mock(
                metrics=["return"],
                metric_weights={"return": 1.0}
            )
        }
        
        outcome = await self.harness._determine_winner(results)
        
        assert outcome == TestOutcome.TEST_WIN
```

CONFIGURATION:

File: config/ab_test_harness.json
```json
{
  "ab_test_harness": {
    "default_significance": 0.05,
    "min_effect_size": 0.1,
    "max_concurrent_tests": 5,
    "early_stopping": {
      "enabled": true,
      "check_interval_hours": 4,
      "min_observations": 50
    },
    "metrics": {
      "return": {
        "weight": 0.6,
        "higher_is_better": true,
        "target_improvement": 0.02
      },
      "sharpe_ratio": {
        "weight": 0.3,
        "higher_is_better": true,
        "target_improvement": 0.2
      },
      "slippage": {
        "weight": 0.1,
        "higher_is_better": false,
        "target_improvement": -0.002
      }
    }
  }
}
```

DASHBOARD WIDGETS:

File: dashboards/ab_test_dashboard.py
```python
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

def create_test_progress_chart(test_data):
    """Create test progress visualization"""
    fig = go.Figure()
    
    # Add cumulative trades
    fig.add_trace(go.Scatter(
        x=test_data['dates'],
        y=test_data['control_trades_cumulative'],
        name='Control Group',
        line=dict(color='blue')
    ))
    
    fig.add_trace(go.Scatter(
        x=test_data['dates'],
        y=test_data['test_trades_cumulative'],
        name='Test Group',
        line=dict(color='red')
    ))
    
    fig.update_layout(
        title='A/B Test Progress',
        xaxis_title='Date',
        yaxis_title='Cumulative Trades'
    )
    
    return fig

def create_metric_comparison(control_stats, test_stats, metric_name):
    """Create metric comparison chart"""
    fig = go.Figure()
    
    # Box plots for distribution
    fig.add_trace(go.Box(
        y=control_stats['values'],
        name='Control',
        boxpoints='outliers'
    ))
    
    fig.add_trace(go.Box(
        y=test_stats['values'],
        name='Test',
        boxpoints='outliers'
    ))
    
    # Add mean lines
    fig.add_hline(
        y=control_stats['mean'],
        line_dash="dash",
        annotation_text=f"Control Mean: {control_stats['mean']:.3f}"
    )
    
    fig.add_hline(
        y=test_stats['mean'],
        line_dash="dash",
        annotation_text=f"Test Mean: {test_stats['mean']:.3f}"
    )
    
    fig.update_layout(
        title=f'{metric_name} Distribution Comparison',
        yaxis_title=metric_name
    )
    
    return fig
```

DEFINITION OF DONE:
- [ ] Test creation and validation
- [ ] Traffic allocation working
- [ ] Trade recording and grouping
- [ ] Statistical significance tests
- [ ] Early stopping rules
- [ ] Winner determination
- [ ] Dashboard widgets
- [ ] All unit tests passing
- [ ] Integration with weight manager
- [ ] Documentation complete

============================================
END OF TICKET US-009
============================================
"""
