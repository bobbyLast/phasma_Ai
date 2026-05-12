# PHASMA AI TRADING SYSTEM - VISUAL FLOW DIAGRAM

## System Flow Chart

```
┌─────────────────────────────────────────────────────────────────┐
│                    PHASMA AI TRADING SYSTEM                      │
└─────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────┐
│                     1. INITIALIZATION                           │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  │
│  │ Market Cache    │  │ Partnership     │  │ Position        │  │
│  │ Refresh         │  │ Monitor Start   │  │ Reconciliation  │  │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────┐
│                   2. SIGNAL GENERATION                          │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  │
│  │ Unified Meta    │  │ News Engine     │  │ Social Engine   │  │
│  │ Brain (15 str)  │  │ (5 APIs)        │  │ (Trends)        │  │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘  │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  │
│  │ Silver Monitor  │  │ Unusual Whales  │  │ Insider/Poli-   │  │
│  │ (Commodities)   │  │ (Options Flow)  │  │ tician Trading  │  │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────┐
│                   3. SIGNAL PROCESSING                          │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  │
│  │ Confluence      │  │ Signal          │  │ Thematic        │  │
│  │ Service         │  │ Validation      │  │ Analysis        │  │
│  │ ($1000 limit)   │  │ (Quality Check) │  │ (Macro Trends)  │  │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────┐
│                   4. CONVERGENCE ANALYSIS                       │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  │
│  │ Multi-Source    │  │ Confluence      │  │ Position        │  │
│  │ Alignment       │  │ Scoring         │  │ Sizing          │  │
│  │ (2+ sources)    │  │ (Boost 80-280%) │  │ (Dynamic)       │  │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘  │
│                                                                 │
│  Source Weights:                                                 │
│  • Corporate: 90%    • Insider: 80%                             │
│  • Politician: 70%   • Kalshi: 60%                              │
└─────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────┐
│                    5. RISK MANAGEMENT                           │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  │
│  │ Confidence      │  │ Portfolio       │  │ Adaptive        │  │
│  │ Threshold       │  │ Limits          │  │ Thresholds      │  │
│  │ (Min 20%)       │  │ (10% max)       │  │ (Learning)      │  │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘  │
│                                                                 │
│  Risk Checks:                                                    │
│  • Max $1000/share  • Max 3 positions                           │
│  • Stop Loss: 10%   • Take Profit: 20%                          │
└─────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────┐
│                    6. TRADE EXECUTION                           │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  │
│  │ Alpaca Paper    │  │ Internal Paper  │  │ Order           │  │
│  │ Trading         │  │ Portfolio       │  │ Parameters      │  │
│  │ (Preferred)     │  │ (Fallback)      │  │ (Market, Day)   │  │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘  │
│                                                                 │
│  Execution Logic:                                                │
│  • Whole shares only  • Fractional if >85% confidence           │
│  • Auto-selling enabled  • Real-time monitoring                 │
└─────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────┐
│                    7. POST-EXECUTION                            │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  │
│  │ Position        │  │ Telegram        │  │ Trade           │  │
│  │ Monitoring      │  │ Alerts          │  │ Recording       │  │
│  │ (P&L Tracking)  │  │ (High Conf)     │  │ (Analytics)     │  │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘  │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  │
│  │ Winner's        │  │ Daily Learning  │  │ Audit           │  │
│  │ Gallery         │  │ Tracker         │  │ Trail           │  │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────┐
│                    8. FEEDBACK LOOP                             │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  │
│  │ Performance     │  │ Source          │  │ Threshold       │  │
│  │ Analytics       │  │ Reliability     │  │ Adjustment      │  │
│  │ (Win Rates)     │  │ Tracking        │  │ (Adaptive)      │  │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

## Decision Tree for Trade Execution

```
                    ┌─────────────┐
                    │ New Signal  │
                    └──────┬──────┘
                           │
                           ▼
                ┌─────────────────────┐
                │ Confidence ≥ 20%?   │───No──► Skip Trade
                └─────────┬───────────┘
                          │Yes
                          ▼
                ┌─────────────────────┐
                │ Whole Share Afford? │───No──► Confidence ≥ 85%?
                └─────────┬───────────┘          │
                          │Yes                    │No
                          ▼                       ▼
                ┌─────────────────────┐   ┌─────────────────────┐
                │ Calculate Position  │   │ Skip Trade          │
                │ Size (1 share)      │   └─────────────────────┘
                └─────────┬───────────┘
                          │
                          ▼
                ┌─────────────────────┐
                │ Portfolio Limit OK? │───No──► Skip Trade
                └─────────┬───────────┘
                          │Yes
                          ▼
                ┌─────────────────────┐
                │ Execute Trade       │
                │ (Alpaca/Internal)   │
                └─────────┬───────────┘
                          │
                          ▼
                ┌─────────────────────┐
                │ Set Auto-Sell       │
                │ (TP 20%, SL 10%)    │
                └─────────┬───────────┘
                          │
                          ▼
                ┌─────────────────────┐
                │ Monitor & Record    │
                └─────────────────────┘
