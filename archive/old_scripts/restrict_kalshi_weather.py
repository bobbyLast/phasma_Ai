print("🌤️ Restricting Kalshi to Weather Markets Only")
print("=" * 60)

# Read the kalshi_engine.py file
with open('engines/kalshi_engine.py', 'r') as f:
    content = f.read()

# Update analyze_market_opportunity to only accept weather markets
print("\n1. Updating market analysis to filter for weather only...")

# Find the analyze_market_opportunity method and add weather filter
lines = content.split('\n')
new_lines = []

for i, line in enumerate(lines):
    new_lines.append(line)
    
    # Add weather filter right after ticker extraction
    if 'ticker = market_data.get(\'ticker\', \'\')' in line:
        # Add weather-only filter
        weather_filter = [
            '',
            '        # KALSHI WEATHER-ONLY RESTRICTION',
            '        if not self._is_weather_market(ticker):',
            '            return {',
            '                \'ticker\': ticker,',
            '                \'signal\': None,',
            '                \'confidence\': 0,',
            '                \'rationale\': f"Non-weather market skipped: {ticker} (Kalshi restricted to weather only)",',
            '                \'action\': None,',
            '                \'position_size\': 0,',
            '                \'trade_link\': self.get_market_trade_link(ticker),',
            '                \'market_type\': \'non_weather\'',
            '            }',
            ''
        ]
        new_lines.extend(weather_filter)
    
    # Remove multi-choice logic since we're weather-only
    elif '# Check for multi-choice markets (elections, etc.)' in line:
        # Skip the multi-choice block
        while i < len(lines) and 'implied_prob = market_data.get' not in lines[i]:
            i += 1
        # Don't add the multi-choice lines
        continue

# Write back the updated content
with open('engines/kalshi_engine.py', 'w') as f:
    f.write('\n'.join(new_lines))

print("✅ Added weather-only filter")

# Now add the _is_weather_market method
print("\n2. Adding weather market detection method...")

with open('engines/kalshi_engine.py', 'r') as f:
    content = f.read()

# Find a good place to add the new method (after _is_political_market)
insert_pos = content.find('    def _is_political_market')
if insert_pos > 0:
    # Find the end of this method
    end_pos = content.find('\n    def ', insert_pos + 1)
    if end_pos == -1:
        end_pos = len(content)
    
    # Insert the new weather method
    weather_method = '''
    def _is_weather_market(self, ticker: str) -> bool:
        """Check if a Kalshi market is weather-related.
        
        Kalshi should ONLY trade weather markets per user requirement.
        """
        ticker_upper = ticker.upper()
        title_upper = ticker.upper()  # In case title is in ticker
        
        # Weather keywords and patterns
        weather_patterns = [
            # Temperature patterns
            'HIGH', 'LOW', 'TEMP', 'TEMPERATURE',
            # Precipitation
            'RAIN', 'SNOW', 'PRECIP', 'PRECIPITATION',
            # Weather conditions
            'WEATHER', 'WIND', 'HUMIDITY', 'DEWPOINT',
            # Location codes (major cities)
            'NYC', 'CHI', 'LA', 'MIA', 'DAL', 'SEA', 'DEN',
            # Specific Kalshi weather patterns
            'HIGHNY', 'LOWNY', 'RAINNY', 'SNOWNY',
            'HIGHCHI', 'LOWCHI', 'RAINCHI', 'SNOWCHI',
            'HIGHMIA', 'LOWMIA', 'RAINMIA', 'SNOWMIA',
            # Generic weather event codes
            'WX', 'WTHR'
        ]
        
        # Check if any weather pattern is in the ticker
        for pattern in weather_patterns:
            if pattern in ticker_upper:
                return True
        
        # Additional check: Weather tickers typically have number ranges
        # Example: HIGHNY0-25-85 (NYC high > 85°F on Dec 25)
        import re
        # Pattern for weather with temperature thresholds
        if re.match(r'.*[0-9]-[0-9]+-[0-9]+', ticker_upper):
            # Likely a weather market with date and threshold
            return True
        
        # If none of the weather patterns match, it's not a weather market
        return False
'''
    
    content = content[:end_pos] + weather_method + content[end_pos:]
    
    with open('engines/kalshi_engine.py', 'w') as f:
        f.write(content)
    
    print("✅ Added weather market detection method")

# Update the config to emphasize weather-only
print("\n3. Updating config to emphasize weather-only Kalshi...")

with open('config.json', 'r') as f:
    config = json.load(f)

# Add weather-only restriction
config['kalshi_weather_only'] = True
config['kalshi_restrictions'] = {
    'allowed_markets': ['weather'],
    'blocked_markets': ['elections', 'sports', 'politics', 'economics', 'fed', 'volatility'],
    'note': 'Kalshi restricted to weather markets only per user requirement'
}

with open('config.json', 'w') as f:
    json.dump(config, f, indent=2)

print("✅ Updated config with weather-only restriction")

print("\n" + "=" * 60)
print("✅ KALSHI RESTRICTED TO WEATHER MARKETS ONLY!")
print("\n🌤️ What This Means:")
print("   • Only weather markets will be analyzed")
print("   • Elections, sports, politics will be skipped")
print("   • AI will focus on consistent weather trading")
print("   • Temperature, rain, snow markets only")

print("\n📊 Examples of ALLOWED markets:")
print("   • HIGHNY0-25-85 (NYC high > 85°F)")
print("   • RAINMIA-25 (Miami rain on Dec 25)")
print("   • SNOWCHIM-25-2 (Chicago snow > 2 inches)")

print("\n❌ Examples of BLOCKED markets:")
print("   • KXPERSONPRES* (Elections)")
print("   • KXTEAMAVSTEAM (Sports)")
print("   • KXFED* (Fed rates)")

print("\n🎯 Result: AI will consistently trade weather markets only!")
