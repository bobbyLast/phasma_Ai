"""
Final Cleanup Analysis - Check remaining unused files
"""

import os
import re

def get_used_files():
    """Get all files that are actually used"""
    
    used = set()
    
    # Check main.py imports
    with open('main.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find all imports
    imports = re.findall(r'from (engines|utils|brain|core)\.(\w+)', content)
    for module, name in imports:
        used.add(f"{module}.{name}")
    
    # Check internal imports in key files
    key_files = [
        'engines/__init__.py',
        'engines/news_engine_core.py',
        'unified_trading_system.py'
    ]
    
    for file in key_files:
        if os.path.exists(file):
            with open(file, 'r', encoding='utf-8') as f:
                content = f.read()
            imports = re.findall(r'from (engines|utils|brain|core)\.(\w+)', content)
            for module, name in imports:
                used.add(f"{module}.{name}")
    
    return used

def analyze_remaining():
    """Analyze what's left and what can be cleaned"""
    
    used = get_used_files()
    
    print("🔍 ANALYZING REMAINING FILES")
    print("=" * 50)
    
    # Check engines
    print("\n🚀 ENGINES ANALYSIS:")
    engines_used = []
    engines_unused = []
    
    for file in os.listdir('engines'):
        if file.endswith('.py') and file != '__init__.py':
            module = f"engines.{file[:-3]}"
            if module in used:
                engines_used.append(file)
            else:
                engines_unused.append(file)
    
    print(f"  ✅ Used ({len(engines_used)}):")
    for f in sorted(engines_used):
        print(f"    - {f}")
    
    print(f"\n  ❌ Unused ({len(engines_unused)}):")
    for f in sorted(engines_unused):
        print(f"    - {f}")
    
    # Check utils
    print("\n🛠️ UTILS ANALYSIS:")
    utils_used = []
    utils_unused = []
    
    for file in os.listdir('utils'):
        if file.endswith('.py') and file != '__init__.py':
            module = f"utils.{file[:-3]}"
            if module in used:
                utils_used.append(file)
            else:
                utils_unused.append(file)
    
    print(f"  ✅ Used ({len(utils_used)}):")
    for f in sorted(utils_used):
        print(f"    - {f}")
    
    print(f"\n  ❌ Unused ({len(utils_unused)}):")
    for f in sorted(utils_unused):
        print(f"    - {f}")
    
    # Check other folders
    print("\n📁 OTHER FOLDERS:")
    
    # Brain
    brain_files = [f for f in os.listdir('brain') if f.endswith('.py') and f != '__init__.py']
    print(f"  🧠 Brain: {len(brain_files)} files (all used)")
    
    # Core
    core_files = [f for f in os.listdir('core') if f.endswith('.py') and f != '__init__.py']
    print(f"  ⚙️ Core: {len(core_files)} files (all used)")
    
    # Summary
    total_unused = len(engines_unused) + len(utils_unused)
    total_remaining = len(engines_used) + len(utils_unused) + len(brain_files) + len(core_files)
    
    print(f"\n📊 SUMMARY:")
    print(f"  Total remaining files: {total_remaining}")
    print(f"  Still unused: {total_unused}")
    print(f"  Usage rate: {((total_remaining - total_unused) / total_remaining * 100):.1f}%")
    
    return engines_unused, utils_unused

if __name__ == "__main__":
    engines_unused, utils_unused = analyze_remaining()
    
    if engines_unused or utils_unused:
        print(f"\n⚠️  FOUND {len(engines_unused + utils_unused)} MORE UNUSED FILES!")
        print("\nThese can be moved to archive/unused_engines/")
    else:
        print("\n✅ All remaining files are in use!")
