# 🚀 QUICK START GUIDE - PHASMA AI WITH SMART MEMORY
## Everything is Connected and Ready to Run!

---

## ✅ **WHAT'S CONNECTED**

Your Phasma AI system now includes:

1. ✅ **Smart Memory Bank** - Automatic deduplication and fast lookups
2. ✅ **News Collection Network** - 58 RSS feeds, 24/7 monitoring
3. ✅ **Main Trading System** - All integrated and ready

---

## 🎯 **HOW TO RUN**

### **Option 1: Standard Trading Cycle (Recommended)**
```python
import asyncio
from main import PhasmaTradingSystem

async def main():
    # Initialize system
    system = PhasmaTradingSystem()
    
    # Run standard trading cycle
    # (News collection runs in background if enabled)
    signals = await system.run_full_cycle()
    
    print(f"Generated {len(signals)} trading signals")

if __name__ == "__main__":
    asyncio.run(main())
```

### **Option 2: With 24/7 News Collection**
```python
import asyncio
from main import PhasmaTradingSystem

async def main():
    # Initialize system
    system = PhasmaTradingSystem()
    
    # Start 24/7 news collection (optional)
    await system.start_news_collection()
    
    # Run trading cycle
    signals = await system.run_full_cycle()
    
    # Check memory stats
    system.get_news_memory_stats()
    
    # Keep running or stop
    # await system.stop_news_collection()

if __name__ == "__main__":
    asyncio.run(main())
```

---

## 📊 **HOW TO CHECK IF EVERYTHING IS WORKING**

### **Test Script**:
```python
import asyncio
from main import PhasmaTradingSystem

async def test_system():
    print("🧪 Testing Phasma AI Integration...")
    
    # Initialize
    system = PhasmaTradingSystem()
    
    # Test 1: Check if memory bank loaded
    memory_stats = system.news_engine.get_memory_stats()
    print(f"\n✅ Smart Memory Bank: {memory_stats.get('status', 'unknown')}")
    
    # Test 2: Check if news network loaded
    network_stats = system.news_engine.get_network_stats()
    print(f"✅ News Collection Network: {network_stats.get('status', 'unknown')}")
    print(f"   RSS Feeds: {network_stats.get('feeds_count', 0)}")
    
    # Test 3: Start news collection
    print("\n🚀 Starting news collection...")
    success = await system.start_news_collection()
    
    if success:
        print("✅ News collection started!")
        
        # Wait 90 seconds for first fetch
        print("\n⏳ Waiting 90 seconds for first news fetch...")
        await asyncio.sleep(90)
        
        # Check stats again
        system.get_news_memory_stats()
        
        # Stop collection
        await system.stop_news_collection()
    else:
        print("❌ News collection failed to start")
    
    print("\n✅ System test complete!")

if __name__ == "__main__":
    asyncio.run(test_system())
```

**Save this as `test_smart_memory.py` and run it!**

---

## 🔧 **WHAT HAPPENS WHEN YOU RUN MAIN.PY**

### **Initialization (Automatic)**:
```
[OK] Successfully loaded NewsAPIIntegration from modular news engine
[OK] Smart Memory Bank initialized
[OK] News Collection Network initialized (58 RSS feeds)
[OK] News Engine initialized with modular components + Smart Memory + RSS Network
✅ Partnership Engine Initialized
✅ Social Media Monitor Initialized
✅ Trade Database Initialized
🚀 Phasma AI Trading System Initialized
```

### **When You Call `run_full_cycle()`**:
```
🔄 Starting Unified Phasma Trading Cycle
================================================
🎯 Using Hybrid Industry Scanning (High-Volume + Targeted News + Partnerships)
📊 Found X industry-focused trading opportunities
```

### **Optional: Start 24/7 News Collection**:
```python
await system.start_news_collection()

# Output:
[INFO] Starting 24/7 News Collection Network...
[OK] News Collection Network started (58 RSS feeds, 60s interval)
🚀 24/7 News Collection Network is now running
   📰 58 RSS feeds being monitored every 60 seconds
   🧠 Smart Memory Bank active for deduplication
```

---

## 💡 **HOW TO USE THE MEMORY BANK**

### **Get News for a Symbol**:
```python
# Get last 24 hours of TSLA news
tsla_news = system.news_engine.get_news_from_memory('TSLA', hours_back=24)

for article in tsla_news:
    print(f"Title: {article['title']}")
    print(f"Sentiment: {article.get('sentiment', 0)}")
    print(f"Source: {article['source']}")
    print()
```

### **Search by Keywords**:
```python
# Search for earnings news
earnings = system.news_engine.search_news_memory(
    keywords=['earnings', 'beat', 'revenue'],
    hours_back=6
)

print(f"Found {len(earnings)} earnings-related articles")
```

