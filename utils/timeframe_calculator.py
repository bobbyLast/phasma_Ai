"""
Smart Timeframe Calculator - Determines optimal trade duration based on characteristics
Not all trades are 7 days! Some are 3 days, some are months!
"""

def calculate_optimal_timeframe(news_item: dict, signal_info: dict = None) -> dict:
    """
    Calculate optimal timeframe based on trade characteristics
    
    Returns:
        dict with 'days_to_expiry', 'timeframe_type', 'reasoning'
    """
    
    # Extract characteristics
    title = news_item.get('title', '').lower()
    sector = news_item.get('sector', '').lower()
    catalyst_score = news_item.get('catalyst_score', 0.5)
    is_moonshot = news_item.get('is_moonshot', False)
    
    # Determine timeframe based on characteristics
    
    # QUICK PLAYS (3-7 days)
    quick_triggers = [
        'earnings', 'er ', 'reports earnings', 'quarterly results',
        'fda approval', 'drug approval', 'clinical trial',
        'merger', 'acquisition', 'buyout',
        'contract awarded', 'wins contract',
        'surprise', 'unexpected', 'breaking'
    ]
    
    if any(trigger in title for trigger in quick_triggers):
        return {
            'days_to_expiry': 7,
            'timeframe_type': 'QUICK_CATALYST',
            'reasoning': 'Catalyst-driven (earnings/FDA/merger) - 7 day window'
        }
    
    # MOONSHOTS (1-5 days)
    if is_moonshot or catalyst_score > 0.8:
        return {
            'days_to_expiry': 5,
            'timeframe_type': 'MOONSHOT',
            'reasoning': 'High-risk moonshot - quick 5 day expiry'
        }
    
    # SWING TRADES (14-30 days)
    swing_triggers = [
        'partnership', 'collaboration', 'deal',
        'expansion', 'growth', 'new product',
        'upgraded', 'raised target', 'analyst',
        'breakout', 'momentum', 'rally'
    ]
    
    if any(trigger in title for trigger in swing_triggers):
        return {
            'days_to_expiry': 21,
            'timeframe_type': 'SWING',
            'reasoning': 'Partnership/growth catalyst - 3 week swing'
        }
    
    # SECTOR-BASED TIMEFRAMES
    if 'biotech' in sector or 'health' in sector or 'pharma' in sector:
        return {
            'days_to_expiry': 45,
            'timeframe_type': 'BIOTECH_PLAY',
            'reasoning': 'Biotech plays need 45+ days for FDA/trial news'
        }
    
    if 'tech' in sector or 'ai' in sector or 'software' in sector:
        return {
            'days_to_expiry': 30,
            'timeframe_type': 'TECH_GROWTH',
            'reasoning': 'Tech growth plays - 30 day window'
        }
    
    if 'energy' in sector or 'oil' in sector:
        return {
            'days_to_expiry': 60,
            'timeframe_type': 'COMMODITY_PLAY',
            'reasoning': 'Energy/commodity plays - 60 day trend'
        }
    
    # LONG-TERM THEMES (60-90 days)
    longterm_triggers = [
        'ai revolution', 'electric vehicle', 'renewable',
        'infrastructure', 'long-term', 'secular trend',
        'transformation', 'restructuring'
    ]
    
    if any(trigger in title for trigger in longterm_triggers):
        return {
            'days_to_expiry': 90,
            'timeframe_type': 'LONG_TERM',
            'reasoning': 'Long-term trend - 90 day LEAPs'
        }
    
    # VALUE PLAYS (120-180 days)
    value_triggers = [
        'undervalued', 'cheap', 'discount',
        'value play', 'accumulation', 'institutional buying'
    ]
    
    if any(trigger in title for trigger in value_triggers):
        return {
            'days_to_expiry': 120,
            'timeframe_type': 'VALUE_ACCUMULATION',
            'reasoning': 'Value accumulation - 4 month horizon'
        }
    
    # DEFAULT: Medium-term swing (21 days)
    return {
        'days_to_expiry': 21,
        'timeframe_type': 'DEFAULT_SWING',
        'reasoning': 'Standard swing trade - 21 day expiry'
    }


def get_expiry_description(days: int) -> str:
    """Get human-readable description of expiry timeframe"""
    if days <= 5:
        return "Ultra-short (Quick catalyst play)"
    elif days <= 10:
        return "Short-term (Week-long play)"
    elif days <= 30:
        return "Medium-term (Monthly swing)"
    elif days <= 60:
        return "Extended (2-month trend)"
    elif days <= 90:
        return "LEAPS (Quarterly position)"
    else:
        return "Long LEAPS (Multi-month hold)"
