"""
Alpaca Paper Trading Integration
Real paper trading with Alpaca's API to replace internal simulation
"""

import alpaca_trade_api as tradeapi
import os
from datetime import datetime
from typing import Dict, List, Optional
import logging

class AlpacaPaperTrader:
    """Real paper trading using Alpaca's API"""
    
    def __init__(self):
        """Initialize Alpaca paper trading client"""
        self.api_key = "PKY7UOZU5S7AZZ4QIH2BJ5F52X"
        self.api_secret = "J8iDXzCoHhrvpPK8yTXu3dRP1FybmAVW77QWZDPyzJs3"
        self.base_url = "https://paper-api.alpaca.markets"
        
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
            print(f"✅ Alpaca Paper Trading Connected")
            print(f"   Account ID: {account.id}")
            print(f"   Buying Power: ${float(account.buying_power):,.2f}")
            print(f"   Portfolio Value: ${float(account.portfolio_value):,.2f}")
            
        except Exception as e:
            print(f"❌ Alpaca Connection Error: {e}")
            self.alpaca = None
    
    def execute_buy(self, symbol: str, quantity: int, price: float = None) -> Dict:
        """Execute a paper buy order"""
        if not self.alpaca:
            return {"success": False, "error": "Alpaca not connected"}
        
        try:
            order = self.alpaca.submit_order(
                symbol=symbol,
                qty=quantity,
                side='buy',
                type='market' if price is None else 'limit',
                time_in_force='day',
                limit_price=price
            )
            
            result = {
                "success": True,
                "order_id": order.id,
                "symbol": symbol,
                "quantity": quantity,
                "side": "buy",
                "price": float(order.limit_price) if order.limit_price else "market",
                "status": order.status,
                "timestamp": datetime.now().isoformat(),
                "paper_trade": True,
                "platform": "Alpaca"
            }
            
            print(f"✅ BUY ORDER PLACED: {symbol} {quantity} @ {result['price']}")
            return result
            
        except Exception as e:
            error_result = {
                "success": False,
                "error": str(e),
                "symbol": symbol,
                "quantity": quantity
            }
            print(f"❌ BUY ORDER FAILED: {symbol} - {e}")
            return error_result
    
    def execute_sell(self, symbol: str, quantity: int = None, price: float = None) -> Dict:
        """Execute a paper sell order"""
        if not self.alpaca:
            return {"success": False, "error": "Alpaca not connected"}
        
        try:
            order = self.alpaca.submit_order(
                symbol=symbol,
                qty=quantity,
                side='sell',
                type='market' if price is None else 'limit',
                time_in_force='day',
                limit_price=price
            )
            
            result = {
                "success": True,
                "order_id": order.id,
                "symbol": symbol,
                "quantity": quantity,
                "side": "sell",
                "price": float(order.limit_price) if order.limit_price else "market",
                "status": order.status,
                "timestamp": datetime.now().isoformat(),
                "paper_trade": True,
                "platform": "Alpaca"
            }
            
            print(f"✅ SELL ORDER PLACED: {symbol} {quantity} @ {result['price']}")
            return result
            
        except Exception as e:
            error_result = {
                "success": False,
                "error": str(e),
                "symbol": symbol,
                "quantity": quantity
            }
            print(f"❌ SELL ORDER FAILED: {symbol} - {e}")
            return error_result
    
    def get_positions(self) -> List[Dict]:
        """Get current positions"""
        if not self.alpaca:
            return []
        
        try:
            positions = self.alpaca.list_positions()
            result = []
            
            for pos in positions:
                result.append({
                    "symbol": pos.symbol,
                    "quantity": int(pos.qty),
                    "avg_cost": float(pos.avg_entry_price),
                    "current_price": float(pos.current_price),
                    "market_value": float(pos.market_value),
                    "unrealized_pnl": float(pos.unrealized_pl),
                    "unrealized_pct": float(pos.unrealized_plpc),
                    "side": pos.side
                })
            
            return result
            
        except Exception as e:
            print(f"❌ ERROR GETTING POSITIONS: {e}")
            return []
    
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
                "equity": float(account.equity),
                "initial_margin": float(account.initial_margin),
                "maintenance_margin": float(account.maintenance_margin),
                "daytrade_count": int(account.daytrade_count),
                "pattern_day_trader": account.pattern_day_trader
            }
        except Exception as e:
            print(f"❌ ERROR GETTING ACCOUNT: {e}")
            return {}
    
    def get_order_history(self, limit: int = 50) -> List[Dict]:
        """Get order history"""
        if not self.alpaca:
            return []
        
        try:
            orders = self.alpaca.list_orders(status='all', limit=limit)
            result = []
            
            for order in orders:
                result.append({
                    "order_id": order.id,
                    "symbol": order.symbol,
                    "quantity": int(order.qty),
                    "side": order.side,
                    "type": order.type,
                    "status": order.status,
                    "price": float(order.limit_price) if order.limit_price else "market",
                    "filled_qty": int(order.filled_qty) or 0,
                    "filled_price": float(order.filled_avg_price) if order.filled_avg_price else None,
                    "created_at": order.created_at,
                    "updated_at": order.updated_at,
                    "canceled_at": order.canceled_at
                })
            
            return result
            
        except Exception as e:
            print(f"❌ ERROR GETTING ORDERS: {e}")
            return []
    
    def cancel_order(self, order_id: str) -> Dict:
        """Cancel an order"""
        if not self.alpaca:
            return {"success": False, "error": "Alpaca not connected"}
        
        try:
            self.alpaca.cancel_order(order_id)
            return {"success": True, "order_id": order_id}
        except Exception as e:
            return {"success": False, "error": str(e), "order_id": order_id}
    
    def get_performance_summary(self) -> Dict:
        """Get performance summary from Alpaca data"""
        try:
            account = self.get_account()
            positions = self.get_positions()
            orders = self.get_order_history()
            
            # Calculate realized P&L from closed positions
            realized_pnl = 0.0
            winning_trades = 0
            losing_trades = 0
            total_trades = 0
            
            for order in orders:
                if order['status'] == 'filled' and order['filled_qty'] > 0:
                    total_trades += 1
                    # This is simplified - would need more complex logic for actual P&L
                    # For now, count trades as separate buy/sell pairs
            
            unrealized_pnl = sum(pos['unrealized_pnl'] for pos in positions)
            
            return {
                "total_trades": total_trades,
                "winning_trades": winning_trades,
                "losing_trades": losing_trades,
                "realized_pnl": realized_pnl,
                "unrealized_pnl": unrealized_pnl,
                "total_pnl": realized_pnl + unrealized_pnl,
                "portfolio_value": account.get('portfolio_value', 0),
                "buying_power": account.get('buying_power', 0),
                "open_positions": len(positions),
                "platform": "Alpaca Paper Trading",
                "last_updated": datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"❌ ERROR CALCULATING PERFORMANCE: {e}")
            return {"error": str(e)}

# Test the connection
if __name__ == "__main__":
    trader = AlpacaPaperTrader()
    if trader.alpaca:
        print("\n📊 Account Info:")
        account = trader.get_account()
        for key, value in account.items():
            print(f"   {key}: {value}")
        
        print("\n📈 Current Positions:")
        positions = trader.get_positions()
        for pos in positions:
            print(f"   {pos['symbol']}: {pos['quantity']} @ ${pos['avg_cost']:.2f} | P&L: ${pos['unrealized_pnl']:+.2f}")
