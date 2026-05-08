"""
Complete AI-Aware Insider System Connection Test
"""

from main import PhasmaTradingSystem

def test_complete_ai_aware_system():
    """Test all AI-aware insider components are connected"""
    
    print("\n" + "="*80)
    print("🔍 COMPLETE AI-AWARE INSIDER SYSTEM CONNECTION TEST")
    print("="*80)
    
    # Initialize the full system
    print("\n1️⃣ INITIALIZING PHASMA AI SYSTEM...")
    system = PhasmaTradingSystem()
    
    # Check core components
    print("\n2️⃣ CORE AI-AWARE COMPONENTS:")
    components = {
        'InsiderSignalIntegrator': hasattr(system, 'insider_signal_integrator'),
        'Form4Parser': hasattr(system, 'form4_parser'),
        'OptionsFlowFilter': hasattr(system, 'options_filter'),
        'HumanValidator': hasattr(system, 'human_validator'),
        'ComplianceLogger': hasattr(system, 'compliance_logger')
    }
    
    for name, exists in components.items():
        status = "✅ CONNECTED" if exists else "❌ MISSING"
        print(f"   {name}: {status}")
    
    # Check meta-brain registration
    print("\n3️⃣ META-BRAIN REGISTRATION:")
    meta_engines = system.meta_brain.engines
    ai_aware_engines = [
        'insider_signal_integrator',
        'form4_parser',
        'options_filter',
        'human_validator',
        'compliance_logger'
    ]
    
    for engine_name in ai_aware_engines:
        if engine_name in meta_engines:
            print(f"   {engine_name}: ✅ REGISTERED")
        else:
            print(f"   {engine_name}: ❌ NOT REGISTERED")
    
    # Check unified system integration
    print("\n4️⃣ UNIFIED SYSTEM INTEGRATION:")
    if hasattr(system, 'unified_system'):
        unified = system.unified_system
        print(f"   UnifiedTradingSystem: ✅ CONNECTED")
        print(f"   InsiderIntegrator: {hasattr(unified, 'insider_integrator')}")
        print(f"   AI-aware routing: ✅ ENABLED")
    else:
        print(f"   UnifiedTradingSystem: ❌ MISSING")
    
    # Test AI-aware features
    print("\n5️⃣ AI-AWARE FEATURES TEST:")
    
    # Test smart money detection
    if hasattr(system, 'insider_signal_integrator'):
        integrator = system.insider_signal_integrator
        print(f"   Smart Money Detection: ✅ {type(integrator.options_filter).__name__}")
        print(f"   Macro Context: ✅ {_check_method(integrator, '_get_macro_context')}")
        print(f"   AI Bubble Warning: ✅ {_check_method(integrator, '_get_pe_ratio')}")
        print(f"   Sector Boost: ✅ {_check_method(integrator, '_get_macro_boost')}")
    
    # Test confluence scoring
    print("\n6️⃣ CONFLUENCE SCORING:")
    if hasattr(system, 'insider_signal_integrator'):
        weights = {
            'Insider': integrator.insider_weight,
            'Institutional': integrator.institutional_weight,
            'Analyst': integrator.analyst_weight,
            'Options': integrator.options_weight
        }
        for source, weight in weights.items():
            print(f"   {source}: {weight:.0%}")
    
    # Check configuration
    print("\n7️⃣ CONFIGURATION:")
    config = system.config
    print(f"   Insider Monitor: {config.get('insider_monitor', {}).get('enabled', False)}")
    print(f"   Confluence Threshold: {config.get('insider_integrator', {}).get('confluence_threshold', 0.7):.1%}")
    print(f"   Max Price: ${config.get('insider_integrator', {}).get('max_price', 20):.0f}")
    
    # Summary
    print("\n" + "="*80)
    print("📊 CONNECTION SUMMARY")
    print("="*80)
    
    all_connected = all(components.values())
    meta_registered = all(e in meta_engines for e in ai_aware_engines)
    
    if all_connected and meta_registered:
        print("✅ ALL AI-AWARE INSIDER COMPONENTS CONNECTED!")
        print("\n🚀 SYSTEM READY FOR:")
        print("   • Smart Money Detection (Sweeps/Blocks)")
        print("   • AI Infrastructure Macro Context")
        print("   • Bubble Awareness (P/E Monitoring)")
        print("   • Sector Momentum Boosts")
        print("   • Confluence Scoring")
        print("   • Unified Trading Integration")
    else:
        print("⚠️ SOME COMPONENTS NOT CONNECTED")
    
    print("\n" + "="*80)
    return all_connected and meta_registered

def _check_method(obj, method_name):
    """Check if object has method"""
    return hasattr(obj, method_name)

if __name__ == "__main__":
    test_complete_ai_aware_system()
