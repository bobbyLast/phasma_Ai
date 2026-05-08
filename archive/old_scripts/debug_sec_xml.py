#!/usr/bin/env python3
"""
Debug SEC XML parsing to find the exact issue
"""

import requests

def debug_sec_xml():
    """Debug the SEC XML parsing issue"""
    
    url = "https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent&CIK=&type=4&company=&dateb=&owner=include&count=100"
    headers = {"User-Agent": "PhasmaAI/InsiderMonitor (https://sec.gov)"}
    
    print("Fetching SEC RSS feed...")
    resp = requests.get(url, headers=headers, timeout=30)
    
    if resp.status_code == 200:
        print(f"Got {len(resp.text)} bytes")
        
        # Look at the first few lines
        lines = resp.text.split('\n')
        
        print("\nFirst 10 lines:")
        for i, line in enumerate(lines[:10], 1):
            print(f"{i:2d}: {line}")
        
        # Find line 2, column 61
        if len(lines) >= 2:
            line2 = lines[1]
            print(f"\nLine 2: {line2}")
            print(f"Length: {len(line2)}")
            
            if len(line2) >= 61:
                print(f"Character at position 61: '{line2[60]}'")
                print(f"Context around position 61:")
                start = max(0, 60 - 20)
                end = min(len(line2), 60 + 20)
                print(f"   {line2[start:end]}")
                print(f"   {' ' * (60 - start)}^")
        
        # Check for special characters
        print("\nChecking for special characters in first 5 lines:")
        for i, line in enumerate(lines[:5], 1):
            special_chars = []
            for j, char in enumerate(line):
                if ord(char) > 127 or ord(char) < 32:
                    special_chars.append((j, char, ord(char)))
            
            if special_chars:
                print(f"Line {i} has special characters:")
                for pos, char, code in special_chars[:5]:
                    print(f"   Position {pos}: '{char}' (code {code})")

if __name__ == "__main__":
    debug_sec_xml()
