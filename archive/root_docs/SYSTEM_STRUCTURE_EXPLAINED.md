# Phasma AI System Structure Explained

## 📁 **FOLDER MEANINGS**

### 🧠 **brain/** - AI Thinking & Decision Making
- Contains ALL AI reasoning components
- Meta brain, signal convergence, market intelligence
- Centralized decision-making logic

### ⚙️ **core/** - Essential System Components
- Configuration management
- Trade logging and classification
- Performance tracking
- Database operations

### 🚀 **engines/** - Trading & Analysis Engines
- 159 specialized engines for different tasks
- News engines, options, Kalshi, weather, etc.
- Each engine handles specific trading functionality

### 🛠️ **utils/** - Utility Functions
- 88 utility modules
- Price fetchers, filters, calculators
- Helper functions used throughout system

### 📊 **data/** - Data Storage & Caches
- Market data caches
- Historical data storage
- Temporary data files

### 📋 **config/** - Configuration Files
- Trading parameters
- API credentials
- System settings

### 🌊 **waves/** - Market Wave Analysis
- Elliott Wave analysis
- Market pattern detection
- Technical analysis components

### 📝 **feedback_analysis/** - Learning & Improvement
- Trade feedback processing
- System learning loops
- Performance analysis

### 🗄️ **archive/** - Old/Deprecated Code
- Archived engines
- Legacy code kept for reference
- Disabled functionality

## 📄 **FILE TYPES**

### 🐍 **Python Files (.py)**
- **main.py** - Main trading system (273KB)
- **telegram_bot.py** - Telegram integration
- **unified_trading_system.py** - Unified trading logic
- **test_*.py** - Test files for various components

### 📄 **Markdown Files (.md)**
- **README.md** - Main documentation
- **_COMPLETE.md** - Completion status files
- **_SUMMARY.md** - Various summary documents
- **GUIDE.md** - User guides and tutorials

### ⚙️ **Config Files (.json)**
- **config.json** - Main configuration
- **phasma_state.json** - System state
- **trade_memory.json** - Trade history
- **_analyses.json** - Various analysis results

### 📊 **Log Files (.log)**
- **phasma_trading.log** - Main trading log
- **main_output.log** - System output
- **integration_test.log** - Test results

### 🗃️ **Database Files (.db)**
- **unified_main.db** - Main database
- **insider_accumulation.db** - Insider trading data

### 📜 **Environment Files (.env)**
- **.env** - API keys and secrets
- **.env.example** - Template for setup

## 🎯 **KEY COMPONENTS**

### **Trading Engines (159 total)**
- **News Engines**: Collect and analyze news
- **Options Engine**: Options trading logic
- **Kalshi Engine**: Prediction market trading
- **Weather Engines**: Weather-based trading
- **Social Engines**: Social media analysis
- **Risk Engines**: Risk management

### **Core Systems**
- **Meta Brain**: Central AI decision maker
- **Portfolio Manager**: Handles positions and capital
- **Trade Logger**: Records all trades
- **Performance Tracker**: Monitors performance

### **Utilities (88 total)**
- **Price Fetchers**: Get real-time prices
- **Filters**: Filter stocks and opportunities
- **Calculators**: Various calculations
- **Analyzers**: Analyze market data

## 🔄 **SYSTEM FLOW**

```
1. CONFIG → Load settings from config/
2. DATA → Fetch data via engines/
3. ANALYZE → Process with brain/
4. DECIDE → Make trading decisions
5. EXECUTE → Trade via unified system
6. LOG → Record in core/ and utils/
7. LEARN → Improve via feedback_analysis/
```

## 📈 **SPECIALIZED FOLDERS**

### **waves/** - Technical Analysis
- Elliott Wave theory implementation
- Market pattern recognition
- Technical indicators

### **feedback_analysis/** - Machine Learning
- Trade outcome analysis
- Strategy optimization
- Performance improvement

### **archive/** - Legacy Code
- Old trading strategies
- Deprecated engines
- Historical implementations

## 🚨 **IMPORTANT FILES**

- **main.py** - The heart of the system (273KB of code)
- **config.json** - All system settings
- **telegram_bot.py** - Communication layer
- **unified_trading_system.py** - Trading execution
- **phasma_state.json** - Current system state
- **emergency_kill_switch_*.json** - Emergency stops

## 💡 **KEY INSIGHTS**

1. **Modular Design**: Each folder has a specific purpose
2. **159 Engines**: Specialized tools for every trading aspect
3. **88 Utils**: Helper functions for everything
4. **Central Brain**: All AI thinking in one place
5. **Extensive Logging**: Every action is tracked
6. **Test Coverage**: Many test files for reliability
