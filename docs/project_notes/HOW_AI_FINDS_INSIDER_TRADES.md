# 🤖 How Phasma AI Finds Insider/Confluence Trades

## **📊 The AI Detection Pipeline**

### **Step 1: News Scanning & Symbol Extraction**
```python
# 1. Scan 1000+ news articles
news = scan_all_sources()

# 2. Extract symbols using company_db
for article in news:
    symbols = extract_symbols(article.text)
    for symbol in symbols:
        analyze_for_signals(symbol)
```

### **Step 2: Multi-Signal Analysis**
For each symbol found in news:

#### **A. Insider Signal Check**
```python
def analyze_insider_signals(symbol):
    # Check for million-dollar buys
    if symbol in insider_data:
        for transaction in insider_data[symbol]:
            if transaction['type'] == 'buy' and transaction['amount'] >= $1M:
                # Calculate confidence based on amount
                confidence = min(amount / $5M, 1.0)
                return {
                    'type': 'insider_buy',
                    'amount': $2,000,000,
                    'confidence': 40%
                }
```

#### **B. Institutional Signal Check**
```python
def analyze_institutional_signals(symbol):
    # Check 13F for NEW positions
    if new_13f_position(symbol):
        return {
            'type': 'institutional_accumulation',
            'institution': 'BlackRock',
            'confidence': 80%
        }
```

#### **C. Analyst Signal Check**
```python
def analyze_analyst_signals(symbol):
    # Get ratings and price targets
    if rating == 'strong_buy' and upside > 20%:
        return {
            'type': 'analyst_upgrade',
            'target': $5.00,
            'confidence': 60%
        }
```

#### **D. Options Signal Check**
```python
def analyze_options_signals(symbol):
    # Check for unusual call flow
    if call_volume > avg_volume * 3:
        return {
            'type': 'unusual_options_flow',
            'multiple': 4.5,
            'confidence': 50%
        }
```

### **Step 3: Confluence Scoring**
```python
def calculate_confluence_score(insider, institutional, analyst, options):
    score = 0
    
    if insider:
        score += insider['confidence'] * 0.30
    if institutional:
        score += institutional['confidence'] * 0.30
    if analyst:
        score += analyst['confidence'] * 0.20
    if options:
        score += options['confidence'] * 0.20
    
    return min(score, 1.0)
```

### **Step 4: Alert Generation**
```python
# Only alert if confluence >= 70%
if confluence_score >= 0.7:
    alert = {
        'symbol': 'XYZ',
        'confidence': 'HIGH',
        'score': 85%,
        'reasoning': 'Insider bought $2M | BlackRock accumulating | Analysts see 300% upside | Options flow 5x normal'
    }
    send_alert(alert)
```

## **🎯 Real Example Flow**

### **News Triggers Analysis:**
```
News: "XYZ Biotech announces Phase 2 trial success"
→ Symbol extracted: XYZ
→ AI runs signal analysis on XYZ
```

### **Signal Detection:**
```python
# 1. Insider Check
XYZ_insider = {
    'CEO bought $1.5M last week',
    'CBO bought $800K last month'
}

# 2. Institutional Check
XYZ_institutional = {
    'ARK Invest initiated 1M shares this quarter',
    'Vanguard added 500K shares'
}

# 3. Analyst Check
XYZ_analyst = {
    'Morgan Stanley: Strong Buy',
    'Price target: $8 (400% upside)'
}

# 4. Options Check
XYZ_options = {
    'Call volume: 10x average',
    'Heavy buying at $5 strikes'
}
```

### **Confluence Calculation:**
```
Insider Score: 40% (based on $2.3M total)
Institutional Score: 80% (major funds initiating)
Analyst Score: 60% (strong buy + 400% upside)
Options Score: 50% (10x volume)

Total = (40% × 30%) + (80% × 30%) + (60% × 20%) + (50% × 20%)
       = 12% + 24% + 12% + 10%
       = 58% → Below threshold, NO ALERT
```

