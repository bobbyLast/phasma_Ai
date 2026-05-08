"""
Emergent Order Theory
Core theory for understanding patterns in complex systems
Used by Galton Mindset for probabilistic thinking
"""

import numpy as np
from scipy import stats
from typing import List, Dict, Tuple, Optional
import json


class EmergentOrderTheory:
    """
    Theory of emergent order in complex systems
    Helps understand how patterns emerge from chaos
    """
    
    def __init__(self):
        self.pattern_types = {
            'normal_distribution': 'Random but predictable',
            'fat_tailed': 'Extreme events more likely',
            'bimodal': 'Two distinct regimes',
            'skewed': 'Bias in one direction',
            'chaotic': 'Sensitive to initial conditions'
        }
    
    def analyze_system_as_galton(self, data: List[float], system_name: str = "System") -> Dict:
        """
        Analyze data through Galton board perspective
        
        A Galton board shows how random events create predictable patterns
        """
        if len(data) < 10:
            return {'error': 'Insufficient data for analysis'}
        
        # Convert to numpy array
        returns = np.array(data)
        
        # Basic statistics
        mean = np.mean(returns)
        std_dev = np.std(returns)
        
        # Distribution analysis
        skewness = stats.skew(returns)
        kurtosis = stats.kurtosis(returns)
        
        # Pattern detection
        pattern_type = self._identify_pattern(returns, skewness, kurtosis)
        
        # Galton insights
        galton_insight = self._generate_galton_insight(pattern_type, mean, std_dev, skewness)
        
        # Predictability score
        predictability = self._calculate_predictability(returns)
        
        return {
            'system_name': system_name,
            'data_points': len(data),
            'mean': mean,
            'std_dev': std_dev,
            'skewness': skewness,
            'kurtosis': kurtosis,
            'pattern_type': pattern_type,
            'pattern_strength': self._get_pattern_strength(skewness, kurtosis),
            'galton_insight': galton_insight,
            'predictability_score': predictability,
            'interpretation': self._interpret_results(pattern_type, predictability)
        }
    
    def _identify_pattern(self, data: np.ndarray, skewness: float, kurtosis: float) -> str:
        """Identify the type of pattern in the data"""
        
        # Check for normal distribution
        _, p_normal = stats.normaltest(data)
        if p_normal > 0.05:
            return 'normal_distribution'
        
        # Check for fat tails (high kurtosis)
        if kurtosis > 3:
            return 'fat_tailed'
        
        # Check for bimodal (using Hartigan's dip test approximation)
        if self._is_bimodal(data):
            return 'bimodal'
        
        # Check for skew
        if abs(skewness) > 0.5:
            return 'skewed'
        
        # Default to chaotic
        return 'chaotic'
    
    def _is_bimodal(self, data: np.ndarray) -> bool:
        """Simple check for bimodal distribution"""
        # Use kernel density estimation peaks
        try:
            from scipy.stats import gaussian_kde
            kde = gaussian_kde(data)
            x_range = np.linspace(min(data), max(data), 100)
            density = kde(x_range)
            
            # Count peaks
            peaks = 0
            for i in range(1, len(density)-1):
                if density[i] > density[i-1] and density[i] > density[i+1]:
                    peaks += 1
            
            return peaks >= 2
        except:
            return False
    
    def _generate_galton_insight(self, pattern_type: str, mean: float, 
                                std_dev: float, skewness: float) -> str:
        """Generate insight based on Galton board principles"""
        
        insights = {
            'normal_distribution': f"Like a Galton board, outcomes follow a bell curve. "
                                   f"Most results cluster around {mean:.2%} with predictable variability.",
            
            'fat_tailed': f"Unlike a simple Galton board, extreme events occur more frequently. "
                          f"Black swans are possible - prepare for tail risks.",
            
            'bimodal': f"The system has two distinct states, like a Galton board with two paths. "
                       f"Outcomes tend to cluster in either high or low regimes.",
            
            'skewed': f"The Galton board is tilted! Outcomes favor "
                     f"{'positive' if skewness > 0 else 'negative'} side.",
            
            'chaotic': f"Like a Galton board with obstacles, small changes create "
                      f"unpredictable outcomes. High sensitivity to conditions."
        }
        
        return insights.get(pattern_type, "Pattern not recognized")
    
    def _calculate_predictability(self, data: np.ndarray) -> float:
        """Calculate how predictable the system is (0-100)"""
        
        # Use autocorrelation as a measure of predictability
        if len(data) < 20:
            return 50.0  # Default for small samples
        
        # Calculate autocorrelation at lag 1
        autocorr = np.corrcoef(data[:-1], data[1:])[0, 1]
        
        # Convert to predictability score
        predictability = abs(autocorr) * 100
        
        # Adjust for volatility
        volatility = np.std(data)
        if volatility > 0.1:  # High volatility reduces predictability
            predictability *= 0.7
        
        return min(100, max(0, predictability))
    
    def _get_pattern_strength(self, skewness: float, kurtosis: float) -> str:
        """Describe the strength of the pattern"""
        
        total_deviation = abs(skewness) + abs(kurtosis - 3)
        
        if total_deviation < 0.5:
            return "very weak"
        elif total_deviation < 1.0:
            return "weak"
        elif total_deviation < 2.0:
            return "moderate"
        elif total_deviation < 3.0:
            return "strong"
        else:
            return "very strong"
    
    def _interpret_results(self, pattern_type: str, predictability: float) -> str:
        """Interpret what the results mean for trading"""
        
        interpretations = {
            'normal_distribution': "Trade with statistical methods - options pricing works well",
            'fat_tailed': "Use tail risk hedging - avoid naked short positions",
            'bimodal': "Look for regime indicators - trend following strategies",
            'skewed': f"Bias trades {'long' if predictability > 50 else 'short'} - follow the skew",
            'chaotic': "Use adaptive strategies - fixed rules will fail"
        }
        
        base = interpretations.get(pattern_type, "Unknown pattern")
        
        if predictability > 70:
            base += " | High predictability - increase position size"
        elif predictability < 30:
            base += " | Low predictability - reduce position size"
        
        return base