```

## Data Flow Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        DATA LAYER                               │
│                                                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │ News APIs    │  │ Market Data │  │ Social      │             │
│  │ (5 sources)  │  │ (Yahoo, AV) │  │ APIs        │             │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘             │
         │                 │                 │                   │
         └─────────────────┴─────────────────┴───────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────┐
│                    PROCESSING LAYER                             │
│                                                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │ Signal      │  │ Confluence  │  │ Convergence │             │
│  │ Validation  │  │ Service     │  │ Engine      │             │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘             │
         │                 │                 │                   │
         └─────────────────┴─────────────────┴───────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────┐
│                     DECISION LAYER                              │
│                                                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │ Risk        │  │ Position    │  │ Adaptive    │             │
│  │ Management  │  │ Sizing      │  │ Thresholds  │             │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘             │
         │                 │                 │                   │
         └─────────────────┴─────────────────┴───────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────┐
│                    EXECUTION LAYER                              │
│                                                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │ Alpaca      │  │ Internal    │  │ Order       │             │
│  │ Paper Trade │  │ Portfolio   │  │ Management  │             │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘             │
         │                 │                 │                   │
         └─────────────────┴─────────────────┴───────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────┐
│                  MONITORING LAYER                               │
│                                                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │ Position    │  │ Telegram    │  │ Analytics   │             │
│  │ Tracking    │  │ Alerts      │  │ & Learning  │             │
│  └─────────────┘  └─────────────┘  └─────────────┘             │
└─────────────────────────────────────────────────────────────────┘
```

## Key Process Timelines

### Signal Processing Timeline
```
0s: Market Cache Refresh
├── 5s: Partnership Monitor Start
├── 10s: Position Reconciliation
├── 30s: Unified Meta Brain Analysis
├── 60s: News Engine Scan (5 APIs)
├── 90s: Social Engine Trends
├── 120s: Additional Sources (Silver, Options, etc.)
├── 180s: Confluence Service Processing
├── 240s: Convergence Analysis
├── 300s: Risk Management Checks
├── 360s: Trade Execution
└── 420s: Post-Execution Setup
```

### Trade Monitoring Timeline
```
Entry: Immediate execution & monitoring
├── 1min: Initial price check
├── 5min: First profit/loss assessment
├── 30min: Regular monitoring cycle
├── 1hr: Market condition update
├── 4hr: Position review
├── 24hr: Daily performance analysis
└── Exit: Auto-sell on TP/SL or manual
```

## Critical Integration Points

1. **Data Source Rotation**: Prevents rate limits, ensures continuous flow
2. **Confluence Service**: Central validation point for all signals
3. **Risk Manager**: Single source of truth for position limits
4. **Adaptive Thresholds**: Self-improving execution criteria
5. **Paper Trading Interface**: Clean separation from real money

## Failure Modes & Recovery

1. **API Failure**: Falls back to alternative sources
2. **Confluence Failure**: Uses individual signals with lower confidence
3. **Execution Failure**: Retries with fallback methods
4. **Monitoring Failure**: Continues trading, logs errors
5. **Data Corruption**: Clears cache, reinitializes

This visual representation provides a clear understanding of how the Phasma AI Trading System processes information and makes trading decisions.
