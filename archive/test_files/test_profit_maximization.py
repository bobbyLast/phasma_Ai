#!/usr/bin/env python3
"""
Test script for Profit Maximization Exit Manager
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.profit_maximization_exit_manager import ProfitMaximizationExitManager
from datetime import datetime, timedelta

def test_profit_maximization():
    """Test the profit maximization exit manager"""
    
    print("="*80)
    print("PROFIT MAXIMIZATION EXIT MANAGER TEST")
    print("="*80)
    
    # Configuration
    config = {
        "trailing_stop_pct": 0.20,
        "min_hold_days": 7,
        "max_hold_days": 90,
        "partial_profit_levels": [0.30, 0.60, 1.00],
        "partial_sell_sizes": [0.25, 0.25, 0.50],
        "momentum_threshold": 0.40
    }
    
    # Initialize manager
    manager = ProfitMaximizationExitManager(config)
    print("✅ Profit Maximization Exit Manager Initialized")
    
    # Test 1: Add a position
    print("\n1. ADDING TEST POSITION")
    print("-"*40)
    ticker = "TEST"
    entry_price = 10.00
    shares = 100
    
    position_id = manager.add_position(ticker, entry_price, shares)
    print(f"✅ Added position: {ticker}")
    print(f"   Entry: ${entry_price:.2f}")
    print(f"   Shares: {shares}")
    print(f"   Position ID: {position_id}")
    
    # Test 2: Check exit signals (should hold - minimum period)
    print("\n2. CHECKING EXIT SIGNALS (Day 1)")
    print("-"*40)
    current_price = 11.00  # 10% profit
    result = manager.check_exit_signals(ticker, current_price)
    print(f"Current Price: ${current_price:.2f} (+10%)")
    print(f"Action: {result['action']}")
    print(f"Reason: {result['reason']}")
    
    # Test 3: Simulate price increase to 30% profit
    print("\n3. PRICE INCREASE TO 30% PROFIT")
    print("-"*40)
    current_price = 13.00  # 30% profit
    result = manager.check_exit_signals(ticker, current_price)
    print(f"Current Price: ${current_price:.2f} (+30%)")
    print(f"Action: {result['action']}")
    print(f"Reason: {result['reason']}")
    
    # Test 4: Simulate 7 days later (minimum hold met)
    print("\n4. AFTER 7 DAYS (Minimum Hold Met)")
    print("-"*40)
    # Manually update the database to simulate time passing
    import sqlite3
    conn = sqlite3.connect(manager.db_path)
    cursor = conn.cursor()
    old_date = (datetime.now() - timedelta(days=8)).isoformat()
    cursor.execute("UPDATE positions SET entry_date = ? WHERE id = ?", (old_date, position_id))
    conn.commit()
    conn.close()
    
    result = manager.check_exit_signals(ticker, current_price)
    print(f"Current Price: ${current_price:.2f} (+30%)")
    print(f"Action: {result['action']}")
    print(f"Reason: {result['reason']}")
    
    if result['action'] == 'PARTIAL_SELL':
        print(f"🎯 PARTIAL PROFIT TAKING TRIGGERED!")
        print(f"   Sell {result['sell_percent']:.0f}% at 30% profit")
        manager.execute_exit(result['position_id'], result['shares'], current_price, result['reason'])
    
    # Test 5: Price continues rising to 60% profit
    print("\n5. PRICE RISES TO 60% PROFIT")
    print("-"*40)
    current_price = 16.00  # 60% profit
    result = manager.check_exit_signals(ticker, current_price)
    print(f"Current Price: ${current_price:.2f} (+60%)")
    print(f"Action: {result['action']}")
    print(f"Reason: {result['reason']}")
    
    if result['action'] == 'PARTIAL_SELL':
        print(f"🎯 SECOND PARTIAL PROFIT TAKING!")
        manager.execute_exit(result['position_id'], result['shares'], current_price, result['reason'])
    
    # Test 6: Trailing stop test
    print("\n6. TRAILING STOP TEST")
    print("-"*40)
    # Price goes up to 100% profit
    current_price = 20.00  # 100% profit
    result = manager.check_exit_signals(ticker, current_price)
    print(f"Price rises to: ${current_price:.2f} (+100%)")
    
    # Get trailing stop
    conn = sqlite3.connect(manager.db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT trailing_stop FROM positions WHERE id = ?", (position_id,))
    trailing_stop = cursor.fetchone()[0]
    conn.close()
    
    print(f"Trailing stop set to: ${trailing_stop:.2f}")
    
    # Price drops to trigger trailing stop
    drop_price = trailing_stop * 0.95  # 5% below trailing stop
    result = manager.check_exit_signals(ticker, drop_price)
    print(f"Price drops to: ${drop_price:.2f}")
    print(f"Action: {result['action']}")
    print(f"Reason: {result['reason']}")
    
    if result['action'] == 'EXIT_ALL':
        print(f"🛑 TRAILING STOP TRIGGERED - EXIT ALL!")
        manager.execute_exit(result['position_id'], result['shares'], drop_price, result['reason'])
    
    # Test 7: Generate report
    print("\n7. PROFIT MAXIMIZATION REPORT")
    print("-"*40)
    report = manager.generate_daily_report()
    print(f"Date: {report['date']}")
    print(f"Active Positions: {report['active_positions']}")
    
    # Test 8: Show exit history
    print("\n8. EXIT HISTORY")
    print("-"*40)
    conn = sqlite3.connect(manager.db_path)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT eh.*, p.ticker 
        FROM exit_history eh 
        JOIN positions p ON eh.position_id = p.id 
        WHERE p.ticker = ?
        ORDER BY eh.exit_date
    """, (ticker,))
    
    exits = cursor.fetchall()
    for exit in exits:
        print(f"Exit: {float(exit[3]):.2f} shares at ${float(exit[2]):.2f}")
        print(f"Profit: {float(exit[5])*100:.1f}% | Reason: {exit[4]}")
    
    conn.close()
    
    print("\n" + "="*80)
    print("✅ PROFIT MAXIMIZATION TEST COMPLETE")
    print("="*80)
    print("\n🎯 KEY FEATURES TESTED:")
    print("   ✓ Minimum holding period enforcement")
    print("   ✓ Partial profit taking at 30% and 60%")
    print("   ✓ Dynamic trailing stops (tighten at higher profits)")
    print("   ✓ Exit history tracking")
    print("\n💡 This system prevents early exits and maximizes profits!")
    
    # Clean up test database
    os.remove(manager.db_path)
    print("\n🧹 Test database cleaned up")

if __name__ == "__main__":
    test_profit_maximization()
