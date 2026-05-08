"""
Root Files Cleanup Script
Safely removes unnecessary files from root directory
"""

import os
import shutil
import json

def create_cleanup_folders():
    """Create folders for organizing files"""
    
    folders = [
        'archive/root_docs',
        'archive/analysis_results',
        'archive/old_scripts',
        'archive/backup_files',
        'archive/logs',
        'archive/outputs'
    ]
    
    for folder in folders:
        os.makedirs(folder, exist_ok=True)
        print(f"✅ Created folder: {folder}")

def cleanup_logs():
    """Move log files to archive"""
    
    log_files = [
        'phasma_trading.log',
        'main_output.log',
        'phasma.log',
        'integration_test.log',
        'test_government_contracts.log',
        'stock_debug.log',
        'phasma_monitor.log'
    ]
    
    moved = 0
    for log in log_files:
        if os.path.exists(log):
            shutil.move(log, f'archive/logs/{log}')
            print(f"  ✅ Moved log: {log}")
            moved += 1
    
    print(f"\n📊 Moved {moved} log files")
    return moved

def cleanup_test_debug():
    """Move test and debug scripts"""
    
    patterns = [
        'check_*.py',
        'debug_*.py',
        'verify_*.py',
        'demo_*.py',
        'simple_test.py'
    ]
    
    import glob
    moved = 0
    
    for pattern in patterns:
        for file in glob.glob(pattern):
            shutil.move(file, f'archive/old_scripts/{file}')
            print(f"  ✅ Moved script: {file}")
            moved += 1
    
    print(f"\n📊 Moved {moved} test/debug scripts")
    return moved

def cleanup_outputs():
    """Move output files"""
    
    outputs = [
        'output.txt',
        'full_output.txt',
        'temp_output.txt',
        'last_run_output.txt',
        'complete_output.txt',
        'test_output.txt'
    ]
    
    moved = 0
    for output in outputs:
        if os.path.exists(output):
            shutil.move(output, f'archive/outputs/{output}')
            print(f"  ✅ Moved output: {output}")
            moved += 1
    
    print(f"\n📊 Moved {moved} output files")
    return moved

def delete_empty_files():
    """Delete empty files"""
    
    empty_files = [
        'check_recent_trades.py',
        'check_sofi_price.py',
        'debug_sec_edgar.py',
        'unified_main.py',
        'ultimate_easy_trade_detector.py',
        'ultimate_easy_trade_detector_all_categories.py',
        'verify_bankroll_limits.py'
    ]
    
    deleted = 0
    for file in empty_files:
        if os.path.exists(file):
            os.remove(file)
            print(f"  🗑️  Deleted empty: {file}")
            deleted += 1
    
    print(f"\n📊 Deleted {deleted} empty files")
    return deleted

def archive_documentation():
    """Move documentation files"""
    
    import glob
    
    # Move markdown docs
    doc_patterns = [
        '*_COMPLETE.md',
        '*_SUMMARY.md',
        'SYSTEM_*.md',
        '*_GUIDE.md',
        'WHY_*.md',
        'MONITORING_*.md',
        'WAVES_*.md',
        'USAGE_*.md',
        'STRUCTURE_*.md'
    ]
    
    moved = 0
    for pattern in doc_patterns:
        for file in glob.glob(pattern):
            if os.path.exists(file):
                shutil.move(file, f'archive/root_docs/{file}')
                print(f"  ✅ Moved doc: {file}")
                moved += 1
    
    print(f"\n📊 Moved {moved} documentation files")
    return moved

def archive_analysis_results():
    """Move analysis result files"""
    
    import glob
    
    result_patterns = [
        '*_results.json',
        '*_analyses.json',
        '*_brain_results.json',
        'engine_test_results.json',
        'top_10_dashboard.json',
        'volatility_edge_*.json'
    ]
    
    moved = 0
    for pattern in result_patterns:
        for file in glob.glob(pattern):
            if os.path.exists(file):
                shutil.move(file, f'archive/analysis_results/{file}')
                print(f"  ✅ Moved analysis: {file}")
                moved += 1
    
    print(f"\n📊 Moved {moved} analysis files")
    return moved

