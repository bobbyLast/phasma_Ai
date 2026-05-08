#!/usr/bin/env python3
"""
Simple analysis of file usage in the codebase
"""

import os
import re

def get_imports_from_file(filepath):
    """Extract all imports from a Python file"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Find all imports
        imports = set()
        
        # from X import Y
        from_imports = re.findall(r'from ([^\s]+) import', content)
        for imp in from_imports:
            if not imp.startswith('.'):
                imports.add(imp.split('.')[0])
        
        # import X
        direct_imports = re.findall(r'^import ([^\s]+)', content, re.MULTILINE)
        for imp in direct_imports:
            if not imp.startswith('.'):
                imports.add(imp.split('.')[0])
        
        return imports
    except:
        return set()

def main():
    print("=" * 80)
    print("PHASMA AI CODEBASE USAGE ANALYSIS")
    print("=" * 80)
    
    # Get all Python files
    all_files = []
    for root, dirs, files in os.walk('.'):
        dirs[:] = [d for d in dirs if not d.startswith('.') and d != '__pycache__']
        for file in files:
            if file.endswith('.py'):
                all_files.append(os.path.join(root, file))
    
    # Build usage map
    usage_map = {}  # file -> set of files that import it
    file_to_module = {}  # file -> module name
    
    for file in all_files:
        # Determine module name
        rel_path = os.path.relpath(file, '.')
        module = rel_path.replace('.py', '').replace('/', '.').replace('\\', '.')
        file_to_module[file] = module
        usage_map[file] = set()
    
    # Check imports in each file
    for file in all_files:
        imports = get_imports_from_file(file)
        
        for imp in imports:
            # Find files that match this import
            for f, mod in file_to_module.items():
                if mod.endswith(imp) or imp in mod:
                    usage_map[f].add(file)
    
    # Categorize and report
    categories = {
        'CORE (Used by main.py or core files)': [],
        'ACTIVE (Used by multiple files)': [],
        'UTILS (Utility modules)': [],
        'ENGINES (Trading engines)': [],
        'UNUSED (Not imported by any file)': [],
        'DEMOS (Demo files)': [],
        'TESTS (Test files)': [],
        'STANDALONE (Self-contained scripts)': []
    }
    
    # Read main.py imports
    main_imports = get_imports_from_file('main.py') if os.path.exists('main.py') else set()
    
    for file, used_by in usage_map.items():
        rel_path = os.path.relpath(file, '.')
        
        # Skip __init__ files
        if file.endswith('__init__.py'):
            continue
        
        # Determine category
        if rel_path == 'main.py':
            categories['CORE (Used by main.py or core files)'].append((rel_path, used_by))
        elif 'test_' in rel_path or '_test.py' in rel_path:
            categories['TESTS (Test files)'].append((rel_path, used_by))
        elif 'demo' in rel_path.lower():
            categories['DEMOS (Demo files)'].append((rel_path, used_by))
        elif rel_path.startswith('core/'):
            categories['CORE (Used by main.py or core files)'].append((rel_path, used_by))
        elif rel_path.startswith('engines/'):
            categories['ENGINES (Trading engines)'].append((rel_path, used_by))
        elif rel_path.startswith('utils/'):
            categories['UTILS (Utility modules)'].append((rel_path, used_by))
        elif not used_by:
            categories['UNUSED (Not imported by any file)'].append((rel_path, used_by))
        elif len(used_by) == 1 and 'if __name__ == "__main__"' in open(file).read():
            categories['STANDALONE (Self-contained scripts)'].append((rel_path, used_by))
        else:
            categories['ACTIVE (Used by multiple files)'].append((rel_path, used_by))
    
    # Print results
    total_files = sum(len(files) for files in categories.values())
    print(f"\nTotal Python files: {total_files}\n")
    
    for category, files in categories.items():
        if not files:
            continue
            
        print(f"\n{category} ({len(files)} files):")
        print("-" * 60)
        
        for file, used_by in sorted(files):
            # Get file size
            size = os.path.getsize(file) if os.path.exists(file) else 0
            
            # Get line count
            try:
                with open(file, 'r') as f:
                    lines = len(f.readlines())
            except:
                lines = 0
            
            status = ""
            if not used_by:
                status = " ❌ UNUSED"
            elif len(used_by) > 5:
                status = f" 🔥 HIGH USAGE ({len(used_by)} files)"
            elif len(used_by) > 2:
                status = f" ⚡ ACTIVE ({len(used_by)} files)"
            
            print(f"  {file:<50} {lines:>4} lines, {size:>6} bytes{status}")
            
            # Show who uses it (for important files)
            if used_by and len(used_by) <= 5 and category != 'TESTS':
                for user in sorted(used_by):
                    user_rel = os.path.relpath(user, '.')
                    if user_rel != file:
                        print(f"    ← Used by: {user_rel}")
    
    # Summary and recommendations
    print("\n" + "=" * 80)
    print("SUMMARY & RECOMMENDATIONS")
    print("=" * 80)
    
    unused_count = len(categories['UNUSED (Not imported by any file)'])
    demo_count = len(categories['DEMOS (Demo files)'])
    test_count = len(categories['TESTS (Test files)'])
    
    print(f"\n📊 File Distribution:")
    print(f"   Core files: {len(categories['CORE (Used by main.py or core files)'])}")
    print(f"   Engines: {len(categories['ENGINES (Trading engines)'])}")
    print(f"   Utils: {len(categories['UTILS (Utility modules)'])}")
    print(f"   Active: {len(categories['ACTIVE (Used by multiple files)'])}")
    print(f"   Unused: {unused_count}")
    print(f"   Demos: {demo_count}")
    print(f"   Tests: {test_count}")
    print(f"   Standalone: {len(categories['STANDALONE (Self-contained scripts)'])}")
    
    print(f"\n⚠️ Recommendations:")
    
    if unused_count > 0:
        print(f"   1. Remove {unused_count} unused files to clean up codebase")
    
    if demo_count > 3:
        print(f"   2. Archive old demo files (found {demo_count})")
    
    # Find large files
    large_files = []
    for file, used_by in usage_map.items():
        if os.path.exists(file):
            with open(file, 'r') as f:
                lines = len(f.readlines())
                if lines > 500:
                    large_files.append((file, lines))
    
    if large_files:
        print(f"   3. Consider refactoring {len(large_files)} large files (>500 lines)")
        for file, lines in sorted(large_files, key=lambda x: x[1], reverse=True)[:5]:
            print(f"      - {os.path.relpath(file, '.')} ({lines} lines)")
    
    # Check for duplicate functionality
    print(f"\n🔍 Potential Issues:")
    
    # Check for multiple similar engines
    engine_files = [f for f, _ in categories['ENGINES (Trading engines)']]
    crash_detectors = [f for f in engine_files if 'crash' in f.lower()]
    if len(crash_detectors) > 1:
        print(f"   - Found {len(crash_detectors)} crash detector engines")
    
    news_engines = [f for f in engine_files if 'news' in f.lower()]
    if len(news_engines) > 3:
        print(f"   - Found {len(news_engines)} news-related engines")
    
    # Check for old test files
    old_tests = []
    for file, _ in categories['TESTS (Test files)']:
        if os.path.exists(file):
            mtime = os.path.getmtime(file)
            import time
            if time.time() - mtime > 30 * 24 * 60 * 60:  # 30 days
                old_tests.append(file)
    
    if old_tests:
        print(f"   - Found {len(old_tests)} test files not modified in 30+ days")

if __name__ == "__main__":
    main()
