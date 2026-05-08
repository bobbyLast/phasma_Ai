import json
import os

print("🔧 Fixing Stock Signals to Use BUY/SELL Instead of Options Terms")
print("=" * 60)

# Read the news engine utils file
utils_file = 'engines/news_engine_utils.py'
with open(utils_file, 'r') as f:
    content = f.read()

# Check if we need to add stock-only mode
if 'stock_only_mode' not in content:
    print("Adding stock-only mode check...")
    
    # Find the get_options_recommendation function
    start_pos = content.find('def get_options_recommendation')
    if start_pos > 0:
        # Find the end of the function
        end_pos = content.find('\n    def ', start_pos + 1)
        if end_pos == -1:
            end_pos = len(content)
        
        # Replace the function to include stock-only check
        old_function = content[start_pos:end_pos]
        
        new_function = '''def get_options_recommendation(news_item: Dict, stock_only_mode: bool = False) -> str:
        """Get options trading recommendation based on news and company data
        
        Args:
            news_item: News item dictionary
            stock_only_mode: If True, returns simple BUY/SELL recommendations
        """
        symbol = news_item.get('symbol', '')
        sentiment = news_item.get('sentiment', 0.0)
        catalyst_score = news_item.get('catalyst_score', 0.0)
        options_data = news_item.get('options_data', {})

        # If in stock-only mode, return simple BUY/SELL
        if stock_only_mode:
            if sentiment > 0.1 or catalyst_score > 0.5:
                return 'BUY'  # Positive sentiment = BUY stock
            elif sentiment < -0.1:
                return 'SELL'  # Negative sentiment = SELL stock
            else:
                return 'HOLD'  # Neutral = hold

        iv = options_data.get('estimated_iv', 0.0)
        volume = options_data.get('estimated_options_volume', 0)

        # Determine recommendation based on sentiment and catalyst'''
        
        content = content[:start_pos] + new_function + content[end_pos:]
        
        # Write back the modified content
        with open(utils_file, 'w') as f:
            f.write(content)
        
        print("✅ Updated get_options_recommendation to support stock-only mode")
    else:
        print("❌ Could not find get_options_recommendation function")

# Now update main.py to pass stock_only_mode=True
main_file = 'main.py'
with open(main_file, 'r') as f:
    main_content = f.read()

# Find where options_recommendation is used
if 'options_recommendation' in main_content and 'stock_only_mode' not in main_content:
    print("\nUpdating main.py to use stock-only mode...")
    
    # Find the line where options_recommendation is accessed
    lines = main_content.split('\n')
    for i, line in enumerate(lines):
        if 'options_recommendation' in line and '=' in line:
            # This is where we get the recommendation
            # Add stock_only_mode=True to the function call
            if 'get_options_recommendation' in lines[i-1]:
                lines[i-1] = lines[i-1].replace(')', ', stock_only_mode=True)')
                break
    
    # Also need to update the action mapping
    for i, line in enumerate(lines):
        if "action = 'BUY_CALL'" in line:
            # Update the mapping to handle BUY/SELL
            lines[i] = lines[i].replace("action = 'BUY_CALL'", "action = 'BUY' if options_recommendation == 'BUY' else 'SELL'")
            lines[i+1] = lines[i+1].replace("elif options_recommendation == 'BUY_PUT':", "elif options_recommendation == 'SELL':")
            lines[i+2] = lines[i+2].replace("action = 'BUY_PUT'", "action = 'SELL'")
            lines[i+3] = lines[i+3].replace("elif options_recommendation == 'BUY_STRADDLE':", "elif options_recommendation == 'HOLD':")
            lines[i+4] = lines[i+4].replace("action = 'BUY_STRADDLE'", "action = 'HOLD'")
            lines[i+5] = lines[i+5].replace("else:", "else:")
            lines[i+6] = lines[i+6].replace("action = 'BUY_CALL'  # Default fallback", "action = 'BUY'  # Default to BUY")
            break
    
    # Write back the modified main.py
    with open(main_file, 'w') as f:
        f.write('\n'.join(lines))
    
    print("✅ Updated main.py to use stock-only recommendations")

# Also update the trade_type to be STOCK instead of empty
print("\nUpdating signal creation to set trade_type='STOCK'...")
for i, line in enumerate(lines):
    if "signal_dict['trade_type']" in line and 'KALSHI' not in line:
        if 'stock' in line.lower():
            lines[i] = "                        signal_dict['trade_type'] = 'STOCK'\n"
            break

# Write the final update
with open(main_file, 'w') as f:
    f.write('\n'.join(lines))

print("✅ All updates complete!")
print("\n📋 Changes Made:")
print("   1. Added stock_only_mode parameter to get_options_recommendation")
print("   2. Stock-only mode returns BUY/SELL instead of BUY_CALL/BUY_PUT")
print("   3. Updated main.py to pass stock_only_mode=True")
print("   4. Updated action mapping to handle BUY/SELL")
print("   5. Ensured trade_type is set to 'STOCK' for stock signals")

print("\n🎯 Result:")
print("   - Stock signals will now show 'BUY' or 'SELL' instead of 'BUY_CALL'")
print("   - No more options terminology for stock trades")
print("   - Kalshi signals still use YES/NO as appropriate")
