import sys
sys.path.insert(0, '.')
from dotenv import load_dotenv
load_dotenv()

import json
from engines.kalshi_engine import KalshiPredictionEngine

# Load config
with open('config.json', 'r') as f:
    config = json.load(f)

# Initialize Kalshi engine
kalshi = KalshiPredictionEngine(config)

            # Extract expiration information from market_data
            market_data = m.get('market_data', {})
            expiration_date = market_data.get('expiration_time') or market_data.get('close_time')
            days_to_expiry = self._calculate_days_to_expiry(expiration_date)
            
            print(f'Debug - Market: {m.get("ticker")}')
            print(f'  expiration_time: {market_data.get("expiration_time")}')
            print(f'  close_time: {market_data.get("close_time")}')
            print(f'  days_to_expiry: {days_to_expiry}')
            print(f'  status: {market_data.get("status")}')
            
            # Determine if this is a short-term opportunity (1-2 weeks)
            is_short_term = days_to_expiry <= 14 and days_to_expiry > 0

            views.append({
                "ticker": m.get("ticker"),
                "title": m.get("title"),
                "series_ticker": m.get("series_ticker"),
                "event_ticker": m.get("event_ticker"),
                "yes_price": yes_price,
                "volume": m.get("volume", 0),
                "open_interest": m.get("open_interest", 0),
                "implied_probability": p_imp,
                "expiration_date": expiration_date,
                "days_to_expiry": days_to_expiry,
                "is_short_term": is_short_term,
                "market_data": m  # Keep full market data for reference
            })

        return views
