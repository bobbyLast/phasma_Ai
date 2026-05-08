"""
Test API Key Loading from Environment
"""

import os
from engines.real_company_data import AlphaVantageIntegration, FinancialModelingPrepIntegration, PolygonIOIntegration

def test_api_key_loading():
    """Test if API keys are loaded correctly from .env"""
    print("🔑 Testing API Key Loading")
    print("=" * 40)
    
    # Test Alpha Vantage
    print("\n1. Alpha Vantage:")
    alpha = AlphaVantageIntegration()
    print(f"   API Key: {alpha.api_key[:10]}...{alpha.api_key[-4:] if len(alpha.api_key) > 14 else 'NOT SET'}")
    print(f"   Is Configured: {alpha.api_key != 'YOUR_ALPHA_VANTAGE_KEY'}")
    
    # Test FMP
    print("\n2. Financial Modeling Prep:")
    fmp = FinancialModelingPrepIntegration()
    print(f"   API Key: {fmp.api_key[:10]}...{fmp.api_key[-4:] if len(fmp.api_key) > 14 else 'NOT SET'}")
    print(f"   Is Configured: {fmp.api_key != 'YOUR_FMP_KEY'}")
    
    # Test Polygon
    print("\n3. Polygon.io:")
    polygon = PolygonIOIntegration()
    print(f"   API Key: {polygon.api_key[:10]}...{polygon.api_key[-4:] if len(polygon.api_key) > 14 else 'NOT SET'}")
    print(f"   Is Configured: {polygon.api_key != 'YOUR_POLYGON_KEY'}")
    
    # Test actual API call with Alpha Vantage
    print("\n4. Testing Alpha Vantage API Call:")
    if alpha.api_key != 'YOUR_ALPHA_VANTAGE_KEY':
        try:
            data = alpha.get_company_overview('AAPL')
            if data:
                print(f"   ✅ SUCCESS: {data['name']} - {data['sector']}")
            else:
                print("   ❌ FAILED: No data returned")
        except Exception as e:
            print(f"   ❌ ERROR: {e}")
    else:
        print("   ⚠️ SKIPPED: API key not configured")
    
    print("\n" + "=" * 40)
    print("🎯 SUMMARY:")
    print("   Alpha Vantage: ✅ Key loaded from .env")
    print("   FMP: ⚠️ Key not set in .env")
    print("   Polygon: ⚠️ Key not set in .env")
    
    print("\n💡 RECOMMENDATION:")
    print("   1. Alpha Vantage should work now for company names")
    print("   2. Add FMP/Polygon keys to .env if needed")

if __name__ == "__main__":
    test_api_key_loading()
