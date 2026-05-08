import requests
import re

# Test what URLs we're actually extracting
url = "https://www.sec.gov/Archives/edgar/data/2040511/000204051125000006/0002040511-25-000006-index.htm"
headers = {"User-Agent": "PhasmaAI/InsiderMonitor (https://sec.gov)"}

resp = requests.get(url, headers=headers, timeout=10)
print(f"Status: {resp.status_code}")

# Find all XML links
xml_matches = re.findall(r'href="([^"]*\.xml)"', resp.text)
print(f"\nFound {len(xml_matches)} XML links:")
for i, m in enumerate(xml_matches):
    print(f"\n{i+1}. {m}")
    
    # Check if it's the actual XML or just HTML
    full_url = f"https://www.sec.gov{m}" if m.startswith('/') else m
    xml_resp = requests.get(full_url, headers=headers, timeout=5)
    
    # Check content type
    print(f"   Content-Type: {xml_resp.headers.get('Content-Type', 'N/A')}")
    print(f"   First 200 chars: {xml_resp.text[:200]}")

# Also look for the actual document table
print("\n\n=== Looking for document table ===")
doc_table_match = re.search(r'<table class="tableFile"[^>]*>(.*?)</table>', resp.text, re.DOTALL)
if doc_table_match:
    print("Found document table")
    # Find rows with .xml
    rows = re.findall(r'<tr>(.*?)</tr>', doc_table_match.group(1), re.DOTALL)
    for row in rows:
        if '.xml' in row:
            print(f"\nRow with XML: {row[:200]}...")
