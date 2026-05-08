#!/usr/bin/env python3

# Enhanced Alpaca Paper Trader with Whole Stock Logic and Auto-Selling
import alpaca_trade_api as tradeapi
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging
import time

class EnhancedAlpacaPaperTrader:
    """Enhanced paper trading with whole stock logic and auto-selling"""
    
    def __init__(self):
        """Initialize Alpaca paper trading client"""
        self.api_key = "PKY7UOZU5S7AZZ4QIH2BJ5F52X"
        self.api_secret = "J8iDXzCoHhrvpPK8yTXu3dRP1FybmAVW77QWZDPyzJs3"
        self.base_url = "https://paper-api.alpaca.markets"
        self.open_positions = {}  # Track open positions for auto-selling
        
        try:
            # Test with real credentials
            self.alpaca = tradeapi.REST(
                key_id=self.api_key,
                secret_key=self.api_secret,
                base_url=self.base_url,
                api_version='v2'
            )
            
            # Test connection
            account = self.alpaca.get_account()
            print(f"✅ Enhanced Alpaca Paper Trading Connected")
            print(f"   Account ID: {account.id}")
            print(f"   Buying Power: ${float(account.buying_power):,.2f}")
            print(f"   Portfolio Value: ${float(account.portfolio_value):,.2f}")
            
        except Exception as e:
            print(f"❌ Alpaca Connection Error: {e}")
            self.alpaca = None
    
    def calculate_position_size(self, symbol: str, entry_price: float, available_capital: float, confidence: float) -> Dict:
        """Calculate position size with whole stock logic"""
        
        # Check if we can afford at least 1 whole stock
        can_buy_whole = available_capital >= entry_price
        
        if can_buy_whole:
            # Buy 1 whole stock
            quantity = 1
            position_cost = entry_price
            reasoning = "WHOLE STOCK - Can afford 1 full share"
        else:
            # Buy shares with available capital (only if AI is confident)
            if confidence >= 85:  # High confidence threshold for fractional shares
                quantity = int(available_capital / entry_price)
                position_cost = quantity * entry_price
                reasoning = f"FRACTIONAL SHARES - High confidence ({confidence}%), can't afford whole stock"
            else:
                return {
                    "quantity": 0,
                    "position_cost": 0,
                    "reasoning": f"SKIP - Can't afford whole stock and confidence {confidence}% below 85% threshold"
                }
        
        return {
            "quantity": quantity,
            "position_cost": position_cost,
            "reasoning": reasoning
        }
    
    def execute_buy(self, symbol: str, quantity: int, price: float = None, confidence: float = 75, take_profit: float = None, stop_loss: float = None) -> Dict:
        """Execute a paper buy order with auto-selling parameters"""
        if not self.alpaca:
            return {"success": False, "error": "Alpaca not connected"}
        
        if quantity <= 0:
            return {"success": False, "error": "Invalid quantity"}
        
        try:
            order = self.alpaca.submit_order(
                symbol=symbol,
                qty=quantity,
                side='buy',
                type='market',
                time_in_force='day'
            )
            
            # Track position for auto-selling
            self.open_positions[symbol] = {
                "quantity": quantity,
                "entry_price": price,
                "take_profit": take_profit or (price * 1.20),  # 20% profit target
                "stop_loss": stop_loss or (price * 0.90),      # 10% stop loss
                "entry_time": datetime.now(),
                "order_id": order.id,
                "confidence": confidence
            }
            
            print(f"✅ BUY ORDER PLACED: {symbol} {quantity} @ ${price}")
            print(f"   📊 Position Type: {'WHOLE STOCK' if quantity == 1 else f'{quantity} SHARES'}")
            print(f"   🎯 Take Profit: ${self.open_positions[symbol]['take_profit']:.2f}")
            print(f"   🛡️ Stop Loss: ${self.open_positions[symbol]['stop_loss']:.2f}")
            
            return {
                "success": True,
                "order_id": order.id,
                "symbol": symbol,
                "quantity": quantity,
                "side": "buy",
                "price": price,
                "status": order.status,
                "timestamp": datetime.now().isoformat(),
                "paper_trade": True,
                "platform": "Alpaca",
                "take_profit": self.open_positions[symbol]['take_profit'],
                "stop_loss": self.open_positions[symbol]['stop_loss']
            }
            
        except Exception as e:
            print(f"❌ BUY ORDER FAILED: {e}")
            return {"success": False, "error": str(e)}
    
    def execute_sell(self, symbol: str, quantity: int, price: float = None, reason: str = "Manual sell") -> Dict:
        """Execute a paper sell order"""
        if not self.alpaca:
            return {"success": False, "error": "Alpaca not connected"}
        
        try:
            order = self.alpaca.submit_order(
                symbol=symbol,
                qty=quantity,
                side='sell',
                type='market',
                time_in_force='day'
            )
            
            # Remove from open positions
            if symbol in self.open_positions:
                position = self.open_positions[symbol]
                pnl = (price - position['entry_price']) * quantity
                pnl_percent = ((price - position['entry_price']) / position['entry_price']) * 100
                
                print(f"✅ SELL ORDER PLACED: {symbol} {quantity} @ ${price}")
                print(f"   📊 Sell Reason: {reason}")
                print(f"   💰 P&L: ${pnl:.2f} ({pnl_percent:+.2f}%)")
                print(f"   ⏱️ Hold Time: {datetime.now() - position['entry_time']}")
                
                del self.open_positions[symbol]
            
            return {
                "success": True,
                "order_id": order.id,
                "symbol": symbol,
                "quantity": quantity,
                "side": "sell",
                "price": price,
                "status": order.status,
                "timestamp": datetime.now().isoformat(),
                "paper_trade": True,
                "platform": "Alpaca",
                "reason": reason
            }
            
        except Exception as e:
            print(f"❌ SELL ORDER FAILED: {e}")
            return {"success": False, "error": str(e)}
    
    def check_exit_signals(self, current_prices: Dict[str, float]) -> List[Dict]:
        """Check for exit signals and execute auto-sells"""
        exit_signals = []
        
        for symbol, position in list(self.open_positions.items()):
            if symbol not in current_prices:
                continue
                
            current_price = current_prices[symbol]
            entry_price = position['entry_price']
            take_profit = position['take_profit']
            stop_loss = position['stop_loss']
            
            # Check take profit
            if current_price >= take_profit:
                result = self.execute_sell(symbol, position['quantity'], current_price, f"TAKE PROFIT - Target ${take_profit:.2f} reached")
                if result['success']:
                    exit_signals.append({
                        "symbol": symbol,
                        "action": "SELL",
                        "reason": "TAKE PROFIT",
                        "price": current_price,
                        "pnl_percent": ((current_price - entry_price) / entry_price) * 100
                    })
            
            # Check stop loss
            elif current_price <= stop_loss:
                result = self.execute_sell(symbol, position['quantity'], current_price, f"STOP LOSS - Limit ${stop_loss:.2f} breached")
                if result['success']:
                    exit_signals.append({
                        "symbol": symbol,
                        "action": "SELL",
                        "reason": "STOP LOSS",
                        "price": current_price,
                        "pnl_percent": ((current_price - entry_price) / entry_price) * 100
                    })
            
            # Check time-based exit (hold max 7 days)
            elif datetime.now() - position['entry_time'] > timedelta(days=7):
                result = self.execute_sell(symbol, position['quantity'], current_price, "TIME EXIT - 7 day limit reached")
                if result['success']:
                    exit_signals.append({
                        "symbol": symbol,
                        "action": "SELL",
                        "reason": "TIME EXIT",
                        "price": current_price,
                        "pnl_percent": ((current_price - entry_price) / entry_price) * 100
                    })
        
        return exit_signals
    
    def get_positions(self) -> List[Dict]:
        """Get current open positions"""
        positions = []
        for symbol, position in self.open_positions.items():
            positions.append({
                "symbol": symbol,
                "quantity": position["quantity"],
                "entry_price": position["entry_price"],
                "take_profit": position["take_profit"],
                "stop_loss": position["stop_loss"],
                "entry_time": position["entry_time"].isoformat(),
                "confidence": position["confidence"]
            })
        return positions
    
    def get_account(self) -> Dict:
        """Get account information"""
        if not self.alpaca:
            return {}
        
        try:
            account = self.alpaca.get_account()
            return {
                "account_id": account.id,
                "buying_power": float(account.buying_power),
                "portfolio_value": float(account.portfolio_value),
                "cash": float(account.cash),
                "equity": float(account.equity)
            }
        except Exception as e:
            print(f"❌ Account info failed: {e}")
            return {}
