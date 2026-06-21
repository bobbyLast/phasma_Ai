#!/usr/bin/env python3
"""
LEGACY ONLY — DO NOT USE FOR EXECUTION. ExecutionRouter is the only active execution path.

PHASMA AI - Live Trading Run with Realistic Data
Uses simulated realistic data to demonstrate full system workflow.
Standalone legacy demo — not imported by main.py or WorkerSupervisor.
"""

import asyncio
import random
from datetime import datetime, timedelta
from trading.signal_framework import *
from trading.ai_integration import *

class RealisticMarketData:
    """Generate realistic market data for testing"""
    
    def __init__(self):
        # Real stock prices as of testing
        self.base_prices = {
            'AAPL': 185.50, 'MSFT': 415.20, 'GOOGL': 175.80, 'AMZN': 175.40,
            'NVDA': 875.30, 'TSLA': 195.60, 'META': 505.20, 'NFLX': 635.80,
            'AMD': 185.40, 'INTC': 43.20, 'CRM': 315.50, 'ORCL': 142.30,
            'BTC-USD': 67500.00, 'ETH-USD': 3550.00
        }
        
        # Recent performance trends (realistic)
        self.trends = {
            'AAPL': 0.02, 'MSFT': 0.015, 'GOOGL': -0.01, 'AMZN': 0.008,
            'NVDA': 0.035, 'TSLA': -0.015, 'META': 0.025, 'NFLX': 0.018,
            'AMD': 0.022, 'INTC': -0.008, 'CRM': 0.012, 'ORCL': 0.005,
            'BTC-USD': 0.045, 'ETH-USD': 0.038
        }
    
    def get_live_price(self, symbol):
        """Get simulated live price with realistic movement"""
        if symbol not in self.base_prices:
            return None
        
        base = self.base_prices[symbol]
        trend = self.trends.get(symbol, 0)
        
        # Add realistic intraday noise
        noise = random.gauss(0, 0.008)  # 0.8% standard deviation
        change_pct = trend + noise
        
        price = base * (1 + change_pct)
        
        return {
            'symbol': symbol,
            'price': round(price, 2),
            'change': round(price - base, 2),
            'change_pct': round(change_pct * 100, 2),
            'volume': random.randint(1000000, 50000000),
            'source': 'live_simulation',
            'timestamp': datetime.now().isoformat()
        }

