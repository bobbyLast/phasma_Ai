"""
Debug Form 4 parsing in detail
"""

import requests
import re
from dateutil.parser import parse

def debug_form4():
    """Debug a specific Form 4 filing"""
    
    # Use a recent filing URL
    filing_url = "https://www.sec.gov/Archives/edgar/data/1064299/0001185533-25-000018.txt"
    
    session = requests.Session()
    session.headers.update({
        "User-Agent": "PhasmaAI Test (https://sec.gov)"
    })
    
    print("🔍 Debugging Form 4 parsing...")
    print(f"URL: {filing_url}")
    
    # Fetch the filing
    response = session.get(filing_url, timeout=10)
    if response.status_code != 200:
        print(f"Error: {response.status_code}")
        return
    
    text = response.text
    
    print(f"\nFiling length: {len(text)} characters")
    
    # Look for transaction tables
    print("\n📋 Looking for transaction tables...")
    
    lines = text.split('\n')
    
    # Find Table I (non-derivative transactions)
    in_table = False
    transaction_count = 0
    
    for i, line in enumerate(lines):
        # Look for table start
        if 'Table I' in line and 'Non-Derivative' in line:
            print(f"\nFound Table I at line {i}")
            in_table = True
            continue
        
        if in_table and 'Table II' in line:
            print("End of Table I")
            break
        
        if not in_table:
            continue
        
        # Print first 50 lines of the table
        if transaction_count < 50:
            print(f"{i:4d}: {line}")
        
        transaction_count += 1
        
        # Stop after reasonable amount
        if transaction_count > 100:
            break
    
    print(f"\nTotal lines in table area: {transaction_count}")
    
    # Look for specific patterns
    print("\n🔍 Searching for transaction codes...")
    
    # Find all lines with transaction codes
    code_patterns = re.findall(r'\n(\d{4}-\d{2}-\d{2}\s+[A-Z]\s+.*)', text)
    print(f"Found {len(code_patterns)} lines with transaction codes")
    
    # Show first few
    for pattern in code_patterns[:5]:
        print(f"  {pattern}")
    
    # Check for purchase codes
    purchases = re.findall(r'\n\d{4}-\d{2}-\d{2}\s+P\s+', text)
    sales = re.findall(r'\n\d{4}-\d{2}-\d{2}\s+S\s+', text)
    
    print(f"\nPurchase transactions (P): {len(purchases)}")
    print(f"Sale transactions (S): {len(sales)}")

if __name__ == "__main__":
    debug_form4()
