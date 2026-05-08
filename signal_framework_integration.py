#!/usr/bin/env python3
"""
PHASMA AI - Signal Framework Integration Module
Integrates the Signal Framework into PhasmaTradingSystem

Usage:
    from signal_framework_integration import SignalFrameworkIntegration
    
    # In PhasmaTradingSystem.__init__:
    self.signal_framework = SignalFrameworkIntegration(self.config)
    
    # In run_full_cycle:
    decisions = self.signal_framework.process_convergence_signals(signals, market_conditions, account_state)
"""

from typing import Dict, List, Any, Optional
from datetime import datetime

# Import Signal Framework
from trading.signal_framework import (
    TradingSignal, SignalProcessor, SignalTier, DecisionBand,
    RiskParameters, TradeDecision
)
from trading.ai_integration import (
    AIModelOutput, SignalGenerator, MultiTimeframeAggregator,
    TradingDecisionEngine
)

class SignalFrameworkIntegration:
    """Integration layer between Phasma AI and Signal Framework"""
    
    def __init__(self, config):
        """Initialize Signal Framework with Phasma config"""
        self.config = config
        
        # Initialize Risk Parameters from config
        self.risk_params = RiskParameters(
            max_risk_per_trade=config.get('risk.max_per_trade', 0.02),
            daily_loss_limit=config.get('risk.daily_loss_limit', 0.05),
            max_concurrent_exposure=config.get('risk.max_exposure', 0.30)
        )
        
        # Initialize Signal Generator
        self.signal_generator = SignalGenerator(
            confidence_weights={
                'probability_margin': 0.4,
                'ensemble_agreement': 0.35,
                'backtest_edge': 0.25
            }
        )
        
        # Initialize Multi-Timeframe Aggregator
        self.tf_aggregator = MultiTimeframeAggregator(
            timeframe_weights={
                '1m': 0.05, '5m': 0.1, '15m': 0.15,
                '1h': 0.3, '4h': 0.25, '1d': 0.15
            }
        )
        
        # Initialize Trading Decision Engine
        self.decision_engine = TradingDecisionEngine(
            self.risk_params,
            self.signal_generator,
            self.tf_aggregator
        )
        
        print("✅ Signal Framework Integration Ready")
        print(f"   Risk per Trade: {self.risk_params.max_risk_per_trade:.1%}")
        print(f"   Daily Loss Limit: {self.risk_params.daily_loss_limit:.1%}")
        print(f"   Max Exposure: {self.risk_params.max_concurrent_exposure:.1%}")
    
    def convert_convergence_to_signal(self, conv_signal: Dict) -> TradingSignal:
        """Convert Phasma convergence signal to Signal Framework format"""
        
        # Extract values from Phasma signal format
        symbol = conv_signal.get('ticker', conv_signal.get('symbol', 'UNKNOWN'))
        confidence = conv_signal.get('confidence', 0.5)
        action = conv_signal.get('action', 'HOLD')
        
        # Determine direction
        if 'BUY' in action.upper() or 'CALL' in action.upper():
            direction = 1
        elif 'SELL' in action.upper() or 'PUT' in action.upper():
            direction = -1
        else:
            direction = 0
        
        # Get expected return if available
        expected_return = conv_signal.get('expected_return')
        if not expected_return and 'potential_upside' in conv_signal:
            expected_return = conv_signal['potential_upside'] / 100
        
        # Get volatility if available
        volatility = conv_signal.get('volatility', 0.02)
        
        return TradingSignal(
            symbol=symbol,
            timeframe=conv_signal.get('timeframe', '1h'),
            direction=direction,
            confidence=confidence,
            expected_return=expected_return,
            volatility=volatility,
            predicted_win_rate=conv_signal.get('win_rate'),
            source=conv_signal.get('source', 'convergence_engine'),
            timestamp=datetime.now().isoformat()
        )
    
    def build_market_conditions(self, symbol: str, market_data: Dict) -> Dict:
        """Build market conditions for signal processing"""
        return {
            'volatility': market_data.get('volatility', 0.02),
            'volatility_regime': market_data.get('volatility_regime', 'NORMAL'),
            'liquidity_score': market_data.get('liquidity', 0.8),
            'spread_pct': market_data.get('spread_pct', 0.02),
            'trend_aligned': market_data.get('trend_aligned', True),
            'stop_distance_pct': market_data.get('stop_distance', 0.02)
        }
    
    def process_convergence_signals(self, 
                                     convergence_signals: List[Dict],
                                     market_conditions: Dict[str, Dict],
                                     account_state: Dict) -> List[TradeDecision]:
        """
        Process Phasma convergence signals through Signal Framework
        
        Args:
            convergence_signals: List of signals from SignalConvergenceEngine
            market_conditions: Dict of symbol -> market conditions
            account_state: Dict with 'equity' and 'current_exposure'
        
        Returns:
            List of TradeDecision objects with actionable trades
        """
        
        # Convert Phasma signals to Signal Framework format
        model_outputs = []
        for conv_signal in convergence_signals:
            trading_signal = self.convert_convergence_to_signal(conv_signal)
            
            # Convert TradingSignal to AIModelOutput
            model_output = AIModelOutput(
                symbol=trading_signal.symbol,
                timeframe=trading_signal.timeframe,
                predictions={
                    'direction': trading_signal.direction * trading_signal.confidence,
                    'return': trading_signal.expected_return or 0,
                    'volatility': trading_signal.volatility or 0.02,
                    'win_rate': trading_signal.predicted_win_rate or trading_signal.confidence
                },
                probabilities={
                    'up': (1 + trading_signal.direction) / 2,
                    'down': (1 - trading_signal.direction) / 2
                },
                ensemble_votes={
                    'convergence': trading_signal.direction,
                    'confidence': 1 if trading_signal.confidence > 0.7 else 0
                }
            )
            model_outputs.append(model_output)
        
        # Process through decision engine
        decisions_dict = self.decision_engine.process_model_outputs(
            model_outputs,
            market_conditions,
            account_state
        )
        
        # Filter for actionable trades only
        actionable_decisions = [
            decision for decision in decisions_dict.values()
            if decision.action not in ['NO_TRADE', 'WATCH', 'ERROR']
        ]
        
        return actionable_decisions
    
    def format_trade_for_execution(self, decision: TradeDecision, current_price: float) -> Dict:
        """Format TradeDecision for Phasma execution system"""
        
        shares = int(decision.size_notional / current_price) if current_price > 0 else 0
        
        return {
            'symbol': decision.symbol,
            'action': 'BUY' if decision.direction > 0 else 'SELL',
            'confidence': decision.confidence,
            'position_size': decision.size_notional,
            'shares': shares,
            'entry_price': current_price,
            'risk_amount': decision.risk_amount,
            'risk_pct': decision.risk_pct,
            'tier': decision.tier,
            'band': decision.band,
            'signal_framework_processed': True,
            'timestamp': decision.timestamp
        }
    
    def get_signal_stats(self) -> Dict:
        """Get statistics from signal framework processing"""
        return {
            'risk_params': {
                'max_risk_per_trade': self.risk_params.max_risk_per_trade,
                'daily_loss_limit': self.risk_params.daily_loss_limit,
                'max_exposure': self.risk_params.max_concurrent_exposure
            },
            'active_signals': len(self.decision_engine.active_signals),
            'last_decisions': len(self.decision_engine.last_decisions)
        }

