#!/usr/bin/env python3
"""
PHASMA AI - AI Model Integration Layer
Connects AI models to the signal framework for production trading
"""

import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
import logging

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from trading.signal_framework import (
    TradingSignal, SignalProcessor, SignalTier, DecisionBand,
    RiskParameters, TradeDecision
)

logger = logging.getLogger(__name__)

class AIModelOutput:
    """Standardized AI model output"""
    
    def __init__(self, 
                 symbol: str,
                 timeframe: str,
                 predictions: Dict[str, float],
                 probabilities: Optional[Dict[str, float]] = None,
                 ensemble_votes: Optional[Dict[str, int]] = None,
                 metadata: Optional[Dict] = None):
        self.symbol = symbol
        self.timeframe = timeframe
        self.predictions = predictions  # e.g., {'direction': 0.7, 'return': 0.02}
        self.probabilities = probabilities  # e.g., {'up': 0.7, 'down': 0.3}
        self.ensemble_votes = ensemble_votes  # e.g., {'model1': 1, 'model2': 1}
        self.metadata = metadata or {}
        self.timestamp = datetime.now()

class SignalGenerator:
    """Converts AI model outputs to normalized trading signals"""
    
    def __init__(self, 
                 confidence_weights: Optional[Dict[str, float]] = None,
                 backtest_edge_scores: Optional[Dict[str, float]] = None):
        """
        Args:
            confidence_weights: Weights for different confidence components
            backtest_edge_scores: Historical edge scores for calibration
        """
        self.confidence_weights = confidence_weights or {
            'probability_margin': 0.4,
            'ensemble_agreement': 0.3,
            'backtest_edge': 0.3
        }
        self.backtest_edge_scores = backtest_edge_scores or {}
    
    def generate_signal(self, model_output: AIModelOutput) -> TradingSignal:
        """Convert AI model output to normalized trading signal"""
        
        # Extract direction
        direction = self._extract_direction(model_output)
        
        # Calculate confidence score
        confidence = self._calculate_confidence(model_output)
        
        # Extract other metrics
        expected_return = model_output.predictions.get('return')
        volatility = model_output.predictions.get('volatility')
        win_rate = model_output.predictions.get('win_rate')
        max_drawdown = model_output.predictions.get('max_drawdown')
        
        return TradingSignal(
            symbol=model_output.symbol,
            timeframe=model_output.timeframe,
            direction=direction,
            confidence=confidence,
            expected_return=expected_return,
            volatility=volatility,
            predicted_win_rate=win_rate,
            predicted_max_drawdown=max_drawdown,
            source="AI_MODEL",
            timestamp=model_output.timestamp.isoformat()
        )
    
    def _extract_direction(self, model_output: AIModelOutput) -> float:
        """Extract direction from model output"""
        # Method 1: Direct prediction
        if 'direction' in model_output.predictions:
            return np.clip(model_output.predictions['direction'], -1, 1)
        
        # Method 2: Probability difference
        if model_output.probabilities:
            up_prob = model_output.probabilities.get('up', 0.5)
            down_prob = model_output.probabilities.get('down', 0.5)
            return up_prob - down_prob
        
        # Method 3: Ensemble majority vote
        if model_output.ensemble_votes:
            votes = list(model_output.ensemble_votes.values())
            if votes:
                avg_vote = np.mean(votes)
                return np.clip(avg_vote, -1, 1)
        
        # Default: no edge
        return 0.0
    
    def _calculate_confidence(self, model_output: AIModelOutput) -> float:
        """Calculate confidence score from multiple components"""
        
        components = {}
        
        # 1. Probability margin
        if model_output.probabilities:
            probs = list(model_output.probabilities.values())
            if len(probs) >= 2:
                # Use max probability as confidence
                components['probability_margin'] = max(probs)
        
        # 2. Ensemble agreement
        if model_output.ensemble_votes:
            votes = list(model_output.ensemble_votes.values())
            if len(votes) > 1:
                # Calculate agreement as inverse of standard deviation
                std_votes = np.std(votes)
                agreement = 1.0 - (std_votes / 2.0)  # Normalize to 0-1
                components['ensemble_agreement'] = max(0, agreement)
        
        # 3. Backtest edge score
        symbol = model_output.symbol
        if symbol in self.backtest_edge_scores:
            components['backtest_edge'] = self.backtest_edge_scores[symbol]
        
        # 4. Model prediction confidence (if available)
        if 'confidence' in model_output.predictions:
            components['model_confidence'] = model_output.predictions['confidence']
        
        # Weighted combination
        confidence = 0.0
        total_weight = 0.0
        
        for component, value in components.items():
            weight = self.confidence_weights.get(component, 0)
            confidence += weight * value
            total_weight += weight
        
        if total_weight > 0:
            confidence /= total_weight
        
        # Ensure valid range
        return np.clip(confidence, 0.0, 1.0)

