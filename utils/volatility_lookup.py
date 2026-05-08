"""Historical volatility database"""
import yfinance as yf
from datetime import datetime, timedelta

class VolatilityLookup:
    def __init__(self):
        self.cache = {}
    
    def get_historical_vol(self, symbol: str, lookback_days: int = 90) -> float:
        """Get annualized historical volatility"""
        if symbol in self.cache:
            return self.cache[symbol]
            
        try:
            end = datetime.now()
            start = end - timedelta(days=lookback_days)
            data = yf.download(symbol, start=start, end=end, progress=False)
            daily_returns = data['Adj Close'].pct_change().dropna()
            vol = daily_returns.std() * (252 ** 0.5)  # Annualize
            self.cache[symbol] = vol
            return vol
        except:
            return 0.3  # Default

get_volatility_lookup = VolatilityLookup()
