#!/usr/bin/env python3
"""
Fix hard-coded stock limit in main.py
"""

def fix_stock_limit():
    # Read the file with UTF-8 encoding
    with open('main.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check if the fix is already applied
    if 'max_stock_positions = self.config.get(\'trading.stock_trading.max_positions\', 50)' in content:
        print("✅ SUCCESS: Stock limit is already configurable!")
        print("   Line: max_stock_positions = self.config.get('trading.stock_trading.max_positions', 50)")
        print("   Uses configurable limit from config.json (default: 50)")
        return
    
    # Replace the hard-coded limit
    old_line = 'max_stock_positions = 10'
    new_line = 'max_stock_positions = self.config.get(\'trading.stock_trading.max_positions\', 50)'
    
    if old_line in content:
        content = content.replace(old_line, new_line)
        
        # Write back to file with UTF-8 encoding
        with open('main.py', 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("✅ SUCCESS: Hard-coded stock limit removed!")
        print(f"   Changed: {old_line}")
        print(f"   To: {new_line}")
        print("   Now uses configurable limit from config.json")
    else:
        print("❌ ERROR: Could not find hard-coded stock limit to replace")
        print("   The line 'max_stock_positions = 10' was not found in main.py")

if __name__ == "__main__":
    fix_stock_limit()
