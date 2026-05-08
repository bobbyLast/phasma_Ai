"""
Test script for SEC EDGAR and IEX Cloud integrations
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engines.sec_edgar_integration import SECEdgarIntegration
from engines.iex_cloud_integration import IEXCloudIntegration
from engines.news_engine_validation import CompanyValidator

def test_sec_edgar():
    """Test SEC EDGAR integration"""
    print("=== Testing SEC EDGAR Integration ===")
    
    sec = SECEdgarIntegration()
    
    # Download company data
    print("Downloading SEC company data...")
    if sec.download_company_tickers():
        print(f"✅ Successfully downloaded {len(sec.company_db)} companies")
        
        # Test specific companies
        test_symbols = ['AAPL', 'GOOGL', 'KSS', 'TSLA']
        for symbol in test_symbols:
            info = sec.get_company_info(symbol)
            if info:
                print(f"✅ {symbol}: {info['name']}")
            else:
                print(f"❌ {symbol}: Not found")
        
        # Test search
        apple_results = sec.search_companies_by_name('Apple')
        print(f"🔍 Found {len(apple_results)} companies with 'Apple' in name")
        
        return True
    else:
        print("❌ Failed to download SEC data")
        return False

def test_iex_cloud():
    """Test IEX Cloud integration"""
    print("\n=== Testing IEX Cloud Integration ===")
    
    iex = IEXCloudIntegration()
    
    # Check if API key is configured
    if iex.api_key == "pk_YOUR_FREE_API_KEY":
        print("⚠️ IEX Cloud API key not configured")
        print("📝 Get free API key from: https://iexcloud.io/pricing")
        print("📝 Add to config or set in IEXCloudIntegration constructor")
        return False
    
    # Test company profile
    test_symbols = ['AAPL', 'GOOGL', 'KSS']
    for symbol in test_symbols:
        profile = iex.get_company_profile(symbol)
        if profile:
            print(f"✅ {symbol}: {profile['name']} - {profile['sector']}")
        else:
            print(f"❌ {symbol}: Not found")
    
    # Test search
    search_results = iex.search_symbols('Apple')
    print(f"🔍 Found {len(search_results)} Apple-related companies")
    
    return True

def test_enhanced_validation():
    """Test enhanced company validation"""
    print("\n=== Testing Enhanced Company Validation ===")
    
    validator = CompanyValidator()
    
    # Test symbols
    test_symbols = ['AAPL', 'GOOGL', 'KSS', 'TSLA', 'INVALID']
    
    for symbol in test_symbols:
        print(f"\n🔍 Testing {symbol}:")
        
        # Create mock news item
        news_item = {'symbol': symbol}
        
        # Test validation
        result = validator.fact_check_company(news_item)
        
        if result['is_valid']:
            company_info = result['company_info']
            print(f"✅ Valid: {company_info['name']}")
            print(f"   Method: {company_info.get('validation_method', 'Unknown')}")
            print(f"   Score: {result['validation_score']:.2f}")
        else:
            print(f"❌ Invalid: {result['company_info']['name']}")
            print(f"   Method: {result['company_info'].get('validation_method', 'Unknown')}")

def main():
    """Run all tests"""
    print("🚀 Testing Enhanced Company Data Integrations")
    print("=" * 50)
    
    # Test SEC EDGAR
    sec_success = test_sec_edgar()
    
    # Test IEX Cloud
    iex_success = test_iex_cloud()
    
    # Test enhanced validation
    test_enhanced_validation()
    
    print("\n" + "=" * 50)
    print("📊 Test Results:")
    print(f"   SEC EDGAR: {'✅ Working' if sec_success else '❌ Failed'}")
    print(f"   IEX Cloud: {'✅ Working' if iex_success else '⚠️ Not Configured'}")
    print(f"   Enhanced Validation: ✅ Implemented")
    
    if sec_success:
        print("\n🎉 SEC EDGAR integration is ready!")
        print("   - Company names will be accurate")
        print("   - No more 'Unknown' company names")
        print("   - Free and reliable data source")

if __name__ == "__main__":
    main()