### **Get Historical Analysis**:
```python
# Get 30-day history for NVDA
history = system.news_engine.get_symbol_history('NVDA', days_back=30)

print(f"Article Count: {history['article_count']}")
print(f"Avg Sentiment: {history['avg_sentiment']:.2f}")
print(f"Most Active Source: {history['most_active_source']}")
```

### **Get System Stats**:
```python
# Get memory and network stats
stats = system.get_news_memory_stats()

# Output:
📊 NEWS INTELLIGENCE SYSTEM STATUS:
==================================================
🧠 Smart Memory Bank:
   Total Articles: 2,847
   Unique Symbols: 523
   Duplicates Prevented: 1,921
   Cache Efficiency: 94.3%

📰 News Collection Network:
   RSS Feeds: 58
   Total Fetches: 1,440
   Articles Collected: 2,847
   Duplicates Filtered: 1,923
   Running: ✅ Yes
```

---

## 🎯 **CONFIGURATION OPTIONS**

Add to your `config.json`:

```json
{
  "trading": {
    "auto_start_news_collection": false,
    "all_sectors_mode": true
  }
}
```

**Options**:
- `auto_start_news_collection`: If `true`, starts 24/7 collection automatically
- `all_sectors_mode`: If `true`, scans all industries equally

---

## 📁 **FILE STRUCTURE**

```
phasma_Ai/
├── main.py                              # Main entry point ✅ CONNECTED
├── engines/
│   ├── __init__.py                      # Exports NewsAPIIntegration ✅
│   ├── news_engine_core.py              # Main news engine ✅ CONNECTED
│   ├── news_memory_bank.py              # Smart Memory Bank ✅ NEW
│   ├── news_collection_network.py       # RSS Network ✅ NEW
│   └── news_engine_apis.py              # API scanners ✅ UPDATED
└── phasma_core_memory/                  # Memory storage (auto-created)
    ├── daily/                           # Daily news files
    ├── symbols/                         # Per-symbol storage
    └── cache/                           # Cache files
```

---

## 🚀 **EXAMPLE: COMPLETE WORKFLOW**

```python
import asyncio
from main import PhasmaTradingSystem

async def complete_workflow():
    # 1. Initialize system
    print("🚀 Initializing Phasma AI...")
    system = PhasmaTradingSystem()
    
    # 2. Start 24/7 news collection (optional)
    print("\n📰 Starting news collection...")
    await system.start_news_collection()
    
    # 3. Wait for first news fetch (90 seconds)
    print("\n⏳ Waiting for first news batch...")
    await asyncio.sleep(90)
    
    # 4. Check what was collected
    print("\n📊 News Memory Stats:")
    stats = system.get_news_memory_stats()
    
    # 5. Run trading cycle
    print("\n🎯 Running trading cycle...")
    signals = await system.run_full_cycle()
    
    print(f"\n✅ Generated {len(signals)} trading signals")
    
    # 6. Check memory for specific symbol
    if signals:
        symbol = signals[0].symbol
        print(f"\n🔍 Checking memory for {symbol}...")
        
        # Get all news for this symbol
        symbol_news = system.news_engine.get_news_from_memory(symbol, hours_back=24)
        print(f"Found {len(symbol_news)} articles for {symbol}")
        
        # Get historical analysis
        history = system.news_engine.get_symbol_history(symbol, days_back=30)
        print(f"30-day article count: {history.get('article_count', 0)}")
        print(f"Avg sentiment: {history.get('avg_sentiment', 0):.2f}")
    
    # 7. Stop news collection when done
    print("\n⏸️ Stopping news collection...")
    await system.stop_news_collection()
    
    print("\n✅ Workflow complete!")

if __name__ == "__main__":
    asyncio.run(complete_workflow())
```

---

## ✅ **VERIFICATION CHECKLIST**

Run `python main.py` and check for these messages:

- ✅ `[OK] Smart Memory Bank initialized`
- ✅ `[OK] News Collection Network initialized (58 RSS feeds)`
- ✅ `[OK] News Engine initialized with modular components + Smart Memory + RSS Network`
- ✅ `🚀 Phasma AI Trading System Initialized`

If you see all these, **everything is connected!**

---

## 🎉 **YOU'RE READY!**

**Everything is connected to main.py and ready to run!**

**What you can do now**:
1. ✅ Run standard trading cycles (memory works automatically)
2. ✅ Start 24/7 news collection (`await system.start_news_collection()`)
3. ✅ Query news from memory (no repeated lookups)
4. ✅ Get historical analysis (sentiment trends, patterns)
5. ✅ Check system stats (`system.get_news_memory_stats()`)

**No configuration needed** - it works out of the box! 🚀
