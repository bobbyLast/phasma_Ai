"""
Portfolio Correlation Tracker - Monitor position correlations and concentration risk
Prevents over-exposure to correlated assets and sectors
"""

import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Optional
import yfinance as yf
from datetime import datetime, timedelta

class CorrelationTracker:
    """Track portfolio correlations and concentration limits"""
    
    def __init__(self, config=None):
        """Initialize correlation tracker"""
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # Default correlation limits
        self.limits = {
            'max_correlation': 0.70,          # Max 0.70 correlation between positions
            'max_sector_concentration': 0.30,  # Max 30% in one sector
            'max_correlated_exposure': 0.50    # Max 50% in highly correlated assets
        }
        
        # Correlation cache
        self.correlation_cache = {}
        self.cache_expiry = timedelta(hours=24)
        
    def check_correlation_limits(
        self,
        new_position: Dict,
        existing_positions: List[Dict]
    ) -> Dict:
        """
        Check if adding new position violates correlation limits
        
        Returns:
            {
                'allowed': bool,
                'reason': str,
                'correlation_report': dict
            }
        """
        try:
            if not existing_positions:
                return {'allowed': True, 'reason': 'No existing positions'}
            
            new_symbol = new_position['symbol']
            new_size = new_position.get('size', new_position.get('position_size', 0))
            
            # Calculate correlations
            correlations = []
            highly_correlated_exposure = 0.0
            total_portfolio_value = sum(
                p.get('current_value', p.get('size', 0))
                for p in existing_positions
            )
            
            for pos in existing_positions:
                pos_symbol = pos['symbol']
                correlation = self._get_correlation(new_symbol, pos_symbol)
                
                correlations.append({
                    'symbol': pos_symbol,
                    'correlation': correlation,
                    'position_size': pos.get('current_value', 0)
                })
                
                # Track highly correlated exposure
                if correlation > self.limits['max_correlation']:
                    pos_value = pos.get('current_value', 0)
                    highly_correlated_exposure += pos_value
            
            # Check correlation limit
            max_corr = max((c['correlation'] for c in correlations), default=0)
            if max_corr > self.limits['max_correlation']:
                highly_correlated_symbol = next(
                    c['symbol'] for c in correlations 
                    if c['correlation'] == max_corr
                )
                
                # Calculate combined exposure
                combined_exposure = (highly_correlated_exposure + new_size) / (total_portfolio_value + new_size)
                
                if combined_exposure > self.limits['max_correlated_exposure']:
                    return {
                        'allowed': False,
                        'reason': f'High correlation with {highly_correlated_symbol}: {max_corr:.2f}',
                        'recommendation': f'Combined correlated exposure {combined_exposure:.1%} exceeds {self.limits["max_correlated_exposure"]:.1%} limit',
                        'correlation_report': correlations
                    }
            
            return {
                'allowed': True,
                'reason': 'Within correlation limits',
                'max_correlation': max_corr,
                'correlation_report': correlations
            }
            
        except Exception as e:
            self.logger.error(f"Error checking correlations: {e}")
            return {
                'allowed': True,  # Default to allow on error
                'reason': f'Error calculating correlations: {e}'
            }
    
    def check_sector_concentration(
        self,
        new_position: Dict,
        existing_positions: List[Dict],
        portfolio_value: float
    ) -> Dict:
        """Check if new position violates sector concentration limits"""
        try:
            new_sector = self._get_sector(new_position['symbol'])
            new_size = new_position.get('size', 0)
            
            # Calculate sector exposures
            sector_exposure = {}
            
            for pos in existing_positions:
                sector = self._get_sector(pos['symbol'])
                value = pos.get('current_value', 0)
                sector_exposure[sector] = sector_exposure.get(sector, 0) + value
            
            # Add new position
            sector_exposure[new_sector] = sector_exposure.get(new_sector, 0) + new_size
            
            # Check limits
            total_value = portfolio_value + new_size
            for sector, exposure in sector_exposure.items():
                concentration = exposure / total_value
                
                if concentration > self.limits['max_sector_concentration']:
                    return {
                        'allowed': False,
                        'reason': f'{sector} concentration too high: {concentration:.1%}',
                        'recommendation': f'Reduce {sector} exposure or increase other sectors',
                        'sector_breakdown': sector_exposure
                    }
            
            return {
                'allowed': True,
                'reason': 'Within sector limits',
                'sector_breakdown': sector_exposure
            }
            
        except Exception as e:
            self.logger.error(f"Error checking sector concentration: {e}")
            return {
                'allowed': True,
                'reason': f'Error: {e}'
            }
    
    def _get_correlation(
        self,
        symbol1: str,
        symbol2: str,
        period: str = '3mo'
    ) -> float:
        """Calculate correlation between two symbols"""
        # Check cache
        cache_key = f"{symbol1}_{symbol2}_{period}"
        if cache_key in self.correlation_cache:
            cached = self.correlation_cache[cache_key]
            if datetime.now() - cached['timestamp'] < self.cache_expiry:
                return cached['correlation']
        
        try:
            # Fetch historical data
            data1 = yf.Ticker(symbol1).history(period=period)
            data2 = yf.Ticker(symbol2).history(period=period)
            
            if data1.empty or data2.empty:
                return 0.0
            
            # Align dates
            common_dates = data1.index.intersection(data2.index)
            if len(common_dates) < 20:  # Need minimum data
                return 0.0
            
            # Calculate returns
            returns1 = data1.loc[common_dates, 'Close'].pct_change().dropna()
            returns2 = data2.loc[common_dates, 'Close'].pct_change().dropna()
            
            # Calculate correlation
            correlation = returns1.corr(returns2)
            
            # Cache result
            self.correlation_cache[cache_key] = {
                'correlation': correlation,
                'timestamp': datetime.now()
            }
            
            return correlation
            
        except Exception as e:
            self.logger.warning(f"Correlation calculation error for {symbol1}/{symbol2}: {e}")
            return 0.0
    
    def _get_sector(self, symbol: str) -> str:
        """Get sector for symbol"""
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            return info.get('sector', 'Unknown')
        except Exception as e:
            return 'Unknown'
    
    def get_portfolio_correlation_matrix(
        self,
        positions: List[Dict]
    ) -> pd.DataFrame:
        """Generate correlation matrix for portfolio"""
        try:
            if len(positions) < 2:
                return pd.DataFrame()
            
            symbols = [p['symbol'] for p in positions]
            n = len(symbols)
            
            # Initialize matrix
            corr_matrix = np.zeros((n, n))
            
            # Calculate pairwise correlations
            for i in range(n):
                for j in range(n):
                    if i == j:
                        corr_matrix[i][j] = 1.0
                    else:
                        corr_matrix[i][j] = self._get_correlation(
                            symbols[i], symbols[j]
                        )
            
            # Create DataFrame
            df = pd.DataFrame(
                corr_matrix,
                index=symbols,
                columns=symbols
            )
            
            return df
            
        except Exception as e:
            self.logger.error(f"Error creating correlation matrix: {e}")
            return pd.DataFrame()
    
    def print_correlation_report(
        self,
        positions: List[Dict],
        portfolio_value: float
    ):
        """Print formatted correlation report"""
        print("\n" + "="*70)
        print("PORTFOLIO CORRELATION REPORT")
        print("="*70)
        
        # Sector concentration
        sector_exposure = {}
        for pos in positions:
            sector = self._get_sector(pos['symbol'])
            value = pos.get('current_value', 0)
            sector_exposure[sector] = sector_exposure.get(sector, 0) + value
        
        print("\nSECTOR CONCENTRATION:")
        for sector, exposure in sorted(sector_exposure.items(), key=lambda x: x[1], reverse=True):
            pct = exposure / portfolio_value if portfolio_value > 0 else 0
            warning = " ⚠️ HIGH" if pct > self.limits['max_sector_concentration'] else ""
            print(f"  {sector}: {pct:.1%}{warning}")
        
        # Correlation matrix
        corr_matrix = self.get_portfolio_correlation_matrix(positions)
        
        if not corr_matrix.empty:
            print("\nHIGH CORRELATIONS (>0.70):")
            n = len(corr_matrix)
            high_corr_found = False
            
            for i in range(n):
                for j in range(i+1, n):
                    corr = corr_matrix.iloc[i, j]
                    if corr > 0.70:
                        high_corr_found = True
                        symbol1 = corr_matrix.index[i]
                        symbol2 = corr_matrix.index[j]
                        print(f"  {symbol1} ↔ {symbol2}: {corr:.2f}")
            
            if not high_corr_found:
                print("  None detected ✓")
        
        print("="*70 + "\n")
