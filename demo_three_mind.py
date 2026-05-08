#!/usr/bin/env python3
"""
Demo script for Three-Mind Trading Framework

This script demonstrates the three-mind framework in action,
showing how it generates high-conviction trading signals.
"""

import asyncio
import sys
from datetime import datetime

# Add project root to path
sys.path.append('.')

from brains.three_mind_integration import ThreeMindIntegration
from core.config import PhasmaConfig


async def demo_three_mind():
    """Run three-mind framework demo"""
    
    print("🧠 THREE-MIND TRADING FRAMEWORK DEMO")
    print("=" * 60)
    print("Mind 1: Macro Navigator - Regime awareness")
    print("Mind 2: Value Selector - Fundamental analysis")
    print("Mind 3: Micro Execution - Technical patterns")
    print("=" * 60)
    
    # Initialize
    config = PhasmaConfig()
    integration = ThreeMindIntegration(config)
    
    # Sample market data (would come from real sources)
    market_data = {
        'vix': 18.5,
        'spy_price': 478.50,
        'spy_ma200': 450.00,
        'dxy': 102.5,
        'rate_expectations': 0.45,
        'growth_momentum': 0.6,
        'inflation': 3.2,
        'liquidity': 0.7
    }
    
    # Sample news items (would come from news engine)
    news_items = [
        {
            'title': 'AI Infrastructure Demand Surges as Data Centers Expand',
            'summary': 'Major tech companies increasing investment in AI computing infrastructure',
            'symbol': 'SMCI',
            'sentiment': 0.7
        },
        {
            'title': 'Energy Transition Accelerates with Renewable Power Investments',
            'summary': 'Government and private sector pouring money into renewable energy projects',
            'symbol': 'FLNC',
            'sentiment': 0.6
        },
        {
            'title': 'Semiconductor Manufacturing Seeing Reshoring Trend',
            'summary': 'Companies bringing chip manufacturing back to domestic soil',
            'symbol': 'UMC',
            'sentiment': 0.5
        }
    ]
    
    print("\n📊 MARKET CONTEXT:")
    print(f"   VIX: {market_data['vix']} ({'Low' if market_data['vix'] < 20 else 'Elevated'} volatility)")
    print(f"   SPY: ${market_data['spy_price']} ({'Above' if market_data['spy_price'] > market_data['spy_ma200'] else 'Below'} 200-day MA)")
    print(f"   Dollar Index: {market_data['dxy']}")
    print(f"   Rate Expectations: {market_data['rate_expectations']}")
    print(f"   Growth Momentum: {market_data['growth_momentum']:.0%}")
    
    print("\n📰 NEWS THEMES:")
    for item in news_items:
        print(f"   • {item['symbol']}: {item['title'][:50]}...")
    
    # Run three-mind analysis
    print("\n🔍 RUNNING THREE-MIND ANALYSIS...")
    signals = await integration.run_three_mind_analysis(market_data, news_items)
    
    # Display results
    if signals:
        print(f"\n✅ FOUND {len(signals)} HIGH-CONVICTION SIGNALS:")
        print("=" * 60)
        
        for i, signal in enumerate(signals, 1):
            print(f"\n{i}. {signal.symbol} - Confluence: {signal.confluence_score:.0f}/100")
            print(f"   {'='*50}")
            print(f"   Action: {signal.action}")
            print(f"   Entry: ${signal.trade_plan.entry_price:.2f}")
            print(f"   Stop: ${signal.trade_plan.stop_loss:.2f} ({abs(signal.trade_plan.entry_price - signal.trade_plan.stop_loss):.2f} risk)")
            print(f"   Target: ${signal.trade_plan.target_price:.2f} ({signal.trade_plan.target_price - signal.trade_plan.entry_price:.2f} reward)")
            print(f"   R:R Ratio: {signal.trade_plan.target_price - signal.trade_plan.entry_price:.2f}:{abs(signal.trade_plan.entry_price - signal.trade_plan.stop_loss):.2f}")
            print(f"   Position Size: {signal.trade_plan.position_size:.1%} of capital")
            
            print(f"\n   MIND BREAKDOWN:")
            print(f"   🌍 Macro: {signal.macro_alignment.get('score', 0):.0%} - {signal.macro_alignment.get('reasoning', 'N/A')}")
            print(f"   💰 Value: {signal.value_assessment.get('score', 0):.0%} - {signal.value_assessment.get('reasoning', 'N/A')}")
            print(f"   📈 Technical: {signal.technical_setup.get('confidence', 0):.0%} - {signal.technical_setup.get('thesis', 'N/A')}")
            
            print(f"\n   FULL THESIS:")
            for line in signal.reasoning.split('\n'):
                if line.strip():
                    print(f"   {line}")
    else:
        print("\n❌ NO HIGH-CONVICTION SIGNALS FOUND")
        print("   Confluence score threshold of 70 not met")
    
    # Show framework benefits
    print("\n\n🎯 FRAMEWORK BENEFITS:")
    print("=" * 60)
    print("✅ Process over prediction - Rules-based, not emotional")
    print("✅ Risk-first design - Always calculates risk before reward")
    print("✅ Evidence-based - Requires confirmation across all minds")
    print("✅ Regime awareness - Adapts strategy to market conditions")
    print("✅ Margin of safety - Graham-style value protection")
    print("✅ Precise execution - Clear entries, stops, and targets")
    print("✅ Continuous learning - Trade journal for improvement")
    
    print("\n📈 NEXT STEPS:")
    print("1. Monitor signals for execution")
    print("2. Track performance in trade journal")
    print("3. Adjust parameters based on results")
    print("4. Expand universe of analyzed symbols")
    print("5. Add more macro indicators for Mind 1")
    print("6. Enhance value models for Mind 2")
    print("7. Add more patterns for Mind 3")


if __name__ == "__main__":
    asyncio.run(demo_three_mind())
