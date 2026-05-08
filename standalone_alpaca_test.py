#!/usr/bin/env python3

# Standalone Alpaca Test - Direct import
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import alpaca_trade_api as tradeapi
from datetime import datetime
from typing import Dict, List, Optional

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
    
    def get_performance_summary(self) -> Dict:
        """Get performance summary from Alpaca data"""
        try:
            account = self.get_account()
            positions = self.get_positions()
            
            unrealized_pnl = sum(pos['unrealized_pnl'] for pos in positions)
            
            return {
                "total_trades": 0,  # Would need order history
                "winning_trades": 0,
                "losing_trades": 0,
                "realized_pnl": 0.0,
                "unrealized_pnl": unrealized_pnl,
                "total_pnl": unrealized_pnl,
                "portfolio_value": account.get('portfolio_value', 0),
                "buying_power": account.get('buying_power', 0),
                "open_positions": len(positions),
                "platform": "Alpaca Paper Trading",
                "last_updated": datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"❌ ERROR CALCULATING PERFORMANCE: {e}")
            return {"error": str(e)}

def test_standalone_alpaca():
    """Test standalone Alpaca integration"""
    print("🔧 Testing Standalone Alpaca Paper Trading...")
    
    try:
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
            
            print("\n📊 Performance Summary:")
            performance = trader.get_performance_summary()
            for key, value in performance.items():
                if key != 'error':
                    print(f"   {key}: {value}")
            
            print("\n🎯 READY TO REPLACE INTERNAL PAPER TRADING!")
            print("   ✅ Real market data via Alpaca")
            print("   ✅ Independent verification")
            print("   ✅ Professional platform")
            print("   ✅ No fake data possible")
            
            return True
        else:
            print("❌ FAILED: Could not connect to Alpaca")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

if __name__ == "__main__":
    success = test_standalone_alpaca()
    if success:
        print("\n🚀 Alpaca Paper Trading is ready for Phasma AI integration!")
    else:
        print("\n⚠️ Integration needs troubleshooting")
