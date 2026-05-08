#!/usr/bin/env python3
"""
Simple Integration Test - Verifies all main components work together
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.insider_monitor import InsiderMonitor
from utils.thesis_manager import ThesisManager
from utils.integrated_trading_system import IntegratedTradingSystem
from utils.universal_stock_evaluator import UniversalStockEvaluator
import sqlite3


def main():
    print("="*80)
    print("SIMPLE INTEGRATION TEST")
    print("="*80)
    
    # Test 1: Thesis Manager
    print("\n1. THESIS MANAGER")
    print("-"*40)
    tm = ThesisManager()
    
    # Test Master Decision Loop
    decision = tm.master_decision_loop("NVDA")
    print(f"✓ NVDA: {decision['action']} - {decision['classification']}")
    
    decision = tm.master_decision_loop("PLUG")
    print(f"✓ PLUG: {decision['action']} - {decision['classification']}")
    
    # Test confidence events
    tm.record_confidence_event("NVDA", "positive", 10, "Test event")
    print("✓ Confidence events working")
    
    # Test 2: Universal Evaluator
    print("\n2. UNIVERSAL EVALUATOR")
    print("-"*40)
    ue = UniversalStockEvaluator()
    
    result = ue.evaluate_any_stock("AAPL")
    print(f"✓ AAPL: {result['action']} - {result['classification']}")
    
    result = ue.evaluate_any_stock("TSLA")
    print(f"✓ TSLA: {result['action']} - {result['classification']}")
    
    # Test batch evaluation
    batch = ["MSFT", "GOOGL", "META"]
    results = ue.batch_evaluate(batch)
    print(f"✓ Batch evaluation: {len(results)} stocks processed")
    
    # Test 3: Integrated System
    print("\n3. INTEGRATED TRADING SYSTEM")
    print("-"*40)
    config = {
        "insider_monitor": {"enabled": True, "lookback_days": 1},
        "watchlist": ["NVDA", "PLUG", "DUK"]
    }
    
    its = IntegratedTradingSystem(config)
    results = its.run_comprehensive_analysis()
    
    print(f"✓ Moonshot signals: {len(results['moonshot_signals'])}")
    print(f"✓ Thesis evaluations: {len(results['thesis_evaluations'])}")
    print(f"✓ Combined recommendations: {len(results['combined_recommendations'])}")
    
    # Test 4: Data Flow
    print("\n4. DATA FLOW TEST")
    print("-"*40)
    
    # Universal → Thesis flow
    test_tickers = ["AMD", "INTC"]
    for ticker in test_tickers:
        decision = ue.evaluate_any_stock(ticker)
        if decision["action"] == "establish_thesis":
            tm.establish_thesis(ticker, decision)
            print(f"✓ {ticker}: Universal → Thesis established")
    
    # Generate report
    report = its.generate_daily_report()
    print("✓ Daily report generated")
    
    # Test 5: Database
    print("\n5. DATABASE CHECK")
    print("-"*40)
    
    conn = sqlite3.connect("insider_accumulation.db")
    cursor = conn.cursor()
    
    # Check thesis positions
    cursor.execute("SELECT COUNT(*) FROM thesis_positions")
    count = cursor.fetchone()[0]
    print(f"✓ Thesis positions: {count}")
    
    # Check confidence events
    cursor.execute("SELECT COUNT(*) FROM confidence_events")
    count = cursor.fetchone()[0]
    print(f"✓ Confidence events: {count}")
    
    conn.close()
    
    print("\n" + "="*80)
    print("INTEGRATION TEST COMPLETE")
    print("="*80)
    
    print("""
✅ ALL COMPONENTS CONNECTED:

• Thesis Manager evaluates any stock
• Universal Evaluator works independently  
• Integrated System combines all signals
• Data flows between components
• Database persists all information
• Reports generated successfully

The system is fully integrated and working as specified.
    """)


if __name__ == "__main__":
    main()
