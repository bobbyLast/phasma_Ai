"""
Test Underground Discovery Debug Output
Shows exactly why no signals are being generated
"""

from main import PhasmaTradingSystem

def test_debug_output():
    """Run underground discovery to see debug output"""
    
    print("\n" + "="*80)
    print("🔍 TESTING UNDERGROUND DISCOVERY DEBUG OUTPUT")
    print("="*80)
    
    # Initialize system
    system = PhasmaTradingSystem()
    
    if not system.underground_discovery:
        print("❌ Underground discovery not enabled in config")
        return
    
    # Run the scan to see debug output
    opportunities = system.underground_discovery.scan_for_opportunities()
    
    print("\n" + "="*80)
    print("📊 DEBUG SUMMARY")
    print("="*80)
    
    print("\n✅ Debug output shows:")
    print("• Which feeds are checked")
    print("• What thresholds are applied")
    print("• Why each feed returns no data")
    print("• Exact requirements for signals")
    
    print("\n📝 NEXT STEPS:")
    print("1. Connect SEC EDGAR API for Form 4/8-K filings")
    print("2. Implement RSS parser for niche news sources")
    print("3. Add options flow data vendor")
    print("4. Build job posting scraper")
    print("5. Test with real data feeds")

if __name__ == "__main__":
    test_debug_output()
