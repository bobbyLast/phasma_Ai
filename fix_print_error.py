#!/usr/bin/env python3

# Quick fix for the print statement error
def fix_print_error():
    """Fix the print statement that causes the error"""
    print("🔧 Fixing print statement error...")
    
    try:
        # Read the file
        with open('main.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Fix the problematic print statement
        old_line = 'print(f"   Starting Capital: ${self.paper_portfolio.state[\'starting_capital\']:,.2f}")'
        new_line = 'if hasattr(self, \'paper_portfolio\') and self.paper_portfolio:\n                print(f"   Starting Capital: ${self.paper_portfolio.state[\'starting_capital\']:,.2f}")'
        
        content = content.replace(old_line, new_line)
        
        # Write back
        with open('main.py', 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("✅ Print statement error fixed")
        return True
        
    except Exception as e:
        print(f"❌ Failed to fix: {e}")
        return False

if __name__ == "__main__":
    success = fix_print_error()
    if success:
        print("\n🎯 Now testing the system...")
        import subprocess
        result = subprocess.run(['python', 'main.py', '--learning-only'], capture_output=True, text=True, timeout=30)
        print("STDOUT:")
        print(result.stdout)
        if result.stderr:
            print("STDERR:")
            print(result.stderr)
    else:
        print("\n⚠️ Manual fix needed")
