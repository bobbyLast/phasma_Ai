import re

ticker = 'HIGHNY0-25-85'
print(f"Ticker: {ticker}")

# Test the pattern
pattern = r'HIGH([A-Z]+)(\d+)-(\d+)-(\d+)'
match = re.match(pattern, ticker.upper())

if match:
    print(f"Match found!")
    groups = match.groups()
    print(f"Groups: {groups}")
    print(f"Number of groups: {len(groups)}")
    for i, group in enumerate(groups):
        print(f"  Group {i}: '{group}'")
else:
    print("No match found")
