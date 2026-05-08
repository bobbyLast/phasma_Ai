#!/usr/bin/env python3
"""
Comprehensive Codebase Investigation
Analyzes all Python files to identify used/unused code and importance
"""

import os
import ast
import json
from datetime import datetime
from typing import Dict, List, Set, Tuple
import re


class CodebaseInvestigator:
    """Investigates the entire codebase for usage and importance"""
    
    def __init__(self, root_dir: str):
        self.root_dir = root_dir
        self.all_files = []
        self.import_graph = {}  # file -> set of imported modules
        self.usage_graph = {}   # file -> set of files that import it
        self.file_analysis = {}  # file -> detailed analysis
        self.main_entry = "main.py"
        
    def investigate(self) -> Dict:
        """Perform full investigation"""
        print("=" * 80)
        print("PHASMA AI CODEBASE INVESTIGATION")
        print("=" * 80)
        
        # 1. Find all Python files
        self._find_all_files()
        
        # 2. Build import graph
        self._build_import_graph()
        
        # 3. Analyze each file
        self._analyze_all_files()
        
        # 4. Categorize files
        categories = self._categorize_files()
        
        # 5. Generate report
        report = self._generate_report(categories)
        
        return report
    
    def _find_all_files(self):
        """Find all Python files in the codebase"""
        for root, dirs, files in os.walk(self.root_dir):
            # Skip __pycache__ and .git
            dirs[:] = [d for d in dirs if not d.startswith('.') and d != '__pycache__']
            
            for file in files:
                if file.endswith('.py'):
                    full_path = os.path.join(root, file)
                    rel_path = os.path.relpath(full_path, self.root_dir)
                    self.all_files.append(rel_path)
        
        print(f"\n📁 Found {len(self.all_files)} Python files")
    
    def _build_import_graph(self):
        """Build import relationships between files"""
        for file_path in self.all_files:
            self.import_graph[file_path] = set()
            
            try:
                with open(os.path.join(self.root_dir, file_path), 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # Parse AST
                tree = ast.parse(content)
                
                # Find all imports
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            self.import_graph[file_path].add(alias.name)
                    elif isinstance(node, ast.ImportFrom):
                        if node.module:
                            self.import_graph[file_path].add(node.module)
                            
            except Exception as e:
                print(f"⚠️ Could not parse {file_path}: {e}")
        
        # Build reverse graph (who imports what)
        for file_path, imports in self.import_graph.items():
            for imported in imports:
                if imported not in self.usage_graph:
                    self.usage_graph[imported] = set()
                self.usage_graph[imported].add(file_path)
    
    def _analyze_all_files(self):
        """Analyze each file for details"""
        for file_path in self.all_files:
            analysis = self._analyze_file(file_path)
            self.file_analysis[file_path] = analysis
    
    def _analyze_file(self, file_path: str) -> Dict:
        """Analyze a single file"""
        full_path = os.path.join(self.root_dir, file_path)
        
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Basic stats
            lines = content.split('\n')
            code_lines = [l for l in lines if l.strip() and not l.strip().startswith('#')]
            
            # Parse AST
            tree = ast.parse(content)
            
            # Find classes and functions
            classes = []
            functions = []
            
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    classes.append(node.name)
                elif isinstance(node, ast.FunctionDef):
                    functions.append(node.name)
            
            # Check if it's a main entry point
            is_main = file_path == self.main_entry or 'if __name__ == "__main__"' in content
            
            # Check for test files
            is_test = 'test_' in file_path or '_test.py' in file_path
            
            # Check for demo files
            is_demo = 'demo' in file_path.lower() or 'example' in file_path.lower()
            
            # Check imports from this project
            local_imports = set()
            for imp in self.import_graph.get(file_path, []):
                if any(imp.startswith(prefix) for prefix in ['core', 'engines', 'utils']):
                    local_imports.add(imp)
            
            # Check if imported by others
            imported_by = set()
            base_name = file_path.replace('.py', '').replace('/', '.').replace('\\', '.')
            for importer, imports in self.import_graph.items():
                if base_name in imports or file_path.replace('.py', '') in imports:
                    imported_by.add(importer)
            
            return {
                'size_lines': len(lines),
                'code_lines': len(code_lines),
                'classes': classes,
                'functions': functions,
                'is_main': is_main,
                'is_test': is_test,
                'is_demo': is_demo,
                'local_imports': local_imports,
                'imported_by': imported_by,
                'last_modified': datetime.fromtimestamp(os.path.getmtime(full_path)).isoformat()
            }
            
        except Exception as e:
            return {
                'error': str(e),
                'size_lines': 0,
                'code_lines': 0,
                'classes': [],
                'functions': [],
                'is_main': False,
                'is_test': False,
                'is_demo': False,
                'local_imports': set(),
                'imported_by': set(),
                'last_modified': None
            }
    
    def _categorize_files(self) -> Dict:
        """Categorize files based on usage and importance"""
        categories = {
            'core_active': [],      # Used by main and actively imported
            'core_support': [],     # Core utilities imported by core files
            'engines': [],          # Trading engines
            'utils': [],            # Utility modules
            'tests': [],            # Test files
            'demos': [],            # Demo/example files
            'unused': [],           # Not imported by anything
            'standalone': []        # Standalone scripts
        }
        
        # Identify main entry point
        main_file = self.main_entry
        if main_file in self.file_analysis:
            categories['core_active'].append(main_file)
        
        # Categorize based on analysis
        for file_path, analysis in self.file_analysis.items():
            if 'error' in analysis:
                continue
                
            if file_path == main_file:
                continue
                
            # Check category
            if analysis['is_test']:
                categories['tests'].append(file_path)
            elif analysis['is_demo']:
                categories['demos'].append(file_path)
            elif file_path.startswith('engines/'):
                categories['engines'].append(file_path)
            elif file_path.startswith('utils/'):
                categories['utils'].append(file_path)
            elif file_path.startswith('core/'):
                if analysis['imported_by']:
                    categories['core_active'].append(file_path)
                else:
                    categories['core_support'].append(file_path)
            else:
                # Root level files
                if analysis['imported_by']:
                    categories['core_active'].append(file_path)
                elif analysis['is_main'] or 'if __name__ == "__main__"' in open(os.path.join(self.root_dir, file_path)).read():
                    categories['standalone'].append(file_path)
                else:
                    categories['unused'].append(file_path)
        
        return categories
    
    def _generate_report(self, categories: Dict) -> Dict:
        """Generate comprehensive report"""
        print("\n" + "=" * 80)
        print("INVESTIGATION RESULTS")
        print("=" * 80)
        
        # Summary
        print("\n📊 SUMMARY:")
        print(f"   Total Files: {len(self.all_files)}")
        for category, files in categories.items():
            print(f"   {category.replace('_', ' ').title()}: {len(files)}")
        
        # Detailed analysis
        report = {
            'summary': {cat: len(files) for cat, files in categories.items()},
            'categories': {},
            'recommendations': []
        }
        
        # Analyze each category
        for category, files in categories.items():
            print(f"\n{category.upper().replace('_', ' ')}:")
            report['categories'][category] = []
            
            for file_path in sorted(files):
                analysis = self.file_analysis.get(file_path, {})
                
                if 'error' in analysis:
                    print(f"   ❌ {file_path} - ERROR: {analysis['error']}")
                    continue
                
                # Status indicator
                if category == 'core_active':
                    status = "🔥"
                elif category == 'engines':
                    status = "⚙️"
                elif category == 'utils':
                    status = "🛠️"
                elif category == 'unused':
                    status = "❌"
                elif category == 'demos':
                    status = "🎭"
                elif category == 'tests':
                    status = "🧪"
                else:
                    status = "📄"
                
                print(f"   {status} {file_path}")
                print(f"      Lines: {analysis['size_lines']} (Code: {analysis['code_lines']})")
                
                if analysis['classes']:
                    print(f"      Classes: {', '.join(analysis['classes'][:5])}")
                    if len(analysis['classes']) > 5:
                        print(f"        ... and {len(analysis['classes']) - 5} more")
                
                if analysis['functions']:
                    print(f"      Functions: {', '.join(analysis['functions'][:5])}")
                    if len(analysis['functions']) > 5:
                        print(f"        ... and {len(analysis['functions']) - 5} more")
                
                if analysis['imported_by']:
                    print(f"      Used by: {len(analysis['imported_by'])} file(s)")
                
                # Add to report
                report['categories'][category].append({
                    'file': file_path,
                    'lines': analysis['size_lines'],
                    'code_lines': analysis['code_lines'],
                    'classes': analysis['classes'],
                    'functions': analysis['functions'],
                    'used_by': len(analysis['imported_by'])
                })
        
        # Generate recommendations
        print("\n📋 RECOMMENDATIONS:")
        
        # Check for unused files
        if categories['unused']:
            print(f"\n   ⚠️ {len(categories['unused'])} UNUSED FILES:")
            for file_path in categories['unused']:
                analysis = self.file_analysis.get(file_path, {})
                print(f"      - {file_path} ({analysis['size_lines']} lines)")
            report['recommendations'].append(f"Consider removing {len(categories['unused'])} unused files")
        
        # Check for old demos
        old_demos = []
        for file_path in categories['demos']:
            analysis = self.file_analysis.get(file_path, {})
            if analysis['last_modified']:
                modified = datetime.fromisoformat(analysis['last_modified'])
                if (datetime.now() - modified).days > 30:
                    old_demos.append(file_path)
        
        if old_demos:
            print(f"\n   🎭 {len(old_demos)} OLD DEMO FILES (>30 days):")
            for file_path in old_demos:
                print(f"      - {file_path}")
            report['recommendations'].append(f"Archive or remove {len(old_demos)} old demo files")
        
        # Check for large files
        large_files = []
        for file_path, analysis in self.file_analysis.items():
            if analysis.get('code_lines', 0) > 1000:
                large_files.append((file_path, analysis['code_lines']))
        
        if large_files:
            print(f"\n   📏 {len(large_files)} LARGE FILES (>1000 lines):")
            for file_path, lines in sorted(large_files, key=lambda x: x[1], reverse=True):
                print(f"      - {file_path} ({lines} lines)")
            report['recommendations'].append(f"Consider refactoring {len(large_files)} large files")
        
        # Save detailed report
        report_file = os.path.join(self.root_dir, 'codebase_investigation_report.json')
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n📄 Detailed report saved to: {report_file}")
        
        return report


def main():
    """Run the investigation"""
    investigator = CodebaseInvestigator(os.path.dirname(os.path.abspath(__file__)))
    report = investigator.investigate()
    return report


if __name__ == "__main__":
    main()
