"""
Test AI Finding New Stocks - Simulate Real Trading Flow
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engines.news_engine_validation import CompanyValidator

def test_ai_finding_stocks():
    """Test what happens when AI finds new stocks during trading"""
    print("🤖 Testing AI Finding New Stocks")
    print("=" * 50)
    
    # Initialize validator
    validator = CompanyValidator()
    
    # Simulate AI finding various stocks from news/social sources
    ai_found_stocks = [
        {'symbol': 'AAPL', 'title': 'Apple announces new iPhone features', 'source': 'news'},
        {'symbol': 'KSS', 'title': 'Kohl reports strong holiday sales', 'source': 'news'},
        {'symbol': 'TSLA', 'title': 'Tesla deliveries beat expectations', 'source': 'social'},
        {'symbol': 'NVDA', 'title': 'NVIDIA AI chip demand surges', 'source': 'news'},
        {'symbol': 'GME', 'title': 'GameStop meme stock activity spikes', 'source': 'social'},
        {'symbol': 'PLTR', 'title': 'Palantir secures government contract', 'source': 'news'},
        {'symbol': 'AMC', 'title': 'AMC Entertainment announces new theater openings', 'source': 'social'},
        {'symbol': 'BB', 'title': 'BlackBerry software update released', 'source': 'news'},
    ]
    
    print("\n🔍 Simulating AI finding stocks in real-time:")
    
    for i, stock_item in enumerate(ai_found_stocks, 1):
        symbol = stock_item['symbol']
        source = stock_item['source']
        title = stock_item['title'][:40] + "..."
        
        print(f"\n{i}. 🤖 AI found {symbol} from {source}")
        print(f"   📰 Headline: {title}")
        
        # This is what happens in main.py line 4712
        fact_check = validator.fact_check_company(stock_item)
        
        if fact_check.get('is_valid', False):
            company_info = fact_check.get('company_info', {})
            company_name = company_info.get('name') or company_info.get('full_name') or symbol
            sector = company_info.get('sector', 'Unknown')
            method = company_info.get('validation_method', 'unknown')
            
            print(f"   ✅ VALID: {company_name}")
            print(f"   📈 Sector: {sector}")
            print(f"   🔧 Validated by: {method}")
            
            # Simulate signal creation (like main.py line 5098)
            signal = {
                'symbol': symbol,
                'action': 'BUY',
                'confidence': 0.75,
                'fact_check': fact_check,
                'source': 'UNIFIED_ANALYSIS'
            }
            
            # Simulate Telegram bot company name extraction (like telegram_bot.py line 296)
            telegram_company_name = signal.get('fact_check', {}).get('company_info', {}).get('name') or signal.get('fact_check', {}).get('company_info', {}).get('full_name') or symbol
            
            print(f"   📱 Telegram will show: {telegram_company_name}")
            
            if telegram_company_name == symbol:
                print(f"   ❌ PROBLEM: Still showing symbol instead of name!")
            else:
                print(f"   ✅ SUCCESS: Full company name will be displayed!")
                
        else:
            print(f"   ❌ INVALID: Not a real company")
            print(f"   🚫 This stock would be filtered out")
    
    print("\n" + "=" * 50)
    print("🎯 ANALYSIS:")
    
    # Count validation methods
    validation_methods = {}
    successful_validations = 0
    
    for stock_item in ai_found_stocks:
        fact_check = validator.fact_check_company(stock_item)
        if fact_check.get('is_valid', False):
            successful_validations += 1
            method = fact_check.get('company_info', {}).get('validation_method', 'unknown')
            validation_methods[method] = validation_methods.get(method, 0) + 1
    
    print(f"📊 Validation Success Rate: {successful_validations}/{len(ai_found_stocks)} ({successful_validations/len(ai_found_stocks)*100:.1f}%)")
    print("📊 Validation Sources Used:")
    for method, count in validation_methods.items():
        print(f"   {method}: {count} stocks")
    
    print("\n💡 CONCLUSION:")
    if successful_validations == len(ai_found_stocks):
        print("✅ ALL stocks found by AI will have proper company names!")
        print("✅ No more 'Unknown' or symbol-only names in Telegram!")
    else:
        print("⚠️ Some stocks still need better validation")
        print("🔧 Consider adding more API keys or improving fallback database")

if __name__ == "__main__":
    test_ai_finding_stocks()
