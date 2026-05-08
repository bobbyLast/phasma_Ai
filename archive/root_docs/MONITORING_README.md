# Phasma AI 24/7 Monitoring System

## Overview
The Phasma AI 24/7 Monitoring System continuously scans all market sectors for trading opportunities around the clock, ensuring you never miss potential trades.

## Features
- **Continuous Scanning**: Runs 24/7 without stopping
- **Multi-Sector Coverage**: Monitors all industries equally
- **Configurable Intervals**: Scan frequency from 1-60 minutes
- **Error Recovery**: Automatic recovery from network/API issues
- **Graceful Shutdown**: Clean exit with Ctrl+C
- **Telegram Alerts**: High-confidence trade notifications
- **Market Regime Awareness**: Adapts to current volatility conditions

## Quick Start

### Method 1: Direct Python (Recommended)
```bash
# 5-minute intervals (default)
python monitor.py

# Custom interval (e.g., 10 minutes)
python monitor.py 10

# 1-minute intervals for high-frequency monitoring
python monitor.py 1
```

### Method 2: Batch File (Windows)
```cmd
# Double-click or run from command prompt
start_monitor.bat

# With custom interval
start_monitor.bat 10
```

### Method 3: Main System Commands
```bash
# Using main.py (same functionality)
python main.py monitor 5    # 5-minute intervals
python main.py monitor 10   # 10-minute intervals
```

## Configuration

The monitoring system uses settings from `config.json`:

```json
{
  "monitoring": {
    "enabled": true,
    "scan_interval_minutes": 5,
    "max_runtime_hours": 24,
    "error_retry_delay_minutes": 1,
    "telegram_alerts_enabled": true,
    "high_confidence_threshold": 0.7
  }
}
```

### Configuration Options

- **`scan_interval_minutes`**: How often to scan for opportunities (1-60 minutes)
- **`max_runtime_hours`**: Maximum hours to run (null = unlimited)
- **`telegram_alerts_enabled`**: Send alerts for high-confidence trades
- **`high_confidence_threshold`**: Minimum confidence for alerts (0.7 = 70%)

## What It Does Each Cycle

1. **Scans All Sectors**: Tech, Energy, Healthcare, Consumer, etc. (all equal weight)
2. **Validates Companies**: Only real, publicly traded companies
3. **Analyzes News**: Real-time sentiment and catalyst detection
4. **Generates Signals**: Using patterns, simulations, and market regime
5. **Risk Assessment**: Greeks-aware position sizing and limits
6. **Telegram Alerts**: Posts high-confidence trades (>70% POP)
7. **State Management**: Saves progress and continues seamlessly

## Sample Output

```
🚀 PHASMA AI 24/7 MONITORING MODE ACTIVATED
============================================================
📊 Scan Interval: 5 minutes
⏰ Max Runtime: 24 hours (288 cycles)
🛡️ Risk Management: Active
📱 Telegram Alerts: Enabled
🎯 High Confidence Threshold: 0.7

🟢 SYSTEM ONLINE - Monitoring all sectors equally
🟢 Press Ctrl+C to stop monitoring gracefully
============================================================

🔄 CYCLE 1 - 14:30:15
----------------------------------------
🌐 ALL SECTORS MODE: Scanning all industries equally
📊 Industry scan (EV/Auto): Found 3 relevant items
🧠 Running UNIFIED AI Analysis (Patterns + Simulations + Between the Lines)...
✅ Found 0 tradable options opportunities from 7 industries
📈 Market Regime: NORMAL

⏰ Next scan in 5 minutes...
💤 System will continue monitoring in background
```

## Monitoring Commands

### Stop Monitoring
- **Ctrl+C**: Graceful shutdown with statistics

### Check Status
The system displays:
- Current cycle number and timestamp
- Sectors scanned and opportunities found
- Market regime (Low/Normal/High volatility)
- High-confidence signals detected
- Next scan time

### Error Handling
- **Network Issues**: Automatic retry after delay
- **API Limits**: Respects rate limits and rotates sources
- **System Errors**: Logs errors and continues monitoring
- **Memory Management**: Efficient resource usage

## Use Cases

### Day Trading
```bash
python monitor.py 1    # 1-minute intervals for day trading
```

### Swing Trading
```bash
python monitor.py 15   # 15-minute intervals for swing opportunities
```

### Overnight Monitoring
```bash
python monitor.py 5    # 5-minute intervals to catch overnight moves
```

### Weekend Scanning
```bash
python monitor.py 30   # 30-minute intervals for weekend opportunities
```

## Safety Features

- **Risk Limits**: Never exceeds configured position sizes
- **Circuit Breakers**: Stops trading in extreme market conditions
- **Validation**: Only trades verified, real companies
- **Error Recovery**: Continues monitoring even after errors
- **State Preservation**: Saves progress between cycles

## Getting Help

If you encounter issues:
1. Check `config.json` for valid settings
2. Verify internet connection for API access
3. Check Telegram credentials in `.env` file
4. Review logs for specific error messages

**The system is designed to run continuously and safely monitor all market sectors for trading opportunities 24/7!**
