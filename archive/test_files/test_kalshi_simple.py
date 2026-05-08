"""Simple test to verify Kalshi AI Playbook is working"""

from core.config import PhasmaConfig
from engines.kalshi_engine import KalshiPredictionEngine

def test_simple():
    config = PhasmaConfig()
    print("🔧 Testing Simple Kalshi Integration")
    print("=" * 60)
    
    # Check config
    print(f"kalshi_enabled: {config.get('kalshi_enabled')}")
    print(f"trading_mode: {config.get('trading_mode')}")
    
    # Initialize engine
    try:
        kalshi = KalshiPredictionEngine(config)
        print("✅ Kalshi engine initialized")
        
        # Test with AI Playbook
        print("\n🤖 Testing with AI Playbook...")
        opportunities = kalshi.scan_all_markets(
            min_volume=50,
            max_markets=20,
            use_playbook=True
        )
        
        print(f"Found {len(opportunities)} opportunities")
        
        if opportunities:
            for opp in opportunities[:3]:
                print(f"\n- {opp['market']['ticker']}")
                print(f"  Title: {opp['market']['title'][:60]}...")
                if opp.get('playbook_opportunity'):
                    print(f"  EV: {opp.get('ev', 0):.1%}")
                    print(f"  Signal: {opp['analysis']['signal']}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_simple()
