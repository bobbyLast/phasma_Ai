"""
Professional options chain analysis (Robinhood-style metrics).
Used by main.py to filter high-confidence options signals on POP, liquidity, and spread.
"""

import math
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import yfinance as yf


class ProOptionsAnalyzer:
    """Option chain with POP, liquidity, bid/ask spread, and Greeks."""

    def __init__(self):
        self.commission_per_contract = 0.65
        self.contracts_multiplier = 100

    def get_robinhood_style_chain(self, symbol: str, days_out: int = 30) -> Dict:
        """Return calls/puts with probability_of_profit, liquidity_score, spread_pct."""
        try:
            stock = yf.Ticker(symbol)
            hist = stock.history(period="1d")
            if hist.empty:
                return {"error": f"No price data for {symbol}"}
            current_price = float(hist["Close"].iloc[-1])

            expirations = stock.options
            if not expirations:
                return {"error": f"No options available for {symbol}"}

            target_date = datetime.now() + timedelta(days=days_out)
            closest_expiry = self._find_closest_expiry(expirations, target_date)
            if not closest_expiry:
                return {"error": f"No suitable expiration found for {symbol}"}

            chain = stock.option_chain(closest_expiry)
            dte = self._calculate_dte(closest_expiry)
            analysis = {
                "symbol": symbol,
                "current_price": current_price,
                "expiration": closest_expiry,
                "dte": dte,
                "timestamp": datetime.now().strftime("%I:%M %p ET"),
                "calls": [],
                "puts": [],
            }

            atm_strike = self._find_atm_strike(current_price)
            for strike in self._get_strikes_around_money(chain, atm_strike, 5):
                call_data = self._get_option_by_strike(chain.calls, strike)
                if call_data and call_data.get("lastPrice", 0) > 0:
                    analysis["calls"].append(
                        self._analyze_option(call_data, "CALL", current_price, dte)
                    )
                put_data = self._get_option_by_strike(chain.puts, strike)
                if put_data and put_data.get("lastPrice", 0) > 0:
                    analysis["puts"].append(
                        self._analyze_option(put_data, "PUT", current_price, dte)
                    )

            return analysis
        except Exception as e:
            return {"error": f"Error: {e}"}

    def _analyze_option(
        self, option_data: Dict, option_type: str, stock_price: float, dte: int
    ) -> Dict:
        last_price = option_data.get("lastPrice", 0) or 0
        bid = option_data.get("bid", 0) or 0
        ask = option_data.get("ask", 0) or 0
        strike = option_data.get("strike", 0) or 0
        volume = int(option_data.get("volume", 0) or 0)
        open_interest = int(option_data.get("openInterest", 0) or 0)
        implied_vol = option_data.get("impliedVolatility", 0) or 0
        delta = option_data.get("delta", 0) or 0

        spread = ask - bid if ask > 0 and bid > 0 else last_price * 0.05
        mid_price = (bid + ask) / 2 if bid > 0 and ask > 0 else last_price
        pop = self._calculate_probability_of_profit(
            last_price, strike, stock_price, dte, implied_vol, option_type
        )

        return {
            "strike": strike,
            "last_price": last_price,
            "bid": bid,
            "ask": ask,
            "spread": spread,
            "spread_pct": (spread / mid_price * 100) if mid_price > 0 else 0,
            "volume": volume,
            "open_interest": open_interest,
            "liquidity_score": self._calculate_liquidity_score(volume, open_interest),
            "delta": delta,
            "probability_of_profit": pop * 100,
            "option_type": option_type,
            "days_to_expiration": dte,
        }

    def _calculate_probability_of_profit(
        self,
        premium: float,
        strike: float,
        stock_price: float,
        dte: int,
        iv: float,
        option_type: str,
    ) -> float:
        if premium <= 0 or dte <= 0:
            return 0.1
        breakeven = strike + premium if option_type == "CALL" else strike - premium
        distance_pct = abs(breakeven - stock_price) / stock_price if stock_price else 1
        time_factor = math.sqrt(dte / 365) if iv > 0 else 1
        volatility_factor = iv if iv > 0 else 0.3
        z_score = distance_pct / (volatility_factor * time_factor)
        pop = (
            1 - self._normal_cdf(z_score)
            if option_type == "CALL"
            else self._normal_cdf(z_score)
        )
        return max(0.1, min(0.9, pop))

    @staticmethod
    def _normal_cdf(x: float) -> float:
        return 0.5 * (1 + math.erf(x / math.sqrt(2)))

    @staticmethod
    def _calculate_liquidity_score(volume: int, open_interest: int) -> str:
        if volume >= 1000 and open_interest >= 1000:
            return "Very High"
        if volume >= 100 and open_interest >= 100:
            return "High"
        if volume >= 10 and open_interest >= 10:
            return "Medium"
        return "Low"

    def _get_strikes_around_money(self, chain, atm_strike: float, count: int) -> List[float]:
        all_strikes = set(chain.calls["strike"].tolist() + chain.puts["strike"].tolist())
        sorted_strikes = sorted(all_strikes)
        atm_index = min(
            range(len(sorted_strikes)),
            key=lambda i: abs(sorted_strikes[i] - atm_strike),
            default=0,
        )
        start = max(0, atm_index - count // 2)
        end = min(len(sorted_strikes), start + count)
        return sorted_strikes[start:end]

    @staticmethod
    def _find_atm_strike(stock_price: float) -> float:
        if stock_price < 50:
            return round(stock_price)
        if stock_price < 200:
            return round(stock_price / 5) * 5
        return round(stock_price / 10) * 10

    @staticmethod
    def _get_option_by_strike(options_df, strike: float) -> Optional[Dict]:
        if options_df.empty:
            return None
        option_row = options_df[options_df["strike"] == strike]
        if option_row.empty:
            return None
        return option_row.iloc[0].to_dict()

    @staticmethod
    def _find_closest_expiry(expirations: List[str], target_date: datetime) -> Optional[str]:
        closest = None
        min_diff = float("inf")
        for expiry in expirations[:6]:
            try:
                expiry_date = datetime.strptime(expiry, "%Y-%m-%d")
                diff = abs((expiry_date - target_date).days)
                if diff < min_diff:
                    min_diff = diff
                    closest = expiry
            except ValueError:
                continue
        return closest

    @staticmethod
    def _calculate_dte(expiry: str) -> int:
        try:
            expiry_date = datetime.strptime(expiry, "%Y-%m-%d")
            return max(0, (expiry_date - datetime.now()).days)
        except ValueError:
            return 0
