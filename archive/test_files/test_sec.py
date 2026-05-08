import requests
import xml.etree.ElementTree as ET

# Test SEC URL
url = "https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent&CIK=&type=4&company=&dateb=&owner=include&count=100&output=atom"

print("Fetching SEC Form 4 data...")
headers = {"User-Agent": "PhasmaAI/InsiderMonitor (https://sec.gov)"}
resp = requests.get(url, headers=headers, timeout=30)

print(f"Status: {resp.status_code}")
print(f"Content-Type: {resp.headers.get('Content-Type', 'N/A')}")
print(f"Content-Length: {len(resp.text)}")

# Save raw response
with open('sec_raw_response.txt', 'w') as f:
    f.write(resp.text)
    print("Saved raw response to sec_raw_response.txt")

# Try to parse XML
try:
    root = ET.fromstring(resp.text)
    print(f"\nRoot tag: {root.tag}")
    print(f"Root attrib: {root.attrib}")
    
    # Find all entries
    entries = root.findall(".//entry")
    print(f"\nFound {len(entries)} entries (no namespace)")
    
    # Try with namespace
    entries_ns = root.findall(".//{http://www.w3.org/2005/Atom}entry")
    print(f"Found {len(entries_ns)} entries (with Atom namespace)")
    
    # Show first 3 entry titles
    for i, entry in enumerate(entries[:3]):
        title = entry.find(".//title")
        if title is not None:
            print(f"\nEntry {i+1}:")
            print(f"  Title: {title.text}")
            
except Exception as e:
    print(f"\nXML parsing error: {e}")
    print(f"First 500 chars of response:\n{resp.text[:500]}")
