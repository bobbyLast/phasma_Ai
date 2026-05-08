#!/usr/bin/env python3
"""
Test if upgrades are ready for main
"""

import sys
sys.path.append('.')

def test_integration():
    """Test if all upgrades are properly integrated"""
    
    print("🔍 CHECKING UPGRADE INTEGRATION")
    print("=" * 50)
    
    checks = []
    
    # 1. Check risk validation in main
    try:
        with open('main.py', 'r') as f:
            main_content = f.read()
            if 'validate_risk_first' in main_content and 'is_valid, risk_msg = self.validate_risk_first' in main_content:
                print("✅ Risk-first validation: INTEGRATED")
                checks.append(True)
            else:
                print("❌ Risk-first validation: NOT integrated")
                checks.append(False)
    except:
        print("❌ Could not check main.py")
        checks.append(False)
    
    # 2. Check confluence scorer in unified brain
    try:
        with open('unified_meta_brain.py', 'r') as f:
            brain_content = f.read()
            if 'from engines.enhanced_confluence_scorer import' in brain_content and 'confluence_score' in brain_content:
                print("✅ Confluence scoring: INTEGRATED")
                checks.append(True)
            else:
                print("❌ Confluence scoring: NOT integrated")
                checks.append(False)
    except:
        print("❌ Could not check unified_meta_brain.py")
        checks.append(False)
    
    # 3. Check confluence in telegram messages
    try:
        with open('telegram_bot.py', 'r') as f:
            telegram_content = f.read()
            if 'confluence_score' in telegram_content and 'HIGH CONVICTION' in telegram_content:
                print("✅ Telegram confluence badges: INTEGRATED")
                checks.append(True)
            else:
                print("❌ Telegram confluence badges: NOT integrated")
                checks.append(False)
    except:
        print("❌ Could not check telegram_bot.py")
        checks.append(False)
    
    # 4. Check config for three-mind
    try:
        import json
        with open('config.json', 'r') as f:
            config = json.load(f)
            if config.get('trading', {}).get('three_mind_enabled', False):
                print("✅ Three-mind framework: ENABLED (optional)")
                checks.append(True)
            else:
                print("⚠️ Three-mind framework: Disabled (optional)")
                checks.append(True)  # Not required
    except:
        print("⚠️ Could not check config")
        checks.append(True)  # Not required
    
    # Summary
    print("\n" + "=" * 50)
    if all(checks):
        print("🎉 ALL UPGRADES READY FOR MAIN!")
        print("\nWhat you'll get:")
        print("• Risk-first validation on all signals")
        print("• Confluence scoring (70+ threshold)")
        print("• Telegram badges (🏆 HIGH CONVICTION)")
        print("• Enhanced signal quality")
        print("\nRun: python main.py")
    else:
        print("⚠️ Some upgrades not ready")
        print("Check the items marked ❌ above")
    
    return all(checks)

if __name__ == "__main__":
    test_integration()
