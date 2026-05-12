"""
Safe Cleanup Script - Identify and remove unused files without breaking imports
"""

import os
import re
import shutil

def get_imported_files():
    """Get all files that are imported in main.py"""
    
    with open('c:/Users/kyran/CascadeProjects/phasma_Ai/main.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find all imports
    imported = set()
    
    # From engines.X import Y
    engine_imports = re.findall(r'from engines\.(\w+)', content)
    imported.update([f"{imp}.py" for imp in engine_imports])
    
    # From utils.X import Y
    utils_imports = re.findall(r'from utils\.(\w+)', content)
    imported.update([f"{imp}.py" for imp in utils_imports])
    
    # From brain.X import Y
    brain_imports = re.findall(r'from brain\.(\w+)', content)
    imported.update([f"{imp}.py" for imp in brain_imports])
    
    # From core.X import Y
    core_imports = re.findall(r'from core\.(\w+)', content)
    imported.update([f"{imp}.py" for imp in core_imports])
    
    # Direct imports
    direct_imports = re.findall(r'import (\w+)', content)
    
    return imported, engine_imports, utils_imports, brain_imports, core_imports

def check_internal_imports(file_path):
    """Check if a file imports other files in the project"""
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except:
        return set()
    
    internal_imports = set()
    
    # Check for imports from engines, utils, brain, core
    patterns = [
        r'from engines\.(\w+)',
        r'from utils\.(\w+)',
        r'from brain\.(\w+)',
        r'from core\.(\w+)'
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, content)
        internal_imports.update(matches)
    
    return internal_imports

def check_file_dependencies():
    """Build a dependency map of all files"""
    
    dependencies = {}
    
    # Check engines
    for file in os.listdir('c:/Users/kyran/CascadeProjects/phasma_Ai/engines'):
        if file.endswith('.py') and file != '__init__.py':
            path = f"c:/Users/kyran/CascadeProjects/phasma_Ai/engines/{file}"
            deps = check_internal_imports(path)
            dependencies[f"engines.{file[:-3]}"] = deps
    
    # Check utils
    for file in os.listdir('c:/Users/kyran/CascadeProjects/phasma_Ai/utils'):
        if file.endswith('.py') and file != '__init__.py':
            path = f"c:/Users/kyran/CascadeProjects/phasma_Ai/utils/{file}"
            deps = check_internal_imports(path)
            dependencies[f"utils.{file[:-3]}"] = deps
    
    # Check brain
    for file in os.listdir('c:/Users/kyran/CascadeProjects/phasma_Ai/brain'):
        if file.endswith('.py') and file != '__init__.py':
            path = f"c:/Users/kyran/CascadeProjects/phasma_Ai/brain/{file}"
            deps = check_internal_imports(path)
            dependencies[f"brain.{file[:-3]}"] = deps
    
    return dependencies

def find_unused_files():
    """Find all unused files"""
    
    print("🔍 Analyzing imports and dependencies...")
    
    # Get directly imported files
    imported, engine_imports, utils_imports, brain_imports, core_imports = get_imported_files()
    
    # Get all dependencies
    dependencies = check_file_dependencies()
    
    # Build set of all required files
    required = set()
    
    # Add directly imported files
    for imp in engine_imports:
        required.add(f"engines.{imp}")
    for imp in utils_imports:
        required.add(f"utils.{imp}")
    for imp in brain_imports:
        required.add(f"brain.{imp}")
    for imp in core_imports:
        required.add(f"core.{imp}")
    
    # Add dependencies
    for file, deps in dependencies.items():
        if file in required:
            for dep in deps:
                if file.startswith('engines.'):
                    required.add(f"engines.{dep}")
                elif file.startswith('utils.'):
                    required.add(f"utils.{dep}")
                elif file.startswith('brain.'):
                    required.add(f"brain.{dep}")
    
    # Find unused files
    unused = {
        'engines': [],
        'utils': [],
        'brain': [],
        'core': []
    }
    
    # Check engines
    for file in os.listdir('c:/Users/kyran/CascadeProjects/phasma_Ai/engines'):
        if file.endswith('.py') and file != '__init__.py':
            module_name = f"engines.{file[:-3]}"
            if module_name not in required:
                unused['engines'].append(file)
    
    # Check utils
    for file in os.listdir('c:/Users/kyran/CascadeProjects/phasma_Ai/utils'):
        if file.endswith('.py') and file != '__init__.py':
            module_name = f"utils.{file[:-3]}"
            if module_name not in required:
                unused['utils'].append(file)
    
    # Check brain
    for file in os.listdir('c:/Users/kyran/CascadeProjects/phasma_Ai/brain'):
        if file.endswith('.py') and file != '__init__.py':
            module_name = f"brain.{file[:-3]}"
            if module_name not in required:
                unused['brain'].append(file)
    
    # Check core
    for file in os.listdir('c:/Users/kyran/CascadeProjects/phasma_Ai/core'):
        if file.endswith('.py') and file != '__init__.py':
            module_name = f"core.{file[:-3]}"
            if module_name not in required:
                unused['core'].append(file)
    
    return required, unused

def move_unused_files(unused):
    """Move unused files to archive/unused_engines"""
    
    print("\n📦 Moving unused files to archive...")
    
    moved = 0
    
    for category, files in unused.items():
        if files:
            print(f"\n{category.upper()} ({len(files)} files):")
            for file in files:
                src = f"c:/Users/kyran/CascadeProjects/phasma_Ai/{category}/{file}"
                dst = f"c:/Users/kyran/CascadeProjects/phasma_Ai/archive/unused_engines/{category}_{file}"
                
                try:
                    shutil.move(src, dst)
                    print(f"  ✅ Moved {file}")
                    moved += 1
                except Exception as e:
                    print(f"  ❌ Error moving {file}: {e}")
    
    print(f"\n🎉 Total files moved: {moved}")
    return moved

def main():
    """Main cleanup function"""
    
    print("🧹 Phasma AI Safe Cleanup Tool")
    print("=" * 50)
    
    # Find unused files
    required, unused = find_unused_files()
    
    print("\n📊 ANALYSIS RESULTS:")
    print(f"\n✅ Required files: {len(required)}")
    for req in sorted(required):
        print(f"  - {req}")
    
    print(f"\n❌ Unused files:")
    total_unused = 0
    for category, files in unused.items():
        if files:
            print(f"  {category}: {len(files)} files")
            total_unused += len(files)
    
    print(f"\nTotal unused: {total_unused} files")
    
    # Ask for confirmation
    response = input("\n🤔 Do you want to move these unused files to archive? (y/n): ")
    
    if response.lower() == 'y':
        moved = move_unused_files(unused)
        print(f"\n✅ Cleanup complete! Moved {moved} files to archive/unused_engines/")
        print("\n⚠️  IMPORTANT: Test the system with 'python main.py' to ensure nothing broke!")
    else:
        print("\n❌ Cleanup cancelled. No files were moved.")

if __name__ == "__main__":
    main()
