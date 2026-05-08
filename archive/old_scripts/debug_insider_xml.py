import requests
import re
import xml.etree.ElementTree as ET
from utils.insider_monitor import InsiderMonitor

# Get first entry to debug
config = {"insider_monitor": {"enabled": True}}
monitor = InsiderMonitor(config)

# Fetch SEC data
url = "https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent&CIK=&type=4&company=&dateb=&owner=include&count=100&output=atom"
headers = {"User-Agent": "PhasmaAI/InsiderMonitor (https://sec.gov)"}
resp = requests.get(url, headers=headers, timeout=30)

# Parse and get first entry
root = ET.fromstring(resp.text)
entry = root.findall("{http://www.w3.org/2005/Atom}entry")[0]
title = entry.find("{http://www.w3.org/2005/Atom}title").text
link = entry.find("{http://www.w3.org/2005/Atom}link").get("href")

print(f"Debugging entry: {title}")
print(f"Link: {link}")

# Fetch the index page
print("\n=== Fetching index page ===")
index_resp = requests.get(link, headers=headers, timeout=10)
print(f"Index page status: {index_resp.status_code}")

# Look for XML links
xml_matches = re.findall(r'href="([^"]*\.xml)"', index_resp.text)
print(f"\nFound {len(xml_matches)} XML links:")
for m in xml_matches[:5]:
    print(f"  - {m}")

# Look for document table
if "document-table" in index_resp.text:
    print("\nFound document-table")
    
# Try to find the primary document
primary_match = re.search(r'primary_doc\.xml', index_resp.text)
if primary_match:
    print("Found primary_doc.xml reference")

# Show first 1000 chars of index page
print(f"\nFirst 1000 chars of index page:")
print(index_resp.text[:1000])