async def run_live_trading_cycle():
    """Run a complete live trading cycle"""
    print("🚀 PHASMA AI - LIVE TRADING CYCLE")
    print("=" * 70)
    print(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("Mode: SIMULATED LIVE DATA (Add API keys for real data)")
    
    # Initialize data source
    market_data = RealisticMarketData()
    
    # Initialize signal framework
    risk_params = RiskParameters(
        max_risk_per_trade=0.02,
        daily_loss_limit=0.05,
        max_concurrent_exposure=0.30
    )
    
    signal_gen = SignalGenerator(
        confidence_weights={
            'probability_margin': 0.4,
            'ensemble_agreement': 0.35,
            'backtest_edge': 0.25
        }
    )
    
    engine = TradingDecisionEngine(risk_params, signal_gen)
    
    # Phase 1: Market Scan
    print("\n📊 PHASE 1: MARKET SCAN")
    print("-" * 40)
    
    symbols = list(market_data.base_prices.keys())
    print(f"Scanning {len(symbols)} assets...")
    
    live_data = []
    for symbol in symbols:
        data = market_data.get_live_price(symbol)
        if data:
            live_data.append(data)
            emoji = "📈" if data['change'] > 0 else "📉"
            print(f"  {emoji} {symbol:8s} ${data['price']:>10.2f} ({data['change']:+.2f}, {data['change_pct']:+.2f}%)")
        await asyncio.sleep(0.05)  # Simulate API delay
    
    print(f"✅ Retrieved {len(live_data)} live prices")
    
    # Phase 2: Signal Generation
    print("\n🤖 PHASE 2: AI SIGNAL GENERATION")
    print("-" * 40)
    
    model_outputs = []
    
    for data in live_data:
        # Generate AI model outputs based on price movement
        change_pct = data['change_pct'] / 100
        
        # Strong signals for large moves
        if abs(change_pct) > 0.02:
            direction = 1 if change_pct > 0 else -1
            confidence = min(0.95, 0.6 + abs(change_pct) * 5)
            
            output = AIModelOutput(
                symbol=data['symbol'],
                timeframe='1h',
                predictions={
                    'direction': direction * confidence,
                    'return': change_pct * 2,
                    'volatility': abs(change_pct) * 2,
                    'win_rate': confidence
                },
                probabilities={
                    'up': (1 + direction * confidence) / 2,
                    'down': (1 - direction * confidence) / 2
                },
                ensemble_votes={
                    'trend_model': direction,
                    'momentum_model': direction if abs(change_pct) > 0.03 else 0,
                    'volume_model': 1 if data['volume'] > 20000000 else 0
                }
            )
            
            model_outputs.append(output)
    
    print(f"✅ Generated {len(model_outputs)} AI signals")
    
    # Phase 3: Market Conditions
    print("\n📈 PHASE 3: MARKET CONDITIONS")
    print("-" * 40)
    
    market_conditions = {}
    for data in live_data:
        volatility_regime = 'HIGH' if abs(data['change_pct']) > 3 else 'NORMAL' if abs(data['change_pct']) > 1 else 'LOW'
        
        market_conditions[data['symbol']] = {
            'volatility': abs(data['change_pct']) / 100,
            'volatility_regime': volatility_regime,
            'liquidity_score': 0.9 if data['volume'] > 10000000 else 0.7,
            'spread_pct': random.uniform(0.01, 0.1),
            'trend_aligned': data['change_pct'] > 0,
            'stop_distance_pct': 0.02 if volatility_regime == 'NORMAL' else 0.03
        }
        
        print(f"  {data['symbol']:8s} Vol: {volatility_regime:6s} | Trend: {'Up' if data['change_pct'] > 0 else 'Down'}")
    
    # Phase 4: Signal Processing
    print("\n🧠 PHASE 4: SIGNAL PROCESSING")
    print("-" * 40)
    
    account_state = {
        'equity': 250000,
        'current_exposure': 35000
    }
    
    decisions = engine.process_model_outputs(model_outputs, market_conditions, account_state)
    
    # Display results
    executable_trades = []
    
    for symbol, decision in decisions.items():
        if decision.action not in ['NO_TRADE', 'WATCH', 'ERROR']:
            executable_trades.append(decision)
            print(f"\n  🎯 {symbol}")
            print(f"     Action: {decision.action}")
            print(f"     Direction: {'BUY' if decision.direction > 0 else 'SELL'}")
            print(f"     Confidence: {decision.confidence:.1%}")
            print(f"     Tier: {SignalTier.get_tier_name(decision.tier)}")
            if decision.size_shares > 0:
                print(f"     Size: ${decision.size_notional:,.2f}")
                print(f"     Risk: {decision.risk_pct:.2%}")
    
    # Phase 5: Trade Execution
    print("\n💰 PHASE 5: TRADE EXECUTION")
    print("-" * 40)
    
    if executable_trades:
        print(f"Executing {len(executable_trades)} trades...\n")
        
        total_exposure = 0
        total_risk = 0
        
        for trade in executable_trades[:5]:  # Top 5
            symbol = trade.symbol
            price_data = next((d for d in live_data if d['symbol'] == symbol), None)
            price = price_data['price'] if price_data else 100
            
            shares = int(trade.size_notional / price) if price > 0 else 0
            
            print(f"  ✅ {symbol} {'BUY' if trade.direction > 0 else 'SELL'} {shares:,} shares @ ${price:.2f}")
            print(f"     Notional: ${trade.size_notional:,.2f} | Risk: ${trade.risk_amount:,.2f}")
            
            total_exposure += trade.size_notional
            total_risk += trade.risk_amount
        
        print(f"\n  Total Exposure: ${total_exposure:,.2f}")
        print(f"  Total Risk: ${total_risk:,.2f} ({total_risk/account_state['equity']:.2%})")
    else:
        print("  ⚠️  No executable trades - all signals filtered out")
    
    # Phase 6: Summary
    print("\n📊 CYCLE SUMMARY")
    print("=" * 70)
    
    tier_counts = {}
    for d in decisions.values():
        tier_counts[d.tier] = tier_counts.get(d.tier, 0) + 1
    
    print(f"⏱️  Cycle Time: {datetime.now().strftime('%H:%M:%S')}")
    print(f"📊 Assets Scanned: {len(symbols)}")
    print(f"🤖 AI Signals: {len(model_outputs)}")
    print(f"🎯 Decisions: {len(decisions)}")
    print(f"💰 Trades: {len(executable_trades)}")
    
    print(f"\n📈 Signal Distribution:")
    for tier in sorted(tier_counts.keys(), reverse=True):
        print(f"   Tier {tier} ({SignalTier.get_tier_name(tier)}): {tier_counts[tier]}")
    
    print(f"\n🛡️ Risk Status:")
    print(f"   Portfolio: ${account_state['equity']:,.2f}")
    print(f"   Exposed: ${account_state['current_exposure']:,.2f}")
    print(f"   New Trades: ${sum(t.size_notional for t in executable_trades):,.2f}")
    
    # Save results
    results = {
        'timestamp': datetime.now().isoformat(),
        'assets_scanned': len(symbols),
        'ai_signals': len(model_outputs),
        'decisions': len(decisions),
        'trades': len(executable_trades),
        'exposure': sum(t.size_notional for t in executable_trades)
    }
    
    import json
    with open('live_cycle_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n✅ CYCLE COMPLETE - Results saved")
    print("=" * 70)

if __name__ == "__main__":
    asyncio.run(run_live_trading_cycle())
