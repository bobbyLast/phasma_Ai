#!/usr/bin/env python3
"""
Integration script for Unusual Whales with Phasma AI
"""

import asyncio
import json
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def integrate_unusual_whales():
    """Demonstrate Unusual Whales integration"""
    print("🐋 Integrating Unusual Whales with Phasma AI...")
    
    try:
        # Load config
        with open('config.json', 'r') as f:
            config = json.load(f)
        
        # Initialize Unusual Whales engine
        from engines.unusual_whales_engine import UnusualWhalesEngine
        unusual_whales = UnusualWhalesEngine(config)
        
        if not unusual_whales.enabled:
            print("⚠️ Unusual Whales engine is disabled")
            print("To enable, add your API key to config.json:")
            print('"unusual_whales": {')
            print('  "enabled": true,')
            print('  "api_key": "YOUR_UNUSUAL_WHALES_API_KEY",')
            print('  "min_volume_multiplier": 3,')
            print('  "min_confidence": 60')
            print('}')
            return
        
        print("✅ Unusual Whales engine ready")
        
        # Get signals
        signals = await unusual_whales.get_signals()
        
        print(f"\n🎯 Found {len(signals)} unusual activity signals:")
        print("-" * 60)
        
        for signal in signals[:5]:
            print(f"\n📊 {signal['symbol']}")
            print(f"   Action: {signal['action']}")
            print(f"   Confidence: {signal['confidence']:.1%}")
            print(f"   Price: ${signal['entry_price']:.2f}")
            print(f"   Source: Unusual Whales")
            print(f"   Rationale: {signal['rationale']}")
            
            # Show additional details if available
            details = signal.get('details', {})
            if details:
                if 'option_type' in details:
                    print(f"   Option: {details['option_type']} ${details['strike']} ({details['expiration']})")
                if 'volume_multiplier' in details:
                    print(f"   Volume: {details['volume_multiplier']:.1f}x normal")
                if 'flow_type' in details:
                    print(f"   Flow Type: {details['flow_type']}")
        
        print("\n" + "=" * 60)
        print("🔗 INTEGRATION COMPLETE")
        print("=" * 60)
        print("\nThe Unusual Whales engine is now integrated into Phasma AI!")
        print("\nFeatures:")
        print("• Tracks unusual options activity (3x+ normal volume)")
        print("• Monitors institutional block trades ($10M+)")
        print("• Generates high-confidence trading signals")
        print("• Works alongside existing news and social signals")
        
        print("\nTo see it in action, run: python main.py")
        print("The system will now include Unusual Whales signals in its analysis.")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(integrate_unusual_whales())