class PatternDetector:
    """
    Detects patterns in time series data
    Companion to EmergentOrderTheory
    """
    
    def __init__(self):
        self.patterns = {
            'trend': self._detect_trend,
            'mean_reversion': self._detect_mean_reversion,
            'momentum': self._detect_momentum,
            'cycle': self._detect_cycle
        }
    
    def detect_patterns(self, data: List[float]) -> Dict[str, float]:
        """Detect all pattern types and return confidence scores"""
        
        results = {}
        for pattern_name, detector in self.patterns.items():
            try:
                confidence = detector(data)
                results[pattern_name] = confidence
            except:
                results[pattern_name] = 0.0
        
        return results
    
    def _detect_trend(self, data: List[float]) -> float:
        """Detect trend strength (0-100)"""
        if len(data) < 10:
            return 0.0
        
        x = np.arange(len(data))
        slope, _, r_value, _, _ = stats.linregress(x, data)
        
        # Confidence based on R-squared
        confidence = r_value ** 2 * 100
        
        # Adjust for slope significance
        if abs(slope) < 0.001:
            confidence *= 0.5
        
        return min(100, max(0, confidence))
    
    def _detect_mean_reversion(self, data: List[float]) -> float:
        """Detect mean reversion tendency"""
        if len(data) < 20:
            return 0.0
        
        # Calculate Hurst exponent (simplified)
        returns = np.diff(data)
        
        # Variance ratio test
        short_var = np.var(returns[:10])
        long_var = np.var(returns)
        
        if long_var == 0:
            return 0.0
        
        variance_ratio = short_var / long_var
        
        # Mean reversion indicated by variance ratio < 1
        if variance_ratio < 1:
            confidence = (1 - variance_ratio) * 100
        else:
            confidence = 0.0
        
        return min(100, max(0, confidence))
    
    def _detect_momentum(self, data: List[float]) -> float:
        """Detect momentum patterns"""
        if len(data) < 10:
            return 0.0
        
        # Simple momentum: positive correlation with lagged returns
        returns = np.diff(data)
        
        if len(returns) < 5:
            return 0.0
        
        # Autocorrelation of returns
        autocorr = np.corrcoef(returns[:-1], returns[1:])[0, 1]
        
        if autocorr > 0:
            confidence = autocorr * 100
        else:
            confidence = 0.0
        
        return min(100, max(0, confidence))
    
    def _detect_cycle(self, data: List[float]) -> float:
        """Detect cyclical patterns"""
        if len(data) < 20:
            return 0.0
        
        # Simple FFT-based cycle detection
        try:
            from scipy.fft import fft, fftfreq
            
            # Remove trend
            detrended = data - np.mean(data)
            
            # FFT
            fft_vals = fft(detrended)
            freqs = fftfreq(len(data))
            
            # Find dominant frequency (excluding zero frequency)
            power = np.abs(fft_vals) ** 2
            power[0] = 0  # Remove DC component
            
            if len(power) > 1:
                max_power = np.max(power)
                total_power = np.sum(power)
                
                # Confidence based on power concentration
                confidence = (max_power / total_power) * 100
                
                # Check if frequency makes sense (not too fast)
                dominant_freq_idx = np.argmax(power)
                dominant_freq = abs(freqs[dominant_freq_idx])
                
                # Reasonable cycles: period between 5 and 50 data points
                if dominant_freq > 0:
                    period = 1 / dominant_freq
                    if 5 <= period <= len(data) / 3:
                        return min(100, max(0, confidence))
            
            return 0.0
        except:
            return 0.0
