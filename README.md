# Phasma AI Trading System - General-Purpose Multi-Asset Trading Platform

## Overview
**Phasma AI** is an institutional-grade trading platform that scans **all market sectors equally** for high-probability opportunities. The system trades any valid company across Technology, Energy, Healthcare, Consumer, Materials, and more with equal risk management and position sizing.

## Core Specifications
- **Platform**: Multi-asset trading (options, stocks, prediction markets, crypto)
- **Data Sources**: Real-time news (RSS feeds, social media, market data)
- **Risk Management**: 1% bankroll per trade, dynamic stop-losses, portfolio limits
- **Target Assets**: **Any publicly traded company** meeting criteria
- **Goals**: High-probability trades across all sectors, not limited to any industry

## System Architecture - Multi-Sector Trading

### Trading Philosophy
1. **Sector Agnostic**: Treats all industries equally (Technology, Energy, Healthcare, etc.)
2. **Company Neutral**: No preference for any specific companies or sectors
3. **Risk-Based**: Only trades when opportunities meet strict criteria
4. **Real Trading**: No fake signals - only real opportunities

### Key Components

#### Multi-Sector Scanner
- Scans **all market sectors** without bias
- Real-time news analysis across industries
- Company validation for any public company
- Equal risk assessment for all opportunities

#### Advanced Risk Engine
- Greeks-aware position sizing (Delta, Vega, Theta)
- Market regime detection (VIX-based volatility)
- Dynamic risk limits by market conditions
- Multi-leg options strategies (spreads, etc.)

#### Meta-Brain Controller
- Signal arbitration across all asset types
- Capital allocation (1% bankroll per trade)
- Risk governance and portfolio management
- Real-time decision optimization

## Repository layout

- **`main.py`** — primary entrypoint; run from the repository root.
- **`brain/`**, **`core/`**, **`engines/`**, **`trading/`**, **`utils/`**, **`compliance/`**, **`services/`**, **`brains/`** — packages used by the live system.
- **`config/`**, **`data/`** — configuration and reference data.
- **`scripts/`** — optional tooling and older drivers:
  - **`scripts/monitoring/`** — `monitor.py` (called by `start_monitor.bat`).
  - **`scripts/alternate_mains/`** — alternate entry scripts (for example `main_production.py`).
  - **`scripts/demos/`** — demos.
  - **`scripts/ops/`** — Telegram bot, production launcher, preflight helpers.
  - **`scripts/legacy/`** — one-off integrators, experiments, and maintenance scripts (not required to run `main.py`).
- **`docs/`** — documentation; planning write-ups are under **`docs/project_notes/`**, tickets under **`docs/tickets/`**.
- **`yfinance.py`** — compatibility shim kept at the repo root so `import yfinance` resolves when running from this directory.

Root-level **`test_*.py`** files and the old **`tests/`** package were removed; they were not part of the production path for `main.py`.

## Usage

### Quick Start
```bash
cd path/to/phasma_Ai
python main.py
```

### Test Output Example
```
🚀 Starting Unified Phasma Trading Cycle
🌐 ALL SECTORS MODE: Scanning all industries equally
📊 Industry scan (EV/Auto): Found 3 relevant items
🧠 Running UNIFIED Analysis (Patterns + Simulations + Between the Lines)...
✅ Found 0 tradable options opportunities from 7 industries
🏁 Phasma session complete!
```

### Key Features
- **Multi-Sector Scanning**: Equal coverage of all market sectors
- **Real Company Validation**: Only trades verified public companies
- **Options Trading**: Greeks-based position sizing and spread strategies
- **Risk Management**: Automated 1% position sizing with Greeks awareness
- **Market Regime Detection**: Adapts strategies based on VIX volatility levels

## Trading Philosophy

### Sector-Neutral Approach
The system **does not prefer any sector** and treats all industries equally:
- **No bias**: Technology sector has same weight as Energy, Healthcare, etc.
- **Equal opportunity**: Any company can be traded if it meets criteria
- **Risk-based decisions**: Only trades when probability and risk metrics align
- **Real validation**: Every company is verified before trading

### Risk Parameters
- **Position Size**: 1% of bankroll per trade (Greeks-adjusted)
- **Stop Loss**: Dynamic based on options Greeks and market regime
- **Max Drawdown**: 10% portfolio protection
- **POP Threshold**: 70%+ probability of profit required

## System Status

✅ **Multi-sector scanning** - All 8 sectors scanned equally  
✅ **Company validation** - Real-time verification via Yahoo Finance  
✅ **Options engine** - Greeks calculation and spread strategies  
✅ **Risk management** - Advanced Greeks-aware position sizing  
✅ **Market regime detection** - VIX-based volatility adaptation  
✅ **Monte Carlo simulation** - Reality-checked predictions  
✅ **Telegram integration** - High-confidence trade alerts  

**The Phasma is now a true general-purpose trading system ready to find opportunities in any market sector!**

## 24/7 Continuous Monitoring

### Quick Start
```bash
# Start continuous monitoring (5-minute intervals)
python monitor.py

# Custom intervals
python monitor.py 10    # 10-minute intervals
python monitor.py 30    # 30-minute intervals

# Via main system
python main.py monitor 5
```

### Features
- **Continuous Scanning**: Never miss opportunities with automated cycles
- **Multi-Sector Coverage**: Monitors all industries equally without bias
- **Telegram Alerts**: Instant notifications for high-confidence trades
- **Market Regime Detection**: Adapts to current volatility conditions
- **Error Recovery**: Continues monitoring even after network issues
- **Graceful Shutdown**: Clean exit with comprehensive statistics

### Configuration
```json
{
  "monitoring": {
    "scan_interval_minutes": 5,
    "max_runtime_hours": 24,
    "telegram_alerts_enabled": true,
    "high_confidence_threshold": 0.7
  }
}
```

### Safety Features
- **Risk Limits**: Never exceeds configured position sizes
- **Company Validation**: Only trades verified, real companies
- **Circuit Breakers**: Automatic stops in extreme market conditions
- **State Preservation**: Maintains progress between cycles