def archive_old_scripts():
    """Move old utility scripts"""
    
    old_scripts = [
        'analyze_archived_engines.py',
        'analyze_usage.py',
        'codebase_investigation.py',
        'find_real_trades.py',
        'fix_stock_signals.py',
        'enhance_kalshi_multi_choice.py',
        'enhance_weather_research.py',
        'early_investment_system.py',
        'plug_ai_analysis.py',
        'restrict_kalshi_weather.py',
        'schedule_insider_monitor.py',
        'show_insider.py',
        'kalshi_multi_choice_summary.py',
        'kalshi_weather_summary.py',
        'weather_research_summary.py'
    ]
    
    moved = 0
    for script in old_scripts:
        if os.path.exists(script):
            shutil.move(script, f'archive/old_scripts/{script}')
            print(f"  ✅ Moved script: {script}")
            moved += 1
    
    print(f"\n📊 Moved {moved} old scripts")
    return moved

def archive_temp_data():
    """Move temporary data files"""
    
    temp_files = [
        'archived_engines_list.txt',
        'bankroll_monitor.json',
        'calibration_adjustments.json',
        'causal_graph.json',
        'counterfactual_scenarios.json',
        'daily_trading_report.txt',
        'daily_unified_report.txt',
        'earnings_analyses.json',
        'emergency_kill_switch_*.json',
        'geopolitical_analyses.json',
        'insider_filing_cache.txt',
        'insider_full_output.txt',
        'macro_analyses.json',
        'pattern_analysis_*.json',
        'prediction_records.json',
        'progression_explanation.txt',
        'risk_guardian_state.json',
        'sample_form4.xml',
        'scenario_graph.json',
        'sec_raw_response.txt',
        'structure_analyses.json',
        'trade_history_*.json',
        'weather_analyses.json',
        'ultimate_options_analysis.json',
        'unified_main_results.json'
    ]
    
    import glob
    moved = 0
    
    for pattern in temp_files:
        for file in glob.glob(pattern):
            if os.path.exists(file):
                shutil.move(file, f'archive/backup_files/{file}')
                print(f"  ✅ Moved data: {file}")
                moved += 1
    
    print(f"\n📊 Moved {moved} temp data files")
    return moved

def show_remaining_files():
    """Show what files are left in root"""
    
    print("\n📁 REMAINING FILES IN ROOT:")
    
    essential = ['main.py', 'config.json', 'telegram_bot.py', 'unified_trading_system.py']
    data = ['.env', 'requirements.txt', 'unified_main.db', 'insider_accumulation.db', 'trade_memory.json', 'phasma_state.json']
    utilities = ['monitor.py', 'reset_ai_properly.py', 'reset_portfolio.py', 'clear_tsla_position.py', 'document_trades.py', 'run_with_all_sources.py']
    
    remaining = essential + data + utilities
    
    for file in remaining:
        if os.path.exists(file):
            size = os.path.getsize(file)
            print(f"  ✅ {file} ({size:,} bytes)")

def main():
    """Main cleanup function"""
    
    print("🧹 ROOT FILES CLEANUP")
    print("=" * 50)
    
    # Ask for confirmation
    response = input("\n⚠️  This will move/delete many files from root directory. Continue? (y/n): ")
    
    if response.lower() != 'y':
        print("\n❌ Cleanup cancelled.")
        return
    
    print("\n🚀 Starting cleanup...")
    
    # Create folders
    create_cleanup_folders()
    
    # Clean up categories
    total_moved = 0
    total_moved += cleanup_logs()
    total_moved += cleanup_test_debug()
    total_moved += cleanup_outputs()
    total_moved += delete_empty_files()
    total_moved += archive_documentation()
    total_moved += archive_analysis_results()
    total_moved += archive_old_scripts()
    total_moved += archive_temp_data()
    
    # Show remaining files
    show_remaining_files()
    
    print(f"\n✅ Cleanup complete!")
    print(f"📊 Total files moved/deleted: {total_moved}")
    print("\n🎯 Root directory is now clean and organized!")

if __name__ == "__main__":
    main()
