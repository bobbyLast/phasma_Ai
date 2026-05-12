#!/usr/bin/env python3

# Fix indentation issues in main.py
def fix_indentation():
    """Fix the indentation issues around line 652"""
    print("🔧 Fixing indentation issues...")
    
    try:
        # Read the file
        with open('main.py', 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Find and fix the problematic lines
        for i, line in enumerate(lines):
            if 'self.alpaca_paper_trader = None' in line and i > 640:
                # Check if this line has wrong indentation
                if line.startswith('                    '):  # Too many spaces
                    lines[i] = '            self.alpaca_paper_trader = None\n'
                elif 'self.alpaca_paper_trader = None' in lines[i+1]:  # Duplicate
                    lines[i+1] = ''  # Remove duplicate
        
        # Write back
        with open('main.py', 'w', encoding='utf-8') as f:
            f.writelines(lines)
        
        print("✅ Indentation issues fixed")
        return True
        
    except Exception as e:
        print(f"❌ Failed to fix: {e}")
        return False

if __name__ == "__main__":
    success = fix_indentation()
    if success:
        print("\n🎯 Testing the fix...")
        import subprocess
        result = subprocess.run(['python', 'test_if_works.py'], capture_output=True, text=True)
        print(result.stdout)
        if result.stderr:
            print("Errors:", result.stderr)
    else:
        print("\n⚠️ Manual fix needed")
