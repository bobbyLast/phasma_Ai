#!/usr/bin/env python3
"""
Analyze all archived engines to determine their purpose and value
"""

import os
import re

def analyze_file(filepath):
    """Extract key information from a Python file"""
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        # Extract docstring
        docstring = ""
        if '"""' in content:
            parts = content.split('"""')
            if len(parts) > 1:
                docstring = parts[1].strip()
        
        # Extract class names
        classes = re.findall(r'class\s+(\w+)', content)
        
        # Extract function names
        functions = re.findall(r'def\s+(\w+)', content)
        
        # Get file size
        size = os.path.getsize(filepath)
        
        return {
            'docstring': docstring[:200] + "..." if len(docstring) > 200 else docstring,
            'classes': classes[:5],  # Show first 5
            'functions': functions[:5],  # Show first 5
            'size': size
        }
    except:
        return None

def main():
    print("=" * 80)
    print("ARCHIVED ENGINES ANALYSIS")
    print("=" * 80)
    
    archive_dir = "archive"
    engines_dir = "engines"
    
    # Categories for analysis
    categories = {
        'POTENTIALLY VALUABLE': [],
        'CLEAR DUPLICATES': [],
        'EXPERIMENTAL/RESEARCH': [],
        'UTILITY/HELPERS': [],
        'UNCLEAR PURPOSE': []
    }
    
    # List all archived files
    archived_files = []
    for root, dirs, files in os.walk(archive_dir):
        for file in files:
            if file.endswith('.py') and not file.startswith('__'):
                archived_files.append(os.path.join(root, file))
    
    print(f"\nFound {len(archived_files)} archived engines\n")
    
    # Analyze each file
    for filepath in sorted(archived_files):
        rel_path = os.path.relpath(filepath, '.')
        filename = os.path.basename(filepath)
        
        analysis = analyze_file(filepath)
        if not analysis:
            continue
        
        # Determine category based on name and content
        name_lower = filename.lower()
        
        if 'crash_detector' in name_lower:
            categories['CLEAR DUPLICATES'].append((filename, analysis))
        elif any(x in name_lower for x in ['backtest', 'test', 'demo']):
            categories['UTILITY/HELPERS'].append((filename, analysis))
        elif any(x in name_lower for x in ['causal', 'narrative', 'scenario', 'self_calibrating']):
            categories['EXPERIMENTAL/RESEARCH'].append((filename, analysis))
        elif any(x in name_lower for x in ['calendar', 'seasonality', 'earnings', 'corporate']):
            categories['POTENTIALLY VALUABLE'].append((filename, analysis))
        else:
            categories['UNCLEAR PURPOSE'].append((filename, analysis))
    
    # Print analysis
    for category, files in categories.items():
        if not files:
            continue
            
        print(f"\n{category}:")
        print("-" * 60)
        
        for filename, analysis in files:
            print(f"\n📄 {filename}")
            print(f"   Size: {analysis['size']:,} bytes")
            
            if analysis['docstring']:
                print(f"   Purpose: {analysis['docstring']}")
            
            if analysis['classes']:
                print(f"   Classes: {', '.join(analysis['classes'])}")
            
            if analysis['functions']:
                print(f"   Key Functions: {', '.join(analysis['functions'])}")
    
    # Summary and recommendations
    print("\n" + "=" * 80)
    print("SUMMARY & RECOMMENDATIONS")
    print("=" * 80)
    
    for category, files in categories.items():
        if files:
            print(f"\n{category}: {len(files)} files")
    
    print("\nRECOMMENDATIONS:")
    print("\n1. POTENTIALLY VALUABLE - Consider restoring:")
    print("   - These engines add real trading features")
    print("   - Could be integrated into main system")
    
    print("\n2. CLEAR DUPLICATES - Can delete:")
    print("   - Old versions of existing engines")
    
    print("\n3. EXPERIMENTAL/RESEARCH - Keep for future:")
    print("   - Advanced features not ready for production")
    
    print("\n4. UTILITY/HELPERS - Consider restoring:")
    print("   - Useful for testing and development")
    
    print("\n5. UNCLEAR PURPOSE - Need investigation:")
    print("   - Review each to determine value")

if __name__ == "__main__":
    main()
