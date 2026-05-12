"""
Optional: Enhanced scoring for higher maximums
"""

# If you want scores up to 100, modify enhanced_confluence_scorer.py:

# Change line 28-33 (macro alignment):
if context.get('macro_regime') == 'RISK_ON':
    scores['macro_alignment'] = 1.0 if opportunity.get('action') == 'BUY' else 0.0
elif context.get('macro_regime') == 'RISK_OFF':
    scores['macro_alignment'] = 0.0 if opportunity.get('action') == 'BUY' else 1.0
else:
    scores['macro_alignment'] = 0.5

# Change line 39-44 (value alignment):
if 0 < price < 50 and target > price * 1.5:  # Higher threshold
    scores['value_alignment'] = 1.0
elif 0 < price < 50 and target > price * 1.1:
    scores['value_alignment'] = 0.8
elif price < 10:
    scores['value_alignment'] = 0.6
else:
    scores['value_alignment'] = 0.3

# Change line 48-53 (technical confirmation):
if any(p in ['breakout', 'oversold', 'divergence'] for p in patterns):
    scores['technical_confirmation'] = 1.0
elif patterns:
    scores['technical_confirmation'] = 0.7
else:
    scores['technical_confirmation'] = 0.3

# Change line 56-59 (news catalyst):
if opportunity.get('news_items'):
    scores['news_catalyst'] = 1.0
else:
    scores['news_catalyst'] = 0.2

# This would allow scores up to 100!
print("To enable 100-point scores, modify enhanced_confluence_scorer.py with the above changes")
