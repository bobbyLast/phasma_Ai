#!/usr/bin/env python3
"""
Test script to debug SEC XML parsing issues
"""

import requests
import xml.etree.ElementTree as etree
import time

def test_sec_fetch():
    """Test fetching and parsing SEC Form 4 data"""
    
    print("Testing SEC Form 4 XML parsing...")
    
    # SEC RSS feed URL
    url = "https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent&CIK=&type=4&company=&dateb=&owner=include&count=100"
    
    headers = {"User-Agent": "PhasmaAI/InsiderMonitor (https://sec.gov)"}
    
    try:
        print("1. Fetching SEC RSS feed...")
        resp = requests.get(url, headers=headers, timeout=30)
        
        if resp.status_code != 200:
            print(f"   Failed: HTTP {resp.status_code}")
            return
        
        print(f"   Success: Got {len(resp.text)} bytes")
        
        # Parse RSS
        print("\n2. Parsing RSS feed...")
        
        # Try different parsing approaches
        content = resp.text
        
        # Method 1: Remove XML declaration
        if content.startswith('<?xml'):
            try:
                content = content.split('?>', 1)[1]
                root = etree.fromstring(content.encode('utf-8'))
            except:
                # Method 2: Try with original content
                try:
                    root = etree.fromstring(content.encode('utf-8'))
                except:
                    # Method 3: Try cleaning special characters
                    content = content.replace('&', '&amp;')
                    root = etree.fromstring(content.encode('utf-8'))
        else:
            root = etree.fromstring(content.encode('utf-8'))
        
        # Count entries
        entries = root.findall(".//item")
        print(f"   Found {len(entries)} Form 4 filings")
        
        if len(entries) == 0:
            print("   No entries found - checking for Atom format...")
            entries = root.findall("{http://www.w3.org/2005/Atom}entry")
            print(f"   Found {len(entries)} Atom entries")
        
        if len(entries) == 0:
            print("   ERROR: No entries found in either format")
            return
        
        # Test first entry
        print("\n3. Testing first entry...")
        first_entry = entries[0]
        
        title_elem = first_entry.find("title")
        title = title_elem.text if title_elem is not None else "No title"
        print(f"   Title: {title}")
        
        link_elem = first_entry.find("link")
        link = link_elem.text if link_elem is not None else "No link"
        print(f"   Link: {link}")
        
        # Try to fetch XML
        if link and link != "No link":
            print("\n4. Fetching Form 4 XML...")
            time.sleep(1.5)  # Rate limit
            
            xml_resp = requests.get(link, headers=headers, timeout=10)
            
            if xml_resp.status_code != 200:
                print(f"   Failed: HTTP {xml_resp.status_code}")
            else:
                print(f"   Success: Got {len(xml_resp.text)} bytes")
                
                # Look for XML files in the page
                import re
                xml_matches = re.findall(r'href="([^"]*\.xml)"', xml_resp.text)
                xml_urls = [m for m in xml_matches if 'xslF345X05' not in m]
                
                if xml_urls:
                    xml_url = xml_urls[0]
                    if not xml_url.startswith("http"):
                        xml_url = "https://www.sec.gov" + xml_url
                    
                    print(f"   Found XML URL: {xml_url}")
                    
                    # Fetch actual XML
                    time.sleep(1.5)
                    final_xml = requests.get(xml_url, headers=headers, timeout=10)
                    
                    if final_xml.status_code == 200:
                        print("   Successfully fetched Form 4 XML")
                        
                        # Try to parse
                        try:
                            xml_root = etree.fromstring(final_xml.content)
                            print("   XML parsed successfully")
                            
                            # Find ticker
                            issuer = xml_root.find(".//issuerTradingSymbol")
                            if issuer is not None:
                                print(f"   Ticker: {issuer.text}")
                            
                            # Find transactions
                            transactions = xml_root.findall(".//nonDerivativeTransaction")
                            print(f"   Found {len(transactions)} transactions")
                            
                        except Exception as e:
                            print(f"   XML parsing failed: {e}")
                    else:
                        print(f"   Failed to fetch XML: {final_xml.status_code}")
                else:
                    print("   No XML files found in the page")
        
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    test_sec_fetch()
