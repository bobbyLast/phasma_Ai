"""
Portfolio Dashboard - Real-time Position Monitoring
Implements AI Feedback: Portfolio snapshot and Greeks exposure tracking
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional

class PortfolioDashboard:
    """Real-time portfolio monitoring and Greeks exposure"""
    
    def __init__(self, trade_db=None, options_engine=None, performance_tracker=None, config=None):
        """Initialize portfolio dashboard"""
        self.trade_db = trade_db
        self.options_engine = options_engine
        self.performance_tracker = performance_tracker
        self.config = config
        self.logger = logging.getLogger(__name__)
        
    def get_open_positions(self) -> List[Dict]:
        """Get all open positions"""
        if not self.trade_db:
            return []
            
        try:
            return self.trade_db.get_open_positions()
        except Exception as e:
            self.logger.error(f"Error getting open positions: {e}")
            return []
    
    def calculate_total_value(self) -> float:
        """Calculate total portfolio value"""
        try:
            positions = self.get_open_positions()
            return sum(p.get('current_value', 0) for p in positions)
        except Exception as e:
            self.logger.error(f"Error calculating total value: {e}")
            return 0.0
    
    def calculate_daily_pnl(self) -> float:
        """Calculate today's P&L"""
        try:
            positions = self.get_open_positions()
            return sum(p.get('daily_pnl', 0) for p in positions)
        except Exception as e:
            self.logger.error(f"Error calculating daily PnL: {e}")
            return 0.0
    
    def calculate_greeks_exposure(self) -> Dict:
        """
        Calculate portfolio-level Greeks exposure
        
        Returns:
            Dictionary with total delta, gamma, theta, vega, rho
        """
        try:
            positions = self.get_open_positions()
            
            greeks = {
                'total_delta': 0.0,
                'total_gamma': 0.0,
                'total_theta': 0.0,
                'total_vega': 0.0,
                'total_rho': 0.0,
                'position_count': len(positions)
            }
            
            for position in positions:
                quantity = position.get('quantity', 0)
                
                # Multiply Greeks by quantity for position exposure
                greeks['total_delta'] += position.get('delta', 0) * quantity
                greeks['total_gamma'] += position.get('gamma', 0) * quantity
                greeks['total_theta'] += position.get('theta', 0) * quantity
                greeks['total_vega'] += position.get('vega', 0) * quantity
                greeks['total_rho'] += position.get('rho', 0) * quantity
            
            return greeks
            
        except Exception as e:
            self.logger.error(f"Error calculating Greeks exposure: {e}")
            return {
                'total_delta': 0.0,
                'total_gamma': 0.0,
                'total_theta': 0.0,
                'total_vega': 0.0,
                'total_rho': 0.0,
                'position_count': 0
            }
    
    def calculate_sector_exposure(self) -> Dict:
        """Calculate exposure by sector"""
        try:
            positions = self.get_open_positions()
            sectors = {}
            
            for position in positions:
                sector = position.get('sector', 'Unknown')
                value = position.get('current_value', 0)
                
                if sector in sectors:
                    sectors[sector] += value
                else:
                    sectors[sector] = value
            
            # Calculate percentages
            total_value = sum(sectors.values())
            if total_value > 0:
                return {
                    sector: (value / total_value) * 100 
                    for sector, value in sectors.items()
                }
            
            return sectors
            
        except Exception as e:
            self.logger.error(f"Error calculating sector exposure: {e}")
            return {}
    
    def get_portfolio_snapshot(self) -> Dict:
        """
        Get comprehensive portfolio snapshot
        
        Returns:
            Complete portfolio status dictionary
        """
        snapshot = {
            'timestamp': datetime.now().isoformat(),
            'bankroll': self.config.get('bankroll') if self.config else 10000,
            'open_positions': self.get_open_positions(),
            'position_count': len(self.get_open_positions()),
            'total_value': self.calculate_total_value(),
            'daily_pnl': self.calculate_daily_pnl(),
            'greeks_exposure': self.calculate_greeks_exposure(),
            'sector_exposure': self.calculate_sector_exposure()
        }
        
        # Add performance metrics if available
        if self.performance_tracker:
            try:
                snapshot['win_rate_30d'] = self.performance_tracker.calculate_win_rate(30)
                snapshot['profit_factor_30d'] = self.performance_tracker.calculate_profit_factor(30)
            except Exception as e:
                self.logger.error(f"Error adding performance metrics: {e}")
        
        return snapshot
    
    def print_portfolio_dashboard(self):
        """Print formatted portfolio dashboard"""
        snapshot = self.get_portfolio_snapshot()
        greeks = snapshot['greeks_exposure']
        
        print("\n" + "="*70)
        print("PORTFOLIO DASHBOARD")
        print("="*70)
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"\nBANKROLL: ${snapshot['bankroll']:,.2f}")
        print(f"Total Portfolio Value: ${snapshot['total_value']:,.2f}")
        print(f"Daily P&L: ${snapshot['daily_pnl']:+,.2f}")
        
        print(f"\nPOSITIONS: {snapshot['position_count']} open")
        
        # Show individual positions
        if snapshot['open_positions']:
            print("\n" + "-"*70)
            print(f"{'Symbol':<10} {'Type':<10} {'Qty':<8} {'Entry':<10} {'Current':<10} {'P&L':<10}")
            print("-"*70)
            
            for pos in snapshot['open_positions'][:10]:  # Show first 10
                symbol = pos.get('symbol', 'N/A')[:10]
                pos_type = pos.get('type', 'N/A')[:10]
                qty = pos.get('quantity', 0)
                entry = pos.get('entry_price', 0)
                current = pos.get('current_price', 0)
                pnl = pos.get('pnl', 0)
                
                print(f"{symbol:<10} {pos_type:<10} {qty:<8.2f} ${entry:<9.2f} ${current:<9.2f} ${pnl:+9.2f}")
        
        print("\n" + "-"*70)
        print("GREEKS EXPOSURE")
        print("-"*70)
        print(f"Total Delta: {greeks['total_delta']:+.4f}")
        print(f"Total Gamma: {greeks['total_gamma']:+.4f}")
        print(f"Total Theta: {greeks['total_theta']:+.2f} (daily decay)")
        print(f"Total Vega:  {greeks['total_vega']:+.2f} (per 1% IV move)")
        print(f"Total Rho:   {greeks['total_rho']:+.2f} (per 1% rate move)")
        
        # Sector exposure
        sectors = snapshot['sector_exposure']
        if sectors:
            print("\n" + "-"*70)
            print("SECTOR EXPOSURE")
            print("-"*70)
            for sector, pct in sorted(sectors.items(), key=lambda x: x[1], reverse=True):
                print(f"{sector:<30} {pct:>6.1f}%")
        
        # Performance metrics
        if 'win_rate_30d' in snapshot:
            print("\n" + "-"*70)
            print("PERFORMANCE (Last 30 Days)")
            print("-"*70)
            print(f"Win Rate: {snapshot['win_rate_30d']:.1%}")
            print(f"Profit Factor: {snapshot['profit_factor_30d']:.2f}")
        
        print("="*70 + "\n")
    
    def get_position_summary(self, symbol: str) -> Optional[Dict]:
        """Get detailed summary for specific position"""
        positions = self.get_open_positions()
        
        for pos in positions:
            if pos.get('symbol') == symbol:
                return {
                    'symbol': symbol,
                    'type': pos.get('type'),
                    'quantity': pos.get('quantity'),
                    'entry_price': pos.get('entry_price'),
                    'current_price': pos.get('current_price'),
                    'pnl': pos.get('pnl'),
                    'pnl_pct': pos.get('pnl_pct'),
                    'delta': pos.get('delta'),
                    'gamma': pos.get('gamma'),
                    'theta': pos.get('theta'),
                    'vega': pos.get('vega'),
                    'stop_loss': pos.get('stop_loss'),
                    'profit_target': pos.get('profit_target'),
                    'days_held': pos.get('days_held', 0)
                }
        
        return None
    
    def check_risk_limits(self) -> Dict:
        """Check if portfolio is within risk limits"""
        snapshot = self.get_portfolio_snapshot()
        greeks = snapshot['greeks_exposure']
        sectors = snapshot['sector_exposure']
        
        warnings = []
        
        # Check delta exposure
        if abs(greeks['total_delta']) > 10:
            warnings.append(f"High delta exposure: {greeks['total_delta']:+.2f}")
        
        # Check theta decay
        if greeks['total_theta'] < -50:
            warnings.append(f"High theta decay: ${greeks['total_theta']:.2f}/day")
        
        # Check sector concentration
        for sector, pct in sectors.items():
            if pct > 40:
                warnings.append(f"High {sector} concentration: {pct:.1f}%")
        
        # Check position count
        if snapshot['position_count'] > 10:
            warnings.append(f"Many open positions: {snapshot['position_count']}")
        
        return {
            'within_limits': len(warnings) == 0,
            'warnings': warnings,
            'timestamp': datetime.now().isoformat()
        }
