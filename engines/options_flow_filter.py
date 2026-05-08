"""
Options Flow Filter - Filter meaningful options activity from noise

Distinguishes real buying interest from gamma hedging, sweeps, and market making noise.
"""

from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import numpy as np
import yfinance as yf


class OptionsFlowFilter:
    """Filter meaningful options activity from noise"""
    
    def __init__(self):
        """Initialize options flow filter"""
        self.min_volume_threshold = 100  # Minimum contracts
        self.min_oi_threshold = 50      # Minimum open interest
        self.sweep_multiplier = 2.0      # Sweep must be 2x average volume
        self.block_threshold = 500       # Block trade threshold
        
    def analyze_options_flow(self, symbol: str, options_data: Dict = None) -> List[Dict]:
        """
        Analyze options flow and filter meaningful signals
        
        Args:
            symbol: Stock ticker
            options_data: Options chain data (if None, will fetch)
            
        Returns:
            List of filtered options signals
        """
        signals = []
        
        # Get options data if not provided
        if options_data is None:
            options_data = self._fetch_options_data(symbol)
        
        if not options_data:
            return signals
        
        # Analyze calls and puts separately
        for option_type in ['calls', 'puts']:
            if option_type in options_data:
                chain = options_data[option_type]
                
                # Detect sweep trades
                sweeps = self._detect_sweeps(chain, option_type)
                signals.extend(sweeps)
                
                # Detect block trades
                blocks = self._detect_blocks(chain, option_type)
                signals.extend(blocks)
                
                # Check for unusual volume
                unusual = self._detect_unusual_volume(chain, option_type)
                signals.extend(unusual)
                
                # Check OI changes
                oi_changes = self._detect_oi_changes(chain, option_type)
                signals.extend(oi_changes)
        
        # Score and rank signals
        scored_signals = self._score_signals(signals)
        
        return scored_signals
    
    def _fetch_options_data(self, symbol: str) -> Dict:
        """Fetch current options data for symbol"""
        try:
            ticker = yf.Ticker(symbol)
            expirations = ticker.options
            
            if not expirations:
                return {}
            
            # Get nearest expiry
            nearest_expiry = expirations[0]
            chain = ticker.option_chain(nearest_expiry)
            
            return {
                'calls': chain.calls.to_dict('records'),
                'puts': chain.puts.to_dict('records'),
                'expiry': nearest_expiry
            }
            
        except Exception as e:
            print(f"Error fetching options for {symbol}: {e}")
            return {}
    
    def _detect_sweeps(self, chain: List[Dict], option_type: str) -> List[Dict]:
        """
        Detect sweep trades (aggressive multi-strike orders)
        
        Sweep characteristics:
        - Large volume relative to OI
        - Aggressive pricing (above ask for calls, below bid for puts)
        - Multiple strikes traded simultaneously
        """
        sweeps = []
        
        # Calculate average volume and OI
        volumes = [c.get('volume', 0) for c in chain]
        open_interests = [c.get('openInterest', 0) for c in chain]
        
        if not volumes:
            return sweeps
        
        avg_volume = np.mean(volumes)
        avg_oi = np.mean(open_interests)
        
        for option in chain:
            volume = option.get('volume', 0)
            oi = option.get('openInterest', 0)
            strike = option.get('strike', 0)
            
            # Sweep criteria
            if volume > avg_volume * self.sweep_multiplier:
                if volume > self.min_volume_threshold:
                    
                    # Check if it's aggressive (for calls)
                    is_aggressive = False
                    if option_type == 'calls':
                        # Would need real-time bid/ask data
                        # For now, assume large volume = aggressive
                        is_aggressive = volume > avg_volume * 3
                    
                    confidence = min(volume / (avg_volume * 5), 1.0)
                    
                    sweeps.append({
                        'type': 'sweep_trade',
                        'option_type': option_type,
                        'strike': strike,
                        'volume': volume,
                        'open_interest': oi,
                        'volume_ratio': volume / avg_volume if avg_volume > 0 else 0,
                        'is_aggressive': is_aggressive,
                        'confidence': confidence,
                        'reasoning': f"Sweep: {volume:.0f} contracts ({volume/avg_volume:.1f}x avg volume)"
                    })
        
        return sweeps
    
    def _detect_blocks(self, chain: List[Dict], option_type: str) -> List[Dict]:
        """
        Detect large block trades
        
        Block characteristics:
        - Very large volume (500+ contracts)
        - Often at midpoint price
        - Institutional size
        """
        blocks = []
        
        for option in chain:
            volume = option.get('volume', 0)
            strike = option.get('strike', 0)
            
            if volume >= self.block_threshold:
                # Additional checks for block quality
                oi = option.get('openInterest', 0)
                
                # Blocks often have high OI or represent new positions
                is_new_position = volume > oi * 0.5
                
                confidence = min(volume / 1000, 1.0)  # 1000 contracts = 100% confidence
                
                blocks.append({
                    'type': 'block_trade',
                    'option_type': option_type,
                    'strike': strike,
                    'volume': volume,
                    'open_interest': oi,
                    'is_new_position': is_new_position,
                    'confidence': confidence,
                    'reasoning': f"Block: {volume:.0f} contracts (institutional size)"
                })
        
        return blocks
    
    def _detect_unusual_volume(self, chain: List[Dict], option_type: str) -> List[Dict]:
        """
        Detect unusual volume spikes
        
        Criteria:
        - Volume > 3x average
        - Volume > 100 contracts
        - Not a sweep or block (already captured)
        """
        unusual = []
        
        volumes = [c.get('volume', 0) for c in chain]
        if not volumes:
            return unusual
        
        avg_volume = np.mean(volumes)
        
        for option in chain:
            volume = option.get('volume', 0)
            strike = option.get('strike', 0)
            oi = option.get('openInterest', 0)
            
            # Unusual volume criteria
            if volume > avg_volume * 3 and volume < self.block_threshold:
                if volume > self.min_volume_threshold:
                    
                    # Check if it's supported by OI change
                    oi_support = oi > 0
                    
                    confidence = min((volume / avg_volume) / 5, 0.7)  # Max 70% for volume alone
                    
                    unusual.append({
                        'type': 'unusual_volume',
                        'option_type': option_type,
                        'strike': strike,
                        'volume': volume,
                        'open_interest': oi,
                        'volume_ratio': volume / avg_volume if avg_volume > 0 else 0,
                        'oi_support': oi_support,
                        'confidence': confidence,
                        'reasoning': f"Unusual volume: {volume:.0f} contracts ({volume/avg_volume:.1f}x avg)"
                    })
        
        return unusual
    
    def _detect_oi_changes(self, chain: List[Dict], option_type: str) -> List[Dict]:
        """
        Detect significant open interest changes
        
        Note: In production, this would compare with previous day's OI
        For now, use absolute OI as proxy
        """
        oi_changes = []
        
        for option in chain:
            oi = option.get('openInterest', 0)
            volume = option.get('volume', 0)
            strike = option.get('strike', 0)
            
            # Look for high OI with supporting volume
            if oi > self.min_oi_threshold * 10:  # 10x minimum threshold
                if volume > oi * 0.1:  # Volume is 10%+ of OI
                    
                    confidence = min(oi / 10000, 0.8)  # 10k OI = 80% confidence
                    
                    oi_changes.append({
                        'type': 'oi_increase',
                        'option_type': option_type,
                        'strike': strike,
                        'open_interest': oi,
                        'volume': volume,
                        'volume_oi_ratio': volume / oi if oi > 0 else 0,
                        'confidence': confidence,
                        'reasoning': f"High OI: {oi:.0f} contracts with {volume:.0f} volume"
                    })
        
        return oi_changes
    
    def _score_signals(self, signals: List[Dict]) -> List[Dict]:
        """
        Score and rank signals by quality
        
        Scoring factors:
        - Signal type (sweep > block > unusual > OI)
        - Volume magnitude
        - Confidence
        - Option type (calls for bullish, puts for bearish)
        """
        
        # Type weights
        type_weights = {
            'sweep_trade': 1.0,
            'block_trade': 0.9,
            'unusual_volume': 0.7,
            'oi_increase': 0.6
        }
        
        scored = []
        
        for signal in signals:
            base_score = signal.get('confidence', 0)
            type_weight = type_weights.get(signal['type'], 0.5)
            
            # Adjust for option type
            if signal['option_type'] == 'calls':
                type_weight *= 1.1  # Slightly prefer calls for momentum
            
            final_score = base_score * type_weight
            
            signal['final_score'] = final_score
            scored.append(signal)
        
        # Sort by score
        scored.sort(key=lambda x: x['final_score'], reverse=True)
        
        return scored
    
    def get_top_signals(self, symbol: str, max_signals: int = 5) -> List[Dict]:
        """
        Get top N signals for a symbol
        
        Args:
            symbol: Stock ticker
            max_signals: Maximum number of signals to return
            
        Returns:
            Top signals sorted by score
        """
        signals = self.analyze_options_flow(symbol)
        return signals[:max_signals]
    
    def calculate_bullish_bearish_ratio(self, signals: List[Dict]) -> Dict:
        """
        Calculate bullish vs bearish signal ratio
        
        Args:
            signals: List of options signals
            
        Returns:
            Ratio analysis
        """
        call_score = sum(s['final_score'] for s in signals if s['option_type'] == 'calls')
        put_score = sum(s['final_score'] for s in signals if s['option_type'] == 'puts')
        
        total_score = call_score + put_score
        
        if total_score == 0:
            return {'bullish': 0.5, 'bearish': 0.5, 'ratio': 1.0}
        
        bullish = call_score / total_score
        bearish = put_score / total_score
        
        return {
            'bullish': bullish,
            'bearish': bearish,
            'ratio': bullish / bearish if bearish > 0 else float('inf'),
            'call_score': call_score,
            'put_score': put_score
        }


# Example usage
if __name__ == "__main__":
    filter = OptionsFlowFilter()
    
    # Analyze a symbol
    signals = filter.analyze_options_flow('AAPL')
    
    print(f"Found {len(signals)} signals:")
    for signal in signals[:5]:
        print(f"- {signal['type']}: {signal['reasoning']} (Score: {signal['final_score']:.2f})")
