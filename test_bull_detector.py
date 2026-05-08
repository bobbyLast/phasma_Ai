"""
Test Bull Run Detector with lower thresholds
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

async def test_bull_detector():
    """Test with lower thresholds to see what's being found"""
    
    from bull_run_detector import BullRunDetector
    from config.secure_config import config
    
    # Initialize detector
    detector = BullRunDetector(config)
    
    # Get all news
    print("📰 Fetching news...")
    all_news = await detector.news_sources.fetch_all_integrated_sources()
    print(f"   Got {len(all_news)} news items")
    
    # Analyze
    print("\n🔍 Analyzing for signals...")
    stock_signals = {}
    
    for item in all_news:
        text = f"{item.get('title', '')} {item.get('summary', '')}".upper()
        symbol = detector._extract_symbol(text)
        
        if not symbol:
            continue
        
        signals = detector._analyze_bull_run_indicators(text)
        
        if signals:
            source_confidence = detector._get_source_confidence(item.get('source', ''))
            
            if symbol not in stock_signals:
                stock_signals[symbol] = {
                    'total_score': 0,
                    'indicators': set(),
                    'sources': [],
                    'evidence': [],
                    'confirmation_count': 0
                }
            
            for indicator_type, strength in signals.items():
                stock_signals[symbol]['indicators'].add(indicator_type)
                stock_signals[symbol]['total_score'] += strength * source_confidence
                stock_signals[symbol]['evidence'].append({
                    'type': indicator_type,
                    'strength': strength,
                    'source': item.get('source', ''),
                    'text': item.get('title', '')[:100] + '...',
                    'confidence': source_confidence
                })
            
            stock_signals[symbol]['sources'].append(item.get('source', ''))
            stock_signals[symbol]['confirmation_count'] = len(set(stock_signals[symbol]['sources']))
    
    print(f"\n📊 Found {len(stock_signals)} stocks with signals:")
    
    # Show all found stocks
    for symbol, data in stock_signals.items():
        print(f"\n• {symbol}")
        print(f"  Score: {data['total_score']:.1f}")
        print(f"  Confirmations: {data['confirmation_count']}")
        print(f"  Indicators: {', '.join(data['indicators'])}")
        print(f"  Sources: {', '.join(set(data['sources']))}")
        
        # Show top evidence
        if data['evidence']:
            print(f"  Top: {data['evidence'][0]['text']}")

if __name__ == "__main__":
    asyncio.run(test_bull_detector())
