# PHASMA AI - Signal Framework Quick Start Guide

## 🚀 Getting Started in 5 Minutes

### Step 1: Add API Keys (Optional but Recommended)
```bash
# Edit .env file and add real API keys:
ALPHA_VANTAGE_KEY=your_key_here
FINNHUB_API_KEY=your_key_here
POLYGON_API_KEY=your_key_here
```

Without API keys, system uses realistic simulated data.

### Step 2: Import Signal Framework in main.py

Add to top of main.py:
```python
from signal_framework_integration import SignalFrameworkIntegration
```

### Step 3: Initialize in PhasmaTradingSystem

In `__init__` method:
```python
self.signal_framework = SignalFrameworkIntegration(self.config)
```

### Step 4: Use in run_full_cycle()\nReplace signal processing section with:
```python
# Process signals through Signal Framework
market_conditions = self._build_market_conditions(symbols)
account_state = {
    'equity': self.real_portfolio.state['total_capital'],
    'current_exposure': self.real_portfolio.state['total_exposure']
}

decisions = self.signal_framework.process_convergence_signals(
    all_signals, 
    market_conditions,
    account_state
)

# Execute trades
for decision in decisions:
    trade = self.signal_framework.format_trade_for_execution(
        decision, 
        current_price
    )
    self.execute_trade(trade)
```

## ✅ What's Working Now

1. **Signal Framework** (`trading/signal_framework.py`)
   - Normalized signals with direction, confidence
   - 5-tier confidence system
   - Risk-managed position sizing
   - Decision bands (No-Trade → Watch → Entry → Conviction)

2. **AI Integration** (`trading/ai_integration.py`)
   - Multi-model aggregation
   - Multi-timeframe analysis
   - Confidence calculation from multiple sources

3. **Integration Module** (`signal_framework_integration.py`)
   - Converts Phasma signals to Signal Framework format
   - Processes through risk management
   - Returns executable trades

## 📊 Example Usage

```python
# Test the system
python live_trading_cycle.py

# Run integration test
python signal_framework_integration.py

# Run filtered funnel demo
python filtered_funnel_demo.py
```

## 🎯 Key Features

- **Tier-Based System**: NO_EDGE → WEAK → MODERATE → STRONG → HIGH_CONV
- **Decision Bands**: Automatic filtering based on market conditions
- **Position Sizing**: Risk-based sizing with tier multipliers
- **Risk Management**: Daily loss limits, max exposure, per-trade risk caps

## 🔧 Configuration Options

Edit risk parameters in SignalFrameworkIntegration:
```python
RiskParameters(
    max_risk_per_trade=0.02,      # 2% per trade
    daily_loss_limit=0.05,        # 5% daily limit
    max_concurrent_exposure=0.30  # 30% max exposure
)
```

## 📈 Next Steps

1. Add real API keys for live data
2. Run 24/7 paper trading test
3. Monitor performance metrics
4. Adjust confidence thresholds based on results

## 🆘 Need Help?

Files to review:
- `trading/signal_framework.py` - Core signal logic
- `trading/ai_integration.py` - AI model integration
- `signal_framework_integration.py` - Phasma integration layer
- `live_trading_cycle.py` - Full working example
