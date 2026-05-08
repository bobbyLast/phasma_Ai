"""
📊 SELF-CALIBRATING PROBABILITY ENGINE

Advanced meta-learning system that continuously improves prediction accuracy using proper scoring rules.
Calibrates probability estimates based on historical performance to become more accurate over time.

Scoring Rules Implemented:
- Brier Score (for binary outcomes)
- Log Loss (cross-entropy)
- Calibration curves
- Probability calibration techniques

Features:
- Prediction tracking and evaluation
- Automatic recalibration of probability estimates
- Confidence interval adjustment
- Performance analytics and reporting
- Continuous learning from resolved events
"""

import asyncio
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import json
import os
import math
import numpy as np
from collections import defaultdict
import statistics

try:
    from engines.kalshi_engine import KalshiPredictionEngine
    from engines.scenario_graph_engine import ScenarioGraphEngine
except ImportError:
    # Mocks for testing
    class KalshiPredictionEngine:
        def __init__(self, *args, **kwargs):
            pass
    class ScenarioGraphEngine:
        def __init__(self, *args, **kwargs):
            pass


@dataclass
class PredictionRecord:
    """Records a single probability prediction for later evaluation."""
    id: str
    event_id: str
    event_description: str
    predicted_probability: float
    predicted_confidence: float
    actual_outcome: Optional[bool] = None  # True/False for binary events
    actual_outcome_date: Optional[datetime] = None
    prediction_date: datetime = field(default_factory=datetime.now)
    source: str = "kalshi"  # 'kalshi', 'internal', 'options', 'correlation'
    market_data: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'event_id': self.event_id,
            'event_description': self.event_description,
            'predicted_probability': self.predicted_probability,
            'predicted_confidence': self.predicted_confidence,
            'actual_outcome': self.actual_outcome,
            'actual_outcome_date': self.actual_outcome_date.isoformat() if self.actual_outcome_date else None,
            'prediction_date': self.prediction_date.isoformat(),
            'source': self.source,
            'market_data': self.market_data
        }


@dataclass
class ScoringRuleResult:
    """Result of applying a scoring rule to predictions."""
    scoring_rule: str  # 'brier', 'log_loss', 'spherical'
    score: float
    sample_size: int
    confidence_interval: Tuple[float, float]
    calibration_data: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'scoring_rule': self.scoring_rule,
            'score': self.score,
            'sample_size': self.sample_size,
            'confidence_interval': self.confidence_interval,
            'calibration_data': self.calibration_data
        }


@dataclass
class CalibrationAdjustment:
    """Adjustment to apply to future probability estimates."""
    source: str
    adjustment_type: str  # 'additive', 'multiplicative', 'isotonic_regression'
    parameters: Dict[str, Any]
    effective_date: datetime = field(default_factory=datetime.now)
    performance_improvement: float = 0.0

    def apply_adjustment(self, probability: float) -> float:
        """Apply this calibration adjustment to a probability."""
        if self.adjustment_type == 'additive':
            bias = self.parameters.get('bias', 0.0)
            return max(0.01, min(0.99, probability + bias))
        elif self.adjustment_type == 'multiplicative':
            scale = self.parameters.get('scale', 1.0)
            # Apply scaling around 0.5
            centered = probability - 0.5
            scaled = centered * scale
            return max(0.01, min(0.99, scaled + 0.5))
        else:
            # Default: no adjustment
            return probability


