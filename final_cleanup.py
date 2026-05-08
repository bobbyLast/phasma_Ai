"""
Final cleanup - move remaining unused files
"""

import os
import shutil

def move_remaining_unused():
    """Move the 22 unused files"""
    
    # These engines are actually unused (news_engine_core is used via imports)
    unused_engines = [
        'calendar_seasonality_engine.py',
        'corporate_actions_engine.py',
        'earnings_drift_engine.py',
        'enhanced_weather_research.py',
        'event_structure_engine.py',
        'macro_calendar_engine.py',
        'market_regime.py',
        'microstructure_engine.py',
        'range_barrier_engine.py',
        'risk_engine.py',
        'scenario_graph_engine.py',
        'weather_consistency_engine_new.py'
    ]
    
    # These utils are unused
    unused_utils = [
        'impact_analyzer.py',
        'pe_ratio_analyzer.py'
    ]
    
    moved = 0
    
    print("🚀 Moving unused engines...")
    for engine in unused_engines:
        src = f'engines/{engine}'
        dst = f'archive/unused_engines/engines_{engine}'
        if os.path.exists(src):
            shutil.move(src, dst)
            print(f"  ✅ Moved: {engine}")
            moved += 1
    
    print("\n🛠️ Moving unused utils...")
    for util in unused_utils:
        src = f'utils/{util}'
        dst = f'archive/unused_engines/utils_{util}'
        if os.path.exists(src):
            shutil.move(src, dst)
            print(f"  ✅ Moved: {util}")
            moved += 1
    
    print(f"\n📊 Total moved: {moved} files")
    
    # Check what's left
    print("\n📁 REMAINING FILES:")
    
    engines_left = [f for f in os.listdir('engines') if f.endswith('.py')]
    utils_left = [f for f in os.listdir('utils') if f.endswith('.py')]
    brain_left = [f for f in os.listdir('brain') if f.endswith('.py')]
    core_left = [f for f in os.listdir('core') if f.endswith('.py')]
    
    print(f"\n  🚀 Engines: {len(engines_left)} files")
    print(f"  🛠️ Utils: {len(utils_left)} files")
    print(f"  🧠 Brain: {len(brain_left)} files")
    print(f"  ⚙️ Core: {len(core_left)} files")
    
    total_left = len(engines_left) + len(utils_left) + len(brain_left) + len(core_left)
    print(f"\n  📊 Total remaining: {total_left} files")
    
    return moved

if __name__ == "__main__":
    print("🧹 FINAL CLEANUP")
    print("=" * 50)
    
    moved = move_remaining_unused()
    
    print(f"\n✅ Final cleanup complete!")
    print(f"📊 Moved {moved} more unused files to archive")
    print("\n🎯 System is now optimized with only necessary files!")
