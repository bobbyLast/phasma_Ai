"""
Robinhood-Style Option Pricing Calculator
Professional interface with Greeks, probabilities, and clean formatting
Designed for Level 2 trading access (educational/analysis)
"""

import yfinance as yf
from datetime import datetime, timedelta
from typing import Dict, Optional, List
import math

class RobinhoodStylePricing:
    """
    Professional option pricing interface similar to Robinhood
    Shows Greeks, probabilities, bid/ask analysis, and clean formatting
    """
    
    def __init__(self):
        self.commission_per_contract = 0.65
        self.contracts_multiplier = 100
        
    def get_robinhood_style_chain(self, symbol: str, days_out: int = 30) -> Dict:
        """
        Get option chain with Robinhood-style presentation
        """
        try:
            stock = yf.Ticker(symbol)
            current_price = stock.history(period="1d")['Close'].iloc[-1]
            
            expirations = stock.options
            if not expirations:
                return {'error': f'No options available for {symbol}'}
            
            target_date = datetime.now() + timedelta(days=days_out)
            closest_expiry = self._find_closest_expiry(expirations, target_date)
            
            if not closest_expiry:
                return {'error': f'No suitable expiration found for {symbol}'}
            
            chain = stock.option_chain(closest_expiry)
            
            # Create Robinhood-style analysis
            analysis = {
                'symbol': symbol,
                'current_price': current_price,
                'expiration': closest_expiry,
                'dte': self._calculate_dte(closest_expiry),
                'timestamp': datetime.now().strftime('%I:%M %p ET'),
                'calls': [],
                'puts': []
            }
            
            # Get top 5 calls and puts around the money
            atm_strike = self._find_atm_strike(current_price)
            strikes = self._get_strikes_around_money(chain, atm_strike, 5)
            
            for strike in strikes:
                # Call option
                call_data = self._get_option_by_strike(chain.calls, strike)
                if call_data and call_data.get('lastPrice', 0) > 0:
                    call_analysis = self._analyze_option_robinhood_style(
                        call_data, 'CALL', symbol, current_price, analysis['dte']
                    )
                    analysis['calls'].append(call_analysis)
                
                # Put option  
                put_data = self._get_option_by_strike(chain.puts, strike)
                if put_data and put_data.get('lastPrice', 0) > 0:
                    put_analysis = self._analyze_option_robinhood_style(
                        put_data, 'PUT', symbol, current_price, analysis['dte']
                    )
                    analysis['puts'].append(put_analysis)
            
            return analysis
            
        except Exception as e:
            return {'error': f'Error: {str(e)}'}
    
    def _analyze_option_robinhood_style(self, option_data: Dict, option_type: str, 
                                      symbol: str, stock_price: float, dte: int) -> Dict:
        """
        Analyze option with Robinhood-style metrics
        """
        # Extract pricing data
        last_price = option_data.get('lastPrice', 0)
        bid = option_data.get('bid', 0)
        ask = option_data.get('ask', 0)
        strike = option_data.get('strike', 0)
        volume = option_data.get('volume', 0)
        open_interest = option_data.get('openInterest', 0)
        implied_vol = option_data.get('impliedVolatility', 0)
        
        # Greeks
        delta = option_data.get('delta', 0)
        gamma = option_data.get('gamma', 0)
        theta = option_data.get('theta', 0)
        vega = option_data.get('vega', 0)
        
        # Calculate Robinhood-style metrics
        spread = ask - bid if ask > 0 and bid > 0 else last_price * 0.05  # Estimate spread
        mid_price = (bid + ask) / 2 if bid > 0 and ask > 0 else last_price
        
        # Probability calculations
        itm_probability = self._calculate_itm_probability(delta, option_type)
        pop = self._calculate_probability_of_profit(last_price, strike, stock_price, dte, implied_vol, option_type)
        
        # Risk metrics
        max_loss = last_price * 100  # Per contract
        breakeven = strike + last_price if option_type == 'CALL' else strike - last_price
        
        # Volume analysis
        liquidity_score = self._calculate_liquidity_score(volume, open_interest)
        
        return {
            'strike': strike,
            'last_price': last_price,
            'bid': bid,
            'ask': ask,
            'spread': spread,
            'spread_pct': (spread / mid_price * 100) if mid_price > 0 else 0,
            'volume': volume,
            'open_interest': open_interest,
            'liquidity_score': liquidity_score,
            
            # Greeks
            'delta': delta,
            'gamma': gamma,
            'theta': theta,
            'vega': vega,
            'implied_volatility': implied_vol * 100 if implied_vol > 0 else 0,  # Convert to %
            
            # Probabilities
            'itm_probability': itm_probability * 100,  # Convert to %
            'probability_of_profit': pop * 100,  # Convert to %
            
            # Risk metrics
            'max_loss_per_contract': max_loss,
            'breakeven': breakeven,
            'days_to_expiration': dte,
            
            # Trade analysis
            'option_type': option_type,
            'in_the_money': self._is_itm(strike, stock_price, option_type),
            'time_value': self._calculate_time_value(last_price, strike, stock_price, option_type),
            'intrinsic_value': self._calculate_intrinsic_value(strike, stock_price, option_type),
            
            # Professional metrics
            'expected_move': self._calculate_expected_move(stock_price, implied_vol, dte),
            'premium_decay_per_day': theta if theta != 0 else (last_price / dte) if dte > 0 else 0
        }
    
    def _calculate_itm_probability(self, delta: float, option_type: str) -> float:
        """Calculate probability of being in the money"""
        if option_type == 'CALL':
            return max(0, min(1, delta))  # Call delta = ITM probability
        else:  # PUT
            return max(0, min(1, -delta + 1))  # Put delta = -(1 - ITM probability)
    
    def _calculate_probability_of_profit(self, premium: float, strike: float, 
                                        stock_price: float, dte: int, iv: float, 
                                        option_type: str) -> float:
        """Simplified probability of profit calculation"""
        if premium <= 0 or dte <= 0:
            return 0.1  # Default 10%
        
        # Breakeven calculation
        breakeven = strike + premium if option_type == 'CALL' else strike - premium
        
        # Distance from current price
        distance_pct = abs(breakeven - stock_price) / stock_price
        
        # Adjust for time and volatility
        time_factor = math.sqrt(dte / 365) if iv > 0 else 1
        volatility_factor = iv if iv > 0 else 0.3  # Default 30% IV
        
        # Simplified POP calculation
        z_score = distance_pct / (volatility_factor * time_factor)
        pop = 1 - self._normal_cdf(z_score) if option_type == 'CALL' else self._normal_cdf(z_score)
        
        return max(0.1, min(0.9, pop))  # Clamp between 10% and 90%
    
    def _normal_cdf(self, x: float) -> float:
        """Normal distribution CDF approximation"""
        return 0.5 * (1 + math.erf(x / math.sqrt(2)))
    
    def _calculate_liquidity_score(self, volume: int, open_interest: int) -> str:
        """Calculate liquidity score like Robinhood"""
        if volume >= 1000 and open_interest >= 1000:
            return "Very High"
        elif volume >= 100 and open_interest >= 100:
            return "High"
        elif volume >= 10 and open_interest >= 10:
            return "Medium"
        else:
            return "Low"
    
    def _is_itm(self, strike: float, stock_price: float, option_type: str) -> bool:
        """Check if option is in the money"""
        if option_type == 'CALL':
            return stock_price > strike
        else:  # PUT
            return stock_price < strike
    
    def _calculate_time_value(self, premium: float, strike: float, 
                            stock_price: float, option_type: str) -> float:
        """Calculate time value component of premium"""
        intrinsic = self._calculate_intrinsic_value(strike, stock_price, option_type)
        return max(0, premium - intrinsic)
    
    def _calculate_intrinsic_value(self, strike: float, stock_price: float, option_type: str) -> float:
        """Calculate intrinsic value"""
        if option_type == 'CALL':
            return max(0, stock_price - strike)
        else:  # PUT
            return max(0, strike - stock_price)
    
    def _calculate_expected_move(self, stock_price: float, iv: float, dte: int) -> float:
        """Calculate expected move based on implied volatility"""
        if iv <= 0 or dte <= 0:
            return stock_price * 0.05  # Default 5% move
        
        # Expected move = stock_price * IV * sqrt(DTE/365)
        return stock_price * iv * math.sqrt(dte / 365)
    
    def _get_strikes_around_money(self, chain: Dict, atm_strike: float, count: int) -> List[float]:
        """Get strikes around the money"""
        all_strikes = set(chain.calls['strike'].tolist() + chain.puts['strike'].tolist())
        sorted_strikes = sorted(list(all_strikes))
        
        # Find ATM position
        atm_index = 0
        for i, strike in enumerate(sorted_strikes):
            if abs(strike - atm_strike) < 0.01:
                atm_index = i
                break
        
        # Get strikes around ATM
        start = max(0, atm_index - count // 2)
        end = min(len(sorted_strikes), start + count)
        
        return sorted_strikes[start:end]
    
    def _find_atm_strike(self, stock_price: float) -> float:
        """Find at-the-money strike (round to nearest $5 for most stocks)"""
        if stock_price < 50:
            return round(stock_price)
        elif stock_price < 200:
            return round(stock_price / 5) * 5
        else:
            return round(stock_price / 10) * 10
    
    def _get_option_by_strike(self, options_df, strike: float) -> Optional[Dict]:
        """Get option data by strike"""
        if options_df.empty:
            return None
        
        option_row = options_df[options_df['strike'] == strike]
        if option_row.empty:
            return None
        
        return option_row.iloc[0].to_dict()
    
    def _find_closest_expiry(self, expirations: List[str], target_date: datetime) -> Optional[str]:
        """Find expiration closest to target"""
        if not expirations:
            return None
        
        closest = None
        min_diff = float('inf')
        
        for expiry in expirations[:6]:
            try:
                expiry_date = datetime.strptime(expiry, '%Y-%m-%d')
                diff = abs((expiry_date - target_date).days)
                if diff < min_diff:
                    min_diff = diff
                    closest = expiry
            except:
                continue
        
        return closest
    
    def _calculate_dte(self, expiry: str) -> int:
        """Calculate days to expiration"""
        try:
            expiry_date = datetime.strptime(expiry, '%Y-%m-%d')
            return (expiry_date - datetime.now()).days
        except:
            return 0
    
    def format_robinhood_style_report(self, symbol: str, days_out: int = 30) -> str:
        """Generate Robinhood-style formatted report"""
        data = self.get_robinhood_style_chain(symbol, days_out)
        
        if 'error' in data:
            return f"❌ Error: {data['error']}"
        
        report = f"📊 **ROBINHOOD-STYLE OPTIONS ANALYSIS** 📊\n\n"
        report += f"**{symbol}** ${data['current_price']:.2f} | {data['expiration']} ({data['dte']} DTE) | {data['timestamp']}\n\n"
        
        # Calls section - Robinhood style
        report += "📈 **CALLS**\n"
        report += "Strike | Price | Breakeven | POP | Volume | Signal\n"
        report += "---|---|---|---|---|---\n"
        
        for call in data['calls']:
            # Visual indicators
            price_emoji = "🟢" if call['in_the_money'] else "🔴"
            pop_emoji = "✅" if call['probability_of_profit'] >= 50 else "⚠️"
            volume_emoji = "🔥" if call['volume'] >= 500 else "📊" if call['volume'] >= 100 else "📉"
            
            # Format for readability
            price_str = f"${call['last_price']:.2f}"
            breakeven_str = f"${call['breakeven']:.2f}"
            pop_str = f"{call['probability_of_profit']:.0f}%"
            volume_str = f"{call['volume']:,}" if call['volume'] > 0 else "Low"
            
            # Trading signal
            if call['probability_of_profit'] >= 60 and call['volume'] >= 100:
                signal = "🚀 STRONG"
            elif call['probability_of_profit'] >= 40:
                signal = "📈 GOOD"
            else:
                signal = "⏸️ WAIT"
            
            report += f"${call['strike']:.0f} | {price_emoji} {price_str} | {breakeven_str} | {pop_emoji} {pop_str} | {volume_emoji} {volume_str} | {signal}\n"
        
        report += "\n"
        
        # Puts section - Robinhood style
        report += "📉 **PUTS**\n"
        report += "Strike | Price | Breakeven | POP | Volume | Signal\n"
        report += "---|---|---|---|---|---\n"
        
        for put in data['puts']:
            # Visual indicators
            price_emoji = "🟢" if put['in_the_money'] else "🔴"
            pop_emoji = "✅" if put['probability_of_profit'] >= 50 else "⚠️"
            volume_emoji = "🔥" if put['volume'] >= 500 else "📊" if put['volume'] >= 100 else "📉"
            
            # Format for readability
            price_str = f"${put['last_price']:.2f}"
            breakeven_str = f"${put['breakeven']:.2f}"
            pop_str = f"{put['probability_of_profit']:.0f}%"
            volume_str = f"{put['volume']:,}" if put['volume'] > 0 else "Low"
            
            # Trading signal
            if put['probability_of_profit'] >= 60 and put['volume'] >= 100:
                signal = "🛡️ PROTECT"
            elif put['probability_of_profit'] >= 40:
                signal = "📉 GOOD"
            else:
                signal = "⏸️ WAIT"
            
            report += f"${put['strike']:.0f} | {price_emoji} {price_str} | {breakeven_str} | {pop_emoji} {pop_str} | {volume_emoji} {volume_str} | {signal}\n"
        
        report += "\n"
        
        # Market analysis
        report += "📊 **MARKET ANALYSIS**\n"
        if data['calls']:
            expected_move = data['calls'][0]['expected_move']
            report += f"Expected Move: ±${expected_move:.2f} ({expected_move/data['current_price']*100:.1f}%)\n"
        
        report += f"Data Source: Yahoo Finance (15-min delayed)\n"
        report += "● = In the Money | ○ = Out of the Money\n"
        
        return report

# Test the Robinhood-style calculator
if __name__ == "__main__":
    calculator = RobinhoodStylePricing()
    
    # Test with popular symbols
    symbols = ['SPY', 'AAPL', 'TSLA']
    
    for symbol in symbols:
        print(f"\n{'='*80}")
        print(calculator.format_robinhood_style_report(symbol, days_out=30))
        print(f"{'='*80}\n")
