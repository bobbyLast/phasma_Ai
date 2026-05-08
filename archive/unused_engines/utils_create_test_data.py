"""
Create Realistic Test Data for Trader Performance Tracker

Generates historical trader calls with realistic dates and prices
to properly test the performance tracking functionality.
"""

import json
import os
from datetime import datetime, timedelta, timezone
from trader_call_logger import TraderCallLogger, TraderCall, Direction, Horizon

def create_realistic_test_data():
    """Create realistic historical trader calls for testing"""
    
    logger = TraderCallLogger()
    
    # Clear existing test data
    logger._save_calls([])
    
    # Historical calls from November 2024 with realistic prices
    test_calls = [
        # Stock Guru - Mixed performance
        {
            'trader_id': 'stock_guru_123',
            'ticker': 'AAPL',
            'direction': 'LONG',
            'horizon': 'SWING',
            'entry_price': 175.00,
            'notes': 'Breakout above resistance',
            'source': 'manual',
            'timestamp': '2024-11-15T10:30:00+00:00'
        },
        {
            'trader_id': 'stock_guru_123',
            'ticker': 'NVDA',
            'direction': 'LONG',
            'horizon': 'SWING',
            'entry_price': 140.00,
            'notes': 'AI momentum continues',
            'source': 'manual',
            'timestamp': '2024-11-20T14:15:00+00:00'
        },
        {
            'trader_id': 'stock_guru_123',
            'ticker': 'GOOGL',
            'direction': 'SHORT',
            'horizon': 'SWING',
            'entry_price': 165.00,
            'notes': 'Overbought conditions',
            'source': 'manual',
            'timestamp': '2024-11-25T11:45:00+00:00'
        },
        
        # Penny King - High risk, mixed results
        {
            'trader_id': 'penny_king',
            'ticker': 'TSLA',
            'direction': 'BULLISH',
            'horizon': 'DAY_TRADE',
            'entry_price': 320.50,
            'notes': 'Momentum play',
            'source': 'manual',
            'timestamp': '2024-11-18T09:30:00+00:00'
        },
        {
            'trader_id': 'penny_king',
            'ticker': 'AMC',
            'direction': 'BULLISH',
            'horizon': 'DAY_TRADE',
            'entry_price': 4.25,
            'notes': 'Squeeze potential',
            'source': 'manual',
            'timestamp': '2024-11-22T10:15:00+00:00'
        },
        {
            'trader_id': 'penny_king',
            'ticker': 'GME',
            'direction': 'SHORT',
            'horizon': 'DAY_TRADE',
            'entry_price': 25.50,
            'notes': 'Overextended',
            'source': 'manual',
            'timestamp': '2024-11-27T13:30:00+00:00'
        },
        
        # Value Investor - Conservative, good performance
        {
            'trader_id': 'value_investor',
            'ticker': 'MSFT',
            'direction': 'LONG',
            'horizon': 'LONG_TERM',
            'entry_price': 410.00,
            'notes': 'Strong fundamentals, good entry point',
            'source': 'manual',
            'timestamp': '2024-11-10T12:00:00+00:00'
        },
        {
            'trader_id': 'value_investor',
            'ticker': 'JPM',
            'direction': 'LONG',
            'horizon': 'LONG_TERM',
            'entry_price': 198.00,
            'notes': 'Banking sector recovery',
            'source': 'manual',
            'timestamp': '2024-11-14T15:30:00+00:00'
        },
        {
            'trader_id': 'value_investor',
            'ticker': 'KO',
            'direction': 'LONG',
            'horizon': 'LONG_TERM',
            'entry_price': 63.50,
            'notes': 'Consumer staples safety',
            'source': 'manual',
            'timestamp': '2024-11-21T11:00:00+00:00'
        },
        
        # Tech Trader - Focus on technology sector
        {
            'trader_id': 'tech_trader',
            'ticker': 'META',
            'direction': 'LONG',
            'horizon': 'SWING',
            'entry_price': 515.00,
            'notes': 'Metaverse momentum',
            'source': 'manual',
            'timestamp': '2024-11-12T09:45:00+00:00'
        },
        {
            'trader_id': 'tech_trader',
            'ticker': 'AMD',
            'direction': 'LONG',
            'horizon': 'SWING',
            'entry_price': 125.00,
            'notes': 'Chip sector rally',
            'source': 'manual',
            'timestamp': '2024-11-19T14:20:00+00:00'
        },
        {
            'trader_id': 'tech_trader',
            'ticker': 'NFLX',
            'direction': 'SHORT',
            'horizon': 'SWING',
            'entry_price': 420.00,
            'notes': 'Streaming competition concerns',
            'source': 'manual',
            'timestamp': '2024-11-26T10:30:00+00:00'
        }
    ]
    
    # Load existing calls file and modify timestamps
    calls_file = logger.calls_file
    
    # Create calls with custom timestamps
    calls = []
    for call_data in test_calls:
        call = TraderCall(
            trader_id=call_data['trader_id'],
            ticker=call_data['ticker'],
            direction=Direction(call_data['direction']),
            timestamp=call_data['timestamp'],
            horizon=Horizon(call_data['horizon']),
            entry_price=call_data['entry_price'],
            notes=call_data['notes'],
            source=call_data['source']
        )
        calls.append(call)
    
    # Save the calls
    logger._save_calls(calls)
    
    # Also update CSV
    with open(logger.csv_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([
            'trader_id', 'ticker', 'direction', 'timestamp', 'horizon',
            'entry_price', 'notes', 'source'
        ])
        for call in calls:
            writer.writerow([
                call.trader_id,
                call.ticker,
                call.direction.value,
                call.timestamp,
                call.horizon.value,
                call.entry_price,
                call.notes,
                call.source
            ])
    
    print(f"✅ Created {len(test_calls)} realistic test calls")
    print("📊 Test data includes:")
    
    # Show summary
    traders = set(call.trader_id for call in calls)
    tickers = set(call.ticker for call in calls)
    
    print(f"   - {len(traders)} unique traders: {', '.join(traders)}")
    print(f"   - {len(tickers)} unique tickers: {', '.join(tickers)}")
    print(f"   - Date range: 2024-11-10 to 2024-11-27")
    print(f"   - Ready for performance tracking analysis")

if __name__ == "__main__":
    import csv
    create_realistic_test_data()