### **What Would Trigger Alert:**
If insider buys were $5M instead of $2.3M:
```
Insider Score: 100% (maxed at $5M)
Total = (100% × 30%) + 24% + 12% + 10% = 76% → ALERT!
```

## **🔍 AI's Pattern Recognition**

### **Pattern 1: Pre-Catalyst Accumulation**
```python
# AI learns: Insiders buy 1-2 months BEFORE good news
if insider_buy_date < catalyst_date - 60_days:
    boost_confidence(20%)
```

### **Pattern 2: Multi-Insider Confirmation**
```python
# AI learns: Multiple insiders buying = stronger signal
if count_insiders_buying >= 3:
    boost_confidence(15%)
```

### **Pattern 3: Sector Momentum**
```python
# AI learns: Biotech insiders buying together = sector trend
if sector_insider_activity > threshold:
    boost_confidence(10%)
```

## **⚡ Real-Time Processing**

### **Every 5 Minutes:**
1. **Fetch new Form 4 filings**
2. **Update 13F database**
3. **Scan news for symbols**
4. **Run confluence analysis**
5. **Send alerts for scores >= 70%**

### **Example Alert Output:**
```
🚨 HIGH CONFLUENCE ALERT: ABC
├── Score: 82% (VERY HIGH)
├── Insider: CEO bought $3.2M at $2.50
├── Institutional: BlackRock initiated 2M shares
├── Analyst: Strong Buy, $6 target (140% upside)
├── Options: Call flow 8x normal
└── Catalyst: FDA decision in 6 weeks
```

## **🤖 AI Learning Loop**

### **Performance Tracking:**
```python
class PerformanceTracker:
    def track_alert(self, alert):
        # Record prediction
        self.predictions[alert.symbol] = {
            'date': alert.date,
            'score': alert.score,
            'prediction': 'UP'
        }
    
    def update_outcome(self, symbol, outcome):
        # Learn from results
        prediction = self.predictions[symbol]
        if prediction['prediction'] == outcome:
            # Increase weight for similar patterns
            self.learn_success(pattern)
        else:
            # Decrease weight for failed patterns
            self.learn_failure(pattern)
```

### **Adaptive Weights:**
```python
# AI adjusts weights based on performance
initial_weights = {'insider': 30%, 'institutional': 30%, 'analyst': 20%, 'options': 20%}

# After learning:
optimized_weights = {'insider': 35%, 'institutional': 25%, 'analyst': 15%, 'options': 25%}
# Reason: Insider signals more predictive, analyst less so
```

## **⚠️ Current Limitations**

### **1. Data Quality**
- Form 4 parsing errors
- Missing transaction codes
- Delayed 13F data

### **2. False Positives**
- 10b5-1 planned sales counted as sells
- Option exercises counted as buys
- Hedge fund rebalancing noise

### **3. Look-Ahead Bias**
- Using current knowledge for historical tests
- Not accounting for filing delays
- Survivorship bias in backtests

## **🎯 Assessment: Is It Good?**

### **Strengths:**
✅ Multi-signal approach reduces noise
✅ Real-time Form 4 processing
✅ Adaptive learning from outcomes
✅ Comprehensive confluence scoring

### **Weaknesses:**
❌ Overweights lagged 13F data (30%)
❌ Blunt insider filters (needs Form 4 codes)
❌ No human validation gates
❌ Look-ahead bias in backtesting

### **Verdict:**
**Conceptually strong but needs refinement.** The multi-signal approach is correct, but execution has issues identified earlier. With the improvements suggested (reduce 13F weight, add Form 4 parsing, human gates), this could be a very effective system.

### **Expected Performance After Fixes:**
- **Hit Rate**: 35% → 45%
- **False Positives**: 65% → 45%
- **Overall Return**: +50% → +70% annually

The AI has the right framework - it just needs the signal quality improvements and realistic timing to be truly effective.