class SelfCalibratingProbabilityEngine:
    """
    📊 Self-Calibrating Probability Engine

    Uses proper scoring rules to continuously improve prediction accuracy.
    Calibrates probability estimates based on historical performance.
    """

    def __init__(self, kalshi_engine: KalshiPredictionEngine, scenario_graph: ScenarioGraphEngine):
        self.kalshi = kalshi_engine
        self.scenario_graph = scenario_graph

        self.prediction_records: Dict[str, PredictionRecord] = {}
        self.calibration_adjustments: Dict[str, List[CalibrationAdjustment]] = defaultdict(list)
        self.scoring_history: List[ScoringRuleResult] = []

        self.predictions_file = "prediction_records.json"
        self.calibration_file = "calibration_adjustments.json"
        self.scoring_file = "scoring_history.json"

        self._load_data()

    def _load_data(self):
        """Load existing prediction records and calibration data."""
        # Load predictions
        if os.path.exists(self.predictions_file):
            try:
                with open(self.predictions_file, 'r') as f:
                    data = json.load(f)
                for pred_data in data.get('predictions', []):
                    pred = PredictionRecord(
                        id=pred_data['id'],
                        event_id=pred_data['event_id'],
                        event_description=pred_data['event_description'],
                        predicted_probability=pred_data['predicted_probability'],
                        predicted_confidence=pred_data['predicted_confidence'],
                        actual_outcome=pred_data.get('actual_outcome'),
                        actual_outcome_date=datetime.fromisoformat(pred_data['actual_outcome_date']) if pred_data.get('actual_outcome_date') else None,
                        prediction_date=datetime.fromisoformat(pred_data['prediction_date']),
                        source=pred_data.get('source', 'kalshi'),
                        market_data=pred_data.get('market_data', {})
                    )
                    self.prediction_records[pred.id] = pred
                print(f"📊 Loaded {len(self.prediction_records)} prediction records")
            except Exception as e:
                print(f"⚠️ Error loading predictions: {e}")

        # Load calibration adjustments
        if os.path.exists(self.calibration_file):
            try:
                with open(self.calibration_file, 'r') as f:
                    data = json.load(f)
                print(f"🎯 Loaded calibration adjustments for {len(data.get('adjustments', {}))} sources")
            except Exception as e:
                print(f"⚠️ Error loading calibration: {e}")

    def _save_data(self):
        """Save current state to disk."""
        # Save predictions
        predictions_data = {
            'predictions': [pred.to_dict() for pred in self.prediction_records.values()],
            'last_updated': datetime.now().isoformat()
        }
        with open(self.predictions_file, 'w') as f:
            json.dump(predictions_data, f, indent=2)

        # Save calibration adjustments
        calibration_data = {
            'adjustments': {
                source: [adj.__dict__ for adj in adjustments]
                for source, adjustments in self.calibration_adjustments.items()
            },
            'last_updated': datetime.now().isoformat()
        }
        with open(self.calibration_file, 'w') as f:
            json.dump(calibration_data, f, indent=2, default=str)

    def record_prediction(self, event_id: str, event_description: str,
                         predicted_probability: float, predicted_confidence: float,
                         source: str = "kalshi", market_data: Dict[str, Any] = None) -> str:
        """Record a new probability prediction for later evaluation."""

        prediction_id = f"pred_{int(datetime.now().timestamp())}_{event_id}"

        record = PredictionRecord(
            id=prediction_id,
            event_id=event_id,
            event_description=event_description,
            predicted_probability=predicted_probability,
            predicted_confidence=predicted_confidence,
            source=source,
            market_data=market_data or {}
        )

        self.prediction_records[prediction_id] = record
        self._save_data()

        return prediction_id

    def record_outcome(self, prediction_id: str, actual_outcome: bool,
                      outcome_date: datetime = None):
        """Record the actual outcome for a prediction."""

        if prediction_id not in self.prediction_records:
            print(f"⚠️ Prediction {prediction_id} not found")
            return

        record = self.prediction_records[prediction_id]
        record.actual_outcome = actual_outcome
        record.actual_outcome_date = outcome_date or datetime.now()

        self._save_data()
        print(f"✅ Recorded outcome for prediction {prediction_id}: {actual_outcome}")

    def calculate_brier_score(self, predictions: List[PredictionRecord]) -> ScoringRuleResult:
        """Calculate Brier score for a set of predictions."""

        resolved_predictions = [p for p in predictions if p.actual_outcome is not None]
        if not resolved_predictions:
            return ScoringRuleResult('brier', 0.0, 0, (0.0, 0.0))

        brier_scores = []
        for pred in resolved_predictions:
            # Brier score = (predicted_prob - actual_outcome)^2
            actual = 1.0 if pred.actual_outcome else 0.0
            brier_scores.append((pred.predicted_probability - actual) ** 2)

        mean_brier = statistics.mean(brier_scores)
        std_brier = statistics.stdev(brier_scores) if len(brier_scores) > 1 else 0

        # 95% confidence interval
        n = len(brier_scores)
        margin = 1.96 * (std_brier / math.sqrt(n)) if n > 1 else 0
        ci_lower = max(0, mean_brier - margin)
        ci_upper = min(1, mean_brier + margin)

        # Calibration analysis
        calibration_data = self._analyze_calibration_curve(resolved_predictions)

        result = ScoringRuleResult(
            scoring_rule='brier',
            score=mean_brier,
            sample_size=len(resolved_predictions),
            confidence_interval=(ci_lower, ci_upper),
            calibration_data=calibration_data
        )

        return result

    def calculate_log_loss(self, predictions: List[PredictionRecord]) -> ScoringRuleResult:
        """Calculate log loss (cross-entropy) for predictions."""

        resolved_predictions = [p for p in predictions if p.actual_outcome is not None]
        if not resolved_predictions:
            return ScoringRuleResult('log_loss', 0.0, 0, (0.0, 0.0))

        log_losses = []
        for pred in resolved_predictions:
            # Log loss = -[y * log(p) + (1-y) * log(1-p)]
            y = 1.0 if pred.actual_outcome else 0.0
            p = max(1e-15, min(1-1e-15, pred.predicted_probability))  # Avoid log(0)

            log_loss = -(y * math.log(p) + (1-y) * math.log(1-p))
            log_losses.append(log_loss)

        mean_log_loss = statistics.mean(log_losses)
        std_log_loss = statistics.stdev(log_losses) if len(log_losses) > 1 else 0

        # 95% confidence interval
        n = len(log_losses)
        margin = 1.96 * (std_log_loss / math.sqrt(n)) if n > 1 else 0
        ci_lower = max(0, mean_log_loss - margin)
        ci_upper = mean_log_loss + margin

        result = ScoringRuleResult(
            scoring_rule='log_loss',
            score=mean_log_loss,
            sample_size=len(resolved_predictions),
            confidence_interval=(ci_lower, ci_upper)
        )

        return result

    def _analyze_calibration_curve(self, predictions: List[PredictionRecord]) -> Dict[str, Any]:
        """Analyze calibration curve to detect systematic biases."""

        if len(predictions) < 10:
            return {'insufficient_data': True}

        # Group predictions into probability bins
        bins = np.linspace(0, 1, 11)  # 10 bins: 0-0.1, 0.1-0.2, etc.
        bin_counts = [0] * 10
        bin_correct = [0] * 10

        for pred in predictions:
            prob = pred.predicted_probability
            actual = 1.0 if pred.actual_outcome else 0.0

            # Find which bin this prediction belongs to
            bin_idx = min(9, int(prob * 10))

            bin_counts[bin_idx] += 1
            bin_correct[bin_idx] += actual

        # Calculate calibration metrics
        calibration_errors = []
        bin_centers = []

        for i in range(10):
            if bin_counts[i] > 0:
                predicted_prob = (i + 0.5) / 10.0
                actual_prob = bin_correct[i] / bin_counts[i]
                error = abs(predicted_prob - actual_prob)
                calibration_errors.append(error)
                bin_centers.append(predicted_prob)

        mean_calibration_error = statistics.mean(calibration_errors) if calibration_errors else 0

        return {
            'mean_calibration_error': mean_calibration_error,
            'bin_counts': bin_counts,
            'bin_correct': bin_correct,
            'calibration_errors': calibration_errors,
            'bin_centers': bin_centers
        }

    def evaluate_predictions_by_source(self, source: str) -> Dict[str, Any]:
        """Evaluate prediction performance for a specific source."""

        source_predictions = [p for p in self.prediction_records.values() if p.source == source]

        if not source_predictions:
            return {'error': f'No predictions found for source {source}'}

        brier_result = self.calculate_brier_score(source_predictions)
        log_loss_result = self.calculate_log_loss(source_predictions)

        # Store results
        self.scoring_history.extend([brier_result, log_loss_result])

        return {
            'source': source,
            'total_predictions': len(source_predictions),
            'resolved_predictions': len([p for p in source_predictions if p.actual_outcome is not None]),
            'brier_score': brier_result.to_dict(),
            'log_loss': log_loss_result.to_dict(),
            'evaluation_date': datetime.now().isoformat()
        }

    def generate_calibration_adjustment(self, source: str) -> Optional[CalibrationAdjustment]:
        """Generate a calibration adjustment based on historical performance."""

        evaluation = self.evaluate_predictions_by_source(source)
        if 'error' in evaluation:
            return None

        calibration_data = evaluation['brier_score']['calibration_data']
        if calibration_data.get('insufficient_data'):
            return None

        mean_calibration_error = calibration_data['mean_calibration_error']

        # If calibration error is significant (> 0.1), create adjustment
        if mean_calibration_error > 0.1:
            # Simple bias correction based on calibration curve
            # In practice, this would use isotonic regression or Platt scaling
            bias = 0.0
            calibration_errors = calibration_data['calibration_errors']
            bin_centers = calibration_data['bin_centers']

            if calibration_errors and bin_centers:
                # Simple linear correction
                weighted_errors = [err * (i + 1) for i, err in enumerate(calibration_errors)]
                bias = -statistics.mean(weighted_errors) * 0.5  # Conservative adjustment

            adjustment = CalibrationAdjustment(
                source=source,
                adjustment_type='additive',
                parameters={'bias': bias},
                performance_improvement=mean_calibration_error * 0.5  # Estimated improvement
            )

            self.calibration_adjustments[source].append(adjustment)
            self._save_data()

            return adjustment

        return None

    def calibrate_probability(self, probability: float, source: str) -> float:
        """Apply all relevant calibration adjustments to a probability estimate."""

        calibrated_prob = probability

        # Apply all adjustments for this source (most recent first)
        adjustments = sorted(self.calibration_adjustments[source],
                           key=lambda x: x.effective_date, reverse=True)

        for adjustment in adjustments[:3]:  # Use up to 3 most recent adjustments
            calibrated_prob = adjustment.apply_adjustment(calibrated_prob)

        return max(0.01, min(0.99, calibrated_prob))

    def get_performance_report(self) -> Dict[str, Any]:
        """Generate a comprehensive performance report."""

        sources = set(p.source for p in self.prediction_records.values())
        source_evaluations = {}

        for source in sources:
            source_evaluations[source] = self.evaluate_predictions_by_source(source)

        # Overall statistics
        all_predictions = list(self.prediction_records.values())
        resolved_predictions = [p for p in all_predictions if p.actual_outcome is not None]

        overall_brier = self.calculate_brier_score(resolved_predictions)
        overall_log_loss = self.calculate_log_loss(resolved_predictions)

        report = {
            'total_predictions': len(all_predictions),
            'resolved_predictions': len(resolved_predictions),
            'resolution_rate': len(resolved_predictions) / len(all_predictions) if all_predictions else 0,
            'overall_brier_score': overall_brier.to_dict(),
            'overall_log_loss': overall_log_loss.to_dict(),
            'source_performance': source_evaluations,
            'calibration_adjustments': {
                source: len(adjustments)
                for source, adjustments in self.calibration_adjustments.items()
            },
            'generated_at': datetime.now().isoformat()
        }

        return report

    def get_prediction_accuracy_trends(self, days: int = 30) -> Dict[str, Any]:
        """Analyze prediction accuracy trends over time."""

        cutoff_date = datetime.now() - timedelta(days=days)
        recent_predictions = [p for p in self.prediction_records.values()
                            if p.prediction_date >= cutoff_date and p.actual_outcome is not None]

        if not recent_predictions:
            return {'error': f'No resolved predictions in last {days} days'}

        # Group by prediction date (daily buckets)
        daily_performance = defaultdict(list)

        for pred in recent_predictions:
            date_key = pred.prediction_date.date()
            actual = 1.0 if pred.actual_outcome else 0.0
            brier = (pred.predicted_probability - actual) ** 2
            daily_performance[date_key].append(brier)

        # Calculate daily average Brier scores
        daily_averages = {}
        for date, scores in daily_performance.items():
            daily_averages[str(date)] = statistics.mean(scores)

        return {
            'period_days': days,
            'total_predictions': len(recent_predictions),
            'daily_average_brier': daily_averages,
            'overall_average_brier': statistics.mean([score for scores in daily_performance.values() for score in scores]),
            'improvement_trend': self._calculate_trend(daily_averages)
        }

    def _calculate_trend(self, daily_data: Dict[str, float]) -> str:
        """Calculate if performance is improving, worsening, or stable."""

        if len(daily_data) < 7:  # Need at least a week of data
            return 'insufficient_data'

        values = list(daily_data.values())
        if len(values) < 2:
            return 'insufficient_data'

        # Simple linear trend
        x = list(range(len(values)))
        slope = np.polyfit(x, values, 1)[0]

        if slope < -0.001:  # Improving (Brier score decreasing)
            return 'improving'
        elif slope > 0.001:  # Worsening (Brier score increasing)
            return 'worsening'
        else:
            return 'stable'


