#!/usr/bin/env python3
"""
PHASMA AI - Preflight Health Check Script
Ensures system is ready before starting trading cycles
"""

import os
import sys
import logging
from datetime import datetime
from typing import Dict, List, Tuple

def check_environment_variables() -> Tuple[bool, List[str]]:
    """Check required environment variables"""
    print("\n🔍 Checking Environment Variables...")
    
    # Required API keys for production system
    required_keys = [
        "ALPACA_API_KEY",
        "ALPACA_SECRET_KEY", 
        "FINNHUB_API_KEY",
        "FRED_API_KEY"
    ]
    
    # Optional but recommended
    optional_keys = [
        "ALPHA_VANTAGE_API_KEY",
        "POLYGON_API_KEY",
        "IEX_API_KEY"
    ]
    
    status = True
    issues = []
    
    # Check required keys
    for key in required_keys:
        value = os.getenv(key)
        if not value or value == "YOUR_KEY_HERE" or value == "...":
            print(f"  ❌ MISSING REQUIRED: {key}")
            status = False
            issues.append(f"Missing required environment variable: {key}")
        else:
            # Mask the key for security
            masked = value[:4] + "*" * (len(value) - 8) + value[-4:] if len(value) > 8 else "****"
            print(f"  ✅ {key}: {masked}")
    
    # Check optional keys
    for key in optional_keys:
        value = os.getenv(key)
        if not value or value == "YOUR_KEY_HERE" or value == "...":
            print(f"  ⚠️  OPTIONAL MISSING: {key}")
        else:
            masked = value[:4] + "*" * (len(value) - 8) + value[-4:] if len(value) > 8 else "****"
            print(f"  ✅ {key}: {masked}")
    
    return status, issues

def check_dependencies() -> Tuple[bool, List[str]]:
    """Check required Python packages"""
    print("\n📦 Checking Dependencies...")
    
    required_packages = [
        ("yfinance", "yfinance"),
        ("pandas", "pandas"),
        ("numpy", "numpy"),
        ("requests", "requests"),
        ("aiohttp", "aiohttp"),
        ("alpaca_trade_api", "alpaca-trade-api")
    ]
    
    status = True
    issues = []
    
    for package_name, import_name in required_packages:
        try:
            __import__(import_name)
            print(f"  ✅ {package_name} installed")
        except ImportError:
            print(f"  ❌ CRITICAL: {package_name} not installed")
            status = False
            issues.append(f"Missing required package: {package_name}")
    
    return status, issues

def check_data_sources() -> Tuple[bool, List[str]]:
    """Test connectivity to data sources"""
    print("\n🌐 Testing Data Source Connectivity...")
    
    status = True
    issues = []
    
    # Test market data provider bridge
    try:
        import yfinance as market_data
        ticker = market_data.Ticker("AAPL")
        info = ticker.info
        if info and 'currentPrice' in info:
            print(f"  ✅ Provider bridge: Connected (AAPL: ${info['currentPrice']})")
        else:
            print(f"  ⚠️  Provider bridge: Connected but limited data")
    except Exception as e:
        print(f"  ❌ Provider bridge: {str(e)[:50]}...")
        status = False
        issues.append(f"Provider bridge connectivity failed: {e}")
    
    # Test Finnhub if key available
    finnhub_key = os.getenv("FINNHUB_API_KEY")
    if finnhub_key and finnhub_key != "...":
        try:
            import requests
            url = f"https://finnhub.io/api/v1/quote?symbol=AAPL&token={finnhub_key}"
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                print(f"  ✅ Finnhub API: Connected")
            else:
                print(f"  ❌ Finnhub API: HTTP {response.status_code}")
                status = False
                issues.append(f"Finnhub API returned status {response.status_code}")
        except Exception as e:
            print(f"  ❌ Finnhub API: {str(e)[:50]}...")
            status = False
            issues.append(f"Finnhub connectivity failed: {e}")
    
    # Test FRED if key available
    fred_key = os.getenv("FRED_API_KEY")
    if fred_key and fred_key != "...":
        try:
            import requests
            url = f"https://api.stlouisfed.org/fred/series/observations?series_id=GDP&api_key={fred_key}&limit=1"
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                print(f"  ✅ FRED API: Connected")
            else:
                print(f"  ❌ FRED API: HTTP {response.status_code}")
                status = False
                issues.append(f"FRED API returned status {response.status_code}")
        except Exception as e:
            print(f"  ❌ FRED API: {str(e)[:50]}...")
            status = False
            issues.append(f"FRED connectivity failed: {e}")
    
    return status, issues

