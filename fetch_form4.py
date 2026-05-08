"""
Fetch and examine a full Form 4 to understand the format
"""

import requests

def fetch_full_form4():
    """Fetch a complete Form 4 to understand structure"""
    
    # URL from debug output
    doc_url = "https://www.sec.gov/Archives/edgar/data/1072796/000107279625000006/0001072796-25-000006.txt"
    
    session = requests.Session()
    session.headers.update({
        "User-Agent": "PhasmaAI Test (https://sec.gov)"
    })
    
    print("🔍 Fetching complete Form 4...")
    
    response = session.get(doc_url, timeout=10)
    if response.status_code != 200:
        print(f"Error: {response.status_code}")
        return
    
    text = response.text
    
    print(f"\nDocument length: {len(text)} characters")
    
    # Print the full document to see structure
    print("\n" + "="*60)
    print("FULL FORM 4 CONTENT:")
    print("="*60)
    print(text)
    print("="*60)

if __name__ == "__main__":
    fetch_full_form4()
