"""Test options profit calculations and display"""

from core.config import PhasmaConfig
from engines.options_engine import PhasmaOptionsEngine
import yfinance as yf
import asyncio

async def test_options():
    # Initialize
    config = PhasmaConfig()
    options_engine = PhasmaOptionsEngine(config)

    # Test with a high-volatility stock
    symbol = "TSLA"
    print(f"Testing options for {symbol}...")

    # Get current price
    ticker = yf.Ticker(symbol)
    current_price = ticker.history(period="1d")['Close'].iloc[-1]
    print(f"Current price: ${current_price:.2f}")

    # Generate signals
    signals = await options_engine.generate_signals([symbol])

    if signals:
        signal = signals[0]
        print("\n=== OPTIONS SIGNAL ===")
        print(f"Symbol: {signal['underlying']}")
        print(f"Action: {signal['action']}")
        print(f"Strike: ${signal['strike']:.2f}")
        print(f"Entry Price: ${signal['entry_price']:.2f}")
        print(f"Expected Stock Move: {signal['expected_stock_move']:.1f}%")
        print(f"Expected Option Return: {signal['expected_option_return']:.0f}%")
        print(f"Optimal Hold Time: {signal['optimal_hold_days']} days")
        print(f"Take Profit: ${signal['take_profit']:.2f} (+{((signal['take_profit']-signal['entry_price'])/signal['entry_price']*100):.1f}%)")
        print(f"Stop Loss: ${signal['stop_loss']:.2f} (-{((signal['entry_price']-signal['stop_loss'])/signal['entry_price']*100):.1f}%)")
        
        # Calculate potential profit
        contracts = 1
        cost = signal['entry_price'] * 100 * contracts
        max_profit = (signal['take_profit'] - signal['entry_price']) * 100 * contracts
        print(f"\nCost for 1 contract: ${cost:.2f}")
        print(f"Max profit: ${max_profit:.2f}")
        print(f"Return on capital: {max_profit/cost*100:.1f}%")
    else:
        print("No signals generated")

# Run the test
if __name__ == "__main__":
    asyncio.run(test_options())
