"""
============================================================
ENGINEERING TICKET: US-007 - Post-Trade Analytics for Weight Tuning
============================================================

TITLE: Automated Post-Trade Analytics to Feed US-004 Weight Tuning
OWNER: Quant Analytics Team
ESTIMATE: 4 days
PRIORITY: MEDIUM
DEPENDENCIES: US-003, US-004, US-006

OVERVIEW:
Build automated analytics pipeline that processes executed trades, compares
realized metrics against models, and generates weight adjustment recommendations
for the ExecutionChecker and Confluence scoring.

ACCEPTANCE CRITERIA:
1. ✅ Daily post-trade analysis for all executed trades
2. ✅ Slippage model accuracy tracking and drift detection
3. ✅ Alpha decay analysis by signal type and confidence
4. ✅ Human gate decision performance analysis
5. ✅ Automatic weight adjustment recommendations
6. ✅ Weekly performance report generation

IMPLEMENTATION DETAILS:

File: analytics/post_trade_analytics.py
```python
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from sqlalchemy import create_engine
import logging

logger = logging.getLogger(__name__)

@dataclass
class TradePerformance:
    trade_id: str
    ticker: str
    signal_date: datetime
    execution_date: datetime
    signal_strength: float
    execution_confidence: float
    entry_price: float
    current_price: float
    max_price: float
    min_price: float
    realized_return: float
    max_return: float
    max_drawdown: float
    holding_days: int
    slippage_estimated: float
    slippage_realized: float
    market_volatility: float
    sector_volatility: float
    signal_type: str
    human_decision: str
    human_reason: str

@dataclass
class ModelAccuracy:
    metric_name: str
    predicted: float
    realized: float
    error_pct: float
    accuracy_score: float
    drift_detected: bool

@dataclass
class WeightRecommendation:
    component: str  # e.g., 'execution_slippage_cap', 'confluence_insider_weight'
    current_value: float
    recommended_value: float
    confidence: float
    reasoning: str
    supporting_metrics: Dict[str, float]

class PostTradeAnalytics:
    def __init__(self, config: Dict):
        self.config = config
        self.db_engine = create_engine(config['database_url'])
        self.lookback_days = config.get('lookback_days', 90)
        self.min_trades_for_analysis = config.get('min_trades_for_analysis', 20)
        
        # Analysis thresholds
        self.slippage_tolerance = config.get('slippage_tolerance', 0.002)
        self.return_target = config.get('return_target', 0.10)
        self.max_drawdown_limit = config.get('max_drawdown_limit', 0.15)
    
    def run_daily_analysis(self, analysis_date: datetime = None) -> Dict:
        """Run complete post-trade analysis for given date"""
        if analysis_date is None:
            analysis_date = datetime.now() - timedelta(days=1)
        
        logger.info(f"Running post-trade analytics for {analysis_date.date()}")
        
        # 1. Fetch executed trades
        trades = self._fetch_executed_trades(analysis_date)
        
        if len(trades) < self.min_trades_for_analysis:
            logger.warning(f"Insufficient trades for analysis: {len(trades)}")
            return self._generate_insufficient_data_report(len(trades))
        
        # 2. Calculate performance metrics
        trade_performance = [self._calculate_trade_performance(t) for t in trades]
        
        # 3. Analyze model accuracy
        model_accuracy = self._analyze_model_accuracy(trade_performance)
        
        # 4. Analyze human gate decisions
        human_analysis = self._analyze_human_decisions(trade_performance)
        
        # 5. Generate weight recommendations
        weight_recommendations = self._generate_weight_recommendations(
            trade_performance, model_accuracy, human_analysis
        )
        
        # 6. Create comprehensive report
        report = {
            'analysis_date': analysis_date.isoformat(),
            'trade_count': len(trades),
            'performance_summary': self._summarize_performance(trade_performance),
            'model_accuracy': [asdict(m) for m in model_accuracy],
            'human_gate_analysis': human_analysis,
            'weight_recommendations': [asdict(w) for w in weight_recommendations],
            'top_performers': self._get_top_performers(trade_performance),
            'worst_performers': self._get_worst_performers(trade_performance),
            'risk_metrics': self._calculate_risk_metrics(trade_performance)
        }
        
        # 7. Store results
        self._store_analysis_results(report)
        
        # 8. Send alerts if needed
        self._check_and_send_alerts(report)
        
        return report
    
    def _fetch_executed_trades(self, analysis_date: datetime) -> List[Dict]:
        """Fetch all trades executed up to analysis date"""
        cutoff_date = analysis_date - timedelta(days=self.lookback_days)
        
        query = """
        SELECT 
            t.trade_id,
            t.ticker,
            t.signal_date,
            t.execution_date,
            t.signal_strength,
            t.execution_confidence,
            t.entry_price,
            t.signal_type,
            t.human_decision,
            t.human_reason,
            t.slippage_estimated,
            t.slippage_realized,
            p.price as current_price,
            p.max_price_30d as max_price,
            p.min_price_30d as min_price,
            m.volatility as market_volatility,
            s.volatility as sector_volatility
        FROM trades t
        LEFT JOIN price_history p ON t.ticker = p.ticker 
            AND p.date = CURRENT_DATE
        LEFT JOIN market_data m ON m.date = t.execution_date
        LEFT JOIN sector_volatility s ON s.ticker = t.ticker 
            AND s.date = t.execution_date
        WHERE t.execution_date BETWEEN %s AND %s
        AND t.status = 'FILLED'
        ORDER BY t.execution_date DESC
        """
        
        df = pd.read_sql(query, self.db_engine, params=(cutoff_date, analysis_date))
        return df.to_dict('records')
    
    def _calculate_trade_performance(self, trade: Dict) -> TradePerformance:
        """Calculate comprehensive performance metrics for a trade"""
        current_price = trade['current_price'] or trade['entry_price']
        max_price = trade['max_price'] or trade['entry_price']
        min_price = trade['min_price'] or trade['entry_price']
        
        # Returns
        realized_return = (current_price - trade['entry_price']) / trade['entry_price']
        max_return = (max_price - trade['entry_price']) / trade['entry_price']
        max_drawdown = (trade['entry_price'] - min_price) / trade['entry_price']
        
        # Holding period
        holding_days = (datetime.now() - trade['execution_date']).days
        
        return TradePerformance(
            trade_id=trade['trade_id'],
            ticker=trade['ticker'],
            signal_date=trade['signal_date'],
            execution_date=trade['execution_date'],
            signal_strength=trade['signal_strength'],
            execution_confidence=trade['execution_confidence'],
            entry_price=trade['entry_price'],
            current_price=current_price,
            max_price=max_price,
            min_price=min_price,
            realized_return=realized_return,
            max_return=max_return,
            max_drawdown=max_drawdown,
            holding_days=holding_days,
            slippage_estimated=trade['slippage_estimated'],
            slippage_realized=trade['slippage_realized'],
            market_volatility=trade['market_volatility'],
            sector_volatility=trade['sector_volatility'],
            signal_type=trade['signal_type'],
            human_decision=trade['human_decision'],
            human_reason=trade['human_reason']
        )
    
    def _analyze_model_accuracy(self, trades: List[TradePerformance]) -> List[ModelAccuracy]:
        """Analyze accuracy of various models"""
        accuracy_metrics = []
        
        # Slippage model accuracy
        slippage_errors = [abs(t.slippage_realized - t.slippage_estimated) 
                          for t in trades]
        avg_slippage_error = np.mean(slippage_errors)
        slippage_accuracy = max(0, 1 - avg_slippage_error / self.slippage_tolerance)
        
        accuracy_metrics.append(ModelAccuracy(
            metric_name='slippage_model',
            predicted=np.mean([t.slippage_estimated for t in trades]),
            realized=np.mean([t.slippage_realized for t in trades]),
            error_pct=avg_slippage_error * 100,
            accuracy_score=slippage_accuracy,
            drift_detected=avg_slippage_error > self.slippage_tolerance * 2
        ))
        
        # Signal strength vs returns correlation
        strengths = [t.signal_strength for t in trades]
        returns = [t.realized_return for t in trades]
        correlation = np.corrcoef(strengths, returns)[0, 1]
        
        accuracy_metrics.append(ModelAccuracy(
            metric_name='signal_strength_correlation',
            predicted=correlation,
            realized=0.3,  # Target correlation
            error_pct=abs(correlation - 0.3) * 100,
            accuracy_score=max(0, 1 - abs(correlation - 0.3) / 0.3),
            drift_detected=correlation < 0.1
        ))
        
        # Execution confidence vs fill rate
        confidences = [t.execution_confidence for t in trades]
        fill_rates = [1.0 if t.slippage_realized < self.slippage_tolerance else 0.0 
                     for t in trades]
        fill_correlation = np.corrcoef(confidences, fill_rates)[0, 1]
        
        accuracy_metrics.append(ModelAccuracy(
            metric_name='execution_confidence_fill_rate',
            predicted=fill_correlation,
            realized=0.5,  # Target correlation
            error_pct=abs(fill_correlation - 0.5) * 100,
            accuracy_score=max(0, 1 - abs(fill_correlation - 0.5) / 0.5),
            drift_detected=fill_correlation < 0.2
        ))
        
        return accuracy_metrics
    
    def _analyze_human_decisions(self, trades: List[TradePerformance]) -> Dict:
        """Analyze human gate decision effectiveness"""
        approved = [t for t in trades if t.human_decision == 'APPROVE']
        rejected = [t for t in trades if t.human_decision == 'REJECT']
        
        # Calculate performance by decision
        approved_returns = [t.realized_return for t in approved]
        rejected_returns = [t.realized_return for t in rejected]
        
        # Decision accuracy (would rejected trades have performed poorly?)
        if rejected_returns:
            rejected_performance = np.mean(rejected_returns)
            avoided_losses = sum(1 for r in rejected_returns if r < -0.05)
        else:
            rejected_performance = 0
            avoided_losses = 0
        
        # Approval efficiency
        if approved_returns:
            approved_performance = np.mean(approved_returns)
            profitable_approvals = sum(1 for r in approved_returns if r > 0)
        else:
            approved_performance = 0
            profitable_approvals = 0
        
        # Reason code analysis
        reason_performance = {}
        for trade in trades:
            reason = trade.human_reason or 'UNKNOWN'
            if reason not in reason_performance:
                reason_performance[reason] = []
            reason_performance[reason].append(trade.realized_return)
        
        reason_avg_performance = {
            reason: np.mean(returns) 
            for reason, returns in reason_performance.items()
        }
        
        return {
            'total_decisions': len(trades),
            'approval_rate': len(approved) / len(trades),
            'approved_performance': approved_performance,
            'rejected_performance': rejected_performance,
            'avoided_losses': avoided_losses,
            'profitable_approvals': profitable_approvals,
            'decision_efficiency': (approved_performance - rejected_performance),
            'reason_code_performance': reason_avg_performance,
            'avg_review_time_hours': self._calculate_avg_review_time(trades)
        }
    
    def _generate_weight_recommendations(self, trades: List[TradePerformance],
                                       model_accuracy: List[ModelAccuracy],
                                       human_analysis: Dict) -> List[WeightRecommendation]:
        """Generate data-driven weight adjustment recommendations"""
        recommendations = []
        
        # Check slippage model
        slippage_acc = next(m for m in model_accuracy if m.metric_name == 'slippage_model')
        if slippage_acc.drift_detected:
            current_cap = self.config.get('max_slippage_pct', 0.01)
            recommended_cap = current_cap * 1.2  # Loosen by 20%
            
            recommendations.append(WeightRecommendation(
                component='max_slippage_pct',
                current_value=current_cap,
                recommended_value=recommended_cap,
                confidence=0.8,
                reasoning=f'Slippage model error ({slippage_acc.error_pct:.1f}%) exceeds tolerance',
                supporting_metrics={
                    'avg_error': slippage_acc.error_pct,
                    'accuracy_score': slippage_acc.accuracy_score
                }
            ))
        
        # Check signal strength correlation
        signal_corr = next(m for m in model_accuracy if m.metric_name == 'signal_strength_correlation')
        if signal_corr.accuracy_score < 0.5:
            current_weight = self.config.get('insider_signal_weight', 0.5)
            recommended_weight = current_weight * 0.8  # Reduce by 20%
            
            recommendations.append(WeightRecommendation(
                component='insider_signal_weight',
                current_value=current_weight,
                recommended_value=recommended_weight,
                confidence=0.7,
                reasoning=f'Signal strength correlation ({signal_corr.predicted:.2f}) below target',
                supporting_metrics={
                    'correlation': signal_corr.predicted,
                    'accuracy_score': signal_corr.accuracy_score
                }
            ))
        
        # Check human gate efficiency
        if human_analysis['decision_efficiency'] < 0:
            current_threshold = self.config.get('human_gate_threshold', 0.5)
            recommended_threshold = current_threshold * 0.9  # Tighten by 10%
            
            recommendations.append(WeightRecommendation(
                component='human_gate_threshold',
                current_value=current_threshold,
                recommended_value=recommended_threshold,
                confidence=0.6,
                reasoning=f'Human decisions reducing alpha ({human_analysis["decision_efficiency"]:.2%})',
                supporting_metrics={
                    'decision_efficiency': human_analysis['decision_efficiency'],
                    'approval_rate': human_analysis['approval_rate']
                }
            ))
        
        # Check position sizing
        avg_return = np.mean([t.realized_return for t in trades])
        if avg_return > self.return_target:
            current_size_limit = self.config.get('max_position_pct', 0.02)
            recommended_size = current_size_limit * 1.1  # Increase by 10%
            
            recommendations.append(WeightRecommendation(
                component='max_position_pct',
                current_value=current_size_limit,
                recommended_value=recommended_size,
                confidence=0.5,
                reasoning=f'Strong performance ({avg_return:.1%}) suggests capacity for larger positions',
                supporting_metrics={
                    'avg_return': avg_return,
                    'return_target': self.return_target
                }
            ))
        
        return recommendations
    
    def _summarize_performance(self, trades: List[TradePerformance]) -> Dict:
        """Generate performance summary statistics"""
        returns = [t.realized_return for t in trades]
        
        return {
            'total_trades': len(trades),
            'avg_return': np.mean(returns),
            'median_return': np.median(returns),
            'std_return': np.std(returns),
            'sharpe_ratio': np.mean(returns) / np.std(returns) if np.std(returns) > 0 else 0,
            'win_rate': sum(1 for r in returns if r > 0) / len(returns),
            'profit_factor': sum(r for r in returns if r > 0) / abs(sum(r for r in returns if r < 0)) if any(r < 0 for r in returns) else float('inf'),
            'max_return': max(returns),
            'min_return': min(returns),
            'avg_holding_days': np.mean([t.holding_days for t in trades])
        }
    
    def _get_top_performers(self, trades: List[TradePerformance], limit: int = 10) -> List[Dict]:
        """Get top performing trades"""
        sorted_trades = sorted(trades, key=lambda t: t.realized_return, reverse=True)
        return [asdict(t) for t in sorted_trades[:limit]]
    
    def _get_worst_performers(self, trades: List[TradePerformance], limit: int = 10) -> List[Dict]:
        """Get worst performing trades"""
        sorted_trades = sorted(trades, key=lambda t: t.realized_return)
        return [asdict(t) for t in sorted_trades[:limit]]
    
    def _calculate_risk_metrics(self, trades: List[TradePerformance]) -> Dict:
        """Calculate risk-related metrics"""
        returns = [t.realized_return for t in trades]
        max_drawdowns = [t.max_drawdown for t in trades]
        
        # VaR calculation (5%)
        var_5 = np.percentile(returns, 5)
        
        # Maximum consecutive losses
        consecutive_losses = self._calculate_max_consecutive_losses(returns)
        
        return {
            'value_at_risk_5pct': var_5,
            'max_consecutive_losses': consecutive_losses,
            'avg_max_drawdown': np.mean(max_drawdowns),
            'drawdown_breach_rate': sum(1 for dd in max_drawdowns if dd > self.max_drawdown_limit) / len(max_drawdowns),
            'volatility_adjusted_return': np.mean(returns) / np.std(returns) if np.std(returns) > 0 else 0
        }
    
    def _calculate_max_consecutive_losses(self, returns: List[float]) -> int:
        """Calculate maximum consecutive losing trades"""
        max_consecutive = 0
        current_consecutive = 0
        
        for r in returns:
            if r < 0:
                current_consecutive += 1
                max_consecutive = max(max_consecutive, current_consecutive)
            else:
                current_consecutive = 0
        
        return max_consecutive
    
    def _store_analysis_results(self, report: Dict):
        """Store analysis results in database"""
        # Store in analytics table
        df = pd.DataFrame([report])
        df.to_sql('post_trade_analysis', self.db_engine, if_exists='append', index=False)
        
        # Store weight recommendations
        if report['weight_recommendations']:
            recommendations_df = pd.DataFrame(report['weight_recommendations'])
            recommendations_df.to_sql('weight_recommendations', self.db_engine, 
                                     if_exists='append', index=False)
        
        logger.info(f"Stored analysis results for {report['analysis_date']}")
    
    def _check_and_send_alerts(self, report: Dict):
        """Check for alert conditions and send notifications"""
        alerts = []
        
        # Performance alerts
        if report['performance_summary']['win_rate'] < 0.3:
            alerts.append({
                'type': 'PERFORMANCE',
                'severity': 'WARNING',
                'message': f"Low win rate: {report['performance_summary']['win_rate']:.1%}"
            })
        
        # Model drift alerts
        for accuracy in report['model_accuracy']:
            if accuracy.drift_detected:
                alerts.append({
                    'type': 'MODEL_DRIFT',
                    'severity': 'CRITICAL',
                    'message': f"Model drift detected: {accuracy.metric_name}"
                })
        
        # Risk alerts
        if report['risk_metrics']['drawdown_breach_rate'] > 0.1:
            alerts.append({
                'type': 'RISK',
                'severity': 'WARNING',
                'message': f"High drawdown breach rate: {report['risk_metrics']['drawdown_breach_rate']:.1%}"
            })
        
        # Send alerts
        for alert in alerts:
            self._send_alert(alert)
    
    def _send_alert(self, alert: Dict):
        """Send alert notification"""
        # Integration with alerting system
        logger.warning(f"ALERT: {alert['message']}")
        # TODO: Send to Slack/PagerDuty
    
    def _generate_insufficient_data_report(self, trade_count: int) -> Dict:
        """Generate report when insufficient data available"""
        return {
            'analysis_date': datetime.now().isoformat(),
            'trade_count': trade_count,
            'status': 'INSUFFICIENT_DATA',
            'message': f'Need at least {self.min_trades_for_analysis} trades, got {trade_count}'
        }
    
    def _calculate_avg_review_time(self, trades: List[TradePerformance]) -> float:
        """Calculate average human gate review time"""
        # This would come from human gate logs
        # Placeholder implementation
        return 2.5  # hours
    
    def generate_weekly_report(self, week_end: datetime = None) -> Dict:
        """Generate comprehensive weekly performance report"""
        if week_end is None:
            week_end = datetime.now()
        
        week_start = week_end - timedelta(days=7)
        
        # Run daily analysis for each day in week
        daily_reports = []
        current_date = week_start
        
        while current_date < week_end:
            daily_report = self.run_daily_analysis(current_date)
            daily_reports.append(daily_report)
            current_date += timedelta(days=1)
        
        # Aggregate weekly metrics
        weekly_summary = self._aggregate_weekly_metrics(daily_reports)
        
        return {
            'week_start': week_start.isoformat(),
            'week_end': week_end.isoformat(),
            'daily_reports': daily_reports,
            'weekly_summary': weekly_summary,
            'recommendations': self._generate_weekly_recommendations(daily_reports)
        }
    
    def _aggregate_weekly_metrics(self, daily_reports: List[Dict]) -> Dict:
        """Aggregate metrics across the week"""
        total_trades = sum(r['trade_count'] for r in daily_reports if r.get('trade_count'))
        
        if total_trades == 0:
            return {'status': 'NO_TRADES'}
        
        # Aggregate performance
        all_returns = []
        for report in daily_reports:
            if 'performance_summary' in report:
                # Extract individual trade returns
                # This would need to be stored properly
                pass
        
        return {
            'total_trades': total_trades,
            'trading_days': len([r for r in daily_reports if r.get('trade_count', 0) > 0]),
            'avg_daily_trades': total_trades / 7
        }
    
    def _generate_weekly_recommendations(self, daily_reports: List[Dict]) -> List[Dict]:
        """Generate weekly recommendations based on daily analyses"""
        all_recommendations = []
        
        for report in daily_reports:
            if 'weight_recommendations' in report:
                all_recommendations.extend(report['weight_recommendations'])
        
        # Consolidate recommendations
        consolidated = {}
        for rec in all_recommendations:
            component = rec['component']
            if component not in consolidated:
                consolidated[component] = []
            consolidated[component].append(rec)
        
        # Generate final recommendations
        final_recommendations = []
        for component, recs in consolidated.items():
            avg_confidence = np.mean([r['confidence'] for r in recs])
            avg_recommended = np.mean([r['recommended_value'] for r in recs])
            
            final_recommendations.append({
                'component': component,
                'current_value': recs[0]['current_value'],
                'recommended_value': avg_recommended,
                'confidence': avg_confidence,
                'supporting_days': len(recs),
                'reasoning': f"Recommended across {len(recs)} days with {avg_confidence:.1%} confidence"
            })
        
        return final_recommendations
```

UNIT TESTS:

File: tests/test_post_trade_analytics.py
```python
import pytest
from unittest.mock import Mock, patch
from datetime import datetime, timedelta
from analytics.post_trade_analytics import PostTradeAnalytics, TradePerformance

class TestPostTradeAnalytics:
    def setup_method(self):
        self.config = {
            'database_url': 'sqlite:///:memory:',
            'lookback_days': 30,
            'min_trades_for_analysis': 5,
            'slippage_tolerance': 0.002,
            'return_target': 0.10,
            'max_drawdown_limit': 0.15
        }
        self.analytics = PostTradeAnalytics(self.config)
    
    def test_trade_performance_calculation(self):
        """Test trade performance metrics calculation"""
        trade = {
            'trade_id': 'TEST_001',
            'ticker': 'AAPL',
            'signal_date': datetime(2025, 1, 1),
            'execution_date': datetime(2025, 1, 2),
            'signal_strength': 0.8,
            'execution_confidence': 0.9,
            'entry_price': 150.0,
            'current_price': 165.0,  # 10% gain
            'max_price': 170.0,  # 13.3% max gain
            'min_price': 145.0,  # 3.3% max drawdown
            'slippage_estimated': 0.001,
            'slippage_realized': 0.0015,
            'market_volatility': 0.2,
            'sector_volatility': 0.25,
            'signal_type': 'insider_buy',
            'human_decision': 'APPROVE',
            'human_reason': 'Strong conviction'
        }
        
        performance = self.analytics._calculate_trade_performance(trade)
        
        assert performance.realized_return == 0.1  # 10%
        assert performance.max_return == pytest.approx(0.133, rel=1e-3)
        assert performance.max_drawdown == pytest.approx(0.033, rel=1e-3)
        assert performance.ticker == 'AAPL'
        assert performance.signal_strength == 0.8
    
    def test_model_accuracy_analysis(self):
        """Test model accuracy metrics"""
        trades = [
            TradePerformance(
                trade_id='T1', ticker='A', signal_date=datetime.now(),
                execution_date=datetime.now(), signal_strength=0.8,
                execution_confidence=0.9, entry_price=100, current_price=105,
                max_price=110, min_price=95, realized_return=0.05,
                max_return=0.1, max_drawdown=0.05, holding_days=5,
                slippage_estimated=0.001, slippage_realized=0.0015,
                market_volatility=0.2, sector_volatility=0.25,
                signal_type='insider', human_decision='APPROVE',
                human_reason='Strong'
            ),
            TradePerformance(
                trade_id='T2', ticker='B', signal_date=datetime.now(),
                execution_date=datetime.now(), signal_strength=0.6,
                execution_confidence=0.7, entry_price=100, current_price=98,
                max_price=102, min_price=95, realized_return=-0.02,
                max_return=0.02, max_drawdown=0.05, holding_days=3,
                slippage_estimated=0.001, slippage_realized=0.001,
                market_volatility=0.2, sector_volatility=0.25,
                signal_type='insider', human_decision='APPROVE',
                human_reason='Moderate'
            )
        ]
        
        accuracy = self.analytics._analyze_model_accuracy(trades)
        
        assert len(accuracy) == 3  # slippage, correlation, fill rate
        assert all(0 <= a.accuracy_score <= 1 for a in accuracy)
        assert any(a.metric_name == 'slippage_model' for a in accuracy)
    
    def test_weight_recommendations(self):
        """Test weight adjustment recommendations"""
        trades = [
            TradePerformance(
                trade_id='T1', ticker='A', signal_date=datetime.now(),
                execution_date=datetime.now(), signal_strength=0.8,
                execution_confidence=0.9, entry_price=100, current_price=115,
                max_price=120, min_price=95, realized_return=0.15,
                max_return=0.2, max_drawdown=0.05, holding_days=5,
                slippage_estimated=0.001, slippage_realized=0.003,  # High slippage
                market_volatility=0.2, sector_volatility=0.25,
                signal_type='insider', human_decision='APPROVE',
                human_reason='Strong'
            )
        ]
        
        model_accuracy = [
            Mock(metric_name='slippage_model', drift_detected=True, 
                 error_pct=0.5, accuracy_score=0.5)
        ]
        
        human_analysis = {
            'decision_efficiency': -0.05,
            'approval_rate': 0.8
        }
        
        recommendations = self.analytics._generate_weight_recommendations(
            trades, model_accuracy, human_analysis
        )
        
        assert len(recommendations) > 0
        assert any(r.component == 'max_slippage_pct' for r in recommendations)
        assert all(0 <= r.confidence <= 1 for r in recommendations)
    
    def test_weekly_report_generation(self):
        """Test weekly performance report"""
        with patch.object(self.analytics, 'run_daily_analysis') as mock_daily:
            # Mock daily reports
            mock_daily.return_value = {
                'analysis_date': '2025-01-01',
                'trade_count': 10,
                'performance_summary': {'win_rate': 0.6},
                'weight_recommendations': []
            }
            
            report = self.analytics.generate_weekly_report()
            
            assert 'week_start' in report
            assert 'week_end' in report
            assert 'daily_reports' in report
            assert len(report['daily_reports']) == 7
    
    @patch('analytics.post_trade_analytics.pd.read_sql')
    def test_insufficient_data_handling(self, mock_read_sql):
        """Test handling when insufficient trade data"""
        mock_read_sql.return_value.to_dict.return_value = []
        
        report = self.analytics.run_daily_analysis()
        
        assert report['status'] == 'INSUFFICIENT_DATA'
        assert 'trade_count' in report
        assert report['trade_count'] == 0
```

SCHEDULED JOB:

File: jobs/scheduled_analytics.py
```python
from analytics.post_trade_analytics import PostTradeAnalytics
import schedule
import time
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

def run_scheduled_analytics():
    """Run scheduled analytics jobs"""
    config = {
        'database_url': 'postgresql://user:pass@localhost/phasma_analytics',
        'lookback_days': 90,
        'min_trades_for_analysis': 20
    }
    
    analytics = PostTradeAnalytics(config)
    
    # Daily analysis at 6 AM UTC
    schedule.every().day.at("06:00").do(
        analytics.run_daily_analysis
    )
    
    # Weekly report on Monday at 8 AM UTC
    schedule.every().monday.at("08:00").do(
        analytics.generate_weekly_report
    )
    
    logger.info("Scheduled analytics jobs started")
    
    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == "__main__":
    run_scheduled_analytics()
```

DASHBOARD WIDGETS:

File: dashboards/analytics_widgets.py
```python
import plotly.graph_objects as go
import pandas as pd

def create_performance_chart(trade_data):
    """Create performance visualization"""
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=trade_data['execution_date'],
        y=trade_data['cumulative_return'],
        mode='lines',
        name='Cumulative Return'
    ))
    
    fig.add_trace(go.Scatter(
        x=trade_data['execution_date'],
        y=trade_data['benchmark_return'],
        mode='lines',
        name='Benchmark'
    ))
    
    fig.update_layout(
        title='Strategy Performance vs Benchmark',
        xaxis_title='Date',
        yaxis_title='Return'
    )
    
    return fig

def create_slippage_analysis(slippage_data):
    """Create slippage analysis chart"""
    fig = go.Figure()
    
    fig.add_trace(go.Histogram(
        x=slippage_data['slippage_error'],
        nbinsx=50,
        name='Slippage Error Distribution'
    ))
    
    fig.add_vline(
        x=slippage_data['tolerance'],
        line_dash="dash",
        line_color="red",
        annotation_text="Tolerance"
    )
    
    fig.update_layout(
        title='Slippage Model Error Distribution',
        xaxis_title='Slippage Error (%)',
        yaxis_title='Frequency'
    )
    
    return fig
```

DEFINITION OF DONE:
- [ ] All unit tests passing
- [ ] Integration tests with database
- [ ] Scheduled job deployed
- [ ] Dashboard widgets created
- [ ] Alert configuration complete
- [ ] Documentation updated
- [ ] Code review completed

============================================
END OF TICKET US-007
============================================
"""
