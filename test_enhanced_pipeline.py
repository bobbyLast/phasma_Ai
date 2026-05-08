"""
Test the enhanced SEC Form 4 pipeline with aggregation audit and diagnostics
"""

from engines.underground_stock_discovery import UndergroundStockDiscovery
import json

def test_enhanced_pipeline():
    """Test the new aggregation and diagnostic features"""
    
    # Initialize with penny moonshot strategy
    config = {
        'underground_discovery': {
            'strategy': 'penny_moonshot',
            'min_market_cap': 10_000_000,
            'max_market_cap': 500_000_000,
            'min_adv': 50_000
        }
    }
    
    discovery = UndergroundStockDiscovery(config)
    
    print("🔍 TESTING ENHANCED SEC PIPELINE")
    print("=" * 60)
    
    # Run scan
    signals = discovery.scan_for_opportunities()
    
    # Show diagnostics
    print("\n📊 COMPREHENSIVE DIAGNOSTICS:")
    print("=" * 60)
    
    diagnostics = discovery.get_diagnostics()
    print(json.dumps(diagnostics, indent=2))
    
    # Test aggregation audit for a sample ticker
    print("\n🔎 AGGREGATION AUDIT EXAMPLE:")
    print("=" * 60)
    
    # Pick first ticker with activity
    if discovery.recent_transactions:
        sample_ticker = list(discovery.recent_transactions.keys())[0]
        audit = discovery.get_aggregation_audit(sample_ticker)
        print(json.dumps(audit, indent=2))
    
    # Test fallback sensitivity
    print("\n⚠️  FALLBACK SENSITIVITY CHECK:")
    print("=" * 60)
    
    borderline = discovery.check_fallback_sensitivity()
    if borderline:
        print(f"Found {len(borderline)} borderline candidates for human review")
        for candidate in borderline[:3]:
            print(f"  - {candidate['ticker']}: {candidate['reason']}")
    else:
        print("No borderline candidates - normal thresholds active")
    
    print("\n✅ Pipeline test complete!")

if __name__ == "__main__":
    test_enhanced_pipeline()
