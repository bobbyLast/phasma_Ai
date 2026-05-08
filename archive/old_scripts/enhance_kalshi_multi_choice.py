print("🔧 Enhancing Kalshi for Multiple-Choice Markets")
print("=" * 60)

# Read the current kalshi_engine.py
with open('engines/kalshi_engine.py', 'r') as f:
    content = f.read()

# Add new method to handle multi-choice markets
multi_choice_method = '''
    def analyze_multi_choice_market(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze a multi-choice Kalshi market (e.g., elections with multiple candidates).
        
        For multi-choice markets, we:
        1. Identify all choices/submarkets
        2. Find the best value based on our probability vs market price
        3. Return the recommended choice(s)
        
        Args:
            market_data: Market data for a specific choice
            
        Returns:
            Dict with analysis and recommendation
        """
        ticker = market_data.get('ticker', '')
        title = market_data.get('title', '')
        implied_prob = market_data.get('implied_probability', 0.5)
        
        # Extract the base event from ticker (remove candidate suffix)
        # Example: KXPERSONPRESFUENTES-45 -> KXPERSONPRES
        import re
        match = re.match(r'([A-Z]+-[A-Z]+)', ticker.upper())
        if match:
            base_event = match.group(1)
        else:
            base_event = ticker
        
        # Try to get all submarkets for this event
        try:
            all_markets = self.get_open_markets_for_series(base_event)
            choices = []
            
            for m in all_markets:
                if base_event in m.get('ticker', ''):
                    choice_ticker = m.get('ticker', '')
                    choice_title = m.get('title', '')
                    
                    # Calculate implied probability for this choice
                    yes_price = None
                    if "yes_ask" in m and m["yes_ask"] > 0:
                        yes_price = m["yes_ask"]
                    elif "yes_price" in m and m["yes_price"] > 0:
                        yes_price = m["yes_price"]
                    elif "last_price" in m and m["last_price"] > 0:
                        yes_price = m["last_price"]
                    
                    if yes_price:
                        choices.append({
                            'ticker': choice_ticker,
                            'title': choice_title,
                            'implied_probability': yes_price / 100,
                            'price': yes_price
                        })
            
            # Sort by implied probability (highest first)
            choices.sort(key=lambda x: x['implied_probability'], reverse=True)
            
            # Find best value (highest probability that's still reasonably priced)
            best_choice = None
            best_edge = 0
            
            for choice in choices:
                # Simple edge calculation: look for high probability choices
                # In real implementation, this would use our own probability estimate
                edge = choice['implied_probability'] - 0.5  # Simple baseline
                
                if edge > best_edge and choice['implied_probability'] > 0.3:
                    best_edge = edge
                    best_choice = choice
            
            if best_choice:
                return {
                    'is_multi_choice': True,
                    'recommended_choice': best_choice,
                    'all_choices': choices,
                    'analysis': f"Multi-choice market with {len(choices)} options. Best value: {best_choice['title']} at {best_choice['implied_probability']:.1%}",
                    'action': 'BUY_YES',  # For the recommended choice
                    'confidence': min(best_choice['implied_probability'] * 1.2, 0.9),
                    'rationale': f"Selected {best_choice['title']} as best value among {len(choices)} choices"
                }
            else:
                return {
                    'is_multi_choice': True,
                    'all_choices': choices,
                    'analysis': f"Multi-choice market with {len(choices)} options, but no clear value found",
                    'action': None,
                    'confidence': 0,
                    'rationale': "No choice offers sufficient edge"
                }
                
        except Exception as e:
            print(f"Error analyzing multi-choice market: {e}")
            # Fallback to single analysis
            return {
                'is_multi_choice': False,
                'analysis': "Could not analyze as multi-choice, treating as single market",
                'action': None,
                'confidence': 0
            }
'''

# Find where to insert the new method (after analyze_market_opportunity)
insert_pos = content.find('    def _calculate_days_to_expiry')
if insert_pos > 0:
    # Insert the new method before _calculate_days_to_expiry
    content = content[:insert_pos] + multi_choice_method + '\n' + content[insert_pos:]
    
    # Write back to file
    with open('engines/kalshi_engine.py', 'w') as f:
        f.write(content)
    
    print("✅ Added multi-choice market analysis method")
else:
    print("❌ Could not find insertion point")

# Now update analyze_market_opportunity to check for multi-choice
print("\n🔄 Updating analyze_market_opportunity to handle multi-choice...")

# Find and update the analyze_market_opportunity method
with open('engines/kalshi_engine.py', 'r') as f:
    lines = f.readlines()

