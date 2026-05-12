# Phasma AI 24/7 Trading Monitor - Quick Start

## Start 24/7 Monitoring

### Method 1: Dedicated Monitor Script (Recommended)
```bash
# 5-minute intervals (default)
python monitor.py

# Custom intervals
python monitor.py 10    # 10-minute intervals
python monitor.py 15    # 15-minute intervals
python monitor.py 30    # 30-minute intervals
```

### Method 2: Windows Batch File
```cmd
# Double-click or run from command prompt
start_monitor.bat

# With custom interval
start_monitor.bat 10
```

### Method 3: Main System
```bash
python main.py monitor 5    # 5-minute intervals
python main.py monitor 15   # 15-minute intervals
```

## What It Does

1. **Scans All Sectors**: Monitors Tech, Energy, Healthcare, Consumer, Materials, etc. equally
2. **Real-time Analysis**: News sentiment, options chains, market regime detection
3. **Risk Management**: Greeks-aware position sizing, stop losses, portfolio limits
4. **Telegram Alerts**: Sends notifications for high-confidence trades (>70% POP)
5. **Error Recovery**: Continues monitoring even after network issues
6. **State Preservation**: Saves progress and resumes seamlessly

## Configuration

Edit `config.json` to customize:

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

## Stop Monitoring

- **Ctrl+C**: Graceful shutdown with statistics
- **Close Terminal**: Emergency stop (less clean)

## Monitor Status

The system displays:
- Current cycle and timestamp
- Sectors scanned and opportunities found
- Market regime (Low/Normal/High volatility)
- High-confidence signals detected
- Next scan time and status

## Safety Features

- **Risk Limits**: Never exceeds configured position sizes
- **Circuit Breakers**: Stops trading in extreme conditions
- **Company Validation**: Only trades verified companies
- **Error Recovery**: Continues after network/API issues
- **Resource Management**: Efficient memory and CPU usage

**The Phasma AI is now ready for 24/7 continuous trading across all market sectors!**