def check_system_resources() -> Tuple[bool, List[str]]:
    """Check system resources and configuration"""
    print("\n💻 Checking System Resources...")
    
    status = True
    issues = []
    
    # Check Python version
    python_version = sys.version_info
    if python_version.major == 3 and python_version.minor >= 8:
        print(f"  ✅ Python: {python_version.major}.{python_version.minor}.{python_version.micro}")
    else:
        print(f"  ❌ Python: {python_version.major}.{python_version.minor}.{python_version.micro} (need 3.8+)")
        status = False
        issues.append(f"Python version too old: {python_version}")
    
    # Check available memory
    try:
        import psutil
        memory = psutil.virtual_memory()
        available_gb = memory.available / (1024**3)
        if available_gb > 1:
            print(f"  ✅ Available Memory: {available_gb:.1f} GB")
        else:
            print(f"  ⚠️  Low Memory: {available_gb:.1f} GB")
            issues.append("Low system memory may affect performance")
    except ImportError:
        print(f"  ⚠️  psutil not installed - cannot check memory")
    
    # Check disk space
    try:
        import shutil
        disk_usage = shutil.disk_usage(".")
        free_gb = disk_usage.free / (1024**3)
        if free_gb > 1:
            print(f"  ✅ Disk Space: {free_gb:.1f} GB free")
        else:
            print(f"  ⚠️  Low Disk Space: {free_gb:.1f} GB free")
            issues.append("Low disk space may affect logging/data storage")
    except Exception as e:
        print(f"  ⚠️  Cannot check disk space: {e}")
    
    return status, issues

def check_configuration() -> Tuple[bool, List[str]]:
    """Check system configuration files"""
    print("\n⚙️  Checking Configuration...")
    
    status = True
    issues = []
    
    # Check for main config
    if os.path.exists("config.json"):
        print(f"  ✅ config.json found")
    elif os.path.exists("core/config.py"):
        print(f"  ✅ core/config.py found")
    else:
        print(f"  ⚠️  No configuration file found")
        issues.append("No configuration file found")
    
    # Check for log directory
    if os.path.exists("logs"):
        print(f"  ✅ logs directory exists")
    else:
        print(f"  ⚠️  Creating logs directory...")
        try:
            os.makedirs("logs", exist_ok=True)
            print(f"  ✅ logs directory created")
        except Exception as e:
            print(f"  ❌ Cannot create logs directory: {e}")
            status = False
            issues.append(f"Cannot create logs directory: {e}")
    
    return status, issues

def run_preflight_check() -> bool:
    """Run complete preflight check"""
    print("=" * 60)
    print("🚀 PHASMA AI - SYSTEM PREFLIGHT CHECK")
    print("=" * 60)
    print(f"Timestamp: {datetime.now().isoformat()}")
    
    all_passed = True
    all_issues = []
    
    # Run all checks
    checks = [
        ("Environment Variables", check_environment_variables),
        ("Dependencies", check_dependencies),
        ("Data Sources", check_data_sources),
        ("System Resources", check_system_resources),
        ("Configuration", check_configuration)
    ]
    
    for check_name, check_func in checks:
        try:
            passed, issues = check_func()
            if not passed:
                all_passed = False
            all_issues.extend(issues)
        except Exception as e:
            print(f"\n❌ {check_name} check failed with error: {e}")
            all_passed = False
            all_issues.append(f"{check_name} check error: {e}")
    
    # Summary
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ ALL CHECKS PASSED - System Ready for Trading")
        print("=" * 60)
        return True
    else:
        print("❌ CHECKS FAILED - Fix Issues Before Trading")
        print("\n📋 Issues to Fix:")
        for issue in all_issues:
            print(f"  • {issue}")
        print("=" * 60)
        return False

if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Run the check
    if not run_preflight_check():
        print("\n⚠️  System health check failed. Fix errors before trading.")
        sys.exit(1)
    else:
        print("\n🎉 System is GO for trading!")
