#!/usr/bin/env python3
"""
Test geopolitical event analysis directly
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from engines.geopolitical_analyzer import GeopoliticalImpactAnalyzer

def test():
    print("=" * 70)
    print("GEOPOLITICAL EVENT ANALYSIS TEST")
    print("=" * 70)
    
    analyzer = GeopoliticalImpactAnalyzer()
    
    demo_events = [
        {
            'title': 'US Military Action in Oil Region',
            'description': 'United States forces secure oil facilities amid escalating tensions in Middle East',
            'source': 'Geopolitical Monitor',
            'relevance': 95
        },
        {
            'title': 'China-US Trade Escalation',
            'description': 'New tariffs announced on semiconductor imports as tech war intensifies',
            'source': 'Trade Monitor',
            'relevance': 92
        },
        {
            'title': 'Russia-Europe Energy Crisis',
            'description': 'Natural gas supply disruptions threaten European industries as winter approaches',
            'source': 'Energy Analysis',
            'relevance': 90
        },
        {
            'title': 'Middle East Conflict Expansion',
            'description': 'Regional tensions rise affecting global shipping routes and oil prices',
            'source': 'Regional Monitor',
            'relevance': 88
        },
        {
            'title': 'Global Supply Chain Disruption',
            'description': 'Major shipping routes affected by Red Sea security concerns and Panama Canal drought',
            'source': 'Trade Monitor',
            'relevance': 85
        },
        {
            'title': 'Cyber Warfare Escalation',
            'description': 'State-sponsored cyber attacks target critical infrastructure across multiple nations',
            'source': 'Security Monitor',
            'relevance': 83
        },
        {
            'title': 'Latin America Political Instability',
            'description': 'Election uncertainty and resource nationalism in key mining regions',
            'source': 'Regional Analysis',
            'relevance': 80
        },
        {
            'title': 'Energy Security Concerns',
            'description': 'Countries reconsider energy dependencies amid conflicts and transition to renewables',
            'source': 'Energy Analysis',
            'relevance': 78
        },
        {
            'title': 'Sanctions Regime Expansion',
            'description': 'New economic sanctions target energy and defense sectors globally',
            'source': 'Policy Monitor',
            'relevance': 76
        },
        {
            'title': 'Rare Earth Supply Chain Risk',
            'description': 'China restricts exports of critical minerals for defense and tech manufacturing',
            'source': 'Resource Monitor',
            'relevance': 74
        },
        {
            'title': 'Currency War Escalation',
            'description': 'Central banks engage in competitive devaluation amid global economic slowdown',
            'source': 'Financial Monitor',
            'relevance': 72
        },
        {
            'title': 'Climate-Related Geopolitics',
            'description': 'Water scarcity and extreme weather drive migration and resource conflicts',
            'source': 'Climate Monitor',
            'relevance': 70
        }
    ]
    
    all_opportunities = []
    
    for i, event in enumerate(demo_events, 1):
        print(f"\n{'=' * 70}")
        print(f"EVENT {i}/{len(demo_events)}: {event['title']}")
        print(f"Relevance: {event['relevance']}")
        print(f"{'=' * 70}")
        
        analysis = analyzer.analyze_event(event['description'])
        
        opportunities = analysis.get('stock_opportunities', [])
        if opportunities:
            print(f"\n✅ Found {len(opportunities)} stock opportunities:")
            for opp in opportunities:
                print(f"  • {opp['symbol']}: ${opp['price']:.2f} | Score: {opp['score']:.0f} | {opp['direction']}")
                all_opportunities.append({
                    'event': event['title'],
                    'symbol': opp['symbol'],
                    'score': opp['score'],
                    'direction': opp['direction']
                })
        else:
            print(f"\n❌ No stock opportunities found")
    
    print(f"\n{'=' * 70}")
    print(f"SUMMARY: {len(all_opportunities)} total opportunities across {len(demo_events)} events")
    print(f"{'=' * 70}")
    
    if all_opportunities:
        print("\nAll opportunities:")
        for opp in all_opportunities:
            print(f"  • {opp['symbol']} ({opp['score']:.0f}%) - {opp['event'][:50]}...")

if __name__ == "__main__":
    test()
