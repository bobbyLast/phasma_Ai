import requests

# Test one of the XML URLs found
xml_url = "https://www.sec.gov/Archives/edgar/data/1577526/000204051125000006/form4-12182025_021240.xml"
headers = {"User-Agent": "PhasmaAI/InsiderMonitor (https://sec.gov)"}

print(f"Fetching: {xml_url}")
resp = requests.get(xml_url, headers=headers, timeout=10)
print(f"Status: {resp.status_code}")
print(f"Content-Type: {resp.headers.get('Content-Type', 'N/A')}")
print(f"Content-Length: {len(resp.text)}")

print("\nFirst 1000 characters:")
print(resp.text[:1000])

# Save full content for inspection
with open('sample_form4.xml', 'w') as f:
    f.write(resp.text)
print("\nSaved full content to sample_form4.xml")
