"""
Trader Call Interface - Manual Input System for Stage 1

Provides a simple command-line interface for manually logging external trader calls.
This bridges the gap between automated data collection and manual entry.

Usage:
    python utils/trader_call_interface.py
"""

import sys
import os
from datetime import datetime
from typing import Optional

# Add the project root to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.trader_call_logger import TraderCallLogger, Direction, Horizon

class TraderCallInterface:
    """
    Command-line interface for manually logging trader calls
    """
    
    def __init__(self):
        self.logger = TraderCallLogger()
        print("🎯 Trader Call Interface")
        print("=" * 50)
        print("Log external trader calls for performance analysis")
        print("Type 'help' for commands, 'quit' to exit")
        print("=" * 50)
    
    def show_help(self):
        """Display help information"""
        print("\n📖 COMMANDS:")
        print("  log     - Log a new trader call")
        print("  recent  - Show recent calls")
        print("  stats   - Show summary statistics")
        print("  trader  - Show calls by specific trader")
        print("  ticker  - Show calls for specific ticker")
        print("  help    - Show this help")
        print("  quit    - Exit the interface")
        print("\n📝 DIRECTIONS: LONG, SHORT, BULLISH, BEARISH, NEUTRAL")
        print("⏰ HORIZONS: DAY_TRADE, SWING, LONG_TERM, UNKNOWN")
    
    def log_call_interactive(self):
        """Interactive call logging"""
        print("\n📝 Log New Trader Call")
        print("-" * 30)
        
        try:
            trader_id = input("Trader ID: ").strip()
            if not trader_id:
                print("❌ Trader ID required")
                return
            
            ticker = input("Ticker (e.g., AAPL): ").strip().upper()
            if not ticker:
                print("❌ Ticker required")
                return
            
            direction = input("Direction (LONG/SHORT/BULLISH/BEARISH): ").strip().upper()
            if direction not in [d.value for d in Direction]:
                print(f"❌ Invalid direction. Use: {[d.value for d in Direction]}")
                return
            
            horizon = input("Horizon (DAY_TRADE/SWING/LONG_TERM): ").strip().upper()
            if horizon not in [h.value for h in Horizon]:
                print(f"⚠️ Invalid horizon. Using UNKNOWN")
                horizon = "UNKNOWN"
            
            entry_price_str = input("Entry Price (optional): ").strip()
            entry_price = None
            if entry_price_str:
                try:
                    entry_price = float(entry_price_str)
                except ValueError:
                    print("⚠️ Invalid price format, skipping entry price")
            
            notes = input("Notes (optional): ").strip()
            if not notes:
                notes = None
            
            # Log the call
            success = self.logger.log_call(
                trader_id=trader_id,
                ticker=ticker,
                direction=direction,
                horizon=horizon,
                entry_price=entry_price,
                notes=notes,
                source="manual_interface"
            )
            
            if success:
                print("✅ Call logged successfully!")
            else:
                print("❌ Failed to log call")
                
        except KeyboardInterrupt:
            print("\n⚠️ Cancelled")
        except Exception as e:
            print(f"❌ Error: {str(e)}")
    
    def show_recent_calls(self):
        """Display recent calls"""
        print("\n📝 Recent Trader Calls")
        print("-" * 30)
        
        try:
            limit = input("How many to show? (default 10): ").strip()
            limit = int(limit) if limit else 10
            
            calls = self.logger.get_recent_calls(limit)
            
            if not calls:
                print("No calls found")
                return
            
            for i, call in enumerate(calls, 1):
                price_str = f" @ ${call.entry_price}" if call.entry_price else ""
                notes_str = f" - {call.notes}" if call.notes else ""
                print(f"{i:2d}. {call.trader_id:15s} {call.direction.value:8s} {call.ticker:6s} ({call.horizon.value:10s}){price_str}{notes_str}")
                
        except ValueError:
            print("❌ Invalid number")
        except Exception as e:
            print(f"❌ Error: {str(e)}")
    
    def show_stats(self):
        """Display summary statistics"""
        print("\n📊 Summary Statistics")
        print("-" * 30)
        
        try:
            stats = self.logger.get_summary_stats()
            
            print(f"Total Calls: {stats['total_calls']}")
            print(f"Unique Traders: {stats['unique_traders']}")
            print(f"Unique Tickers: {stats['unique_tickers']}")
            
            print("\n📈 Direction Breakdown:")
            for direction, count in stats['directions'].items():
                if count > 0:
                    print(f"  {direction}: {count}")
            
            print("\n⏰ Horizon Breakdown:")
            for horizon, count in stats['horizons'].items():
                if count > 0:
                    print(f"  {horizon}: {count}")
            
            if stats['date_range']['earliest']:
                print(f"\n📅 Date Range:")
                print(f"  Earliest: {stats['date_range']['earliest']}")
                print(f"  Latest: {stats['date_range']['latest']}")
                
        except Exception as e:
            print(f"❌ Error: {str(e)}")
    
    def show_trader_calls(self):
        """Show calls by specific trader"""
        print("\n👤 Calls by Trader")
        print("-" * 30)
        
        try:
            trader_id = input("Trader ID: ").strip()
            if not trader_id:
                print("❌ Trader ID required")
                return
            
            calls = self.logger.get_calls_by_trader(trader_id)
            
            if not calls:
                print(f"No calls found for trader: {trader_id}")
                return
            
            print(f"\n📊 {trader_id} - {len(calls)} calls:")
            for i, call in enumerate(calls, 1):
                price_str = f" @ ${call.entry_price}" if call.entry_price else ""
                notes_str = f" - {call.notes}" if call.notes else ""
                print(f"{i:2d}. {call.direction.value:8s} {call.ticker:6s} ({call.horizon.value:10s}) {call.timestamp[:19]}{price_str}{notes_str}")
                
        except Exception as e:
            print(f"❌ Error: {str(e)}")
    
    def show_ticker_calls(self):
        """Show calls for specific ticker"""
        print("\n📈 Calls by Ticker")
        print("-" * 30)
        
        try:
            ticker = input("Ticker: ").strip().upper()
            if not ticker:
                print("❌ Ticker required")
                return
            
            calls = self.logger.get_calls_by_ticker(ticker)
            
            if not calls:
                print(f"No calls found for ticker: {ticker}")
                return
            
            print(f"\n📊 {ticker} - {len(calls)} calls:")
            for i, call in enumerate(calls, 1):
                price_str = f" @ ${call.entry_price}" if call.entry_price else ""
                notes_str = f" - {call.notes}" if call.notes else ""
                print(f"{i:2d}. {call.trader_id:15s} {call.direction.value:8s} ({call.horizon.value:10s}) {call.timestamp[:19]}{price_str}{notes_str}")
                
        except Exception as e:
            print(f"❌ Error: {str(e)}")
    
    def run(self):
        """Run the interactive interface"""
        while True:
            try:
                print("\n" + "=" * 50)
                command = input("🎯 Enter command: ").strip().lower()
                
                if command == 'quit' or command == 'q':
                    print("👋 Goodbye!")
                    break
                elif command == 'help' or command == 'h':
                    self.show_help()
                elif command == 'log' or command == 'l':
                    self.log_call_interactive()
                elif command == 'recent' or command == 'r':
                    self.show_recent_calls()
                elif command == 'stats' or command == 's':
                    self.show_stats()
                elif command == 'trader' or command == 't':
                    self.show_trader_calls()
                elif command == 'ticker':
                    self.show_ticker_calls()
                else:
                    print("❌ Unknown command. Type 'help' for available commands")
                    
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {str(e)}")

def main():
    """Main entry point"""
    interface = TraderCallInterface()
    interface.run()

if __name__ == "__main__":
    main()
