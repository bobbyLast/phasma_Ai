"""
Simple Silver News Detector
Uses existing APIs to find silver-related news
"""

import re
from typing import List, Dict, Any

def detect_silver_opportunities(news_items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Filter news items for silver-related opportunities"""
    
    silver_keywords = [
        'silver', 'slv', 'silver price', 'silver futures',
        'silver spot', 'ounce silver', 'silver etf',
        'precious metals silver', 'silver market',
        'silver rally', 'silver surge', 'silver jump',
        'silver bullion', 'silver coins', 'silver bars',
        'silver prices rise', 'silver climbs', 'silver soars'
    ]
    
    silver_opportunities = []
    
    for item in news_items:
        # Get text from title and summary
        title = item.get('title', '').lower()
        summary = item.get('summary', '').lower()
        text = f"{title} {summary}"
        
        # Check for silver keywords
        for keyword in silver_keywords:
            if keyword in text:
                # Check for positive movement indicators
                positive_words = ['rise', 'rally', 'surge', 'jump', 'climb', 'soar', 'gain', 'up', 'higher', 'increase']
                
                is_positive = any(word in text for word in positive_words)
                
                if is_positive:
                    # Create silver signal
                    silver_signal = {
                        'symbol': 'SLV',
                        'source': item.get('source', 'news'),
                        'title': item.get('title', ''),
                        'summary': item.get('summary', ''),
                        'confidence': min(90, 60 + len([k for k in silver_keywords if k in text]) * 10),
                        'timestamp': item.get('timestamp', ''),
                        'signal_type': 'SILVER_RALLY',
                        'reason': f'Silver rally detected: {keyword}',
                        'url': item.get('url', ''),
                        'original_item': item
                    }
                    
                    silver_opportunities.append(silver_signal)
                    print(f"🥈 SILVER OPPORTUNITY: {item.get('title', '')[:60]}...")
                    break
    
    return silver_opportunities

def add_silver_detection_to_news_engine(news_engine):
    """Add silver detection to existing news engine"""
    
    # Store original scan method
    original_scan = news_engine.scan_all_sources
    
    async def enhanced_scan_with_silver(symbols=None):
        """Enhanced scan that detects silver opportunities"""
        
        # Get original news
        original_news = await original_scan(symbols)
        
        # Detect silver opportunities
        silver_opportunities = detect_silver_opportunities(original_news)
        
        # Add silver opportunities to the news
        if silver_opportunities:
            print(f"\n🥈 DETECTED {len(silver_opportunities)} SILVER OPPORTUNITIES!")
            original_news.extend(silver_opportunities)
        else:
            print("\n🥈 No silver opportunities detected in current news")
        
        return original_news
    
    # Replace the method
    news_engine.scan_all_sources = enhanced_scan_with_silver
    
    print("✅ Silver opportunity detector added to news engine")
