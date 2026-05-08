#!/usr/bin/env python3
"""
Comprehensive Engine Test Suite
Tests all engines for initialization, functionality, and identifies duplicates
"""

import os
import sys
import importlib
import inspect
import time
from typing import Dict, List, Tuple, Any

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

class EngineTester:
    """Test suite for all engines"""
    
    def __init__(self):
        self.results = {}
        self.duplicates = {}
        self.categories = {
            'News Engines': [],
            'Risk Engines': [],
            'Exit Engines': [],
            'Market Analysis': [],
            'Options Engines': [],
            'Utility Engines': [],
            '24/7 Loop Engines': [],
            'Other': []
        }
        
    def categorize_engine(self, filename: str) -> str:
        """Categorize engine by filename"""
        name = filename.lower()
        
        if any(x in name for x in ['news', 'narrative']):
            return 'News Engines'
        elif any(x in name for x in ['risk', 'crash', 'guardian']):
            return 'Risk Engines'
        elif any(x in name for x in ['exit', 'stop', 'target']):
            return 'Exit Engines'
        elif any(x in name for x in ['market', 'scanner', 'regime', 'microstructure']):
            return 'Market Analysis'
        elif any(x in name for x in ['option', 'volatility', 'iv', 'strike']):
            return 'Options Engines'
        elif any(x in name for x in ['calendar', 'seasonality', 'correlation', 'pricing']):
            return 'Utility Engines'
        elif any(x in name for x in ['24_7', 'continuous', 'loop']):
            return '24/7 Loop Engines'
        else:
            return 'Other'
    
    def test_engine_import(self, filepath: str) -> Tuple[bool, str, Any]:
        """Test if engine can be imported and initialized"""
        try:
            # Convert filepath to module name
            module_name = filepath.replace('.py', '').replace('/', '.').replace('\\', '.')
            
            # Import module
            module = importlib.import_module(module_name)
            
            # Find classes
            classes = []
            for name, obj in inspect.getmembers(module, inspect.isclass):
                if obj.__module__ == module_name:
                    classes.append(name)
            
            # Try to initialize main class (usually first one)
            if classes:
                main_class = getattr(module, classes[0])
                
                # Check if it needs config
                sig = inspect.signature(main_class.__init__)
                if 'config' in sig.parameters:
                    instance = main_class({})
                else:
                    instance = main_class()
                    
                return True, f"Successfully initialized {classes[0]}", instance
            else:
                return True, "Module imported (no classes)", None
                
        except Exception as e:
            return False, str(e), None
    
    def test_engine_methods(self, instance: Any) -> Dict[str, bool]:
        """Test key methods of an engine"""
        methods = {}
        
        if not instance:
            return methods
            
        # Common method names to test
        test_methods = [
            'analyze', 'run', 'start', 'update', 'process', 'scan',
            'calculate', 'predict', 'evaluate', 'check', 'monitor'
        ]
        
        for method_name in test_methods:
            if hasattr(instance, method_name):
                method = getattr(instance, method_name)
                if callable(method):
                    try:
                        # Try to call with no args (if possible)
                        sig = inspect.signature(method)
                        if len(sig.parameters) == 0 or any(p.default != inspect.Parameter.empty for p in sig.parameters.values()):
                            method()
                            methods[method_name] = True
                        else:
                            methods[method_name] = None  # Needs args
                    except:
                        methods[method_name] = False
                        
        return methods
    
    def find_duplicates(self) -> Dict[str, List[str]]:
        """Identify engines with similar functionality"""
        duplicates = {}
        
        # Group by keywords
        keyword_groups = {
            'crash': [],
            'news': [],
            'monte_carlo': [],
            'volatility': [],
            'exit': [],
            'risk': [],
            'market': [],
            'scenario': []
        }
        
        for root, dirs, files in os.walk('engines'):
            for file in files:
                if file.endswith('.py') and file != '__init__.py':
                    name = file.lower()
                    for keyword, group in keyword_groups.items():
                        if keyword in name:
                            group.append(file)
                            break
        
        # Find groups with multiple engines
        for keyword, group in keyword_groups.items():
            if len(group) > 1:
                duplicates[keyword] = group
                
        return duplicates
    
    def test_24_7_compatibility(self, filepath: str) -> Dict[str, Any]:
        """Test if engine is suitable for 24/7 operation"""
        results = {
            'has_timeout': False,
            'has_exception_handling': False,
            'memory_safe': True,
            'blocking_operations': []
        }
        
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Check for timeout handling
            if 'timeout' in content.lower():
                results['has_timeout'] = True
            
            # Check for exception handling
            if 'try:' in content and 'except' in content:
                results['has_exception_handling'] = True
            
            # Check for potential blocking operations
            blocking_keywords = ['time.sleep(', 'requests.get(', 'urllib.request', 'socket.']
            for keyword in blocking_keywords:
                if keyword in content:
                    results['blocking_operations'].append(keyword)
            
            # Check for accumulation patterns
            if 'append(' in content and 'clear(' not in content:
                results['memory_safe'] = False
                
        except:
            pass
            
        return results
    
    def run_all_tests(self):
        """Run comprehensive tests on all engines"""
        print("=" * 80)
        print("COMPREHENSIVE ENGINE TEST SUITE")
        print("=" * 80)
        
        # Find all engines
        all_engines = []
        for root, dirs, files in os.walk('engines'):
            for file in files:
                if file.endswith('.py') and file != '__init__.py':
                    filepath = os.path.join(root, file)
                    rel_path = os.path.relpath(filepath, '.')
                    category = self.categorize_engine(file)
                    self.categories[category].append(rel_path)
                    all_engines.append(rel_path)
        
        print(f"\nFound {len(all_engines)} engines to test\n")
        
        # Test each engine
        for engine in all_engines:
            print(f"Testing: {engine}")
            
            # Test import
            success, message, instance = self.test_engine_import(engine)
            
            # Test methods
            methods = {}
            if instance:
                methods = self.test_engine_methods(instance)
            
            # Test 24/7 compatibility
            compatibility = self.test_24_7_compatibility(engine)
            
            # Store results
            self.results[engine] = {
                'import_success': success,
                'message': message,
                'methods': methods,
                'compatibility': compatibility
            }
            
            status = "PASS" if success else "FAIL"
            print(f"  {status} {message}")
            
            # Show methods tested
            if methods:
                tested = [f"{k}({('OK' if v is True else 'ARGS' if v is None else 'FAIL')})" 
                         for k, v in methods.items() if v is not None]
                if tested:
                    print(f"  Methods: {', '.join(tested)}")
            
            # Show compatibility issues
            if compatibility['blocking_operations']:
                print(f"  WARNING Blocking operations: {', '.join(compatibility['blocking_operations'])}")
            if not compatibility['memory_safe']:
                print(f"  WARNING Potential memory leak")
            
            print()
        
        # Find duplicates
        self.duplicates = self.find_duplicates()
        
        # Generate report
        self.generate_report()
    
    def generate_report(self):
        """Generate comprehensive test report"""
        print("=" * 80)
        print("TEST REPORT")
        print("=" * 80)
        
        # Summary by category
        print("\nSUMMARY BY CATEGORY:")
        for category, engines in self.categories.items():
            if engines:
                passed = sum(1 for e in engines if self.results.get(e, {}).get('import_success'))
                print(f"\n{category}:")
                print(f"  Total: {len(engines)}, Passed: {passed}, Failed: {len(engines) - passed}")
                
                # Show failed engines
                failed = [e for e in engines if not self.results.get(e, {}).get('import_success')]
                for f in failed:
                    print(f"    FAIL {f}: {self.results.get(f, {}).get('message', 'Unknown error')}")
        
        # Duplicates
        if self.duplicates:
            print(f"\nPOTENTIAL DUPLICATES:")
            for keyword, engines in self.duplicates.items():
                print(f"\n{keyword.upper()} engines ({len(engines)}):")
                for e in engines:
                    print(f"  - {e}")
                print(f"  Recommendation: Combine into single {keyword} engine")
        
        # 24/7 compatibility issues
        print(f"\n24/7 COMPATIBILITY ISSUES:")
        incompatible = []
        for engine, result in self.results.items():
            if not result['compatibility']['memory_safe'] or result['compatibility']['blocking_operations']:
                incompatible.append(engine)
        
        if incompatible:
            for e in incompatible:
                comp = self.results[e]['compatibility']
                print(f"\n  WARNING {e}:")
                if not comp['memory_safe']:
                    print(f"    - Memory accumulation risk")
                if comp['blocking_operations']:
                    print(f"    - Blocking operations: {', '.join(comp['blocking_operations'])}")
        else:
            print("  All engines appear 24/7 compatible")
        
        # Overall summary
        total = len(self.results)
        passed = sum(1 for r in self.results.values() if r['import_success'])
        
        print(f"\nOVERALL SUMMARY:")
        print(f"  Total engines tested: {total}")
        print(f"  Successfully imported: {passed}")
        print(f"  Failed to import: {total - passed}")
        print(f"  Potential duplicate groups: {len(self.duplicates)}")
        print(f"  24/7 incompatible: {len(incompatible)}")
        
        # Recommendations
        print(f"\nRECOMMENDATIONS:")
        print(f"1. Fix {total - passed} engines that fail to import")
        if self.duplicates:
            print(f"2. Combine {len(self.duplicates)} duplicate engine groups")
        if incompatible:
            print(f"3. Fix {len(incompatible)} engines for 24/7 operation")


def main():
    """Run the comprehensive engine test suite"""
    tester = EngineTester()
    tester.run_all_tests()


if __name__ == "__main__":
    main()