# Quick test function
def test_integration():
    """Test the integration"""
    print("🧪 Testing Signal Framework Integration")
    print("=" * 60)
    
    # Mock config
    class MockConfig:
        def get(self, key, default=None):
            return default
    
    config = MockConfig()
    
    # Initialize
    integration = SignalFrameworkIntegration(config)
    
    # Test signals
    test_signals = [
        {
            'ticker': 'AAPL',
            'confidence': 0.85,
            'action': 'BUY_CALL',
            'expected_return': 0.05,
            'source': 'convergence'
        },
        {
            'ticker': 'TSLA',
            'confidence': 0.72,
            'action': 'BUY_PUT',
            'expected_return': -0.03,
            'source': 'convergence'
        }
    ]
    
    market_conditions = {
        'AAPL': {
            'volatility': 0.025,
            'volatility_regime': 'NORMAL',
            'liquidity': 0.9,
            'trend_aligned': True,
            'stop_distance': 0.02
        },
        'TSLA': {
            'volatility': 0.04,
            'volatility_regime': 'HIGH',
            'liquidity': 0.8,
            'trend_aligned': False,
            'stop_distance': 0.03
        }
    }
    
    account_state = {
        'equity': 250000,
        'current_exposure': 35000
    }
    
    # Process signals
    decisions = integration.process_convergence_signals(
        test_signals,
        market_conditions,
        account_state
    )
    
    print(f"\n✅ Processed {len(test_signals)} signals")
    print(f"🎯 Found {len(decisions)} actionable trades")
    
    for decision in decisions:
        print(f"\n  {decision.symbol}:")
        print(f"    Action: {decision.action}")
        print(f"    Confidence: {decision.confidence:.1%}")
        print(f"    Size: ${decision.size_notional:,.2f}")

if __name__ == "__main__":
    test_integration()
