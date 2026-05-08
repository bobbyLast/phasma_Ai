#!/usr/bin/env python3
"""
Test Unusual Whales Engine
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def test_unusual_whales():
    """Test the Unusual Whales engine"""
    print("🐋 Testing Unusual Whales Engine...")
    
    try:
        # Load config
        with open('config.json', 'r') as f:
            config = json.load(f)
        
        # Initialize Unusual Whales engine
        from engines.unusual_whales_engine import UnusualWhalesEngine
        unusual_whales = UnusualWhalesEngine(config)
        
        if not unusual_whales.enabled:
            print("⚠️ Unusual Whales engine is disabled in config")
            return
        
        print("✅ Unusual Whales engine initialized")
        
        # Get unusual options flow
        print("\n📊 Getting unusual options flow...")
        unusual_flows = await unusual_whales.get_unusual_options_flow()
        print(f"Found {len(unusual_flows)} unusual options flows")
        
        for flow in unusual_flows[:3]:
            print(f"\n• {flow.symbol}: {flow.action} {flow.option_type} ${flow.strike}")
            print(f"  Volume: {flow.volume:,} (avg: {flow.volume_avg:,}, {flow.volume/flow.volume_avg:.1f}x)")
            print(f"  Sentiment: {flow.sentiment} | Confidence: {flow.confidence}%")
        
        # Get institutional flow
        print("\n📊 Getting institutional flow...")
        institutional_flows = await unusual_whales.get_institutional_flow()
        print(f"Found {len(institutional_flows)} institutional flows")
        
        for flow in institutional_flows[:3]:
            print(f"\n• {flow['symbol']}: {flow['action']} ${flow['size']:,}")
            print(f"  Type: {flow['type']} | Confidence: {flow['confidence']}%")
        
        # Convert to trading signals
        print("\n🎯 Converting to trading signals...")
        signals = await unusual_whales.get_signals()
        print(f"Generated {len(signals)} trading signals")
        
        for signal in signals[:3]:
            print(f"\n• {signal['symbol']}: {signal['action']} @ ${signal['entry_price']:.2f}")
            print(f"  Confidence: {signal['confidence']:.1%}")
            print(f"  Rationale: {signal['rationale']}")
        
        print("\n✅ Unusual Whales test complete!")
        
    except Exception as e:
        print(f"❌ Error testing Unusual Whales: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    import json
    asyncio.run(test_unusual_whales())
