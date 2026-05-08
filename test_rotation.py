"""Test script to demonstrate data source rotation"""

import asyncio
import logging
from utils.multi_source_data_provider import get_multi_source_provider
from utils.free_market_data_sources import FreeMarketDataSources

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

async def test_rotation():
    """Test rotation through data sources"""
    
    print("\n🔄 TESTING DATA SOURCE ROTATION STRATEGY")
    print("=" * 60)
    
    # Test symbols
    symbols = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA']
    
    # Test multi-source provider
    print("\n📊 Testing Multi-Source Provider with Rotation:")
    print("-" * 50)
    
    config = {
        # Add your API keys here or leave as None to test fallback
        'FINNHUB_API_KEY': None,
        'ALPHA_VANTAGE_API_KEY': None,
        'POLYGON_API_KEY': None,
        'IEX_API_KEY': None
    }
    
    async with get_multi_source_provider(config) as provider:
        for i, symbol in enumerate(symbols):
            print(f"\nRequest {i+1}: {symbol}")
            data = await provider.get_price_data(symbol)
            if data:
                print(f"  ✓ {symbol}: ${data.price:.2f} (source: {data.source})")
            else:
                print(f"  ✗ Failed to get {symbol} data")
    
    print("\n\n📊 Testing Free Market Data Sources with Rotation:")
    print("-" * 50)
    
    async with FreeMarketDataSources() as free_provider:
        for i, symbol in enumerate(symbols):
            print(f"\nRequest {i+1}: {symbol}")
            data = await free_provider.get_quote(symbol)
            if data and data.get('price'):
                print(f"  ✓ {symbol}: ${data['price']:.2f} (source: {data['source']})")
            else:
                print(f"  ✗ Failed to get {symbol} data")
    
    print("\n\n✅ ROTATION TEST COMPLETE")
    print("\nKey Benefits:")
    print("• Distributes load across all available sources")
    print("• Reduces risk of hitting rate limits on any single source")
    print("• Automatic fallback if current source fails")
    print("• Each request uses a different source in sequence")

if __name__ == "__main__":
    asyncio.run(test_rotation())
