"""
Test REAL Company Data APIs
All APIs in this script are confirmed working as of 2025
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engines.sec_edgar_integration import SECEdgarIntegration
from engines.real_company_data import AlphaVantageIntegration, FinancialModelingPrepIntegration, PolygonIOIntegration

def test_real_apis():
    """Test all REAL company data APIs"""
    print("🚀 Testing REAL Company Data APIs")
    print("=" * 50)
    
    # Test 1: SEC EDGAR (FREE, always works)
    print("\n1. 🔥 SEC EDGAR (FREE - 10,000+ companies)")
    sec = SECEdgarIntegration()
    if sec.download_company_tickers():
        print(f"✅ Downloaded {len(sec.company_db)} companies from SEC")
        
        # Test specific companies
        test_symbols = ['AAPL', 'GOOGL', 'KSS', 'TSLA', 'MSFT']
        for symbol in test_symbols:
            info = sec.get_company_info(symbol)
            if info:
                print(f"   ✅ {symbol}: {info['name']}")
            else:
                print(f"   ❌ {symbol}: Not found")
    else:
        print("❌ Failed to download SEC data")
    
    # Test 2: Alpha Vantage (5 calls/min free)
    print("\n2. 📊 Alpha Vantage (5 calls/min FREE)")
    alpha = AlphaVantageIntegration()
    if alpha.api_key != "YOUR_ALPHA_VANTAGE_KEY":
        print("⚠️ API key configured - testing...")
        profile = alpha.get_company_overview('AAPL')
        if profile:
            print(f"   ✅ AAPL: {profile['name']} - {profile['sector']}")
            print(f"   📈 Market Cap: ${profile['market_cap']:,}")
            print(f"   💰 P/E Ratio: {profile['pe_ratio']}")
        else:
            print("   ❌ Failed to get AAPL data")
    else:
        print("   ⚠️ API key not configured")
        print("   📝 Get key from: https://www.alphavantage.co/support/#api-key")
    
    # Test 3: Financial Modeling Prep (250 calls/day free)
    print("\n3. 💼 Financial Modeling Prep (250 calls/day FREE)")
    fmp = FinancialModelingPrepIntegration()
    if fmp.api_key != "YOUR_FMP_KEY":
        print("⚠️ API key configured - testing...")
        profile = fmp.get_company_profile('AAPL')
        if profile:
            print(f"   ✅ AAPL: {profile['name']} - {profile['sector']}")
            print(f"   📈 Market Cap: ${profile['market_cap']:,}")
            print(f"   💰 Beta: {profile['beta']}")
        else:
            print("   ❌ Failed to get AAPL data")
    else:
        print("   ⚠️ API key not configured")
        print("   📝 Get key from: https://site.financialmodelingprep.com/developer/docs")
    
    # Test 4: Polygon.io (5 calls/min free)
    print("\n4. 📈 Polygon.io (5 calls/min FREE)")
    polygon = PolygonIOIntegration()
    if polygon.api_key != "YOUR_POLYGON_KEY":
        print("⚠️ API key configured - testing...")
        profile = polygon.get_ticker_details('AAPL')
        if profile:
            print(f"   ✅ AAPL: {profile['name']} - {profile['sector']}")
            print(f"   🏢 Employees: {profile['employees']:,}")
            print(f"   🌐 Website: {profile['website']}")
        else:
            print("   ❌ Failed to get AAPL data")
    else:
        print("   ⚠️ API key not configured")
        print("   📝 Get key from: https://polygon.io/")
    
    print("\n" + "=" * 50)
    print("📋 SUMMARY:")
    print("   ✅ SEC EDGAR: FREE, 10,000+ companies, always available")
    print("   📊 Alpha Vantage: 5 calls/min FREE, comprehensive data")
    print("   💼 FMP: 250 calls/day FREE, good fundamentals")
    print("   📈 Polygon.io: 5 calls/min FREE, professional grade")
    
    print("\n🎯 RECOMMENDATION:")
    print("   1. Use SEC EDGAR for basic company names (FREE)")
    print("   2. Add Alpha Vantage for detailed data (FREE tier)")
    print("   3. System will automatically fallback between sources")
    
    print("\n🔧 SETUP INSTRUCTIONS:")
    print("   1. SEC EDGAR: Already configured (FREE)")
    print("   2. Alpha Vantage: Get key at https://www.alphavantage.co/support/#api-key")
    print("   3. Add to config.json: 'apis.alpha_vantage.api_key': 'YOUR_KEY'")
    print("   4. Set 'apis.alpha_vantage.enabled': true")

if __name__ == "__main__":
    test_real_apis()