class MultiTimeframeAggregator:
    """Aggregates signals across multiple timeframes"""
    
    def __init__(self, 
                 timeframe_weights: Optional[Dict[str, float]] = None,
                 alignment_requirement: bool = True):
        """
        Args:
            timeframe_weights: Weights for different timeframes
            alignment_requirement: Whether higher TF must align with lower TF
        """
        self.timeframe_weights = timeframe_weights or {
            '1m': 0.1, '5m': 0.15, '15m': 0.2,
            '1h': 0.25, '4h': 0.2, '1d': 0.1
        }
        self.alignment_requirement = alignment_requirement
    
    def aggregate_signals(self, signals: List[TradingSignal]) -> TradingSignal:
        """Aggregate multiple timeframe signals into one"""
        
        if not signals:
            raise ValueError("No signals to aggregate")
        
        if len(signals) == 1:
            return signals[0]
        
        # Sort by timeframe (higher to lower)
        tf_order = ['1d', '4h', '1h', '15m', '5m', '1m']
        signals.sort(key=lambda s: tf_order.index(s.timeframe) if s.timeframe in tf_order else 99)
        
        # Check alignment if required
        if self.alignment_requirement:
            higher_tf_direction = signals[0].direction  # Highest TF
            for signal in signals[1:]:
                if signal.direction != 0 and signal.direction != higher_tf_direction:
                    # Misalignment - reduce confidence or return neutral
                    return self._create_misaligned_signal(signals)
        
        # Weighted aggregation
        weighted_direction = 0.0
        weighted_confidence = 0.0
        total_weight = 0.0
        
        for signal in signals:
            weight = self.timeframe_weights.get(signal.timeframe, 0.1)
            weighted_direction += weight * signal.direction
            weighted_confidence += weight * signal.confidence
            total_weight += weight
        
        # Normalize
        if total_weight > 0:
            weighted_direction /= total_weight
            weighted_confidence /= total_weight
        
        # Create aggregated signal
        return TradingSignal(
            symbol=signals[0].symbol,
            timeframe="AGGREGATED",
            direction=weighted_direction,
            confidence=weighted_confidence,
            expected_return=np.mean([s.expected_return for s in signals if s.expected_return]),
            volatility=np.mean([s.volatility for s in signals if s.volatility]),
            source="MULTI_TF_AGG",
            timestamp=datetime.now().isoformat(),
            metadata={
                'num_timeframes': len(signals),
                'timeframes': [s.timeframe for s in signals],
                'aligned': all(s.direction == signals[0].direction or s.direction == 0 for s in signals)
            }
        )
    
    def _create_misaligned_signal(self, signals: List[TradingSignal]) -> TradingSignal:
        """Create signal for misaligned timeframes"""
        # Use middle timeframe as primary with reduced confidence
        middle_idx = len(signals) // 2
        primary = signals[middle_idx]
        
        # Reduce confidence due to misalignment
        reduced_confidence = primary.confidence * 0.6
        
        return TradingSignal(
            symbol=primary.symbol,
            timeframe="MISALIGNED",
            direction=primary.direction * 0.5,  # Weaken direction
            confidence=reduced_confidence,
            expected_return=primary.expected_return,
            volatility=primary.volatility,
            source="MISALIGNED_TF",
            timestamp=datetime.now().isoformat(),
            metadata={
                'misaligned': True,
                'timeframes': [s.timeframe for s in signals]
            }
        )

