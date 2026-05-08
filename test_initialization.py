#!/usr/bin/env python3
"""
Test if all required attributes are initialized
"""

import sys
sys.path.append('.')

from main import PhasmaTradingSystem

def test_initialization():
    """Test if all required attributes are initialized"""
    
    print("🔍 Testing PhasmaTradingSystem initialization...")
    
    try:
        # Initialize system
        system = PhasmaTradingSystem()
        print("✅ System initialized")
        
        # Check critical attributes
        critical_attrs = [
            'thematic_analyzer',
            'social_engine',
            'news_engine',
            'meta_brain',
            'telegram_bot'
        ]
        
        print("\n📊 Checking critical attributes:")
        all_good = True
        
        for attr in critical_attrs:
            if hasattr(system, attr):
                value = getattr(system, attr)
                if value is not None:
                    print(f"✅ {attr}: Initialized")
                else:
                    print(f"⚠️ {attr}: None (might be disabled)")
            else:
                print(f"❌ {attr}: MISSING")
                all_good = False
        
        # Test specific methods
        print("\n🔧 Testing methods:")
        
        # Test thematic analyzer
        if hasattr(system, 'thematic_analyzer') and system.thematic_analyzer:
            try:
                result = system.thematic_analyzer.analyze_news_themes([])
                print("✅ thematic_analyzer.analyze_news_themes: Works")
            except Exception as e:
                print(f"❌ thematic_analyzer.analyze_news_themes: {e}")
                all_good = False
        
        # Test social engine
        if hasattr(system, 'social_engine'):
            if system.social_engine is None:
                print("⚠️ social_engine: None (Reddit monitoring disabled)")
            else:
                print("✅ social_engine: Initialized")
        
        return all_good
        
    except Exception as e:
        print(f"❌ Initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_initialization()
    if success:
        print("\n✅ All critical components initialized properly")
    else:
        print("\n⚠️ Some components missing - check above")
