#!/usr/bin/env python3
"""
Paper Trading Performance Dashboard
Shows AI trading performance without real money
"""

import os
import sys
from datetime import datetime

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engines.paper_trading_portfolio import get_paper_trading_portfolio
from core.config import PhasmaConfig

def show_paper_trading_dashboard():
    """Display paper trading performance dashboard"""
    
    # Load config
    config = PhasmaConfig()
    
    # Check if paper trading is enabled
    if not config.get('paper_trading', {}).get('enabled', False):
        print("\n❌ Paper trading is not enabled in config.json")
        print("To enable, add 'paper_trading.enabled': true to your config")
        return
    
    # Get paper trading portfolio
    portfolio = get_paper_trading_portfolio(config)
    
    # Get performance summary
    summary = portfolio.get_portfolio_summary()
    
    # Clear screen
    os.system('cls' if os.name == 'nt' else 'clear')
    
    # Display dashboard
    print("="*70)
    print("🤖 PHASMA AI - PAPER TRADING PERFORMANCE DASHBOARD")
    print("="*70)
    print(f"📅 As of: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Portfolio Value
    print("💰 PORTFOLIO VALUE:")
    print(f"   Starting Capital: ${summary['starting_capital']:,.2f}")
    print(f"   Current Value:    ${summary['total_portfolio_value']:,.2f}")
    print(f"   Total Return:      ${summary['total_return']:+,.2f} ({summary['total_return_pct']:+.2f}%)")
    print()
    
    # P&L Breakdown
    print("📊 P&L BREAKDOWN:")
    print(f"   Available Cash:    ${summary['available_capital']:,.2f}")
    print(f"   Realized P&L:      ${summary['realized_pnl']:,.2f}")
    print(f"   Unrealized P&L:    ${summary['unrealized_pnl']:,.2f}")
    print()
    
    # Trading Statistics
    print("📈 TRADING STATISTICS:")
    print(f"   Total Trades:      {summary['total_trades']}")
    print(f"   Winning Trades:    {summary['winning_trades']}")
    print(f"   Losing Trades:     {summary['losing_trades']}")
    print(f"   Win Rate:          {summary['win_rate']:.1f}%")
    print(f"   Profit Factor:     {summary['profit_factor']:.2f}")
    print(f"   Open Positions:    {summary['open_positions_count']}")
    print()
    
    # AI Performance Analysis
    ai_perf = summary['ai_performance']
    print("🧠 AI PERFORMANCE ANALYSIS:")
    print(f"   Avg Confidence:    {ai_perf['avg_confidence']:.1f}%")
    print(f"   Conf/Return Corr:  {ai_perf['confidence_vs_return_corr']:.2f}")
    print(f"   High Conf Win Rate: {ai_perf['high_confidence_win_rate']:.1f}% (>80% confidence)")
    print(f"   Low Conf Win Rate:  {ai_perf['low_confidence_win_rate']:.1f}% (≤60% confidence)")
    print(f"   Analyzed Trades:   {ai_perf.get('total_analyzed_trades', 0)}")
    print()
    
    # Verification Status
    verification = summary.get('verification', {})
    if verification:
        print("🔍 VERIFICATION STATUS:")
        print(f"   Total Trades:      {verification.get('total_trades', 0)}")
        print(f"   Verified Trades:   {verification.get('verified_trades', 0)}")
        print(f"   Verification Rate: {verification.get('verification_rate', 0):.1%}")
        if verification.get('failed_verifications', 0) > 0:
            print(f"   ⚠️  Failed Verifications: {verification.get('failed_verifications', 0)}")
        print()
    
    # Performance Metrics
    metrics = summary['performance_metrics']
    print("📊 PERFORMANCE METRICS:")
    print(f"   Average Win:       ${metrics['avg_win']:,.2f}")
    print(f"   Average Loss:      ${metrics['avg_loss']:,.2f}")
    print(f"   Largest Win:       ${metrics['largest_win']:,.2f}")
    print(f"   Largest Loss:      ${metrics['largest_loss']:,.2f}")
    print()
    
    # Recent Daily P&L
    print("📅 RECENT DAILY P&L (Last 7 days):")
    recent_daily = summary['daily_pnl'][-7:]
    if recent_daily:
        for day in recent_daily:
            date_str = day['date']
            pnl = day['pnl']
            pnl_str = f"${pnl:,.2f}" if pnl >= 0 else f"-${abs(pnl):,.2f}"
            print(f"   {date_str}: {pnl_str}")
    else:
        print("   No recent activity")
    print()
    
    # Open Positions
    if summary['open_positions']:
        print("📋 OPEN POSITIONS:")
        for pos in summary['open_positions']:
            pnl_str = f"${pos['unrealized_pnl']:,.2f}" if pos['unrealized_pnl'] >= 0 else f"-${abs(pos['unrealized_pnl']):,.2f}"
            pct_str = f"+{pos['unrealized_pct']:.1f}%" if pos['unrealized_pct'] >= 0 else f"{pos['unrealized_pct']:.1f}%"
            print(f"   {pos['symbol']}: {pos['quantity']} shares @ ${pos['avg_cost']:.2f}")
            print(f"      Current: ${pos['current_price']:.2f} | P&L: {pnl_str} ({pct_str}) | Held: {pos['days_held']} days")
        print()
    
    # Recent Trades
    recent_trades = portfolio.get_trade_history(5)
    if recent_trades:
        print("🔄 RECENT TRADES:")
        for trade in recent_trades:
            if trade['action'] == 'SELL':
                pnl = trade['realized_pnl']
                pnl_str = f"${pnl:,.2f}" if pnl >= 0 else f"-${abs(pnl):,.2f}"
                pct = trade.get('realized_pct', 0)
                pct_str = f"+{pct:.1f}%" if pct >= 0 else f"{pct:.1f}%"
                print(f"   {trade['timestamp'][:19]}: {trade['symbol']} {trade['action']} {trade['quantity']} @ ${trade['price']:.2f}")
                print(f"      P&L: {pnl_str} ({pct_str})")
                if trade.get('confidence'):
                    print(f"      AI Confidence: {trade['confidence']:.1f}%")
        print()
    
    # Performance Report
    print(portfolio.get_performance_report())
    
    # Menu
    print("\n" + "="*70)
    print("OPTIONS:")
    print("  [R] Reset Portfolio")
    print("  [T] Trade History")
    print("  [E] Export for Audit")
    print("  [Q] Quit")
    print("="*70)
    
    while True:
        choice = input("\nSelect option: ").upper()
        
        if choice == 'Q':
            break
        elif choice == 'R':
            confirm = input("Reset portfolio? This will clear all data (y/N): ").upper()
            if confirm == 'Y':
                portfolio.reset_portfolio()
                print("Portfolio reset!")
                input("Press Enter to continue...")
                show_paper_trading_dashboard()
                return
        elif choice == 'T':
            print("\n📜 TRADE HISTORY:")
            trades = portfolio.get_trade_history(20)
            for trade in trades:
                if trade['action'] == 'BUY':
                    print(f"  {trade['timestamp'][:19]}: {trade['symbol']} {trade['action']} {trade['quantity']} @ ${trade['price']:.2f}")
                    if trade.get('confidence'):
                        print(f"     AI Confidence: {trade['confidence']:.1f}%")
                else:
                    pnl = trade['realized_pnl']
                    pnl_str = f"${pnl:,.2f}" if pnl >= 0 else f"-${abs(pnl):,.2f}"
                    print(f"  {trade['timestamp'][:19]}: {trade['symbol']} {trade['action']} {trade['quantity']} @ ${trade['price']:.2f} P&L: {pnl_str}")
            input("\nPress Enter to continue...")
            show_paper_trading_dashboard()
            return
        elif choice == 'E':
            print("\n📤 Exporting for Audit...")
            try:
                from engines.paper_trading_verifier import PaperTradingVerifier
                verifier = PaperTradingVerifier()
                filename = verifier.export_for_audit()
                print(f"✅ Exported audit file: {filename}")
                print("   This file contains complete trade history and verification data")
            except Exception as e:
                print(f"❌ Export failed: {e}")
            input("\nPress Enter to continue...")
            show_paper_trading_dashboard()
            return
        else:
            print("Invalid option")

if __name__ == "__main__":
    show_paper_trading_dashboard()