class TradingDecisionEngine:
    """Main engine that connects AI models to trading decisions"""
    
    def __init__(self,
                 risk_params: Optional[RiskParameters] = None,
                 signal_generator: Optional[SignalGenerator] = None,
                 tf_aggregator: Optional[MultiTimeframeAggregator] = None):
        self.signal_processor = SignalProcessor(risk_params)
        self.signal_generator = signal_generator or SignalGenerator()
        self.tf_aggregator = tf_aggregator or MultiTimeframeAggregator()
        
        # Track state
        self.active_signals = {}  # symbol -> TradingSignal
        self.last_decisions = {}  # symbol -> TradeDecision
    
    def process_model_outputs(self,
                             model_outputs: List[AIModelOutput],
                             market_conditions: Dict[str, Dict],
                             account_state: Dict) -> Dict[str, TradeDecision]:
        """
        Process multiple model outputs and return trading decisions
        
        Args:
            model_outputs: List of AI model outputs
            market_conditions: Market conditions per symbol
            account_state: Account state dict
        
        Returns:
            Dict of symbol -> TradeDecision
        """
        decisions = {}
        
        # Group outputs by symbol
        outputs_by_symbol = {}
        for output in model_outputs:
            if output.symbol not in outputs_by_symbol:
                outputs_by_symbol[output.symbol] = []
            outputs_by_symbol[output.symbol].append(output)
        
        # Process each symbol
        for symbol, outputs in outputs_by_symbol.items():
            try:
                # Generate signals from model outputs
                signals = []
                for output in outputs:
                    signal = self.signal_generator.generate_signal(output)
                    signals.append(signal)
                
                # Aggregate if multiple timeframes
                if len(signals) > 1:
                    aggregated_signal = self.tf_aggregator.aggregate_signals(signals)
                else:
                    aggregated_signal = signals[0]
                
                # Store active signal
                self.active_signals[symbol] = aggregated_signal
                
                # Get market conditions for this symbol
                conditions = market_conditions.get(symbol, {})
                
                # Make trading decision
                decision = self.signal_processor.process_signal(
                    aggregated_signal,
                    conditions,
                    account_state
                )
                
                decisions[symbol] = decision
                self.last_decisions[symbol] = decision
                
                # Log decision
                logger.info(f"Decision for {symbol}: {decision.action} "
                           f"(tier {decision.tier}, confidence {decision.confidence:.2f})")
                
            except Exception as e:
                logger.error(f"Error processing {symbol}: {e}")
                decisions[symbol] = TradeDecision(
                    action="ERROR",
                    direction=0,
                    symbol=symbol,
                    size_notional=0,
                    size_shares=0,
                    tier=0,
                    band="NO_TRADE",
                    confidence=0,
                    risk_amount=0,
                    risk_pct=0,
                    reasoning=[f"Processing error: {str(e)}"],
                    timestamp=datetime.now().isoformat()
                )
        
        return decisions
    
    def get_active_signals(self) -> Dict[str, TradingSignal]:
        """Get all active signals"""
        return self.active_signals.copy()
    
    def get_last_decisions(self) -> Dict[str, TradeDecision]:
        """Get last trading decisions"""
        return self.last_decisions.copy()
    
    def update_performance(self, symbol: str, pnl: float):
        """Update performance metrics for adaptive learning"""
        self.signal_processor.update_daily_pnl(pnl)
        
        # Could update backtest edge scores here
        # based on realized performance

# Example usage
def main():
    """Example of AI model integration"""
    print("🤖 PHASMA AI - Model Integration Demo")
    print("=" * 60)
    
    # Initialize engine
    risk_params = RiskParameters(max_risk_per_trade=0.01)
    engine = TradingDecisionEngine(risk_params)
    
    # Simulate AI model outputs
    model_outputs = [
        # BTC signals from multiple timeframes
        AIModelOutput(
            symbol="BTCUSDT",
            timeframe="1h",
            predictions={'direction': 0.8, 'return': 0.02, 'volatility': 0.04},
            probabilities={'up': 0.8, 'down': 0.2},
            ensemble_votes={'model1': 1, 'model2': 1, 'model3': 1}
        ),
        AIModelOutput(
            symbol="BTCUSDT",
            timeframe="15m",
            predictions={'direction': 0.6, 'return': 0.015, 'volatility': 0.035},
            probabilities={'up': 0.6, 'down': 0.4},
            ensemble_votes={'model1': 1, 'model2': 0, 'model3': 1}
        ),
        # ETH signal
        AIModelOutput(
            symbol="ETHUSDT",
            timeframe="1h",
            predictions={'direction': -0.3, 'return': -0.005, 'volatility': 0.03},
            probabilities={'up': 0.35, 'down': 0.65},
            ensemble_votes={'model1': -1, 'model2': 0, 'model3': -1}
        )
    ]
    
    # Market conditions
    market_conditions = {
        "BTCUSDT": {
            'volatility': 0.04,
            'volatility_regime': 'NORMAL',
            'liquidity_score': 0.9,
            'spread_pct': 0.05,
            'trend_aligned': True,
            'stop_distance_pct': 0.025
        },
        "ETHUSDT": {
            'volatility': 0.03,
            'volatility_regime': 'NORMAL',
            'liquidity_score': 0.85,
            'spread_pct': 0.03,
            'trend_aligned': False,
            'stop_distance_pct': 0.02
        }
    }
    
    # Account state
    account_state = {
        'equity': 100000,
        'current_exposure': 10000
    }
    
    # Process and get decisions
    decisions = engine.process_model_outputs(model_outputs, market_conditions, account_state)
    
    # Display results
    for symbol, decision in decisions.items():
        print(f"\n📊 {symbol} Decision")
        print("-" * 40)
        print(f"Action: {decision.action}")
        print(f"Direction: {decision.direction:+.0f}")
        print(f"Confidence: {decision.confidence:.2f}")
        print(f"Tier: {SignalTier.get_tier_name(decision.tier)}")
        
        if decision.size_shares > 0:
            print(f"Position Size: ${decision.size_notional:,.2f}")
            print(f"Risk: {decision.risk_pct:.2%}")
        
        print("\nReasoning:")
        for reason in decision.reasoning:
            print(f"  • {reason}")

if __name__ == "__main__":
    main()
