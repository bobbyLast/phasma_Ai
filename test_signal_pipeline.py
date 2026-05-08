#!/usr/bin/env python3
"""
PHASMA AI - Complete Signal Pipeline Test
Demonstrates the full signal framework from AI to execution
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
from datetime import datetime
from trading.signal_framework import *
from trading.ai_integration import *

def test_complete_pipeline():
    """Test the complete signal pipeline"""
    print("🚀 PHASMA AI - COMPLETE SIGNAL PIPELINE")
    print("=" * 60)
    
    # Initialize components
    risk_params = RiskParameters(
        max_risk_per_trade=0.02,  # 2% per trade
        daily_loss_limit=0.05,    # 5% daily limit
        max_concurrent_exposure=0.25  # 25% max exposure
    )
    
    # Configure signal generator with custom weights
    signal_gen = SignalGenerator(
        confidence_weights={
            'probability_margin': 0.5,
            'ensemble_agreement': 0.3,
            'backtest_edge': 0.2
        },
        backtest_edge_scores={
            'BTCUSDT': 0.75,
            'ETHUSDT': 0.65,
            'AAPL': 0.70,
            'TSLA': 0.60
        }
    )
    
    # Configure multi-timeframe aggregator
    tf_aggregator = MultiTimeframeAggregator(
        timeframe_weights={
            '1m': 0.05, '5m': 0.1, '15m': 0.15,
            '1h': 0.3, '4h': 0.25, '1d': 0.15
        },
        alignment_requirement=True
    )
    
    # Initialize decision engine
    engine = TradingDecisionEngine(
        risk_params=risk_params,
        signal_generator=signal_gen,
        tf_aggregator=tf_aggregator
    )
    
    # Simulate diverse AI model outputs
    print("\n📊 SIMULATING AI MODEL OUTPUTS")
    print("-" * 40)
    
    model_outputs = []
    
    # BTC - Strong bullish across timeframes
    btc_timeframes = ['1d', '4h', '1h', '15m']
    for tf in btc_timeframes:
        output = AIModelOutput(
            symbol="BTCUSDT",
            timeframe=tf,
            predictions={
                'direction': 0.8 + np.random.normal(0, 0.1),
                'return': 0.02 + np.random.normal(0, 0.005),
                'volatility': 0.04,
                'confidence': 0.85
            },
            probabilities={
                'up': 0.85 + np.random.normal(0, 0.05),
                'down': 0.15 - np.random.normal(0, 0.05)
            },
            ensemble_votes={
                'trend_model': 1,
                'sentiment_model': 1,
                'technical_model': 1
            }
        )
        model_outputs.append(output)
    
    # ETH - Mixed signals
    eth_outputs = [
        AIModelOutput(
            symbol="ETHUSDT",
            timeframe="4h",
            predictions={'direction': 0.6, 'return': 0.01, 'volatility': 0.035},
            probabilities={'up': 0.6, 'down': 0.4},
            ensemble_votes={'trend_model': 1, 'sentiment_model': 0}
        ),
        AIModelOutput(
            symbol="ETHUSDT",
            timeframe="1h",
            predictions={'direction': -0.2, 'return': -0.003, 'volatility': 0.03},
            probabilities={'up': 0.4, 'down': 0.6},
            ensemble_votes={'trend_model': -1, 'sentiment_model': 0}
        )
    ]
    model_outputs.extend(eth_outputs)
    
    # AAPL - Strong signal
    model_outputs.append(
        AIModelOutput(
            symbol="AAPL",
            timeframe="1h",
            predictions={'direction': 0.75, 'return': 0.015, 'volatility': 0.025},
            probabilities={'up': 0.75, 'down': 0.25},
            ensemble_votes={'trend_model': 1, 'sentiment_model': 1, 'technical_model': 1}
        )
    )
    
    # TSLA - Weak signal
    model_outputs.append(
        AIModelOutput(
            symbol="TSLA",
            timeframe="15m",
            predictions={'direction': 0.3, 'return': 0.005, 'volatility': 0.05},
            probabilities={'up': 0.55, 'down': 0.45},
            ensemble_votes={'trend_model': 0, 'sentiment_model': 1}
        )
    )
    
    print(f"Generated {len(model_outputs)} model outputs")
    
    # Market conditions for each symbol
    market_conditions = {
        "BTCUSDT": {
            'volatility': 0.04,
            'volatility_regime': 'NORMAL',
            'liquidity_score': 0.95,
            'spread_pct': 0.03,
            'trend_aligned': True,
            'stop_distance_pct': 0.02
        },
        "ETHUSDT": {
            'volatility': 0.035,
            'volatility_regime': 'NORMAL',
            'liquidity_score': 0.9,
            'spread_pct': 0.04,
            'trend_aligned': False,
            'stop_distance_pct': 0.025
        },
        "AAPL": {
            'volatility': 0.025,
            'volatility_regime': 'LOW',
            'liquidity_score': 0.98,
            'spread_pct': 0.01,
            'trend_aligned': True,
            'stop_distance_pct': 0.015
        },
        "TSLA": {
            'volatility': 0.05,
            'volatility_regime': 'HIGH',
            'liquidity_score': 0.85,
            'spread_pct': 0.08,
            'trend_aligned': True,
            'stop_distance_pct': 0.03
        }
    }
    
    # Account state
    account_state = {
        'equity': 250000,  # $250k portfolio
        'current_exposure': 35000  # Already exposed $35k
    }
    
    print(f"\n💼 Account State:")
    print(f"   Equity: ${account_state['equity']:,.2f}")
    print(f"   Current Exposure: ${account_state['current_exposure']:,.2f}")
    print(f"   Available: ${account_state['equity'] - account_state['current_exposure']:,.2f}")
    
    # Process all model outputs
    print(f"\n🔄 PROCESSING SIGNALS...")
    print("-" * 40)
    
    decisions = engine.process_model_outputs(model_outputs, market_conditions, account_state)
    
    # Display results
    print(f"\n📈 TRADING DECISIONS")
    print("=" * 60)
    
    total_risk = 0
    trades_to_make = 0
    
    for symbol, decision in decisions.items():
        print(f"\n🎯 {symbol}")
        print("-" * 40)
        
        # Get original signals for this symbol
        symbol_signals = [s for s in engine.active_signals.values() if s.symbol == symbol]
        
        if symbol_signals:
            for sig in symbol_signals:
                print(f"   Signal ({sig.timeframe}): dir={sig.direction:+.2f}, conf={sig.confidence:.2f}")
        
        print(f"\nDecision: {decision.action}")
        print(f"Direction: {decision.direction:+.0f}")
        print(f"Confidence: {decision.confidence:.2f}")
        print(f"Tier: {SignalTier.get_tier_name(decision.tier)}")
        print(f"Band: {decision.band}")
        
        if decision.size_shares > 0:
            trades_to_make += 1
            total_risk += decision.risk_amount
            print(f"\nPosition Details:")
            print(f"   Size: {decision.size_shares:,} units")
            print(f"   Notional: ${decision.size_notional:,.2f}")
            print(f"   Risk: ${decision.risk_amount:,.2f} ({decision.risk_pct:.2%})")
            print(f"   Stop Distance: {market_conditions[symbol]['stop_distance_pct']:.1%}")
        else:
            print(f"\nNo position - {decision.reasoning[0] if decision.reasoning else 'No edge'}")
    
    # Summary
    print(f"\n📊 EXECUTION SUMMARY")
    print("=" * 60)
    print(f"Signals Processed: {len(model_outputs)}")
    print(f"Symbols Analyzed: {len(decisions)}")
    print(f"Trades to Execute: {trades_to_make}")
    print(f"Total Risk at Stake: ${total_risk:,.2f}")
    print(f"Risk as % of Equity: {total_risk/account_state['equity']:.2%}")
    print(f"Remaining Capacity: ${(account_state['equity'] * risk_params.max_concurrent_exposure) - (account_state['current_exposure'] + sum(d.size_notional for d in decisions.values())):,.2f}")
    
    # Show tier distribution
    tier_counts = {}
    for decision in decisions.values():
        tier = decision.tier
        tier_counts[tier] = tier_counts.get(tier, 0) + 1
    
    print(f"\n📈 Signal Tier Distribution:")
    for tier in sorted(tier_counts.keys()):
        print(f"   Tier {tier} ({SignalTier.get_tier_name(tier)}): {tier_counts[tier]} signals")
    
    # Performance expectations
    print(f"\n💡 PERFORMANCE EXPECTATIONS")
    print("-" * 40)
    
    high_conviction = [d for d in decisions.values() if d.tier >= SignalTier.STRONG]
    if high_conviction:
        avg_confidence = np.mean([d.confidence for d in high_conviction])
        print(f"High Conviction Signals: {len(high_conviction)}")
        print(f"Average Confidence: {avg_confidence:.2%}")
        print(f"Expected Win Rate: {avg_confidence * 0.6:.1%}")  # Rough estimate
    
    print(f"\n✅ Pipeline Complete!")
    print(f"System is ready for live execution with proper risk management")

if __name__ == "__main__":
    test_complete_pipeline()
