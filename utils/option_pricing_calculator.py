"""
Option Pricing Calculator - Shows True Trade Costs
Provides realistic pricing examples for analysis (not live trading)
"""

import yfinance as yf
from datetime import datetime, timedelta
from typing import Dict, Optional, List
import math

class OptionPricingCalculator:
    """
    Calculates realistic option trade costs including:
    - Premium costs (per contract)
    - Time decay (theta)
    - Commissions and fees
    - Total capital required
    """
    
    def __init__(self):
        self.commission_per_contract = 0.65  # Typical broker commission
        self.contracts_multiplier = 100  # Options control 100 shares
        
    def get_realistic_option_prices(self, symbol: str, days_out: int = 30) -> Dict:
        """
        Get realistic option pricing for analysis
        Shows what trades would actually cost
        """
        try:
            stock = yf.Ticker(symbol)
            current_price = stock.history(period="1d")['Close'].iloc[-1]
            
            # Get available expirations
            expirations = stock.options
            if not expirations:
                return {'error': f'No options available for {symbol}'}
            
            # Find closest expiration to requested days
            target_date = datetime.now() + timedelta(days=days_out)
            closest_expiry = self._find_closest_expiry(expirations, target_date)
            
            if not closest_expiry:
                return {'error': f'No suitable expiration found for {symbol}'}
            
            # Get option chain
            chain = stock.option_chain(closest_expiry)
            
            # Calculate realistic pricing examples
            pricing_examples = {
                'symbol': symbol,
                'current_stock_price': current_price,
                'expiration_date': closest_expiry,
                'days_to_expiration': self._calculate_dte(closest_expiry),
                'examples': []
            }
            
            # ATM Call example
            atm_call = self._find_atm_option(chain.calls, current_price)
            if atm_call:
                call_example = self._calculate_trade_cost(atm_call, 'CALL', symbol, current_price)
                pricing_examples['examples'].append(call_example)
            
            # OTM Call example (higher strike)
            otm_call = self._find_otm_option(chain.calls, current_price, 0.05)  # 5% OTM
            if otm_call:
                otm_call_example = self._calculate_trade_cost(otm_call, 'CALL', symbol, current_price)
                pricing_examples['examples'].append(otm_call_example)
            
            # ATM Put example
            atm_put = self._find_atm_option(chain.puts, current_price)
            if atm_put:
                put_example = self._calculate_trade_cost(atm_put, 'PUT', symbol, current_price)
                pricing_examples['examples'].append(put_example)
            
            # OTM Put example (lower strike)
            otm_put = self._find_otm_option(chain.puts, current_price, -0.05)  # 5% OTM
            if otm_put:
                otm_put_example = self._calculate_trade_cost(otm_put, 'PUT', symbol, current_price)
                pricing_examples['examples'].append(otm_put_example)
            
            return pricing_examples
            
        except Exception as e:
            return {'error': f'Error calculating option prices: {str(e)}'}
    
    def _calculate_trade_cost(self, option_data, option_type: str, symbol: str, stock_price: float) -> Dict:
        """
        Calculate realistic trade cost for a single option
        """
        # Debug: Print the actual data structure
        print(f"DEBUG: Option data type: {type(option_data)}")
        if hasattr(option_data, 'keys'):
            print(f"DEBUG: Option keys: {list(option_data.keys())}")
        
        # Get realistic execution price (ask for buying, bid for selling)
        # Debug: Print actual values
        ask_price = option_data.get('ask', 0)
        bid_price = option_data.get('bid', 0)
        last_price = option_data.get('lastPrice', 0)
        
        print(f"DEBUG: Premium values - Ask: {ask_price}, Bid: {bid_price}, Last: {last_price}")
        
        # Use ask if available, otherwise last price, filter out zero values
        premium = ask_price if ask_price and ask_price > 0 else last_price if last_price and last_price > 0 else 0
        strike = option_data.get('strike', 0)
        volume = option_data.get('volume', 0)
        open_interest = option_data.get('openInterest', 0)
        
        print(f"DEBUG: Final premium: {premium}, Strike: {strike}, Volume: {volume}")
        
        if premium <= 0:
            return {'error': f'Invalid option premium (ask:{ask_price}, last:{last_price})'}
        
        # Calculate costs for different contract sizes
        contract_sizes = [1, 5, 10]
        trade_examples = []
        
        for contracts in contract_sizes:
            # Premium cost (premium * 100 shares * contracts)
            premium_cost = premium * self.contracts_multiplier * contracts
            
            # Commission costs
            commission_cost = self.commission_per_contract * contracts
            
            # Total cost to enter trade
            total_cost = premium_cost + commission_cost
            
            # Buying power required (margin for naked puts, full premium for calls/covered puts)
            if option_type == 'PUT':
                # Naked put requires margin = 20% of underlying value - OTM amount
                margin_requirement = max(
                    stock_price * self.contracts_multiplier * contracts * 0.20,
                    (stock_price * self.contracts_multiplier - (strike - premium) * self.contracts_multiplier) * contracts
                )
                buying_power = margin_requirement + commission_cost
            else:
                # Call option: just premium + commission
                buying_power = total_cost
            
            # Calculate potential outcomes
            max_loss = total_cost  # Maximum you can lose
            breakeven_price = strike + premium if option_type == 'CALL' else strike - premium
            
            trade_example = {
                'contracts': contracts,
                'premium_per_contract': premium,
                'total_premium_cost': premium_cost,
                'commission_cost': commission_cost,
                'total_cost_to_enter': total_cost,
                'buying_power_required': buying_power,
                'max_loss': max_loss,
                'breakeven_price': breakeven_price,
                'volume': volume,
                'open_interest': open_interest,
                'liquidity_rating': self._rate_liquidity(volume, open_interest)
            }
            trade_examples.append(trade_example)
        
        return {
            'option_type': option_type,
            'strike': strike,
            'premium': premium,
            'trade_examples': trade_examples,
            'greeks': {
                'delta': option_data.get('delta', 'N/A'),
                'gamma': option_data.get('gamma', 'N/A'),
                'theta': option_data.get('theta', 'N/A'),
                'vega': option_data.get('vega', 'N/A')
            },
            'implied_volatility': option_data.get('impliedVolatility', 'N/A')
        }
    
    def _rate_liquidity(self, volume: int, open_interest: int) -> str:
        """Rate option liquidity based on volume and open interest"""
        if volume >= 1000 and open_interest >= 1000:
            return "Excellent - Very liquid"
        elif volume >= 100 and open_interest >= 100:
            return "Good - Reasonably liquid"
        elif volume >= 10 and open_interest >= 10:
            return "Fair - Some liquidity"
        else:
            return "Poor - Limited liquidity"
    
    def _find_closest_expiry(self, expirations: List[str], target_date: datetime) -> Optional[str]:
        """Find expiration date closest to target"""
        if not expirations:
            return None
        
        closest = None
        min_diff = float('inf')
        
        for expiry in expirations[:6]:  # Check first 6 expirations
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
    
    def _find_atm_option(self, options_df, stock_price: float) -> Optional[Dict]:
        """Find at-the-money option"""
        if options_df.empty:
            return None
        
        # Find strike closest to current price
        options_df['strike_diff'] = abs(options_df['strike'] - stock_price)
        atm_row = options_df.loc[options_df['strike_diff'].idxmin()]
        
        return atm_row.to_dict()
    
    def _find_otm_option(self, options_df, stock_price: float, otm_percentage: float) -> Optional[Dict]:
        """Find out-of-the-money option"""
        if options_df.empty:
            return None
        
        if otm_percentage > 0:  # OTM call
            target_strike = stock_price * (1 + otm_percentage)
        else:  # OTM put
            target_strike = stock_price * (1 + otm_percentage)
        
        # Find strike closest to target
        options_df['strike_diff'] = abs(options_df['strike'] - target_strike)
        otm_row = options_df.loc[options_df['strike_diff'].idxmin()]
        
        return otm_row.to_dict()
    
    def generate_pricing_report(self, symbol: str, days_out: int = 30) -> str:
        """Generate human-readable pricing report"""
        pricing_data = self.get_realistic_option_prices(symbol, days_out)
        
        if 'error' in pricing_data:
            return f"❌ Error: {pricing_data['error']}"
        
        report = f"📊 **OPTION PRICING REALITY CHECK** 📊\n\n"
        report += f"**{symbol}** - Stock Price: ${pricing_data['current_stock_price']:.2f}\n"
        report += f"Expiration: {pricing_data['expiration_date']} ({pricing_data['days_to_expiration']} days)\n\n"
        
        for example in pricing_data['examples']:
            if 'error' in example:
                report += f"❌ Error getting option data: {example['error']}\n\n"
                continue
            report += f"🎯 **{example['option_type']} ${example['strike']:.0f}**\n"
            report += f"   Premium: ${example['premium']:.2f} per contract\n"
            report += f"   Liquidity: {example['trade_examples'][0]['liquidity_rating']}\n\n"
            
            for trade in example['trade_examples']:
                report += f"   **{trade['contracts']} contract(s):**\n"
                report += f"   💰 Premium cost: ${trade['total_premium_cost']:.2f}\n"
                report += f"   💸 Commission: ${trade['commission_cost']:.2f}\n"
                report += f"   💳 Total cost: ${trade['total_cost_to_enter']:.2f}\n"
                report += f"   🏦 Buying power needed: ${trade['buying_power_required']:.2f}\n"
                report += f"   ⚠️ Max loss: ${trade['max_loss']:.2f}\n"
                report += f"   📈 Breakeven: ${trade['breakeven_price']:.2f}\n\n"
        
        report += "---\n"
        report += "*Prices are from Yahoo Finance (15-min delayed)\n"
        report += "*Actual execution prices may vary due to bid/ask spreads\n"
        report += "*Commissions are estimates ($0.65/contract typical)\n"
        
        return report

# Test the calculator
if __name__ == "__main__":
    calculator = OptionPricingCalculator()
    
    # Example with a popular stock
    symbols = ['AAPL', 'TSLA', 'SPY', 'NVDA']
    
    for symbol in symbols:
        print(f"\n{'='*60}")
        print(calculator.generate_pricing_report(symbol, days_out=30))
        print(f"{'='*60}\n")