# Test/demo functions
async def test_self_calibrating_engine():
    """Test the self-calibrating probability engine."""
    print("📊 TESTING SELF-CALIBRATING PROBABILITY ENGINE")
    print("=" * 55)

    # Mock engines
    kalshi = KalshiPredictionEngine()
    scenario_graph = ScenarioGraphEngine(kalshi)

    engine = SelfCalibratingProbabilityEngine(kalshi, scenario_graph)

    print(f"🎯 Initialized with {len(engine.prediction_records)} existing predictions")

    # Simulate some prediction records with known outcomes
    test_predictions = [
        # Accurate predictions
        ("FED_CUT_Q1", "Fed cuts rates in Q1 2025", 0.75, True),  # Predicted 75%, actually happened
        ("BTC_200K_EOFY", "BTC hits 200K by end of 2025", 0.25, False),  # Predicted 25%, didn't happen

        # Biased predictions (overconfident)
        ("AI_BREAKTHROUGH_25", "Major AI breakthrough in 2025", 0.85, True),  # Predicted 85%, actually happened
        ("CPI_ABOVE_3", "CPI exceeds 3% in 2025", 0.90, False),  # Predicted 90%, didn't happen

        # Underconfident predictions
        ("ELECTION_DEM", "Democrat wins 2024 election", 0.45, True),  # Predicted 45%, actually happened
        ("OIL_150", "Oil hits 150/barrel in 2025", 0.30, False),  # Predicted 30%, didn't happen
    ]

    print("\n📝 RECORDING TEST PREDICTIONS:")
    for event_id, description, prob, outcome in test_predictions:
        pred_id = engine.record_prediction(event_id, description, prob, 0.8)
        engine.record_outcome(pred_id, outcome)
        print(f"✅ Recorded: {event_id} (predicted {prob:.1%}, actual {outcome})")

    # Evaluate performance
    print("\n📈 EVALUATING PREDICTION PERFORMANCE:")
    brier_result = engine.calculate_brier_score(list(engine.prediction_records.values()))
    log_loss_result = engine.calculate_log_loss(list(engine.prediction_records.values()))

    print(f"Brier Score: {brier_result.score:.4f} (95% CI: {brier_result.confidence_interval[0]:.4f} - {brier_result.confidence_interval[1]:.4f})")
    print(f"Log Loss: {log_loss_result.score:.4f} (95% CI: {log_loss_result.confidence_interval[0]:.4f} - {log_loss_result.confidence_interval[1]:.4f})")

    # Generate calibration adjustment
    print("\n🎯 GENERATING CALIBRATION ADJUSTMENT:")
    adjustment = engine.generate_calibration_adjustment('kalshi')
    if adjustment:
        print(f"✅ Generated {adjustment.adjustment_type} adjustment for 'kalshi'")
        print(f"   Parameters: {adjustment.parameters}")
        print(f"   Expected improvement: {adjustment.performance_improvement:.1%}")

        # Test calibration
        test_prob = 0.7
        calibrated_prob = engine.calibrate_probability(test_prob, 'kalshi')
        print(f"   Calibration test: {test_prob:.1%} → {calibrated_prob:.1%}")
    else:
        print("❌ No calibration adjustment needed (performance acceptable)")

    # Performance report
    print("\n📊 PERFORMANCE REPORT:")
    report = engine.get_performance_report()
    print(f"Total predictions: {report['total_predictions']}")
    print(f"Resolved predictions: {report['resolved_predictions']}")
    print(".1%")
    print(f"Overall Brier score: {report['overall_brier_score']['score']:.4f}")

    # Accuracy trends
    print("\n📈 ACCURACY TRENDS:")
    trends = engine.get_prediction_accuracy_trends(days=7)
    if 'error' not in trends:
        print(f"Average Brier score: {trends['overall_average_brier']:.4f}")
        print(f"Trend: {trends['improvement_trend']}")
    else:
        print(f"No trend data available: {trends['error']}")

    print("\n✅ Self-Calibrating Probability Engine test complete!")


if __name__ == "__main__":
    asyncio.run(test_self_calibrating_engine())
