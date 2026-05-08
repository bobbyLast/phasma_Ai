#!/usr/bin/env python3
"""
Check actual usage of all engines and utilities
"""

import os
import re

def find_all_imports():
    """Find all imports in the codebase"""
    all_imports = set()
    
    for root, dirs, files in os.walk('.'):
        if '__pycache__' in dirs:
            dirs.remove('__pycache__')
        
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                    
                    # Find from imports
                    from_imports = re.findall(r'from ([^\s]+) import', content)
                    for imp in from_imports:
                        if imp.startswith('engines.') or imp.startswith('utils.') or imp.startswith('core.'):
                            all_imports.add(imp)
                    
                    # Find direct imports
                    direct_imports = re.findall(r'^import ([^\s]+)', content, re.MULTILINE)
                    for imp in direct_imports:
                        if imp.startswith('engines.') or imp.startswith('utils.') or imp.startswith('core.'):
                            all_imports.add(imp)
                            
                except:
                    pass
    
    return all_imports

def main():
    print("Checking actual usage of engines and utilities...")
    
    # Find all imports
    all_imports = find_all_imports()
    
    # Get all available modules
    engines = []
    utils = []
    core = []
    
    for root, dirs, files in os.walk('.'):
        if '__pycache__' in dirs:
            dirs.remove('__pycache__')
        
        for file in files:
            if file.endswith('.py') and file != '__init__.py':
                filepath = os.path.relpath(os.path.join(root, file), '.')
                module = filepath.replace('.py', '').replace('/', '.').replace('\\', '.')
                
                if module.startswith('engines.'):
                    engines.append(module)
                elif module.startswith('utils.'):
                    utils.append(module)
                elif module.startswith('core.'):
                    core.append(module)
    
    print("\n=== ENGINES ===")
    print(f"Total engines: {len(engines)}")
    
    used_engines = []
    unused_engines = []
    
    for engine in sorted(engines):
        if engine in all_imports or any(e.startswith(engine + '.') for e in all_imports):
            used_engines.append(engine)
        else:
            unused_engines.append(engine)
    
    print(f"\n✅ USED ENGINES ({len(used_engines)}):")
    for e in used_engines:
        print(f"  - {e}")
    
    print(f"\n❌ UNUSED ENGINES ({len(unused_engines)}):")
    for e in unused_engines:
        print(f"  - {e}")
    
    print("\n=== UTILITIES ===")
    print(f"Total utils: {len(utils)}")
    
    used_utils = []
    unused_utils = []
    
    for util in sorted(utils):
        if util in all_imports or any(u.startswith(util + '.') for u in all_imports):
            used_utils.append(util)
        else:
            unused_utils.append(util)
    
    print(f"\n✅ USED UTILS ({len(used_utils)}):")
    for u in used_utils:
        print(f"  - {u}")
    
    print(f"\n❌ UNUSED UTILS ({len(unused_utils)}):")
    for u in unused_utils:
        print(f"  - {u}")
    
    print("\n=== CORE ===")
    print(f"Total core: {len(core)}")
    
    used_core = []
    unused_core = []
    
    for c in sorted(core):
        if c in all_imports or any(co.startswith(c + '.') for co in all_imports):
            used_core.append(c)
        else:
            unused_core.append(c)
    
    print(f"\n✅ USED CORE ({len(used_core)}):")
    for c in used_core:
        print(f"  - {c}")
    
    print(f"\n❌ UNUSED CORE ({len(unused_core)}):")
    for c in unused_core:
        print(f"  - {c}")
    
    # Summary
    total_used = len(used_engines) + len(used_utils) + len(used_core)
    total_unused = len(unused_engines) + len(unused_utils) + len(unused_core)
    total = total_used + total_unused
    
    print(f"\n=== SUMMARY ===")
    print(f"Total modules: {total}")
    print(f"Used: {total_used} ({total_used/total*100:.1f}%)")
    print(f"Unused: {total_unused} ({total_unused/total*100:.1f}%)")
    
    # List files that can be deleted
    print(f"\n=== FILES SAFE TO DELETE ===")
    all_unused = unused_engines + unused_utils + unused_core
    for module in all_unused:
        filepath = module.replace('.', '/') + '.py'
        if os.path.exists(filepath):
            print(f"  - {filepath}")

if __name__ == "__main__":
    main()