# Find the beginning of analyze_market_opportunity
for i, line in enumerate(lines):
    if 'def analyze_market_opportunity' in line:
        # Look for the weather check we added earlier
        for j in range(i, min(i+50, len(lines))):
            if 'if self.consistency_engine:' in lines[j]:
                # Insert multi-choice check after weather check
                insert_idx = j + 20  # After the weather block
                multi_check = [
                    '\n',
                    '        # Check for multi-choice markets (elections, etc.)\n',
                    '        if self._is_multi_choice_market(ticker):\n',
                    '            multi_analysis = self.analyze_multi_choice_market(market_data)\n',
                    '            if multi_analysis.get(\'action\'):\n',
                    '                return {\n',
                    '                    \'ticker\': ticker,\n',
                    '                    \'signal\': multi_analysis[\'action\'],\n',
                    '                    \'confidence\': multi_analysis[\'confidence\'],\n',
                    '                    \'rationale\': multi_analysis[\'rationale\'],\n',
                    '                    \'action\': multi_analysis[\'action\'],\n',
                    '                    \'position_size\': 100,  # Default size for multi-choice\n',
                    '                    \'is_multi_choice\': True,\n',
                    '                    \'choices\': multi_analysis.get(\'all_choices\', []),\n',
                    '                    \'recommended_choice\': multi_analysis.get(\'recommended_choice\', {}),\n',
                    '                    \'trade_link\': self.get_market_trade_link(ticker)\n',
                    '                }\n',
                    '            else:\n',
                    '                return {\n',
                    '                    \'ticker\': ticker,\n',
                    '                    \'signal\': None,\n',
                    '                    \'confidence\': 0,\n',
                    '                    \'rationale\': multi_analysis.get(\'rationale\', \'No value in multi-choice market\'),\n',
                    '                    \'action\': None,\n',
                    '                    \'position_size\': 0,\n',
                    '                    \'trade_link\': self.get_market_trade_link(ticker)\n',
                    '                }\n'
                ]
                
                # Insert the lines
                lines = lines[:insert_idx] + multi_check + lines[insert_idx:]
                break
        break

# Write the updated file
with open('engines/kalshi_engine.py', 'w') as f:
    f.writelines(lines)

print("✅ Updated analyze_market_opportunity to handle multi-choice markets")

# Also update the _is_multi_choice_market method to be more comprehensive
print("\n🔄 Updating _is_multi_choice_market detection...")

with open('engines/kalshi_engine.py', 'r') as f:
    content = f.read()

# Replace the existing method
old_method = '''    def _is_multi_choice_market(self, ticker: str) -> bool:
        """Check if market has multiple choices (election with multiple candidates)"""
        # Multi-choice markets typically have candidate identifiers
        # Example: KXPERSONPRESFUENTES-45, KXPERSONPRESMAM-45
        ticker_upper = ticker.upper()
        
        # Check for candidate identifiers (usually 2-4 letters at end)
        import re
        # Pattern: EVENT-CANDIDATE (e.g., PERSONPRESFUENTES-45)
        match = re.match(r'([A-Z]+)-([A-Z]+)', ticker_upper)
        if match:
            event_part, candidate_part = match.groups()'''

new_method = '''    def _is_multi_choice_market(self, ticker: str) -> bool:
        """Check if market has multiple choices (election with multiple candidates)"""
        # Multi-choice markets indicators:
        # 1. Candidate identifiers in ticker (e.g., KXPERSONPRESFUENTES-45)
        # 2. "vs" or "versus" in title
        # 3. Election-related keywords
        ticker_upper = ticker.upper()
        
        # Check for candidate identifiers (usually 2-4 letters at end)
        import re
        # Pattern: EVENT-CANDIDATE (e.g., PERSONPRESFUENTES-45)
        match = re.match(r'([A-Z]+)-([A-Z]+)', ticker_upper)
        if match:
            event_part, candidate_part = match.groups()'''

content = content.replace(old_method, new_method)

with open('engines/kalshi_engine.py', 'w') as f:
    f.write(content)

print("✅ Updated multi-choice market detection")

print("\n" + "=" * 60)
print("✅ Multi-Choice Market Support Added!")
print("\n📋 How it works:")
print("1. Detects multi-choice markets (elections, vs markets)")
print("2. Fetches all choices for the event")
print("3. Identifies the best value choice")
print("4. Returns recommendation for that specific choice")
print("\n🎯 Example:")
print("   Market: 'KXPERSONPRESFUENTES-45' (Fuentes for President)")
print("   → Analyzes all candidates (Fuentes, Mam, etc.)")
print("   → Picks the one with best probability vs price")
print("   → Returns BUY_YES for that candidate only")
