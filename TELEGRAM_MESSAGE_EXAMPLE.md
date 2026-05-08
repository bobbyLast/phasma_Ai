# 📱 NEW TELEGRAM MESSAGE FORMAT

## Example Trade Signal:

```
🚀 PHASMA AI TRADE SIGNAL

━━━━━━━━━━━━━━━━━━━━━━
📱 COPY TO ROBINHOOD/WEBULL:
━━━━━━━━━━━━━━━━━━━━━━

**Ticker:** META
**Action:** BUY TO OPEN
**Option Type:** Call
**Strike Price:** $639.35
**Expiration:** 11/17/25
**Contracts:** 4
**Limit Price:** $151.75 per contract

━━━━━━━━━━━━━━━━━━━━━━
💰 TRADE DETAILS:
━━━━━━━━━━━━━━━━━━━━━━

Total Cost: $607.00
Max Loss: $607.00
Take Profit: $265.56 (+75%)
Stop Loss: $91.05 (-40%)

🎯 EXIT STRATEGY (FROM SIMULATION):
Exit on Day 6 (11/17/25)
^ Simulations show profits PEAK this day ^

Confidence: 36.5%
POP: 42.0%

━━━━━━━━━━━━━━━━━━━━━━
📋 HOW TO ENTER IN APP:
━━━━━━━━━━━━━━━━━━━━━━

1. Search: META
2. Tap "Trade" → "Options"
3. Select: 11/17/25 expiration
4. Choose: $639.35 Call
5. Action: "Buy" (Level 2)
6. Quantity: 4 contract(s)
7. Order Type: "Limit"
8. Limit Price: $151.75
9. Review & Submit

━━━━━━━━━━━━━━━━━━━━━━
📊 AI ANALYSIS:
━━━━━━━━━━━━━━━━━━━━━━

📊 500+ Simulations ran every scenario
🎯 Profits PEAK on Day 6 → EXIT THEN
💰 Win rate: 42.0% | Avg P&L: $205
📈 POP: 42.0% (probability of profit)

━━━━━━━━━━━━━━━━━━━━━━
⚠️ EXIT RULES (STRICT!):
━━━━━━━━━━━━━━━━━━━━━━

1. SELL on Day 6 (simulation exit)
2. OR sell at $265.56 if hit early (+75% TP)
3. OR sell at $91.05 if hit (-40% SL)

Max risk: $607.00
Simulation tested 500+ scenarios → Day 6 = peak profit

🤖 Phasma AI - Level 2 Options Trading
```

---

## KEY CHANGES:

### BEFORE:
```
Exit Target: 6 days
```
^ Vague, sounds like a suggestion

### AFTER:
```
🎯 EXIT STRATEGY (FROM SIMULATION):
Exit on Day 6 (11/17/25)
^ Simulations show profits PEAK this day ^

⚠️ EXIT RULES (STRICT!):
1. SELL on Day 6 (simulation exit)
2. OR sell at $265.56 if hit early (+75% TP)
3. OR sell at $91.05 if hit (-40% SL)

Simulation tested 500+ scenarios → Day 6 = peak profit
```
^ Crystal clear: THIS IS THE EXIT DATE determined by simulation!

---

## HOW IT WORKS:

The Monte Carlo engine:
1. Runs 500+ different price scenarios
2. Calculates P&L for each day (Day 1, 2, 3, 4, 5, 6, 7)
3. Finds which day has the HIGHEST average profit across all scenarios
4. That day = optimal_exit_day = YOUR EXIT DATE

**No guessing. The simulation TELLS you when to exit!** 🎯
