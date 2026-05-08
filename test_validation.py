"""
Test Company Validation with Real APIs
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engines.news_engine_validation import CompanyValidator

def test_company_validation():
    """Test company validation with real APIs"""
    print("🧪 Testing Company Validation System")
    print("=" * 50)
    
    # Initialize validator with config
    validator = CompanyValidator()
    
    # Test symbols that were problematic before
    test_symbols = ['AAPL', 'GOOGL', 'KSS', 'TSLA', 'MSFT', 'GME', 'NVDA']
    
    print("\n🔍 Testing Company Validation:")
    for symbol in test_symbols:
        print(f"\n📊 Testing {symbol}:")
        
        # Create mock news item
        news_item = {'symbol': symbol}
        
        # Test validation
        result = validator.fact_check_company(news_item)
        
        if result['is_valid']:
            company_info = result['company_info']
            print(f"   ✅ VALID: {company_info['name']}")
            print(f"   📈 Sector: {company_info['sector']}")
            print(f"   🔧 Method: {company_info.get('validation_method', 'Unknown')}")
            print(f"   📊 Score: {result['validation_score']:.2f}")
        else:
            company_info = result['company_info']
            print(f"   ❌ INVALID: {company_info['name']}")
            print(f"   🔧 Method: {company_info.get('validation_method', 'Unknown')}")
    
    print("\n" + "=" * 50)
    print("🎯 SUMMARY:")
    
    # Count validation sources
    validation_methods = {}
    for symbol in test_symbols:
        news_item = {'symbol': symbol}
        result = validator.fact_check_company(news_item)
        method = result['company_info'].get('validation_method', 'unknown')
        validation_methods[method] = validation_methods.get(method, 0) + 1
    
    print("📊 Validation Sources Used:")
    for method, count in validation_methods.items():
        print(f"   {method}: {count} symbols")
    
    print("\n💡 EXPECTED RESULTS:")
    print("   ✅ SEC EDGAR should handle most symbols")
    print("   ✅ Alpha Vantage should handle remaining symbols")
    print("   ✅ No more 'Unknown' company names")
    print("   ✅ Full company names in Telegram messages")

if __name__ == "__main__":
    test_company_validation()
