#!/usr/bin/env python3
"""
Demo: Geopolitical Analysis in Main System
Shows how the AI analyzes real events while running
"""

import sys
import os
_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)
from main import PhasmaTradingSystem
from core.config import PhasmaConfig

import asyncio

def demo():
    print("GEOPOLITICAL ANALYSIS DEMO - INTEGRATED WITH MAIN")
    print("=" * 60)
    
    # Initialize system
    config = PhasmaConfig("config.json")
    config.update({
        'geopolitical_analysis': {
            'enabled': True,
            'event_threshold': 70
        },
        'paper_trading': {
            'enabled': True,
            'starting_capital': 10000
        }
    })
    
    system = PhasmaTradingSystem()
    
    # Run a single cycle to show geopolitical analysis
    print("\nRunning analysis cycle...")
    signals = asyncio.run(system.run_full_cycle())
    
    # Show geopolitical signals
    geo_signals = [s for s in signals if s.source in ['geopolitical_analysis', 'Geopolitical Analysis', 'Multi-Platform Analysis', 'multi_platform_scanner']]
    
    if geo_signals:
        print(f"\nGEOPOLITICAL OPPORTUNITIES FOUND:")
        for i, signal in enumerate(geo_signals, 1):
            print(f"{i}. {signal.symbol}")
            print(f"   Action: {signal.action}")
            print(f"   Confidence: {signal.confidence:.0%}")
            print(f"   Reason: {signal.rationale}")
            if hasattr(signal, 'metadata') and signal.metadata:
                print(f"   Event: {signal.metadata.get('event', 'N/A')}")
            print()
    else:
        print("\nNo major geopolitical events detected")
    
    print("\nDemo complete! The AI is monitoring global events...")

if __name__ == "__main__":
    demo()
